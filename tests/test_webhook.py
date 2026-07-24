"""
Tests for the GitHub webhook handler (src/api/webhook.py).

Covers:
    - verify_signature(): valid, invalid, missing, no-secret-configured
    - POST /webhook/github: ping, pull_request, issues, unknown, bad sig, bad JSON
"""

import hashlib
import hmac
import json
import os
import pytest
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app
from src.api.webhook import verify_signature


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


SECRET = "test_webhook_secret"


def make_signature(payload: bytes, secret: str = SECRET) -> str:
    """Generate a valid X-Hub-Signature-256 header value."""
    digest = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def post_webhook(client, payload: dict, event: str = "push",
                 secret: str = SECRET, sig_override=None):
    """Helper to POST a signed webhook payload."""
    body = json.dumps(payload).encode()
    sig  = sig_override if sig_override is not None else make_signature(body, secret)
    return client.post(
        "/webhook/github",
        data=body,
        content_type="application/json",
        headers={
            "X-GitHub-Event":       event,
            "X-Hub-Signature-256":  sig,
        },
    )


# ---------------------------------------------------------------------------
# verify_signature unit tests
# ---------------------------------------------------------------------------

class TestVerifySignature:

    def test_valid_signature_returns_true(self):
        payload = b'{"action": "opened"}'
        sig = make_signature(payload)
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            assert verify_signature(payload, sig) is True

    def test_wrong_signature_returns_false(self):
        payload = b'{"action": "opened"}'
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            assert verify_signature(payload, "sha256=deadbeef") is False

    def test_missing_signature_header_returns_false(self):
        payload = b'{"action": "opened"}'
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            assert verify_signature(payload, None) is False

    def test_malformed_signature_no_prefix_returns_false(self):
        payload = b'{"action": "opened"}'
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            assert verify_signature(payload, "deadbeef") is False

    def test_no_secret_configured_returns_true(self):
        """When secret is not set, verification is skipped and True is returned."""
        payload = b'{"action": "opened"}'
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": ""}):
            assert verify_signature(payload, None) is True

    def test_tampered_payload_returns_false(self):
        original = b'{"action": "opened"}'
        sig = make_signature(original)
        tampered = b'{"action": "closed"}'
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            assert verify_signature(tampered, sig) is False


# ---------------------------------------------------------------------------
# Webhook route tests
# ---------------------------------------------------------------------------

class TestWebhookRoute:

    def test_ping_event_returns_pong(self, client):
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, {"zen": "Keep it logically awesome."}, event="ping")
        assert res.status_code == 200
        assert res.get_json()["message"] == "pong"

    def test_invalid_signature_returns_401(self, client):
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, {}, sig_override="sha256=badsig")
        assert res.status_code == 401
        assert res.get_json()["error"] == "invalid_signature"

    def test_pull_request_event_returns_200(self, client):
        payload = {"action": "closed", "pull_request": {"html_url": "https://github.com/test/repo/pull/1"}}
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, payload, event="pull_request")
        assert res.status_code == 200
        assert res.get_json()["event"] == "pull_request"

    @patch("src.api.webhook.Database")
    def test_issues_event_returns_200(self, MockDB, client):
        MockDB.return_value.upsert_user.return_value = 1
        MockDB.return_value.upsert_contribution.return_value = 5
        payload = {"action": "closed", "sender": {"login": "testuser", "id": 1},
                   "issue": {"id": 5, "title": "bug", "html_url": "https://github.com/t/r/issues/5"}}
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, payload, event="issues")
        assert res.status_code == 200
        assert res.get_json()["event"] == "issues"

    def test_unknown_event_is_ignored(self, client):
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, {}, event="star")
        assert res.status_code == 200
        assert res.get_json()["status"] == "ignored"

    def test_action_echoed_in_pull_request_response(self, client):
        payload = {"action": "synchronize", "pull_request": {}}
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, payload, event="pull_request")
        assert res.get_json()["action"] == "synchronize"

    def test_action_echoed_in_issues_response(self, client):
        payload = {"action": "reopened", "issue": {}}
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, payload, event="issues")
        assert res.get_json()["action"] == "reopened"


# ---------------------------------------------------------------------------
# Event parsing tests
# ---------------------------------------------------------------------------

MOCK_SENDER = {"login": "bytebymanas", "id": 1, "avatar_url": "https://github.com/img.png"}

MERGED_PR_PAYLOAD = {
    "action": "closed",
    "sender": MOCK_SENDER,
    "pull_request": {
        "id": 999,
        "merged": True,
        "title": "Fix auth bug",
        "html_url": "https://github.com/test/repo/pull/1",
        "base": {"repo": {"full_name": "test/repo"}},
    },
}

CLOSED_ISSUE_PAYLOAD = {
    "action": "closed",
    "sender": MOCK_SENDER,
    "issue": {
        "id": 888,
        "title": "Crash on login",
        "html_url": "https://github.com/test/repo/issues/5",
    },
}


class TestWebhookEventParsing:

    @patch("src.api.webhook.Database")
    def test_merged_pr_is_persisted(self, MockDB, client):
        """A merged pull_request event should persist the contribution."""
        mock_db = MockDB.return_value
        mock_db.upsert_user.return_value = 1
        mock_db.upsert_contribution.return_value = 42
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, MERGED_PR_PAYLOAD, event="pull_request")
        data = res.get_json()
        assert res.status_code == 200
        assert data["persisted"] is True
        assert data["contrib_id"] == 42
        assert data["username"] == "bytebymanas"

    @patch("src.api.webhook.Database")
    def test_open_pr_is_not_persisted(self, MockDB, client):
        """A pull_request event with action=opened should not persist."""
        payload = {**MERGED_PR_PAYLOAD, "action": "opened"}
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, payload, event="pull_request")
        assert res.get_json()["persisted"] is False
        MockDB.return_value.upsert_contribution.assert_not_called()

    @patch("src.api.webhook.Database")
    def test_unmerged_closed_pr_is_not_persisted(self, MockDB, client):
        """A closed but unmerged PR should not persist."""
        payload = {
            "action": "closed",
            "sender": MOCK_SENDER,
            "pull_request": {"id": 1, "merged": False, "title": "x", "html_url": ""},
        }
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, payload, event="pull_request")
        assert res.get_json()["persisted"] is False

    @patch("src.api.webhook.Database")
    def test_closed_issue_is_persisted(self, MockDB, client):
        """A closed issues event should persist the contribution."""
        mock_db = MockDB.return_value
        mock_db.upsert_user.return_value = 2
        mock_db.upsert_contribution.return_value = 77
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, CLOSED_ISSUE_PAYLOAD, event="issues")
        data = res.get_json()
        assert res.status_code == 200
        assert data["persisted"] is True
        assert data["contrib_id"] == 77

    @patch("src.api.webhook.Database")
    def test_opened_issue_is_not_persisted(self, MockDB, client):
        """An opened issues event should not persist."""
        payload = {**CLOSED_ISSUE_PAYLOAD, "action": "opened"}
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, payload, event="issues")
        assert res.get_json()["persisted"] is False
        MockDB.return_value.upsert_contribution.assert_not_called()

    @patch("src.api.webhook.Database")
    def test_pr_missing_sender_returns_400(self, MockDB, client):
        """A merged PR payload without sender.login should return 400."""
        payload = {**MERGED_PR_PAYLOAD, "sender": {}}
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, payload, event="pull_request")
        assert res.status_code == 400
        assert res.get_json()["error"] == "invalid_payload"

    @patch("src.api.webhook.Database")
    def test_issue_missing_sender_returns_400(self, MockDB, client):
        """A closed issue payload without sender.login should return 400."""
        payload = {**CLOSED_ISSUE_PAYLOAD, "sender": {}}
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            res = post_webhook(client, payload, event="issues")
        assert res.status_code == 400

    @patch("src.api.webhook.Database")
    def test_upsert_user_called_with_correct_username(self, MockDB, client):
        """upsert_user should be called with the sender's login."""
        mock_db = MockDB.return_value
        mock_db.upsert_user.return_value = 5
        mock_db.upsert_contribution.return_value = 10
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
            post_webhook(client, MERGED_PR_PAYLOAD, event="pull_request")
        call_kwargs = mock_db.upsert_user.call_args
        assert call_kwargs is not None
        assert "bytebymanas" in str(call_kwargs)

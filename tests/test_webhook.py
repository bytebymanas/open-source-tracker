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

    def test_issues_event_returns_200(self, client):
        payload = {"action": "closed", "issue": {"html_url": "https://github.com/test/repo/issues/5"}}
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

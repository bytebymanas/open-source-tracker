"""
GitHub Webhook Handler

Receives and verifies incoming GitHub webhook events.

Signature verification:
    GitHub signs every webhook payload with HMAC-SHA256 using the secret
    configured in GITHUB_WEBHOOK_SECRET. The signature is sent in the
    X-Hub-Signature-256 header as "sha256=<hex_digest>".

Supported events (X-GitHub-Event header):
    - pull_request  : logged and acknowledged
    - issues        : logged and acknowledged
    - ping          : responds with pong to confirm the webhook is live

All other event types receive a 200 with {"status": "ignored"}.
"""

import hashlib
import hmac
import logging
import os
from typing import Optional

from flask import Blueprint, jsonify, request
from src.models.database import Database
from src.utils.scoring import ScoringEngine

logger = logging.getLogger(__name__)

webhook = Blueprint("webhook", __name__, url_prefix="/webhook")


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------

def verify_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
    """
    Verify the HMAC-SHA256 signature sent by GitHub.

    Args:
        payload_bytes:     Raw request body as bytes.
        signature_header:  Value of X-Hub-Signature-256 header (may be None).

    Returns:
        True if the signature is valid or if no webhook secret is configured.
        False if the secret is set but the signature is missing or invalid.
    """
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "").strip()

    # If no secret is configured, skip verification (dev/test mode)
    if not secret:
        logger.warning("GITHUB_WEBHOOK_SECRET not set — skipping signature verification")
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()

    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------

@webhook.route("/github", methods=["POST"])
def github_webhook():
    """
    Receive GitHub webhook events.

    Verifies the HMAC-SHA256 signature, then routes to a handler based on
    the X-GitHub-Event header. Unknown events are acknowledged but ignored.

    Returns:
        JSON response with {"status": "ok"} on success.
        JSON response with {"error": "..."} on failure.
    """
    payload_bytes = request.get_data()
    signature     = request.headers.get("X-Hub-Signature-256")
    event_type    = request.headers.get("X-GitHub-Event", "")

    if not verify_signature(payload_bytes, signature):
        logger.warning("Webhook signature verification failed")
        return jsonify({"error": "invalid_signature", "message": "Signature mismatch."}), 401

    try:
        payload = request.get_json(force=True, silent=True) or {}
    except Exception:
        return jsonify({"error": "invalid_payload", "message": "Could not parse JSON body."}), 400

    logger.info("Received GitHub webhook event: %s", event_type)

    if event_type == "ping":
        return jsonify({"status": "ok", "message": "pong"}), 200

    if event_type == "pull_request":
        return _handle_pull_request(payload)

    if event_type == "issues":
        return _handle_issue(payload)

    return jsonify({"status": "ignored", "event": event_type}), 200


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def _handle_pull_request(payload: dict):
    """
    Handle a pull_request webhook event.

    Only persists the contribution when:
        - action == "closed"
        - pull_request.merged == True

    All other actions (opened, synchronize, reopened, etc.) are acknowledged
    but produce no database writes.
    """
    action = payload.get("action", "")
    pr     = payload.get("pull_request", {})

    if action != "closed" or not pr.get("merged"):
        logger.info("pull_request ignored: action=%s merged=%s", action, pr.get("merged"))
        return jsonify({"status": "ok", "event": "pull_request", "action": action, "persisted": False}), 200

    sender   = payload.get("sender", {})
    username = sender.get("login", "")
    if not username:
        return jsonify({"error": "invalid_payload", "message": "sender.login missing"}), 400

    db     = Database()
    scorer = ScoringEngine()

    user_id = db.upsert_user(
        github_username=username,
        github_id=sender.get("id"),
        name=sender.get("login"),
        avatar_url=sender.get("avatar_url"),
    )

    item = {
        "type":      "pull_request",
        "is_merged": True,
        "is_first_contribution": False,
    }
    points    = scorer.score_contribution(item)
    repo_name = pr.get("base", {}).get("repo", {}).get("full_name", "")
    github_id = str(pr.get("id", ""))

    contrib_id = db.upsert_contribution(
        user_id=user_id,
        github_id=github_id,
        contribution_type="pull_request",
        title=pr.get("title", ""),
        url=pr.get("html_url", ""),
        status="merged",
        is_merged=True,
    )

    logger.info(
        "pull_request persisted: user=%s repo=%s contrib_id=%s points=%s",
        username, repo_name, contrib_id, points,
    )
    return jsonify({
        "status":      "ok",
        "event":       "pull_request",
        "action":      action,
        "persisted":   True,
        "contrib_id":  contrib_id,
        "username":    username,
    }), 200


def _handle_issue(payload: dict):
    """
    Handle an issues webhook event.

    Only persists the contribution when:
        - action == "closed"

    All other actions are acknowledged but produce no database writes.
    """
    action = payload.get("action", "")
    issue  = payload.get("issue", {})

    if action != "closed":
        logger.info("issues event ignored: action=%s", action)
        return jsonify({"status": "ok", "event": "issues", "action": action, "persisted": False}), 200

    sender   = payload.get("sender", {})
    username = sender.get("login", "")
    if not username:
        return jsonify({"error": "invalid_payload", "message": "sender.login missing"}), 400

    db     = Database()
    scorer = ScoringEngine()

    user_id = db.upsert_user(
        github_username=username,
        github_id=sender.get("id"),
        name=sender.get("login"),
        avatar_url=sender.get("avatar_url"),
    )

    item = {
        "type":      "issue",
        "is_merged": False,
        "is_first_contribution": False,
    }
    points    = scorer.score_contribution(item)
    github_id = str(issue.get("id", ""))

    contrib_id = db.upsert_contribution(
        user_id=user_id,
        github_id=github_id,
        contribution_type="issue",
        title=issue.get("title", ""),
        url=issue.get("html_url", ""),
        status="closed",
        is_merged=False,
    )

    logger.info(
        "issue persisted: user=%s issue_id=%s contrib_id=%s points=%s",
        username, github_id, contrib_id, points,
    )
    return jsonify({
        "status":      "ok",
        "event":       "issues",
        "action":      action,
        "persisted":   True,
        "contrib_id":  contrib_id,
        "username":    username,
    }), 200


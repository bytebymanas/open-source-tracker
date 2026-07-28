"""
Flask Routes

Defines all HTTP API endpoints for the Open Source Contribution Tracker.
Routes are connected to the GitHub API, scoring engine, database layer,
and cache utility.

All responses are JSON. Errors follow the format:
    {"error": "code", "message": "Human-readable description"}
"""

import csv
import io
import json as _json
from flask import Blueprint, jsonify, request, Response
from src.api.github_api import GitHubAPI, GitHubAPIError
from src.models.database import Database
from src.utils.scoring import ScoringEngine
from src.utils.cache import default_cache
import logging

logger = logging.getLogger(__name__)

api = Blueprint("api", __name__, url_prefix="/api")

github = GitHubAPI()
db = Database()
db.init_schema()
scorer = ScoringEngine()


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------

@api.route("/health", methods=["GET"])
def health():
    """
    Server health check endpoint.

    Returns:
        JSON: {"status": "ok", "message": "Server is running"}
    """
    return jsonify({"status": "ok", "message": "Server is running"}), 200


# ------------------------------------------------------------------
# User
# ------------------------------------------------------------------

@api.route("/user/<username>", methods=["GET"])
def get_user(username):
    """
    Fetch contribution data and computed score for a GitHub user.

    Checks the in-memory cache first. On a cache miss, fetches from
    the GitHub API, computes the score, persists to the database,
    and caches the result.

    Args:
        username (str): GitHub username from the URL path

    Returns:
        JSON: User profile, score summary, and contribution breakdown
    """
    cache_key = f"user:{username}"
    cached = default_cache.get(cache_key)
    if cached:
        logger.info("Cache hit for user: %s", username)
        return jsonify(cached), 200

    # Fetch user profile from GitHub
    try:
        profile = github.get_user(username)
    except GitHubAPIError as e:
        return jsonify({"error": "github_api_error", "message": str(e)}), 503

    if profile is None:
        return jsonify({"error": "not_found", "message": f"GitHub user '{username}' not found."}), 404

    # Fetch merged PRs and closed issues
    try:
        prs = github.get_merged_pull_requests(username)
        issues = github.get_user_issues(username, state="closed")
    except GitHubAPIError as e:
        return jsonify({"error": "github_api_error", "message": str(e)}), 503

    # Build contribution list for the scoring engine
    contributions = []
    for pr in prs:
        contributions.append({
            "github_id": str(pr.get("id")),
            "type": "pull_request",
            "is_merged": True,
            "is_first_contribution": False,
            "title": pr.get("title"),
            "url": pr.get("html_url"),
        })
    for issue in issues:
        contributions.append({
            "github_id": str(issue.get("id")),
            "type": "issue",
            "is_merged": False,
            "is_first_contribution": False,
            "title": issue.get("title"),
            "url": issue.get("html_url"),
        })

    # Compute score
    score_result = scorer.compute_score(contributions)

    # Persist to database
    user_id = db.upsert_user(
        github_username=username,
        github_id=profile.get("id"),
        name=profile.get("name"),
        avatar_url=profile.get("avatar_url"),
    )
    db.upsert_score(
        user_id=user_id,
        total_score=score_result["total_score"],
        pr_count=score_result["pr_count"],
        issue_count=score_result["issue_count"],
        review_count=score_result["review_count"],
        commit_count=score_result["commit_count"],
    )

    response = {
        "username": username,
        "name": profile.get("name"),
        "avatar_url": profile.get("avatar_url"),
        "public_repos": profile.get("public_repos"),
        "score": {
            "total": score_result["total_score"],
            "merged_prs": score_result["pr_count"],
            "issues_closed": score_result["issue_count"],
            "reviews": score_result["review_count"],
        },
    }

    default_cache.set(cache_key, response)
    return jsonify(response), 200


# ------------------------------------------------------------------
# Leaderboard
# ------------------------------------------------------------------

@api.route("/departments", methods=["GET"])
def get_departments():
    """
    Return the sorted list of distinct department names across active users.

    Useful for populating filter dropdowns in the frontend without
    hard-coding department values.

    Returns:
        JSON: {"departments": ["CS", "EE", ...]}
    """
    depts = db.get_departments()
    return jsonify({"departments": depts}), 200


@api.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    """
    Return the ranked leaderboard of all tracked users.

    Query parameters:
        period (str): 'all_time' (default), 'this_month', or 'this_week'
        limit (int): Max entries to return (default 50, max 200)
        department (str): Optional department name to filter results

    Returns:
        JSON: Ranked list of users with scores
    """
    period = request.args.get("period", "all_time")
    valid_periods = {"all_time", "this_month", "this_week"}
    if period not in valid_periods:
        return jsonify({
            "error": "invalid_param",
            "message": f"period must be one of: {', '.join(sorted(valid_periods))}",
        }), 400

    try:
        limit = int(request.args.get("limit", 50))
        if limit < 1 or limit > 200:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "error": "invalid_param",
            "message": "limit must be an integer between 1 and 200",
        }), 400

    department = request.args.get("department", "").strip() or None

    cache_key = f"leaderboard:{period}:{limit}:{department or ''}"
    cached = default_cache.get(cache_key)
    if cached:
        return jsonify(cached), 200

    board = db.get_leaderboard(period=period, limit=limit, department=department)
    ranked = []
    for i, entry in enumerate(board, start=1):
        ranked.append({
            "rank": i,
            "username": entry["github_username"],
            "name": entry.get("name"),
            "avatar_url": entry.get("avatar_url"),
            "department": entry.get("department"),
            "total_score": entry["total_score"],
            "merged_prs": entry["pr_count"],
            "issues_closed": entry["issue_count"],
        })

    response = {"period": period, "department": department, "leaderboard": ranked}
    default_cache.set(cache_key, response)
    return jsonify(response), 200



# ------------------------------------------------------------------
# Rate limit status
# ------------------------------------------------------------------

@api.route("/ratelimit", methods=["GET"])
def rate_limit():
    """
    Return the current GitHub API rate limit status.

    Returns:
        JSON: Remaining requests and reset timestamp
    """
    try:
        data = github.get_rate_limit()
        return jsonify({"github_rate_limit": data}), 200
    except GitHubAPIError as e:
        return jsonify({"error": "github_api_error", "message": str(e)}), 503


# ------------------------------------------------------------------
# User contributions breakdown
# ------------------------------------------------------------------

@api.route("/user/<username>/contributions", methods=["GET"])
def get_user_contributions(username):
    """
    Return a detailed list of contributions for a GitHub user with
    individual scores applied per contribution.

    Fetches merged PRs and closed issues from GitHub, runs each through
    the scoring engine, and returns a scored, sorted list.

    Args:
        username (str): GitHub username from the URL path

    Returns:
        JSON: List of contributions with type, title, URL, and points
    """
    cache_key = f"contributions:{username}"
    cached = default_cache.get(cache_key)
    if cached:
        return jsonify(cached), 200

    # Check user exists
    try:
        profile = github.get_user(username)
    except GitHubAPIError as e:
        return jsonify({"error": "github_api_error", "message": str(e)}), 503

    if profile is None:
        return jsonify({"error": "not_found", "message": f"GitHub user '{username}' not found."}), 404

    # Fetch PRs and issues
    try:
        prs    = github.get_merged_pull_requests(username)
        issues = github.get_user_issues(username, state="closed")
    except GitHubAPIError as e:
        return jsonify({"error": "github_api_error", "message": str(e)}), 503

    # Ensure user exists in the DB so contributions can be linked
    user_id = db.upsert_user(
        github_username=username,
        github_id=profile.get("id"),
        name=profile.get("name"),
        avatar_url=profile.get("avatar_url"),
    )

    contributions = []

    for pr in prs:
        item = {
            "github_id":  str(pr.get("id")),
            "type":       "pull_request",
            "is_merged":  True,
            "is_first_contribution": False,
            "title":      pr.get("title", ""),
            "url":        pr.get("html_url", ""),
            "repo":       pr.get("repository_url", "").split("/repos/")[-1],
            "state":      "merged",
        }
        item["points"] = scorer.score_contribution(item)
        # Persist contribution and attach internal ID for annotation linking
        item["id"] = db.upsert_contribution(
            user_id=user_id,
            github_id=item["github_id"],
            contribution_type=item["type"],
            title=item["title"],
            url=item["url"],
            status=item["state"],
            is_merged=item["is_merged"],
        )
        contributions.append(item)

    for issue in issues:
        item = {
            "github_id":  str(issue.get("id")),
            "type":       "issue",
            "is_merged":  False,
            "is_first_contribution": False,
            "title":      issue.get("title", ""),
            "url":        issue.get("html_url", ""),
            "repo":       issue.get("repository_url", "").split("/repos/")[-1],
            "state":      issue.get("state", "closed"),
        }
        item["points"] = scorer.score_contribution(item)
        item["id"] = db.upsert_contribution(
            user_id=user_id,
            github_id=item["github_id"],
            contribution_type=item["type"],
            title=item["title"],
            url=item["url"],
            status=item["state"],
            is_merged=False,
        )
        contributions.append(item)

    # Sort by points descending
    contributions.sort(key=lambda x: x["points"], reverse=True)

    response = {
        "username":      username,
        "total":         len(contributions),
        "contributions": contributions,
    }
    default_cache.set(cache_key, response)
    return jsonify(response), 200


# ------------------------------------------------------------------
# User repositories
# ------------------------------------------------------------------

@api.route("/user/<username>/repos", methods=["GET"])
def get_user_repos(username):
    """
    Return a list of public repositories for a GitHub user.

    Args:
        username (str): GitHub username from the URL path

    Returns:
        JSON: List of repos with name, description, language, and URL
    """
    cache_key = f"repos:{username}"
    cached = default_cache.get(cache_key)
    if cached:
        return jsonify(cached), 200

    try:
        profile = github.get_user(username)
    except GitHubAPIError as e:
        return jsonify({"error": "github_api_error", "message": str(e)}), 503

    if profile is None:
        return jsonify({"error": "not_found", "message": f"GitHub user '{username}' not found."}), 404

    try:
        raw_repos = github.get_user_repos(username)
    except GitHubAPIError as e:
        return jsonify({"error": "github_api_error", "message": str(e)}), 503

    repos = [
        {
            "name":        r.get("name"),
            "full_name":   r.get("full_name"),
            "description": r.get("description") or "",
            "language":    r.get("language") or "—",
            "url":         r.get("html_url"),
            "stars":       r.get("stargazers_count", 0),
            "forks":       r.get("forks_count", 0),
            "is_fork":     r.get("fork", False),
        }
        for r in raw_repos
    ]

    # Sort by stars descending
    repos.sort(key=lambda x: x["stars"], reverse=True)

    response = {"username": username, "total": len(repos), "repos": repos}
    default_cache.set(cache_key, response)
    return jsonify(response), 200

# ------------------------------------------------------------------
# Mentor Annotations
# ------------------------------------------------------------------

@api.route("/contributions/<int:contribution_id>/annotations", methods=["GET"])
def get_annotations(contribution_id):
    """
    Get all mentor annotations for a specific contribution.
    """
    annotations = db.get_annotations_for_contribution(contribution_id)
    return jsonify({"contribution_id": contribution_id, "annotations": annotations}), 200

@api.route("/contributions/<int:contribution_id>/annotations", methods=["POST"])
def add_annotation(contribution_id):
    """
    Add a mentor annotation to a specific contribution.
    Requires JSON payload: { "mentor_username": str, "note": str (optional), "verified": int (0 or 1), "score_override": int (optional) }
    """
    data = request.get_json()
    if not data or "mentor_username" not in data:
        return jsonify({"error": "invalid_payload", "message": "mentor_username is required"}), 400
    
    mentor_username = data["mentor_username"]
    note = data.get("note")
    
    try:
        verified = int(data.get("verified", 0))
        score_override = data.get("score_override")
        if score_override is not None:
            score_override = int(score_override)
    except (ValueError, TypeError):
        return jsonify({"error": "invalid_payload", "message": "verified and score_override must be integers"}), 400

    # Optional: We could verify if the contribution_id actually exists in the DB first.
    # For now we'll let it fail at DB constraint level if it doesn't.
    try:
        annotation_id = db.add_annotation(
            contribution_id=contribution_id,
            mentor_username=mentor_username,
            note=note,
            verified=verified,
            score_override=score_override
        )
    except Exception as e:
        return jsonify({"error": "db_error", "message": str(e)}), 500
        
    return jsonify({"success": True, "annotation_id": annotation_id}), 201


# ------------------------------------------------------------------
# Export
# ------------------------------------------------------------------

@api.route("/leaderboard/export", methods=["GET"])
def export_leaderboard():
    """
    Export the leaderboard as a downloadable CSV or JSON file.

    Query parameters:
        period (str): 'all_time' (default), 'this_month', or 'this_week'
        limit (int): Max entries to return (default 200)
        format (str): 'csv' (default) or 'json'

    Returns:
        File download: Leaderboard data in the requested format
    """
    period = request.args.get("period", "all_time")
    valid_periods = {"all_time", "this_month", "this_week"}
    if period not in valid_periods:
        return jsonify({
            "error": "invalid_param",
            "message": f"period must be one of: {', '.join(sorted(valid_periods))}",
        }), 400

    try:
        limit = int(request.args.get("limit", 200))
        if limit < 1 or limit > 1000:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "error": "invalid_param",
            "message": "limit must be an integer between 1 and 1000",
        }), 400

    fmt = request.args.get("format", "csv").lower()
    if fmt not in {"csv", "json"}:
        return jsonify({
            "error": "invalid_param",
            "message": "format must be 'csv' or 'json'",
        }), 400

    department = request.args.get("department", "").strip() or None
    board = db.get_leaderboard(period=period, limit=limit, department=department)
    ranked = []
    for i, entry in enumerate(board, start=1):
        ranked.append({
            "rank": i,
            "username": entry["github_username"],
            "name": entry.get("name") or "",
            "department": entry.get("department") or "",
            "total_score": entry["total_score"],
            "merged_prs": entry["pr_count"],
            "issues_closed": entry["issue_count"],
            "reviews": entry["review_count"],
        })

    filename_period = period.replace("_", "-")

    if fmt == "json":
        payload = _json.dumps(
            {"period": period, "leaderboard": ranked},
            indent=2
        )
        return Response(
            payload,
            mimetype="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=leaderboard-{filename_period}.json"
            },
        )

    # CSV
    fields = ["rank", "username", "name", "department", "total_score",
              "merged_prs", "issues_closed", "reviews"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    writer.writerows(ranked)
    csv_content = buf.getvalue()

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=leaderboard-{filename_period}.csv"
        },
    )



# =============================================================================
# Student Roster Routes
# =============================================================================

@api.route("/students", methods=["GET"])
def list_students():
    """
    GET /api/students
    Return all tracked students with their scores and metadata.
    """
    try:
        students = db.get_all_students()
        return jsonify({"total": len(students), "students": students})
    except Exception as exc:
        logger.exception("list_students error")
        return jsonify({"error": "db_error", "message": str(exc)}), 500


@api.route("/students/import", methods=["POST"])
def import_students():
    """
    POST /api/students/import
    Body: {"usernames": ["user1", "user2", ...]}

    Fetch and persist multiple GitHub users in parallel.
    Returns a per-username status report.
    """
    body = request.get_json(silent=True) or {}
    usernames = body.get("usernames", [])
    if not usernames or not isinstance(usernames, list):
        return jsonify({"error": "invalid_payload",
                        "message": "usernames must be a non-empty list"}), 400

    usernames = [u.strip() for u in usernames if isinstance(u, str) and u.strip()]
    if not usernames:
        return jsonify({"error": "invalid_payload",
                        "message": "No valid usernames provided"}), 400

    import concurrent.futures

    def fetch_one(username):
        try:
            user_data  = github.get_user(username)
            score_data = github.get_user_contributions(username)
            scored     = scorer.score_contributions(score_data)
            user_id    = db.upsert_user(
                github_username=username,
                github_id=user_data.get("id"),
                name=user_data.get("name") or user_data.get("login"),
                avatar_url=user_data.get("avatar_url"),
            )
            db.upsert_score(
                user_id=user_id,
                total_score=scored["total_score"],
                pr_count=scored["merged_prs"],
                issue_count=scored["issues_closed"],
                review_count=scored["reviews"],
                period="all_time",
            )
            return {"username": username, "status": "ok",
                    "score": scored["total_score"]}
        except GitHubAPIError as exc:
            return {"username": username, "status": "error", "message": str(exc)}
        except Exception as exc:
            logger.exception("import_students: error for %s", username)
            return {"username": username, "status": "error", "message": str(exc)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(fetch_one, usernames))

    ok    = [r for r in results if r["status"] == "ok"]
    errs  = [r for r in results if r["status"] != "ok"]
    return jsonify({
        "imported": len(ok),
        "failed":   len(errs),
        "results":  results,
    })


@api.route("/students/<username>", methods=["PATCH"])
def update_student(username):
    """
    PATCH /api/students/<username>
    Body: {"department": "CSE", "university": "Chandigarh University"}
    Update department and/or university for a tracked student.
    """
    body = request.get_json(silent=True) or {}
    department = body.get("department")
    university = body.get("university")
    if department is None and university is None:
        return jsonify({"error": "invalid_payload",
                        "message": "Provide at least one of: department, university"}), 400
    updated = db.update_student_meta(username, department=department, university=university)
    if not updated:
        return jsonify({"error": "not_found",
                        "message": f"Student '{username}' not found"}), 404
    return jsonify({"status": "ok", "username": username,
                    "department": department, "university": university})


@api.route("/students/<username>", methods=["DELETE"])
def delete_student(username):
    """
    DELETE /api/students/<username>
    Remove a student and all their data from the tracker.
    """
    deleted = db.delete_student(username)
    if not deleted:
        return jsonify({"error": "not_found",
                        "message": f"Student '{username}' not found"}), 404
    return jsonify({"status": "ok", "username": username, "deleted": True})


# =============================================================================
# Mentor Dashboard Routes
# =============================================================================

@api.route("/annotations", methods=["GET"])
def list_annotations():
    """
    GET /api/annotations
    Query params: mentor, verified (0|1), student
    Return all mentor annotations with contribution and student context.
    """
    mentor  = request.args.get("mentor")
    student = request.args.get("student")
    verified_raw = request.args.get("verified")
    verified = None
    if verified_raw is not None:
        if verified_raw not in ("0", "1"):
            return jsonify({"error": "invalid_param",
                            "message": "verified must be 0 or 1"}), 400
        verified = int(verified_raw)
    try:
        rows = db.get_all_annotations(
            mentor_username=mentor,
            verified=verified,
            student_username=student,
        )
        return jsonify({"total": len(rows), "annotations": rows})
    except Exception as exc:
        logger.exception("list_annotations error")
        return jsonify({"error": "db_error", "message": str(exc)}), 500


@api.route("/annotations/<int:annotation_id>", methods=["PATCH"])
def update_annotation(annotation_id):
    """
    PATCH /api/annotations/<id>
    Body: {"note": "...", "verified": 1, "score_override": 8}
    Partially update a mentor annotation.
    """
    body = request.get_json(silent=True) or {}
    note           = body.get("note")
    verified       = body.get("verified")
    score_override = body.get("score_override")
    if note is None and verified is None and score_override is None:
        return jsonify({"error": "invalid_payload",
                        "message": "Provide at least one field to update"}), 400
    updated = db.update_annotation(annotation_id, note=note,
                                   verified=verified, score_override=score_override)
    if not updated:
        return jsonify({"error": "not_found",
                        "message": f"Annotation {annotation_id} not found"}), 404
    return jsonify({"status": "ok", "annotation_id": annotation_id})


@api.route("/annotations/<int:annotation_id>", methods=["DELETE"])
def delete_annotation(annotation_id):
    """
    DELETE /api/annotations/<id>
    Remove a mentor annotation.
    """
    deleted = db.delete_annotation(annotation_id)
    if not deleted:
        return jsonify({"error": "not_found",
                        "message": f"Annotation {annotation_id} not found"}), 404
    return jsonify({"status": "ok", "annotation_id": annotation_id, "deleted": True})

# API Documentation

> **Status:** Week 3 — Up to Date  
> **Last Updated:** July 2026  
> **Base URL:** `http://localhost:5000` (development)

---

## Overview

The Open Source Contribution Tracker exposes a REST API built with Python Flask 3.0. All responses are JSON unless the endpoint returns a file download. Errors follow a consistent format:

```json
{
  "error": "error_code",
  "message": "Human-readable description"
}
```

---

## Authentication

No authentication is required for public endpoints. A GitHub personal access token must be configured in `.env` for the server to make GitHub API calls:

```
GITHUB_TOKEN=your_token_here
```

---

## Endpoints

### Health Check

```
GET /api/health
```

Returns server status. Used by the frontend to show the API online indicator.

**Response `200`:**
```json
{
  "status": "ok",
  "message": "Server is running"
}
```

---

### Get User Score & Profile

```
GET /api/user/<username>
```

Fetches the GitHub profile, computes a contribution score, persists it to the database, and caches the result for 5 minutes.

**Path Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `username` | string | GitHub username |

**Response `200`:**
```json
{
  "username": "bytebymanas",
  "name": "Manas Chhabra",
  "avatar_url": "https://avatars.githubusercontent.com/u/12345",
  "public_repos": 42,
  "score": {
    "total": 37,
    "merged_prs": 3,
    "issues_closed": 2,
    "reviews": 0
  }
}
```

**Errors:** `404` user not found, `503` GitHub API error.

---

### Get User Contributions (Detailed)

```
GET /api/user/<username>/contributions
```

Returns a scored, sorted list of all merged PRs and closed issues for a user.

**Response `200`:**
```json
{
  "username": "bytebymanas",
  "total": 5,
  "contributions": [
    {
      "github_id": "1001",
      "type": "pull_request",
      "is_merged": true,
      "title": "Fix login bug",
      "url": "https://github.com/test/repo/pull/1",
      "repo": "test/repo",
      "state": "merged",
      "points": 10
    }
  ]
}
```

**Errors:** `404` user not found, `503` GitHub API error.

---

### Get User Repositories

```
GET /api/user/<username>/repos
```

Returns the user's public repositories, sorted by stars descending.

**Response `200`:**
```json
{
  "username": "bytebymanas",
  "total": 12,
  "repos": [
    {
      "name": "open-source-tracker",
      "full_name": "bytebymanas/open-source-tracker",
      "description": "CUSoC 2026 — contribution tracker",
      "language": "Python",
      "url": "https://github.com/bytebymanas/open-source-tracker",
      "stars": 5,
      "forks": 1,
      "is_fork": false
    }
  ]
}
```

---

### Get Leaderboard

```
GET /api/leaderboard
```

Returns the ranked leaderboard.

**Query Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `period` | string | `all_time` | `all_time`, `this_month`, or `this_week` |
| `limit` | integer | `50` | Number of entries (1–200) |

**Response `200`:**
```json
{
  "period": "all_time",
  "leaderboard": [
    {
      "rank": 1,
      "username": "bytebymanas",
      "name": "Manas Chhabra",
      "avatar_url": "...",
      "department": null,
      "total_score": 37,
      "merged_prs": 3,
      "issues_closed": 2
    }
  ]
}
```

---

### Export Leaderboard

```
GET /api/leaderboard/export
```

Downloads the leaderboard as a file attachment.

**Query Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `period` | string | `all_time` | `all_time`, `this_month`, or `this_week` |
| `limit` | integer | `200` | Number of entries (1–1000) |
| `format` | string | `csv` | `csv` or `json` |

**CSV Response (`format=csv`):**
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename=leaderboard-all-time.csv`
- Columns: `rank, username, name, department, total_score, merged_prs, issues_closed, reviews`

**JSON Response (`format=json`):**
- Content-Type: `application/json`
- Content-Disposition: `attachment; filename=leaderboard-all-time.json`

---

### Rate Limit Status

```
GET /api/ratelimit
```

Returns the current GitHub API rate limit status.

**Response `200`:**
```json
{
  "github_rate_limit": {
    "limit": 5000,
    "remaining": 4987,
    "reset": 1721234567
  }
}
```

---

### Get Annotations for a Contribution

```
GET /api/contributions/<contribution_id>/annotations
```

Returns all mentor annotations for a specific stored contribution.

**Path Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `contribution_id` | integer | Internal contribution DB ID |

**Response `200`:**
```json
{
  "contribution_id": 42,
  "annotations": [
    {
      "id": 1,
      "mentor_username": "mentor_alice",
      "note": "Great work!",
      "verified": 1,
      "score_override": null,
      "annotated_at": "2026-07-17T12:00:00"
    }
  ]
}
```

---

### Add Annotation to a Contribution

```
POST /api/contributions/<contribution_id>/annotations
```

Adds a mentor annotation to a stored contribution.

**Request Body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mentor_username` | string | ✅ | GitHub username of the mentor |
| `note` | string | ❌ | Free-text annotation |
| `verified` | integer | ❌ | `0` (unverified) or `1` (verified). Default: `0` |
| `score_override` | integer | ❌ | Override the computed score for this contribution |

**Response `201`:**
```json
{
  "success": true,
  "annotation_id": 7
}
```

**Errors:** `400` missing `mentor_username` or invalid field types.

---

## Error Reference

| HTTP Status | Error Code | Meaning |
|------------|------------|---------|
| `400` | `invalid_param` | Invalid or missing query parameter |
| `400` | `invalid_payload` | Invalid or missing request body field |
| `404` | `not_found` | GitHub user not found |
| `500` | `db_error` | Database operation failed |
| `503` | `github_api_error` | GitHub API unavailable or rate-limited |

---

## GitHub API Integration

- **API Version:** GitHub REST API v3
- **Auth:** Personal Access Token via `GITHUB_TOKEN` environment variable
- **Rate Limits:** 60 req/hour (unauthenticated) · 5,000 req/hour (with token)
- **Docs:** https://docs.github.com/en/rest

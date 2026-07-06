# API Documentation

> **Status:** Draft — Week 1  
> **Last Updated:** July 2026  
> **Base URL:** `http://localhost:5000` (development)

---

## Overview

The Open Source Contribution Tracker exposes a REST API built with Python Flask. All responses are returned in JSON format.

---

## Authentication

Currently, no authentication is required for public endpoints. A GitHub personal access token must be configured in `.env` for the server to make GitHub API calls on the backend.

```
GITHUB_TOKEN=your_token_here
```

---

## Endpoints

### Health Check

```
GET /api/health
```

Returns the server status. Used to verify the server is running.

**Response:**
```json
{
  "status": "ok",
  "message": "Server is running"
}
```

---

### Home

```
GET /
```

Returns the home page (HTML or status message).

---

### *(Planned)* Get User Contributions

```
GET /api/user/<username>
```

Fetches contribution data for a given GitHub username.

> ⚠️ **Not yet implemented.** Coming in Week 2.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `username` | string | Yes | GitHub username |

**Planned Response:**
```json
{
  "username": "bytebymanas",
  "total_repos": 12,
  "contributions": {
    "commits": 0,
    "pull_requests": 0,
    "issues": 0,
    "reviews": 0
  },
  "repositories": []
}
```

---

### *(Planned)* Get Leaderboard

```
GET /api/leaderboard
```

Returns a ranked list of contributors.

> ⚠️ **Not yet implemented.** Coming in Week 3.

---

## Error Handling

All errors follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable message"
}
```

| HTTP Status | Meaning |
|------------|---------|
| `200` | OK |
| `400` | Bad Request |
| `404` | Not Found |
| `429` | Rate Limit Exceeded (GitHub API) |
| `500` | Internal Server Error |

---

## GitHub API Integration

This project uses the **GitHub REST API v3**.

- Base URL: `https://api.github.com`
- Rate limit: 60 requests/hour (unauthenticated), 5000/hour (with token)
- Docs: https://docs.github.com/en/rest

---

*This document will be updated as endpoints are implemented in Week 2 and Week 3.*

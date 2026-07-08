# Database Schema Design

> **Status:** Design Phase — Week 1  
> **Last Updated:** July 2026  
> **Project:** Open Source Contribution Tracker (CUSoC 2026)

---

## Overview

This document defines the database schema for the Open Source Contribution Tracker. The schema is designed for SQLite in development and PostgreSQL in production. Implementation begins in Week 2.

---

## Tables

### 1. `users`

Stores GitHub users being tracked by the system.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal user ID |
| `github_username` | TEXT | UNIQUE, NOT NULL | GitHub username |
| `github_id` | INTEGER | UNIQUE | GitHub user ID |
| `name` | TEXT | | Full display name |
| `avatar_url` | TEXT | | GitHub avatar URL |
| `department` | TEXT | | University department |
| `university` | TEXT | | University name |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether user is tracked |
| `created_at` | TIMESTAMP | DEFAULT NOW | Record creation timestamp |
| `last_synced_at` | TIMESTAMP | | Last GitHub data fetch |

---

### 2. `repositories`

Stores GitHub repositories associated with tracked users.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal repo ID |
| `github_repo_id` | INTEGER | UNIQUE, NOT NULL | GitHub repository ID |
| `name` | TEXT | NOT NULL | Repository name |
| `full_name` | TEXT | NOT NULL | Owner/repo-name format |
| `description` | TEXT | | Repository description |
| `language` | TEXT | | Primary programming language |
| `html_url` | TEXT | | GitHub URL |
| `is_tracked` | BOOLEAN | DEFAULT TRUE | Whether repo is tracked |
| `created_at` | TIMESTAMP | DEFAULT NOW | Record creation timestamp |

---

### 3. `contributions`

Stores individual contribution events fetched from GitHub.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal contribution ID |
| `user_id` | INTEGER | FOREIGN KEY (users.id) | Contributing user |
| `repo_id` | INTEGER | FOREIGN KEY (repositories.id) | Target repository |
| `github_id` | TEXT | UNIQUE | GitHub event ID (PR/issue/commit) |
| `type` | TEXT | NOT NULL | `pull_request`, `issue`, `review`, `commit` |
| `title` | TEXT | | Contribution title or description |
| `url` | TEXT | | GitHub URL to the contribution |
| `status` | TEXT | | `merged`, `open`, `closed` |
| `is_merged` | BOOLEAN | DEFAULT FALSE | Whether PR was merged |
| `is_first_contribution` | BOOLEAN | DEFAULT FALSE | First-time contributor flag |
| `contributed_at` | TIMESTAMP | | When contribution was made on GitHub |
| `created_at` | TIMESTAMP | DEFAULT NOW | Record creation timestamp |

---

### 4. `scores`

Stores computed contribution scores per user per time period.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal score ID |
| `user_id` | INTEGER | FOREIGN KEY (users.id) | Scored user |
| `total_score` | INTEGER | DEFAULT 0 | Cumulative score |
| `pr_count` | INTEGER | DEFAULT 0 | Merged pull request count |
| `issue_count` | INTEGER | DEFAULT 0 | Issues closed count |
| `review_count` | INTEGER | DEFAULT 0 | Code reviews count |
| `commit_count` | INTEGER | DEFAULT 0 | Commits count |
| `period` | TEXT | | `all_time`, `this_month`, `this_week` |
| `calculated_at` | TIMESTAMP | DEFAULT NOW | When score was last computed |

---

### 5. `mentor_annotations`

Stores mentor reviews and annotations on individual contributions.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Annotation ID |
| `contribution_id` | INTEGER | FOREIGN KEY (contributions.id) | Annotated contribution |
| `mentor_username` | TEXT | NOT NULL | Mentor's GitHub username |
| `note` | TEXT | | Mentor's annotation text |
| `verified` | BOOLEAN | DEFAULT FALSE | Whether contribution is verified |
| `score_override` | INTEGER | | Manual score override (if any) |
| `annotated_at` | TIMESTAMP | DEFAULT NOW | Annotation timestamp |

---

## Relationships

```
users
  |
  |--- (1:N) ---> contributions
  |--- (1:N) ---> scores
  
contributions
  |--- (N:1) ---> repositories
  |--- (1:N) ---> mentor_annotations
```

---

## Scoring Formula

Scores are computed by the scoring engine based on contribution type:

```
score = (merged_prs × 10) + (reviews × 5) + (issues_closed × 3) + first_contributor_bonus
```

Where:
- `first_contributor_bonus` = +5 points if `is_first_contribution = TRUE`
- Scores are recalculated every 24 hours via scheduled job

---

## Notes

- Raw contribution data from GitHub is never overwritten by mentor annotations. Annotations are stored as a separate layer in `mentor_annotations`.
- The `contributions.github_id` field ensures idempotent ingestion — re-fetching the same PR/issue will not create duplicates.
- Implementation begins in **Week 2, Day 4**.

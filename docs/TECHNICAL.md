# DSync — Technical Documentation

This document describes how DSync works internally: architecture, data flow, service responsibilities, and what happens at each layer.

For setup and usage instructions, see the [README](../README.md).

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Application Bootstrap](#2-application-bootstrap)
3. [Data Model](#3-data-model)
4. [Authentication & Authorization](#4-authentication--authorization)
5. [Service Layer](#5-service-layer)
6. [Feature Flows](#6-feature-flows)
7. [External Integrations](#7-external-integrations)
8. [Frontend Architecture](#8-frontend-architecture)
9. [Database & Migrations](#9-database--migrations)
10. [Configuration Reference](#10-configuration-reference)
11. [Known Limitations](#11-known-limitations)

---

## 1. System Overview

DSync is a **Flask monolith** with a service-oriented internal structure. HTTP requests enter through two blueprints (`auth` and `main`), route handlers delegate to service classes, services call external APIs and persist to SQLite via SQLAlchemy.

```
Request
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│  Blueprint (routes.py / auth.py)                        │
│  • Validates auth (@login_required)                     │
│  • Parses form/JSON input                               │
│  • Calls service layer                                  │
│  • Returns HTML template or JSON response               │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Service Layer (app/services/)                          │
│  • Business logic                                       │
│  • External API calls (Figma, GitHub, Otari, Gradium)   │
│  • AI prompt construction                               │
│  • Database reads/writes                                │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     SQLite DB      External APIs    File System
   (instance/)     (Figma, etc.)    (uploads/)
```

### Design principles

- **Routes are thin** — they handle HTTP concerns only; logic lives in services.
- **Context is centralized** — `ContextService.build_context()` aggregates all project knowledge for AI prompts.
- **AI is unified** — `AIService.chat()` is the single entry point to Otari for design review, handoff, and PR comparison.
- **Snapshots enable diffing** — Figma state is stored as JSON snapshots; changes are computed by comparing node IDs and properties.

---

## 2. Application Bootstrap

### Entry point: `run.py`

```python
from app import create_app
app = create_app()
```

Flask CLI uses `FLASK_APP=run.py` to locate the application instance.

### Factory: `app/__init__.py` → `create_app()`

`create_app()` performs these steps:

1. Creates the Flask app instance.
2. Sets `UPLOAD_FOLDER` to `app/uploads`.
3. Loads config from `config.Config` (which reads `.env` via `python-dotenv`).
4. Registers the `markdown` Jinja filter (used for handoff specs and AI output).
5. Initializes extensions:
   - `SQLAlchemy` (`db`)
   - `Flask-Migrate` (`migrate`)
   - `Flask-Login` (`login_manager`, login view = `auth.login`)
6. Registers blueprints:
   - `main` from `app/routes.py`
   - `auth` from `app/auth.py`

### Configuration: `config.py`

All secrets and API keys are loaded from environment variables. The SQLite database URI points to `instance/database.db`.

---

## 3. Data Model

All models are defined in `app/models.py`. Timestamps use `Asia/Kolkata` timezone.

### Entity-Relationship Diagram

```
User
 ├── Project (many)
 │    ├── Knowledge (many)
 │    ├── Recording (many)
 │    ├── Constraint (many)
 │    ├── FigmaFile (many)
 │    │    └── FigmaSnapshot (many)
 │    ├── AiInsight (many)
 │    ├── DesignHandoff (many) ──▶ FigmaSnapshot (optional FK)
 │    ├── GitHubRepo (many)
 │    └── PullRequest (many)
 ├── Chat (many)          ← defined, not used in routes
 └── UploadedFile (many)  ← defined, not used in routes
```

### Model reference

#### `User` (`users`)

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `username` | String(50) | Unique |
| `email` | String(120) | Unique |
| `password_hash` | String(255) | Werkzeug hash, never plain text |
| `created_at` | DateTime | Auto-set |

Flask-Login integration via `UserMixin`. User loader at bottom of `models.py`.

#### `Project` (`project`)

Central workspace entity. All features are scoped to a project.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `title` | String(150) | Required |
| `description` | Text | Optional |
| `user_id` | FK → users.id | Owner |
| `created_at`, `updated_at` | DateTime | |

Cascade deletes all child records when a project is deleted.

#### `Knowledge` (`knowledge`)

Manual knowledge base entries.

| Column | Type | Notes |
|--------|------|-------|
| `title` | String(200) | |
| `content` | Text | Full entry body |
| `source` | String(50) | Default `"manual"` |
| `project_id` | FK → project.id | |

Used by `ContextService` to build AI prompts.

#### `Recording`

Browser-captured audio/video with Gradium transcription.

| Column | Type | Notes |
|--------|------|-------|
| `title` | String(150) | |
| `media_type` | String(20) | `"audio"` or `"video"` |
| `file_path` | String(300) | Path under `uploads/recordings/` |
| `transcript` | Text | Gradium output |
| `transcript_status` | String(20) | Default `"Pending"` |
| `project_id` | FK → project.id | |

#### `Constraint` (`constraint`)

Engineer-defined rules injected into AI prompts.

| Column | Type | Notes |
|--------|------|-------|
| `text` | Text | Rule description |
| `project_id` | FK → project.id | |

#### `FigmaFile` (`figma_file`)

Linked Figma design file.

| Column | Type | Notes |
|--------|------|-------|
| `file_key` | String(100) | Extracted from URL or raw key |
| `file_name` | String(255) | From Figma API |
| `last_modified` | String(50) | From Figma API |
| `connected_at` | DateTime | |
| `project_id` | FK → project.id | |

#### `FigmaSnapshot` (`figma_snapshot`)

Point-in-time capture of parsed Figma nodes.

| Column | Type | Notes |
|--------|------|-------|
| `nodes_json` | Text | JSON array of parsed node objects |
| `version_hash` | String(64) | MD5 of sorted nodes JSON |
| `figma_file_id` | FK → figma_file.id | |
| `created_at` | DateTime | |

Each sync creates a new snapshot if the hash differs from the previous one.

#### `AiInsight` (`ai_insight`)

AI-generated design alert.

| Column | Type | Notes |
|--------|------|-------|
| `insight_type` | String(50) | Default `"design_change"` |
| `summary` | Text | AI-generated alert text |
| `sources_json` | Text | Metadata (query, change count) |
| `changes_json` | Text | Raw diff data |
| `status` | String(20) | `pending`, `acknowledged`, `dismissed`, `snoozed` |
| `action_note` | Text | Optional user note |
| `action_at` | DateTime | When action was taken |
| `snoozed_until` | DateTime | Snooze expiry |
| `project_id` | FK → project.id | |

Method `refresh_snooze()` auto-expires snoozes when past `snoozed_until`.

#### `DesignHandoff` (`design_handoff`)

AI-generated engineer spec.

| Column | Type | Notes |
|--------|------|-------|
| `spec` | Text | Markdown handoff document |
| `status` | String(20) | `"draft"` or `"finalized"` |
| `finalized_at` | DateTime | |
| `figma_snapshot_id` | FK → figma_snapshot.id | Optional |
| `project_id` | FK → project.id | |

#### `GitHubRepo` (`github_repo`)

| Column | Type | Notes |
|--------|------|-------|
| `owner` | String(100) | GitHub org or user |
| `repo_name` | String(100) | Repository name |
| `project_id` | FK → project.id | |

#### `PullRequest` (`pull_request`)

| Column | Type | Notes |
|--------|------|-------|
| `pr_number` | Integer | |
| `title` | String(500) | |
| `pr_url` | String(500) | |
| `diff_files_json` | Text | Truncated file diffs |
| `is_design_change` | Boolean | True if UI/style files touched |
| `mismatch_report` | Text | AI comparison result |
| `status` | String(20) | `pending`, `analyzed`, `skipped` |
| `project_id` | FK → project.id | |

---

## 4. Authentication & Authorization

**File:** `app/auth.py`

### Registration flow

```
POST /register
  → RegisterForm validation (Flask-WTF)
  → Check username/email uniqueness
  → generate_password_hash(password)
  → Save User to DB
  → Redirect to /login
```

### Login flow

```
POST /login
  → LoginForm validation
  → User.query.filter_by(email=...)
  → check_password_hash(stored_hash, input_password)
  → login_user(user)  [Flask-Login session cookie]
  → Redirect to /dashboard (or ?next= URL)
```

### Authorization pattern

All project routes verify ownership:

```python
project = Project.query.filter_by(
    id=project_id,
    user_id=current_user.id
).first_or_404()
```

This ensures users can only access their own projects. The GitHub webhook at `/webhooks/github` is the only unauthenticated write endpoint (protected by optional HMAC verification).

---

## 5. Service Layer

Each service is a Python class with static methods. Services never import from routes.

### Core AI pipeline

```
ContextService.build_context(project_id)
        │
        ▼
AIService.chat(system_prompt, user_prompt)
        │
        ▼
OtariClient.completion(model, messages, temperature)
```

### Service catalog

| Service | File | Responsibility |
|---------|------|----------------|
| **AIService** | `ai_service.py` | Single Otari SDK wrapper. Handles auth errors and model-not-found with actionable messages. |
| **ContextService** | `context_service.py` | Aggregates knowledge entries, recording transcripts, and constraints into a formatted text block for AI prompts. Optional keyword filtering via `_matches()`. |
| **DesignReviewService** | `design_review_service.py` | Takes Figma diff changes → builds prompt with context → calls AIService → saves `AiInsight`. |
| **HandoffService** | `handoff_service.py` | Reads latest Figma snapshot + constraints + context → generates markdown dev spec → saves `DesignHandoff`. |
| **PRCompareService** | `pr_compare_service.py` | Compares PR code diff against handoff spec (or Figma snapshot fallback) via AI. |
| **FigmaService** | `figma_service.py` | Figma REST API client. `get_file()`, `extract_file_key()`, `parse_nodes()`. Handles 429 rate limits with retry. |
| **FigmaSyncService** | `figma_sync_service.py` | Orchestrates connect/sync workflow: fetch → parse → hash → snapshot → diff → AI review. |
| **FigmaDiffService** | `figma_diff_service.py` | Compares two node arrays by ID. Detects added, removed, and modified nodes. `format_changes()` for AI prompts. |
| **GitHubService** | `github_service.py` | GitHub REST API. Fetch PR data and files. `is_design_pr()` checks file extensions and path keywords. |
| **PRProcessingService** | `pr_processing_service.py` | Connect repo, fetch PR, detect design changes, run PRCompareService, save PullRequest record. |
| **TranscriptionService** | `transcription_service.py` | Converts WebM → WAV via ffmpeg, sends audio to Gradium ASR, parses streaming JSON response. |
| **AudioConverter** | `audio_converter.py` | ffmpeg subprocess for WebM → WAV conversion. |
| **InsightService** | `insight_service.py` | Insight lifecycle: acknowledge, dismiss, snooze (7 days), status labels, actionable check. |
| **TimelineService** | `timeline_service.py` | Builds unified chronological event feed from all project models. |
| **ConstraintService** | `constraint_service.py` | CRUD for engineer constraints. |
| **KnowledgeService** | `knowledge_service.py` | Add knowledge entries. |
| **ProjectService** | `project_service.py` | Create projects. |

---

## 6. Feature Flows

### 6.1 Figma Connect & Sync

This is the core design sync pipeline.

#### Connect (`POST /project/<id>/figma/connect`)

```
figma.js (browser)
  │  POST { file_key: "..." }
  ▼
routes.connect_figma()
  ▼
FigmaSyncService.connect(project, file_key, api_key)
  │
  ├─ FigmaService.extract_file_key(url)     → "AqXC7qvqAwF4exqcwsZR9K"
  ├─ FigmaService.get_file(file_key)        → GET api.figma.com/v1/files/{key}
  ├─ FigmaService.parse_nodes(file_data)    → walk document tree, extract nodes
  ├─ _hash_nodes(nodes)                     → MD5 of sorted JSON
  ├─ Create/update FigmaFile record
  └─ Create initial FigmaSnapshot
```

**Node parsing** (`FigmaService.parse_nodes`): Recursively walks the Figma document tree. For each node, extracts:

- `id`, `name`, `type`, `page`
- Position and size from `absoluteBoundingBox`
- Text content (for `TEXT` nodes)
- Fill color (for `SOLID` fills)

#### Sync (`POST /project/<id>/figma/sync`)

```
FigmaSyncService.sync(figma_file, api_key)
  │
  ├─ Fetch current file from Figma API
  ├─ Parse nodes, compute version_hash
  ├─ Compare hash with last FigmaSnapshot
  │
  ├─ [No change] → return { changed: false }
  │
  └─ [Changed]
       ├─ FigmaDiffService.diff_snapshots(old, new)
       ├─ Save new FigmaSnapshot
       ├─ DesignReviewService.review_changes(project_id, changes)
       │    ├─ ContextService.build_context(project_id, query=node_names)
       │    ├─ AIService.chat(system, user_prompt)
       │    └─ Save AiInsight
       └─ return { changed: true, changes, insight }
```

#### Diff algorithm (`FigmaDiffService.diff_snapshots`)

1. Index old and new nodes by `id`.
2. **Added:** IDs in new but not in old.
3. **Removed:** IDs in old but not in new.
4. **Modified:** IDs in both, but any property differs (excluding `id` and `page`).

Each change record: `{ change: "added"|"removed"|"modified", node: {...}, diffs?: {...} }`.

---

### 6.2 AI Design Review

Triggered automatically during Figma sync when changes are detected.

```
DesignReviewService.review_changes(project_id, changes)
  │
  ├─ FigmaDiffService.format_changes(changes)  → plain text diff
  ├─ Build query from changed node names
  ├─ ContextService.build_context(project_id, query)
  │    → KNOWLEDGE BASE section
  │    → MEETING TRANSCRIPTS section
  │    → ENGINEER CONSTRAINTS section
  │
  ├─ AIService.chat(SYSTEM_PROMPT, user_prompt)
  │    System: "You are a design advisor..."
  │    User: context + changes
  │
  └─ Save AiInsight(summary=AI response, changes_json=diff)
```

The AI is instructed to flag conflicts with past findings, reference specific dates/sources, and start warnings with "Heads up:".

---

### 6.3 Recording & Transcription

```
Browser (record.js)
  │  MediaRecorder → WebM blob
  │  POST multipart/form-data to /project/<id>/record
  ▼
routes.record()
  │  Save file to uploads/recordings/
  ▼
TranscriptionService.transcribe(filepath)
  │
  ├─ [if .webm] AudioConverter.webm_to_wav()  → ffmpeg
  ├─ POST audio/wav to Gradium ASR API
  │    URL: https://api.gradium.ai/api/post/speech/asr
  │    Header: x-api-key
  │    Response: streaming JSON lines with type="text"
  └─ Join text chunks → transcript string
  ▼
Save Recording(transcript=..., transcript_status="Complete")
```

Transcripts are later included in `ContextService.build_context()` under `=== MEETING TRANSCRIPTS ===`.

---

### 6.4 Design Handoff

```
POST /project/<id>/handoff/finalize
  ▼
HandoffService.finalize(project)
  │
  ├─ Get latest FigmaFile + FigmaSnapshot
  ├─ HandoffService._summarize_nodes(nodes, limit=40)
  │    → Filter to FRAME, COMPONENT, TEXT, etc.
  │    → Format: "name (type) | page=X | WxH px | text=... | color=rgb(...)"
  ├─ Load all Constraint records
  ├─ ContextService.build_context(project.id)
  │
  ├─ AIService.chat(SYSTEM_PROMPT, user_prompt, temperature=0.2)
  │    System: "You are a senior front-end engineer writing a handoff..."
  │    User: project info + figma summary + constraints + context
  │
  └─ Save DesignHandoff(spec=markdown, status="finalized")
```

The handoff page also embeds the Figma file via:

```
https://www.figma.com/embed?embed_host=share&url=https://www.figma.com/design/{file_key}
```

---

### 6.5 GitHub PR Check

#### Manual check

```
POST /project/<id>/github/check  { pr_number: 42 }
  ▼
PRProcessingService.process_pr(project, owner, repo, pr_number)
  │
  ├─ GitHubService.get_pull_request()   → PR metadata
  ├─ GitHubService.get_pr_files()       → changed files + patches
  ├─ GitHubService.is_design_pr(files)  → check extensions/paths
  │
  ├─ [Design PR]
  │    └─ PRCompareService.compare(project, files)
  │         ├─ _get_design_context() → handoff spec or Figma snapshot
  │         ├─ GitHubService.format_diff(files)
  │         └─ AIService.chat() → mismatch report
  │
  └─ Save PullRequest record
```

#### Webhook (automatic)

```
POST /webhooks/github
  │
  ├─ Verify HMAC signature (if GITHUB_WEBHOOK_SECRET set)
  ├─ Parse event: pull_request (opened, synchronize, reopened)
  ├─ PRProcessingService.find_project_for_repo(owner, repo)
  └─ PRProcessingService.process_pr(...)
```

**Design PR detection** checks for:

- File extensions: `.css`, `.scss`, `.tsx`, `.jsx`, `.vue`, `.html`, etc.
- Path keywords: `components/`, `styles/`, `ui/`, `pages/`, etc.

---

### 6.6 Insight Lifecycle

```
InsightService.acknowledge(insight, note?)  → status="acknowledged"
InsightService.dismiss(insight, note?)        → status="dismissed"
InsightService.snooze(insight, days=7)        → status="snoozed", snoozed_until=now+7d
```

`refresh_snooze()` on the model auto-resets expired snoozes to `"pending"`. Called when rendering insights and timeline.

`is_actionable(insight)` returns true only for `status="pending"`.

---

### 6.7 Activity Timeline

`TimelineService.get_events(project_id)` queries all project-scoped models and builds a unified list of event dicts:

| Event kind | Source model | Trigger |
|------------|-------------|---------|
| `recording` | Recording | File saved |
| `knowledge` | Knowledge | Entry added |
| `constraint` | Constraint | Rule added |
| `figma_connect` | FigmaFile | File linked |
| `figma_sync` | FigmaSnapshot | Sync after baseline |
| `insight` | AiInsight | AI alert created |
| `insight_action` | AiInsight | Acknowledge/dismiss/snooze |
| `handoff` | DesignHandoff | Spec finalized |
| `github_connect` | GitHubRepo | Repo linked |
| `pr_analyzed` | PullRequest | PR checked |

Events are sorted by timestamp descending.

---

## 7. External Integrations

### Figma REST API

| Detail | Value |
|--------|-------|
| Base URL | `https://api.figma.com/v1` |
| Auth | `X-Figma-Token: {FIGMA_API_KEY}` |
| Used endpoint | `GET /files/{file_key}` |
| Client | `app/services/figma_service.py` |
| Rate limiting | Auto-retry on 429 using `Retry-After` header (max 2 retries) |
| Error class | `FigmaRateLimitError` → HTTP 429 to client |

**Important:** Tier 1 endpoints (`GET file`) are limited to ~6 requests/month for Viewer/Collab seats. Full/Dev seats get 10–20 requests/minute.

### Otari AI

| Detail | Value |
|--------|-------|
| SDK | `otari.OtariClient(platform_token=api_key)` |
| Method | `client.completion(model, messages, temperature)` |
| Client | `app/services/ai_service.py` |
| Used by | DesignReviewService, HandoffService, PRCompareService |
| Config | `OTARI_API_KEY`, `OTARI_MODEL` |

### Gradium ASR

| Detail | Value |
|--------|-------|
| URL | `https://api.gradium.ai/api/post/speech/asr` |
| Auth | `x-api-key: {GRADIUM_API_KEY}` |
| Input | Raw WAV audio bytes |
| Output | Streaming JSON lines: `{ "type": "text", "text": "..." }` |
| Client | `app/services/transcription_service.py` |

### GitHub REST API

| Detail | Value |
|--------|-------|
| Base URL | `https://api.github.com` |
| Auth | `Authorization: Bearer {GITHUB_TOKEN}` |
| Endpoints | `GET /repos/{owner}/{repo}/pulls/{n}`, `GET .../pulls/{n}/files` |
| Webhook | `POST /webhooks/github` with optional HMAC-SHA256 verification |
| Client | `app/services/github_service.py`, `pr_processing_service.py` |

### ffmpeg

| Detail | Value |
|--------|-------|
| Purpose | Convert browser WebM recordings to WAV before Gradium |
| Client | `app/services/audio_converter.py` |
| Note | Path is currently hardcoded for Windows; update for your machine |

---

## 8. Frontend Architecture

### Template hierarchy

```
base.html                    ← Layout, nav, Bootstrap CDN, flash messages
  ├── index.html             ← Landing page
  ├── dashboard.html         ← Project list
  ├── project.html           ← Project hub (links to all features)
  ├── figma.html             ← Figma connect/sync UI
  ├── insights.html          ← AI alert management
  ├── timeline.html          ← Activity feed
  ├── handoff.html           ← Handoff spec + Figma embed
  ├── github.html            ← Repo connect + PR check
  ├── constraints.html       ← Engineer rules
  ├── knowledge.html         ← Knowledge list
  ├── record_recording.html  ← Browser recorder
  └── _macros.html           ← Reusable components (ai_card, badges, etc.)
```

### JavaScript modules

| File | Purpose |
|------|---------|
| `static/js/figma.js` | AJAX connect/sync via `fetch()` to JSON endpoints. Reloads page on successful connect. |
| `static/js/record.js` | `MediaRecorder` API for browser audio/video capture. POSTs blob as multipart form. |
| `static/js/script.js` | General UI interactions. |

### Styling

`static/css/style.css` — dark theme with custom CSS variables, feature cards, AI output cards, timeline styling. Bootstrap 5.3.7 loaded from CDN in `base.html`.

### Jinja filters

- `markdown` — registered in `create_app()`, renders markdown with `nl2br`, `fenced_code`, and `tables` extensions. Used for handoff specs and AI insight display.

---

## 9. Database & Migrations

### Setup

```bash
flask db upgrade    # Apply all migrations
flask db migrate -m "description"   # Generate new migration after model changes
```

### Migration history (chronological)

| Revision | Description |
|----------|-------------|
| `594ffb895e89` | Users table |
| `8fd351b51a50` | Project model |
| `b18dc521ee77` | Knowledge model |
| `408f7b0e2fa2`, `f5b08f42dbec` | Recording model |
| `d3a537cf147c` | Additional schema |
| `f51aa204b04c` | Constraints |
| `c8e2f1a9b3d4` | FigmaFile, FigmaSnapshot, AiInsight |
| `d4a7b2c9e1f0` | DesignHandoff |
| `e5f8a3b2c1d0` | GitHubRepo, PullRequest |
| `f6a1b2c3d4e5` | Insight action fields (status, snooze, etc.) |

Database file: `instance/database.db` (SQLite, gitignored).

---

## 10. Configuration Reference

### `config.py` → `Config` class

| Key | Source | Default | Used by |
|-----|--------|---------|---------|
| `SECRET_KEY` | env | `"change-this-later"` | Flask sessions |
| `SQLALCHEMY_DATABASE_URI` | computed | `sqlite:///instance/database.db` | SQLAlchemy |
| `FIGMA_API_KEY` | env | — | FigmaService |
| `OTARI_API_KEY` | env | — | AIService |
| `OTARI_MODEL` | env | `mzai:moonshotai/Kimi-K2.6` | AIService |
| `OTARI_BASE_URL` | env | `https://api.otari.ai/v1` | Defined but unused (SDK handles URL) |
| `GRADIUM_API_KEY` | env | — | TranscriptionService |
| `GITHUB_TOKEN` | env | — | GitHubService |
| `GITHUB_WEBHOOK_SECRET` | env | — | Webhook HMAC verification |

### App-level config (set in `create_app()`)

| Key | Value |
|-----|-------|
| `UPLOAD_FOLDER` | `app/uploads` |

---

## 11. Known Limitations

| Item | Details |
|------|---------|
| **Shared Figma token** | One `FIGMA_API_KEY` in `.env` is used for all users. Rate limits are shared. |
| **Hardcoded ffmpeg path** | `audio_converter.py` has a Windows-specific path. Must be updated per machine. |
| **Unused models** | `Chat`, `Message`, `UploadedFile` are defined but have no active routes. |
| **Legacy code** | `app/services/file_service.py` is an unused duplicate of `figma_service.py`. |
| **Empty stub** | `RecordingService` exists but is empty. |
| **SQLite only** | No production database configuration. Suitable for development/demo. |
| **No background jobs** | Figma sync and AI calls are synchronous — long operations block the HTTP request. |
| **Simple keyword matching** | `ContextService._matches()` uses basic word-in-text search, not semantic retrieval. |
| **Single Figma file per project** | Routes query the most recently connected FigmaFile only. |

---

## Appendix: Request Lifecycle Example

**User clicks "Sync" on the Figma page:**

```
1. Browser: figma.js sends POST /project/5/figma/sync
2. routes.sync_figma()
   - @login_required check
   - Load project (user_id scoped)
   - Load latest FigmaFile for project
3. FigmaSyncService.sync(figma_file, FIGMA_API_KEY)
   a. FigmaService.get_file("AqXC7qvqAwF4exqcwsZR9K")
      → HTTP GET to Figma API
      → Returns full file JSON
   b. FigmaService.parse_nodes(file_data)
      → Returns [{id, name, type, page, x, y, width, height, text?, fill?}, ...]
   c. MD5 hash of nodes → compare with last snapshot hash
   d. [Hash differs]
      → FigmaDiffService.diff_snapshots(old_nodes, new_nodes)
      → Returns [{change: "modified", node: {...}, diffs: {...}}]
      → Save new FigmaSnapshot
      → DesignReviewService.review_changes(5, changes)
         → ContextService.build_context(5, query="Button Header")
         → AIService.chat(system_prompt, user_prompt)
            → OtariClient.completion(...)
            → Returns "Heads up: The button color change conflicts with..."
         → Save AiInsight
4. routes.sync_figma() returns JSON:
   { success: true, changed: true, change_count: 3, insight: {...}, message: "Found 3 change(s)." }
5. Browser: figma.js displays message and prepends AI card to insights list
```

This completes the full round-trip from user action to persisted AI insight.

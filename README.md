# DSync

**Design & Engineering in Sync** — a Flask web app that keeps designers and engineers aligned by connecting Figma, meeting transcripts, knowledge bases, and GitHub pull requests into one AI-powered workflow.

Built for the RAISE Summit hackathon. DSync uses **Otari AI** for design review and handoffs, **Gradium** for transcription, **Figma REST API** for design sync, and **GitHub** for PR validation.
1 min - https://youtu.be/EMAnmTbxuGk?si=OZQvZBK5cwdijDrn
4 min (must watch) - https://youtu.be/Fl1ydArW28c?si=cMj3L6-sSt-d9b-P
---

## Table of Contents

- [How Cursor Helped Me](#Cursor-Usage)
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [User Guide](#user-guide)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [External Services Setup](#external-services-setup)
- [Troubleshooting](#troubleshooting)
- [Technical Documentation](#technical-documentation)

---
## How Cursor Helped Me
Honestly, this is my first time using Cursor. The very reason I chose this track was because my Professor said 'You will love it!'. And yes, I loved it! I got so impressed that I don't manually have to give the model the context of what I am working on. Just connect it to the folder and you are good to go. 

Cursor was literally my life saviour in this journey. DSync requires an entirely new website and also the figma designs for demo. I have participated in the RAISE Summit individually. So, it seemed impossible to also code DSync and make another website and figma design in such a short span of time. But, I used cursor and it did the work for me. The website - womentor seen in the demo is coded by Cursor. Website is done but now I was unsure about the figma designs. However, Cursor gave me the figma Code to Design plugin code and boom....all the designs are ready!!! I also used Cursor to implement the Figma and Github PR features.

Thank you so much for the credits Cursor team! You all are a blessing to the world :)

## Features

| Feature | What it does |
|---------|--------------|
| **AI Design Memory** | Store knowledge entries and meeting recordings. Transcripts become searchable context for AI. |
| **Figma Sync** | Connect a Figma file, snapshot design nodes, diff on sync, and generate AI alerts when changes conflict with project history. |
| **Engineer Constraints** | Define rules (e.g. "CTA must stay rectangular") that feed into every AI prompt. |
| **Design Handoff** | Generate a markdown dev spec from the latest Figma snapshot, constraints, and project knowledge. |
| **GitHub PR Check** | Connect a repo, analyze PRs for UI/style files, and compare code diffs against the design spec. |
| **Activity Timeline** | Unified chronological feed of recordings, knowledge, Figma events, insights, handoffs, and GitHub activity. |
| **Insight Workflow** | Acknowledge, dismiss, or snooze AI design alerts. |

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────────────────────────────────────────┐
│   Browser   │────▶│  Flask App (run.py → create_app)                 │
│  Templates  │     │  ├── auth blueprint   (login, register)          │
│  + JS/CSS   │     │  ├── main blueprint   (projects, figma, github)  │
└─────────────┘     │  └── services layer   (business logic)           │
                    └──────────┬───────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
   ┌───────────┐        ┌───────────┐        ┌───────────┐
   │  SQLite   │        │  Otari AI │        │   Figma   │
   │ instance/ │        │  Gradium  │        │  GitHub   │
   └───────────┘        └───────────┘        └───────────┘
```

For a deep dive into every module, service, and data flow, see **[docs/TECHNICAL.md](docs/TECHNICAL.md)**.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3, Flask 3.1 |
| Database | SQLite + SQLAlchemy + Flask-Migrate (Alembic) |
| Auth | Flask-Login, Werkzeug password hashing, Flask-WTF forms |
| AI | [Otari](https://otari.ai) SDK (`otari` package) |
| Transcription | [Gradium](https://gradium.ai) ASR API |
| Design | Figma REST API |
| Version control | GitHub REST API + webhooks |
| Frontend | Jinja2 templates, Bootstrap 5.3, vanilla JavaScript |
| Audio | ffmpeg (WebM → WAV conversion before Gradium) |

---

## Prerequisites

- **Python 3.10+**
- **ffmpeg** — required for browser recording transcription (WebM → WAV)
- API keys for: Figma, Otari, Gradium, GitHub (see [Environment Variables](#environment-variables))

---

## Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd code

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Initialize the database
set FLASK_APP=run.py          # Windows
export FLASK_APP=run.py       # macOS / Linux
flask db upgrade

# 6. Run the development server
flask run
```

Open **http://127.0.0.1:5000** in your browser.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Recommended | Flask session secret. Defaults to `"change-this-later"` if unset. |
| `FIGMA_API_KEY` | Yes (Figma features) | Figma personal access token. Use a **Full** or **Dev** seat token for best rate limits. |
| `OTARI_API_KEY` | Yes (AI features) | Otari platform token (`tk_...`). Get one at [otari.ai](https://otari.ai). |
| `OTARI_MODEL` | No | AI model name. Default: `mzai:moonshotai/Kimi-K2.6` |
| `GRADIUM_API_KEY` | Yes (recordings) | Gradium API key for speech-to-text. |
| `GITHUB_TOKEN` | Yes (PR check) | GitHub PAT with repo read access. |
| `GITHUB_WEBHOOK_SECRET` | Optional | HMAC secret for `/webhooks/github`. Skipped if unset. |

Test Otari connectivity independently:

```bash
python test_otari.py
```

---

## Running the App

```bash
# Standard development server
flask run

# With debug mode
flask run --debug

# Alternative (direct Python)
python -c "from run import app; app.run(debug=True)"
```

**Entry point:** `run.py` exports `app = create_app()`.

**Database location:** `instance/database.db` (SQLite, auto-created on migrate).

**Uploads:** Recordings saved to `uploads/recordings/`.

---

## User Guide

### 1. Create an account

Register at `/register`, then log in. All project features require authentication.

### 2. Create a project

From the dashboard, create a project. Each project is an isolated workspace with its own Figma file, knowledge, recordings, and GitHub repo.

### 3. Build project context

Before Figma sync is most useful, add context:

- **Knowledge** — paste design decisions, research notes, or specs (`/project/<id>/knowledge/new`).
- **Recordings** — record audio/video meetings in the browser; Gradium transcribes them automatically.
- **Constraints** — add engineer rules (`/project/<id>/constraints`).

This context is injected into every AI prompt via `ContextService`.

### 4. Connect Figma

1. Go to **Figma** in the project hub.
2. Paste a Figma file URL or file key.
3. Click **Connect** — the app fetches the file, parses design nodes, and saves a baseline snapshot.
4. After editing in Figma, click **Sync** — the app diffs against the last snapshot and runs AI design review if changes are detected.

### 5. Review AI insights

When Figma changes conflict with past knowledge or constraints, DSync creates an **AI design alert**. Manage alerts from the Insights page:

- **Acknowledge** — mark as seen
- **Dismiss** — ignore permanently
- **Snooze** — hide for 7 days

### 6. Finalize design handoff

Once the design is ready:

1. Go to **Handoff**.
2. Review the embedded Figma preview and constraints.
3. Click **Finalize** — Otari generates a markdown dev spec from the latest snapshot + project context.

### 7. Connect GitHub and check PRs

1. Go to **GitHub** and connect `owner/repo`.
2. Enter a PR number and click **Check PR**, or configure a webhook pointing to `/webhooks/github`.
3. For PRs touching UI/style files, Otari compares the code diff against your handoff spec or Figma snapshot.

### 8. View the timeline

The **Timeline** page aggregates all project activity — recordings, knowledge, Figma syncs, insights, handoffs, and PR checks — in one chronological feed.

---

## Project Structure

```
code/
├── run.py                      # App entry point
├── config.py                   # Configuration + dotenv loading
├── requirements.txt
├── .env.example
├── test_otari.py               # Standalone Otari connectivity test
├── instance/                   # SQLite database (gitignored)
├── uploads/                    # Recording files (gitignored)
├── migrations/                 # Alembic database migrations
├── docs/
│   └── TECHNICAL.md            # Full technical documentation
└── app/
    ├── __init__.py             # create_app() factory
    ├── models.py               # SQLAlchemy models
    ├── routes.py               # Main blueprint (projects, figma, github, etc.)
    ├── auth.py                 # Auth blueprint (login, register, logout)
    ├── forms.py                # WTForms form definitions
    ├── services/               # Business logic layer
    │   ├── ai_service.py           # Otari AI wrapper
    │   ├── context_service.py      # Aggregates knowledge for AI prompts
    │   ├── design_review_service.py
    │   ├── figma_service.py        # Figma REST API client
    │   ├── figma_sync_service.py   # Connect + sync workflow
    │   ├── figma_diff_service.py   # Snapshot diffing
    │   ├── handoff_service.py      # Design handoff generation
    │   ├── github_service.py       # GitHub REST API client
    │   ├── pr_processing_service.py
    │   ├── pr_compare_service.py   # PR vs design comparison
    │   ├── transcription_service.py
    │   ├── audio_converter.py      # ffmpeg WebM → WAV
    │   ├── insight_service.py
    │   ├── timeline_service.py
    │   ├── constraint_service.py
    │   ├── knowledge_service.py
    │   └── project_service.py
    ├── templates/              # Jinja2 HTML templates
    └── static/
        ├── css/style.css
        ├── js/{script.js, figma.js, record.js}
        └── images/
```

---

## API Endpoints

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| GET, POST | `/register` | Create account |
| GET, POST | `/login` | Log in |
| GET | `/logout` | Log out |

### Projects

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Landing page |
| GET | `/dashboard` | List user projects |
| GET, POST | `/projects/create` | Create project |
| POST | `/project/<id>/delete` | Delete project |
| GET | `/project/<id>` | Project hub |

### Knowledge & Recordings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/project/<id>/knowledge` | List knowledge entries |
| GET, POST | `/project/<id>/knowledge/new` | Add knowledge |
| GET, POST | `/project/<id>/record` | Browser recording + transcription |
| GET | `/project/<id>/recordings` | List recordings |
| POST | `/recording/<id>/delete` | Delete recording |
| GET | `/uploads/recordings/<filename>` | Serve recording file |

### Figma (JSON API)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/project/<id>/figma` | Figma UI page |
| POST | `/project/<id>/figma/connect` | Connect Figma file |
| POST | `/project/<id>/figma/sync` | Sync and diff Figma file |

### Insights & Timeline

| Method | Path | Description |
|--------|------|-------------|
| GET | `/project/<id>/insights` | List AI insights |
| GET | `/project/<id>/timeline` | Activity timeline |
| POST | `/project/<id>/insights/<id>/acknowledge` | Acknowledge insight |
| POST | `/project/<id>/insights/<id>/dismiss` | Dismiss insight |
| POST | `/project/<id>/insights/<id>/snooze` | Snooze insight (7 days) |

### Handoff & Constraints

| Method | Path | Description |
|--------|------|-------------|
| GET, POST | `/project/<id>/constraints` | Manage engineer constraints |
| POST | `/project/<id>/constraints/<id>/delete` | Delete constraint |
| GET | `/project/<id>/handoff` | Handoff page + Figma embed |
| POST | `/project/<id>/handoff/finalize` | Generate handoff spec |

### GitHub

| Method | Path | Description |
|--------|------|-------------|
| GET, POST | `/project/<id>/github` | Connect repo |
| POST | `/project/<id>/github/check` | Manually check a PR |
| POST | `/webhooks/github` | GitHub webhook (no auth) |

All `/project/*` routes require login and scope data to the current user.

---

## External Services Setup

### Figma

1. Go to **Figma → Settings → Security → Personal access tokens**.
2. Generate a token from an account with a **Full** or **Dev** seat (Viewer/Collab seats are limited to ~6 file requests/month).
3. Add to `.env` as `FIGMA_API_KEY`.
4. Ensure the token owner has access to the Figma file you want to connect.

### Otari AI

1. Sign up at [otari.ai](https://otari.ai).
2. Generate an API key (`tk_...`) from the API Keys tab.
3. Pick an available model from the Models tab (managed models start with `mzai:`).
4. Add `OTARI_API_KEY` and `OTARI_MODEL` to `.env`.

### Gradium

1. Get an API key from [gradium.ai](https://gradium.ai).
2. Add to `.env` as `GRADIUM_API_KEY`.
3. Install **ffmpeg** and update the path in `app/services/audio_converter.py` if needed.

### GitHub

1. Create a PAT at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` read access.
2. Add to `.env` as `GITHUB_TOKEN`.
3. (Optional) Configure a webhook on your repo:
   - **Payload URL:** `https://your-domain/webhooks/github`
   - **Events:** Pull requests
   - **Secret:** same value as `GITHUB_WEBHOOK_SECRET`

---

## Troubleshooting

### Figma: `429 Too Many Requests`

Figma rate-limits API calls. Common fixes:

- Use a **Full/Dev seat** token, not Viewer/Collab.
- Wait 60+ seconds before retrying.
- Don't click Connect repeatedly.

The app auto-retries twice using Figma's `Retry-After` header.

### Otari: model not found (404)

Check your model name in the Otari dashboard Models tab. Copy the exact name into `OTARI_MODEL`. Run `python test_otari.py` to verify.

### Recording transcription fails

- Ensure `GRADIUM_API_KEY` is set.
- Ensure **ffmpeg** is installed and the path in `audio_converter.py` is correct for your machine.
- Check that the browser supports `MediaRecorder` (Chrome/Edge recommended).

### GitHub PR check returns empty

- Ensure `GITHUB_TOKEN` has access to the repo.
- The PR must touch UI/style files (`.css`, `.tsx`, `.jsx`, `components/`, etc.) to trigger design analysis.

### Database errors on first run

```bash
flask db upgrade
```

If migrations fail, delete `instance/database.db` and run `flask db upgrade` again (development only).

---

## Technical Documentation

For architecture diagrams, data model relationships, service layer details, and step-by-step flow descriptions, see:

**[docs/TECHNICAL.md](docs/TECHNICAL.md)**

---

## License

Built for the RAISE Summit hackathon.

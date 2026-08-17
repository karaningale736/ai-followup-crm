# AI Client Follow-Up & CRM Automation System

Automates a manual client follow-up workflow: given a client's stage, contact
history, agreement status, and meeting status, the system deterministically
decides whether a follow-up is due, which template category to use, what
tone to use, and what the priority is -- then uses AI *only* to personalize
the already-approved template text. The AI never decides business logic.

```
Client Data → Stage Analysis → Follow-Up Timing → Next Action →
Template Selection → AI Personalization → Human Review → Send → History
```

## What's implemented (backend)

- **Deterministic follow-up engine** (`app/services/followup_engine.py`) --
  working-day-based timing for Follow-Up 1/2/3, agreement-stage logic
  (sent/opened/pending-signature), meeting logic, participation-pending
  logic, budget-objection handling (never invents an offer), and a terminal-
  stage guard (declined/signed/completed/do-not-contact stop all follow-ups).
- **Working-day calculator** (`app/core/workdays.py`) -- Mon-Fri by default,
  with a `holidays: set[date]` parameter so a holiday calendar can be added
  later without touching the engine.
- **AI provider abstraction** (`app/services/ai_provider.py`) -- a
  `MockAIProvider` (deterministic, no network, used automatically when
  `GEMINI_API_KEY` is unset and always in tests) and a `GeminiAIProvider`
  using the official `google-genai` SDK. Both only fill in an
  already-selected template and classify replies -- neither picks the
  template or changes CRM state.
- **SQLAlchemy models** for Client, EmailHistory, FollowUp, Meeting,
  Agreement, Template, User.
- **FastAPI routers**: clients (CRUD + CSV import/export + timeline),
  followups (analyze/generate/due/overdue), dashboard, templates (CRUD),
  emails (draft/send/history, mock or SMTP), meetings, agreements,
  response classification.
- **Seed data**: 17 fictional clients across every stage, 20 templates (one
  per category from the workflow), in `backend/seed/`.
- **31 pytest tests** covering working-day math, the follow-up engine
  (timing, terminal stages, budget objections, agreement states), the mock
  AI provider, and the API endpoints (CRUD, CSV import, dashboard,
  agreements, meetings, email sending, response classification).

## What's NOT built yet (honesty about scope)

The original spec also asked for a full React/TypeScript/Tailwind frontend,
Docker Compose with Postgres, Alembic migrations, and 5 documentation files.
Those are substantial additional work (a real SaaS-grade frontend alone is
typically its own multi-day project) and are **not** included in this pass
to avoid producing a shallow, half-working version of all of it. The backend
above is real and testable; say the word and I'll build the frontend next,
screen by screen, on top of this API.

## Running the backend locally (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m seed.seed_all
uvicorn app.main:app --reload
```

## Running the backend locally (macOS/Linux)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m seed.seed_all
uvicorn app.main:app --reload
```

API docs will be at `http://localhost:8000/docs`.

## Running tests (no API key required -- uses the mock AI provider)

```bash
cd backend
pytest -v
```

## Environment variables (`backend/.env`)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Defaults to local SQLite; swap for a Postgres URL in production |
| `GEMINI_API_KEY` | If unset, the app automatically falls back to the mock AI provider -- everything still works |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` / `SMTP_FROM_EMAIL` | Optional; if `SMTP_HOST` is unset, `/api/emails/send` mock-sends and still records history |
| `IMAP_HOST` / `IMAP_PORT` / `IMAP_USERNAME` / `IMAP_PASSWORD` / `IMAP_MAILBOX` / `IMAP_USE_SSL` | Optional inbound mailbox settings. When configured, `/api/emails/inbox/sync` loads your inbox and creates `INBOUND` / `REPLY_REQUIRED` records for new messages |
| `SECRET_KEY` | Placeholder for future auth |
| `FRONTEND_URL` | Used for CORS |

## Connecting your own mailbox

To connect your own Gmail or Outlook inbox to this CRM:

1. In `backend/.env`, add your mailbox credentials:

```env
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USERNAME=you@gmail.com
IMAP_PASSWORD=your-app-password
IMAP_MAILBOX=INBOX
IMAP_USE_SSL=true
```

2. Start the backend and sync the inbox:

```bash
cd backend
uvicorn app.main:app --reload
```

3. Call the API endpoint:

```bash
curl -X POST http://localhost:8000/api/emails/inbox/sync \
  -H "Content-Type: application/json" \
  -d '{
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "username": "you@gmail.com",
    "password": "your-app-password",
    "mailbox": "INBOX",
    "use_ssl": true
  }'
```

4. Review the reply-needed queue:

```bash
curl http://localhost:8000/api/emails/inbox/notifications
```

This endpoint returns inbound emails that need a human response. The app records them as `INBOUND` with a `REPLY_REQUIRED` status and links them to the matching client when the sender email matches a stored client record.

## Key design rule

The AI is downstream of the business logic, never upstream of it:

```
Database → Deterministic Business Logic → Follow-Up Engine →
Next Action Engine → Template Selection → AI Personalization →
Human Review → Email
```

The AI cannot invent prices, discounts, dates, meeting times, or company
facts -- the mock provider enforces this by leaving `[MISSING: field]`
markers rather than guessing, and the Gemini provider is prompted with the
same constraint.

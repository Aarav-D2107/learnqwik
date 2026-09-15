# LearnQwik

**Learn what you don't know you don't know.**

LearnQwik measures what a student actually knows, works out the specific gap,
teaches that gap, and then proves — with a number — that it closed.

Built for the **Quality Education** track.

---

## Contents

- [What it does](#what-it-does)
- [Why it's different](#why-its-different)
- [Is the AI real?](#is-the-ai-real)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Quick start](#quick-start)
- [Full setup](#full-setup)
- [Environment variables](#environment-variables)
- [The learning loop](#the-learning-loop)
- [How scoring works](#how-scoring-works)
- [How mastery works](#how-mastery-works)
- [How recommendations work](#how-recommendations-work)
- [How the roadmap personalizes](#how-the-roadmap-personalizes)
- [The document pipeline](#the-document-pipeline)
- [API overview](#api-overview)
- [Database schema](#database-schema)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security](#security)
- [What's real and what isn't](#whats-real-and-what-isnt)
- [Known limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

---

## What it does

1. **Assess** — timed, fullscreen-monitored quizzes, scored on the server with
   difficulty weighting.
2. **Diagnose** — mastery per topic, weak-area detection, before/after tracking.
3. **Learn** — 5 subjects, 30 topics of written content with code examples,
   common mistakes and key points.
4. **Ask** — an AI Tutor that knows the topic you're on *and* how well you're
   doing at it.
5. **Upload** — your own PDFs, slides and notes get parsed, visually analyzed,
   indexed, summarized and turned into quizzes.
6. **Reassess** — retake, and see the delta.
7. **Improve** — the roadmap reorders itself around what you still don't know.

## Why it's different

Most learning apps serve everyone the same course and call a progress bar
"personalization". LearnQwik:

- **Never shows a personalized roadmap it hasn't earned.** Before your first
  assessment it says `DEFAULT ROADMAP` outright. The contrast with the "after"
  is the point.
- **Weights questions by difficulty.** Getting the Hard ones right is worth more
  than getting the Easy ones right. 33% raw can be 44% weighted — or 22%.
- **Blends mastery over time** — 70% your latest attempt, 30% your history — so
  one lucky quiz doesn't declare you an expert.
- **Explains every recommendation.** Five weighted factors, each visible.
- **Proves improvement.** "32% → 71%. Up 39 percentage points. You moved from
  Weak to Developing."
- **Uses vision on your documents.** A lecture slide that's one ER diagram has
  almost no extractable text. Text-only RAG fails on exactly the material
  students most need explained.

## Is the AI real?

Yes, and there are four ways to check without taking my word for it:

1. **No fallback answer exists.** With no `AI_API_KEY` the tutor returns
   `503 AI_NOT_CONFIGURED`. A scripted chatbot would answer anyway.
   Enforced by `test_no_canned_ai_response_is_ever_returned`.
2. **The prototype's fake tutor is deleted.** `tools/audit.py` fails the build
   if `generateTutorReply`, `"Local demo"`, or an `alert()`-based response path
   reappears.
3. **Ask it something unscripted** — *"explain checked exceptions using only
   cooking metaphors, in exactly four sentences."* No keyword table does that.
4. **Watch the call.** `services/ai_provider.py` POSTs to
   `api.anthropic.com/v1/messages` or `api.openai.com/v1/chat/completions`.

The tutor is given the topic's real learning content, your measured mastery
percentage and band, your weak topics across the subject, and the conversation
so far. That's why it's more useful than pasting the question into a generic
chatbot — it knows what you got wrong.

Full detail: **[docs/AI_PIPELINE.md](docs/AI_PIPELINE.md)**.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Static HTML/CSS/JS on Vercel | The hand-written neomorphic CSS *is* the product's identity. A hash-routed SPA covers an authenticated app fine. See [ARCHITECTURE.md](docs/ARCHITECTURE.md). |
| Backend | FastAPI (Python 3.12) on Render | Async, automatic OpenAPI docs, excellent PDF/vision library support |
| Database | Supabase Postgres | Managed, with RLS and auth in the same product |
| Auth | Supabase Auth, backend-proxied | The browser holds no Supabase credential at all |
| Storage | Supabase Storage (private bucket) | Owner-scoped policies |
| AI | Anthropic or OpenAI | Pluggable via `AI_PROVIDER` |
| Documents | PyMuPDF, python-pptx, python-docx | Real parsing, not a text dump |

## Project structure

```
learnqwik/
├── backend/
│   ├── main.py                 FastAPI app, CORS, error handlers
│   ├── config.py               every setting, env-overridable
│   ├── db.py                   the ONLY place the service-role key is used
│   ├── deps.py                 auth, rate limits, quiz lockout
│   ├── errors.py               structured errors, no traceback leaks
│   ├── routes/                 thin HTTP layer
│   ├── services/               all the logic
│   ├── schemas/                Pydantic request/response models
│   ├── tests/                  87 offline tests + API/AI tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── css/style.css           unchanged from the prototype
│   ├── js/env.js               GENERATED by build.js
│   ├── js/auth.js              session + token refresh
│   ├── js/api.js               the single API client
│   ├── js/app.js               routing and views
│   ├── js/data.js              curriculum source → database/seed.sql
│   ├── build.js                injects API_BASE_URL at build time
│   └── vercel.json
├── database/
│   ├── schema.sql              tables, indexes, RLS, storage policies
│   └── seed.sql                GENERATED from js/data.js
├── tools/
│   ├── generate-seed.js        data.js → seed.sql
│   ├── selfcheck.py            87 tests, zero dependencies
│   └── audit.py                no fake AI, no leaked secrets
├── docs/
└── render.yaml
```

## Quick start

Prerequisites: **Python 3.12+**, **Node 18+**, a **Supabase** project, and an
**Anthropic or OpenAI API key**.

```bash
# verify the core logic works before installing anything
python3 tools/selfcheck.py        # expect: passed: 87  failed: 0
```

---

## Full setup

### 1. Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. **SQL Editor** → paste all of `database/schema.sql` → **Run**.
3. New query → paste all of `database/seed.sql` → **Run**.
4. Verify the curriculum loaded:
   ```sql
   select (select count(*) from subjects)  as subjects,
          (select count(*) from topics)    as topics,
          (select count(*) from questions) as questions,
          (select count(*) from resources) as resources;
   ```
   Expect **5 / 30 / 100 / 14**.
5. **Storage** → confirm the private `learnqwik-documents` bucket exists.
6. **Settings → API** → copy your Project URL, `anon` key, and `service_role` key.

> **For a fast demo**, disable email confirmation:
> Authentication → Providers → Email → uncheck *Confirm email*.
> Otherwise every signup needs an inbox round-trip.

### 2. Backend

**macOS / Linux**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# edit .env — see the table below
uvicorn main:app --reload --port 8000
```

**Windows (PowerShell)**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
# edit .env — see the table below
uvicorn main:app --reload --port 8000
```

Check it:
```bash
curl http://localhost:8000/health
```
```json
{ "status": "healthy", "service": "learnqwik-api",
  "checks": { "database": "ok", "ai_provider": "configured", "storage": "ok" } }
```

Interactive API docs: <http://localhost:8000/docs>

If PowerShell blocks the activate script:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Frontend

No build step is needed for local development — `js/env.js` already points at
`http://localhost:8000`.

```bash
cd frontend
python3 -m http.server 3000      # or: npx serve -l 3000
```

Open <http://localhost:3000>.

**Do not open `index.html` directly via `file://`** — the browser will block the
API requests as cross-origin.

If your backend runs somewhere else:
```bash
cd frontend
API_BASE_URL=http://localhost:9000 node build.js
```

---

## Environment variables

### Backend (`backend/.env`, and Render)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `SUPABASE_URL` | **yes** | — | `https://xxxx.supabase.co` |
| `SUPABASE_ANON_KEY` | **yes** | — | Used for signup/login/refresh |
| `SUPABASE_SERVICE_ROLE_KEY` | **yes** | — | **Backend only. Never ship this.** |
| `AI_PROVIDER` | no | `anthropic` | `anthropic` or `openai` |
| `AI_API_KEY` | **yes** | — | Without it, AI endpoints return 503 |
| `TEXT_MODEL` | no | `claude-sonnet-4-6` | |
| `VISION_MODEL` | no | `claude-sonnet-4-6` | Must support images |
| `FRONTEND_URL` | **yes in prod** | `http://localhost:3000` | Exact origin, no trailing slash |
| `EXTRA_CORS_ORIGINS` | no | — | Comma-separated, for preview deploys |
| `ENVIRONMENT` | no | `development` | `production` disables localhost CORS |
| `STORAGE_BUCKET` | no | `learnqwik-documents` | |
| `MAX_UPLOAD_SIZE_MB` | no | `20` | |
| `MAX_VISION_PAGES` | no | `12` | Caps cost per document |
| `SECONDS_PER_QUESTION` | no | `60` | |
| `MAX_FULLSCREEN_VIOLATIONS` | no | `3` | |
| `USE_EMBEDDINGS` | no | `false` | `true` needs pgvector enabled |
| `RATE_LIMIT_AI_PER_MINUTE` | no | `20` | |
| `RATE_LIMIT_UPLOAD_PER_HOUR` | no | `30` | |

### Frontend (Vercel)

| Variable | Required | Notes |
|---|---|---|
| `API_BASE_URL` | **yes** | Your Render URL, no trailing slash |

That's the only one. **No Supabase keys are needed in the browser** — auth is
proxied through the backend, so no credential is exposed client-side at all.

---

## The learning loop

```
Assess ──► Diagnose ──► Learn ──► Practice ──► Reassess ──► Improve
   ▲                                                           │
   └───────────────────────────────────────────────────────────┘
```

`POST /api/quiz/{id}/complete` runs most of it in one request: score → mastery →
persist → compare → recommend → regenerate roadmap → version → diff → explain →
return. The frontend renders the response and computes nothing.

## How scoring works

Difficulty-weighted, server-side:

| Difficulty | Weight |
|---|---|
| Easy | 1.0 |
| Medium | 1.5 |
| Hard | 2.0 |

```
weighted % = (sum of weights of correct answers / sum of all weights) × 100
```

Nine questions, 3 of each difficulty. Get the 3 Easy right and nothing else:
**33% raw, 3.0/13.5 = 22% weighted**. Get the 3 Hard ones instead: still 33%
raw, but **6.0/13.5 = 44% weighted**.

The raw percentage is shown too, because hiding it would feel like a trick.

## How mastery works

```
first attempt:  mastery = weighted score
after that:     mastery = 0.7 × latest + 0.3 × previous mastery
```

Recent performance dominates, but one good day doesn't erase a history.

| Range | Band |
|---|---|
| 0–39 | Weak |
| 40–59 | Struggling |
| 60–79 | Developing |
| 80–100 | Mastered |

## How recommendations work

Five weighted factors, all visible in the API response:

| Factor | Weight | What it rewards |
|---|---|---|
| Topic relevance | 0.40 | Material for the topic you're weak in |
| Difficulty match | 0.20 | Easy when you're at 30%, Hard when you're at 90% |
| Gap urgency | 0.15 | The bigger the gap, the higher the priority |
| Quality | 0.15 | Higher-rated resources |
| Time fit | 0.10 | Shorter material when the gap is large |

Deterministic and explainable — no model involved. Every recommendation carries
a `reason` string and a `components` breakdown.

## How the roadmap personalizes

Two states, and the app is honest about which one you're in.

**Default** — before any assessment. Curriculum order. Labelled `DEFAULT ROADMAP`.

**Personalized** — after an assessment. Ordered weakest-measured-mastery first,
with unassessed topics ranking above strong ones, prerequisites pulled ahead of
their dependents, and mastered topics sinking to the end as review. A
**Reassess** step is inserted for weak topics.

The **backend decides the order**. The AI writes the step titles and the
per-student reasoning. Every `topic_id` and `resource_id` it returns is
validated against the database; if it invents one, the response is rejected,
retried once, and then replaced by a deterministic planner that is *still
personalized*. If the model claims you're at 99% on a topic measured at 32%,
the measured number wins.

Each regeneration is versioned, and the results screen shows a real diff against
the previous version.

Full detail: **[docs/ROADMAP_PERSONALIZATION.md](docs/ROADMAP_PERSONALIZATION.md)**.

## The document pipeline

```
upload → extract text → classify each page → vision on the pages that need it
       → build understanding → chunk + index → ready
```

Page classification decides where the vision model is spent:

| Quality | Meaning | Vision? |
|---|---|---|
| `text_rich` | plenty of text, no significant images | no |
| `sparse` | very little text — probably diagrams | **yes** |
| `scanned` | no text layer at all | **yes** |
| `mixed` | substantial text *and* images | **yes** |
| `empty` | nothing | skipped |

Capped at `MAX_VISION_PAGES`, prioritising `scanned` > `sparse` > `mixed`, and
cached by content hash. Text chunks and vision chunks stay separate with page
provenance, so *"explain the diagram on page 8"* retrieves the page-8 vision
chunk rather than whatever shares the most keywords.

The progress stages in the UI reflect work that has actually completed. Nothing
is on a timer.

## API overview

32 endpoints. Full reference: **[docs/API.md](docs/API.md)**. Interactive docs
at `/docs`.

| Group | Endpoints |
|---|---|
| System | `/health`, `/api/config` |
| Auth | signup, login, refresh, logout, me |
| Curriculum | subjects, topics, topic detail |
| Assessment | start, answer, complete, reassess |
| Analytics | overview, topics, progress, improvement |
| Roadmap | get, recompute, versions |
| AI | tutor, greeting, explain, learning-plan |
| Documents | upload, list, status, delete, summary, quiz, grade, ask |

## Database schema

17 tables. The ones that matter:

| Table | Holds |
|---|---|
| `profiles` | user profile, created by trigger on signup |
| `subjects` / `topics` / `questions` / `resources` | the curriculum |
| `quiz_attempts` / `answers` | every attempt and every answer, with timings |
| `topic_mastery` | current mastery per user per topic |
| `progress_history` | the append-only record that powers before/after |
| `roadmap_versions` | every roadmap ever generated, with its mastery snapshot |
| `uploaded_files` / `document_pages` / `document_chunks` | the document pipeline |
| `document_summaries` / `generated_quizzes` | cached AI output |
| `ai_conversations` | tutor history |

Row Level Security is enabled on every user-owned table. Storage policies are
owner-only.

## Testing

```bash
python3 tools/selfcheck.py      # 87 tests, zero dependencies
cd backend && pytest -q          # full suite, needs requirements.txt
python3 tools/audit.py           # no fake AI, no leaked secrets
node tools/generate-seed.js      # curriculum integrity
```

`selfcheck.py` works because the scoring, mastery, recommendation, roadmap,
reassessment, parsing and retrieval modules have **zero third-party imports** —
deliberately. The logic that decides what a student is told about themselves
should be verifiable with no network and nothing installed.

Details and the manual QA checklist: **[docs/TESTING.md](docs/TESTING.md)**.

## Deployment

Supabase → Render → Vercel, in that order. Step by step:
**[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**.

```
Vercel (static)  ──►  Render (FastAPI)  ──►  Supabase + AI provider
   API_BASE_URL         FRONTEND_URL
```

> **Render free tier sleeps after ~15 minutes.** Hit `/health` a few minutes
> before demoing or the first request takes 30–60 seconds.

## Security

- The `service_role` key exists only on the backend, only in `db.py`.
- The browser holds **no** Supabase credential — not even the anon key.
- Tokens are verified against Supabase per request, not decoded locally, so
  revoked sessions stop working immediately.
- **A `user_id` in a request body is never read.** Identity comes from the
  token. There's a test for it.
- `correct_index` is stripped from every question served during a quiz.
- Scoring and mastery are server-side. Editing the JavaScript changes nothing.
- RLS on every user-owned table; owner-only storage policies.
- CORS is never `*` in production — enforced by a test.
- Uploads are checked by magic number, not just extension.
- Errors never include tracebacks or database internals.
- Rate limiting on AI and upload endpoints.

## What's real and what isn't

Being explicit, because "it's a demo" usually hides something.

**Real:**
- Supabase Postgres, Auth and Storage
- Difficulty-weighted scoring and mastery blending, server-side
- AI Tutor, roadmap generation, explanations, summaries, document quizzes —
  genuine model calls
- Vision analysis of diagram and scanned pages
- Document parsing (PyMuPDF / python-pptx / python-docx), chunking, retrieval
- Upload progress stages — actual pipeline state
- Before/after improvement, from stored history
- Roadmap versioning and diffing

**Honest about being limited:**
- **Fullscreen monitoring is not proctoring.** It's a nudge. The UI says so.
- Rate limiting is in-process — fine for one Render instance, not for a
  horizontally scaled deployment. Swap for Redis if that changes.
- Retrieval defaults to BM25 keyword search. Embeddings are implemented but off
  by default (`USE_EMBEDDINGS=false`) because pgvector needs enabling.
- Document processing runs in a FastAPI background task, not a job queue. Fine
  for a demo; a real deployment wants Celery or similar.
- The curriculum is 5 subjects / 30 topics / 100 questions — enough to
  demonstrate the loop, not a full syllabus.

**Not implemented:**
- OCR fallback when the vision model is unavailable
- Collaborative or classroom features
- Mobile apps
- Spaced-repetition scheduling

## Known limitations

- Free-tier Render cold starts (30–60s).
- The AI Tutor has no streaming — replies arrive whole.
- No end-to-end browser test suite (see [TESTING.md](docs/TESTING.md)).
- Very large PDFs (100+ pages) will be slow; vision is capped at 12 pages.
- Legacy `.ppt` and `.doc` are rejected with a message asking for the modern
  format.

## Troubleshooting

| Symptom | Cause |
|---|---|
| CORS error in console | `FRONTEND_URL` doesn't exactly match the browser origin — check trailing slash and http/https |
| 503 `SUPABASE_NOT_CONFIGURED` | `SUPABASE_URL` or `SUPABASE_SERVICE_ROLE_KEY` missing or has pasted whitespace |
| 503 `AI_NOT_CONFIGURED` | `AI_API_KEY` not set. Working as designed — it refuses rather than faking |
| Every request 404s | `API_BASE_URL` has a trailing slash → `//api/subjects` |
| Signup email never arrives | Supabase confirmation enabled + free-tier mailer limits. Disable confirmation for the demo |
| Subjects list is empty | `seed.sql` wasn't run |
| Render build fails on PyMuPDF | Set `PYTHON_VERSION=3.12.8` |
| `file://` page makes no requests | Serve over HTTP — `python3 -m http.server 3000` |

## Documentation

| Document | Covers |
|---|---|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and why each layer exists |
| [AI_PIPELINE.md](docs/AI_PIPELINE.md) | How the AI works and how to verify it's real |
| [ROADMAP_PERSONALIZATION.md](docs/ROADMAP_PERSONALIZATION.md) | Exactly how the roadmap adapts |
| [API.md](docs/API.md) | All 32 endpoints |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Supabase + Render + Vercel, step by step |
| [TESTING.md](docs/TESTING.md) | What's tested, what isn't, manual QA checklist |
| [DEMO.md](docs/DEMO.md) | Five-minute demo script |

---

Built for the Quality Education track.

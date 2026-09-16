# 🎓 LearnQwik

**Learn what you need, Improve what you don't.**

> 🚀 **Live Demo:** https://learnqwik.vercel.app  
> 🧠 **Core Loop:** Assess → Diagnose → Learn → Practice → Reassess → Improve

LearnQwik measures what a student actually knows, works out the specific gap, teaches that gap, and then proves — with a number — that it closed.

### ✨ At a glance

| 🧩 Capability | 💡 What LearnQwik does |
|---|---|
| 🎯 Personalized assessment | Measures topic-level understanding |
| 🔎 Gap diagnosis | Identifies weak concepts instead of only wrong answers |
| 🤖 AI Tutor | Explains concepts using the student's current context |
| 📚 Document intelligence | Turns PDFs, slides, and notes into usable learning material |
| 🗺️ Adaptive roadmap | Reorders learning around measured weaknesses |
| 📈 Reassessment | Measures before/after improvement numerically |
| 🧠 Mastery tracking | Maintains topic-level progress over time |

Built for the **Quality Education** track.

---

## 📑 Contents

- [🎯 What it does](#-what-it-does)
- [💡 Why it's different](#-why-its-different)
- [🤖 Is the AI real?](#-is-the-ai-real)
- [🛠️ Tech stack](#️-tech-stack)
- [🗂️ Project structure](#️-project-structure)
- [⚡ Quick start](#-quick-start)
- [🧰 Full setup](#-full-setup)
- [🔐 Environment variables](#-environment-variables)
- [🔄 The learning loop](#-the-learning-loop)
- [🧮 How scoring works](#-how-scoring-works)
- [🧠 How mastery works](#-how-mastery-works)
- [💡 How recommendations work](#-how-recommendations-work)
- [🗺️ How the roadmap personalizes](#️-how-the-roadmap-personalizes)
- [📄 The document pipeline](#-the-document-pipeline)
- [🔌 API overview](#-api-overview)
- [🗄️ Database schema](#️-database-schema)
- [🧪 Testing](#-testing)
- [🚀 Deployment](#-deployment)
- [🔒 Security](#-security)
- [✅ What's real and what isn't](#-whats-real-and-what-isnt)
- [❗ Known limitations](#known-limitations)
<a id="known-limitations"></a>
- [🩺 Troubleshooting](#-troubleshooting)
- [📚 Documentation](#-documentation)
- [🌟 LearnQwik in one sentence](#-learnqwik-in-one-sentence)
  
---

## 🎯 What it does

LearnQwik follows a complete personalized learning cycle:

1. **🎯 Assess** — timed, fullscreen-monitored quizzes, scored on the server with difficulty weighting.
2. **🔎 Diagnose** — mastery per topic, weak-area detection, before/after tracking.
3. **📚 Learn** — 5 subjects, 30 topics of written content with code examples, common mistakes and key points.
4. **🤖 Ask** — an AI Tutor that knows the topic you're on *and* how well you're doing at it.
5. **📄 Upload** — your own PDFs, slides and notes get parsed, visually analyzed, indexed, summarized and turned into quizzes.
6. **🔄 Reassess** — retake, and see the delta.
7. **📈 Improve** — the roadmap reorders itself around what you still don't know.

---

## 💡 Why it's different

Most learning apps serve everyone the same course and call a progress bar "personalization".

LearnQwik:

- **Never shows a personalized roadmap it hasn't earned.** Before your first assessment it says `DEFAULT ROADMAP` outright. The contrast with the "after" is the point.
- **Weights questions by difficulty.** Getting the Hard ones right is worth more than getting the Easy ones right. 33% raw can be 44% weighted — or 22%.
- **Blends mastery over time** — 70% your latest attempt, 30% your history — so one lucky quiz doesn't declare you an expert.
- **Explains every recommendation.** Five weighted factors, each visible.
- **Proves improvement.** Example: `32% → 71%. Up 39 percentage points.`
- **Uses vision on your documents.** A lecture slide that's one ER diagram has almost no extractable text. Text-only RAG fails on exactly the material students most need explained.

---

## 🤖 Is the AI real?

Yes, and there are four ways to check without taking my word for it:

1. **No fallback answer exists.** With no `AI_API_KEY` the tutor returns `503 AI_NOT_CONFIGURED`. A scripted chatbot would answer anyway. Enforced by `test_no_canned_ai_response_is_ever_returned`.

2. **The prototype's fake tutor is deleted.** `tools/audit.py` fails the build if `generateTutorReply`, `"Local demo"`, or an `alert()`-based response path reappears.

3. **Ask it something unscripted** — for example:  
   *"Explain checked exceptions using only cooking metaphors, in exactly four sentences."*

   No keyword table can reliably produce that kind of response.

4. **Watch the call.** `services/ai_provider.py` makes an actual model request through the configured OpenAI-compatible or supported provider API.

The tutor is given the topic's real learning content, your measured mastery percentage and band, your weak topics across the subject, and the conversation so far.

That's why it's more useful than pasting the question into a generic chatbot — it knows what you got wrong.

Full detail: **[docs/AI_PIPELINE.md](docs/AI_PIPELINE.md)**.

---

## 🛠️ Tech stack

| Layer | Choice | Why |
|---|---|---|
| 🖥️ Frontend | Static HTML/CSS/JS on Vercel | Lightweight SPA with custom neomorphic UI |
| ⚙️ Backend | FastAPI + Python 3.12 on Render | Async API, OpenAPI docs and strong document-processing support |
| 🗄️ Database | Supabase Postgres | Managed database with RLS |
| 🔐 Auth | Supabase Auth, backend-proxied | Browser holds no Supabase credential |
| 📦 Storage | Supabase Storage | Private owner-scoped document storage |
| 🤖 AI | Groq / OpenAI-compatible API | Fast, pluggable model inference |
| 📄 Documents | PyMuPDF, python-pptx, python-docx | Real document parsing and extraction |

---

## 🗂️ Project structure

    learnqwik/
    ├── backend/
    │   ├── main.py                 FastAPI app, CORS, error handlers
    │   ├── config.py               environment configuration
    │   ├── db.py                   database access
    │   ├── deps.py                 auth, rate limits, quiz lockout
    │   ├── errors.py               structured errors, no traceback leaks
    │   ├── routes/                 thin HTTP layer
    │   ├── services/               application logic
    │   ├── schemas/                Pydantic request/response models
    │   ├── tests/                  automated test suite
    │   ├── requirements.txt
    │   └── .env.example
    ├── frontend/
    │   ├── index.html
    │   ├── css/style.css
    │   ├── js/env.js               generated by build.js
    │   ├── js/auth.js              session + token refresh
    │   ├── js/api.js               single API client
    │   ├── js/app.js               routing and views
    │   ├── js/data.js              curriculum source
    │   ├── build.js                injects API_BASE_URL
    │   └── vercel.json
    ├── database/
    │   ├── schema.sql              tables, indexes, RLS, storage policies
    │   └── seed.sql                generated curriculum data
    ├── tools/
    │   ├── generate-seed.js
    │   ├── selfcheck.py
    │   └── audit.py
    ├── docs/
    └── render.yaml

---

## ⚡ Quick start

### Prerequisites

- **Python 3.12+**
- **Node 18+**
- A **Supabase** project
- An **AI provider API key**

The deployed demo uses **Groq through an OpenAI-compatible API**.

### Verify the core logic

    python3 tools/selfcheck.py

Expected:

    passed: 87
    failed: 0

---

## 🧰 Full setup

### 1. 🗄️ Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. Open **SQL Editor** and run `database/schema.sql`.
3. Run `database/seed.sql`.
4. Verify the curriculum:

       select (select count(*) from subjects)  as subjects,
              (select count(*) from topics)    as topics,
              (select count(*) from questions) as questions,
              (select count(*) from resources) as resources;

   Expected:

       5 / 30 / 100 / 14

5. Confirm the private `learnqwik-documents` storage bucket exists.
6. From **Settings → API**, configure the required project credentials for the backend.

> ⚠️ Never commit `.env` files or secret API keys to GitHub.

For a fast demo, email confirmation can be disabled in Supabase:

**Authentication → Providers → Email → Confirm email**

---

### 2. ⚙️ Backend

#### macOS / Linux

    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cp .env.example .env

Edit `.env` using the environment-variable table below.

Then:

    uvicorn main:app --reload --port 8000

#### Windows PowerShell

    cd backend
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install --upgrade pip
    pip install -r requirements.txt
    Copy-Item .env.example .env

Edit `.env`, then:

    uvicorn main:app --reload --port 8000

### Health check

    curl http://localhost:8000/health

Expected structure:

    {
      "status": "healthy",
      "service": "learnqwik-api",
      "checks": {
        "database": "ok",
        "ai_provider": "configured",
        "storage": "ok"
      }
    }

Interactive API documentation:

    http://localhost:8000/docs

If PowerShell blocks activation:

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

---

### 3. 🖥️ Frontend

No build step is needed for local development.

`js/env.js` points to:

    http://localhost:8000

Run:

    cd frontend
    python3 -m http.server 3000

Or:

    npx serve -l 3000

Open:

    http://localhost:3000

> ⚠️ Do not open `index.html` directly using `file://`.  
> Serve it through HTTP so API requests work correctly.

If the backend runs elsewhere:

    cd frontend
    API_BASE_URL=http://localhost:9000 node build.js

---

## 🔐 Environment variables

### Backend

| Variable | Required | Default | Notes |
|---|---|---|---|
| `SUPABASE_URL` | **yes** | — | Supabase project URL |
| `SUPABASE_ANON_KEY` | **yes** | — | Used for auth operations |
| `SUPABASE_SERVICE_ROLE_KEY` | **yes** | — | **Backend only. Never ship this.** |
| `AI_PROVIDER` | no | `anthropic` | Configured provider |
| `AI_API_KEY` | **yes** | — | Required for AI endpoints |
| `TEXT_MODEL` | no | provider-dependent | Text generation model |
| `VISION_MODEL` | no | provider-dependent | Vision-capable model |
| `FRONTEND_URL` | **yes in prod** | `http://localhost:3000` | Exact frontend origin |
| `EXTRA_CORS_ORIGINS` | no | — | Additional preview origins |
| `ENVIRONMENT` | no | `development` | Use `production` in deployment |
| `STORAGE_BUCKET` | no | `learnqwik-documents` | Private document bucket |
| `MAX_UPLOAD_SIZE_MB` | no | `20` | Upload size limit |
| `MAX_VISION_PAGES` | no | `12` | Vision processing cap |
| `SECONDS_PER_QUESTION` | no | `60` | Quiz timing |
| `MAX_FULLSCREEN_VIOLATIONS` | no | `3` | Fullscreen warning limit |
| `USE_EMBEDDINGS` | no | `false` | Requires pgvector when enabled |
| `RATE_LIMIT_AI_PER_MINUTE` | no | `20` | AI rate limit |
| `RATE_LIMIT_UPLOAD_PER_HOUR` | no | `30` | Upload rate limit |

### Frontend — Vercel

| Variable | Required | Notes |
|---|---|---|
| `API_BASE_URL` | **yes** | Public Render backend URL, without trailing slash |

Example:

    API_BASE_URL=https://learnqwik.onrender.com

> 🔒 No Supabase keys are needed in the browser.  
> Authentication is proxied through the backend.

---

## 🔄 The learning loop

    ┌──────────────┐
    │    ASSESS    │
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │   DIAGNOSE   │
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │     LEARN    │
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │   PRACTICE   │
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │  REASSESS    │
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │   IMPROVE    │
    └──────┬───────┘
           │
           └──────────────► next learning cycle

`POST /api/quiz/{id}/complete` runs most of this flow in one request:

    score
      ↓
    mastery
      ↓
    persist
      ↓
    compare
      ↓
    recommend
      ↓
    regenerate roadmap
      ↓
    version
      ↓
    diff
      ↓
    explain
      ↓
    return

The frontend renders the response and does not calculate the core learning logic itself.

---

## 🧮 How scoring works

Scoring is difficulty-weighted and performed server-side.

| Difficulty | Weight |
|---|---:|
| 🟢 Easy | 1.0 |
| 🟡 Medium | 1.5 |
| 🔴 Hard | 2.0 |

Formula:

    weighted % =
    (sum of weights of correct answers / sum of all weights) × 100

For example, with nine questions:

- 3 Easy
- 3 Medium
- 3 Hard

Getting only the three Easy questions correct:

    33% raw
    3.0 / 13.5 = 22% weighted

Getting only the three Hard questions correct:

    33% raw
    6.0 / 13.5 = 44% weighted

The raw percentage is also shown so the scoring remains transparent.

---

## 🧠 How mastery works

### First attempt

    mastery = weighted score

### Later attempts

    mastery = 0.7 × latest score + 0.3 × previous mastery

Recent performance dominates, while historical performance prevents one unusually good or bad quiz from completely changing the student's profile.

### Mastery bands

| Range | Band |
|---:|---|
| 0–39 | 🔴 Weak |
| 40–59 | 🟠 Struggling |
| 60–79 | 🟡 Developing |
| 80–100 | 🟢 Mastered |

---

## 💡 How recommendations work

Recommendations use five weighted factors:

| Factor | Weight | What it rewards |
|---|---:|---|
| 🎯 Topic relevance | 0.40 | Material for the topic you're weak in |
| 📊 Difficulty match | 0.20 | Appropriate challenge for current mastery |
| 🚨 Gap urgency | 0.15 | Larger knowledge gaps |
| ⭐ Quality | 0.15 | Higher-rated resources |
| ⏱️ Time fit | 0.10 | Shorter material when the gap is large |

The recommendation engine is deterministic and explainable.

Every recommendation includes:

- a `reason`
- a `components` breakdown
- the relevant topic
- the resource selected

No AI model is required to decide the core recommendation ranking.

---

## 🗺️ How the roadmap personalizes

LearnQwik has two roadmap states.

### 🟦 Default roadmap

Before any assessment:

    DEFAULT ROADMAP

The curriculum follows its normal order.

### 🟣 Personalized roadmap

After an assessment:

- Weak measured topics are prioritized.
- Unassessed topics rank above already-strong topics.
- Prerequisites can move ahead of their dependents.
- Mastered topics move toward the end as review.
- A **Reassess** step is inserted for weak topics.

The **backend decides the order**.

The AI can write step titles and per-student reasoning, but every returned `topic_id` and `resource_id` is validated against the database.

If the model invents an invalid identifier:

    model response
          ↓
       validate
          ↓
       retry once
          ↓
    deterministic personalized planner

Measured data wins over unsupported model claims.

For example, if a model claims:

    99% mastery

but the measured mastery is:

    32%

the measured value remains authoritative.

Every roadmap regeneration is versioned, and the results screen can show a real difference between versions.

Full detail:

**[docs/ROADMAP_PERSONALIZATION.md](docs/ROADMAP_PERSONALIZATION.md)**

---

## 📄 The document pipeline

LearnQwik does not treat every uploaded document as plain text.

    upload
       ↓
    extract text
       ↓
    classify each page
       ↓
    vision on pages that need it
       ↓
    build understanding
       ↓
    chunk + index
       ↓
    ready

### Page classification

| Quality | Meaning | Vision? |
|---|---|---|
| `text_rich` | Plenty of text, no significant images | ❌ |
| `sparse` | Very little text — probably diagrams | ✅ |
| `scanned` | No text layer | ✅ |
| `mixed` | Substantial text and images | ✅ |
| `empty` | Nothing useful | ⏭️ Skipped |

Vision processing is capped by `MAX_VISION_PAGES`.

Priority:

    scanned > sparse > mixed

Content is cached by content hash.

Text and vision chunks remain separate and preserve page provenance.

This means a question such as:

    "Explain the diagram on page 8."

can retrieve the page-8 vision chunk rather than relying only on keyword matching.

The progress stages shown in the UI correspond to actual pipeline states rather than arbitrary timers.

---

## 🔌 API overview

The backend exposes grouped endpoints for:

| Group | Examples |
|---|---|
| ❤️ System | `/health`, `/api/config` |
| 🔐 Auth | signup, login, refresh, logout, me |
| 📚 Curriculum | subjects, topics, topic detail |
| 📝 Assessment | start, answer, complete, reassess |
| 📊 Analytics | overview, topics, progress, improvement |
| 🗺️ Roadmap | get, recompute, versions |
| 🤖 AI | tutor, greeting, explain, learning-plan |
| 📄 Documents | upload, list, status, delete, summary, quiz, grade, ask |

Full reference:

**[docs/API.md](docs/API.md)**

Interactive API documentation:

    https://learnqwik.onrender.com/docs

---

## 🗄️ Database schema

LearnQwik uses **17 database tables**.

| Table | Holds |
|---|---|
| `profiles` | User profile |
| `subjects` / `topics` / `questions` / `resources` | Curriculum |
| `quiz_attempts` / `answers` | Attempts and answers |
| `topic_mastery` | Current mastery per topic |
| `progress_history` | Before/after learning history |
| `roadmap_versions` | Generated roadmap versions |
| `uploaded_files` / `document_pages` / `document_chunks` | Document pipeline |
| `document_summaries` / `generated_quizzes` | Cached AI output |
| `ai_conversations` | Tutor conversation history |

Row Level Security is enabled on user-owned tables.

Storage policies are owner-scoped.

---

## 🧪 Testing

Run the core self-check:

    python3 tools/selfcheck.py

Run the backend test suite:

    cd backend
    pytest -q

Run the security / fake-AI audit:

    python3 tools/audit.py

Regenerate curriculum seed data:

    node tools/generate-seed.js

The scoring, mastery, recommendation, roadmap, reassessment, parsing and retrieval modules are deliberately designed so their core logic can be verified without requiring network access.

Full testing documentation:

**[docs/TESTING.md](docs/TESTING.md)**

---

## 🚀 Deployment

### 🌐 Live application

> # 👉 https://learnqwik.vercel.app

### Production architecture

    ┌──────────────────────┐
    │   🌐 Vercel Frontend │
    └──────────┬───────────┘
               │
         API_BASE_URL
               │
               ▼
    ┌──────────────────────┐
    │   ⚙️ Render Backend  │
    │       FastAPI        │
    └──────┬─────────┬─────┘
           │         │
    ┌──────┘         └──────────┐
    ▼                           ▼
    ┌─────────────────┐   ┌─────────────────┐
    │ 🗄️ Supabase     │   │ 🤖 AI Provider  │
    │ DB/Auth/Storage │   │      Groq       │
    └─────────────────┘   └─────────────────┘

Deployment order:

    Supabase → Render → Vercel

Full deployment guide:

**[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**

### 🔗 Production URLs

**Frontend**

    https://learnqwik.vercel.app

**Backend**

    https://learnqwik.onrender.com

**API documentation**

    https://learnqwik.onrender.com/docs

> ⚠️ Render's free tier can sleep after inactivity. The first request after a cold start may take longer than normal.

---

## 🔒 Security

LearnQwik includes several security protections:

- 🔐 The `service_role` key exists only on the backend.
- 🖥️ The browser holds no Supabase credential.
- 🔑 Tokens are verified against Supabase per request.
- 👤 Identity comes from the authenticated token, not a client-supplied `user_id`.
- 📝 `correct_index` is stripped from quiz questions sent to the client.
- 🧮 Scoring and mastery calculations happen server-side.
- 🗄️ RLS protects user-owned database records.
- 📦 Storage policies are owner-only.
- 🌐 Production CORS is restricted.
- 📄 Uploads are checked by file signatures, not only extensions.
- 🚫 Errors do not expose tracebacks or database internals.
- ⏱️ AI and upload endpoints have rate limiting.

> 🔑 **Never commit `.env`, service-role keys, AI API keys, or other secrets to the repository.**

---

## ✅ What's real and what isn't

Being explicit, because "it's a demo" can hide important limitations.

### 🟢 Real

- Supabase Postgres, Auth and Storage
- Difficulty-weighted scoring and mastery blending
- AI Tutor with genuine model calls
- AI-generated roadmaps and explanations
- AI-generated summaries and document quizzes
- Vision analysis of diagrams and scanned pages
- Document parsing using PyMuPDF / python-pptx / python-docx
- Document chunking and retrieval
- Actual upload-processing stages
- Stored before/after improvement history
- Roadmap versioning and diffing

### 🟡 Honest limitations

- **Fullscreen monitoring is not proctoring.** It is a behavioral nudge.
- Rate limiting is in-process and suited to a single Render instance.
- Retrieval defaults to BM25 keyword search.
- Embeddings are implemented but disabled by default.
- Document processing runs as a FastAPI background task rather than a production job queue.
- The curriculum currently contains 5 subjects, 30 topics, 100 questions and 14 resources.

### 🔴 Not implemented

- OCR fallback when the vision model is unavailable
- Collaborative classroom features
- Native mobile applications
- Spaced-repetition scheduling

---

## ⚠️ Known limitations

- Render free-tier cold starts can take approximately 30–60 seconds.
- AI Tutor responses are not streamed.
- There is no complete end-to-end browser test suite yet.
- Very large PDFs can take longer to process.
- Vision processing is capped at 12 pages by default.
- Legacy `.ppt` and `.doc` formats are rejected in favor of modern formats.

---

## 🩺 Troubleshooting

| Symptom | Possible cause |
|---|---|
| ❌ CORS error | `FRONTEND_URL` does not exactly match the frontend origin |
| ❌ `503 SUPABASE_NOT_CONFIGURED` | Missing Supabase backend configuration |
| ❌ `503 AI_NOT_CONFIGURED` | `AI_API_KEY` is missing |
| ❌ Every API request returns 404 | `API_BASE_URL` may contain a trailing slash |
| 📧 Signup email never arrives | Supabase email confirmation or mailer limits |
| 📚 Subjects list is empty | `seed.sql` was not run |
| 🐍 Render build fails on PyMuPDF | Set `PYTHON_VERSION=3.12.8` |
| 🌐 `file://` page makes no requests | Serve the frontend over HTTP |

---

## 📚 Documentation

| Document | Covers |
|---|---|
| **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** | System design and architecture decisions |
| **[AI_PIPELINE.md](docs/AI_PIPELINE.md)** | AI pipeline and verification |
| **[ROADMAP_PERSONALIZATION.md](docs/ROADMAP_PERSONALIZATION.md)** | Adaptive roadmap logic |
| **[API.md](docs/API.md)** | API reference |
| **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** | Supabase + Render + Vercel deployment |
| **[TESTING.md](docs/TESTING.md)** | Tests and manual QA |
| **[DEMO.md](docs/DEMO.md)** | Five-minute hackathon demo script |

---

## 🌟 LearnQwik in one sentence

> **Don't just tell students what they got wrong — understand what they know, teach what they don't, and prove that they improved.**

### 🎓 Built for the Quality Education track.

**Assess → Diagnose → Learn → Practice → Reassess → Improve**

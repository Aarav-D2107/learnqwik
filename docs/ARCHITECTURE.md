# Architecture

## The shape of the system

```
┌──────────────────────────────┐
│  Browser (Vercel, static)    │
│  index.html · style.css      │
│  env.js → auth.js → api.js   │
│  → app.js                    │
│                              │
│  Holds: a session token,     │
│  UI preferences, and the     │
│  current quiz in memory.     │
│  Holds NO learning data.     │
└──────────────┬───────────────┘
               │  HTTPS + Bearer token
               ▼
┌──────────────────────────────┐
│  FastAPI (Render)            │
│                              │
│  routes/   thin HTTP layer   │
│  services/ all the logic     │
│  deps.py   auth + limits     │
│  db.py     the ONLY place    │
│            the service-role  │
│            key is used       │
└───┬──────────────────┬───────┘
    │                  │
    ▼                  ▼
┌─────────────┐  ┌──────────────┐
│  Supabase   │  │ AI provider  │
│  Auth       │  │ text+vision  │
│  Postgres   │  └──────────────┘
│  Storage    │
└─────────────┘
```

## The one rule

**The browser is never trusted with a number that matters.**

Scores, mastery percentages, weak-topic rankings, recommendation scores and
roadmap ordering are all computed on the server. The client sends *which option
was selected*; it never sends a score. `correct_index` is stripped from every
question the API serves during a quiz, so the answer key is not sitting in the
DOM waiting to be read out of devtools.

This is also why `js/data.js` is no longer loaded by `index.html`. In the
prototype it was the runtime data source and it contained every correct answer.
It is now the *authoring* source for `database/seed.sql` only.

## Why each layer exists

### `routes/` — HTTP and nothing else
Parse the request, call one service function, shape the response. No business
logic. This keeps the interesting code testable without spinning up a server,
which is what let the whole scoring/mastery/roadmap core be verified with
`python3 tools/selfcheck.py` and no dependencies at all.

### `services/` — the product
Split by what they *decide*, not by what table they touch:

| Module | Owns |
|---|---|
| `scoring_service` | difficulty-weighted scoring |
| `mastery_service` | recent/historical blending, bands, weak topics |
| `recommendation_service` | the five-factor explainable ranking |
| `roadmap_service` | default roadmap, priority order, AI output validation, diffing |
| `reassessment_service` | before/after comparison and update triggers |
| `ai_provider` | the provider abstraction (Anthropic / OpenAI) |
| `ai_service` | roadmap prompting, validation, repair, fallback |
| `tutor_service` | context assembly for the AI Tutor |
| `document_parser` | extraction and per-page quality classification |
| `vision_service` | page selection and vision analysis |
| `document_retriever` | chunking and hybrid retrieval |
| `summarizer` | grounded document summaries |
| `question_generator` | document-grounded quiz generation + validation |
| `document_service` | pipeline orchestration and status |
| `quiz_service` | the full attempt lifecycle |
| `catalog` | curriculum reads |

The first five have **zero third-party imports**. That's deliberate: the logic
that decides what a student is told about themselves should be verifiable
without a network connection.

### `db.py` — one door to the data
Every Postgres, Storage and Auth call goes through here. The service-role key
is used in exactly one module, so the blast radius of a mistake is one file.

## Authentication

Supabase Auth, **proxied through the backend**. The browser never holds a
Supabase credential — not even the anon key.

```
POST /api/auth/login  ──► backend ──► Supabase Auth
                      ◄──  {access_token, refresh_token, user}
```

The client stores the tokens and sends `Authorization: Bearer <token>`. The
backend verifies each token against Supabase (`deps.current_user`) rather than
decoding it locally, so a revoked session stops working immediately.

**A `user_id` in a request body is never read.** Identity comes from the token
or the request is rejected. There is a test for this
(`test_client_supplied_user_id_is_ignored`).

Row Level Security is on for every user-owned table as a second line of defence.

## The learning loop

```
Assess ──► Diagnose ──► Learn ──► Practice ──► Reassess ──► Improve
   ▲                                                           │
   └───────────────────────────────────────────────────────────┘
```

One request drives most of it. `POST /api/quiz/{id}/complete`:

1. score the attempt (difficulty-weighted)
2. blend into mastery (70% recent / 30% historical)
3. write `quiz_attempts` + `progress_history`
4. compare before/after
5. rank recommendations
6. regenerate the roadmap, version it, diff it
7. ask the AI to explain the result
8. return all of it in one response

The frontend renders that response. It computes nothing.

## Frontend: why still static HTML?

This was a deliberate trade, not an oversight.

The prototype's 448 lines of hand-written CSS *are* the product's identity —
the neomorphic shadows, the cyberpunk palette, the scanline overlay. Porting
that to Next.js during a hackathon risks the thing that makes LearnQwik look
like LearnQwik, in exchange for routing and SSR that a hash-router already
covers for an authenticated single-page app.

What was added instead: a real API client, real session handling with token
refresh, real loading and error states on every view, and build-time
configuration injection (`build.js` → `js/env.js`) so no URL is hard-coded.

Vercel serves it as static files. Deployment is a `git push`.

## Failure behaviour

| Failure | What happens |
|---|---|
| No AI credentials | Tutor returns HTTP 503 `AI_NOT_CONFIGURED` — never a canned reply |
| AI returns invalid JSON | One repair retry, then the deterministic fallback planner |
| AI invents a topic/resource ID | Rejected by validation, fallback used |
| AI provider down | Fallback roadmap; explanations degrade to a written summary |
| Vision model fails on a page | That page keeps its text; the document still completes |
| Supabase unreachable | `/health` reports `degraded`, routes return structured 503s |

The fallback roadmap is still **personalized** — it orders by measured mastery.
It never silently reverts to the default curriculum.

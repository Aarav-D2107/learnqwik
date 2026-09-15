# API reference

Base URL: `http://localhost:8000` (local) · `https://<your-service>.onrender.com` (production)

Interactive docs are served at **`/docs`** (Swagger) and **`/redoc`**.

## Authentication

All authenticated endpoints take a bearer token:

```
Authorization: Bearer <access_token>
```

Get one from `POST /api/auth/login`. The backend verifies every token against
Supabase — it does not decode it locally, so revoked sessions stop working
immediately.

**A `user_id` in a request body is never read.** Identity always comes from the
token.

## Error format

Every error — including validation failures and 500s — has the same shape:

```json
{ "error": "MACHINE_READABLE_CODE",
  "message": "A sentence a student can actually act on." }
```

Tracebacks and database internals are never included.

| Code | Status | Meaning |
|---|---|---|
| `NOT_AUTHENTICATED` | 401 | Missing or malformed token |
| `SESSION_EXPIRED` | 401 | Token rejected — refresh or sign in |
| `TUTOR_LOCKED_DURING_QUIZ` | 403 | Tutor is locked during an active assessment |
| `NOT_FOUND` / `DOCUMENT_NOT_FOUND` | 404 | No such resource, or not yours |
| `VALIDATION_ERROR` | 422 | Request body failed validation |
| `RATE_LIMITED` | 429 | Too many requests |
| `AI_NOT_CONFIGURED` | 503 | Backend has no `AI_API_KEY` |
| `AI_UNAVAILABLE` | 503 | The provider failed or timed out |
| `SUPABASE_NOT_CONFIGURED` | 503 | Backend has no database credentials |
| `INTERNAL_ERROR` | 500 | Unexpected — details are logged, not returned |

---

## System

### `GET /health`
No auth. Used by Render's health check.
```json
{ "status": "healthy", "service": "learnqwik-api",
  "checks": { "database": "ok", "ai_provider": "configured", "storage": "ok" } }
```
`status` is `degraded` if the database is unreachable. Secrets never appear here.

### `GET /api/config`
No auth. Non-secret runtime rules, so the frontend doesn't duplicate them.
```json
{ "seconds_per_question": 60, "max_fullscreen_violations": 3,
  "max_upload_size_mb": 20, "allowed_extensions": ["pdf","pptx","docx","txt","py",...],
  "ai_configured": true }
```

---

## Auth

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /api/auth/signup` | no | Create an account |
| `POST /api/auth/login` | no | Sign in |
| `POST /api/auth/refresh` | no | Exchange a refresh token |
| `POST /api/auth/logout` | yes | Revoke the session |
| `GET /api/auth/me` | yes | Current user |

**`POST /api/auth/signup`**
```json
{ "email": "student@college.edu", "password": "atleast8chars", "full_name": "Aisha Rahman" }
```
Returns tokens, or — if email confirmation is enabled in your Supabase project —
a `message` telling the student to check their inbox.

**`POST /api/auth/login`** → 
```json
{ "access_token": "...", "refresh_token": "...", "expires_in": 3600,
  "user": { "id": "uuid", "email": "...", "full_name": "..." } }
```

---

## Curriculum

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /api/subjects` | optional | All subjects. With a token, includes `mastery_pct` |
| `GET /api/subjects/{subject_id}/topics` | optional | Topics, with per-topic mastery when signed in |
| `GET /api/topics/{topic_id}` | optional | Full learning content |

`GET /api/topics/{topic_id}` returns the topic's `content` object (intro,
concepts, practical, examples, mistakes, important) plus the caller's mastery.
It **never** includes quiz answer keys.

---

## Assessment

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /api/quiz/start` | yes | Begin an attempt |
| `GET /api/quiz/{attempt_id}/questions` | yes | Re-fetch questions (resume) |
| `POST /api/quiz/{attempt_id}/answer` | yes | Save one answer |
| `POST /api/quiz/{attempt_id}/complete` | yes | Submit and score |
| `POST /api/assessment/reassess` | yes | Begin a targeted reassessment |

**`POST /api/quiz/start`**
```json
{ "subject_id": "java", "topic_id": "java-exceptions", "mode": "quiz" }
```
`mode` ∈ `quiz` | `reassess`. The **server** picks the questions. The response
omits `correct_index` entirely:
```json
{ "attempt_id": "uuid", "mode": "quiz",
  "subject": {...}, "topic": {...},
  "questions": [ { "id": "...", "question": "...",
                   "options": ["a","b","c","d"], "difficulty": "Medium" } ],
  "total_seconds": 300, "max_fullscreen_violations": 3 }
```

**`POST /api/quiz/{attempt_id}/answer`**
```json
{ "question_id": "java-exceptions-q3", "selected_index": 2, "response_time_ms": 8400 }
```
Saved as you go, so a crashed browser doesn't lose the attempt. Returns no
correctness — that would let the client build an answer key.

**`POST /api/quiz/{attempt_id}/complete`** — the big one.
```json
{ "fullscreen_violations": 1, "auto_submitted": false, "time_used_seconds": 247 }
```
Response contains the entire learning loop in one payload:
```json
{
  "score": { "raw_percentage": 40, "weighted_percentage": 33.3,
             "correct_count": 4, "incorrect_count": 5, "unanswered_count": 1,
             "time_used_seconds": 247,
             "difficulty_breakdown": { "Easy": {"correct":3,"total":3}, ... } },
  "mastery": { "mastery_pct": 33.3, "mastery_band": "Weak",
               "previous_mastery_pct": null, "delta": null },
  "comparison": { "before": null, "after": 33.3, "delta": null, "summary": "..." },
  "recommendations": [ { "title": "...", "type": "Article", "score_percent": 91,
                         "reason": "Matched to your 33% mastery." } ],
  "roadmap_updated": true,
  "roadmap": { "state": "personalized", "title": "...", "reason": "...", "steps": [...] },
  "roadmap_changes": { "added": [...], "removed": [...], "reordered": true },
  "explanation": "You're strong on the basics but ...",
  "review": [ { "question": "...", "options": [...], "selected_index": 1,
                "correct_index": 2, "explanation": "...", "difficulty": "Hard" } ]
}
```
The answer key appears here — after submission, which is the correct time.

---

## Analytics

| Endpoint | Auth | Returns |
|---|---|---|
| `GET /api/analytics/overview` | yes | Overall mastery, counts, weak topics, recent attempts |
| `GET /api/analytics/topics?subject_id=` | yes | Per-topic mastery for the knowledge map |
| `GET /api/analytics/progress?topic_id=` | yes | Mastery over time |
| `GET /api/analytics/improvement` | yes | Before/after pairs where a reassessment happened |

`overview` returns `has_data: false` with an `empty_state` message for a new
account, rather than zeros that look like failure.

---

## Recommendations & roadmap

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /api/recommendations` | yes | Ranked resources (`topic_id`, `limit`, `type`, `max_duration`) |
| `GET /api/roadmap?subject_id=` | yes | Current roadmap — `state` is `default` or `personalized` |
| `POST /api/roadmap/recompute` | yes | Force regeneration |
| `GET /api/roadmap/versions?subject_id=` | yes | Version history |

Every recommendation carries a `reason` and a `components` breakdown of the five
scoring factors, so nothing is a black box.

---

## AI

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /api/ai/tutor` | yes | The AI Tutor (topic or document grounded) |
| `GET /api/ai/tutor/greeting` | yes | Context-aware opening message |
| `POST /api/ai/explain` | yes | Explain a completed attempt |
| `POST /api/ai/learning-plan` | yes | Standalone plan generation |

**`POST /api/ai/tutor`**
```json
{ "message": "Why does my catch block never run?",
  "topic": "java-exceptions",
  "conversation": [ { "role": "user", "content": "..." } ],
  "document_id": null, "page_context": null }
```
```json
{ "reply": "...", "sources": [ { "page_number": 8, "source": "vision" } ] }
```

This is a real model call. With no `AI_API_KEY` it returns **503
`AI_NOT_CONFIGURED`** — never a scripted reply. Returns **403
`TUTOR_LOCKED_DURING_QUIZ`** while an assessment is in progress, enforced
server-side.

Rate limited to `RATE_LIMIT_AI_PER_MINUTE` (default 20) per user.

---

## Documents

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /api/uploads` | yes | Upload (multipart `file`) |
| `GET /api/uploads` | yes | Your documents |
| `GET /api/uploads/{file_id}` | yes | Document + per-page analysis |
| `GET /api/uploads/{file_id}/status` | yes | Live processing stage |
| `DELETE /api/uploads/{file_id}` | yes | Delete file, chunks and storage object |
| `POST /api/uploads/{file_id}/summary` | yes | Grounded summary |
| `POST /api/uploads/{file_id}/quiz` | yes | Generate a document quiz |
| `POST /api/uploads/{file_id}/quiz/{quiz_id}/grade` | yes | Grade it |
| `POST /api/uploads/{file_id}/ask` | yes | Ask about this document |

**`GET /api/uploads/{file_id}/status`** drives the real progress UI:
```json
{ "status": "analyzing_visuals",
  "stages": [
    { "key": "uploading", "label": "Uploading", "state": "done" },
    { "key": "extracting_text", "label": "Extracting text", "state": "done" },
    { "key": "analyzing_visuals", "label": "Analyzing visual content", "state": "active" },
    { "key": "building_understanding", "label": "Building document understanding", "state": "pending" },
    { "key": "indexing", "label": "Indexing material", "state": "pending" },
    { "key": "ready", "label": "Ready", "state": "pending" }
  ],
  "page_count": 24, "pages_analyzed": 7 }
```
These stages reflect work that has actually completed. Nothing is on a timer.

All document endpoints are owner-scoped: requesting someone else's `file_id`
returns 404, not 403, so the API doesn't confirm that the document exists.

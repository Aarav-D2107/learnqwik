# Testing

## The short version

```bash
# No dependencies needed at all — verifies the deterministic core
python3 tools/selfcheck.py            # 87 tests

# The full suite, once dependencies are installed
cd backend && pytest -q

# Repository hygiene: no fake AI, no leaked secrets
python3 tools/audit.py

# Curriculum integrity
node tools/generate-seed.js
```

## Why `selfcheck.py` exists

The modules that decide what a student is told about themselves — scoring,
mastery, recommendations, roadmap ordering, reassessment, parsing, retrieval —
are written with **zero third-party imports**.

That isn't an accident. It means they can be verified on any machine with
Python and nothing else: no pip, no network, no Supabase, no AI key.
`tools/selfcheck.py` supplies a minimal `pytest` shim and runs the *real* test
files in `backend/tests/`. Same assertions, no install step.

```
test_scoring.py        (7 tests)
test_mastery.py        (9 tests)
test_recommendations.py (8 tests)
test_roadmap.py       (22 tests)
test_reassessment.py   (9 tests)
test_documents.py     (32 tests)
──────────────────────────────────
passed: 87   failed: 0   skipped: 0
```

`test_documents.py` includes genuine round-trips: it builds a real `.docx` and a
real `.pptx` in memory and parses them back.

## The full suite

`test_api.py` and `test_ai_pipeline.py` need FastAPI and pytest installed. They
still make **no network calls** — Supabase is monkeypatched and the AI provider
is replaced by `MockAIProvider` from `conftest.py`.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

## What's actually covered

### Scoring
All-correct, all-wrong, unanswered questions, empty quizzes, truncated answer
arrays. The important one: **a Hard question is worth more than an Easy one**,
verified by scoring two attempts that are both 1/3 raw and asserting the
weighted scores differ.

### Mastery
The 70/30 recent/historical blend, clamping, all four band boundaries (39/40,
59/60, 79/80), delta tracking, weak-topic sorting.

### Recommendations
That the weights sum to 1.0, that difficulty targeting follows mastery, that
on-topic beats off-topic, that a weak student gets Easy material and a strong
one gets Hard, that every recommendation carries a reason, and that scores are
deterministic across runs.

### Roadmap
Both states. Priority ordering including the prerequisite guard. AI output
validation: hallucinated topic IDs, hallucinated resource IDs, empty steps,
non-object responses, absurd time estimates, unknown step kinds. And the
critical one — `test_ai_cannot_overwrite_mastery_numbers`, where the model
claims 99% for a topic measured at 32% and loses.

### Reassessment
The headline 32% → 71% scenario, regressions reported honestly, no-change,
first measurement, and the trigger rules including that 1-point noise does *not*
regenerate the roadmap.

### Documents
Extension validation, magic-number sniffing (a `.exe` renamed to `.pdf` is
caught), all five quality classifications and their vision routing, the vision
page budget, real DOCX/PPTX parsing, chunking with text and vision kept
separate, BM25 retrieval, page-reference extraction (`"the diagram on page 8"`),
cosine similarity, and strict question validation.

### API
Health and degraded health, that secrets never appear in any response, 401 on
anonymous and malformed tokens, **that a `user_id` in the body is ignored**,
request validation, the tutor lockout during an active quiz, rate limiting,
structured errors with no tracebacks, and that CORS never uses `*` in
production.

### AI pipeline
Valid AI roadmaps accepted; hallucinated IDs and provider errors falling back to
the deterministic planner; explanations degrading gracefully; JSON recovery from
markdown fences and surrounding prose; summary context assembly and budgets.

## What is *not* covered

Being straight about this:

- **No end-to-end browser test.** There is no Playwright/Cypress suite. The
  frontend is verified by `node --check` and by the manual smoke test in
  `DEPLOYMENT.md`.
- **No live AI integration test.** Every AI test uses `MockAIProvider`. A real
  model call costs money and is non-deterministic, so it is a manual step.
- **No live Supabase test.** `db.py` is mocked throughout. Schema correctness is
  verified by running `schema.sql` and `seed.sql` for real.
- **No load testing.**

## Manual verification checklist

Run after deploying. This is what a judge will click through.

- [ ] `/health` returns `healthy`
- [ ] Sign up, sign out, sign back in
- [ ] Subjects list shows 5 subjects, 30 topics
- [ ] Topic content renders (intro, concepts, code, mistakes)
- [ ] AI Tutor answers a question no keyword table could — *"explain inheritance using only cooking metaphors"*
- [ ] Roadmap before any quiz says `DEFAULT ROADMAP`
- [ ] Quiz enters fullscreen; exiting warns; three exits auto-submit
- [ ] Timer counts down and auto-submits at zero
- [ ] Results show weighted score ≠ raw score on a mixed-difficulty quiz
- [ ] Roadmap now says `PERSONALIZED ROADMAP` and leads with the weakest topic
- [ ] Reassess from the roadmap; results show before → after with a delta
- [ ] My Progress shows the knowledge map and measured improvement
- [ ] Upload a PDF with a diagram; the pipeline shows real stages
- [ ] Ask the document tutor about the diagram; the answer cites a page
- [ ] Generate a document quiz; questions reference the actual content
- [ ] Open the app in a second account — no data leaks between users

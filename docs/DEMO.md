# Demo script

Five minutes, in the order that makes the product make sense. The whole pitch is
one sentence: *LearnQwik finds out what you don't know, teaches you that
specific thing, and proves you learned it.*

**Before you start:** hit the backend `/health` URL to wake Render off its cold
start, and have a PDF with at least one diagram ready to upload.

---

### 0:00 — The problem (20s)

> "Every learning app gives everyone the same course. If you're already good at
> loops but terrible at exception handling, you still start at lesson one.
> LearnQwik measures what you actually know first."

Land on the homepage. The six-step loop under the hero — Assess → Diagnose →
Learn → Practice → Reassess → Improve — is the whole architecture in one line.

### 0:20 — The default roadmap (30s)

Sign in, open **Java**, click **View My Roadmap**.

> "No assessment yet, so this is just the standard curriculum. The app says so —
> it doesn't pretend to personalize before it has anything to personalize from."

Point at the `DEFAULT ROADMAP` label. **This contrast is the demo.** Judges need
to see the "before" to believe the "after".

### 0:50 — Assess (60s)

Open **Exception Handling** → **Take the Quiz**.

Show the fullscreen prompt, then briefly tab away to trigger the integrity
warning. Answer deliberately badly — get the Hard ones wrong.

> "Timed, fullscreen-monitored, and scored on the server. The browser never sees
> the answer key — it isn't in the page source."

### 1:50 — Diagnose (45s)

On the results screen:

- raw vs **weighted** score — *"Hard questions count double. 40% raw, 33% weighted."*
- the difficulty breakdown bars
- the AI explanation of what specifically went wrong
- the green **ROADMAP UPDATED** panel with its **WHAT CHANGED** diff

> "That diff is a real comparison against the stored previous version, not a
> message that always appears."

### 2:35 — The personalized roadmap (40s)

Click **See My Personalized Roadmap**.

> "Exception Handling is now step one — it was step four. Mastered topics moved
> to the end. And there's a **Reassess Me** step, because the roadmap's job
> isn't finished until it's proved the gap closed."

Point at `PERSONALIZED ROADMAP` and the priority bars.

### 3:15 — The AI Tutor (45s)

Open the topic and ask something no keyword table could answer:

> *"Explain checked vs unchecked exceptions using only cooking metaphors, in exactly four sentences."*

> "This is a real model call. It has the topic's actual learning content, my
> measured mastery — 33%, Weak — and my weak areas across the subject. It
> explains differently to me than to someone at 85%."

If asked whether it's really AI: with no API key configured this endpoint
returns `503 AI_NOT_CONFIGURED`. It errors rather than faking. See
`docs/AI_PIPELINE.md`.

### 4:00 — Prove improvement (45s)

Back to the roadmap → **Reassess Me** → answer well this time.

> "32% to 71%. Up 39 points. Weak to Developing. That's the whole product in one
> number — and it's measured, not claimed."

Then **My Progress**: knowledge map, measured improvement cards, weak topics.

### 4:45 — Study your own material (60s)

**Study Your Own Material** → drop in your PDF.

> "Watch the stages — these aren't a fake progress bar. Text extraction, then
> *visual* analysis: pages that are diagrams or scans go to a vision model,
> because a slide that's one ER diagram has almost no extractable text."

When it's ready, ask: *"Explain the diagram on page 4."*

> "It cites the page. It's answering from my actual lecture slides."

Then **Quiz Me** → questions generated from the document, each tagged with its
source page.

### 5:45 — Close (15s)

> "Assess, diagnose, teach, reassess, prove. Every number measured server-side
> and stored. The AI writes the explanations; it never decides your score."

---

## If something breaks

- **Cold start** — keep `/health` open in a tab and refresh it before you begin.
- **AI errors** — say it out loud: *"That's the system refusing to fake an
  answer when the provider is unreachable."* Then show the roadmap, which still
  works via the deterministic fallback.
- **Upload is slow** — a large PDF with many diagram pages means many vision
  calls. Use a 5–10 page file.
- **Total backend failure** — run `python3 tools/selfcheck.py` on screen. 87
  tests, no dependencies, proving the logic is real.

## Questions you will get

**"Is the AI real or a chatbot?"**
Real. `docs/AI_PIPELINE.md` has four ways to verify, including that it returns
503 rather than a canned reply when unconfigured.

**"What if the AI hallucinates a roadmap?"**
Every topic and resource ID is validated against the database. Invalid output is
retried once, then falls back to a deterministic planner — which is still
personalized by measured mastery, never the default curriculum.

**"Could a student cheat by editing the JavaScript?"**
The answer key is never sent to the browser during a quiz. Scoring and mastery
happen on the server. A `user_id` in a request body is ignored; identity comes
from the verified token.

**"Why isn't the frontend a React app?"**
Deliberate trade — see `docs/ARCHITECTURE.md`. The hand-written CSS *is* the
product's identity, and a hash-routed SPA covers what's needed. The engineering
went into the backend, where the actual product lives.

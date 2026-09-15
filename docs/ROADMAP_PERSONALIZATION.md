# Roadmap personalization

The judging question this answers: *how exactly does the roadmap change, and
can you prove it changed because of the assessment?*

## Two states, never more

### State 1 — Default
Shown to a student with no completed assessment in this subject. It is the
curriculum in its authored order.

```
1. Java Fundamentals
2. Object-Oriented Programming
3. Inheritance and Polymorphism
4. Exception Handling
5. Collections Framework
6. Multithreading
```

The UI labels it `DEFAULT ROADMAP` and says so plainly: *"Your personalized
roadmap will adapt after your first assessment."* No AI call is made. No
pretence of personalization before there is anything to personalize from.

### State 2 — Personalized
Generated the moment the first assessment completes, and regenerated on every
assessment after that.

## Worked example

A student assesses across Java and the backend measures:

| Topic | Mastery | Band |
|---|---|---|
| Java Fundamentals | 88% | Mastered |
| Object-Oriented Programming | 81% | Mastered |
| Inheritance and Polymorphism | 76% | Developing |
| **Exception Handling** | **32%** | **Weak** |
| Collections Framework | 55% | Struggling |
| Multithreading | 70% | Developing |

The roadmap becomes:

```
1. Exception Handling — Core Concepts        [LEARN]     30m
   You scored 32% here. This is your largest gap.
2. Try/Catch/Finally in Practice             [RESOURCE]  14m
3. Exception Handling Drills                 [PRACTICE]  20m
4. Reassess: Exception Handling              [REASSESS]   8m
   Prove the gap closed before moving on.
5. Collections Framework — Core Concepts     [LEARN]     30m
   55% — your second weakest area.
...
Mastered topics drop to the end as light review.
```

The UI labels this `PERSONALIZED ROADMAP`, states the version number, and shows
a **WHAT CHANGED** panel diffing it against the previous version.

## How the order is decided

`roadmap_service.build_priority_topics()` — deterministic, on the server:

1. **Weakest measured mastery first.** 32% outranks 55% outranks 76%.
2. **Unassessed topics rank after weak topics, before strong ones.** An unknown
   is a risk, but a *measured* 32% is a known emergency.
3. **Prerequisites are pulled ahead of their dependents.** If Collections
   depends on Exception Handling, Exception Handling is studied first even when
   the raw percentages would say otherwise. Tested by
   `test_prerequisite_is_pulled_ahead_of_its_dependent`.
4. **Mastered topics (80%+) sink to the end** as optional review.

The AI never decides this order. It receives it.

## What the AI actually contributes

It is given the measured priority list, the real topic list, the real resource
list, and the student's mastery numbers. It returns JSON: step titles, per-step
reasons written for this student, time estimates, and which real resources to
attach.

So the AI writes the *narrative*. The backend owns the *ordering*.

### Validation — every field is checked

| Check | On failure |
|---|---|
| Response is a JSON object | reject |
| `steps` is a non-empty list | reject |
| Every `topic_id` exists in this subject | reject |
| Every `resource_id` exists in the database | reject |
| `estimated_minutes` is 1–180 | clamped |
| `kind` ∈ learn/practice/resource/reassess | defaults to `learn` |
| `priority_topics[].mastery` | **overwritten with the measured value** |

On rejection: one repair attempt with the validation error fed back to the
model, then the deterministic fallback.

### The fallback is still personalized

This matters. When the AI is unavailable, the student does **not** get the
default curriculum back. `build_fallback_roadmap()` produces the same
weakest-first ordering with template-written reasons:

```
1. Exception Handling — Core Concepts   "Your mastery here is 32% (Weak). Start here."
2. Try/Catch/Finally in Practice
3. Reassess: Exception Handling
```

The only thing lost is the AI's phrasing. The UI marks it
`· deterministic planner` rather than pretending otherwise.

## Versioning and the diff

Every regeneration writes a row to `roadmap_versions` with the full roadmap, the
mastery snapshot that produced it, and the attempt that triggered it. Only one
row per (user, subject) is `is_current`.

`diff_roadmaps()` compares against the previous version and returns:

```json
{
  "added":   ["Exception Handling Drills", "Reassess: Exception Handling"],
  "removed": ["Multithreading — Core Concepts"],
  "reordered": true,
  "is_first_version": false
}
```

That's what the green **ROADMAP UPDATED** panel renders on the results screen.
It's a real diff of two stored versions, not a message that always appears.

## When regeneration is triggered

`reassessment_service.should_trigger_roadmap_update()`:

| Situation | Regenerate? |
|---|---|
| First ever attempt on a topic | yes |
| A reassessment | always |
| Mastery band changed (e.g. Weak → Struggling) | yes |
| Mastery moved ≥ 10 points | yes |
| Mastery moved 1–2 points | no — that's noise |

Regenerating on noise would make the "your roadmap updated" message
meaningless. So it doesn't.

## The demo moment

1. Assess Exception Handling, score badly → roadmap puts it first.
2. Study the topic, ask the AI Tutor about it.
3. Hit **Reassess Me** from step 4 of the roadmap.
4. Results show `32% → 71%`, `+39 pts`, *"You moved from Weak to Developing."*
5. The roadmap reorders — Exception Handling drops, Collections rises.
6. **My Progress** shows the before/after permanently.

Every number there was measured by the server and stored in Postgres.

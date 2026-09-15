"""
AI orchestration — builds prompts, calls the provider, hands raw output to the
validators. Deliberately thin: every number the AI sees is already final, and
every structure it returns is re-validated before it touches the database.
"""
import json
import logging

from services import roadmap_service
from services.ai_provider import (
    AIError,
    AINotConfiguredError,
    get_provider,
)

log = logging.getLogger("learnqwik.ai")

ROADMAP_SYSTEM = """You are the roadmap planner inside LearnQwik, a personalized learning platform.

You will be given a student's MEASURED mastery per topic, a list of valid topic IDs,
a list of valid resource IDs, and a deterministic priority ordering produced by
LearnQwik's scoring engine.

Your job is ONLY to:
  - order the plan into concrete study steps
  - write short, specific reasons a student would find motivating and honest
  - choose among the resource IDs you were given

You must NOT:
  - invent any topic_id or resource_id that was not supplied to you
  - change, recalculate or contradict any mastery percentage
  - recommend advanced material for a topic whose prerequisite is still weak

Write reasons in second person ("you"), one or two sentences, no filler.
Respond with a single JSON object and nothing else."""


def _roadmap_prompt(subject, topics, priorities, resources, mastery_by_topic,
                    previous_roadmap, trigger):
    topic_lines = []
    for t in sorted(topics, key=lambda x: x.get("position", 0)):
        row = mastery_by_topic.get(t["id"])
        pct = row.get("mastery_pct") if row else None
        topic_lines.append({
            "topic_id": t["id"],
            "name": t["name"],
            "curriculum_position": t.get("position"),
            "measured_mastery": pct,
            "assessed": pct is not None,
        })

    resource_lines = [{
        "resource_id": r["id"],
        "title": r["title"],
        "type": r.get("type"),
        "topic_id": r.get("topic_id"),
        "difficulty": r.get("difficulty"),
        "duration_minutes": r.get("duration_minutes"),
    } for r in resources]

    payload = {
        "subject": subject["name"],
        "topics": topic_lines,
        "deterministic_priority_order": priorities,
        "available_resources": resource_lines,
        "previous_roadmap_steps": [
            {"order": s.get("order"), "title": s.get("title"), "topic_id": s.get("topic_id")}
            for s in (previous_roadmap or {}).get("steps", [])
        ][:20],
        "trigger": trigger,
    }

    return (
        "Here is the student's current state:\n\n"
        + json.dumps(payload, indent=2)
        + """

Produce an updated learning plan as JSON with exactly this shape:

{
  "title": "Personalized <Subject> Roadmap",
  "reason": "One sentence naming the single biggest gap and why the plan changed.",
  "priority_topics": [
    {"topic_id": "<must be from the list above>", "reason": "why this ranks here"}
  ],
  "steps": [
    {
      "order": 1,
      "topic_id": "<must be from the list above>",
      "title": "Short imperative step title",
      "reason": "Why this step, now.",
      "estimated_minutes": 30,
      "kind": "learn" | "resource" | "practice" | "reassess",
      "resource_ids": ["<must be from available_resources, or empty>"]
    }
  ]
}

Rules for the plan:
  - Start with the weakest assessed topic. Include a reassessment step for it.
  - Interleave learning, a concrete resource, practice, then reassessment.
  - After the weak topics, resume the normal curriculum order.
  - Mastered topics go last; do not re-teach them.
  - Between 6 and 14 steps total."""
    )


async def generate_ai_roadmap(subject, topics, priorities, resources,
                              mastery_by_topic, previous_roadmap=None, trigger=None):
    """
    Returns (roadmap_dict, generated_by). Falls back to the deterministic
    planner on any AI failure or invalid output — the user always gets a real
    personalized plan.
    """
    fallback = lambda: roadmap_service.build_fallback_roadmap(
        subject, topics, mastery_by_topic, resources,
        trigger_topic_id=(trigger or {}).get("topic_id"),
    )

    try:
        provider = get_provider()
    except AINotConfiguredError:
        log.info("AI not configured — using deterministic roadmap planner.")
        return fallback(), roadmap_service.GENERATED_BY_FALLBACK

    prompt = _roadmap_prompt(subject, topics, priorities, resources,
                             mastery_by_topic, previous_roadmap, trigger)

    last_error = None
    for attempt in range(2):  # one repair retry
        try:
            raw = await provider.generate_structured_output(
                prompt if attempt == 0 else prompt + (
                    "\n\nYour previous response was rejected: %s\n"
                    "Return corrected JSON using only the IDs supplied above." % last_error
                ),
                system=ROADMAP_SYSTEM,
                max_tokens=3000,
            )
            return roadmap_service.validate_ai_roadmap(
                raw, subject, topics, resources, priorities
            ), roadmap_service.GENERATED_BY_AI
        except roadmap_service.RoadmapValidationError as exc:
            last_error = str(exc)
            log.warning("AI roadmap rejected by validator (attempt %d): %s", attempt + 1, exc)
        except AIError as exc:
            log.warning("AI roadmap generation failed: %s", exc.code)
            break

    return fallback(), roadmap_service.GENERATED_BY_FALLBACK


EXPLAIN_SYSTEM = """You are LearnQwik's assessment analyst. You are given a student's
already-calculated results. Never recalculate or dispute the numbers — explain what they
mean and what to do next. Be specific, honest and encouraging without flattery.
Three to five sentences, plain prose, no headings, no bullet points."""


async def explain_result(subject_name, topic_name, result, mastery, comparison=None,
                         missed_questions=None):
    """Natural-language reading of a finished attempt. Degrades to a deterministic
    explanation if AI is unavailable — never blocks the results screen."""
    try:
        provider = get_provider()
    except AINotConfiguredError:
        return deterministic_explanation(topic_name, mastery, result)

    payload = {
        "subject": subject_name,
        "topic": topic_name,
        "raw_score_percent": result.get("raw_percentage"),
        "difficulty_weighted_percent": result.get("weighted_percentage"),
        "difficulty_breakdown": result.get("difficulty_breakdown"),
        "unanswered": result.get("unanswered_count"),
        "current_mastery_percent": mastery.get("mastery_pct"),
        "mastery_band": mastery.get("mastery_band"),
        "before_after": comparison,
        "questions_missed": (missed_questions or [])[:6],
    }
    try:
        return await provider.generate_text(
            "Explain these assessment results to the student:\n\n" + json.dumps(payload, indent=2),
            system=EXPLAIN_SYSTEM,
            max_tokens=500,
        )
    except AIError:
        return deterministic_explanation(topic_name, mastery, result)


def deterministic_explanation(topic_name, mastery, result):
    pct = float(mastery.get("mastery_pct") or 0)
    breakdown = result.get("difficulty_breakdown") or {}
    hard = breakdown.get("Hard", {})
    if pct >= 80:
        base = ("Strong work — you're demonstrating solid command of %s. "
                "Consider moving on to the next topic." % topic_name)
    elif pct >= 60:
        base = ("You have a working understanding of %s, but points slipped on the harder "
                "questions, which usually means edge cases rather than fundamentals." % topic_name)
    elif pct >= 40:
        base = ("You're struggling with the core mechanics of %s. Revisit Key Concepts and "
                "Common Mistakes before your next attempt." % topic_name)
    else:
        base = ("%s is currently a weak area. Start again from the Introduction and Key "
                "Concepts — your roadmap has been reordered to rebuild it from the "
                "ground up." % topic_name)
    if hard.get("total") and hard.get("correct", 0) == 0:
        base += " You missed every Hard-difficulty question, which is where the weighted score lost the most ground."
    return base

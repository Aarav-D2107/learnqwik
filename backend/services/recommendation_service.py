"""
Recommendation engine — deterministic and explainable.

The AI never invents a recommendation score. This module is the source of
truth; the AI is only allowed to describe, in natural language, what this
engine already decided.

Port of `scoreResource` / `recommendForTopic` from the prototype.
"""
from config import RECOMMENDATION_WEIGHTS, IDEAL_DURATION_MINUTES

DIFFICULTY_ORDER = ["Easy", "Medium", "Hard"]


def target_difficulty(mastery_pct):
    """Which difficulty band a learner at this mastery should be working in."""
    pct = float(mastery_pct or 0)
    if pct < 60:
        return "Easy"
    if pct < 80:
        return "Medium"
    return "Hard"


def score_resource(resource, topic_id, mastery_pct, format_preference=None):
    """
    Returns (score, component_breakdown). Every component is 0..1 and the
    weights sum to 1.0, so the score is directly readable as a percentage.
    """
    w = RECOMMENDATION_WEIGHTS

    topic_relevance = 1.0 if resource.get("topic_id") == topic_id else 0.0

    desired = target_difficulty(mastery_pct)
    try:
        distance = abs(
            DIFFICULTY_ORDER.index(resource.get("difficulty", "Medium"))
            - DIFFICULTY_ORDER.index(desired)
        )
    except ValueError:
        distance = 1
    difficulty_match = 1.0 - (distance / 2.0)

    quality = float(resource.get("rating", 0) or 0) / 5.0

    if format_preference:
        format_score = 1.0 if resource.get("type") == format_preference else 0.4
    else:
        # No preference captured yet — neutral baseline, same as the prototype.
        format_score = 0.75

    duration = float(resource.get("duration_minutes", 0) or 0)
    if duration <= IDEAL_DURATION_MINUTES:
        duration_fit = 1.0
    else:
        duration_fit = max(0.0, 1.0 - (duration - IDEAL_DURATION_MINUTES) / 30.0)

    components = {
        "topic_relevance": round(topic_relevance, 3),
        "difficulty_match": round(difficulty_match, 3),
        "quality": round(quality, 3),
        "format_preference": round(format_score, 3),
        "duration_fit": round(duration_fit, 3),
    }
    score = (
        topic_relevance * w["topic_relevance"]
        + difficulty_match * w["difficulty_match"]
        + quality * w["quality"]
        + format_score * w["format_preference"]
        + duration_fit * w["duration_fit"]
    )
    return round(score, 4), components


def explain(resource, components, mastery_pct):
    bits = []
    if components["topic_relevance"] >= 1.0:
        bits.append("directly covers this topic")
    if components["difficulty_match"] >= 1.0:
        bits.append(
            "pitched at %s level, which matches your current mastery of %d%%"
            % (resource.get("difficulty", "Medium").lower(), round(float(mastery_pct or 0)))
        )
    elif components["difficulty_match"] >= 0.5:
        bits.append("close to the right difficulty for you")
    if components["quality"] >= 0.9:
        bits.append("rated %.1f/5 by other learners" % float(resource.get("rating", 0) or 0))
    if components["duration_fit"] >= 1.0:
        bits.append("fits in a single %d-minute session" % int(resource.get("duration_minutes", 0) or 0))
    if not bits:
        bits.append("the closest available match in the resource pool")
    return "Recommended because it " + ", ".join(bits) + "."


def recommend_for_topic(resources, topic_id, mastery_pct, limit=3, format_preference=None):
    scored = []
    for r in resources:
        score, components = score_resource(r, topic_id, mastery_pct, format_preference)
        scored.append({
            "resource_id": r.get("id"),
            "title": r.get("title"),
            "type": r.get("type"),
            "difficulty": r.get("difficulty"),
            "duration_minutes": r.get("duration_minutes"),
            "rating": r.get("rating"),
            "url": r.get("url"),
            "topic_id": r.get("topic_id"),
            "score": score,
            "score_percent": round(score * 100, 1),
            "components": components,
            "reason": explain(r, components, mastery_pct),
        })
    scored.sort(key=lambda x: (-x["score"], x["title"] or ""))
    return scored[: max(1, int(limit))]


def recommend_for_user(resources, mastery_rows, limit=6, format_preference=None):
    """
    Weakest topics first, then the best resource(s) for each. Guarantees the
    recommendation list actually reflects measured mastery.
    """
    rows = sorted(mastery_rows, key=lambda r: float(r.get("mastery_pct", 0) or 0))
    out = []
    seen = set()
    for row in rows:
        topic_id = row.get("topic_id")
        picks = recommend_for_topic(
            resources, topic_id, row.get("mastery_pct", 0), limit=2,
            format_preference=format_preference,
        )
        for p in picks:
            if p["resource_id"] in seen or p["components"]["topic_relevance"] < 1.0:
                continue
            seen.add(p["resource_id"])
            p["for_topic_id"] = topic_id
            p["for_topic_mastery"] = row.get("mastery_pct")
            out.append(p)
            if len(out) >= limit:
                return out
    return out

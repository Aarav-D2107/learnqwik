"""
Mastery — blends the newest weighted score with prior mastery.

Port of `updateMastery` from the prototype. Recent performance is weighted at
70% and historical at 30% by default (both configurable). Pure stdlib.
"""
from config import (
    RECENT_WEIGHT,
    HISTORICAL_WEIGHT,
    MASTERY_BANDS,
    WEAK_TOPIC_THRESHOLD,
)


def band_for(pct):
    """Return the mastery band label for a 0-100 percentage."""
    pct = max(0.0, min(100.0, float(pct)))
    for upper, label in MASTERY_BANDS:
        if pct <= upper:
            return label
    return MASTERY_BANDS[-1][1]


def blend(new_weighted_pct, previous_mastery_pct=None):
    """
    First attempt at a topic -> mastery is simply the weighted score.
    Later attempts -> 0.7 * new + 0.3 * previous.
    """
    new_weighted_pct = max(0.0, min(100.0, float(new_weighted_pct)))
    if previous_mastery_pct is None:
        blended = new_weighted_pct
    else:
        prev = max(0.0, min(100.0, float(previous_mastery_pct)))
        blended = RECENT_WEIGHT * new_weighted_pct + HISTORICAL_WEIGHT * prev
    return round(blended, 1)


def apply_attempt(previous_row, weighted_pct):
    """
    previous_row: existing topic_mastery row (dict) or None.
    Returns the new authoritative mastery state for that topic.
    """
    previous_pct = previous_row.get("mastery_pct") if previous_row else None
    attempts = (previous_row or {}).get("attempts_count", 0) or 0
    new_pct = blend(weighted_pct, previous_pct)
    return {
        "previous_mastery_pct": round(float(previous_pct), 1) if previous_pct is not None else None,
        "mastery_pct": new_pct,
        "mastery_band": band_for(new_pct),
        "attempts_count": attempts + 1,
        "delta": round(new_pct - float(previous_pct), 1) if previous_pct is not None else None,
    }


def is_weak(pct):
    return float(pct) < WEAK_TOPIC_THRESHOLD


def weak_topics(mastery_rows):
    """
    mastery_rows: iterable of dicts with 'topic_id' and 'mastery_pct'.
    Returns weakest-first list of the topics below the weak threshold.
    """
    weak = [r for r in mastery_rows if is_weak(r.get("mastery_pct", 0))]
    weak.sort(key=lambda r: float(r.get("mastery_pct", 0)))
    return weak


def overall_mastery(mastery_rows):
    rows = [r for r in mastery_rows if r.get("mastery_pct") is not None]
    if not rows:
        return 0.0
    return round(sum(float(r["mastery_pct"]) for r in rows) / len(rows), 1)


def subject_mastery(mastery_rows, topic_ids):
    rows = [r for r in mastery_rows if r.get("topic_id") in set(topic_ids)]
    return overall_mastery(rows)

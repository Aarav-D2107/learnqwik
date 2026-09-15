"""
Scoring — the deterministic, authoritative grading of a quiz attempt.

This is a direct port of the prototype's `computeWeightedPct` logic in
js/app.js, moved server-side so the browser can no longer decide its own score.
Pure stdlib: no FastAPI, no Supabase, no AI. That makes it trivially testable.
"""
from config import DIFFICULTY_WEIGHTS, SECONDS_PER_QUESTION

DIFFICULTIES = ("Easy", "Medium", "Hard")


def weight_for(difficulty):
    return DIFFICULTY_WEIGHTS.get(difficulty, DIFFICULTY_WEIGHTS.get("Easy", 1.0))


def weighted_percentage(answers, questions):
    """
    answers: list of selected option indices (None = unanswered), index-aligned
             with `questions`.
    questions: list of dicts with 'difficulty' and 'correct_index'.

    Returns sum(correct x weight) / sum(weight) * 100.
    """
    numerator = 0.0
    denominator = 0.0
    for i, q in enumerate(questions):
        w = weight_for(q.get("difficulty"))
        denominator += w
        selected = answers[i] if i < len(answers) else None
        if selected is not None and selected == q.get("correct_index"):
            numerator += w
    if denominator <= 0:
        return 0.0
    return (numerator / denominator) * 100.0


def difficulty_breakdown(answers, questions):
    out = {d: {"correct": 0, "total": 0} for d in DIFFICULTIES}
    for i, q in enumerate(questions):
        d = q.get("difficulty") if q.get("difficulty") in out else "Easy"
        out[d]["total"] += 1
        selected = answers[i] if i < len(answers) else None
        if selected is not None and selected == q.get("correct_index"):
            out[d]["correct"] += 1
    return out


def score_attempt(answers, questions, time_used_seconds=None, violations=0):
    """Full authoritative result for one attempt."""
    total = len(questions)
    correct = 0
    unanswered = 0
    for i, q in enumerate(questions):
        selected = answers[i] if i < len(answers) else None
        if selected is None:
            unanswered += 1
        elif selected == q.get("correct_index"):
            correct += 1
    incorrect = total - correct - unanswered
    raw_pct = round((correct / total) * 100) if total else 0
    weighted = weighted_percentage(answers, questions)

    if time_used_seconds is None:
        time_used_seconds = total * SECONDS_PER_QUESTION

    return {
        "total_questions": total,
        "correct_count": correct,
        "incorrect_count": incorrect,
        "unanswered_count": unanswered,
        "raw_percentage": raw_pct,
        "weighted_percentage": round(weighted, 1),
        "difficulty_breakdown": difficulty_breakdown(answers, questions),
        "time_used_seconds": int(time_used_seconds),
        "fullscreen_violations": int(violations or 0),
    }

"""Difficulty-weighted scoring — the number the browser is never allowed to compute."""
from services import scoring_service


def test_all_correct_is_100(questions):
    result = scoring_service.score_attempt([1, 0, 2], questions)
    assert result["raw_percentage"] == 100
    assert result["weighted_percentage"] == 100.0
    assert result["correct_count"] == 3


def test_all_wrong_is_zero(questions):
    result = scoring_service.score_attempt([0, 1, 0], questions)
    assert result["raw_percentage"] == 0
    assert result["weighted_percentage"] == 0.0
    assert result["incorrect_count"] == 3


def test_hard_questions_weigh_more(questions):
    """Getting only the Hard one right (weight 2.0 of 4.5) beats only the Easy one (1.0 of 4.5),
    even though both are 1/3 raw."""
    only_hard = scoring_service.score_attempt([0, 1, 2], questions)
    only_easy = scoring_service.score_attempt([1, 1, 0], questions)
    assert only_hard["raw_percentage"] == only_easy["raw_percentage"] == 33
    assert only_hard["weighted_percentage"] > only_easy["weighted_percentage"]
    assert only_hard["weighted_percentage"] == round(2.0 / 4.5 * 100, 1)
    assert only_easy["weighted_percentage"] == round(1.0 / 4.5 * 100, 1)


def test_unanswered_counted_separately(questions):
    result = scoring_service.score_attempt([1, None, None], questions)
    assert result["correct_count"] == 1
    assert result["unanswered_count"] == 2
    assert result["incorrect_count"] == 0


def test_difficulty_breakdown(questions):
    result = scoring_service.score_attempt([1, 0, 0], questions)
    breakdown = result["difficulty_breakdown"]
    assert breakdown["Easy"] == {"correct": 1, "total": 1}
    assert breakdown["Medium"] == {"correct": 1, "total": 1}
    assert breakdown["Hard"] == {"correct": 0, "total": 1}


def test_empty_quiz_does_not_divide_by_zero():
    result = scoring_service.score_attempt([], [])
    assert result["weighted_percentage"] == 0.0
    assert result["raw_percentage"] == 0


def test_short_answer_list_treated_as_unanswered(questions):
    """A truncated answer array must not raise — it means the student ran out of time."""
    result = scoring_service.score_attempt([1], questions)
    assert result["correct_count"] == 1
    assert result["unanswered_count"] == 2

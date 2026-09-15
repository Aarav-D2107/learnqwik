"""Recent/historical blending and mastery bands."""
from services import mastery_service


def test_first_attempt_uses_raw_score():
    assert mastery_service.blend(72.0, None) == 72.0


def test_blend_is_70_30():
    # 0.7 * 80 + 0.3 * 40 = 68
    assert mastery_service.blend(80, 40) == 68.0


def test_blend_is_clamped():
    assert mastery_service.blend(150, None) == 100.0
    assert mastery_service.blend(-20, None) == 0.0


def test_bands():
    assert mastery_service.band_for(0) == "Weak"
    assert mastery_service.band_for(39) == "Weak"
    assert mastery_service.band_for(40) == "Struggling"
    assert mastery_service.band_for(59) == "Struggling"
    assert mastery_service.band_for(60) == "Developing"
    assert mastery_service.band_for(79) == "Developing"
    assert mastery_service.band_for(80) == "Mastered"
    assert mastery_service.band_for(100) == "Mastered"


def test_apply_attempt_tracks_delta_and_count():
    previous = {"mastery_pct": 32.0, "attempts_count": 1}
    result = mastery_service.apply_attempt(previous, 88.0)
    # 0.7 * 88 + 0.3 * 32 = 71.2
    assert result["mastery_pct"] == 71.2
    assert result["previous_mastery_pct"] == 32.0
    assert result["delta"] == 39.2
    assert result["mastery_band"] == "Developing"
    assert result["attempts_count"] == 2


def test_apply_attempt_with_no_history():
    result = mastery_service.apply_attempt(None, 45.0)
    assert result["mastery_pct"] == 45.0
    assert result["previous_mastery_pct"] is None
    assert result["delta"] is None
    assert result["attempts_count"] == 1


def test_weak_topics_sorted_weakest_first(mastery_rows):
    weak = mastery_service.weak_topics(mastery_rows)
    assert weak[0]["topic_id"] == "java-exceptions"
    assert weak[1]["topic_id"] == "java-collections"
    assert all(r["mastery_pct"] < 60 for r in weak)


def test_overall_mastery(mastery_rows):
    assert mastery_service.overall_mastery(mastery_rows) == 67.0


def test_overall_mastery_empty():
    assert mastery_service.overall_mastery([]) == 0.0

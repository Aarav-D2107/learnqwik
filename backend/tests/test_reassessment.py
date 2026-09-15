"""Before/after improvement — the central LearnQwik story."""
from services import reassessment_service as ra


def test_the_headline_scenario():
    result = ra.compare(32, 71)
    assert result["delta"] == 39
    assert result["improved"] is True
    assert result["before_band"] == "Weak"
    assert result["after_band"] == "Developing"
    assert result["band_changed"] is True
    assert "39 percentage points" in result["summary"]
    assert "Weak to Developing" in result["summary"]


def test_regression_is_reported_honestly():
    result = ra.compare(70, 55)
    assert result["delta"] == -15
    assert result["improved"] is False
    assert "down 15" in result["summary"]


def test_no_change():
    result = ra.compare(60, 60)
    assert result["delta"] == 0
    assert result["improved"] is False
    assert "Held steady" in result["summary"]


def test_first_measurement_has_no_before():
    result = ra.compare(None, 64)
    assert result["before"] is None
    assert result["delta"] is None
    assert result["improved"] is None
    assert result["after_band"] == "Developing"


def test_fractional_delta_formatting():
    result = ra.compare(32.0, 43.5)
    assert "11.5 percentage points" in result["summary"]


def test_reassessment_always_triggers_roadmap_update():
    comparison = ra.compare(60, 61)
    assert ra.should_trigger_roadmap_update(comparison, is_reassessment=True) is True


def test_first_attempt_triggers_roadmap_update():
    comparison = ra.compare(None, 50)
    assert ra.should_trigger_roadmap_update(comparison, is_reassessment=False) is True


def test_band_change_triggers_roadmap_update():
    comparison = ra.compare(58, 61)  # Struggling -> Developing
    assert ra.should_trigger_roadmap_update(comparison, is_reassessment=False) is True


def test_noise_does_not_trigger_roadmap_update():
    comparison = ra.compare(70, 71)
    assert ra.should_trigger_roadmap_update(comparison, is_reassessment=False) is False

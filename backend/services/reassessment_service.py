"""
Reassessment — measuring that the gap actually closed.

"Exception Handling: 32% -> 71%, +39 percentage points" is the LearnQwik
story, so the arithmetic behind it lives in one small, tested place.
"""
from services.mastery_service import band_for


def compare(before_pct, after_pct):
    if before_pct is None:
        return {
            "before": None,
            "after": round(float(after_pct), 1),
            "delta": None,
            "improved": None,
            "before_band": None,
            "after_band": band_for(after_pct),
            "band_changed": False,
            "summary": "First measurement for this topic: %d%% (%s)." % (
                round(float(after_pct)), band_for(after_pct)),
        }

    before = round(float(before_pct), 1)
    after = round(float(after_pct), 1)
    delta = round(after - before, 1)
    before_band = band_for(before)
    after_band = band_for(after)

    if delta > 0:
        summary = "%d%% to %d%% — up %s percentage points." % (
            round(before), round(after), _fmt(delta))
    elif delta < 0:
        summary = "%d%% to %d%% — down %s percentage points." % (
            round(before), round(after), _fmt(abs(delta)))
    else:
        summary = "Held steady at %d%%." % round(after)

    if before_band != after_band and delta > 0:
        summary += " You moved from %s to %s." % (before_band, after_band)

    return {
        "before": before,
        "after": after,
        "delta": delta,
        "improved": delta > 0,
        "before_band": before_band,
        "after_band": after_band,
        "band_changed": before_band != after_band,
        "summary": summary,
    }


def _fmt(value):
    return str(int(value)) if float(value).is_integer() else ("%.1f" % value)


def should_trigger_roadmap_update(comparison, is_reassessment):
    """
    Don't burn an AI call and a roadmap version on noise. Regenerate when the
    mastery band changed, the swing was meaningful, or this was an explicit
    reassessment the user asked for.
    """
    if is_reassessment:
        return True
    if comparison.get("before") is None:
        return True
    if comparison.get("band_changed"):
        return True
    return abs(comparison.get("delta") or 0) >= 5.0

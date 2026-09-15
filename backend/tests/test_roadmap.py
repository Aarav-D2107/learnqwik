"""The two roadmap states, AI output validation, fallback, and diffing."""
import pytest

from services import roadmap_service as rm


# ---------------------------------------------------------------- STATE 1
def test_default_roadmap_follows_curriculum_order(subject, topics):
    roadmap = rm.build_default_roadmap(subject, topics)
    assert roadmap["state"] == "default"
    assert roadmap["generated_by"] == "default"
    assert [s["topic_id"] for s in roadmap["steps"]] == [t["id"] for t in topics]
    assert roadmap["steps"][0]["title"] == "Java Fundamentals"
    assert "first assessment" in roadmap["reason"]


def test_default_roadmap_needs_no_ai_and_no_history(subject, topics):
    roadmap = rm.build_default_roadmap(subject, topics)
    assert roadmap["priority_topics"] == []
    assert len(roadmap["steps"]) == 6


# ---------------------------------------------------------------- Priorities
def test_weakest_topic_ranks_first(subject, topics, mastery_rows):
    by_topic = {m["topic_id"]: m for m in mastery_rows}
    priorities = rm.build_priority_topics(topics, by_topic)
    assert priorities[0]["topic_id"] == "java-exceptions"
    assert priorities[0]["mastery"] == 32
    assert priorities[0]["band"] == "Weak"


def test_mastered_topics_rank_last(subject, topics, mastery_rows):
    by_topic = {m["topic_id"]: m for m in mastery_rows}
    priorities = rm.build_priority_topics(topics, by_topic)
    assert priorities[-1]["topic_id"] == "java-fundamentals"  # 88%, the strongest


def test_unassessed_topics_rank_after_weak_ones(subject, topics):
    by_topic = {"java-exceptions": {"topic_id": "java-exceptions", "mastery_pct": 30}}
    priorities = rm.build_priority_topics(topics, by_topic)
    assert priorities[0]["topic_id"] == "java-exceptions"
    assert priorities[1]["mastery"] is None


def test_prerequisite_is_pulled_ahead_of_its_dependent(subject, topics):
    """Collections (55%) depends on Exception Handling (20%). Even though 55 > 20 would
    normally order them that way anyway, the guard must hold when the dependent is weaker."""
    by_topic = {
        "java-exceptions": {"topic_id": "java-exceptions", "mastery_pct": 50},
        "java-collections": {"topic_id": "java-collections", "mastery_pct": 20},
    }
    priorities = rm.build_priority_topics(topics, by_topic)
    order = [p["topic_id"] for p in priorities]
    assert order.index("java-exceptions") < order.index("java-collections")


# ---------------------------------------------------------------- STATE 2 fallback
def test_fallback_roadmap_leads_with_the_gap(subject, topics, mastery_rows, resources):
    by_topic = {m["topic_id"]: m for m in mastery_rows}
    roadmap = rm.build_fallback_roadmap(subject, topics, by_topic, resources)
    assert roadmap["state"] == "personalized"
    assert roadmap["generated_by"] == "fallback"
    assert roadmap["steps"][0]["topic_id"] == "java-exceptions"
    assert "Exception Handling" in roadmap["reason"]


def test_fallback_includes_reassessment_for_weak_topics(subject, topics, mastery_rows, resources):
    by_topic = {m["topic_id"]: m for m in mastery_rows}
    roadmap = rm.build_fallback_roadmap(subject, topics, by_topic, resources)
    reassess = [s for s in roadmap["steps"] if s["kind"] == "reassess"]
    assert reassess
    assert reassess[0]["topic_id"] == "java-exceptions"


def test_fallback_covers_every_topic_exactly_once_per_thread(subject, topics, mastery_rows, resources):
    by_topic = {m["topic_id"]: m for m in mastery_rows}
    roadmap = rm.build_fallback_roadmap(subject, topics, by_topic, resources)
    covered = {s["topic_id"] for s in roadmap["steps"]}
    assert covered == {t["id"] for t in topics}


def test_fallback_only_uses_real_resource_ids(subject, topics, mastery_rows, resources):
    by_topic = {m["topic_id"]: m for m in mastery_rows}
    roadmap = rm.build_fallback_roadmap(subject, topics, by_topic, resources)
    valid = {r["id"] for r in resources}
    for step in roadmap["steps"]:
        for rid in step["resource_ids"]:
            assert rid in valid


# ---------------------------------------------------------------- AI validation
def _priorities(topics, mastery_rows):
    return rm.build_priority_topics(topics, {m["topic_id"]: m for m in mastery_rows})


def test_valid_ai_roadmap_is_accepted(subject, topics, resources, mastery_rows):
    payload = {
        "title": "Personalized Java Roadmap",
        "reason": "Exception Handling is your biggest gap.",
        "priority_topics": [{"topic_id": "java-exceptions", "reason": "32% mastery"}],
        "steps": [
            {"order": 1, "topic_id": "java-exceptions", "title": "Exception basics",
             "reason": "Start here.", "estimated_minutes": 30, "kind": "learn",
             "resource_ids": ["r1"]},
            {"order": 2, "topic_id": "java-exceptions", "title": "Reassess",
             "reason": "Confirm it stuck.", "estimated_minutes": 8, "kind": "reassess",
             "resource_ids": []},
        ],
    }
    result = rm.validate_ai_roadmap(payload, subject, topics, resources,
                                    _priorities(topics, mastery_rows))
    assert result["generated_by"] == "ai"
    assert len(result["steps"]) == 2
    assert result["steps"][0]["resource_ids"] == ["r1"]


def test_hallucinated_topic_id_is_rejected(subject, topics, resources, mastery_rows):
    payload = {"steps": [{"topic_id": "java-quantum-computing", "title": "Nope"}]}
    with pytest.raises(rm.RoadmapValidationError, match="unknown topic_id"):
        rm.validate_ai_roadmap(payload, subject, topics, resources,
                               _priorities(topics, mastery_rows))


def test_hallucinated_resource_id_is_rejected(subject, topics, resources, mastery_rows):
    payload = {"steps": [{"topic_id": "java-exceptions", "title": "Study",
                          "resource_ids": ["r999"]}]}
    with pytest.raises(rm.RoadmapValidationError, match="unknown resource_id"):
        rm.validate_ai_roadmap(payload, subject, topics, resources,
                               _priorities(topics, mastery_rows))


def test_empty_steps_rejected(subject, topics, resources, mastery_rows):
    with pytest.raises(rm.RoadmapValidationError):
        rm.validate_ai_roadmap({"steps": []}, subject, topics, resources,
                               _priorities(topics, mastery_rows))


def test_non_object_rejected(subject, topics, resources, mastery_rows):
    with pytest.raises(rm.RoadmapValidationError):
        rm.validate_ai_roadmap(["not", "an", "object"], subject, topics, resources,
                               _priorities(topics, mastery_rows))


def test_ai_cannot_overwrite_mastery_numbers(subject, topics, resources, mastery_rows):
    """The model claims 99% for a topic the backend measured at 32%. Ours wins."""
    payload = {
        "priority_topics": [{"topic_id": "java-exceptions", "mastery": 99,
                             "reason": "model's opinion"}],
        "steps": [{"topic_id": "java-exceptions", "title": "Step", "resource_ids": []}],
    }
    result = rm.validate_ai_roadmap(payload, subject, topics, resources,
                                    _priorities(topics, mastery_rows))
    assert result["priority_topics"][0]["mastery"] == 32


def test_absurd_time_estimates_are_clamped(subject, topics, resources, mastery_rows):
    payload = {"steps": [{"topic_id": "java-exceptions", "title": "Step",
                          "estimated_minutes": 99999, "resource_ids": []}]}
    result = rm.validate_ai_roadmap(payload, subject, topics, resources,
                                    _priorities(topics, mastery_rows))
    assert result["steps"][0]["estimated_minutes"] == 180


def test_unknown_step_kind_defaults_to_learn(subject, topics, resources, mastery_rows):
    payload = {"steps": [{"topic_id": "java-exceptions", "title": "Step",
                          "kind": "teleport", "resource_ids": []}]}
    result = rm.validate_ai_roadmap(payload, subject, topics, resources,
                                    _priorities(topics, mastery_rows))
    assert result["steps"][0]["kind"] == "learn"


# ---------------------------------------------------------------- Diffing
def test_first_version_diff():
    current = {"steps": [{"title": "A"}, {"title": "B"}]}
    diff = rm.diff_roadmaps(None, current)
    assert diff["is_first_version"] is True
    assert diff["added"] == ["A", "B"]


def test_diff_detects_added_and_removed():
    previous = {"steps": [{"title": "Java Fundamentals"}, {"title": "OOP"}]}
    current = {"steps": [{"title": "Exception Handling Practice"}, {"title": "OOP"}]}
    diff = rm.diff_roadmaps(previous, current)
    assert diff["added"] == ["Exception Handling Practice"]
    assert diff["removed"] == ["Java Fundamentals"]


def test_diff_detects_reordering():
    previous = {"steps": [{"title": "A"}, {"title": "B"}]}
    current = {"steps": [{"title": "B"}, {"title": "A"}]}
    diff = rm.diff_roadmaps(previous, current)
    assert diff["reordered"] is True
    assert diff["added"] == []


def test_total_estimated_minutes():
    roadmap = {"steps": [{"estimated_minutes": 30}, {"estimated_minutes": 20}]}
    assert rm.total_estimated_minutes(roadmap) == 50

"""The deterministic, explainable recommendation engine."""
from services import recommendation_service as rs


def test_weights_sum_to_one():
    assert round(sum(rs.RECOMMENDATION_WEIGHTS.values()), 6) == 1.0


def test_target_difficulty_follows_mastery():
    assert rs.target_difficulty(20) == "Easy"
    assert rs.target_difficulty(55) == "Easy"
    assert rs.target_difficulty(70) == "Medium"
    assert rs.target_difficulty(95) == "Hard"


def test_on_topic_beats_off_topic(resources):
    picks = rs.recommend_for_topic(resources, "java-exceptions", 32, limit=4)
    assert picks[0]["topic_id"] == "java-exceptions"
    off_topic = [p for p in picks if p["topic_id"] != "java-exceptions"]
    assert all(p["score"] < picks[0]["score"] for p in off_topic)


def test_weak_learner_gets_easy_material(resources):
    picks = rs.recommend_for_topic(resources, "java-exceptions", 25, limit=1)
    assert picks[0]["difficulty"] == "Easy"


def test_strong_learner_gets_harder_material(resources):
    picks = rs.recommend_for_topic(resources, "java-exceptions", 90, limit=1)
    assert picks[0]["difficulty"] == "Hard"


def test_every_recommendation_is_explained(resources):
    for pick in rs.recommend_for_topic(resources, "java-exceptions", 40, limit=3):
        assert pick["reason"]
        assert 0 <= pick["score"] <= 1
        assert set(pick["components"]) == set(rs.RECOMMENDATION_WEIGHTS)


def test_user_recommendations_lead_with_weakest_topic(resources, mastery_rows):
    picks = rs.recommend_for_user(resources, mastery_rows, limit=4)
    assert picks
    assert picks[0]["for_topic_id"] == "java-exceptions"


def test_scores_are_deterministic(resources):
    a = rs.recommend_for_topic(resources, "java-exceptions", 32, limit=3)
    b = rs.recommend_for_topic(resources, "java-exceptions", 32, limit=3)
    assert [x["resource_id"] for x in a] == [x["resource_id"] for x in b]
    assert [x["score"] for x in a] == [x["score"] for x in b]

"""
AI orchestration with a mocked provider. Never requires live credentials.

    pip install -r requirements.txt && pytest -q
"""
import pytest

pytest.importorskip("fastapi")

from services import ai_service, roadmap_service, summarizer  # noqa: E402
from services.ai_provider import AIUnavailableError, extract_json  # noqa: E402


def _priorities(topics, mastery_rows):
    return roadmap_service.build_priority_topics(
        topics, {m["topic_id"]: m for m in mastery_rows}
    )


@pytest.mark.asyncio
async def test_ai_roadmap_used_when_valid(monkeypatch, subject, topics, resources,
                                          mastery_rows, mock_provider):
    provider = mock_provider(structured_response={
        "title": "Personalized Java Roadmap",
        "reason": "Exception Handling is your biggest gap at 32%.",
        "priority_topics": [{"topic_id": "java-exceptions", "reason": "Weakest topic"}],
        "steps": [
            {"order": 1, "topic_id": "java-exceptions", "title": "Exception fundamentals",
             "reason": "Start from the basics.", "estimated_minutes": 30,
             "kind": "learn", "resource_ids": ["r1"]},
            {"order": 2, "topic_id": "java-exceptions", "title": "Reassess Exception Handling",
             "reason": "Prove the gap closed.", "estimated_minutes": 8,
             "kind": "reassess", "resource_ids": []},
        ],
    })
    monkeypatch.setattr(ai_service, "get_provider", lambda: provider)

    roadmap, generated_by = await ai_service.generate_ai_roadmap(
        subject, topics, _priorities(topics, mastery_rows), resources,
        {m["topic_id"]: m for m in mastery_rows},
    )
    assert generated_by == "ai"
    assert roadmap["steps"][0]["topic_id"] == "java-exceptions"
    assert provider.calls


@pytest.mark.asyncio
async def test_falls_back_when_ai_hallucinates_ids(monkeypatch, subject, topics, resources,
                                                   mastery_rows, mock_provider):
    provider = mock_provider(structured_response={
        "steps": [{"topic_id": "java-does-not-exist", "title": "Nonsense", "resource_ids": []}]
    })
    monkeypatch.setattr(ai_service, "get_provider", lambda: provider)

    roadmap, generated_by = await ai_service.generate_ai_roadmap(
        subject, topics, _priorities(topics, mastery_rows), resources,
        {m["topic_id"]: m for m in mastery_rows},
    )
    assert generated_by == "fallback"
    # The user still gets a real personalized plan, not the default curriculum.
    assert roadmap["state"] == "personalized"
    assert roadmap["steps"][0]["topic_id"] == "java-exceptions"


@pytest.mark.asyncio
async def test_falls_back_when_provider_errors(monkeypatch, subject, topics, resources,
                                               mastery_rows, mock_provider):
    provider = mock_provider(fail_with=AIUnavailableError("provider down"))
    monkeypatch.setattr(ai_service, "get_provider", lambda: provider)

    roadmap, generated_by = await ai_service.generate_ai_roadmap(
        subject, topics, _priorities(topics, mastery_rows), resources,
        {m["topic_id"]: m for m in mastery_rows},
    )
    assert generated_by == "fallback"
    assert roadmap["steps"]


@pytest.mark.asyncio
async def test_explanation_degrades_without_ai(monkeypatch):
    from services.ai_provider import AINotConfiguredError

    def no_provider():
        raise AINotConfiguredError("no key")
    monkeypatch.setattr(ai_service, "get_provider", no_provider)

    text = await ai_service.explain_result(
        "Java", "Exception Handling",
        {"raw_percentage": 30, "weighted_percentage": 28.0, "difficulty_breakdown": {}},
        {"mastery_pct": 30, "mastery_band": "Weak"},
    )
    assert "Exception Handling" in text
    assert text  # a real, useful explanation — just not model-generated


# ---------------------------------------------------------------- JSON recovery
def test_extract_json_handles_plain_object():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_strips_markdown_fences():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_recovers_from_surrounding_prose():
    assert extract_json('Here you go:\n{"a": 1}\nHope that helps!') == {"a": 1}


def test_extract_json_raises_on_garbage():
    from services.ai_provider import AIInvalidOutputError
    with pytest.raises(AIInvalidOutputError):
        extract_json("no json here at all")


# ---------------------------------------------------------------- Summaries
def test_summary_context_interleaves_text_and_vision():
    pages = [{
        "page_number": 8, "extracted_text": "Figure 3.1",
        "visual_analysis": "An ER diagram connecting Student and Enrollment.",
        "content_quality": "mixed",
    }]
    context = summarizer.build_context(pages)
    assert "PAGE 8" in context
    assert "TEXT:" in context
    assert "VISION ANALYSIS:" in context


def test_summary_context_respects_its_budget():
    pages = [{"page_number": i, "extracted_text": "x" * 5000, "content_quality": "text_rich"}
             for i in range(1, 40)]
    context = summarizer.build_context(pages, max_chars=10000)
    assert len(context) <= 10500


def test_summary_normalization_fills_missing_sections():
    result = summarizer.normalize({"overview": "Covers normalization."})
    assert result["key_concepts"] == []
    assert result["exam_focus"] == []
    assert result["overview"] == "Covers normalization."


def test_summary_markdown_export():
    summary = summarizer.normalize({
        "overview": "Covers ACID.",
        "key_concepts": [{"concept": "Atomicity", "explanation": "All or nothing", "page": 4}],
    })
    markdown = summarizer.to_markdown(summary, "dbms.pdf")
    assert "# Summary — dbms.pdf" in markdown
    assert "Atomicity" in markdown
    assert "(page 4)" in markdown

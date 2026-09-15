"""
AI endpoints: tutor, explanation, learning plan.

The tutor is locked during an active assessment — enforced here on the server,
not just by hiding the UI.
"""
import db
import deps
import errors
from fastapi import APIRouter, Depends
from schemas.models import ExplainRequest, LearningPlanRequest, TutorRequest
from services import ai_service, catalog, document_service, mastery_service, quiz_service, tutor_service
from services.ai_provider import AIError

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _ai_error(exc):
    return errors.AppError(exc.code, exc.message, exc.http_status)


@router.post("/tutor")
async def tutor(body: TutorRequest, user=Depends(deps.ai_rate_limit)):
    await deps.assert_no_active_quiz(user)

    conversation = [m.model_dump() for m in body.conversation]

    # ---------- Document-grounded mode
    if body.document_id:
        document = await document_service.get_document(body.document_id, user["id"])
        if not document:
            raise errors.not_found("That document wasn't found in your library.",
                                   code="DOCUMENT_NOT_FOUND")
        if document.get("status") != document_service.STATUS_READY:
            raise errors.bad_request(
                "That document is still processing. Wait for it to finish, then ask again.",
                code="DOCUMENT_NOT_READY",
            )
        chunks = await document_service.retrieve_context(
            body.document_id, user["id"], body.message, body.page_context
        )
        if not chunks:
            return {
                "reply": "I couldn't find anything in your uploaded material that relates to "
                         "that. Try rephrasing, or ask about a specific page.",
                "grounded": True,
                "sources": [],
            }
        context = tutor_service.build_document_context(document, chunks, body.page_context)
        try:
            reply = await tutor_service.answer(body.message, context, conversation,
                                               document_mode=True)
        except AIError as exc:
            raise _ai_error(exc)

        await _save_conversation(user["id"], body, reply, document_id=body.document_id)
        return {
            "reply": reply,
            "grounded": True,
            "sources": [{
                "page_number": c.get("page_number"),
                "source": c.get("source"),
                "content_type": c.get("content_type"),
            } for c in chunks],
        }

    # ---------- Topic mode
    if not body.topic:
        raise errors.bad_request("Ask from a topic page, or pass a document_id.",
                                 code="NO_CONTEXT")

    topic = await catalog.get_topic(body.topic)
    subject = await catalog.get_subject(topic["subject_id"])
    mastery_row = await quiz_service.get_mastery_row(user["id"], topic["id"])

    mastery_rows = [m for m in await quiz_service.all_mastery(user["id"])
                    if m.get("subject_id") == subject["id"]]
    topic_names = {t["id"]: t["name"] for t in await catalog.topics_for(subject["id"])}
    weak = [{**w, "topic_name": topic_names.get(w["topic_id"])}
            for w in mastery_service.weak_topics(mastery_rows)]

    context = tutor_service.build_topic_context(
        subject, topic, topic.get("content") or {}, mastery_row, weak
    )
    try:
        reply = await tutor_service.answer(body.message, context, conversation)
    except AIError as exc:
        raise _ai_error(exc)

    await _save_conversation(user["id"], body, reply, topic_id=topic["id"])
    return {"reply": reply, "grounded": False, "sources": []}


@router.get("/tutor/greeting")
async def greeting(topic_id: str, user=Depends(deps.current_user)):
    topic = await catalog.get_topic(topic_id)
    return {"greeting": tutor_service.greeting(topic["name"])}


@router.post("/explain")
async def explain(body: ExplainRequest, user=Depends(deps.ai_rate_limit)):
    """Natural-language reading of a completed attempt."""
    attempt = await quiz_service.get_attempt(body.attempt_id, user["id"])
    if attempt["status"] != "completed":
        raise errors.bad_request("That assessment hasn't been completed yet.",
                                 code="ATTEMPT_NOT_COMPLETED")
    topic = await catalog.get_topic(attempt["topic_id"])
    subject = await catalog.get_subject(attempt["subject_id"])
    mastery_row = await quiz_service.get_mastery_row(user["id"], attempt["topic_id"]) or {}

    from services import reassessment_service
    comparison = reassessment_service.compare(
        attempt.get("before_mastery_pct"), attempt.get("after_mastery_pct") or 0
    )
    result = {
        "raw_percentage": attempt.get("raw_score_pct"),
        "weighted_percentage": attempt.get("weighted_score_pct"),
        "difficulty_breakdown": attempt.get("difficulty_breakdown"),
        "unanswered_count": attempt.get("unanswered_count"),
    }
    explanation = await ai_service.explain_result(
        subject["name"], topic["name"], result, mastery_row, comparison
    )
    return {"explanation": explanation, "comparison": comparison}


@router.post("/learning-plan")
async def learning_plan(body: LearningPlanRequest, user=Depends(deps.ai_rate_limit)):
    """Regenerate the personalized plan on demand (same engine as post-assessment)."""
    return await quiz_service.recompute_roadmap(user["id"], body.subject_id, force=True)


async def _save_conversation(user_id, body, reply, topic_id=None, document_id=None):
    try:
        await db.insert("ai_conversations", {
            "user_id": user_id,
            "topic_id": topic_id,
            "uploaded_file_id": document_id,
            "user_message": body.message[:4000],
            "assistant_message": (reply or "")[:8000],
            "page_context": body.page_context,
        })
    except Exception:
        pass  # transcript persistence is best-effort; never fail the reply

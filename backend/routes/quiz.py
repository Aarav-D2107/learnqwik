"""Quiz lifecycle endpoints. Answer keys never leave the server until submission."""
from fastapi import APIRouter, Depends

import deps
from schemas.models import (
    QuizAnswerRequest,
    QuizCompleteRequest,
    QuizStartRequest,
    ReassessRequest,
)
from services import quiz_service

router = APIRouter(prefix="/api", tags=["quiz"])


@router.post("/quiz/start")
async def start_quiz(body: QuizStartRequest, user=Depends(deps.current_user)):
    return await quiz_service.start(
        user["id"], body.subject_id, body.topic_id, body.mode, body.question_count
    )


@router.get("/quiz/{attempt_id}/questions")
async def attempt_questions(attempt_id: str, user=Depends(deps.current_user)):
    attempt, questions = await quiz_service.questions_for_attempt(attempt_id, user["id"])
    return {
        "attempt_id": attempt_id,
        "status": attempt["status"],
        "mode": attempt.get("mode"),
        "questions": questions,
    }


@router.post("/quiz/{attempt_id}/answer")
async def save_answer(attempt_id: str, body: QuizAnswerRequest,
                      user=Depends(deps.current_user)):
    return await quiz_service.record_answer(
        attempt_id, user["id"], body.question_id, body.selected_index, body.response_time_ms
    )


@router.post("/quiz/{attempt_id}/complete")
async def complete_quiz(attempt_id: str, body: QuizCompleteRequest,
                        user=Depends(deps.current_user)):
    """Scores the attempt and runs the full personalization pipeline."""
    return await quiz_service.complete(
        user["id"], attempt_id,
        fullscreen_violations=body.fullscreen_violations,
        auto_submitted=body.auto_submitted,
        time_used_seconds=body.time_used_seconds,
    )


@router.get("/quiz/attempts")
async def list_attempts(user=Depends(deps.current_user), limit: int = 20):
    import db
    rows = await db.select("quiz_attempts", {
        "select": "*",
        "user_id": "eq.%s" % user["id"],
        "status": "eq.completed",
        "order": "completed_at.desc",
        "limit": str(min(max(limit, 1), 100)),
    })
    return {"attempts": rows}


@router.post("/assessment/reassess")
async def reassess(body: ReassessRequest, user=Depends(deps.current_user)):
    """Short, targeted reassessment of one topic."""
    return await quiz_service.start(
        user["id"], body.subject_id, body.topic_id, mode="reassess",
        question_count=body.question_count,
    )

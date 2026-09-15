"""Progress dashboard data. Every number comes from the database — nothing is fabricated."""
from fastapi import APIRouter, Depends

import db
import deps
from services import catalog, mastery_service, quiz_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(user=Depends(deps.current_user)):
    mastery_rows = await quiz_service.all_mastery(user["id"])
    attempts = await db.select("quiz_attempts", {
        "select": "id,subject_id,topic_id,mode,raw_score_pct,weighted_score_pct,"
                  "after_mastery_pct,completed_at,total_questions,correct_count",
        "user_id": "eq.%s" % user["id"],
        "status": "eq.completed",
        "order": "completed_at.desc",
        "limit": "50",
    })

    if not attempts and not mastery_rows:
        return {
            "has_data": False,
            "empty_state": "You haven't taken an assessment yet. Pick a subject and take your "
                           "first quiz — your dashboard fills in from there.",
            "overall_mastery": 0, "total_quizzes": 0, "subjects_studied": 0,
            "topics_mastered": 0, "weak_topics": 0, "recent_scores": [],
        }

    topics = {t["id"]: t for t in await catalog.all_topics()}
    subjects = {s["id"]: s for s in await catalog.all_subjects()}
    weak = mastery_service.weak_topics(mastery_rows)

    return {
        "has_data": True,
        "overall_mastery": mastery_service.overall_mastery(mastery_rows),
        "total_quizzes": len(attempts),
        "subjects_studied": len({a["subject_id"] for a in attempts}),
        "topics_assessed": len(mastery_rows),
        "topics_mastered": sum(1 for m in mastery_rows if (m.get("mastery_pct") or 0) >= 80),
        "weak_topics": [{
            "topic_id": w["topic_id"],
            "topic_name": topics.get(w["topic_id"], {}).get("name", w["topic_id"]),
            "subject_id": w.get("subject_id"),
            "subject_name": subjects.get(w.get("subject_id"), {}).get("name"),
            "mastery_pct": w.get("mastery_pct"),
            "mastery_band": w.get("mastery_band"),
        } for w in weak[:6]],
        "recent_scores": [{
            "attempt_id": a["id"],
            "topic_name": topics.get(a["topic_id"], {}).get("name", a["topic_id"]),
            "subject_name": subjects.get(a["subject_id"], {}).get("name"),
            "score_pct": a.get("raw_score_pct"),
            "weighted_pct": a.get("weighted_score_pct"),
            "mode": a.get("mode"),
            "completed_at": a.get("completed_at"),
        } for a in attempts[:10]],
    }


@router.get("/topics")
async def topic_breakdown(user=Depends(deps.current_user), subject_id: str = None):
    """Powers the knowledge map."""
    mastery_rows = await quiz_service.all_mastery(user["id"])
    by_topic = {m["topic_id"]: m for m in mastery_rows}
    all_topics = await catalog.all_topics()
    if subject_id:
        all_topics = [t for t in all_topics if t["subject_id"] == subject_id]
    subjects = {s["id"]: s for s in await catalog.all_subjects()}

    return {"topics": [{
        "topic_id": t["id"],
        "topic_name": t["name"],
        "subject_id": t["subject_id"],
        "subject_name": subjects.get(t["subject_id"], {}).get("name"),
        "subject_color": subjects.get(t["subject_id"], {}).get("color"),
        "position": t.get("position"),
        "mastery_pct": by_topic.get(t["id"], {}).get("mastery_pct"),
        "mastery_band": by_topic.get(t["id"], {}).get("mastery_band"),
        "attempts_count": by_topic.get(t["id"], {}).get("attempts_count", 0),
        "assessed": t["id"] in by_topic,
    } for t in all_topics]}


@router.get("/progress")
async def progress(user=Depends(deps.current_user), topic_id: str = None, limit: int = 100):
    params = {
        "select": "*",
        "user_id": "eq.%s" % user["id"],
        "order": "recorded_at.asc",
        "limit": str(min(max(limit, 1), 500)),
    }
    if topic_id:
        params["topic_id"] = "eq.%s" % topic_id
    rows = await db.select("progress_history", params)
    topics = {t["id"]: t["name"] for t in await catalog.all_topics()}
    return {
        "points": [{
            "recorded_at": r.get("recorded_at"),
            "topic_id": r.get("topic_id"),
            "topic_name": topics.get(r.get("topic_id")),
            "mastery_pct": r.get("mastery_pct"),
            "score_pct": r.get("score_pct"),
        } for r in rows],
        "empty_state": None if rows else "No progress recorded yet.",
    }


@router.get("/improvement")
async def improvement(user=Depends(deps.current_user)):
    """Before/after pairs from reassessments — the measurable-improvement story."""
    rows = await db.select("quiz_attempts", {
        "select": "id,topic_id,subject_id,before_mastery_pct,after_mastery_pct,completed_at,mode",
        "user_id": "eq.%s" % user["id"],
        "status": "eq.completed",
        "mode": "eq.reassess",
        "order": "completed_at.desc",
        "limit": "20",
    })
    topics = {t["id"]: t["name"] for t in await catalog.all_topics()}
    from services import reassessment_service
    out = []
    for r in rows:
        if r.get("after_mastery_pct") is None:
            continue
        comparison = reassessment_service.compare(r.get("before_mastery_pct"),
                                                  r["after_mastery_pct"])
        out.append({
            "attempt_id": r["id"],
            "topic_id": r["topic_id"],
            "topic_name": topics.get(r["topic_id"], r["topic_id"]),
            "completed_at": r.get("completed_at"),
            **comparison,
        })
    return {"improvements": out,
            "empty_state": None if out else "Reassess a weak topic to see measured improvement."}

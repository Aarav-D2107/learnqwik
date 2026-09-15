"""Curriculum browsing. Public — no auth needed to read content."""
from fastapi import APIRouter, Depends

import deps
from services import catalog, quiz_service

router = APIRouter(prefix="/api", tags=["curriculum"])


@router.get("/subjects")
async def list_subjects(user=Depends(deps.optional_user)):
    subjects = await catalog.all_subjects()
    mastery = {}
    if user:
        mastery = {m["topic_id"]: m for m in await quiz_service.all_mastery(user["id"])}

    topics = await catalog.all_topics()
    by_subject = {}
    for t in topics:
        by_subject.setdefault(t["subject_id"], []).append(t)

    out = []
    for s in subjects:
        subject_topics = by_subject.get(s["id"], [])
        scores = [mastery[t["id"]]["mastery_pct"] for t in subject_topics if t["id"] in mastery]
        out.append({
            **s,
            "topic_count": len(subject_topics),
            "mastery_pct": round(sum(scores) / len(scores), 1) if scores else 0,
            "topics_assessed": len(scores),
        })
    return {"subjects": out}


@router.get("/subjects/{subject_id}/topics")
async def list_topics(subject_id: str, user=Depends(deps.optional_user)):
    subject = await catalog.get_subject(subject_id)
    topics = await catalog.topics_for(subject_id)
    mastery = {}
    if user:
        mastery = {m["topic_id"]: m for m in await quiz_service.all_mastery(user["id"])}
    return {
        "subject": subject,
        "topics": [{
            **t,
            "mastery_pct": mastery.get(t["id"], {}).get("mastery_pct"),
            "mastery_band": mastery.get(t["id"], {}).get("mastery_band"),
        } for t in topics],
    }


@router.get("/topics/{topic_id}")
async def get_topic(topic_id: str, user=Depends(deps.optional_user)):
    topic = await catalog.get_topic(topic_id)
    subject = await catalog.get_subject(topic["subject_id"])
    questions = await catalog.questions_for(topic_id)
    mastery = None
    if user:
        mastery = await quiz_service.get_mastery_row(user["id"], topic_id)
    return {
        "subject": subject,
        "topic": topic,
        "question_count": len(questions),
        "mastery": mastery,
    }

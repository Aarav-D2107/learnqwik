"""Deterministic, explainable recommendations."""
from fastapi import APIRouter, Depends

import deps
from services import catalog, quiz_service, recommendation_service

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("")
async def recommendations(user=Depends(deps.current_user), subject_id: str = None,
                          topic_id: str = None, limit: int = 6):
    resources = (await catalog.resources_for_subject(subject_id)) if subject_id \
        else (await catalog.all_resources())
    mastery_rows = await quiz_service.all_mastery(user["id"])
    if subject_id:
        mastery_rows = [m for m in mastery_rows if m.get("subject_id") == subject_id]

    if topic_id:
        row = next((m for m in mastery_rows if m["topic_id"] == topic_id), None)
        items = recommendation_service.recommend_for_topic(
            resources, topic_id, (row or {}).get("mastery_pct", 0), limit=limit
        )
    else:
        items = recommendation_service.recommend_for_user(resources, mastery_rows, limit=limit)

    topics = {t["id"]: t["name"] for t in await catalog.all_topics()}
    for item in items:
        item["topic_name"] = topics.get(item.get("for_topic_id") or item.get("topic_id"))

    return {
        "recommendations": items,
        "weights": recommendation_service.RECOMMENDATION_WEIGHTS
        if hasattr(recommendation_service, "RECOMMENDATION_WEIGHTS") else None,
        "explainable": True,
        "empty_state": None if items else
        "Take an assessment and your recommendations will be scored against your actual mastery.",
    }

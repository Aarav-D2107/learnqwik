"""Roadmap: default (state 1) and personalized (state 2), with versioning."""
from fastapi import APIRouter, Depends

import db
import deps
from schemas.models import RoadmapRecomputeRequest
from services import quiz_service

router = APIRouter(prefix="/api/roadmap", tags=["roadmap"])


@router.get("")
async def get_roadmap(subject_id: str, user=Depends(deps.current_user)):
    return await quiz_service.get_roadmap(user["id"], subject_id)


@router.post("/recompute")
async def recompute(body: RoadmapRecomputeRequest, user=Depends(deps.ai_rate_limit)):
    return await quiz_service.recompute_roadmap(
        user["id"], body.subject_id,
        trigger={"attempt_id": body.trigger_attempt_id} if body.trigger_attempt_id else None,
        force=body.force,
    )


@router.get("/versions")
async def versions(subject_id: str, user=Depends(deps.current_user), limit: int = 10):
    rows = await db.select("roadmap_versions", {
        "select": "id,version_number,generated_by,trigger_attempt_id,changes_json,created_at",
        "user_id": "eq.%s" % user["id"],
        "subject_id": "eq.%s" % subject_id,
        "order": "version_number.desc",
        "limit": str(min(max(limit, 1), 50)),
    })
    return {"versions": rows}

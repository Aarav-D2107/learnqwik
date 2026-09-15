"""Health and readiness."""
from fastapi import APIRouter

import config
import db

router = APIRouter(tags=["health"])

VERSION = "1.0.0"


@router.get("/health")
async def health():
    """Liveness + dependency readiness. Never returns secret values, only booleans."""
    db_ok, db_error = await db.health()
    ai_ok = config.ai_configured()
    status = "healthy" if db_ok else "degraded"
    return {
        "status": status,
        "service": "learnqwik-api",
        "version": VERSION,
        "environment": config.ENVIRONMENT,
        "checks": {
            "database": {"ok": db_ok, "detail": db_error},
            "supabase_configured": config.supabase_configured(),
            "ai_configured": ai_ok,
            "ai_provider": config.AI_PROVIDER if ai_ok else None,
            "storage_bucket": config.STORAGE_BUCKET,
        },
    }


@router.get("/api/config")
async def public_config():
    """Non-secret runtime config the frontend needs (quiz rules, limits)."""
    return {
        "seconds_per_question": config.SECONDS_PER_QUESTION,
        "max_fullscreen_violations": config.MAX_FULLSCREEN_VIOLATIONS,
        "reassess_question_count": config.REASSESS_QUESTION_COUNT,
        "max_upload_size_mb": config.MAX_UPLOAD_SIZE_MB,
        "allowed_extensions": sorted(config.ALLOWED_EXTENSIONS),
        "mastery_bands": [{"max": m, "label": l} for m, l in config.MASTERY_BANDS],
        "ai_configured": config.ai_configured(),
    }

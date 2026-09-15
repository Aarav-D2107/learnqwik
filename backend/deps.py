"""
Request dependencies: authentication, quiz lockout, rate limiting.

The identity of the caller ALWAYS comes from the bearer token, verified against
Supabase. A `user_id` in a request body is never trusted and is never read.
"""
import time
from collections import defaultdict, deque

from fastapi import Depends, Header, Request

import config
import db
import errors


async def current_user(authorization: str = Header(default=None)):
    """Required auth. Returns the verified Supabase user record."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise errors.unauthorized("Sign in to continue.")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise errors.unauthorized("Sign in to continue.")

    try:
        user = await db.get_user_from_token(token)
    except db.DatabaseNotConfigured as exc:
        raise errors.unavailable(str(exc), code="SUPABASE_NOT_CONFIGURED")
    except db.DatabaseError:
        raise errors.unavailable("Authentication is temporarily unavailable.",
                                 code="AUTH_UNAVAILABLE")

    if not user or not user.get("id"):
        raise errors.unauthorized("Your session has expired. Please sign in again.",
                                  code="SESSION_EXPIRED")
    return user


async def optional_user(authorization: str = Header(default=None)):
    """For endpoints that work signed-out (subjects, topics, content)."""
    if not authorization:
        return None
    try:
        return await current_user(authorization)
    except Exception:
        return None


def user_id(user=Depends(current_user)):
    return user["id"]


# ------------------------------------------------------------------ Quiz lockout
async def assert_no_active_quiz(user):
    """
    The AI Tutor is unavailable during an active assessment. Hiding the UI is
    not enough — a student could call the API directly, so the backend enforces
    it too by checking for an in-progress attempt.
    """
    rows = await db.select("quiz_attempts", {
        "select": "id,status,started_at",
        "user_id": "eq.%s" % user["id"],
        "status": "eq.in_progress",
        "limit": "1",
    })
    if rows:
        raise errors.forbidden(
            "The AI Tutor is unavailable while an assessment is in progress. "
            "Submit your quiz first.",
            code="TUTOR_LOCKED_DURING_QUIZ",
        )


# ------------------------------------------------------------------ Rate limiting
_buckets = defaultdict(deque)


def _check(key, limit, window_seconds):
    now = time.time()
    bucket = _buckets[key]
    while bucket and now - bucket[0] > window_seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


async def ai_rate_limit(user=Depends(current_user)):
    """In-process limiter. Adequate for a single Render instance; swap for Redis
    if the backend is ever scaled horizontally."""
    if not _check("ai:%s" % user["id"], config.RATE_LIMIT_AI_PER_MINUTE, 60):
        raise errors.rate_limited(
            "You've hit the AI request limit for this minute. Give it a moment."
        )
    return user


async def upload_rate_limit(user=Depends(current_user)):
    if not _check("upload:%s" % user["id"], config.RATE_LIMIT_UPLOAD_PER_HOUR, 3600):
        raise errors.rate_limited("You've hit the upload limit for this hour.")
    return user


def reset_rate_limits():
    _buckets.clear()

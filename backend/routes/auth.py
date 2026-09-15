"""Authentication — thin proxy over Supabase Auth.

The backend never stores passwords and never issues its own tokens. It forwards
credentials to Supabase and hands the resulting session back to the browser.
"""
from fastapi import APIRouter, Depends, Header

import db
import deps
import errors
from schemas.models import AuthResponse, RefreshRequest, SignInRequest, SignUpRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def signup(body: SignUpRequest):
    try:
        status, data = await db.sign_up(body.email, body.password, body.full_name)
    except db.DatabaseNotConfigured as exc:
        raise errors.unavailable(str(exc), code="SUPABASE_NOT_CONFIGURED")
    if status >= 400:
        raise errors.bad_request(
            data.get("msg") or data.get("error_description") or "Could not create that account.",
            code="SIGNUP_FAILED",
        )

    session = data.get("session") or {}
    user = data.get("user") or data
    if user and user.get("id"):
        await _ensure_profile(user, body.full_name)

    if not session.get("access_token"):
        return AuthResponse(
            user=_public_user(user),
            message="Account created. Check your inbox to confirm your email, then sign in.",
        )
    return AuthResponse(
        access_token=session.get("access_token"),
        refresh_token=session.get("refresh_token"),
        expires_in=session.get("expires_in"),
        user=_public_user(user),
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: SignInRequest):
    try:
        status, data = await db.sign_in(body.email, body.password)
    except db.DatabaseNotConfigured as exc:
        raise errors.unavailable(str(exc), code="SUPABASE_NOT_CONFIGURED")
    if status >= 400:
        raise errors.unauthorized("That email and password didn't match.",
                                  code="INVALID_CREDENTIALS")
    user = data.get("user") or {}
    await _ensure_profile(user)
    return AuthResponse(
        access_token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        expires_in=data.get("expires_in"),
        user=_public_user(user),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh(body: RefreshRequest):
    """Exchanges a refresh token for a fresh access token, so a student is not
    signed out mid-assessment."""
    try:
        status, data = await db.refresh_session(body.refresh_token)
    except db.DatabaseNotConfigured as exc:
        raise errors.unavailable(str(exc), code="SUPABASE_NOT_CONFIGURED")
    if status >= 400 or not data.get("access_token"):
        raise errors.unauthorized("Your session has expired. Please sign in again.",
                                  code="SESSION_EXPIRED")
    return AuthResponse(
        access_token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        expires_in=data.get("expires_in"),
        user=_public_user(data.get("user") or {}),
    )


@router.post("/logout")
async def logout(authorization: str = Header(default=None)):
    if authorization and authorization.lower().startswith("bearer "):
        try:
            await db.sign_out(authorization.split(" ", 1)[1])
        except Exception:
            pass
    return {"signed_out": True}


@router.get("/me")
async def me(user=Depends(deps.current_user)):
    profile = await db.select_one("profiles", {"select": "*", "id": "eq.%s" % user["id"]})
    return {"user": _public_user(user), "profile": profile}


def _public_user(user):
    if not user:
        return None
    metadata = user.get("user_metadata") or {}
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "full_name": metadata.get("full_name") or (user.get("email") or "").split("@")[0],
    }


async def _ensure_profile(user, full_name=None):
    if not user or not user.get("id"):
        return
    metadata = user.get("user_metadata") or {}
    try:
        await db.insert("profiles", {
            "id": user["id"],
            "email": user.get("email"),
            "full_name": full_name or metadata.get("full_name")
                         or (user.get("email") or "").split("@")[0],
        }, upsert=True, on_conflict="id")
    except db.DatabaseError:
        pass

"""
Supabase access layer.

Talks to PostgREST, Storage and the Auth API over HTTPS with the service-role
key. This module is server-side only and the service-role key never leaves it.

Row Level Security still exists and is the real protection (see
database/schema.sql). Because the service role bypasses RLS, every query in
this file that touches user-owned data also filters on user_id explicitly —
defence in depth, so a mistake here can't become a data leak.
"""
import logging

import httpx

import config

log = logging.getLogger("learnqwik.db")


class DatabaseNotConfigured(RuntimeError):
    pass


class DatabaseError(RuntimeError):
    pass


def _require():
    if not config.supabase_configured():
        raise DatabaseNotConfigured(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
            "on the backend (see backend/.env.example)."
        )


def _rest_url(table):
    return "%s/rest/v1/%s" % (config.SUPABASE_URL.rstrip("/"), table)


def _headers(extra=None, prefer=None):
    h = {
        "apikey": config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": "Bearer %s" % config.SUPABASE_SERVICE_ROLE_KEY,
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    if extra:
        h.update(extra)
    return h


async def _request(method, url, **kwargs):
    _require()
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(method, url, **kwargs)
    except httpx.RequestError as exc:
        log.warning("Supabase transport failure: %s", type(exc).__name__)
        raise DatabaseError("Could not reach the database.")
    if resp.status_code >= 400:
        # Log the status only. Response bodies can echo row contents.
        log.warning("Supabase %s %s -> %s", method, url.split("?")[0], resp.status_code)
        raise DatabaseError("Database request failed (%s)." % resp.status_code)
    return resp


async def select(table, params=None):
    resp = await _request("GET", _rest_url(table), headers=_headers(), params=params or {})
    return resp.json()


async def select_one(table, params=None):
    rows = await select(table, {**(params or {}), "limit": "1"})
    return rows[0] if rows else None


async def insert(table, rows, upsert=False, on_conflict=None):
    prefer = "return=representation"
    if upsert:
        prefer += ",resolution=merge-duplicates"
    params = {"on_conflict": on_conflict} if on_conflict else None
    resp = await _request("POST", _rest_url(table), headers=_headers(prefer=prefer),
                          json=rows, params=params)
    data = resp.json()
    if isinstance(rows, dict):
        return data[0] if data else None
    return data


async def update(table, params, values):
    resp = await _request("PATCH", _rest_url(table), headers=_headers(prefer="return=representation"),
                          params=params, json=values)
    data = resp.json()
    return data[0] if data else None


async def delete(table, params):
    await _request("DELETE", _rest_url(table), headers=_headers(), params=params)


async def rpc(function_name, payload):
    url = "%s/rest/v1/rpc/%s" % (config.SUPABASE_URL.rstrip("/"), function_name)
    resp = await _request("POST", url, headers=_headers(), json=payload)
    return resp.json()


# ------------------------------------------------------------------ Auth
async def get_user_from_token(access_token):
    """
    Verifies a Supabase access token by asking Supabase who it belongs to.

    We deliberately do NOT decode the JWT locally and trust the claims — the
    identity always comes from Supabase itself, so a forged or revoked token
    can't impersonate a user.
    """
    _require()
    url = "%s/auth/v1/user" % config.SUPABASE_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers={
                "apikey": config.SUPABASE_ANON_KEY or config.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": "Bearer %s" % access_token,
            })
    except httpx.RequestError:
        raise DatabaseError("Could not reach the authentication service.")
    if resp.status_code == 401 or resp.status_code == 403:
        return None
    if resp.status_code >= 400:
        log.warning("Auth lookup returned %s", resp.status_code)
        return None
    return resp.json()


async def sign_up(email, password, full_name=None):
    _require()
    url = "%s/auth/v1/signup" % config.SUPABASE_URL.rstrip("/")
    body = {"email": email, "password": password}
    if full_name:
        body["data"] = {"full_name": full_name}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, headers={
            "apikey": config.SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        }, json=body)
    return resp.status_code, resp.json()


async def sign_in(email, password):
    _require()
    url = "%s/auth/v1/token?grant_type=password" % config.SUPABASE_URL.rstrip("/")
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, headers={
            "apikey": config.SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        }, json={"email": email, "password": password})
    return resp.status_code, resp.json()


async def refresh_session(refresh_token):
    _require()
    url = "%s/auth/v1/token?grant_type=refresh_token" % config.SUPABASE_URL.rstrip("/")
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, headers={
            "apikey": config.SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        }, json={"refresh_token": refresh_token})
    try:
        return resp.status_code, resp.json()
    except ValueError:
        return resp.status_code, {}


async def sign_out(access_token):
    _require()
    url = "%s/auth/v1/logout" % config.SUPABASE_URL.rstrip("/")
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(url, headers={
            "apikey": config.SUPABASE_ANON_KEY,
            "Authorization": "Bearer %s" % access_token,
        })


# ------------------------------------------------------------------ Storage
async def storage_upload(path, data, content_type):
    _require()
    url = "%s/storage/v1/object/%s/%s" % (
        config.SUPABASE_URL.rstrip("/"), config.STORAGE_BUCKET, path.lstrip("/"))
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers={
                "apikey": config.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": "Bearer %s" % config.SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": content_type or "application/octet-stream",
                "x-upsert": "true",
            }, content=data)
    except httpx.RequestError:
        raise DatabaseError("Could not reach storage.")
    if resp.status_code >= 400:
        log.warning("Storage upload returned %s", resp.status_code)
        raise DatabaseError("File could not be stored.")
    return path


async def storage_download(path):
    _require()
    url = "%s/storage/v1/object/%s/%s" % (
        config.SUPABASE_URL.rstrip("/"), config.STORAGE_BUCKET, path.lstrip("/"))
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(url, headers={
                "apikey": config.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": "Bearer %s" % config.SUPABASE_SERVICE_ROLE_KEY,
            })
    except httpx.RequestError:
        raise DatabaseError("Could not reach storage.")
    if resp.status_code >= 400:
        raise DatabaseError("File could not be retrieved from storage.")
    return resp.content


async def storage_delete(path):
    _require()
    url = "%s/storage/v1/object/%s/%s" % (
        config.SUPABASE_URL.rstrip("/"), config.STORAGE_BUCKET, path.lstrip("/"))
    async with httpx.AsyncClient(timeout=30) as client:
        await client.delete(url, headers={
            "apikey": config.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": "Bearer %s" % config.SUPABASE_SERVICE_ROLE_KEY,
        })


async def health():
    """Cheap connectivity probe used by GET /health."""
    try:
        await select("subjects", {"select": "id", "limit": "1"})
        return True, None
    except DatabaseNotConfigured as exc:
        return False, str(exc)
    except DatabaseError as exc:
        return False, str(exc)

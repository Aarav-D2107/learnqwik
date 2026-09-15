"""
Route-level tests. These need the real dependencies installed:

    pip install -r requirements.txt
    pytest -q

Supabase and the AI provider are both mocked — no live credentials, no network.
"""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import config  # noqa: E402
import db  # noqa: E402
import deps  # noqa: E402
from main import app  # noqa: E402
from services import ai_provider, quiz_service  # noqa: E402

FAKE_USER = {"id": "11111111-1111-1111-1111-111111111111", "email": "student@college.edu",
             "user_metadata": {"full_name": "Test Student"}}
AUTH = {"Authorization": "Bearer fake-token"}


@pytest.fixture
def client():
    deps.reset_rate_limits()
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def signed_in(monkeypatch):
    async def fake_user(access_token):
        return FAKE_USER if access_token == "fake-token" else None
    monkeypatch.setattr(db, "get_user_from_token", fake_user)
    monkeypatch.setattr(config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_SERVICE_ROLE_KEY", "service-role")
    return FAKE_USER


# ---------------------------------------------------------------- Health
def test_health_is_reachable(client, monkeypatch):
    async def fake_health():
        return True, None
    monkeypatch.setattr(db, "health", fake_health)

    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "learnqwik-api"
    assert "database" in body["checks"]


def test_health_reports_degraded_without_database(client, monkeypatch):
    async def fake_health():
        return False, "Supabase is not configured."
    monkeypatch.setattr(db, "health", fake_health)
    assert client.get("/health").json()["status"] == "degraded"


def test_health_never_leaks_secrets(client, monkeypatch):
    async def fake_health():
        return True, None
    monkeypatch.setattr(db, "health", fake_health)
    monkeypatch.setattr(config, "AI_API_KEY", "sk-super-secret-value")
    monkeypatch.setattr(config, "SUPABASE_SERVICE_ROLE_KEY", "service-role-secret")

    raw = client.get("/health").text
    assert "sk-super-secret-value" not in raw
    assert "service-role-secret" not in raw


def test_public_config_exposes_rules_not_secrets(client, monkeypatch):
    monkeypatch.setattr(config, "AI_API_KEY", "sk-secret")
    body = client.get("/api/config").json()
    assert body["max_fullscreen_violations"] == config.MAX_FULLSCREEN_VIOLATIONS
    assert body["ai_configured"] is True
    assert "sk-secret" not in client.get("/api/config").text


def test_docs_are_served(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


# ---------------------------------------------------------------- Auth
def test_protected_route_rejects_anonymous(client):
    response = client.get("/api/analytics/overview")
    assert response.status_code == 401
    assert response.json()["error"] in ("NOT_AUTHENTICATED", "SESSION_EXPIRED")


def test_protected_route_rejects_bad_token(client, signed_in):
    response = client.get("/api/analytics/overview", headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401


def test_malformed_auth_header_rejected(client, signed_in):
    assert client.get("/api/analytics/overview",
                      headers={"Authorization": "fake-token"}).status_code == 401


def test_client_supplied_user_id_is_ignored(client, signed_in, monkeypatch):
    """The whole point: a user_id in the body must never influence whose data is used."""
    captured = {}

    async def fake_select(table, params=None):
        captured["params"] = params or {}
        return []
    monkeypatch.setattr(db, "select", fake_select)

    client.get("/api/analytics/overview", headers=AUTH)
    assert "eq.%s" % FAKE_USER["id"] in str(captured["params"])


# ---------------------------------------------------------------- Validation
def test_quiz_start_validates_mode(client, signed_in):
    response = client.post("/api/quiz/start", headers=AUTH,
                           json={"subject_id": "java", "topic_id": "java-oop",
                                 "mode": "cheat-mode"})
    assert response.status_code == 422
    assert response.json()["error"] == "VALIDATION_ERROR"


def test_tutor_rejects_empty_message(client, signed_in):
    response = client.post("/api/ai/tutor", headers=AUTH,
                           json={"message": "", "topic": "java-oop"})
    assert response.status_code == 422


def test_signup_rejects_short_password(client):
    response = client.post("/api/auth/signup",
                           json={"email": "a@b.com", "password": "short"})
    assert response.status_code == 422


def test_signup_rejects_invalid_email(client):
    response = client.post("/api/auth/signup",
                           json={"email": "not-an-email", "password": "longenough123"})
    assert response.status_code == 422


# ---------------------------------------------------------------- Tutor lockout
def test_tutor_blocked_during_active_quiz(client, signed_in, monkeypatch):
    async def fake_select(table, params=None):
        if table == "quiz_attempts":
            return [{"id": "attempt-1", "status": "in_progress"}]
        return []
    monkeypatch.setattr(db, "select", fake_select)

    response = client.post("/api/ai/tutor", headers=AUTH,
                           json={"message": "What is polymorphism?", "topic": "java-oop"})
    assert response.status_code == 403
    assert response.json()["error"] == "TUTOR_LOCKED_DURING_QUIZ"


def test_tutor_available_when_no_quiz_running(client, signed_in, monkeypatch):
    """Not blocked by the lock — it fails later, on the AI call, which is the point."""
    async def fake_select(table, params=None):
        if table == "quiz_attempts":
            return []
        if table == "topics":
            return [{"id": "java-oop", "subject_id": "java", "name": "OOP", "content": {}}]
        if table == "subjects":
            return [{"id": "java", "name": "Java"}]
        return []
    monkeypatch.setattr(db, "select", fake_select)
    monkeypatch.setattr(config, "AI_API_KEY", "")
    ai_provider.reset_provider_cache()

    response = client.post("/api/ai/tutor", headers=AUTH,
                           json={"message": "What is polymorphism?", "topic": "java-oop"})
    assert response.status_code != 403


# ---------------------------------------------------------------- AI degradation
def test_missing_ai_credentials_give_a_clear_error(client, signed_in, monkeypatch):
    async def fake_select(table, params=None):
        if table == "quiz_attempts":
            return []
        if table == "topics":
            return [{"id": "java-oop", "subject_id": "java", "name": "OOP", "content": {}}]
        if table == "subjects":
            return [{"id": "java", "name": "Java"}]
        return []
    monkeypatch.setattr(db, "select", fake_select)
    monkeypatch.setattr(config, "AI_API_KEY", "")
    ai_provider.reset_provider_cache()

    response = client.post("/api/ai/tutor", headers=AUTH,
                           json={"message": "Explain inheritance", "topic": "java-oop"})
    assert response.status_code == 503
    body = response.json()
    assert body["error"] == "AI_NOT_CONFIGURED"
    assert "AI_API_KEY" in body["message"]


def test_no_canned_ai_response_is_ever_returned(client, signed_in, monkeypatch):
    """Without credentials the tutor must ERROR, never fabricate an answer."""
    async def fake_select(table, params=None):
        if table == "quiz_attempts":
            return []
        if table == "topics":
            return [{"id": "java-oop", "subject_id": "java", "name": "OOP", "content": {}}]
        if table == "subjects":
            return [{"id": "java", "name": "Java"}]
        return []
    monkeypatch.setattr(db, "select", fake_select)
    monkeypatch.setattr(config, "AI_API_KEY", "")
    ai_provider.reset_provider_cache()

    body = client.post("/api/ai/tutor", headers=AUTH,
                       json={"message": "Explain inheritance", "topic": "java-oop"}).json()
    assert "reply" not in body


# ---------------------------------------------------------------- Errors
def test_unknown_route_is_structured_json(client):
    body = client.get("/api/does-not-exist").json()
    assert body["error"] == "NOT_FOUND"


def test_errors_never_contain_tracebacks(client, signed_in, monkeypatch):
    async def explode(table, params=None):
        raise RuntimeError("psycopg2.errors.UndefinedTable: relation does not exist")
    monkeypatch.setattr(db, "select", explode)

    response = client.get("/api/analytics/overview", headers=AUTH)
    assert response.status_code == 500
    assert "Traceback" not in response.text
    assert "psycopg2" not in response.text
    assert response.json()["error"] == "INTERNAL_ERROR"


# ---------------------------------------------------------------- CORS
def test_cors_never_uses_wildcard_in_production(monkeypatch):
    monkeypatch.setattr(config, "ENVIRONMENT", "production")
    monkeypatch.setattr(config, "FRONTEND_URL", "https://learnqwik.vercel.app")
    origins = config.cors_origins()
    assert "*" not in origins
    assert "https://learnqwik.vercel.app" in origins
    assert not any("localhost" in o for o in origins)


def test_cors_allows_localhost_in_development(monkeypatch):
    monkeypatch.setattr(config, "ENVIRONMENT", "development")
    assert any("localhost" in o for o in config.cors_origins())


# ---------------------------------------------------------------- Rate limiting
def test_ai_rate_limit_eventually_fires(client, signed_in, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_AI_PER_MINUTE", 2)

    async def fake_select(table, params=None):
        return []
    monkeypatch.setattr(db, "select", fake_select)

    statuses = [
        client.post("/api/ai/tutor", headers=AUTH,
                    json={"message": "hi", "topic": "java-oop"}).status_code
        for _ in range(4)
    ]
    assert 429 in statuses

"""
LearnQwik API.

Run locally:   uvicorn main:app --reload --port 8000
Run on Render: uvicorn main:app --host 0.0.0.0 --port $PORT
Swagger docs:  /docs
"""
import logging

from fastapi import FastAPI, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

import config
import errors
from routes import analytics, auth, health, quiz, recommendations, roadmap, subjects, tutor, uploads

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("learnqwik")

app = FastAPI(
    title="LearnQwik API",
    version=health.VERSION,
    description=(
        "Backend for LearnQwik — assessment, difficulty-weighted mastery, an explainable "
        "recommendation engine, AI-personalized roadmaps, and hybrid text + vision "
        "document intelligence."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Explicit origins only — never "*", because credentials are allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)

app.add_exception_handler(StarletteHTTPException, errors.http_exception_handler)
app.add_exception_handler(RequestValidationError, errors.validation_exception_handler)
app.add_exception_handler(Exception, errors.unhandled_exception_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(subjects.router)
app.include_router(quiz.router)
app.include_router(analytics.router)
app.include_router(recommendations.router)
app.include_router(roadmap.router)
app.include_router(tutor.router)
app.include_router(uploads.router)


@app.on_event("startup")
async def startup():
    log.info("LearnQwik API starting in %s mode", config.ENVIRONMENT)
    log.info("CORS origins: %s", ", ".join(config.cors_origins()) or "(none)")
    if not config.supabase_configured():
        log.warning("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set — "
                    "database-backed endpoints will return 503.")
    if not config.ai_configured():
        log.warning("AI_API_KEY is not set — AI Tutor, summaries, Vision analysis and "
                    "document quizzes will return 503. Roadmaps fall back to the "
                    "deterministic planner.")


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "learnqwik-api",
        "version": health.VERSION,
        "docs": "/docs",
        "health": "/health",
    }

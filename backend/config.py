"""
LearnQwik — central configuration.

Every tunable constant lives here and is overridable with an environment
variable. Nothing in this module imports third-party packages, so it can be
imported by the pure-logic services and by the offline self-check.
"""
import os


def _f(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


def _i(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return int(default)


def _b(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------- Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "learnqwik-documents")

# ---------------------------------------------------------------- AI provider
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic").strip().lower()
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "")
TEXT_MODEL = os.getenv("TEXT_MODEL", "claude-sonnet-4-6")
VISION_MODEL = os.getenv("VISION_MODEL", "claude-sonnet-4-6")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "")
AI_TIMEOUT_SECONDS = _i("AI_TIMEOUT_SECONDS", 90)
AI_MAX_OUTPUT_TOKENS = _i("AI_MAX_OUTPUT_TOKENS", 2000)

# ---------------------------------------------------------------- Networking
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
EXTRA_CORS_ORIGINS = os.getenv("EXTRA_CORS_ORIGINS", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()

# ---------------------------------------------------------------- Quiz rules
SECONDS_PER_QUESTION = _i("SECONDS_PER_QUESTION", 60)
MAX_FULLSCREEN_VIOLATIONS = _i("MAX_FULLSCREEN_VIOLATIONS", 3)
REASSESS_QUESTION_COUNT = _i("REASSESS_QUESTION_COUNT", 4)
MIN_QUESTIONS_PER_QUIZ = _i("MIN_QUESTIONS_PER_QUIZ", 5)
MAX_QUESTIONS_PER_QUIZ = _i("MAX_QUESTIONS_PER_QUIZ", 10)

# ---------------------------------------------------------------- Scoring
DIFFICULTY_WEIGHTS = {
    "Easy": _f("DIFFICULTY_WEIGHT_EASY", 1.0),
    "Medium": _f("DIFFICULTY_WEIGHT_MEDIUM", 1.5),
    "Hard": _f("DIFFICULTY_WEIGHT_HARD", 2.0),
}
RECENT_WEIGHT = _f("RECENT_WEIGHT", 0.7)
HISTORICAL_WEIGHT = _f("HISTORICAL_WEIGHT", 0.3)

# (upper_bound_inclusive, label)
MASTERY_BANDS = [
    (_i("MASTERY_BAND_WEAK_MAX", 39), "Weak"),
    (_i("MASTERY_BAND_STRUGGLING_MAX", 59), "Struggling"),
    (_i("MASTERY_BAND_DEVELOPING_MAX", 79), "Developing"),
    (100, "Mastered"),
]
WEAK_TOPIC_THRESHOLD = _i("WEAK_TOPIC_THRESHOLD", 60)

# ---------------------------------------------------------------- Recommendations
RECOMMENDATION_WEIGHTS = {
    "topic_relevance": _f("REC_W_TOPIC_RELEVANCE", 0.40),
    "difficulty_match": _f("REC_W_DIFFICULTY_MATCH", 0.20),
    "quality": _f("REC_W_QUALITY", 0.15),
    "format_preference": _f("REC_W_FORMAT_PREFERENCE", 0.15),
    "duration_fit": _f("REC_W_DURATION_FIT", 0.10),
}
IDEAL_DURATION_MINUTES = _i("IDEAL_DURATION_MINUTES", 20)

# ---------------------------------------------------------------- Uploads
MAX_UPLOAD_SIZE_MB = _i("MAX_UPLOAD_SIZE_MB", 20)
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
MAX_VISION_PAGES = _i("MAX_VISION_PAGES", 12)
VISION_RENDER_DPI = _i("VISION_RENDER_DPI", 130)
CHUNK_TARGET_CHARS = _i("CHUNK_TARGET_CHARS", 1100)
CHUNK_OVERLAP_CHARS = _i("CHUNK_OVERLAP_CHARS", 150)
RETRIEVAL_TOP_K = _i("RETRIEVAL_TOP_K", 6)
USE_EMBEDDINGS = _b("USE_EMBEDDINGS", False)

DOCUMENT_EXTENSIONS = {
    "pdf": "application/pdf",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}
SOURCE_EXTENSIONS = {
    "py": "text/x-python",
    "java": "text/x-java-source",
    "c": "text/x-c",
    "cpp": "text/x-c++src",
    "js": "text/javascript",
    "ts": "text/x-typescript",
    "html": "text/html",
    "css": "text/css",
    "sql": "application/sql",
}
ALLOWED_EXTENSIONS = {**DOCUMENT_EXTENSIONS, **SOURCE_EXTENSIONS}

# ---------------------------------------------------------------- Rate limiting
RATE_LIMIT_AI_PER_MINUTE = _i("RATE_LIMIT_AI_PER_MINUTE", 20)
RATE_LIMIT_UPLOAD_PER_HOUR = _i("RATE_LIMIT_UPLOAD_PER_HOUR", 30)


def cors_origins() -> list:
    """Explicit allow-list. Never '*' — credentials are enabled."""
    origins = {FRONTEND_URL.rstrip("/")} if FRONTEND_URL else set()
    for extra in EXTRA_CORS_ORIGINS.split(","):
        extra = extra.strip().rstrip("/")
        if extra:
            origins.add(extra)
    if ENVIRONMENT != "production":
        origins.update({
            "http://localhost:8080", "http://127.0.0.1:8080",
            "http://localhost:3000", "http://127.0.0.1:3000",
            "http://localhost:5500", "http://127.0.0.1:5500",
        })
    return sorted(o for o in origins if o)


def ai_configured() -> bool:
    return bool(AI_API_KEY) and bool(AI_PROVIDER)


def supabase_configured() -> bool:
    return bool(SUPABASE_URL) and bool(SUPABASE_SERVICE_ROLE_KEY)

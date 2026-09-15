"""Pydantic models for request validation and response shaping."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ------------------------------------------------------------------ Auth
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=120)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=4096)


class AuthResponse(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    user: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


# ------------------------------------------------------------------ Quiz
class QuizStartRequest(BaseModel):
    subject_id: str = Field(max_length=64)
    topic_id: str = Field(max_length=64)
    mode: str = Field(default="quiz")
    question_count: Optional[int] = Field(default=None, ge=3, le=15)

    @field_validator("mode")
    @classmethod
    def _mode(cls, v):
        if v not in ("quiz", "reassess"):
            raise ValueError("mode must be 'quiz' or 'reassess'")
        return v


class QuizAnswerRequest(BaseModel):
    question_id: str = Field(max_length=64)
    selected_index: Optional[int] = Field(default=None, ge=0, le=9)
    response_time_ms: Optional[int] = Field(default=None, ge=0, le=3_600_000)


class QuizCompleteRequest(BaseModel):
    fullscreen_violations: int = Field(default=0, ge=0, le=100)
    auto_submitted: bool = False
    time_used_seconds: Optional[int] = Field(default=None, ge=0, le=86_400)


# ------------------------------------------------------------------ Roadmap
class RoadmapRecomputeRequest(BaseModel):
    subject_id: str = Field(max_length=64)
    trigger_attempt_id: Optional[str] = Field(default=None, max_length=64)
    force: bool = False


class ReassessRequest(BaseModel):
    subject_id: str = Field(max_length=64)
    topic_id: str = Field(max_length=64)
    question_count: Optional[int] = Field(default=None, ge=3, le=15)


# ------------------------------------------------------------------ AI
class TutorMessage(BaseModel):
    role: str = Field(max_length=16)
    content: str = Field(max_length=6000)


class TutorRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    subject: Optional[str] = Field(default=None, max_length=64)
    topic: Optional[str] = Field(default=None, max_length=64)
    conversation: List[TutorMessage] = Field(default_factory=list, max_length=40)
    document_id: Optional[str] = Field(default=None, max_length=64)
    page_context: Optional[int] = Field(default=None, ge=1, le=10_000)


class ExplainRequest(BaseModel):
    attempt_id: str = Field(max_length=64)


class LearningPlanRequest(BaseModel):
    subject_id: str = Field(max_length=64)


# ------------------------------------------------------------------ Documents
class DocumentQuizRequest(BaseModel):
    question_count: int = Field(default=8, ge=3, le=15)
    regenerate: bool = False


class DocumentAskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation: List[TutorMessage] = Field(default_factory=list, max_length=40)
    page_context: Optional[int] = Field(default=None, ge=1, le=10_000)


class SummaryRequest(BaseModel):
    regenerate: bool = False


# ------------------------------------------------------------------ Responses
class HealthResponse(BaseModel):
    status: str
    service: str = "learnqwik-api"
    version: str
    checks: Dict[str, Any]


class ErrorResponse(BaseModel):
    error: str
    message: str

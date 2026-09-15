"""
Structured error responses.

Users see a stable machine-readable code and a sentence they can act on.
They never see a Python traceback, a provider message, or a database detail.
"""
import logging

from fastapi import HTTPException
from fastapi.responses import JSONResponse

log = logging.getLogger("learnqwik")


class AppError(HTTPException):
    def __init__(self, code, message, status_code=400):
        super().__init__(status_code=status_code, detail={"error": code, "message": message})
        self.code = code
        self.message = message


def bad_request(message, code="BAD_REQUEST"):
    return AppError(code, message, 400)


def unauthorized(message="You need to sign in to do that.", code="NOT_AUTHENTICATED"):
    return AppError(code, message, 401)


def forbidden(message="You don't have access to that.", code="FORBIDDEN"):
    return AppError(code, message, 403)


def not_found(message="That wasn't found.", code="NOT_FOUND"):
    return AppError(code, message, 404)


def too_large(message, code="FILE_TOO_LARGE"):
    return AppError(code, message, 413)


def rate_limited(message="Too many requests. Please slow down.", code="RATE_LIMITED"):
    return AppError(code, message, 429)


def unavailable(message, code="SERVICE_UNAVAILABLE"):
    return AppError(code, message, 503)


async def http_exception_handler(request, exc):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": _code_for(exc.status_code), "message": str(detail)},
    )


async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Some fields in that request weren't valid.",
            "fields": [
                {"field": ".".join(str(p) for p in e.get("loc", [])[1:]), "issue": e.get("msg")}
                for e in exc.errors()[:10]
            ],
        },
    )


async def unhandled_exception_handler(request, exc):
    # Log the type and path only — never the payload, which may contain
    # document contents or tokens.
    log.exception("Unhandled %s on %s", type(exc).__name__, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "Something went wrong on our side. Please try again.",
        },
    )


def _code_for(status):
    return {
        400: "BAD_REQUEST", 401: "NOT_AUTHENTICATED", 403: "FORBIDDEN",
        404: "NOT_FOUND", 413: "FILE_TOO_LARGE", 429: "RATE_LIMITED",
        500: "INTERNAL_ERROR", 503: "SERVICE_UNAVAILABLE",
    }.get(status, "ERROR")

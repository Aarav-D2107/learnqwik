"""
Study Your Own Material — upload, processing, summary, document quiz, ask.

Every route is scoped to the authenticated owner. Files live under
users/{user_id}/documents/{file_id}/ in a private Supabase Storage bucket.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

import config
import db
import deps
import errors
from schemas.models import DocumentAskRequest, DocumentQuizRequest, SummaryRequest
from services import document_parser as dp
from services import document_service, question_generator, summarizer, tutor_service
from services.ai_provider import AIError

router = APIRouter(prefix="/api/uploads", tags=["documents"])


def _now():
    return datetime.now(timezone.utc).isoformat()


def _ai_error(exc):
    return errors.AppError(exc.code, exc.message, exc.http_status)


@router.post("")
async def upload(background: BackgroundTasks, file: UploadFile = File(...),
                 user=Depends(deps.upload_rate_limit)):
    filename = file.filename or "upload"

    try:
        ext = dp.detect_extension(filename, file.content_type)
    except dp.UnsupportedFileError as exc:
        raise errors.bad_request(str(exc), code="UNSUPPORTED_FILE_TYPE")

    data = await file.read()
    size = len(data)
    if size == 0:
        raise errors.bad_request("That file is empty.", code="EMPTY_FILE")
    if size > config.MAX_UPLOAD_SIZE_BYTES:
        raise errors.too_large(
            "That file is %.1f MB. The limit is %d MB."
            % (size / 1024 / 1024, config.MAX_UPLOAD_SIZE_MB)
        )
    # The filename alone is never trusted — check the magic number too.
    if not dp.sniff_mime(data, ext):
        raise errors.bad_request(
            "That file's contents don't match its .%s extension." % ext,
            code="FILE_TYPE_MISMATCH",
        )

    file_id = str(uuid.uuid4())
    path = document_service.storage_path(user["id"], file_id, ext)

    try:
        await db.storage_upload(path, data, config.ALLOWED_EXTENSIONS.get(ext))
    except db.DatabaseNotConfigured as exc:
        raise errors.unavailable(str(exc), code="SUPABASE_NOT_CONFIGURED")
    except db.DatabaseError:
        raise errors.unavailable("The file could not be stored. Please try again.",
                                 code="STORAGE_UNAVAILABLE")

    record = {
        "id": file_id,
        "user_id": user["id"],
        "filename": "original.%s" % ext,
        "original_filename": filename[:255],
        "file_type": ext,
        "storage_path": path,
        "file_size": size,
        "status": document_service.STATUS_UPLOADING,
        "created_at": _now(),
    }
    await db.insert("uploaded_files", record)

    # Processing continues after the response so the browser can start polling
    # /status immediately and show real stages.
    background.add_task(document_service.process, file_id, user["id"], data, filename)

    return {
        "file_id": file_id,
        "original_filename": filename,
        "file_type": ext,
        "file_size": size,
        "status": document_service.STATUS_UPLOADING,
        "status_url": "/api/uploads/%s/status" % file_id,
    }


@router.get("")
async def list_uploads(user=Depends(deps.current_user)):
    rows = await db.select("uploaded_files", {
        "select": "id,original_filename,file_type,file_size,status,page_count,"
                  "error_message,created_at,processed_at",
        "user_id": "eq.%s" % user["id"],
        "order": "created_at.desc",
        "limit": "100",
    })
    return {"uploads": rows}


@router.get("/{file_id}")
async def get_upload(file_id: str, user=Depends(deps.current_user)):
    document = await _require_document(file_id, user)
    pages = await document_service.load_pages(file_id, user["id"])
    return {
        "document": {k: v for k, v in document.items() if k != "storage_path"},
        "pages": [{
            "page_number": p["page_number"],
            "content_quality": p.get("content_quality"),
            "important_visuals": p.get("important_visuals"),
            "analysis_source": p.get("analysis_source"),
            "has_text": bool((p.get("extracted_text") or "").strip()),
            "has_visual_analysis": bool(p.get("visual_analysis")),
        } for p in pages],
    }


@router.get("/{file_id}/status")
async def status(file_id: str, user=Depends(deps.current_user)):
    document = await _require_document(file_id, user)
    return document_service.status_payload(document)


@router.delete("/{file_id}")
async def delete_upload(file_id: str, user=Depends(deps.current_user)):
    document = await _require_document(file_id, user)
    try:
        await db.storage_delete(document["storage_path"])
    except Exception:
        pass
    await db.delete("document_chunks", {"uploaded_file_id": "eq.%s" % file_id,
                                        "user_id": "eq.%s" % user["id"]})
    await db.delete("document_pages", {"uploaded_file_id": "eq.%s" % file_id,
                                       "user_id": "eq.%s" % user["id"]})
    await db.delete("uploaded_files", {"id": "eq.%s" % file_id, "user_id": "eq.%s" % user["id"]})
    return {"deleted": True}


@router.post("/{file_id}/summary")
async def summary(file_id: str, body: SummaryRequest = SummaryRequest(),
                  user=Depends(deps.ai_rate_limit)):
    document = await _require_ready(file_id, user)

    if not body.regenerate:
        cached = await db.select_one("document_summaries", {
            "select": "*", "uploaded_file_id": "eq.%s" % file_id,
            "user_id": "eq.%s" % user["id"],
        })
        if cached and cached.get("summary_json"):
            return {"summary": cached["summary_json"], "cached": True,
                    "document": _doc_brief(document)}

    pages = await document_service.load_pages(file_id, user["id"])
    try:
        result = await summarizer.summarize(document, pages)
    except AIError as exc:
        raise _ai_error(exc)
    except ValueError as exc:
        raise errors.bad_request(str(exc), code="NO_CONTENT")

    try:
        await db.insert("document_summaries", {
            "uploaded_file_id": file_id, "user_id": user["id"],
            "summary_json": result, "created_at": _now(),
        }, upsert=True, on_conflict="uploaded_file_id")
    except db.DatabaseError:
        pass

    return {"summary": result, "cached": False, "document": _doc_brief(document),
            "markdown": summarizer.to_markdown(result, document["original_filename"])}


@router.post("/{file_id}/quiz")
async def document_quiz(file_id: str, body: DocumentQuizRequest = DocumentQuizRequest(),
                        user=Depends(deps.ai_rate_limit)):
    document = await _require_ready(file_id, user)

    if not body.regenerate:
        cached = await db.select_one("generated_quizzes", {
            "select": "*", "uploaded_file_id": "eq.%s" % file_id,
            "user_id": "eq.%s" % user["id"], "order": "created_at.desc",
        })
        if cached and cached.get("questions_json"):
            return {"questions": _strip_answers(cached["questions_json"]),
                    "quiz_id": cached["id"], "cached": True,
                    "document": _doc_brief(document)}

    pages = await document_service.load_pages(file_id, user["id"])
    try:
        questions = await question_generator.generate(document, pages, body.question_count)
    except AIError as exc:
        raise _ai_error(exc)
    except ValueError as exc:
        raise errors.bad_request(str(exc), code="QUIZ_GENERATION_FAILED")

    quiz_id = str(uuid.uuid4())
    try:
        await db.insert("generated_quizzes", {
            "id": quiz_id, "uploaded_file_id": file_id, "user_id": user["id"],
            "questions_json": questions, "question_count": len(questions),
            "created_at": _now(),
        })
    except db.DatabaseError:
        pass

    return {"questions": _strip_answers(questions), "quiz_id": quiz_id,
            "cached": False, "document": _doc_brief(document)}


@router.post("/{file_id}/quiz/{quiz_id}/grade")
async def grade_document_quiz(file_id: str, quiz_id: str, answers: dict,
                              user=Depends(deps.current_user)):
    """Grading stays server-side: the browser never receives the answer key."""
    row = await db.select_one("generated_quizzes", {
        "select": "*", "id": "eq.%s" % quiz_id, "user_id": "eq.%s" % user["id"],
    })
    if not row:
        raise errors.not_found("That quiz wasn't found.", code="QUIZ_NOT_FOUND")

    questions = row["questions_json"]
    selected = answers.get("answers") or []
    from services import scoring_service
    normalized = [{"difficulty": q.get("difficulty"), "correct_index": q.get("correct_index")}
                  for q in questions]
    result = scoring_service.score_attempt(selected, normalized)
    return {
        "score": result,
        "review": [{
            "question": q["question"],
            "options": q["options"],
            "correct_index": q["correct_index"],
            "selected_index": selected[i] if i < len(selected) else None,
            "explanation": q.get("explanation"),
            "source_page": q.get("source_page"),
            "source_type": q.get("source_type"),
        } for i, q in enumerate(questions)],
    }


@router.post("/{file_id}/ask")
async def ask(file_id: str, body: DocumentAskRequest, user=Depends(deps.ai_rate_limit)):
    """Document-grounded tutor. Retrieval first, then a strictly grounded answer."""
    await deps.assert_no_active_quiz(user)
    document = await _require_ready(file_id, user)

    chunks = await document_service.retrieve_context(
        file_id, user["id"], body.message, body.page_context
    )
    if not chunks:
        return {"reply": "I couldn't find that in your uploaded material.",
                "grounded": True, "sources": []}

    context = tutor_service.build_document_context(document, chunks, body.page_context)
    try:
        reply = await tutor_service.answer(
            body.message, context, [m.model_dump() for m in body.conversation],
            document_mode=True,
        )
    except AIError as exc:
        raise _ai_error(exc)

    try:
        await db.insert("ai_conversations", {
            "user_id": user["id"], "uploaded_file_id": file_id,
            "user_message": body.message[:4000], "assistant_message": reply[:8000],
            "page_context": body.page_context,
        })
    except Exception:
        pass

    return {
        "reply": reply,
        "grounded": True,
        "sources": [{"page_number": c.get("page_number"), "source": c.get("source"),
                     "content_type": c.get("content_type")} for c in chunks],
    }


# ------------------------------------------------------------------ helpers
async def _require_document(file_id, user):
    document = await document_service.get_document(file_id, user["id"])
    if not document:
        raise errors.not_found("That document wasn't found in your library.",
                               code="DOCUMENT_NOT_FOUND")
    return document


async def _require_ready(file_id, user):
    document = await _require_document(file_id, user)
    if document.get("status") == document_service.STATUS_FAILED:
        raise errors.bad_request(
            document.get("error_message") or "That document failed to process.",
            code="DOCUMENT_FAILED",
        )
    if document.get("status") != document_service.STATUS_READY:
        raise errors.bad_request("That document is still processing.",
                                 code="DOCUMENT_NOT_READY")
    return document


def _doc_brief(document):
    return {"file_id": document["id"], "original_filename": document["original_filename"],
            "file_type": document.get("file_type"), "page_count": document.get("page_count")}


def _strip_answers(questions):
    return [{
        "index": i,
        "question": q["question"],
        "options": q["options"],
        "difficulty": q.get("difficulty"),
        "source_page": q.get("source_page"),
        "source_type": q.get("source_type"),
    } for i, q in enumerate(questions)]

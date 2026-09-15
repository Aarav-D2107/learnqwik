"""
Document processing orchestration.

Runs the real pipeline and writes a real status after each stage, so the
frontend's progress display reflects work that actually happened:

    uploading -> extracting_text -> analyzing_visuals -> building_understanding
              -> indexing -> ready   (or: failed, with a usable explanation)

Vision is invoked only for pages the classifier flagged, capped by
MAX_VISION_PAGES, and every analysis is cached by image hash.
"""
import logging

import config
import db
from services import document_parser as dp
from services import document_retriever, vision_service
from services.ai_provider import AIError, AINotConfiguredError, get_provider

log = logging.getLogger("learnqwik.documents")

STATUS_UPLOADING = "uploading"
STATUS_EXTRACTING = "extracting_text"
STATUS_VISION = "analyzing_visuals"
STATUS_UNDERSTANDING = "building_understanding"
STATUS_INDEXING = "indexing"
STATUS_READY = "ready"
STATUS_FAILED = "failed"

STAGE_LABELS = {
    STATUS_UPLOADING: "Uploading",
    STATUS_EXTRACTING: "Extracting text",
    STATUS_VISION: "Analyzing visual content",
    STATUS_UNDERSTANDING: "Building document understanding",
    STATUS_INDEXING: "Indexing material",
    STATUS_READY: "Ready",
    STATUS_FAILED: "Processing failed",
}
STAGE_ORDER = [STATUS_UPLOADING, STATUS_EXTRACTING, STATUS_VISION,
               STATUS_UNDERSTANDING, STATUS_INDEXING, STATUS_READY]


def storage_path(user_id, file_id, ext):
    return "users/%s/documents/%s/original.%s" % (user_id, file_id, ext)


async def _set_status(file_id, status, **extra):
    values = {"status": status}
    values.update(extra)
    try:
        await db.update("uploaded_files", {"id": "eq.%s" % file_id}, values)
    except db.DatabaseError:
        log.warning("Could not persist status %s for file %s", status, file_id)


async def process(file_id, user_id, raw_bytes, filename):
    """
    The full pipeline. Runs in a background task; every stage persists its own
    status so GET /api/uploads/{id}/status is truthful rather than animated.
    """
    try:
        await _set_status(file_id, STATUS_EXTRACTING)
        ext, pages = dp.parse(raw_bytes, filename)
        await _set_status(file_id, STATUS_EXTRACTING, page_count=len(pages))

        # ---- Vision, only where the classifier says it's needed
        vision_pages = vision_service.select_pages_for_vision(pages)
        vision_used = 0
        vision_error = None

        if vision_pages:
            await _set_status(file_id, STATUS_VISION)
            cache = {}
            for page in vision_pages:
                try:
                    analysis = await vision_service.analyze_page(raw_bytes, ext, page, cache=cache)
                except AINotConfiguredError as exc:
                    vision_error = str(exc)
                    break
                except AIError as exc:
                    vision_error = exc.message
                    break
                if analysis:
                    page["visual_analysis"] = analysis
                    page["analysis_source"] = (["text_model"] if page.get("extracted_text") else []) + ["vision_model"]
                    vision_used += 1
        for page in pages:
            page.setdefault("analysis_source", ["text_model"] if page.get("extracted_text") else [])
            page.setdefault("visual_analysis", None)
            page.setdefault("important_visuals", bool(page.get("visual_analysis")))

        await _set_status(file_id, STATUS_UNDERSTANDING)

        readable = any((p.get("extracted_text") or "").strip() or p.get("visual_analysis")
                       for p in pages)
        if not readable:
            message = ("No readable content could be extracted from this file. "
                       "If it's a scanned document, Vision analysis is required — "
                       + (vision_error or "check that AI credentials are configured."))
            await _set_status(file_id, STATUS_FAILED, error_message=message)
            return

        # ---- Chunk + index
        await _set_status(file_id, STATUS_INDEXING)
        chunks = document_retriever.chunk_pages(pages)
        await _persist_pages(file_id, user_id, pages)
        await _persist_chunks(file_id, user_id, chunks)

        await _set_status(
            file_id, STATUS_READY,
            page_count=len(pages),
            processed_at="now()",
            error_message=vision_error,
        )
        log.info("Processed document %s: %d pages, %d chunks, %d vision calls",
                 file_id, len(pages), len(chunks), vision_used)

    except (dp.UnsupportedFileError, dp.DocumentParseError) as exc:
        await _set_status(file_id, STATUS_FAILED, error_message=str(exc))
    except db.DatabaseError:
        await _set_status(file_id, STATUS_FAILED,
                          error_message="The document was processed but could not be saved.")
    except Exception as exc:
        log.exception("Document processing failed for %s (%s)", file_id, type(exc).__name__)
        await _set_status(file_id, STATUS_FAILED,
                          error_message="Processing failed unexpectedly. Try re-uploading the file.")


async def _persist_pages(file_id, user_id, pages):
    rows = [{
        "uploaded_file_id": file_id,
        "user_id": user_id,
        "page_number": p["page_number"],
        "extracted_text": (p.get("extracted_text") or "")[:60000],
        "visual_analysis": p.get("visual_analysis"),
        "content_quality": p.get("content_quality"),
        "important_visuals": bool(p.get("important_visuals")),
        "analysis_source": p.get("analysis_source") or [],
    } for p in pages]
    for i in range(0, len(rows), 50):
        await db.insert("document_pages", rows[i:i + 50])


async def _persist_chunks(file_id, user_id, chunks):
    rows = [{
        "uploaded_file_id": file_id,
        "user_id": user_id,
        "chunk_index": c["chunk_index"],
        "page_number": c.get("page_number"),
        "content": c["content"][:20000],
        "content_type": c.get("content_type"),
        "source": c.get("source"),
        "metadata": c.get("metadata") or {},
    } for c in chunks]
    for i in range(0, len(rows), 50):
        await db.insert("document_chunks", rows[i:i + 50])


async def load_pages(file_id, user_id):
    """Rebuilds the unified text+vision page view from the database."""
    rows = await db.select("document_pages", {
        "select": "*",
        "uploaded_file_id": "eq.%s" % file_id,
        "user_id": "eq.%s" % user_id,
        "order": "page_number.asc",
    })
    return rows


async def load_chunks(file_id, user_id):
    return await db.select("document_chunks", {
        "select": "*",
        "uploaded_file_id": "eq.%s" % file_id,
        "user_id": "eq.%s" % user_id,
        "order": "chunk_index.asc",
    })


async def get_document(file_id, user_id):
    """Always scoped to the owner — a user can never read another user's file."""
    return await db.select_one("uploaded_files", {
        "select": "*",
        "id": "eq.%s" % file_id,
        "user_id": "eq.%s" % user_id,
    })


def status_payload(document):
    status = document.get("status") or STATUS_UPLOADING
    if status == STATUS_FAILED:
        index = -1
    else:
        index = STAGE_ORDER.index(status) if status in STAGE_ORDER else 0
    return {
        "file_id": document.get("id"),
        "status": status,
        "label": STAGE_LABELS.get(status, status),
        "stages": [
            {"key": s, "label": STAGE_LABELS[s],
             "state": ("done" if index > i else "active" if index == i else "pending")}
            for i, s in enumerate(STAGE_ORDER)
        ],
        "page_count": document.get("page_count"),
        "error_message": document.get("error_message"),
        "processed_at": document.get("processed_at"),
    }


async def retrieve_context(file_id, user_id, query, page_context=None):
    chunks = await load_chunks(file_id, user_id)
    if page_context:
        query = "%s (page %d)" % (query, page_context)
    provider = None
    if config.USE_EMBEDDINGS:
        try:
            provider = get_provider()
        except AINotConfiguredError:
            provider = None
    return await document_retriever.retrieve(query, chunks, provider=provider)

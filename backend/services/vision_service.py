"""
Vision analysis — actually sends rendered pages to a vision-capable model.

Cost control is built in, not bolted on:
  1. Text extraction runs first.
  2. Only pages the quality classifier flags get here at all.
  3. Results are cached by content hash, so re-processing or re-summarizing a
     document never re-bills the same page.
  4. MAX_VISION_PAGES caps the worst case for a huge deck.
"""
import hashlib
import logging

import config
from services.ai_provider import AIError, get_provider
from services import document_parser as dp

log = logging.getLogger("learnqwik.vision")

VISION_SYSTEM = """You are analyzing one page or slide from a student's study material.

Describe what the page MEANS, not that it exists. Bad: "Page 8 contains an ER diagram."
Good: "Page 8 shows an ER diagram connecting Student, Course and Enrollment. Student has a
one-to-many relationship with Enrollment, and Course has a one-to-many relationship with
Enrollment, making Enrollment the junction table that resolves the many-to-many between them."

Cover whatever is actually present:
  - text inside images, including handwriting and screenshots
  - diagrams and flowcharts: what the nodes are and how they relate, including direction
  - tables: the columns, and what the data shows
  - charts: axes, units, trend, and the takeaway
  - formulas: transcribe them and say what each symbol means
  - code screenshots: transcribe the code and explain what it does
  - educational figures: the concept being illustrated

Write plain prose a student can revise from. No preamble, no "This image shows". If the
page is genuinely blank or decorative, say so in one line."""


def cache_key(image_bytes):
    return hashlib.sha256(image_bytes).hexdigest()


async def analyze_image(image_bytes, media_type, page_number, extracted_text=None,
                        cache=None):
    """
    Returns (analysis_text, was_cached). `cache` is any dict-like mapping —
    the document service passes a per-document dict, and analyses are also
    persisted alongside the chunks so a second summary run is free.
    """
    key = cache_key(image_bytes)
    if cache is not None and key in cache:
        return cache[key], True

    provider = get_provider()
    prompt = "This is page/slide %d of the student's document." % page_number
    if extracted_text and extracted_text.strip():
        prompt += (
            "\n\nText already extracted from this page (do not simply repeat it — explain "
            "the visual content the extraction missed, and how it relates to this text):\n"
            + extracted_text.strip()[:1500]
        )
    else:
        prompt += ("\n\nNo selectable text could be extracted from this page, so transcribe "
                   "and explain everything you can see.")

    analysis = await provider.analyze_image(image_bytes, prompt, media_type=media_type,
                                            system=VISION_SYSTEM)
    if cache is not None:
        cache[key] = analysis
    return analysis, False


async def analyze_page(raw_file_bytes, ext, page, cache=None):
    """
    Renders the right image(s) for this page and analyzes them.
    Returns None when there is nothing visual to send.
    """
    images = []
    try:
        if ext == "pdf":
            images = [(dp.render_pdf_page(raw_file_bytes, page["page_number"] - 1), "image/png")]
        elif ext == "pptx":
            images = dp.extract_pptx_images(raw_file_bytes, page["page_number"] - 1)
        elif ext == "docx":
            images = dp.extract_docx_images(raw_file_bytes, limit=2)
    except Exception as exc:
        log.warning("Could not render page %s for vision: %s", page["page_number"], type(exc).__name__)
        return None

    if not images:
        return None

    analyses = []
    for image_bytes, media_type in images[:2]:
        if not image_bytes:
            continue
        try:
            text, _cached = await analyze_image(
                image_bytes, media_type, page["page_number"],
                extracted_text=page.get("extracted_text"), cache=cache,
            )
            if text:
                analyses.append(text)
        except AIError:
            raise
        except Exception as exc:
            log.warning("Vision analysis failed on page %s: %s",
                        page["page_number"], type(exc).__name__)
    return "\n\n".join(analyses) if analyses else None


def select_pages_for_vision(pages, limit=None):
    """
    Which pages are worth the call. Scanned pages first (we have nothing else
    for them), then sparse, then mixed — capped by MAX_VISION_PAGES.
    """
    limit = limit or config.MAX_VISION_PAGES
    priority = {dp.QUALITY_SCANNED: 0, dp.QUALITY_SPARSE: 1, dp.QUALITY_MIXED: 2}
    candidates = [p for p in pages if dp.needs_vision(p["content_quality"])]
    candidates.sort(key=lambda p: (priority.get(p["content_quality"], 9), p["page_number"]))
    return candidates[:limit]

"""
Document summary — grounded in the unified text + vision representation.

The model only sees material that came out of the user's own file, and is told
to cite pages. Nothing is generated from the filename or general knowledge.
"""
import json

from services.ai_provider import get_provider

MAX_CONTEXT_CHARS = 22000

SUMMARY_SYSTEM = """You are producing revision notes from a student's own uploaded material.

You will receive page-by-page content. Some pages carry extracted text, some carry Vision
analysis of the page image (diagrams, tables, charts, code screenshots), and some carry both.

Every statement you make must come from that material. Never add outside facts. If a section
below has nothing to draw on, omit it entirely rather than padding it.

Cite page or slide numbers inline like "(page 4)" wherever it helps the student find the source.

Respond with a single JSON object:

{
  "overview": "3-5 sentences on what this material covers and how it is organized.",
  "key_concepts": [{"concept": "...", "explanation": "...", "page": 3}],
  "definitions": [{"term": "...", "definition": "...", "page": 2}],
  "formulas": [{"formula": "...", "meaning": "...", "page": 7}],
  "examples": [{"description": "...", "page": 5}],
  "diagrams": [{"title": "...", "explanation": "what it shows and how the parts relate", "page": 8}],
  "tables_and_charts": [{"title": "...", "explanation": "...", "page": 9}],
  "code": [{"language": "...", "what_it_does": "...", "page": 6}],
  "common_mistakes": ["..."],
  "exam_focus": ["The points most likely to be assessed, each specific."],
  "revision_notes": ["Short, memorizable one-liners."]
}

Use empty arrays for sections the material does not support."""


def build_context(pages, max_chars=MAX_CONTEXT_CHARS):
    """Interleaves text and vision output page by page, trimmed to a budget."""
    parts = []
    used = 0
    for page in pages:
        segments = []
        text = (page.get("extracted_text") or "").strip()
        visual = (page.get("visual_analysis") or "").strip()
        if text:
            segments.append("TEXT:\n" + text)
        if visual:
            segments.append("VISION ANALYSIS:\n" + visual)
        if not segments:
            continue
        block = "--- PAGE %s (%s) ---\n%s" % (
            page.get("page_number"), page.get("content_quality"), "\n\n".join(segments))
        if used + len(block) > max_chars:
            remaining = max_chars - used
            if remaining < 400:
                break
            block = block[:remaining]
        parts.append(block)
        used += len(block)
        if used >= max_chars:
            break
    return "\n\n".join(parts)


async def summarize(document, pages):
    provider = get_provider()
    context = build_context(pages)
    if not context.strip():
        raise ValueError("No readable content was extracted from this document.")

    prompt = (
        "Document: %s (%s pages)\n\n%s"
        % (document.get("original_filename"), document.get("page_count"), context)
    )
    data = await provider.generate_structured_output(prompt, system=SUMMARY_SYSTEM, max_tokens=4000)
    return normalize(data)


def normalize(data):
    """Defensive shaping so the frontend can render without null checks everywhere."""
    if not isinstance(data, dict):
        raise ValueError("Summary response was not an object")
    list_fields = ["key_concepts", "definitions", "formulas", "examples", "diagrams",
                   "tables_and_charts", "code", "common_mistakes", "exam_focus",
                   "revision_notes"]
    out = {"overview": str(data.get("overview") or "").strip()}
    for field in list_fields:
        value = data.get(field)
        out[field] = value if isinstance(value, list) else []
    return out


def to_markdown(summary, filename):
    """Plain-text export for the 'copy notes' button."""
    lines = ["# Summary — %s" % filename, "", summary.get("overview", ""), ""]

    def section(title, items, render):
        if not items:
            return
        lines.append("## %s" % title)
        for item in items:
            lines.append(render(item))
        lines.append("")

    def page_suffix(item):
        page = item.get("page") if isinstance(item, dict) else None
        return " (page %s)" % page if page else ""

    section("Key concepts", summary.get("key_concepts"),
            lambda i: "- **%s** — %s%s" % (i.get("concept", ""), i.get("explanation", ""), page_suffix(i)))
    section("Definitions", summary.get("definitions"),
            lambda i: "- **%s**: %s%s" % (i.get("term", ""), i.get("definition", ""), page_suffix(i)))
    section("Formulas", summary.get("formulas"),
            lambda i: "- `%s` — %s%s" % (i.get("formula", ""), i.get("meaning", ""), page_suffix(i)))
    section("Diagrams", summary.get("diagrams"),
            lambda i: "- **%s** — %s%s" % (i.get("title", ""), i.get("explanation", ""), page_suffix(i)))
    section("Tables and charts", summary.get("tables_and_charts"),
            lambda i: "- **%s** — %s%s" % (i.get("title", ""), i.get("explanation", ""), page_suffix(i)))
    section("Code", summary.get("code"),
            lambda i: "- `%s` — %s%s" % (i.get("language", ""), i.get("what_it_does", ""), page_suffix(i)))
    section("Common mistakes", summary.get("common_mistakes"), lambda i: "- %s" % i)
    section("Exam focus", summary.get("exam_focus"), lambda i: "- %s" % i)
    section("Revision notes", summary.get("revision_notes"), lambda i: "- %s" % i)
    return "\n".join(lines).strip()

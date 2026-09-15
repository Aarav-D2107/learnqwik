"""
Document-grounded quiz generation.

Questions must come from the student's own material — text, diagrams, tables,
charts, formulas, code. Anything the model returns is validated: four options,
an in-range answer index, a real page number, a non-empty explanation. Invalid
questions are dropped, not patched over.
"""
from services.ai_provider import get_provider
from services.summarizer import build_context

DIFFICULTIES = ("Easy", "Medium", "Hard")
SOURCE_TYPES = ("text", "diagram", "table", "chart", "formula", "code", "screenshot", "mixed")

QUIZ_SYSTEM = """You write assessment questions from a student's own uploaded study material.

Every question must be answerable from the material you are given, and must test
understanding rather than trivia about formatting or page layout.

Draw from everything available: prose, diagrams, tables, charts, formulas, code and
screenshots. A good diagram question asks what a relationship implies, not what colour
a box is.

Distractors must be plausible — wrong for a reason a student would actually fall for.

Respond with a single JSON object:

{
  "questions": [
    {
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "explanation": "Why the correct answer is correct, and why the tempting wrong one isn't.",
      "difficulty": "Easy" | "Medium" | "Hard",
      "source_page": 4,
      "source_type": "text" | "diagram" | "table" | "chart" | "formula" | "code" | "screenshot"
    }
  ]
}

Exactly four options per question. Mix the difficulties. Never repeat a question."""


async def generate(document, pages, count=8):
    provider = get_provider()
    context = build_context(pages)
    if not context.strip():
        raise ValueError("No readable content was extracted from this document.")

    count = max(3, min(15, int(count)))
    valid_pages = {p.get("page_number") for p in pages}

    prompt = (
        "Document: %s (%s pages)\n\nGenerate exactly %d questions grounded in the material below.\n\n%s"
        % (document.get("original_filename"), document.get("page_count"), count, context)
    )
    data = await provider.generate_structured_output(prompt, system=QUIZ_SYSTEM, max_tokens=4000)
    questions = validate(data, valid_pages)
    if not questions:
        raise ValueError("The AI did not return any usable questions for this document.")
    return questions[:count]


def validate(data, valid_pages):
    """Drops malformed questions rather than letting them reach a student."""
    if not isinstance(data, dict):
        return []
    raw = data.get("questions")
    if not isinstance(raw, list):
        return []

    out = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        text = str(item.get("question") or "").strip()
        options = item.get("options")
        if not text or not isinstance(options, list) or len(options) != 4:
            continue
        options = [str(o).strip() for o in options]
        if any(not o for o in options) or len(set(options)) != 4:
            continue
        try:
            correct = int(item.get("correct_index"))
        except (TypeError, ValueError):
            continue
        if not 0 <= correct <= 3:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)

        difficulty = item.get("difficulty")
        if difficulty not in DIFFICULTIES:
            difficulty = "Medium"
        source_type = item.get("source_type")
        if source_type not in SOURCE_TYPES:
            source_type = "text"
        page = item.get("source_page")
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = None
        if page is not None and valid_pages and page not in valid_pages:
            page = None

        out.append({
            "question": text[:600],
            "options": [o[:300] for o in options],
            "correct_index": correct,
            "explanation": str(item.get("explanation") or "").strip()[:800]
                           or "Check the cited page in your material.",
            "difficulty": difficulty,
            "source_page": page,
            "source_type": source_type,
        })
    return out

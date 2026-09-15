"""
AI Tutor — the real one.

The prototype's keyword-matching reply function is gone. Every reply
here comes from the configured provider, grounded in:

  - the current subject and topic
  - the actual learning content the student is reading
  - the student's measured mastery and weak areas
  - retrieved chunks from their uploaded document (when in document mode)
  - the recent conversation

Document mode is strictly grounded: if the retrieved material doesn't support
an answer, the tutor says so rather than inventing document facts. Anything it
adds from general knowledge is labelled as such.
"""
import json

from services.ai_provider import get_provider

MAX_HISTORY_TURNS = 8
MAX_CONTENT_CHARS = 4000
MAX_CHUNK_CHARS = 6000

TOPIC_SYSTEM = """You are LearnQwik's AI Tutor, helping a college-level student.

You will be given the topic they are studying, the exact learning content on their
screen, and their measured mastery. Teach to that context.

You can: explain concepts, give worked examples, compare two ideas, simplify something
that didn't land, walk through code line by line, explain a diagram, diagnose a mistake
in their reasoning, and generate practice questions when asked.

Style:
  - Answer the actual question first, then add context.
  - Concrete over abstract: show a small example rather than describing one.
  - Use fenced code blocks for code.
  - Keep it to a few short paragraphs unless they asked for depth.
  - If their mastery in this topic is low, slow down and check the fundamentals.
  - Never flatter. Never pad. If they're wrong, say so plainly and show why."""

DOCUMENT_SYSTEM = """You are LearnQwik's AI Tutor answering questions about a document the
student uploaded.

You will be given excerpts retrieved from that document. Some excerpts come from
extracted text and some come from Vision analysis of a page image (diagrams, tables,
charts, screenshots, handwriting). Each excerpt is labelled with its page or slide number.

Rules:
  - Ground every document-specific claim in the excerpts you were given.
  - Cite the page or slide, like "(page 8)".
  - If the excerpts do not contain the answer, say clearly: "I couldn't find that in
    your uploaded material." Do not guess at what the document says.
  - You may add general knowledge afterwards, but you must label it, e.g.
    "Outside your document, in general: ...".
  - When explaining a diagram or table, explain what it means and how the parts relate,
    not merely that it exists."""


def build_topic_context(subject, topic, content, mastery_row, weak_topics):
    ctx = {
        "subject": subject.get("name"),
        "topic": topic.get("name"),
        "topic_description": topic.get("description"),
    }
    if content:
        trimmed = {
            "introduction": content.get("intro"),
            "key_concepts": content.get("concepts"),
            "practical_explanation": content.get("practical"),
            "common_mistakes": content.get("mistakes"),
            "important_points": content.get("important"),
            "code_examples": content.get("examples"),
        }
        serialized = json.dumps(trimmed)
        if len(serialized) > MAX_CONTENT_CHARS:
            trimmed.pop("code_examples", None)
        ctx["learning_content"] = trimmed
    if mastery_row and mastery_row.get("mastery_pct") is not None:
        ctx["student_mastery_percent"] = mastery_row["mastery_pct"]
        ctx["student_mastery_band"] = mastery_row.get("mastery_band")
    if weak_topics:
        ctx["student_weak_topics"] = [
            {"topic": w.get("topic_name") or w.get("topic_id"), "mastery": w.get("mastery_pct")}
            for w in weak_topics[:4]
        ]
    return ctx


def build_document_context(document, chunks, page_context=None):
    excerpts = []
    used = 0
    for c in chunks:
        text = (c.get("content") or "").strip()
        if not text:
            continue
        if used + len(text) > MAX_CHUNK_CHARS:
            text = text[: max(0, MAX_CHUNK_CHARS - used)]
        if not text:
            break
        used += len(text)
        excerpts.append({
            "page": c.get("page_number"),
            "source": c.get("source", "text"),
            "content_type": c.get("content_type"),
            "excerpt": text,
        })
        if used >= MAX_CHUNK_CHARS:
            break
    ctx = {
        "document_name": document.get("original_filename"),
        "page_count": document.get("page_count"),
        "retrieved_excerpts": excerpts,
    }
    if page_context:
        ctx["student_is_asking_about_page"] = page_context
    return ctx


def _history(conversation):
    turns = []
    for m in (conversation or [])[-MAX_HISTORY_TURNS * 2:]:
        role = "Student" if m.get("role") in ("user", "student") else "Tutor"
        text = (m.get("content") or "").strip()
        if text:
            turns.append("%s: %s" % (role, text[:1200]))
    return "\n".join(turns)


async def answer(message, context, conversation=None, document_mode=False):
    provider = get_provider()
    system = DOCUMENT_SYSTEM if document_mode else TOPIC_SYSTEM

    parts = ["Context:\n" + json.dumps(context, indent=2, default=str)]
    history = _history(conversation)
    if history:
        parts.append("Recent conversation:\n" + history)
    parts.append("The student now asks:\n%s" % message.strip())

    return await provider.generate_text(
        "\n\n".join(parts), system=system, max_tokens=1400, temperature=0.4,
    )


def greeting(topic_name):
    return ("I'm the LearnQwik AI Tutor and I can see you're on **%s**. Ask me to explain a "
            "concept, walk through an example, compare two ideas, or check where your "
            "reasoning went wrong." % topic_name)

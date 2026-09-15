"""
Chunking and retrieval.

The tutor never gets the whole document. It gets the handful of chunks that
actually bear on the question, which is both the only way to stay accurate and
the main lever on AI cost.

Two retrieval paths:

  vector    pgvector + embeddings, when USE_EMBEDDINGS=true and an
            EMBEDDING_MODEL is configured.
  keyword   a BM25-style lexical scorer that runs entirely in Python.

The keyword path is the default and is deliberately good enough to ship on.
Vector search being unavailable must never make the product unusable.
"""
import math
import re
from collections import Counter

import config

STOPWORDS = {
    "a", "about", "an", "and", "are", "as", "at", "be", "but", "by", "can", "do", "does",
    "for", "from", "has", "have", "how", "i", "in", "is", "it", "its", "me", "of", "on",
    "or", "please", "so", "such", "than", "that", "the", "their", "them", "then", "there",
    "these", "they", "this", "to", "was", "were", "what", "when", "where", "which", "who",
    "why", "will", "with", "you", "your", "explain", "tell", "show",
}

TOKEN_RE = re.compile(r"[a-z0-9_]+")


def tokenize(text):
    return [t for t in TOKEN_RE.findall((text or "").lower())
            if len(t) > 1 and t not in STOPWORDS]


# ------------------------------------------------------------------ Chunking
def chunk_pages(pages, target_chars=None, overlap=None):
    """
    Produces chunk dicts ready for the document_chunks table. Page/slide
    provenance is preserved so the tutor can say "(page 8)" and mean it.

    Vision output becomes its own chunk with source='vision', so retrieval can
    surface a diagram explanation even when the page's text says nothing.
    """
    target = target_chars or config.CHUNK_TARGET_CHARS
    lap = overlap if overlap is not None else config.CHUNK_OVERLAP_CHARS
    chunks = []
    index = 0

    for page in pages:
        page_no = page.get("page_number")

        text = (page.get("extracted_text") or "").strip()
        if text:
            content_type = "code" if page.get("is_source_code") else "text"
            for piece in _split(text, target, lap):
                chunks.append({
                    "chunk_index": index,
                    "page_number": page_no,
                    "content": piece,
                    "content_type": content_type,
                    "source": "text",
                    "metadata": {
                        "content_quality": page.get("content_quality"),
                        "language": page.get("language"),
                    },
                })
                index += 1

        visual = (page.get("visual_analysis") or "").strip()
        if visual:
            for piece in _split(visual, target, lap):
                chunks.append({
                    "chunk_index": index,
                    "page_number": page_no,
                    "content": piece,
                    "content_type": "visual",
                    "source": "vision",
                    "metadata": {
                        "content_quality": page.get("content_quality"),
                        "analysis_source": page.get("analysis_source"),
                    },
                })
                index += 1

    return chunks


def _split(text, target, overlap):
    if len(text) <= target:
        return [text]
    pieces = []
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) + 2 <= target:
            buffer = (buffer + "\n\n" + para).strip()
            continue
        if buffer:
            pieces.append(buffer)
            buffer = buffer[-overlap:] + "\n\n" + para if overlap else para
        else:
            for i in range(0, len(para), target):
                pieces.append(para[i:i + target])
            buffer = ""
    if buffer.strip():
        pieces.append(buffer.strip())
    return [p for p in pieces if p.strip()] or [text[:target]]


# ------------------------------------------------------------------ Keyword search
def keyword_search(query, chunks, top_k=None, page_hint=None):
    """
    BM25-flavoured lexical retrieval. Deterministic, dependency-free, and
    fast enough for the per-document corpus sizes we deal with.
    """
    top_k = top_k or config.RETRIEVAL_TOP_K
    query_terms = tokenize(query)
    if not chunks:
        return []
    if not query_terms:
        return sorted(chunks, key=lambda c: c.get("chunk_index", 0))[:top_k]

    tokenized = [(c, tokenize(c.get("content", ""))) for c in chunks]
    n = len(tokenized)
    avg_len = sum(len(t) for _, t in tokenized) / max(n, 1) or 1.0

    df = Counter()
    for _, terms in tokenized:
        for term in set(terms):
            df[term] += 1

    k1, b = 1.5, 0.75
    scored = []
    for chunk, terms in tokenized:
        if not terms:
            continue
        counts = Counter(terms)
        length = len(terms)
        score = 0.0
        matched = 0
        for term in query_terms:
            tf = counts.get(term, 0)
            if not tf:
                continue
            matched += 1
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * length / avg_len))

        if page_hint and chunk.get("page_number") == page_hint:
            score += 6.0  # "explain the diagram on page 8"
        if chunk.get("source") == "vision" and _is_visual_question(query):
            score += 1.5

        if score > 0:
            scored.append((score, matched, chunk))

    scored.sort(key=lambda x: (-x[0], x[2].get("chunk_index", 0)))
    results = [c for _s, _m, c in scored[:top_k]]

    # A page-specific question must always surface that page, even if its
    # wording doesn't overlap the query at all.
    if page_hint and not any(c.get("page_number") == page_hint for c in results):
        page_chunks = [c for c in chunks if c.get("page_number") == page_hint]
        results = page_chunks[:2] + results[: max(0, top_k - 2)]

    return results[:top_k]


VISUAL_WORDS = {"diagram", "figure", "chart", "graph", "table", "image", "picture",
                "screenshot", "flowchart", "slide", "drawing", "illustration"}


def _is_visual_question(query):
    return bool(VISUAL_WORDS & set(tokenize(query)))


def extract_page_hint(query):
    """Pull an explicit page/slide reference out of the student's question."""
    match = re.search(r"\b(?:page|slide|pg\.?|p\.)\s*(\d{1,4})\b", (query or "").lower())
    return int(match.group(1)) if match else None


# ------------------------------------------------------------------ Vector search
def cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def vector_search(query_embedding, chunks, top_k=None):
    top_k = top_k or config.RETRIEVAL_TOP_K
    scored = []
    for c in chunks:
        emb = c.get("embedding")
        if not emb:
            continue
        scored.append((cosine(query_embedding, emb), c))
    scored.sort(key=lambda x: -x[0])
    return [c for _s, c in scored[:top_k]]


async def retrieve(query, chunks, top_k=None, provider=None):
    """
    Hybrid entry point. Tries vectors when configured and available, and
    always falls back to keyword search rather than failing.
    """
    top_k = top_k or config.RETRIEVAL_TOP_K
    page_hint = extract_page_hint(query)

    if config.USE_EMBEDDINGS and provider is not None and any(c.get("embedding") for c in chunks):
        try:
            embedding = await provider.create_embedding(query)
            hits = vector_search(embedding, chunks, top_k)
            if hits:
                if page_hint and not any(c.get("page_number") == page_hint for c in hits):
                    hits = [c for c in chunks if c.get("page_number") == page_hint][:2] + hits
                return hits[:top_k]
        except Exception:
            pass  # fall through to keyword

    return keyword_search(query, chunks, top_k, page_hint=page_hint)

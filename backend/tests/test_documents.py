"""Document parsing, quality classification, chunking and retrieval."""
import io

import pytest

from services import document_parser as dp
from services import document_retriever as dr
from services import question_generator, vision_service


# ---------------------------------------------------------------- Validation
def test_supported_extensions_accepted():
    for name in ["notes.pdf", "deck.pptx", "essay.docx", "main.py", "query.sql"]:
        assert dp.detect_extension(name)


def test_unsupported_extension_rejected():
    with pytest.raises(dp.UnsupportedFileError):
        dp.detect_extension("virus.exe")


def test_legacy_formats_give_a_useful_message():
    with pytest.raises(dp.UnsupportedFileError, match="pptx"):
        dp.parse(b"anything", "old.ppt")
    with pytest.raises(dp.UnsupportedFileError, match="docx"):
        dp.parse(b"anything", "old.doc")


def test_magic_number_check_catches_renamed_files():
    assert dp.sniff_mime(b"%PDF-1.7 rest of file", "pdf") is True
    assert dp.sniff_mime(b"MZ\x90\x00 this is an exe", "pdf") is False


# ---------------------------------------------------------------- Quality routing
def test_text_rich_page_skips_vision():
    quality = dp.classify_page("x" * 800, has_visuals=False)
    assert quality == dp.QUALITY_TEXT_RICH
    assert dp.needs_vision(quality) is False


def test_scanned_page_needs_vision():
    quality = dp.classify_page("", has_visuals=True, visual_area_ratio=0.9)
    assert quality == dp.QUALITY_SCANNED
    assert dp.needs_vision(quality) is True


def test_sparse_page_needs_vision():
    quality = dp.classify_page("Figure 3.", has_visuals=False)
    assert quality == dp.QUALITY_SPARSE
    assert dp.needs_vision(quality) is True


def test_mixed_page_uses_both_models():
    quality = dp.classify_page("x" * 900, has_visuals=True, visual_area_ratio=0.4)
    assert quality == dp.QUALITY_MIXED
    assert dp.needs_vision(quality) is True


def test_empty_page_is_skipped():
    assert dp.classify_page("", has_visuals=False) == dp.QUALITY_EMPTY


def test_vision_page_budget_is_capped():
    pages = [{"page_number": i, "content_quality": dp.QUALITY_SCANNED} for i in range(1, 60)]
    selected = vision_service.select_pages_for_vision(pages, limit=5)
    assert len(selected) == 5


def test_scanned_pages_prioritized_over_mixed():
    pages = [
        {"page_number": 1, "content_quality": dp.QUALITY_MIXED},
        {"page_number": 2, "content_quality": dp.QUALITY_SCANNED},
    ]
    selected = vision_service.select_pages_for_vision(pages, limit=1)
    assert selected[0]["page_number"] == 2


# ---------------------------------------------------------------- Text + source parsing
def test_plain_text_parsing():
    ext, pages = dp.parse(b"Normalization removes redundancy in relational schemas.", "notes.txt")
    assert ext == "txt"
    assert "Normalization" in pages[0]["extracted_text"]
    assert pages[0]["has_visuals"] is False


def test_source_code_preserves_formatting_and_never_uses_vision():
    code = b"def add(a, b):\n    # indented comment\n    return a + b\n"
    ext, pages = dp.parse(code, "math.py")
    assert ext == "py"
    assert "    return a + b" in pages[0]["extracted_text"]
    assert pages[0]["is_source_code"] is True
    assert dp.needs_vision(pages[0]["content_quality"]) is False


def test_docx_parsing_real_file():
    docx = pytest.importorskip("docx")
    document = docx.Document()
    document.add_heading("Normalization", level=1)
    document.add_paragraph("Third normal form removes transitive dependencies.")
    buffer = io.BytesIO()
    document.save(buffer)

    ext, pages = dp.parse(buffer.getvalue(), "notes.docx")
    assert ext == "docx"
    assert "Third normal form" in pages[0]["extracted_text"]


def test_pptx_parsing_real_file():
    pptx = pytest.importorskip("pptx")
    presentation = pptx.Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    slide.shapes.title.text = "ER Diagrams"
    buffer = io.BytesIO()
    presentation.save(buffer)

    ext, pages = dp.parse(buffer.getvalue(), "lecture.pptx")
    assert ext == "pptx"
    assert "ER Diagrams" in pages[0]["extracted_text"]


# ---------------------------------------------------------------- Chunking
def test_text_and_vision_become_separate_chunks():
    pages = [{
        "page_number": 8,
        "extracted_text": "Figure 3.1",
        "visual_analysis": "An ER diagram connecting Student, Course and Enrollment.",
        "content_quality": dp.QUALITY_MIXED,
    }]
    chunks = dr.chunk_pages(pages)
    sources = {c["source"] for c in chunks}
    assert sources == {"text", "vision"}
    assert all(c["page_number"] == 8 for c in chunks)


def test_chunk_indices_are_sequential():
    pages = [{"page_number": i, "extracted_text": "content " * 40} for i in range(1, 6)]
    chunks = dr.chunk_pages(pages)
    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))


def test_long_pages_are_split():
    pages = [{"page_number": 1, "extracted_text": "\n\n".join(["paragraph " * 60] * 8)}]
    chunks = dr.chunk_pages(pages, target_chars=500)
    assert len(chunks) > 1


# ---------------------------------------------------------------- Retrieval
@pytest.fixture
def indexed_chunks():
    pages = [
        {"page_number": 1,
         "extracted_text": "Normalization removes redundancy. Third normal form requires "
                           "that no non-key attribute is transitively dependent on the key."},
        {"page_number": 4,
         "extracted_text": "A transaction satisfies ACID: atomicity, consistency, isolation, durability."},
        {"page_number": 8, "extracted_text": "",
         "visual_analysis": "An ER diagram connecting Student, Course and Enrollment entities. "
                            "Student has a one-to-many relationship with Enrollment."},
    ]
    return dr.chunk_pages(pages)


def test_keyword_retrieval_finds_the_right_page(indexed_chunks):
    hits = dr.keyword_search("what is third normal form", indexed_chunks, top_k=1)
    assert hits[0]["page_number"] == 1


def test_page_reference_is_extracted():
    assert dr.extract_page_hint("explain the diagram on page 8") == 8
    assert dr.extract_page_hint("what's on slide 12?") == 12
    assert dr.extract_page_hint("explain normalization") is None


def test_page_specific_question_returns_that_page(indexed_chunks):
    hits = dr.keyword_search("explain the diagram on page 8", indexed_chunks, top_k=2, page_hint=8)
    assert hits[0]["page_number"] == 8
    assert hits[0]["source"] == "vision"


def test_page_hint_wins_even_with_no_word_overlap(indexed_chunks):
    hits = dr.keyword_search("zzzz qqqq", indexed_chunks, top_k=2, page_hint=4)
    assert any(c["page_number"] == 4 for c in hits)


def test_retrieval_is_bounded(indexed_chunks):
    hits = dr.keyword_search("normalization transaction diagram", indexed_chunks, top_k=2)
    assert len(hits) <= 2


def test_empty_corpus_returns_nothing():
    assert dr.keyword_search("anything", [], top_k=5) == []


def test_cosine_similarity():
    assert dr.cosine([1, 0], [1, 0]) == pytest.approx(1.0)
    assert dr.cosine([1, 0], [0, 1]) == pytest.approx(0.0)
    assert dr.cosine([], [1]) == 0.0


# ---------------------------------------------------------------- Question validation
def test_valid_generated_questions_accepted():
    data = {"questions": [{
        "question": "What does the ER diagram on page 8 imply about Enrollment?",
        "options": ["It is a junction table", "It is a view", "It is an index", "It is a trigger"],
        "correct_index": 0,
        "explanation": "Enrollment resolves the many-to-many between Student and Course.",
        "difficulty": "Medium", "source_page": 8, "source_type": "diagram",
    }]}
    result = question_generator.validate(data, valid_pages={1, 4, 8})
    assert len(result) == 1
    assert result[0]["source_type"] == "diagram"


def test_wrong_option_count_dropped():
    data = {"questions": [{"question": "Q", "options": ["a", "b"], "correct_index": 0}]}
    assert question_generator.validate(data, valid_pages={1}) == []


def test_out_of_range_answer_dropped():
    data = {"questions": [{"question": "Q", "options": ["a", "b", "c", "d"], "correct_index": 7}]}
    assert question_generator.validate(data, valid_pages={1}) == []


def test_duplicate_options_dropped():
    data = {"questions": [{"question": "Q", "options": ["a", "a", "c", "d"], "correct_index": 0}]}
    assert question_generator.validate(data, valid_pages={1}) == []


def test_duplicate_questions_deduplicated():
    item = {"question": "Same?", "options": ["a", "b", "c", "d"], "correct_index": 0}
    result = question_generator.validate({"questions": [item, dict(item)]}, valid_pages={1})
    assert len(result) == 1


def test_hallucinated_page_reference_is_nulled():
    data = {"questions": [{"question": "Q", "options": ["a", "b", "c", "d"],
                           "correct_index": 0, "source_page": 999}]}
    result = question_generator.validate(data, valid_pages={1, 2})
    assert result[0]["source_page"] is None


def test_malformed_response_yields_nothing():
    assert question_generator.validate("not a dict", valid_pages={1}) == []
    assert question_generator.validate({"questions": "nope"}, valid_pages={1}) == []

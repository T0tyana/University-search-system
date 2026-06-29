import pytest

from app.services.document_processor import (
    extract_text_from_pdf,
    extract_text_from_docx,
)


VALID_PDF = "../tests/fixtures/valid/university.pdf"
VALID_DOCX = "../tests/fixtures/valid/university.docx"

EMPTY_PDF = "../tests/fixtures/empty/empty.pdf"
EMPTY_DOCX = "../tests/fixtures/empty/empty.docx"

BROKEN_PDF = "../tests/fixtures/corrupted/broken.pdf"
BROKEN_DOCX = "../tests/fixtures/corrupted/broken.docx"

UNICODE_PDF = "../tests/fixtures/unicode/unicode.pdf"
UNICODE_DOCX = "../tests/fixtures/unicode/unicode.docx"


def test_valid_pdf_fixture():
    result = extract_text_from_pdf(VALID_PDF)

    assert len(result) > 0
    assert isinstance(result, list)


def test_valid_docx_fixture():
    result = extract_text_from_docx(VALID_DOCX)

    assert len(result) > 0
    assert isinstance(result, list)


def test_empty_pdf_fixture():
    result = extract_text_from_pdf(EMPTY_PDF)

    assert result == []


def test_empty_docx_fixture():
    result = extract_text_from_docx(EMPTY_DOCX)

    assert result == []


def test_broken_pdf_fixture():
    with pytest.raises(ValueError):
        extract_text_from_pdf(BROKEN_PDF)


def test_broken_docx_fixture():
    with pytest.raises(ValueError):
        extract_text_from_docx(BROKEN_DOCX)


def test_unicode_pdf_fixture():
    result = extract_text_from_pdf(UNICODE_PDF)

    assert len(result) > 0

    text = result[0][0]

    assert "Привет" in text
    assert "Hello" in text


def test_unicode_docx_fixture():
    result = extract_text_from_docx(UNICODE_DOCX)

    assert len(result) > 0

    text = result[0][0]

    assert "Привет" in text
    assert "Hello" in text
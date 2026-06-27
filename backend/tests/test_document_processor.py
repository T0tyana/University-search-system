import pytest
from app.services.document_processor import split_text_into_chunks
from app.services.document_processor import process_document
from app.services.document_processor import extract_text_from_pdf
from app.services.document_processor import extract_text_from_docx


def test_split_short_text():
    text = "Hello world"

    chunks = split_text_into_chunks(
        text,
        chunk_size=100,
        overlap=10
    )

    assert chunks == ["Hello world"]


def test_split_empty_text():
    assert split_text_into_chunks("") == []


def test_split_whitespace_text():
    assert split_text_into_chunks("      ") == []


def test_split_long_text():
    text = "A" * 250

    chunks = split_text_into_chunks(
        text,
        chunk_size=100,
        overlap=10
    )

    assert len(chunks) >= 3
    assert chunks[0] == "A" * 100


def test_split_with_overlap():
    text = "ABCDEFGHIJ"

    chunks = split_text_into_chunks(
        text,
        chunk_size=5,
        overlap=2
    )

    assert chunks == [
        "ABCDE",
        "DEFGH",
        "GHIJ",
        "J"
    ]


def test_custom_chunk_size():
    text = "123456789"

    chunks = split_text_into_chunks(
        text,
        chunk_size=3,
        overlap=1
    )

    assert chunks[0] == "123"


def test_chunk_size_bigger_than_text():
    text = "Python"

    chunks = split_text_into_chunks(
        text,
        chunk_size=100,
        overlap=10
    )

    assert len(chunks) == 1
    assert chunks[0] == "Python"


def test_invalid_chunk_parameters():
    with pytest.raises(ValueError):
        split_text_into_chunks(
            "A" * 100,
            chunk_size=100,
            overlap=100
        )
        
def test_process_document_file_not_found():

    with pytest.raises(FileNotFoundError):
        process_document(
            "unknown_file",
            "pdf"
        )

def test_process_document_invalid_extension(tmp_path, mocker):

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    file = upload_dir / "test.txt"
    file.write_text("text")

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    with pytest.raises(ValueError):
        process_document(
            "test",
            "txt"
        )

def test_process_document_invalid_extension(tmp_path, mocker):

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    file = upload_dir / "test.txt"
    file.write_text("text")

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    with pytest.raises(ValueError):
        process_document(
            "test",
            "txt"
        )
        
def test_process_document_empty_pdf(mocker):

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    mocker.patch(
        "app.services.document_processor.extract_text_from_pdf",
        return_value=[]
    )

    result = process_document(
        "test",
        "pdf"
    )

    assert result == []
    
def test_process_document_empty_docx(mocker):

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    mocker.patch(
        "app.services.document_processor.extract_text_from_docx",
        return_value=[]
    )

    result = process_document(
        "test",
        "docx"
    )

    assert result == []
    
def test_process_document_success_pdf(mocker):

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    mocker.patch(
        "app.services.document_processor.extract_text_from_pdf",
        return_value=[
            ("Hello world", 1)
        ]
    )

    mocker.patch(
        "app.services.document_processor.split_text_into_chunks",
        return_value=[
            "Hello world"
        ]
    )

    result = process_document(
        "test",
        "pdf"
    )

    assert result == [
        {
            "text": "Hello world",
            "page_number": 1
        }
    ]
    
def test_process_document_skip_invalid_page(mocker):

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    mocker.patch(
        "app.services.document_processor.extract_text_from_pdf",
        return_value=[
            ("Some text", 1)
        ]
    )

    mocker.patch(
        "app.services.document_processor.split_text_into_chunks",
        side_effect=ValueError
    )

    result = process_document(
        "test",
        "pdf"
    )

    assert result == []
    

def test_extract_pdf_file_not_found():

    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf("unknown.pdf")
        
def test_extract_docx_file_not_found():

    with pytest.raises(FileNotFoundError):
        extract_text_from_docx("unknown.docx")
        
def test_extract_pdf_invalid_file(mocker):

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    mocker.patch(
        "app.services.document_processor.pdfplumber.open",
        side_effect=Exception("PDF error")
    )

    with pytest.raises(ValueError):
        extract_text_from_pdf("test.pdf")
        
def test_extract_docx_invalid_file(mocker):

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    mocker.patch(
        "app.services.document_processor.Document",
        side_effect=Exception("DOCX error")
    )

    with pytest.raises(ValueError):
        extract_text_from_docx("test.docx")
        
def test_extract_empty_docx(mocker):

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    fake_doc = mocker.Mock()
    fake_doc.paragraphs = []

    mocker.patch(
        "app.services.document_processor.Document",
        return_value=fake_doc
    )

    assert extract_text_from_docx("test.docx") == []
    
def test_extract_docx_success(mocker):

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    paragraph = mocker.Mock()
    paragraph.text = "Hello"

    fake_doc = mocker.Mock()
    fake_doc.paragraphs = [paragraph]

    mocker.patch(
        "app.services.document_processor.Document",
        return_value=fake_doc
    )

    result = extract_text_from_docx("test.docx")

    assert result == [("Hello", 1)]
    
def test_extract_empty_pdf(mocker):

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    fake_pdf = mocker.Mock()
    fake_pdf.pages = []

    mocker.patch(
        "app.services.document_processor.pdfplumber.open"
    ).return_value.__enter__.return_value = fake_pdf

    assert extract_text_from_pdf("test.pdf") == []
    
def test_extract_pdf_success(mocker):

    mocker.patch(
        "app.services.document_processor.os.path.exists",
        return_value=True
    )

    page = mocker.Mock()
    page.extract_text.return_value = "Hello PDF"

    fake_pdf = mocker.Mock()
    fake_pdf.pages = [page]

    mocker.patch(
        "app.services.document_processor.pdfplumber.open"
    ).return_value.__enter__.return_value = fake_pdf

    result = extract_text_from_pdf("test.pdf")

    assert result == [("Hello PDF", 1)]
    

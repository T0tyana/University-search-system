from app.services.document_processor import split_text_into_chunks
import pytest


def test_split_short_text():
    text = "Hello world"

    chunks = split_text_into_chunks(
        text,
        chunk_size=100,
        overlap=10
    )

    assert chunks == ["Hello world"]


def test_split_empty_text():

    chunks = split_text_into_chunks("")

    assert chunks == []


def test_split_whitespace_text():

    chunks = split_text_into_chunks("      ")

    assert chunks == []

@pytest.mark.timeout(2)
def test_split_long_text():

    text = "A" * 250

    chunks = split_text_into_chunks(
        text,
        chunk_size=100,
        overlap=0
    )

    assert len(chunks) == 3
    assert chunks[0] == "A" * 100
    assert chunks[1] == "A" * 100
    assert chunks[2] == "A" * 50


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

@pytest.mark.timeout(2)
def test_custom_chunk_size():

    text = "123456789"

    chunks = split_text_into_chunks(
        text,
        chunk_size=3,
        overlap=0
    )

    assert chunks == [
        "123",
        "456",
        "789"
    ]


def test_chunk_size_bigger_than_text():

    text = "Python"

    chunks = split_text_into_chunks(
        text,
        chunk_size=100,
        overlap=10
    )

    assert len(chunks) == 1

    assert chunks[0] == "Python"
    


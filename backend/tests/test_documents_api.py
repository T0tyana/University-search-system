from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.documents import router
from app.services.auth_service import get_current_user
from unittest.mock import MagicMock, patch


app = FastAPI()
app.include_router(router)


def fake_user():
    class User:
        username = "tester"
    return User()


app.dependency_overrides[get_current_user] = fake_user

client = TestClient(app)


def test_upload_without_filename():

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "",
                b"test",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 422


def test_upload_invalid_extension():

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "file.txt",
                b"hello",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400


@patch("app.api.v1.documents.check_file_exists")
def test_upload_duplicate(mock_exists):

    mock_exists.return_value = True

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "file.pdf",
                b"hello",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 409


@patch("app.api.v1.documents.check_file_exists")
def test_upload_empty_file(mock_exists):

    mock_exists.return_value = False

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "file.pdf",
                b"",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400


@patch("app.api.v1.documents.check_file_exists")
def test_upload_file_too_large(mock_exists):

    mock_exists.return_value = False

    huge = b"A" * (30 * 1024 * 1024)

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "file.pdf",
                huge,
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400


@patch("app.api.v1.documents.index_chunks")
@patch("app.api.v1.documents.process_document")
@patch("app.api.v1.documents.check_file_exists")
def test_upload_empty_document(
    mock_exists,
    mock_process,
    mock_index
):

    mock_exists.return_value = False
    mock_process.return_value = []

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "file.pdf",
                b"hello",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400
    mock_index.assert_not_called()


@patch("app.api.v1.documents.index_chunks")
@patch("app.api.v1.documents.process_document")
@patch("app.api.v1.documents.check_file_exists")
def test_upload_success(
    mock_exists,
    mock_process,
    mock_index
):

    mock_exists.return_value = False

    mock_process.return_value = [
        {
            "text": "Hello",
            "page_number": 1
        }
    ]

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "file.pdf",
                b"hello",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "indexed"
    assert body["file_name"] == "file.pdf"

    mock_index.assert_called_once()
    


@patch("app.api.v1.documents.get_all_documents")
def test_list_documents_success(mock_docs):

    mock_docs.return_value = [
        "file1.pdf",
        "file2.docx"
    ]

    response = client.get("/documents")

    assert response.status_code == 200

    body = response.json()

    assert len(body["documents"]) == 2
    assert body["documents"][0]["file_name"] == "file1.pdf"


@patch("app.api.v1.documents.get_all_documents")
def test_list_documents_empty(mock_docs):

    mock_docs.return_value = []

    response = client.get("/documents")

    assert response.status_code == 200

    assert response.json()["documents"] == []


@patch("app.api.v1.documents.get_all_documents")
def test_list_documents_error(mock_docs):

    mock_docs.side_effect = Exception("ES error")

    response = client.get("/documents")

    assert response.status_code == 500


@patch("app.api.v1.documents.redis_client", None)
def test_search_history_without_redis():

    response = client.get("/search/history")

    assert response.status_code == 200
    assert response.json()["history"] == []


@patch("app.api.v1.documents.redis_client")
def test_search_history_success(mock_redis):

    mock_redis.lrange.return_value = [
        '{"query":"python","files_found":["book.pdf"],"total_results":1,"timestamp":"2024"}'
    ]

    response = client.get("/search/history")

    assert response.status_code == 200

    body = response.json()

    assert len(body["history"]) == 1
    assert body["history"][0]["query"] == "python"


@patch("app.api.v1.documents.redis_client")
def test_search_history_error(mock_redis):

    mock_redis.lrange.side_effect = Exception()

    response = client.get("/search/history")

    assert response.status_code == 500
    
from unittest.mock import patch


@patch("app.api.v1.documents.es_client")
def test_search_success(mock_es):

    mock_es.search.return_value = {
        "hits": {
            "total": {
                "value": 1
            },
            "hits": [
                {
                    "_score": 1.2,
                    "_source": {
                        "chunk_id": "1",
                        "file_name": "book.pdf",
                        "page_number": 2,
                        "text": "Python tutorial"
                    }
                }
            ]
        }
    }

    response = client.get(
        "/search",
        params={
            "q": "python"
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["results"]) == 1
    assert body["results"][0]["file_name"] == "book.pdf"


@patch("app.api.v1.documents.es_client")
def test_search_empty_result(mock_es):

    mock_es.search.return_value = {
        "hits": {
            "total": {
                "value": 0
            },
            "hits": []
        }
    }

    response = client.get(
        "/search",
        params={
            "q": "python"
        }
    )

    assert response.status_code == 200

    assert response.json()["results"] == []


def test_search_empty_query():

    response = client.get(
        "/search",
        params={
            "q": ""
        }
    )

    assert response.status_code == 422
    
def test_search_whitespace_query():

    response = client.get(
        "/search",
        params={
            "q": "   "
        }
    )

    assert response.status_code == 400


@patch("app.api.v1.documents.es_client")
def test_search_elasticsearch_error(mock_es):

    mock_es.search.side_effect = Exception("ES error")

    response = client.get(
        "/search",
        params={
            "q": "python"
        }
    )

    assert response.status_code == 500


@patch("app.api.v1.documents.es_client", None)
def test_search_without_client():

    response = client.get(
        "/search",
        params={
            "q": "python"
        }
    )

    assert response.status_code == 500
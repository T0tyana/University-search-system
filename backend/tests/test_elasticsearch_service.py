from unittest.mock import MagicMock, patch
import pytest
from elasticsearch import ConnectionError

from app.services.elasticsearch_service import (
    create_index,
    check_file_exists,
    get_file_id_by_name,
    delete_file_by_name,
    index_chunks,
    get_all_documents,
)

def test_create_index_already_exists():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.indices.exists.return_value = True

        assert create_index() is True

        mock_es.indices.create.assert_not_called()


def test_create_index_success():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.indices.exists.return_value = False

        assert create_index() is True

        mock_es.indices.create.assert_called_once()


def test_create_index_without_client():

    with patch("app.services.elasticsearch_service.es_client", None):

        assert create_index() is False

def test_check_file_exists_true():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.return_value = {
            "hits": {
                "total": {
                    "value": 1
                }
            }
        }

        assert check_file_exists("document.pdf") is True


def test_check_file_exists_false():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.return_value = {
            "hits": {
                "total": {
                    "value": 0
                }
            }
        }

        assert check_file_exists("document.pdf") is False


def test_check_file_exists_without_client():

    with patch("app.services.elasticsearch_service.es_client", None):

        assert check_file_exists("document.pdf") is False


def test_check_file_exists_exception():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.side_effect = Exception("Elasticsearch error")

        assert check_file_exists("document.pdf") is False

# ---------------- create_index ----------------

def test_create_index_already_exists():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.indices.exists.return_value = True

        assert create_index() is True

        mock_es.indices.create.assert_not_called()


def test_create_index_success():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.indices.exists.return_value = False

        assert create_index() is True

        mock_es.indices.create.assert_called_once()


def test_create_index_without_client():

    with patch("app.services.elasticsearch_service.es_client", None):

        assert create_index() is False


# ---------------- check_file_exists ----------------

def test_check_file_exists_true():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.return_value = {
            "hits": {
                "total": {
                    "value": 1
                }
            }
        }

        assert check_file_exists("document.pdf") is True


def test_check_file_exists_false():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.return_value = {
            "hits": {
                "total": {
                    "value": 0
                }
            }
        }

        assert check_file_exists("document.pdf") is False


def test_check_file_exists_without_client():

    with patch("app.services.elasticsearch_service.es_client", None):

        assert check_file_exists("document.pdf") is False


def test_check_file_exists_exception():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.side_effect = Exception()

        assert check_file_exists("document.pdf") is False


# ---------------- get_file_id_by_name ----------------

def test_get_file_id_success():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "file_id": "123"
                        }
                    }
                ]
            }
        }

        assert get_file_id_by_name("doc.pdf") == "123"


def test_get_file_id_not_found():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.return_value = {
            "hits": {
                "hits": []
            }
        }

        assert get_file_id_by_name("doc.pdf") is None


def test_get_file_id_without_client():

    with patch("app.services.elasticsearch_service.es_client", None):

        assert get_file_id_by_name("doc.pdf") is None


def test_get_file_id_exception():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.side_effect = Exception()

        assert get_file_id_by_name("doc.pdf") is None


# ---------------- delete_file_by_name ----------------

def test_delete_file_success():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.delete_by_query.return_value = {
            "deleted": 5
        }

        assert delete_file_by_name("doc.pdf") == 5


def test_delete_file_without_client():

    with patch("app.services.elasticsearch_service.es_client", None):

        with pytest.raises(ValueError):

            delete_file_by_name("doc.pdf")


def test_delete_file_connection_error():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.delete_by_query.side_effect = ConnectionError("error")

        with pytest.raises(ValueError):

            delete_file_by_name("doc.pdf")


# ---------------- index_chunks ----------------

def test_index_chunks_success():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.bulk.return_value = {
            "errors": False
        }

        chunks = [
            {
                "text": "hello",
                "page_number": 1
            }
        ]

        index_chunks("1", "doc.pdf", chunks)

        mock_es.bulk.assert_called_once()


def test_index_chunks_empty():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        index_chunks("1", "doc.pdf", [])

        mock_es.bulk.assert_not_called()


def test_index_chunks_bulk_error():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.bulk.return_value = {
            "errors": True,
            "items": [
                {
                    "index": {
                        "error": "failed"
                    }
                }
            ]
        }

        chunks = [
            {
                "text": "hello",
                "page_number": 1
            }
        ]

        with pytest.raises(ValueError):

            index_chunks("1", "doc.pdf", chunks)


def test_index_chunks_without_client():

    chunks = [
        {
            "text": "hello",
            "page_number": 1
        }
    ]

    with patch("app.services.elasticsearch_service.es_client", None):

        with pytest.raises(ValueError):

            index_chunks("1", "doc.pdf", chunks)


# ---------------- get_all_documents ----------------

def test_get_all_documents_success():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.return_value = {
            "aggregations": {
                "unique_files": {
                    "buckets": [
                        {
                            "key": "one.pdf"
                        },
                        {
                            "key": "two.pdf"
                        }
                    ]
                }
            }
        }

        assert get_all_documents() == [
            "one.pdf",
            "two.pdf"
        ]


def test_get_all_documents_without_client():

    with patch("app.services.elasticsearch_service.es_client", None):

        with pytest.raises(ValueError):

            get_all_documents()


def test_get_all_documents_connection_error():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.side_effect = ConnectionError("error")

        with pytest.raises(ValueError):

            get_all_documents()
            

def test_create_index_connection_error():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.indices.exists.return_value = False
        mock_es.indices.create.side_effect = ConnectionError("connection")

        assert create_index() is False


def test_create_index_unknown_exception():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.indices.exists.return_value = False
        mock_es.indices.create.side_effect = Exception("boom")

        assert create_index() is False


def test_delete_file_unknown_exception():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.delete_by_query.side_effect = Exception("boom")

        with pytest.raises(ValueError):

            delete_file_by_name("doc.pdf")


def test_index_chunks_connection_error():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.bulk.side_effect = ConnectionError("boom")

        chunks = [
            {
                "text": "hello",
                "page_number": 1
            }
        ]

        with pytest.raises(ValueError):

            index_chunks("1", "doc.pdf", chunks)


def test_index_chunks_unknown_exception():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.bulk.side_effect = Exception("boom")

        chunks = [
            {
                "text": "hello",
                "page_number": 1
            }
        ]

        with pytest.raises(ValueError):

            index_chunks("1", "doc.pdf", chunks)


def test_get_all_documents_unknown_exception():

    with patch("app.services.elasticsearch_service.es_client") as mock_es:

        mock_es.search.side_effect = Exception("boom")

        with pytest.raises(ValueError):

            get_all_documents()
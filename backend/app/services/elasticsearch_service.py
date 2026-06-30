import logging
import uuid
from typing import Optional
from elasticsearch import Elasticsearch, ConnectionError, RequestError
from app.core.config import settings

logger = logging.getLogger(__name__)

# Инициализация клиента Elasticsearch
try:
    es_client = Elasticsearch([settings.ELASTICSEARCH_URL])
    if not es_client.ping():
        logger.error("Elasticsearch connection failed")
        es_client = None
    else:
        logger.info("Elasticsearch connected successfully")
except Exception as e:
    logger.error(f"Failed to connect to Elasticsearch: {e}")
    es_client = None

INDEX_NAME = "documents"


def create_index() -> bool:
    """
    Создает индекс documents с русскоязычным анализатором и корректным маппингом.
    
    Returns:
        True, если индекс создан или уже существует, False при ошибке.
    """
    if es_client is None:
        logger.error("Elasticsearch client is not initialized")
        return False
    
    try:
        if es_client.indices.exists(index=INDEX_NAME):
            logger.info(f"Index '{INDEX_NAME}' already exists")
            return True
        
        mapping = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "russian_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "russian_stop", "russian_stemmer"]
                        }
                    },
                    "filter": {
                        "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                        "russian_stemmer": {"type": "stemmer", "language": "russian"}
                    }
                }
            },
            "mappings": {
                "properties": {
                    "file_id": {"type": "keyword"},
                    "file_name": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "page_number": {"type": "integer"},
                    "chunk_id": {"type": "keyword"},
                    "text": {"type": "text", "analyzer": "russian_analyzer"}
                }
            }
        }
        
        es_client.indices.create(index=INDEX_NAME, body=mapping)
        logger.info(f"Index '{INDEX_NAME}' created successfully")
        return True
        
    except RequestError as e:
        logger.error(f"Elasticsearch mapping error: {e}")
        return False
    except ConnectionError as e:
        logger.error(f"Elasticsearch connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating index: {e}", exc_info=True)
        return False


def check_file_exists(file_name: str) -> bool:
    """
    Проверяет, существует ли файл с данным именем в индексе.
    
    Args:
        file_name: Имя файла для проверки.
        
    Returns:
        True, если файл найден, иначе False.
    """
    if es_client is None:
        return False
    
    try:
        response = es_client.search(
            index=INDEX_NAME,
            body={
                "query": {
                    "term": {
                        "file_name.keyword": file_name
                    }
                },
                "size": 0
            }
        )
        total_hits = response['hits']['total']['value']
        return total_hits > 0
        
    except Exception as e:
        logger.error(f"Error checking file existence: {e}", exc_info=True)
        return False


def get_file_id_by_name(file_name: str) -> Optional[str]:
    """
    Получает file_id документа по его имени.
    
    Args:
        file_name: Имя файла.
        
    Returns:
        file_id (str) если найден, иначе None.
    """
    if es_client is None:
        return None
    
    try:
        response = es_client.search(
            index=INDEX_NAME,
            body={
                "query": {
                    "term": {
                        "file_name.keyword": file_name
                    }
                },
                "size": 1,
                "_source": ["file_id"]
            }
        )
        hits = response['hits']['hits']
        if hits:
            return hits[0]['_source']['file_id']
        return None
    except Exception as e:
        logger.error(f"Error getting file_id by name: {e}", exc_info=True)
        return None


def delete_file_by_name(file_name: str) -> int:
    """
    Удаляет все чанки документа из Elasticsearch по имени файла.
    
    Args:
        file_name: Имя файла для удаления.
        
    Returns:
        Количество удалённых документов (чанков).
        
    Raises:
        ValueError: Если Elasticsearch недоступен.
    """
    if es_client is None:
        raise ValueError("Elasticsearch client is not initialized")
    
    try:
        response = es_client.delete_by_query(
            index=INDEX_NAME,
            body={
                "query": {
                    "term": {
                        "file_name.keyword": file_name
                    }
                }
            },
            refresh=True
        )
        deleted_count = response.get('deleted', 0)
        logger.info(f"Deleted {deleted_count} chunks for file: {file_name}")
        return deleted_count
        
    except ConnectionError as e:
        logger.error(f"Elasticsearch connection error during deletion: {e}")
        raise ValueError("Ошибка подключения к Elasticsearch")
    except Exception as e:
        logger.error(f"Error deleting file from Elasticsearch: {e}", exc_info=True)
        raise ValueError(f"Ошибка удаления документа: {str(e)}")


def index_chunks(file_id: str, file_name: str, chunks_with_meta: list[dict]) -> None:
    """
    Индексирует чанки документа в Elasticsearch с немедленным обновлением.
    
    Args:
        file_id: UUID файла.
        file_name: Имя файла.
        chunks_with_meta: Список чанков с метаданными.
        
    Raises:
        ValueError: Если Elasticsearch недоступен или произошла ошибка индексации.
    """
    if es_client is None:
        raise ValueError("Elasticsearch client is not initialized")
    
    if not chunks_with_meta:
        logger.warning(f"No chunks to index for file: {file_name}")
        return
    
    operations = []
    for item in chunks_with_meta:
        doc = {
            "file_id": file_id,
            "file_name": file_name,
            "page_number": item['page_number'],
            "chunk_id": str(uuid.uuid4()),
            "text": item['text']
        }
        operations.append({"index": {"_index": INDEX_NAME}})
        operations.append(doc)
    
    try:
        response = es_client.bulk(operations=operations, refresh=True)
        
        if response.get('errors'):
            error_items = [item for item in response['items'] if item['index'].get('error')]
            logger.error(f"Bulk indexing errors: {error_items}")
            raise ValueError(f"Ошибка индексации: {len(error_items)} документов не удалось проиндексировать")
        
        logger.info(f"Successfully indexed {len(chunks_with_meta)} chunks for file: {file_name}")
        
    except ConnectionError as e:
        logger.error(f"Elasticsearch connection error during indexing: {e}")
        raise ValueError("Ошибка подключения к Elasticsearch")
    except Exception as e:
        logger.error(f"Error indexing chunks: {e}", exc_info=True)
        raise ValueError(f"Ошибка индексации документов: {str(e)}")


def get_all_documents() -> list[str]:
    """
    Получает список уникальных имен файлов из индекса Elasticsearch.
    
    Returns:
        Список строк с названиями файлов.
        
    Raises:
        ValueError: Если произошла ошибка при получении списка.
    """
    if es_client is None:
        raise ValueError("Elasticsearch client is not initialized")
    
    try:
        response = es_client.search(
            index=INDEX_NAME,
            body={
                "size": 0,
                "aggs": {
                    "unique_files": {
                        "terms": {"field": "file_name.keyword", "size": 1000}
                    }
                }
            }
        )
        buckets = response.get('aggregations', {}).get('unique_files', {}).get('buckets', [])
        return [b['key'] for b in buckets]
        
    except ConnectionError as e:
        logger.error(f"Elasticsearch connection error: {e}")
        raise ValueError("Ошибка подключения к Elasticsearch")
    except Exception as e:
        logger.error(f"Error getting document list: {e}", exc_info=True)
        raise ValueError(f"Ошибка получения списка документов: {str(e)}")
    
def search_documents(query: str, page: int = 1, size: int = 10) -> dict:
    """
    Выполняет полнотекстовый поиск с подсветкой совпадений.
    
    Args:
        query: Поисковый запрос.
        page: Номер страницы (начинается с 1).
        size: Количество результатов на странице.
        
    Returns:
        Словарь с результатами поиска и метаданными.
        
    Raises:
        ValueError: Если Elasticsearch недоступен.
    """
    if es_client is None:
        raise ValueError("Elasticsearch client is not initialized")
    
    from_offset = (page - 1) * size
    
    search_body = {
        "from": from_offset,
        "size": size,
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["text"],
                "type": "best_fields",
                "fuzziness": "AUTO"  # защита от опечаток
            }
        },
        # 🔑 КЛЮЧЕВАЯ ЧАСТЬ — настройка подсветки
        "highlight": {
            "pre_tags": ["<mark>"],     # открывающий тег подсветки
            "post_tags": ["</mark>"],   # закрывающий тег подсветки
            "fields": {
                "text": {
                    "fragment_size": 200,      # длина фрагмента в символах
                    "number_of_fragments": 3,  # максимум фрагментов на документ
                    "boundary_scanner": "sentence"  # резать по предложениям
                }
            }
        }
    }
    
    try:
        response = es_client.search(index=INDEX_NAME, body=search_body)
    except ConnectionError as e:
        logger.error(f"Elasticsearch connection error during search: {e}")
        raise ValueError("Ошибка подключения к Elasticsearch")
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise ValueError(f"Ошибка поиска: {str(e)}")
    
    total = response['hits']['total']['value']
    results = []
    
    for hit in response['hits']['hits']:
        source = hit['_source']
        score = hit.get('_score', 0) or 0
        
        # Elasticsearch возвращает подсветку в отдельном поле highlight
        highlight_fragments = hit.get('highlight', {}).get('text', [])
        
        results.append({
            "chunk_id": source.get('chunk_id', ''),
            "file_name": source.get('file_name', ''),
            "page": source.get('page_number', 1),
            "text": source.get('text', ''),
            "score": round(score, 4),
            # Если подсветки нет (маловероятно при совпадении), отдаём None
            "highlighted_text": highlight_fragments if highlight_fragments else None
        })
    
    logger.info(f"Search query='{query}': found {total} results, returned {len(results)}")
    
    return {
        "query": query,
        "results": results,
        "total": total,
        "page": page,
        "size": size
    }
from elasticsearch import Elasticsearch
from app.core.config import settings
import uuid

es_client = Elasticsearch([settings.ELASTICSEARCH_URL])
INDEX_NAME = "documents"

def create_index():
    """
    Создает индекс documents с русским анализатором и корректным маппингом.
    
    Returns:
        True, если индекс создан или уже существует.
    """
    if es_client.indices.exists(index=INDEX_NAME):
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
                # Явное определение keyword-подполя для агрегаций
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
    try:
        es_client.indices.create(index=INDEX_NAME, body=mapping)
        print(f"Index '{INDEX_NAME}' created with correct mapping.")
        return True
    except Exception as e:
        print(f"Error creating index: {e}")
        return False

def index_chunks(file_id: str, file_name: str, chunks_with_meta: list[dict]):
    """
    Индексирует чанки документа в Elasticsearch с немедленным обновлением.
    
    Args:
        file_id: UUID файла.
        file_name: Имя файла.
        chunks_with_meta: Список чанков с метаданными.
    """
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
        
    if operations:
        # refresh=True делает данные доступными для поиска синхронно
        es_client.bulk(operations=operations, refresh=True) 

def get_all_documents() -> list[str]:
    """
    Получает список уникальных имен файлов из индекса Elasticsearch.
    
    Returns:
        Список строк с названиями файлов.
    """
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
    except Exception as e:
        print(f"Error getting document list: {e}")
        return []
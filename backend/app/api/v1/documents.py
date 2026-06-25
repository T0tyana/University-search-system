import os
import uuid
import json
import redis
from datetime import datetime
from typing import Optional
from app.services.elasticsearch_service import index_chunks, get_all_documents, es_client
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from app.models.schemas import (
    UploadResponse, SearchResponse, SearchResult, 
    DocumentListResponse, DocumentInfo, SearchHistoryResponse
)
from app.core.config import settings
from app.services.document_processor import process_document
from app.services.auth_service import get_current_user
from app.models.user import User

router = APIRouter()

# Безопасная инициализация Redis
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None
    print("Warning: Redis unavailable. Caching and History disabled.")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024

@router.post("/documents/upload", response_model=UploadResponse, summary="Загрузка документа")
async def upload_document(
    file: UploadFile = File(..., description="Файл PDF или DOCX"),
    current_user: User = Depends(get_current_user)
):
    """
    Загружает файл, валидирует его, сохраняет и индексирует в Elasticsearch.
    Требует авторизации.
    
    Args:
        file: Загружаемый файл.
        current_user: Текущий авторизованный пользователь.
        
    Returns:
        Информация о загруженном файле (file_id, file_name, status).
        
    Raises:
        HTTPException: 400 Bad Request (неверный формат/размер), 500 Internal Server Error (ошибка обработки).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")
        
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Неподдерживаемый формат. Только {ALLOWED_EXTENSIONS}")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail=f"Файл слишком большой. Максимум {settings.MAX_FILE_SIZE_MB} МБ")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_ext}")
    
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        chunks_with_meta = process_document(file_id, file_ext)
        if not chunks_with_meta:
             raise HTTPException(status_code=400, detail="Не удалось извлечь текст из файла")
        
        index_chunks(file_id, file.filename, chunks_with_meta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {str(e)}")

    return UploadResponse(file_id=file_id, file_name=file.filename, status="indexed")

@router.get("/search", response_model=SearchResponse, summary="Поиск по документам")
async def search_documents(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    file_name: Optional[str] = Query(None, description="Фильтр по имени файла"),
    page: int = Query(1, ge=1, description="Номер страницы результатов"),
    size: int = Query(10, ge=1, le=100, description="Количество результатов на странице"),
    current_user: User = Depends(get_current_user)
):
    """
    Выполняет полнотекстовый поиск в Elasticsearch с кешированием в Redis.
    Требует авторизации.
    
    Args:
        q: Текст запроса.
        file_name: Опциональный фильтр по названию файла.
        page: Номер страницы пагинации.
        size: Размер страницы.
        current_user: Текущий авторизованный пользователь.
        
    Returns:
        Результаты поиска с метаданными и оценкой релевантности.
        
    Raises:
        HTTPException: 500 Internal Server Error при ошибке Elasticsearch.
    """
    # Безопасная работа с Redis (кеш + история)
    if redis_client:
        cache_key = f"search:{q}:{file_name}:{page}:{size}"
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return SearchResponse(**json.loads(cached_result))
        except Exception:
            pass

    try:
        from_val = (page - 1) * size
        query_body = {
            "from": from_val,
            "size": size,
            "query": {
                "bool": {
                    "must": [{"multi_match": {"query": q, "fields": ["text"]}}]
                }
            }
        }
        
        if file_name:
            query_body["query"]["bool"]["filter"] = [
                {"term": {"file_name.keyword": file_name}}
            ]

        response = es_client.search(index="documents", body=query_body)
        hits = response['hits']['hits']
        total_hits = response['hits']['total']['value']
        
        results = [
            SearchResult(
                chunk_id=h['_source']['chunk_id'],
                file_name=h['_source']['file_name'],
                page=h['_source']['page_number'],
                text=h['_source']['text'],
                score=h['_score']
            ) for h in hits
        ]
        
        final_response = SearchResponse(query=q, results=results, total=total_hits, page=page, size=size)
        
        # Сохраняем в кеш и историю ТОЛЬКО если Redis жив
        if redis_client:
            try:
                redis_client.setex(cache_key, 300, json.dumps(final_response.dict()))
                
                # Персональная история поиска
                history_key = f"user_history:{current_user.username}"
                history_item = {"query": q, "timestamp": datetime.now().isoformat()}
                redis_client.lpush(history_key, json.dumps(history_item))
                redis_client.ltrim(history_key, 0, 99)
            except Exception:
                pass
                
        return final_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска: {str(e)}")

@router.get("/documents", response_model=DocumentListResponse, summary="Список документов")
async def list_documents():
    """
    Возвращает список всех уникальных имен файлов, проиндексированных в системе.
    
    Returns:
        Список объектов DocumentInfo.
    """
    files = get_all_documents()
    docs = [DocumentInfo(file_name=f) for f in files]
    return DocumentListResponse(documents=docs)

@router.get("/search/history", response_model=SearchHistoryResponse, summary="История поиска")
async def get_search_history(current_user: User = Depends(get_current_user)):
    """
    Возвращает персональную историю поисковых запросов текущего пользователя.
    Требует авторизации.
    
    Args:
        current_user: Текущий авторизованный пользователь.
        
    Returns:
        Список элементов истории поиска.
    """
    if not redis_client:
        return SearchHistoryResponse(history=[])
        
    try:
        # Читаем ПЕРСОНАЛЬНУЮ историю
        history_key = f"user_history:{current_user.username}"
        items = redis_client.lrange(history_key, 0, -1)
        history = [json.loads(item) for item in items]
        return SearchHistoryResponse(history=history)
    except Exception:
        return SearchHistoryResponse(history=[])
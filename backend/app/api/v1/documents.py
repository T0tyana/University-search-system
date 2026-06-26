import os
import uuid
import json
import logging
import redis
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends, status
from app.services.elasticsearch_service import (
    index_chunks, get_all_documents, es_client, 
    check_file_exists, delete_file_by_name, get_file_id_by_name
)
from app.models.schemas import (
    UploadResponse, SearchResponse, SearchResult, 
    DocumentListResponse, DocumentInfo, SearchHistoryResponse, 
    ConflictResponse, DeleteResponse
)
from app.core.config import settings
from app.services.document_processor import process_document
from app.services.auth_service import get_current_user
from app.models.user import User

# Настройка логирования
logger = logging.getLogger(__name__)

router = APIRouter()

# Безопасная инициализация Redis
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connected successfully")
except Exception as e:
    redis_client = None
    logger.warning(f"Redis unavailable: {e}. Caching and History disabled.")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post(
    "/documents/upload",
    response_model=UploadResponse,
    summary="Загрузка документа",
    responses={
        200: {"description": "Документ успешно загружен и проиндексирован"},
        400: {"description": "Ошибка валидации файла (формат, размер, содержимое)"},
        401: {"description": "Требуется авторизация"},
        404: {"description": "Файл не найден после сохранения"},
        409: {"description": "Файл с таким именем уже существует в системе"},
        422: {"description": "Ошибка валидации данных запроса"},
        500: {"description": "Внутренняя ошибка сервера при обработке файла"},
    }
)
async def upload_document(
    file: UploadFile = File(..., description="Файл PDF или DOCX"),
    current_user: User = Depends(get_current_user)
):
    """
    Загружает файл, валидирует его, сохраняет и индексирует в Elasticsearch.
    Требует авторизации.
    Проверяет наличие дубликатов по имени файла.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Имя файла отсутствует"
        )
    
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый формат файла. Разрешены только: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    if check_file_exists(file.filename):
        logger.warning(f"Duplicate upload attempt: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Файл '{file.filename}' уже существует в системе",
        )
    
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка чтения файла"
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл пустой"
        )
    
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимальный размер: {settings.MAX_FILE_SIZE_MB} МБ"
        )
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_ext}")
    
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except IOError as e:
        logger.error(f"Error saving file {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сохранения файла на сервере"
        )
    
    try:
        chunks_with_meta = process_document(file_id, file_ext)
        
        if not chunks_with_meta:
            try:
                os.remove(file_path)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось извлечь текст из файла. Возможно, файл поврежден или не содержит текста"
            )
        
        index_chunks(file_id, file.filename, chunks_with_meta)
        logger.info(f"Document {file.filename} (ID: {file_id}) indexed successfully")
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"File not found during processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден после сохранения"
        )
    except ValueError as e:
        logger.error(f"Value error during document processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error processing file {file_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при обработке файла"
        )
    
    return UploadResponse(file_id=file_id, file_name=file.filename, status="indexed")


@router.delete(
    "/documents/{file_name}",
    response_model=DeleteResponse,
    summary="Удаление документа по имени",
    responses={
        200: {"description": "Документ успешно удалён из системы"},
        401: {"description": "Требуется авторизация"},
        404: {"description": "Документ с таким именем не найден"},
        500: {"description": "Внутренняя ошибка сервера при удалении"},
    }
)
async def delete_document(
    file_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Удаляет документ по его имени из Elasticsearch и с диска.
    Требует авторизации.
    
    Процесс удаления:
    1. Проверяет наличие документа в Elasticsearch
    2. Получает file_id для поиска физического файла
    3. Удаляет все чанки из Elasticsearch
    4. Удаляет физический файл из папки uploads/
    5. Очищает кеш поиска, связанный с удалённым файлом
    """
    # Валидация имени файла
    if not file_name or not file_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Имя файла не может быть пустым"
        )
    
    # Проверяем, существует ли документ
    if not check_file_exists(file_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Документ '{file_name}' не найден в системе"
        )
    
    # Получаем file_id для удаления физического файла
    file_id = get_file_id_by_name(file_name)
    
    # Определяем расширение для поиска физического файла
    file_ext = file_name.split(".")[-1].lower() if "." in file_name else None
    
    # 1. Удаляем из Elasticsearch
    try:
        chunks_deleted = delete_file_by_name(file_name)
        logger.info(f"Deleted {chunks_deleted} chunks from ES for file: {file_name}")
    except ValueError as e:
        logger.error(f"Error deleting from Elasticsearch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления из Elasticsearch: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting from ES: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка при удалении из Elasticsearch"
        )
    
    # 2. Удаляем физический файл с диска
    file_removed = False
    if file_id and file_ext:
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_ext}")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                file_removed = True
                logger.info(f"Physical file removed: {file_path}")
            else:
                logger.warning(f"Physical file not found on disk: {file_path}")
        except Exception as e:
            logger.error(f"Error removing physical file {file_path}: {e}")
            # Не прерываем операцию — чанки уже удалены из ES
    
    # 3. Очищаем кеш поиска, связанный с этим файлом
    if redis_client:
        try:
            cursor = 0
            deleted_cache_keys = 0
            while True:
                cursor, keys = redis_client.scan(cursor, match=f"search:*:{file_name}:*", count=100)
                if keys:
                    deleted_cache_keys += redis_client.delete(*keys)
                if cursor == 0:
                    break
            if deleted_cache_keys > 0:
                logger.info(f"Cleared {deleted_cache_keys} cache keys for file: {file_name}")
        except Exception as e:
            logger.warning(f"Error clearing cache for deleted file: {e}")
    
    logger.info(f"Document '{file_name}' fully deleted by user: {current_user.username}")
    
    return DeleteResponse(
        msg="Документ успешно удалён",
        file_name=file_name,
        chunks_deleted=chunks_deleted,
        file_removed_from_disk=file_removed
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Поиск по документам",
    responses={
        200: {"description": "Поиск выполнен успешно (может вернуть 0 результатов)"},
        400: {"description": "Пустой или невалидный поисковый запрос"},
        401: {"description": "Требуется авторизация"},
        422: {"description": "Ошибка валидации query-параметров"},
        500: {"description": "Ошибка выполнения поискового запроса в Elasticsearch"},
    }
)
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
    """
    if not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поисковый запрос не может быть пустым"
        )
    
    if redis_client:
        cache_key = f"search:{q}:{file_name}:{page}:{size}"
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for query: {q}")
                return SearchResponse(**json.loads(cached_result))
        except Exception as e:
            logger.warning(f"Redis cache read error: {e}")
    
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
        
        final_response = SearchResponse(
            query=q, 
            results=results, 
            total=total_hits, 
            page=page, 
            size=size
        )
        
        if redis_client:
            try:
                redis_client.setex(cache_key, 300, json.dumps(final_response.dict()))
                
                history_key = f"user_history:{current_user.username}"
                files_found = list({h['_source']['file_name'] for h in hits})
                history_item = {
                    "query": q,
                    "files_found": files_found,
                    "total_results": total_hits,
                    "timestamp": datetime.now().isoformat()
                }
                redis_client.lpush(history_key, json.dumps(history_item))
                redis_client.ltrim(history_key, 0, 99)
            except Exception as e:
                logger.warning(f"Redis cache/history write error: {e}")
        
        logger.info(f"Search query '{q}' returned {total_hits} results")
        return final_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Elasticsearch search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка выполнения поискового запроса"
        )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="Список документов",
    responses={
        200: {"description": "Список документов успешно получен (может быть пустым)"},
        401: {"description": "Требуется авторизация"},
        500: {"description": "Ошибка получения списка документов"},
    }
)
async def list_documents(current_user: User = Depends(get_current_user)):
    """
    Возвращает список всех уникальных имен файлов, проиндексированных в системе.
    Требует авторизации.
    """
    try:
        files = get_all_documents()
        docs = [DocumentInfo(file_name=f) for f in files]
        return DocumentListResponse(documents=docs)
    except Exception as e:
        logger.error(f"Error getting document list: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения списка документов"
        )


@router.get(
    "/search/history",
    response_model=SearchHistoryResponse,
    summary="История поиска",
    responses={
        200: {"description": "История поиска успешно получена (может быть пустой)"},
        401: {"description": "Требуется авторизация"},
        500: {"description": "Ошибка получения истории поиска из Redis"},
    }
)
async def get_search_history(current_user: User = Depends(get_current_user)):
    """
    Возвращает персональную историю поисковых запросов текущего пользователя.
    Требует авторизации.
    """
    if not redis_client:
        return SearchHistoryResponse(history=[])
        
    try:
        history_key = f"user_history:{current_user.username}"
        items = redis_client.lrange(history_key, 0, -1)
        history = [json.loads(item) for item in items]
        return SearchHistoryResponse(history=history)
    except Exception as e:
        logger.error(f"Error getting search history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения истории поиска"
        )
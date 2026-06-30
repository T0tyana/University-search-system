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
    SearchHistoryItem, ConflictResponse, DeleteResponse
)
from app.core.config import settings
from app.services.document_processor import process_document
from app.services.auth_service import get_current_user
from app.models.user import User
from app.services.elasticsearch_service import search_documents
import json

logger = logging.getLogger(__name__)

router = APIRouter()

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


def _cleanup_file(file_path: str):
    """Вспомогательная функция для удаления файла с диска."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {e}")


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
            _cleanup_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось извлечь текст из файла. Возможно, файл поврежден или не содержит текста"
            )
        
        index_chunks(file_id, file.filename, chunks_with_meta)
        logger.info(f"Document {file.filename} (ID: {file_id}) indexed successfully")
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        _cleanup_file(file_path)
        logger.error(f"File not found during processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден после сохранения"
        )
    except ValueError as e:
        _cleanup_file(file_path)
        logger.error(f"Value error during document processing: {e}")
        error_msg = str(e).lower()
        if "pdf" in error_msg or "docx" in error_msg or "package not found" in error_msg or "root object" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл поврежден или имеет неверный формат. Загрузите корректный PDF или DOCX файл"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка обработки файла: {str(e)}"
            )
    except Exception as e:
        _cleanup_file(file_path)
        logger.error(f"Unexpected error processing file {file_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при обработке файла"
        )
    
    return UploadResponse(file_id=file_id, file_name=file.filename, status="indexed")


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="Список всех документов",
    responses={
        200: {"description": "Список документов успешно получен"},
        401: {"description": "Требуется авторизация"},
        500: {"description": "Внутренняя ошибка сервера / Elasticsearch недоступен"},
    }
)
async def list_documents(
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает список всех загруженных документов в системе.
    Требует авторизации.
    """
    try:
        files = get_all_documents()
        documents = [DocumentInfo(file_name=f) for f in files]
        return DocumentListResponse(documents=documents)
    except ValueError as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/documents/{file_name:path}",
    response_model=DeleteResponse,
    summary="Удаление документа",
    responses={
        200: {"description": "Документ успешно удалён"},
        401: {"description": "Требуется авторизация"},
        404: {"description": "Документ не найден в системе"},
        500: {"description": "Внутренняя ошибка сервера"},
    }
)
async def delete_document(
    file_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Удаляет документ из Elasticsearch и физический файл с диска.
    Требует авторизации.
    """
    # 1. Проверяем, существует ли документ в Elasticsearch
    file_id = get_file_id_by_name(file_name)
    if not file_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Документ '{file_name}' не найден в системе"
        )
    
    # 2. Удаляем из Elasticsearch
    try:
        chunks_deleted = delete_file_by_name(file_name)
    except ValueError as e:
        logger.error(f"Error deleting from Elasticsearch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    # 3. Удаляем физический файл с диска
    file_removed = False
    for ext in ALLOWED_EXTENSIONS:
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{ext}")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                file_removed = True
                logger.info(f"Deleted physical file: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting physical file {file_path}: {e}")
    
    # 4. Очищаем кэш поиска, если он был связан с этим файлом
    if redis_client:
        try:
            # Удаляем все ключи кэша (упрощённый вариант — можно точечно)
            keys = redis_client.keys("search:*")
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} search cache keys")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
    
    return DeleteResponse(
        msg="Документ успешно удалён",
        file_name=file_name,
        chunks_deleted=chunks_deleted,
        file_removed_from_disk=file_removed
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Полнотекстовый поиск по документам",
    responses={
        200: {"description": "Поиск выполнен успешно, возвращены результаты с подсветкой"},
        400: {"description": "Пустой поисковый запрос"},
        401: {"description": "Требуется авторизация"},
        500: {"description": "Внутренняя ошибка сервера / Elasticsearch недоступен"},
    }
)
async def search(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    page: int = Query(1, ge=1, description="Номер страницы результатов"),
    size: int = Query(10, ge=1, le=100, description="Количество результатов на странице"),
    current_user: User = Depends(get_current_user)
):
    """
    Выполняет полнотекстовый поиск по загруженным документам.
    
    Результаты содержат поле `highlighted_text` с фрагментами,
    в которых совпадения обёрнуты в HTML-теги `<mark>...</mark>`.
    
    Частые запросы кэшируются в Redis на 5 минут (BE-10).
    История поиска сохраняется для текущего пользователя.
    """
    cache_key = f"search:{q.strip().lower()}:p{page}:s{size}"
    
    # 1. Проверяем кэш Redis
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"Cache HIT for query: {q}")
                return SearchResponse(**json.loads(cached))
        except Exception as e:
            logger.warning(f"Redis cache read error: {e}")
    
    # 2. Выполняем поиск в Elasticsearch
    try:
        search_result = search_documents(query=q, page=page, size=size)
    except ValueError as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    response = SearchResponse(**search_result)
    
    # 3. Сохраняем в кэш Redis (TTL = 5 минут)
    if redis_client:
        try:
            redis_client.setex(
                cache_key,
                300,  # 5 минут = 300 секунд
                response.model_dump_json()
            )
        except Exception as e:
            logger.warning(f"Redis cache write error: {e}")
    
    # 4. Сохраняем запрос в историю пользователя
    if redis_client:
        try:
            history_key = f"search_history:{current_user.username}"
            history_item = {
                "query": q,
                "files_found": list({r.file_name for r in response.results}),
                "total_results": response.total,
                "timestamp": datetime.utcnow().isoformat()
            }
            redis_client.lpush(history_key, json.dumps(history_item, ensure_ascii=False))
            redis_client.ltrim(history_key, 0, 49)  # храним последние 50 запросов
        except Exception as e:
            logger.warning(f"Failed to save search history: {e}")
    
    return response


@router.get(
    "/search/history",
    response_model=SearchHistoryResponse,
    summary="История поиска пользователя",
    responses={
        200: {"description": "История успешно получена"},
        401: {"description": "Требуется авторизация"},
    }
)
async def get_search_history(
    limit: int = Query(50, ge=1, le=100, description="Количество записей истории"),
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает историю поисковых запросов текущего пользователя.
    Хранятся последние 50 запросов с информацией о найденных файлах.
    Требует авторизации.
    """
    if not redis_client:
        return SearchHistoryResponse(history=[])
    
    try:
        history_key = f"search_history:{current_user.username}"
        history_items = redis_client.lrange(history_key, 0, limit - 1)
        
        history = []
        for item in history_items:
            try:
                data = json.loads(item)
                history.append(SearchHistoryItem(**data))
            except Exception as e:
                logger.warning(f"Error parsing history item: {e}")
                continue
        
        return SearchHistoryResponse(history=history)
    except Exception as e:
        logger.error(f"Error retrieving search history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения истории поиска"
        )
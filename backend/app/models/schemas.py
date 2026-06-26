from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class UploadResponse(BaseModel):
    """Модель ответа после успешной загрузки файла."""
    file_id: str = Field(..., description="Уникальный идентификатор файла (UUID)")
    file_name: str = Field(..., description="Оригинальное имя файла")
    status: str = Field("indexed", description="Статус обработки файла")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "file_name": "document.pdf",
                "status": "indexed"
            }
        }


class SearchResult(BaseModel):
    """Модель отдельного результата поиска."""
    chunk_id: str = Field(..., description="ID фрагмента текста")
    file_name: str = Field(..., description="Название документа")
    page: int = Field(..., description="Номер страницы в документе", ge=1)
    text: str = Field(..., description="Найденный фрагмент текста")
    score: float = Field(..., description="Оценка релевантности от Elasticsearch", ge=0)


class SearchResponse(BaseModel):
    """Модель ответа эндпоинта поиска."""
    query: str = Field(..., description="Поисковый запрос")
    results: List[SearchResult] = Field(default_factory=list, description="Список результатов поиска")
    total: int = Field(..., description="Общее количество найденных совпадений", ge=0)
    page: int = Field(..., description="Текущая страница результатов", ge=1)
    size: int = Field(..., description="Количество результатов на странице", ge=1, le=100)


class DocumentInfo(BaseModel):
    """Информация о загруженном документе."""
    file_name: str = Field(..., description="Название файла")
    upload_date: datetime = Field(default_factory=datetime.now, description="Дата загрузки")


class DocumentListResponse(BaseModel):
    """Список всех документов в системе."""
    documents: List[DocumentInfo] = Field(..., description="Список документов")


class SearchHistoryItem(BaseModel):
    """Элемент истории поиска."""
    query: str = Field(..., description="Текст поискового запроса")
    files_found: List[str] = Field(
        default_factory=list, 
        description="Список файлов, в которых найдены результаты"
    )
    total_results: int = Field(0, description="Общее количество найденных результатов")
    timestamp: datetime = Field(..., description="Время выполнения запроса")


class SearchHistoryResponse(BaseModel):
    """История поисковых запросов пользователя."""
    history: List[SearchHistoryItem] = Field(..., description="Список элементов истории")


class ErrorResponse(BaseModel):
    """Модель ответа с ошибкой."""
    detail: str = Field(..., description="Описание ошибки")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Описание ошибки"
            }
        }


class RegisterResponse(BaseModel):
    """Ответ после успешной регистрации пользователя."""
    msg: str = Field(..., description="Сообщение об успешной регистрации")
    
    class Config:
        json_schema_extra = {
            "example": {
                "msg": "User created successfully"
            }
        }


class LoginResponse(BaseModel):
    """Ответ после успешной авторизации пользователя."""
    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field("bearer", description="Тип токена (всегда bearer)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class ConflictResponse(BaseModel):
    """Ответ при попытке загрузить уже существующий файл."""
    detail: str = Field(..., description="Сообщение об ошибке")
    file_name: str = Field(..., description="Имя существующего файла")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Файл с таким именем уже существует в системе",
                "file_name": "document.pdf"
            }
        }


# ============================================================
# НОВАЯ МОДЕЛЬ для ответа при удалении документа
# ============================================================

class DeleteResponse(BaseModel):
    """Ответ после успешного удаления документа."""
    msg: str = Field(..., description="Сообщение о результате удаления")
    file_name: str = Field(..., description="Имя удалённого файла")
    chunks_deleted: int = Field(..., description="Количество удалённых чанков из Elasticsearch")
    file_removed_from_disk: bool = Field(..., description="Был ли удалён физический файл с диска")
    
    class Config:
        json_schema_extra = {
            "example": {
                "msg": "Документ успешно удалён",
                "file_name": "document.pdf",
                "chunks_deleted": 15,
                "file_removed_from_disk": True
            }
        }
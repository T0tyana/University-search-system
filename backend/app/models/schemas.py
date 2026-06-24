from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class UploadResponse(BaseModel):
    """Модель ответа после успешной загрузки файла."""
    file_id: str = Field(..., description="Уникальный идентификатор файла (UUID)")
    file_name: str = Field(..., description="Оригинальное имя файла")
    status: str = Field("indexed", description="Статус обработки файла")

class SearchResult(BaseModel):
    """Модель отдельного результата поиска."""
    chunk_id: str = Field(..., description="ID фрагмента текста")
    file_name: str = Field(..., description="Название документа")
    page: int = Field(..., description="Номер страницы в документе")
    text: str = Field(..., description="Найденный фрагмент текста")
    score: float = Field(..., description="Оценка релевантности от Elasticsearch")

class SearchResponse(BaseModel):
    """Модель ответа эндпоинта поиска."""
    query: str = Field(..., description="Поисковый запрос")
    results: List[SearchResult] = Field(default_factory=list)
    total: int = Field(..., description="Общее количество найденных совпадений")
    page: int = Field(..., description="Текущая страница результатов")
    size: int = Field(..., description="Количество результатов на странице")

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
    timestamp: datetime = Field(..., description="Время выполнения запроса")

class SearchHistoryResponse(BaseModel):
    """История поисковых запросов пользователя."""
    history: List[SearchHistoryItem] = Field(..., description="Список элементов истории")
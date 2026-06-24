from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import documents, auth
from app.services.elasticsearch_service import create_index
from app.models.database import engine, Base

app = FastAPI(
    title=settings.APP_NAME, 
    version=settings.APP_VERSION,
    description="Интеллектуальная поисковая система по базе знаний университета"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Инициализация БД и Elasticsearch при запуске приложения."""
    # Создаем таблицы в БД
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")
    
    # Создаем индекс в ES
    try:
        create_index()
        print("Elasticsearch index 'documents' is ready.")
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")

# Подключаем роутеры
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])

@app.get("/", summary="Health Check")
def read_root():
    """Проверка доступности сервиса."""
    return {"status": "ok"}
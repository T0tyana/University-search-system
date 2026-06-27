import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.api.v1 import documents, auth
from app.services.elasticsearch_service import create_index, es_client
from app.models.database import engine, Base
import redis

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME, 
    version=settings.APP_VERSION,
    description="Интеллектуальная поисковая система по базе знаний университета",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "auth", "description": "Авторизация и регистрация пользователей"},
        {"name": "documents", "description": "Загрузка и поиск документов"},
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Инициализация и проверка всех сервисов при запуске приложения."""
    logger.info("=" * 60)
    logger.info("🚀 Starting application startup checks...")
    logger.info("=" * 60)
    
    # 1. Проверка PostgreSQL
    logger.info("📊 Checking PostgreSQL connection...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ PostgreSQL: Connected successfully")
        logger.info(f"   Database: {settings.POSTGRES_DB}")
        logger.info(f"   Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    except Exception as e:
        logger.error(f"❌ PostgreSQL: Connection failed - {e}", exc_info=True)
        logger.warning("   Application will start without DB connection. Check your .env file.")
    
    # 2. Проверка Elasticsearch
    logger.info("🔍 Checking Elasticsearch connection...")
    try:
        if es_client and es_client.ping():
            if create_index():
                logger.info("✅ Elasticsearch: Connected successfully")
                logger.info(f"   URL: {settings.ELASTICSEARCH_URL}")
                logger.info("   Index 'documents' is ready")
            else:
                logger.warning("⚠️  Elasticsearch: Connected, but index creation failed")
        else:
            logger.error("❌ Elasticsearch: Connection failed - client not initialized")
    except Exception as e:
        logger.error(f"❌ Elasticsearch: Connection error - {e}", exc_info=True)
    
    # 3. Проверка Redis
    logger.info("🔴 Checking Redis connection...")
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Redis: Connected successfully")
        logger.info(f"   URL: {settings.REDIS_URL}")
        
        # Дополнительная проверка: запись и чтение тестового ключа
        test_key = "startup_test_key"
        redis_client.set(test_key, "test_value", ex=10)
        test_value = redis_client.get(test_key)
        redis_client.delete(test_key)
        
        if test_value == "test_value":
            logger.info("✅ Redis: Read/write operations working correctly")
        else:
            logger.warning("⚠️  Redis: Connected, but read/write test failed")
    except Exception as e:
        logger.error(f"❌ Redis: Connection failed - {e}", exc_info=True)
        logger.warning("   Caching and search history will be disabled")
    
    logger.info("=" * 60)
    logger.info("✅ Application startup checks completed")
    logger.info("=" * 60)


# Глобальный обработчик валидационных ошибок (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации Pydantic."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Ошибка валидации данных",
            "errors": exc.errors()
        },
    )


# Глобальный обработчик всех необработанных исключений (500)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Обработчик всех необработанных исключений."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера"},
    )


# Подключаем роутеры
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])


@app.get("/", summary="Health Check")
def read_root():
    """Проверка доступности сервиса."""
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health", summary="Detailed Health Check")
def detailed_health_check():
    """
    Детальная проверка состояния всех сервисов.
    Возвращает статус каждого компонента системы.
    """
    health_status = {
        "application": "ok",
        "services": {}
    }
    
    # Проверка PostgreSQL
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["services"]["postgresql"] = {
            "status": "ok",
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "database": settings.POSTGRES_DB
        }
    except Exception as e:
        health_status["services"]["postgresql"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Проверка Elasticsearch
    try:
        if es_client and es_client.ping():
            health_status["services"]["elasticsearch"] = {
                "status": "ok",
                "url": settings.ELASTICSEARCH_URL
            }
        else:
            health_status["services"]["elasticsearch"] = {
                "status": "error",
                "error": "Client not initialized"
            }
    except Exception as e:
        health_status["services"]["elasticsearch"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Проверка Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.ping()
        health_status["services"]["redis"] = {
            "status": "ok",
            "url": settings.REDIS_URL
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "error",
            "error": str(e)
        }
    
    return health_status
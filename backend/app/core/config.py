import secrets
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения."""
    APP_NAME: str = "University Knowledge Search"
    APP_VERSION: str = "0.1.0"
    
    # База данных и сервисы
    DATABASE_URL: str = "postgresql://university_user:university_pass@localhost:5432/knowledge_db"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Безопасность JWT
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Бизнес-логика
    MAX_FILE_SIZE_MB: int = 20
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
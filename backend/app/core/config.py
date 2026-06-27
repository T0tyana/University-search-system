import secrets
from pydantic_settings import BaseSettings
from pydantic import computed_field
from urllib.parse import quote_plus

class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения."""
    APP_NAME: str = "University Knowledge Search"
    APP_VERSION: str = "0.1.0"
    
    # PostgreSQL
    POSTGRES_USER: str = "university_user"
    POSTGRES_PASSWORD: str = "university_pass"
    POSTGRES_DB: str = "knowledge_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # Elasticsearch и Redis
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

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Генерирует корректный URL для SQLAlchemy с psycopg v3."""
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        host = self.POSTGRES_HOST
        port = self.POSTGRES_PORT
        db = self.POSTGRES_DB
        # ВАЖНО: используем psycopg v3 вместо psycopg2!
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

    # Pydantic V2 синтаксис - игнорируем лишние переменные из .env
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
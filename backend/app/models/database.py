from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# psycopg v3 использует тот же URL формат, что и psycopg2
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Генератор сессии базы данных для зависимостей FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
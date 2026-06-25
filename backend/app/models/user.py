from sqlalchemy import Column, Integer, String
from app.models.database import Base

class User(Base):
    """Модель пользователя для авторизации."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
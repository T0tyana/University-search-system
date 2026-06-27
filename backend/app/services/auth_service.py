from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
from app.core.config import settings
from app.models.database import get_db
from app.models.user import User
from sqlalchemy.orm import Session

# Используем HTTPBearer вместо OAuth2PasswordBearer для простой авторизации
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля хешу.
    
    Args:
        plain_password: Пароль в открытом виде.
        hashed_password: Хеш пароля из БД.
        
    Returns:
        True, если пароль верен, иначе False.
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    """
    Генерирует хеш пароля с использованием bcrypt.
    
    Args:
        password: Пароль в открытом виде.
        
    Returns:
        Захешированная строка пароля.
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password=pwd_bytes, salt=salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Создает JWT токен доступа.
    
    Args:
        data: Данные для включения в payload токена.
        expires_delta: Время жизни токена. По умолчанию берется из настроек.
        
    Returns:
        Строка JWT токена.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Получает текущего пользователя из JWT токена.
    
    Args:
        credentials: HTTP заголовки с Bearer токеном.
        db: Сессия базы данных.
        
    Returns:
        Объект модели User.
        
    Raises:
        HTTPException: 401 Unauthorized, если токен невалиден или пользователь не найден.
    """
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
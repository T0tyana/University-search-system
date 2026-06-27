from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.models.schemas import RegisterResponse, LoginResponse
from app.services.auth_service import verify_password, get_password_hash, create_access_token
from pydantic import BaseModel

router = APIRouter()


class UserCreate(BaseModel):
    """Модель для регистрации нового пользователя."""
    username: str
    password: str


class UserLogin(BaseModel):
    """Модель для входа пользователя."""
    username: str
    password: str


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Регистрация пользователя",
    responses={
        200: {"description": "Пользователь успешно зарегистрирован"},
        400: {"description": "Имя пользователя уже занято"},
        422: {"description": "Ошибка валидации данных"},
        500: {"description": "Внутренняя ошибка сервера"},
    }
)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрирует нового пользователя в системе.
    
    Args:
        user_data: Данные для регистрации (username, password).
        db: Сессия базы данных.
        
    Returns:
        RegisterResponse: Сообщение об успешной регистрации.
        
    Raises:
        HTTPException: 400 Bad Request, если имя пользователя занято.
        HTTPException: 422 Unprocessable Entity, если данные невалидны.
        HTTPException: 500 Internal Server Error, если произошла ошибка БД.
    """
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = User(
        username=user_data.username, 
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RegisterResponse(msg="User created successfully")


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Авторизация пользователя",
    responses={
        200: {"description": "Успешная авторизация, выдан JWT токен"},
        401: {"description": "Неверный логин или пароль"},
        422: {"description": "Ошибка валидации данных"},
        500: {"description": "Внутренняя ошибка сервера"},
    }
)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Авторизует пользователя и выдает JWT токен.
    
    Args:
        credentials: Данные для входа (username, password).
        db: Сессия базы данных.
        
    Returns:
        LoginResponse: JWT токен и его тип.
        
    Raises:
        HTTPException: 401 Unauthorized, если логин или пароль неверны.
        HTTPException: 422 Unprocessable Entity, если данные невалидны.
        HTTPException: 500 Internal Server Error, если произошла ошибка.
    """
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return LoginResponse(access_token=access_token, token_type="bearer")
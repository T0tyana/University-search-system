from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.services.auth_service import verify_password, get_password_hash, create_access_token
from pydantic import BaseModel

router = APIRouter()

class UserCreate(BaseModel):
    """Модель для регистрации нового пользователя."""
    username: str
    password: str

@router.post("/register", summary="Регистрация пользователя")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрирует нового пользователя в системе.
    
    Args:
        user_data: Данные для регистрации (username, password).
        db: Сессия базы данных.
        
    Returns:
        Сообщение об успешной регистрации.
        
    Raises:
        HTTPException: 400 Bad Request, если имя пользователя занято.
    """
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = User(username=user_data.username, hashed_password=get_password_hash(user_data.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User created successfully"}

@router.post("/login", summary="Авторизация пользователя")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Авторизует пользователя и выдает JWT токен.
    
    Args:
        form_data: Форма входа (username, password).
        db: Сессия базы данных.
        
    Returns:
        access_token и token_type.
        
    Raises:
        HTTPException: 401 Unauthorized, если логин или пароль неверны.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
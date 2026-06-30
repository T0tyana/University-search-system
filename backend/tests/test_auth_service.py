from datetime import timedelta

from jose import jwt

from app.core.config import settings
from app.services.auth_service import (
    create_access_token,
    get_password_hash,
    verify_password,
)

from unittest.mock import MagicMock

from app.services.auth_service import get_current_user

import pytest
from fastapi import HTTPException

from fastapi.security import HTTPAuthorizationCredentials

def test_get_password_hash_returns_string():
    password = "Qa123456!"

    hashed = get_password_hash(password)

    assert isinstance(hashed, str)
    assert hashed != password


def test_verify_password_success():
    password = "Qa123456!"

    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True


def test_verify_password_wrong_password():
    password = "Qa123456!"

    hashed = get_password_hash(password)

    assert verify_password("WrongPassword", hashed) is False


def test_hashes_are_different():
    """
    bcrypt использует salt.
    Поэтому одинаковые пароли должны иметь разные хеши.
    """

    password = "Qa123456!"

    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    assert hash1 != hash2


def test_create_access_token_returns_string():

    token = create_access_token(
        {
            "sub": "qa_user"
        }
    )

    assert isinstance(token, str)


def test_create_access_token_contains_username():

    token = create_access_token(
        {
            "sub": "qa_user"
        }
    )

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )

    assert payload["sub"] == "qa_user"


def test_create_access_token_contains_expiration():

    token = create_access_token(
        {
            "sub": "qa_user"
        },
        expires_delta=timedelta(minutes=5)
    )

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )

    assert "exp" in payload


def test_verify_password_empty_string():

    hashed = get_password_hash("")

    assert verify_password("", hashed)


def test_verify_password_unicode():

    password = "Пароль123"

    hashed = get_password_hash(password)

    assert verify_password(password, hashed)


def test_hash_is_not_empty():

    hashed = get_password_hash("Qa123456!")

    assert len(hashed) > 0
    
def test_verify_password_long_password():
    password = "A" * 1000

    hashed = get_password_hash(password)

    assert verify_password(password, hashed)
    
def test_password_case_sensitive():

    hashed = get_password_hash("Password123")

    assert verify_password("password123", hashed) is False
    
def test_hashes_for_different_passwords():

    hash1 = get_password_hash("Password1")
    hash2 = get_password_hash("Password2")

    assert hash1 != hash2

def test_create_empty_access_token():

    token = create_access_token({})

    assert isinstance(token, str)

def test_password_special_symbols():

    password = "!@#$%^&*()_+"

    hashed = get_password_hash(password)

    assert verify_password(password, hashed)
def test_get_current_user_success():

    token = create_access_token(
        {"sub": "qa_user"},
        expires_delta=timedelta(minutes=5)
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )

    fake_user = MagicMock()
    fake_user.username = "qa_user"

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = fake_user

    user = get_current_user(credentials, db)

    assert user.username == "qa_user"

def test_get_current_user_not_found():

    token = create_access_token({"sub": "unknown"})

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials, db)

    assert exc.value.status_code == 401

def test_get_current_user_invalid_token():

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid_token"
    )

    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials, db)

    assert exc.value.status_code == 401
    
def test_get_current_user_without_subject():

    token = create_access_token({})

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )

    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials, db)

    assert exc.value.status_code == 401
    
def test_get_current_user_expired_token():

    token = create_access_token(
        {"sub": "qa_user"},
        expires_delta=timedelta(seconds=-1)
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )

    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials, db)

    assert exc.value.status_code == 401


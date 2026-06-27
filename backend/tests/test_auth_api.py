from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth import router


app = FastAPI()
app.include_router(router)

client = TestClient(app)


class FakeQuery:

    def __init__(self, user):
        self.user = user

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.user


class FakeDB:

    def __init__(self, user=None):
        self.user = user

    def query(self, model):
        return FakeQuery(self.user)

    def add(self, obj):
        pass

    def commit(self):
        pass

    def refresh(self, obj):
        pass


@pytest.fixture
def override_db():

    def _override(user=None):

        def get_db():
            yield FakeDB(user)

        return get_db

    return _override


def test_register_success(override_db):

    from app.models.database import get_db

    app.dependency_overrides[get_db] = override_db()

    response = client.post(
        "/register",
        json={
            "username": "tester",
            "password": "Password123"
        }
    )

    assert response.status_code == 200
    assert response.json()["msg"] == "User created successfully"

    app.dependency_overrides.clear()


def test_register_existing_user(override_db):

    from app.models.database import get_db

    fake_user = MagicMock()

    app.dependency_overrides[get_db] = override_db(fake_user)

    response = client.post(
        "/register",
        json={
            "username": "tester",
            "password": "Password123"
        }
    )

    assert response.status_code == 400

    app.dependency_overrides.clear()


def test_login_success(override_db):

    from app.models.database import get_db

    fake_user = MagicMock()
    fake_user.username = "tester"

    with patch(
        "app.api.v1.auth.verify_password",
        return_value=True
    ):

        with patch(
            "app.api.v1.auth.create_access_token",
            return_value="jwt_token"
        ):

            app.dependency_overrides[get_db] = override_db(fake_user)

            response = client.post(
                "/login",
                json={
                    "username": "tester",
                    "password": "Password123"
                }
            )

            assert response.status_code == 200
            assert response.json()["access_token"] == "jwt_token"

            app.dependency_overrides.clear()


def test_login_wrong_password(override_db):

    from app.models.database import get_db

    fake_user = MagicMock()

    with patch(
        "app.api.v1.auth.verify_password",
        return_value=False
    ):

        app.dependency_overrides[get_db] = override_db(fake_user)

        response = client.post(
            "/login",
            json={
                "username": "tester",
                "password": "wrong"
            }
        )

        assert response.status_code == 401

        app.dependency_overrides.clear()


def test_login_user_not_found(override_db):

    from app.models.database import get_db

    app.dependency_overrides[get_db] = override_db()

    response = client.post(
        "/login",
        json={
            "username": "tester",
            "password": "Password123"
        }
    )

    assert response.status_code == 401

    app.dependency_overrides.clear()


def test_register_validation_error():

    response = client.post(
        "/register",
        json={
            "username": ""
        }
    )

    assert response.status_code == 422


def test_login_validation_error():

    response = client.post(
        "/login",
        json={}
    )

    assert response.status_code == 422
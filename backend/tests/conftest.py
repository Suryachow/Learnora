"""Test configuration.

The environment is prepared *before* the app is imported so the app picks up a
throwaway SQLite database and a test-only JWT secret.
"""

import os
import tempfile
from pathlib import Path

TEST_DB_PATH = Path(tempfile.gettempdir()) / "skillearn_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["JWT_SECRET"] = "test-secret-not-for-production-0123456789abcdef"
os.environ["ENV"] = "test"

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, User  # noqa: E402
from app.services.security import hash_password  # noqa: E402

PASSWORD = "Passw0rd1"
API = "/api/v1"


@pytest.fixture(scope="session", autouse=True)
def _database() -> Iterator[None]:
    TEST_DB_PATH.unlink(missing_ok=True)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    """Every test starts with an empty database."""
    yield
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


@pytest.fixture
def register(client: TestClient):
    def _register(
        name: str = "Test Learner",
        email: str = "learner@example.com",
        password: str = PASSWORD,
    ) -> dict:
        response = client.post(
            f"{API}/auth/register",
            json={"name": name, "email": email, "password": password},
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _register


@pytest.fixture
def auth_headers(register):
    def _auth_headers(**kwargs) -> dict[str, str]:
        payload = register(**kwargs)
        return {"Authorization": f"Bearer {payload['access_token']}"}

    return _auth_headers


@pytest.fixture
def make_admin(db: Session):
    def _make_admin(
        name: str = "Admin",
        email: str = "admin@example.com",
        password: str = PASSWORD,
        subscribed: bool = False,
    ) -> User:
        from datetime import timedelta

        from app.utils import utcnow

        admin = User(
            name=name,
            email=email.lower(),
            password_hash=hash_password(password),
            is_admin=True,
            subscribed_until=utcnow() + timedelta(days=30) if subscribed else None,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    return _make_admin


@pytest.fixture
def login(client: TestClient):
    def _login(email: str = "learner@example.com", password: str = PASSWORD) -> str:
        response = client.post(f"{API}/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return response.json()["access_token"]

    return _login

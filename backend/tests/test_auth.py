"""Registration, login and the /me endpoint."""

from sqlalchemy import select

from app.models import User

API = "/api/v1"


def test_register_returns_token_and_profile(client):
    response = client.post(
        f"{API}/auth/register",
        json={"name": "Asha Rao", "email": "Asha@Example.com", "password": "Passw0rd1"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["name"] == "Asha Rao"
    assert body["user"]["email"] == "asha@example.com"  # normalised to lower case
    assert body["user"]["is_admin"] is False
    assert body["user"]["has_active_subscription"] is False
    assert "password" not in body["user"]


def test_password_is_stored_hashed(client, db):
    client.post(
        f"{API}/auth/register",
        json={"name": "Asha Rao", "email": "asha@example.com", "password": "Passw0rd1"},
    )

    user = db.scalar(select(User).where(User.email == "asha@example.com"))
    assert user is not None
    assert user.password_hash != "Passw0rd1"
    assert user.password_hash.startswith("$argon2")


def test_duplicate_email_is_rejected(client, register):
    register(email="taken@example.com")

    response = client.post(
        f"{API}/auth/register",
        json={"name": "Someone Else", "email": "taken@example.com", "password": "Passw0rd1"},
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_weak_password_returns_readable_error(client):
    response = client.post(
        f"{API}/auth/register",
        json={"name": "Asha Rao", "email": "asha@example.com", "password": "passwordonly"},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, str)
    assert "number" in detail


def test_login_with_correct_credentials(client, register):
    register(email="asha@example.com")
    response = client.post(
        f"{API}/auth/login", json={"email": "ASHA@example.com", "password": "Passw0rd1"}
    )

    assert response.status_code == 200, response.text
    assert response.json()["user"]["email"] == "asha@example.com"


def test_login_with_wrong_password_is_401(client, register):
    register(email="asha@example.com")
    response = client.post(
        f"{API}/auth/login", json={"email": "asha@example.com", "password": "WrongPass123"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "That email and password combination is not correct."


def test_login_with_unknown_email_is_401(client):
    response = client.post(
        f"{API}/auth/login", json={"email": "nobody@example.com", "password": "Passw0rd1"}
    )
    assert response.status_code == 401


def test_me_requires_a_token(client):
    response = client.get(f"{API}/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Please log in to continue."


def test_me_rejects_a_garbage_token(client):
    response = client.get(f"{API}/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_returns_the_signed_in_user(client, auth_headers):
    headers = auth_headers(name="Asha Rao", email="asha@example.com")

    response = client.get(f"{API}/me", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["email"] == "asha@example.com"
    assert body["name"] == "Asha Rao"
    assert body["subscribed_until"] is None


def test_health_endpoint(client):
    response = client.get(f"{API}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

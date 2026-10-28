"""Server-side access gates: administrator rights and subscription gating.

These call the dependencies directly, so the rules are covered even before the
admin and wallet routers exist.
"""

from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.deps import get_current_admin, require_active_subscription
from app.models import User
from app.utils import utcnow

API = "/api/v1"


def _user(*, is_admin: bool, subscribed_until=None) -> User:
    user = User(
        id=1,
        name="Someone",
        email="someone@example.com",
        password_hash="not-used-here",
        is_admin=is_admin,
        subscribed_until=subscribed_until,
    )
    return user


def test_admin_gate_rejects_a_learner():
    with pytest.raises(HTTPException) as raised:
        get_current_admin(_user(is_admin=False))

    assert raised.value.status_code == 403
    assert "administrator" in raised.value.detail


def test_admin_gate_allows_an_admin():
    admin = _user(is_admin=True)
    assert get_current_admin(admin) is admin


def test_subscription_gate_rejects_a_user_without_subscription():
    with pytest.raises(HTTPException) as raised:
        require_active_subscription(_user(is_admin=False))

    assert raised.value.status_code == 402
    assert "subscription" in raised.value.detail.lower()


def test_subscription_gate_rejects_an_expired_subscription():
    with pytest.raises(HTTPException) as raised:
        require_active_subscription(_user(is_admin=False, subscribed_until=utcnow()))

    assert raised.value.status_code == 402


def test_subscription_gate_allows_an_active_subscription():
    user = _user(is_admin=False, subscribed_until=utcnow() + timedelta(days=1))
    assert require_active_subscription(user) is user


def test_admin_account_created_directly_can_reach_admin_routes(client, make_admin, login):
    """An admin row in the database is enough - the UI is not the security boundary."""
    make_admin(email="boss@example.com")
    token = login(email="boss@example.com")

    response = client.get(f"{API}/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["is_admin"] is True

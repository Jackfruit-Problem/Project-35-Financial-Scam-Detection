"""Auth and RBAC. SRS 6.3, REQ-23."""
from app.models.enums import Role

REGISTRATION = {
    "full_name": "Asha Rao",
    "email": "asha@example.com",
    "phone": "9876543210",
    "password": "correct-horse-1",
}


def test_register_creates_victim(client):
    response = client.post("/api/v1/auth/register", json=REGISTRATION)
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == Role.VICTIM
    assert "password" not in body and "hashed_password" not in body


def test_registration_rejects_self_assigned_role(client):
    """Passing a role must not elevate the account -- it is simply ignored."""
    response = client.post(
        "/api/v1/auth/register", json={**REGISTRATION, "role": "admin"}
    )
    assert response.status_code == 201
    assert response.json()["role"] == Role.VICTIM


def test_duplicate_email_rejected(client):
    client.post("/api/v1/auth/register", json=REGISTRATION)
    response = client.post("/api/v1/auth/register", json=REGISTRATION)
    assert response.status_code == 409


def test_login_and_me(client):
    client.post("/api/v1/auth/register", json=REGISTRATION)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": REGISTRATION["email"], "password": REGISTRATION["password"]},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == REGISTRATION["email"]


def test_wrong_password_and_unknown_email_are_indistinguishable(client):
    """Identical response for both, so the endpoint cannot enumerate accounts."""
    client.post("/api/v1/auth/register", json=REGISTRATION)

    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": REGISTRATION["email"], "password": "not-the-password"},
    )
    unknown_email = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "not-the-password"},
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_no_token_is_rejected(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_garbage_token_is_rejected(client):
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert response.status_code == 401


def test_deactivated_account_loses_access_immediately(
    client, make_user, auth_headers, db_session
):
    """REQ-23: deactivation must bite while the token is still unexpired."""
    user = make_user("temp@example.com")
    headers = auth_headers("temp@example.com")
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

    user.is_active = False
    db_session.commit()

    assert client.get("/api/v1/auth/me", headers=headers).status_code == 403

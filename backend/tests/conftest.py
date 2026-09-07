"""Test fixtures.

Each test gets a fresh in-memory database. StaticPool keeps every connection
pointed at the same in-memory instance -- without it SQLite hands each
connection its own empty database and the tables vanish between calls.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import Role
from app.models.user import User


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session: Session):
    """Create a user of any role directly, bypassing the victim-only signup."""

    def _make(email: str, role: Role = Role.VICTIM, password: str = "password123") -> User:
        user = User(
            full_name=email.split("@")[0].title(),
            email=email,
            hashed_password=hash_password(password),
            role=role,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture
def auth_headers(client):
    """Log a user in and return the Authorization header for them."""

    def _headers(email: str, password: str = "password123") -> dict[str, str]:
        response = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _headers


# A description that trips several detection signals at once, so it reliably
# lands in the HIGH band without depending on any single rule's weight.
HIGH_RISK_TEXT = (
    "URGENT: your account will be blocked immediately. Share your OTP and PAN card "
    "to claim your guaranteed returns prize at http://bit.ly/x9fraud"
)

LOW_RISK_TEXT = "I bought a book online last Tuesday and the delivery was late."

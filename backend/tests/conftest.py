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
from app.services import ml_client

# Captured before anything patches it, so tests of the client itself can put
# the real implementation back. Without this, the autouse fixture below
# replaces the function under test and "returns None" passes vacuously.
_REAL_ML_PREDICT = ml_client.predict


@pytest.fixture
def real_ml_client(monkeypatch):
    """Restore the genuine client, for tests that exercise its own defences."""
    monkeypatch.setattr(ml_client, "predict", _REAL_ML_PREDICT)
    return ml_client


@pytest.fixture(autouse=True)
def no_model_service(monkeypatch):
    """Force every test onto the rule-based fallback by default.

    Without this the suite would score differently depending on whether the
    model service happened to be running on this machine at the time -- passing
    locally and failing in CI, or worse, the reverse. Tests that want the model
    path use the fake_model fixture to opt in explicitly.
    """
    monkeypatch.setattr(ml_client, "predict", lambda text: None)


@pytest.fixture
def fake_model(monkeypatch):
    """Stand in for the model service with a fixed answer.

    A fake rather than the real service: these tests are about how the
    application behaves given a model response, not about how good the model
    is. Model quality is measured in ml/tests.
    """

    def _install(risk_score: int, reasons: list[str] | None = None,
                 version: str = "tfidf-logreg-v1"):
        def fake_predict(text: str):
            return {
                "risk_score": risk_score,
                "reasons": reasons if reasons is not None else ["the wording \"test\""],
                "model_version": version,
                "probability": risk_score / 100,
            }

        monkeypatch.setattr(ml_client, "predict", fake_predict)

    return _install


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

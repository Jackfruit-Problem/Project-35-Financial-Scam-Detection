"""Application configuration, loaded from environment with sane local defaults."""
import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Named rather than inlined so the production check can recognise it. Anyone
# holding this value can mint a valid token for any account, and can decrypt
# every evidence file, since the file key is derived from it.
DEV_SECRET_KEY = "dev-only-change-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "FSDIRAS"
    API_V1_PREFIX: str = "/api/v1"

    # Postgres in Docker; SQLite fallback so the suite runs before Docker is installed.
    DATABASE_URL: str = "sqlite:///./fsdiras.db"

    # Set FSDIRAS_ENV=production on a real deployment. It turns the checks in
    # verify_production_safety() from advice into a refusal to start.
    FSDIRAS_ENV: str = "development"

    SECRET_KEY: str = DEV_SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    ALGORITHM: str = "HS256"

    # REQ-6.3 has no brute-force clause, but an unthrottled login is one short
    # script away from every weak password in the system. Generous enough that
    # no honest user meets it, including during a demonstration.
    LOGIN_MAX_FAILURES: int = 10
    LOGIN_LOCKOUT_SECONDS: int = 300

    # REQ-3: configurable risk bands.
    RISK_MEDIUM_THRESHOLD: int = 40
    RISK_HIGH_THRESHOLD: int = 70

    ML_SERVICE_URL: str = "http://127.0.0.1:8001"
    # Well inside the 5-second budget in REQ-2, so a slow model cannot make the
    # application miss its own performance requirement.
    ML_TIMEOUT_SECONDS: float = 2.5

    # Local encrypted evidence store; swapped for S3 or equivalent on deploy.
    EVIDENCE_DIR: str = "./evidence_store"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def verify_production_safety(current: Settings | None = None) -> list[str]:
    """Report anything that must not be true on a real deployment.

    Returns the problems rather than raising, so the caller decides: the app
    refuses to start when FSDIRAS_ENV=production, and warns loudly otherwise.
    Failing outright in development would mean nobody could run the project
    without first inventing a secret, which is how a safety check gets deleted.
    """
    current = current or settings
    problems: list[str] = []

    if current.SECRET_KEY == DEV_SECRET_KEY:
        problems.append(
            "SECRET_KEY is still the development default. Tokens can be forged "
            "and stored evidence can be decrypted by anyone with this source."
        )
    elif len(current.SECRET_KEY) < 32:
        problems.append(
            f"SECRET_KEY is only {len(current.SECRET_KEY)} characters; use at "
            "least 32 random ones."
        )

    if current.DATABASE_URL.startswith("sqlite"):
        problems.append(
            "DATABASE_URL points at SQLite. SRS 2.4 specifies PostgreSQL, which "
            "the test suite is run against in CI."
        )

    return problems


def enforce_production_safety() -> None:
    """Called at startup. Refuses to run an unsafe production configuration."""
    problems = verify_production_safety()
    if not problems:
        return

    if settings.FSDIRAS_ENV.lower() == "production":
        bullets = "\n  - ".join(problems)
        raise RuntimeError(
            f"Refusing to start in production with an unsafe configuration:\n  - {bullets}"
        )

    for problem in problems:
        logger.warning("development configuration: %s", problem)

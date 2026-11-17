"""FSDIRAS API entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importing the model package registers every table on Base.metadata.
from app import models  # noqa: F401
from app.api.v1 import admin, auth, cases, education, evidence, recovery, reports
from app.core.config import enforce_production_safety, settings
from app.db.migrations import run_migrations


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Refuses to start on an unsafe production configuration; warns in
    # development. Runs before the migrations, so a misconfigured deployment
    # stops before it touches the database at all.
    enforce_production_safety()

    # Alembic, not create_all: create_all cannot alter an existing table, so it
    # is not a migration path. See app/db/migrations.py.
    run_migrations()
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    description=(
        "Financial Scam Detection, Investigation, and Recovery Assistance System. "
        "Project ID 35, UE24CS341A."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)
app.include_router(cases.router, prefix=settings.API_V1_PREFIX)
app.include_router(evidence.router, prefix=settings.API_V1_PREFIX)
app.include_router(recovery.router, prefix=settings.API_V1_PREFIX)
app.include_router(education.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.PROJECT_NAME}

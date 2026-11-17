"""Bring the database up to the latest schema revision at start-up.

This replaces the interim `Base.metadata.create_all()`. create_all can only
create tables that do not exist yet; it can never alter one, so it silently
does nothing when a model changes and the database quietly falls behind the
code. Alembic applies an ordered list of revisions instead, and records which
ones have run.

Paths are resolved from this file's own location rather than the current
working directory, because the project has already been bitten once by
cwd-relative paths (evidence files were readable only when uvicorn happened to
be started from `backend/`).
"""
from pathlib import Path

from sqlalchemy import inspect

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from app.db.session import engine

# app/db/migrations.py -> app/db -> app -> backend
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def alembic_config() -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return cfg


def current_revision() -> str | None:
    """The revision this database says it is at, or None if it has never run."""
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def run_migrations() -> None:
    """Upgrade the database to head, adopting a pre-migration database if needed."""
    cfg = alembic_config()
    tables = set(inspect(engine).get_table_names()) - {"alembic_version"}

    if tables and current_revision() is None:
        # The database has application tables but no recorded revision. Two ways
        # to get here: it was built by the old create_all path, or a previous
        # migration run died part-way and left the version table empty. Either
        # way the tables are already there, so stamp rather than re-create.
        #
        # Testing for the *revision* and not merely for the alembic_version
        # table matters: a half-finished run leaves that table created but
        # empty, and a presence check would wave it through to an upgrade that
        # then fails on the first CREATE TABLE.
        #
        # Stamp the base, not head, so any later revision still gets applied by
        # the upgrade below.
        base = ScriptDirectory.from_config(cfg).get_bases()[0]
        command.stamp(cfg, base)

    command.upgrade(cfg, "head")

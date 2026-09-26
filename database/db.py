"""Database connection helper — SQLite locally, Postgres in production.

Local dev uses the SQLite file below by default. For a persistent deployment
(e.g. Streamlit Cloud, where the filesystem resets on every redeploy), set
DATABASE_URL in that app's Secrets to a Postgres connection string:
  postgresql://user:pass@host:5432/dbname
Nothing else needs to change — run_query/run_write/insert_returning_id all
work identically against either engine.
"""
from pathlib import Path
import os
import sqlite3
import streamlit as st
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import NullPool

from utils.fiscal_calendar import current_fiscal_year

_HERE = Path(__file__).parent
DB_PATH = _HERE / "cel_mel.db"
SCHEMA_PATH = _HERE / "schema.sql"
SCHEMA_PATH_POSTGRES = _HERE / "schema_postgres.sql"


def _database_url() -> str:
    try:
        secret_url = st.secrets.get("DATABASE_URL")
    except Exception:
        secret_url = None
    url = secret_url or os.environ.get("DATABASE_URL") or f"sqlite:///{DB_PATH}"
    # Force the psycopg (v3) driver explicitly rather than relying on
    # SQLAlchemy's default dialect choice for a bare "postgresql://" URL.
    # psycopg2 has no prebuilt wheel on newer Python versions (e.g. the
    # 3.14 Streamlit Cloud now runs), which surfaced as a
    # ModuleNotFoundError at create_engine() on the live site.
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


DATABASE_URL = _database_url()
IS_POSTGRES = DATABASE_URL.startswith("postgresql")


@st.cache_resource
def get_engine():
    """Return a cached SQLAlchemy engine (one per Streamlit process)."""
    if IS_POSTGRES:
        # NullPool: every engine.begin()/engine.connect() call opens a fresh
        # TCP connection and closes it on exit.  No connection reuse means no
        # prepared-statement lifecycle collisions from Supabase's PgBouncer
        # (which operates in transaction-pooling mode and may hand different
        # backend sessions to consecutive calls, making session-scoped
        # prepared statements invisible across those calls).
        engine = create_engine(DATABASE_URL, poolclass=NullPool)

        # psycopg3 semantics for prepare_threshold:
        #   None → never auto-prepare  (what we want)
        #   0    → prepare on every first execution
        #   N    → prepare after N executions (default 5)
        # SQLAlchemy strips None from connect_args before passing to the
        # driver, so we cannot pass it that way.  A "connect" event listener
        # sets the attribute directly on the psycopg3 Connection object after
        # creation — this is the only reliable path.
        @event.listens_for(engine, "connect")
        def _disable_auto_prepare(dbapi_conn, _):
            dbapi_conn.prepare_threshold = None

        return engine

    return create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )


def get_connection():
    """Return a raw sqlite3 connection for scripts that don't need SQLAlchemy.
    SQLite only — under Postgres, use get_engine()/run_write() instead."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create all tables and apply migrations — exactly once per process.

    Every page calls this on every load, for every concurrent user session.
    Postgres DDL (ALTER TABLE) takes a strong lock, so if this ran fresh each
    time, multiple sessions hitting it at once (e.g. right after a reboot)
    could deadlock against each other. st.cache_resource makes the actual
    work below run once and caches the result; concurrent first-callers
    block on Streamlit's cache lock rather than racing Postgres locks.
    """
    _run_migrations()


@st.cache_resource
def _run_migrations() -> bool:
    if IS_POSTGRES:
        # Strip '--' line comments before splitting on ';' — a semicolon
        # inside a comment (e.g. "-- one row; not two") would otherwise
        # produce a bogus empty/partial statement.
        lines = (ln.split("--", 1)[0] for ln in SCHEMA_PATH_POSTGRES.read_text().splitlines())
        schema = "\n".join(lines)
        engine = get_engine()
        with engine.begin() as conn:
            # Belt-and-braces against the same deadlock across separate
            # processes (e.g. old + new process briefly overlapping during a
            # rolling redeploy) — pg_advisory_xact_lock serializes any other
            # session trying to migrate at the same time and auto-releases
            # at transaction end, so it can't leak on an exception.
            conn.execute(text("SELECT pg_advisory_xact_lock(823771)"))
            for stmt in schema.split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))
            # Migrate existing tables that predate these columns.
            for stmt in (
                "ALTER TABLE raw_data_analysis ADD COLUMN IF NOT EXISTS reporting_year INTEGER",
                "ALTER TABLE data_collection_plan ADD COLUMN IF NOT EXISTS last_collected_date TEXT",
            ):
                conn.execute(text(stmt))
            # Backfill rows written before reporting_year existed, so every
            # query can filter on it directly without a NULL special case.
            conn.execute(
                text("UPDATE raw_data_analysis SET reporting_year=:yr WHERE reporting_year IS NULL"),
                {"yr": current_fiscal_year()},
            )
        return True

    schema = SCHEMA_PATH.read_text()
    conn = get_connection()
    conn.executescript(schema)
    # Migrate existing databases that predate these columns.
    for stmt in (
        "ALTER TABLE toc_nodes ADD COLUMN source_verified BOOLEAN DEFAULT 1",
        "ALTER TABLE toc_nodes ADD COLUMN source_note TEXT",
        "ALTER TABLE raw_data_analysis ADD COLUMN reporting_year INTEGER",
        "ALTER TABLE data_collection_plan ADD COLUMN last_collected_date TEXT",
    ):
        try:
            conn.execute(stmt)
        except Exception:
            pass  # column already exists
    # Backfill rows written before reporting_year existed, so every query
    # can filter on it directly without a NULL special case.
    conn.execute(
        "UPDATE raw_data_analysis SET reporting_year=? WHERE reporting_year IS NULL",
        (current_fiscal_year(),),
    )
    conn.commit()
    conn.close()
    return True


def run_query(sql: str, params: dict | None = None):
    """Execute a SELECT and return rows as a list of dicts."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        keys = result.keys()
        return [dict(zip(keys, row)) for row in result.fetchall()]


def run_write(sql: str, params: dict | None = None):
    """Execute an INSERT / UPDATE / DELETE inside a transaction."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})


def insert_returning_id(sql: str, params: dict | None = None) -> int:
    """Execute an INSERT and return the new row's primary key.

    SQLite: reads the cursor's lastrowid directly.
    Postgres has no such cursor attribute, since IDENTITY columns are
    sequence-backed rather than rowid-backed — lastval() returns the most
    recent value drawn from any sequence on this same connection/transaction,
    which is exactly what the just-executed INSERT produced.
    """
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text(sql), params or {})
        if IS_POSTGRES:
            return conn.execute(text("SELECT lastval()")).scalar()
        return result.lastrowid

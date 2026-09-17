"""SQLite connection helper.

To migrate to Postgres: change DATABASE_URL only — nothing else needs to move.
  SQLite:   sqlite:///./database/cel_mel.db
  Postgres: postgresql://user:pass@host:5432/cel_mel
"""
from pathlib import Path
import sqlite3
import streamlit as st
from sqlalchemy import create_engine, text

_HERE = Path(__file__).parent
DB_PATH = _HERE / "cel_mel.db"
SCHEMA_PATH = _HERE / "schema.sql"

DATABASE_URL = f"sqlite:///{DB_PATH}"


@st.cache_resource
def get_engine():
    """Return a cached SQLAlchemy engine (one per Streamlit process)."""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    return engine


def get_connection():
    """Return a raw sqlite3 connection for scripts that don't need SQLAlchemy."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create all tables from schema.sql if they do not yet exist."""
    schema = SCHEMA_PATH.read_text()
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()


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
    """Execute an INSERT and return the new row's lastrowid."""
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text(sql), params or {})
        return result.lastrowid

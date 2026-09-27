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
                "ALTER TABLE raw_data_analysis ADD COLUMN IF NOT EXISTS progression_stage TEXT",
                "ALTER TABLE raw_data_analysis ADD COLUMN IF NOT EXISTS pillar TEXT",
                "ALTER TABLE raw_data_analysis ADD COLUMN IF NOT EXISTS dqa_stage TEXT",
                "ALTER TABLE raw_data_analysis ADD COLUMN IF NOT EXISTS disaggregation TEXT",
            ):
                conn.execute(text(stmt))
            # Backfill rows written before reporting_year existed, so every
            # query can filter on it directly without a NULL special case.
            conn.execute(
                text("UPDATE raw_data_analysis SET reporting_year=:yr WHERE reporting_year IS NULL"),
                {"yr": current_fiscal_year()},
            )
            # Backfill progression_stage, pillar, dqa_stage for rows that
            # predate these columns (joined via logframe_rows.indicator_code).
            for _code, _ps, _pl in [
                ("LoP.1",    "D&F",  "Programme-wide"),
                ("PI.1",     "WEO",  "Capacity Building & Inclusion"),
                ("PI.3",     "WEO",  "Capacity Building & Inclusion"),
                ("PI.9",     "WEO",  "Capacity Building & Inclusion"),
                ("PI.11",    "WEO",  "Capacity Building & Inclusion"),
                ("PI.12",    "WEO",  "Capacity Building & Inclusion"),
                ("PI.13",    "WEO",  "Capacity Building & Inclusion"),
                ("PI.17",    "WEO",  "Capacity Building & Inclusion"),
                ("PI.18",    "WEO",  "Capacity Building & Inclusion"),
                ("PI.19",    "WEO",  "Capacity Building & Inclusion"),
                ("PI.20",    "WEO",  "Capacity Building & Inclusion"),
                ("PI.22",    "WEO",  "Capacity Building & Inclusion"),
                ("PI.23",    "WEO",  "Capacity Building & Inclusion"),
                ("PIV.5",    "WEO",  "Ecosystem Strengthening"),
                ("PII.R5",   "YIW",  "Production Expansion & Productivity"),
                ("PIII.R1",  "YIW",  "Value Addition & Market Systems"),
                ("PII.R6",   "D&F",  "Production Expansion & Productivity"),
                ("PII.R7",   "D&F",  "Production Expansion & Productivity"),
                ("PIII.R2",  "D&F",  "Value Addition & Market Systems"),
                ("PIII.R3",  "D&F",  "Value Addition & Market Systems"),
                ("PIII.6",   "WEO",  "Value Addition & Market Systems"),
            ]:
                conn.execute(text("""
                    UPDATE raw_data_analysis rda
                    SET    progression_stage = :ps,
                           pillar             = :pl,
                           dqa_stage          = 'Raw'
                    FROM   logframe_rows lr
                    WHERE  rda.logframe_row_id  = lr.id
                      AND  lr.indicator_code    = :code
                      AND  rda.progression_stage IS NULL
                """), {"ps": _ps, "pl": _pl, "code": _code})
            # Correct data_collection_plan dates to SAWA Jul 2026–Jun 2030
            # fiscal calendar.  Old seed had Feb/May 2026 (before programme
            # start); keyed on stakeholder+frequency which is unique per row.
            for _stakeholder, _freq, _month, _year in [
                ("PWD participants",                      "Once",       8, 2026),
                ("All programme participants",            "Quarterly",  9, 2026),
                ("Non-continuers and dropouts",           "Quarterly",  9, 2026),
                ("Production enterprises (fishpond operators)", "Quarterly", 9, 2026),
                ("Young women participants",              "Bi-annual", 11, 2026),
                ("Enterprises and value chain actors",   "Bi-annual", 11, 2026),
                ("Individual participants",               "Bi-annual", 11, 2026),
                ("Supported enterprises",                "Annual",     6, 2027),
                ("Programme participants (all)",          "Annual",     6, 2027),
                ("SAWA-supported enterprises",           "Annual",     6, 2027),
                ("Programme staff and CEL management",   "Annual",     6, 2027),
            ]:
                conn.execute(text("""
                    UPDATE data_collection_plan
                    SET collection_month = :m, collection_year = :y
                    WHERE stakeholder = :s AND frequency = :f
                      AND (collection_month <> :m OR collection_year <> :y)
                """), {"s": _stakeholder, "f": _freq, "m": _month, "y": _year})
            # One-time cleanup: retire old partner names and their cascaded
            # partner_targets (left over from pre-Sep-2026-deck seed versions
            # that were never purged, causing _needs_seed to fire on every load
            # and concurrent reseeds to produce duplicate partner_target rows).
            # Rename Aglow Aqua to its correct operating name before the
            # retired-name purge so it survives the subsequent DELETE pass.
            conn.execute(text("""
                UPDATE partners SET name = 'Aglow Farms'
                WHERE name = 'Aglow Aqua'
            """))
            # Also update any partner_targets source_doc references.
            conn.execute(text("""
                UPDATE partner_targets
                SET source_doc = REPLACE(source_doc, 'Aglow Aqua', 'Aglow Farms')
                WHERE source_doc LIKE '%Aglow Aqua%'
            """))
            for _retired in (
                "Yedent/Naple Betta", "AFRIGEM Global LBG", "R&B Farms",
            ):
                conn.execute(
                    text("DELETE FROM partners WHERE name = :n"), {"n": _retired}
                )
            # Dedup any surviving partner_targets rows (keep lowest id per
            # logical key) that may have been double-inserted during the
            # concurrent-reseed window.
            conn.execute(text("""
                DELETE FROM partner_targets a
                USING partner_targets b
                WHERE a.id > b.id
                  AND a.project_id = b.project_id
                  AND a.level = b.level
                  AND a.metric_label = b.metric_label
                  AND COALESCE(a.partner_id, -1) = COALESCE(b.partner_id, -1)
                  AND COALESCE(a.time_basis, '') = COALESCE(b.time_basis, '')
            """))
            # Remove decision_reports/actions whose logframe_row_id no longer
            # exists (left by a concurrent reseed where one process deleted
            # logframe_rows that another process had used for its FK inserts).
            conn.execute(text("""
                DELETE FROM decision_actions
                WHERE report_id IN (
                    SELECT id FROM decision_reports
                    WHERE logframe_row_id IS NOT NULL
                      AND logframe_row_id NOT IN (SELECT id FROM logframe_rows)
                )
            """))
            conn.execute(text("""
                DELETE FROM decision_reports
                WHERE logframe_row_id IS NOT NULL
                  AND logframe_row_id NOT IN (SELECT id FROM logframe_rows)
            """))
            # Insert the 6 AIL cross-cutting review protocols added in Sep 2026.
            # NOT EXISTS guard makes every INSERT idempotent across redeploys.
            for _dt, _freq, _nsd in [
                ("Safeguarding (SG)",                          "Quarterly", "2026-10-07"),
                ("Gender & Social Inclusion (GYSI)",           "Quarterly", "2026-10-07"),
                ("Climate & Environmental Sustainability (CES)", "Quarterly", "2026-10-07"),
                ("Financial Inclusion (FI)",                   "Quarterly", "2026-10-07"),
                ("Voice & Agency (VA)",                        "Bi-annual", "2026-11-01"),
                ("Communications & Visibility (CV)",           "Quarterly", "2026-10-07"),
            ]:
                conn.execute(text("""
                    INSERT INTO review_protocols
                           (project_id, data_type, review_frequency, next_scheduled_date)
                    SELECT pr.project_id, :dt, :freq, :nsd
                    FROM   projects pr
                    WHERE  pr.name = 'SAWA'
                      AND NOT EXISTS (
                          SELECT 1 FROM review_protocols rp2
                          WHERE  rp2.project_id = pr.project_id
                            AND  rp2.data_type   = :dt
                      )
                """), {"dt": _dt, "freq": _freq, "nsd": _nsd})
            # Remove the TBC placeholder row that was never confirmed.
            conn.execute(text("""
                DELETE FROM partner_targets
                WHERE metric_label = 'Women mentored (peer circles)'
                  AND target_value  = 'TBC'
            """))
            # Correct Year 1 target: ~2,000 was the LoP figure; Year 1 is 500.
            conn.execute(text("""
                UPDATE partner_targets
                SET target_value = '500'
                WHERE metric_label = 'Women in coaching & mentoring'
                  AND time_basis = 'Year 1'
                  AND target_value <> '500'
            """))
            # Rename Level 2 Year 1 metric labels and units to match revised workplan.
            conn.execute(text("""
                UPDATE partner_targets
                SET metric_label = 'Women in coaching & mentorship (gender, financial and digital literacy)'
                WHERE metric_label = 'Women in coaching & mentoring'
                  AND level = 2 AND time_basis = 'Year 1'
            """))
            conn.execute(text("""
                UPDATE partner_targets
                SET metric_label = 'WAN forum engagements (awareness campaigns/road shows, institutionalize occupational health standards)',
                    unit         = 'engagements, campaigns/roadshows, sites/partners covered'
                WHERE metric_label IN (
                        'WAN forum engagements',
                        'WAN forum engagements (awareness campaigns/road shows, institutionalize occupational health standards)'
                      )
                  AND level = 2 AND time_basis = 'Year 1'
                  AND unit <> 'engagements, campaigns/roadshows, sites/partners covered'
            """))
            conn.execute(text("""
                UPDATE partner_targets
                SET metric_label = 'Women-led cooperatives/clusters strengthened (focal persons on GALS & EMAP)',
                    unit         = 'cooperatives/clusters, focal persons'
                WHERE metric_label IN ('Women-led groups strengthened',
                                       'Women-led cooperatives/clusters strengthened (focal persons on GALS & EMAP)')
                  AND level = 2 AND time_basis = 'Year 1'
                  AND unit <> 'cooperatives/clusters, focal persons'
            """))
            # Insert new Level 1 Year 1 partner targets from the Sep 2026 partner
            # implementation decks (cluster sites, communities, districts,
            # anchor operators, FC & CSIR Year 1 targets).  NOT EXISTS guard
            # makes every INSERT idempotent across redeploys.
            for _pname, _label, _val, _unit, _basis, _doc in [
                ("Naple Betta",          "D&F jobs",                     "1,284",   "jobs",         "Year 1", "Naple Betta SAWA Year 1 Implementation Plan, Sep 2026"),
                ("Naple Betta",          "Participants in value addition","575",     "participants", "Year 1", "Naple Betta SAWA Year 1 Implementation Plan, Sep 2026"),
                ("Naple Betta",          "Women-led grill outlets",       "13",      "outlets",      "Year 1", "Naple Betta SAWA Year 1 Implementation Plan, Sep 2026"),
                ("Naple Betta",          "Value-added fish trade",        "110",     "MT",           "Year 1", "Naple Betta SAWA Year 1 Implementation Plan, Sep 2026"),
                ("Naple Betta",          "Value-added revenue",           "841,500", "USD",          "Year 1", "Naple Betta SAWA Year 1 Implementation Plan, Sep 2026"),
                ("TechnoServe",          "Young women reached",   "320",    "beneficiaries", "Year 1", "TechnoServe SAWA Year 1 Implementation Plan, Sep 2026"),
                ("TechnoServe",          "PWD reached",           "10",     "beneficiaries", "Year 1", "TechnoServe SAWA Year 1 Implementation Plan, Sep 2026"),
                ("TechnoServe",          "Catalytic grantees",    "10",     "grantees",      "Year 1", "TechnoServe SAWA Year 1 Implementation Plan, Sep 2026"),
                ("TechnoServe",          "Micro-grant businesses","150",    "businesses",    "Year 1", "TechnoServe SAWA Year 1 Implementation Plan, Sep 2026"),
                ("TechnoServe",          "Jobs created",          "250",    "jobs",          "Year 1", "TechnoServe SAWA Year 1 Implementation Plan, Sep 2026"),
                ("TechnoServe",          "Fish traded",           "1,298+", "MT",            "Year 1", "TechnoServe SAWA Year 1 Implementation Plan, Sep 2026"),
                ("TechnoServe",          "Value from catfish sales","845,000","USD",          "Year 1", "TechnoServe SAWA Year 1 Implementation Plan, Sep 2026"),
                ("NewAge Agric",         "D&F jobs",              "5,800",  "jobs",          "Year 1", "NewAge Agric SAWA Year 1 Implementation Plan, Sep 2026"),
                ("NewAge Agric",         "Young women in jobs",   "≥90%",   "% of D&F jobs", "Year 1", "NewAge Agric SAWA Year 1 Implementation Plan, Sep 2026"),
                ("NewAge Agric",         "PWD reached",           "290",    "beneficiaries", "Year 1", "NewAge Agric SAWA Year 1 Implementation Plan, Sep 2026"),
                ("NewAge Agric",         "Regions covered",       "7",      "regions",       "Year 1", "NewAge Agric SAWA Year 1 Implementation Plan, Sep 2026"),
                ("AgroKings",           "Cluster sites",          "10",     "sites",         "Year 1", "AgroKings SAWA Year 1 Implementation Plan, Sep 2026"),
                ("Aglow Farms",         "Communities reached",    "15",     "communities",   "Year 1", "Aglow Farms SAWA Year 1 Implementation Plan, Sep 2026"),
                ("Aglow Farms",         "Districts covered",      "4",      "districts",     "Year 1", "Aglow Farms SAWA Year 1 Implementation Plan, Sep 2026"),
                ("AFRIGEM",             "Communities reached",    "10",     "communities",   "Year 1", "AFRIGEM SAWA Year 1 Implementation Plan, Sep 2026"),
                ("AFRIGEM",             "Districts covered",      "6",      "districts",     "Year 1", "AFRIGEM SAWA Year 1 Implementation Plan, Sep 2026"),
                ("AFRIGEM",             "Anchor operators",       "10",     "operators",     "Year 1", "AFRIGEM SAWA Year 1 Implementation Plan, Sep 2026"),
                ("Fisheries Commission","Participants reached",   "15,000", "participants",  "Year 1", "Fisheries Commission SAWA Year 1 Implementation Plan, Sep 2026"),
                ("Fisheries Commission","PWD reached",            "750",    "beneficiaries", "Year 1", "Fisheries Commission SAWA Year 1 Implementation Plan, Sep 2026"),
                ("Fisheries Commission","Enterprises supported",  "500",    "enterprises",   "Year 1", "Fisheries Commission SAWA Year 1 Implementation Plan, Sep 2026"),
                ("CSIR",                "Young women coached",    "100",    "beneficiaries", "Year 1", "CSIR SAWA Year 1 Implementation Plan, Sep 2026"),
            ]:
                conn.execute(text("""
                    INSERT INTO partner_targets
                           (partner_id, project_id, level, metric_label,
                            target_value, unit, time_basis, source_doc, source_page)
                    SELECT p.partner_id, p.project_id, 1, :label,
                           :val, :unit, :basis, :doc, ''
                    FROM partners p
                    JOIN projects pr ON p.project_id = pr.project_id
                    WHERE pr.name = 'SAWA' AND p.name = :pname
                      AND NOT EXISTS (
                          SELECT 1 FROM partner_targets pt2
                          WHERE pt2.project_id = p.project_id
                            AND pt2.partner_id  = p.partner_id
                            AND pt2.metric_label = :label
                            AND pt2.time_basis   = :basis
                      )
                """), {
                    "pname": _pname, "label": _label, "val": _val,
                    "unit": _unit, "basis": _basis, "doc": _doc,
                })
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
        "ALTER TABLE raw_data_analysis ADD COLUMN progression_stage TEXT",
        "ALTER TABLE raw_data_analysis ADD COLUMN pillar TEXT",
        "ALTER TABLE raw_data_analysis ADD COLUMN dqa_stage TEXT",
        "ALTER TABLE raw_data_analysis ADD COLUMN disaggregation TEXT",
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
    # Backfill progression_stage, pillar, dqa_stage for rows that predate
    # these columns (correlated subquery — SQLite doesn't support UPDATE...FROM).
    for _code, _ps, _pl in [
        ("LoP.1",    "D&F",  "Programme-wide"),
        ("PI.1",     "WEO",  "Capacity Building & Inclusion"),
        ("PI.3",     "WEO",  "Capacity Building & Inclusion"),
        ("PI.9",     "WEO",  "Capacity Building & Inclusion"),
        ("PI.11",    "WEO",  "Capacity Building & Inclusion"),
        ("PI.12",    "WEO",  "Capacity Building & Inclusion"),
        ("PI.13",    "WEO",  "Capacity Building & Inclusion"),
        ("PI.17",    "WEO",  "Capacity Building & Inclusion"),
        ("PI.18",    "WEO",  "Capacity Building & Inclusion"),
        ("PI.19",    "WEO",  "Capacity Building & Inclusion"),
        ("PI.20",    "WEO",  "Capacity Building & Inclusion"),
        ("PI.22",    "WEO",  "Capacity Building & Inclusion"),
        ("PI.23",    "WEO",  "Capacity Building & Inclusion"),
        ("PIV.5",    "WEO",  "Ecosystem Strengthening"),
        ("PII.R5",   "YIW",  "Production Expansion & Productivity"),
        ("PIII.R1",  "YIW",  "Value Addition & Market Systems"),
        ("PII.R6",   "D&F",  "Production Expansion & Productivity"),
        ("PII.R7",   "D&F",  "Production Expansion & Productivity"),
        ("PIII.R2",  "D&F",  "Value Addition & Market Systems"),
        ("PIII.R3",  "D&F",  "Value Addition & Market Systems"),
        ("PIII.6",   "WEO",  "Value Addition & Market Systems"),
    ]:
        conn.execute(
            """UPDATE raw_data_analysis
               SET progression_stage = ?,
                   pillar             = ?,
                   dqa_stage          = 'Raw'
               WHERE logframe_row_id IN (
                   SELECT id FROM logframe_rows WHERE indicator_code = ?
               )
                 AND progression_stage IS NULL""",
            (_ps, _pl, _code),
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

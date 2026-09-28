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
                "ALTER TABLE data_collection_plan ADD COLUMN IF NOT EXISTS instrument_name TEXT",
                "ALTER TABLE data_collection_plan ADD COLUMN IF NOT EXISTS logframe_row_id INTEGER REFERENCES logframe_rows(id) ON DELETE SET NULL",
                "ALTER TABLE raw_data_analysis ADD COLUMN IF NOT EXISTS progression_stage TEXT",
                "ALTER TABLE raw_data_analysis ADD COLUMN IF NOT EXISTS pillar TEXT",
                "ALTER TABLE raw_data_analysis ADD COLUMN IF NOT EXISTS dqa_stage TEXT",
                "ALTER TABLE raw_data_analysis ADD COLUMN IF NOT EXISTS disaggregation TEXT",
                "ALTER TABLE raw_data_analysis ADD COLUMN IF NOT EXISTS partner_id INTEGER",
            ):
                conn.execute(text(stmt))
            # Index must come after ADD COLUMN (schema.sql can't do it safely on existing DBs).
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_rda_partner ON raw_data_analysis(partner_id)"
            ))
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
            # Backfill DCP logframe_row_id for existing rows that predate the FK.
            # Keyed on stakeholder which is unique per project in SAWA seed data.
            for _stakeholder, _code in [
                ("PWD participants",                                    "PI.1"),
                ("All programme participants",                          "PI.3"),
                ("Partner implementing organisations",                  "PI.9"),
                ("Women in Aquaculture Network (WAN) members",          "PI.11"),
                ("WAN members and CEL programme staff",                 "PI.12"),
                ("PWD participants and peer mentors",                   "PI.13"),
                ("Women-led cooperative and cluster members",           "PI.17"),
                ("Women-led cooperatives and clusters",                 "PI.18"),
                ("Programme participants and community champions",      "PI.19"),
                ("Young women programme participants",                  "PI.20"),
                ("SAWA intervention communities",                       "PI.22"),
                ("Programme partners and implementation sites",         "PI.23"),
                ("Young women programme participants",                  "PIV.5"),
                ("Supported enterprises",                               "PII.R6"),
                ("Persons with Disabilities (PWDs) placed into D&F employment", "PII.R5"),
                ("Young women PWDs in D&F production",                 "PII.R7"),
                ("Enterprises and value chain actors",                  "PIII.6"),
                ("Programme participants (all)",                        "LoP.1"),
                ("Individual participants",                             "PIII.R1"),
                ("SAWA-supported enterprises",                          "PIII.R3"),
                ("Production enterprises (fishpond operators)",         "PIII.R2"),
            ]:
                conn.execute(text("""
                    UPDATE data_collection_plan
                    SET    logframe_row_id = (
                               SELECT lr.id
                               FROM   logframe_rows lr
                               WHERE  lr.project_id    = data_collection_plan.project_id
                                 AND  lr.indicator_code = :code
                               LIMIT 1
                           )
                    WHERE  stakeholder      = :s
                      AND  logframe_row_id IS NULL
                """), {"s": _stakeholder, "code": _code})
            # Backfill instrument_name for the original 11 DCP rows seeded before
            # the instrument_name column was added (ADD COLUMN leaves them NULL).
            for _stakeholder, _iname in [
                ("PWD participants",                          "Enrolment Screening Form (KoboToolbox Tool 1)"),
                ("All programme participants",                "Training & BDS Attendance Register (KoboToolbox Tool 2)"),
                ("Supported enterprises",                    "Enterprise Output & Revenue Survey"),
                ("Young women participants",                 "Gender Empowerment Structured Interview"),
                ("Enterprises and value chain actors",       "Market Linkage Verification Form"),
                ("Non-continuers and dropouts",              "Dropout Follow-up Phone Interview"),
                ("Programme participants (all)",             "Dignified & Fulfilling Work (DFW) Survey"),
                ("Individual participants",                  "Participant Income Tracking Survey"),
                ("SAWA-supported enterprises",               "Enterprise Sustainability Assessment"),
                ("Production enterprises (fishpond operators)", "Production Volume Record (Partner MEAL)"),
                ("Programme staff and CEL management",       "Programme Quality & Adaptive Management Log"),
            ]:
                conn.execute(text("""
                    UPDATE data_collection_plan
                    SET    instrument_name = :n
                    WHERE  stakeholder = :s
                      AND  (instrument_name IS NULL OR instrument_name = '')
                """), {"s": _stakeholder, "n": _iname})
            # Insert/backfill the 13 new DCP instruments added when DCP was
            # expanded from 11 to 24 rows (one per logframe indicator).
            # Keyed on instrument_name (unique per row) — NOT stakeholder,
            # because PI.20 and PIV.5 share the same stakeholder value.
            # Idempotent: INSERT only when instrument_name absent; UPDATE
            # data_points/rationale for rows already inserted without them.
            _NEW_DCP = [
              # (stakeholder, lf_code, status, freq, cm, cy, resp, instrument_name, journey_step, integration_mechanism, data_points, rationale)
              ("Partner implementing organisations", "PI.9", "New", "Quarterly", 9, 2026, "Programme Team",
               "GYSI Focal Person Training Certificate & Registry", "Training",
               "Partner-submitted completion certificates and registry reviewed by CEL MEAL",
               "Name; partner organisation; training module (GALS/EMAP); date; region; sex",
               "Tracks ToT capacity building; ensures each partner has trained GYSI champions before Phase 2 community-level delivery begins"),
              ("Women in Aquaculture Network (WAN) members", "PI.11", "Existing", "Quarterly", 9, 2026, "Programme Team",
               "WAN Forum Attendance Register", "Training",
               "Paper register collected at each WAN session; digitised monthly by CEL field officer",
               "Name; region; forum type; session date; PWD status; membership status",
               "WAN attendance is the primary evidence of women's collective agency activation; register disaggregation by PWD status flags inclusion within the network"),
              ("WAN members and CEL programme staff", "PI.12", "New", "Quarterly", 3, 2027, "Programme Team",
               "WAN Event Report & Attendance Log", "Training",
               "CEL field officer event report submitted within 5 days of each event",
               "Event type (bootcamp/exchange); date; location; attendance count; outcomes summary",
               "Leadership events cannot be measured through routine attendance registers; a dedicated event report captures qualitative outcomes alongside headcount"),
              ("PWD participants and peer mentors", "PI.13", "New", "Quarterly", 9, 2026, "Programme Team",
               "Peer Mentor Registry & Match Record", "Training",
               "Programme Team maintains registry; field officer verifies match via phone call",
               "Mentor ID; mentee ID; disability type; match date; region; follow-up date",
               "PWD peer mentorship is a SAWA inclusion commitment; the registry is the only evidence of active mentor-mentee relationships and ongoing engagement"),
              ("Women-led cooperative and cluster members", "PI.17", "Existing", "Quarterly", 12, 2026, "Programme Team",
               "Cooperative Member Training Register", "Training",
               "Paper register maintained by cooperative secretary; collected quarterly by partner MEAL",
               "Name; cooperative ID; training module; date; membership status; region",
               "Cooperative membership records confirm participation is by active members, not community bystanders; distinguishes Pillar III reach from Pillar I reach"),
              ("Women-led cooperatives and clusters", "PI.18", "New", "Quarterly", 3, 2027, "Programme Team",
               "Governance Checklist & Adoption Record (KoboToolbox Tool 3)", "6-month follow-up",
               "CEL field officer administers Tool 3 at cooperative; signed document photographed and uploaded",
               "Cooperative ID; framework type; adoption date; signatory; region; governance score",
               "Governance adoption requires physical documentation; the KoboToolbox governance checklist score provides standardised evidence across all 25 cooperatives"),
              ("Programme participants and community champions", "PI.19", "New", "Quarterly", 12, 2026, "CEL MEAL",
               "Gender-Transformative Training Register & Knowledge Assessment", "Training",
               "CEL MEAL-administered pre/post test at each training session",
               "Name; role (participant/champion); training date; knowledge score; sex; region",
               "Pre/post knowledge scores evidence transformative impact beyond attendance headcount; community champions are a distinct cohort from programme participants"),
              ("Young women programme participants", "PI.20", "New", "Quarterly", 12, 2026, "CEL MEAL",
               "Safeguarding Training Record & Incident Log", "Training",
               "CEL safeguarding officer maintains log; training records digitised via KoboToolbox",
               "Name; training date; session type; incident flag (Y/N); facilitator; region",
               "PSEA training is a SAWA donor compliance requirement; the incident log enables real-time safeguarding response alongside quarterly reporting"),
              ("SAWA intervention communities", "PI.22", "New", "Annual", 6, 2027, "CEL MEAL",
               "Community Safeguarding Campaign Report", "Mobilisation",
               "CEL safeguarding officer submits campaign report within 7 days of each event",
               "Event type; community name; date; attendance count; feedback summary; region",
               "Community-level safeguarding awareness cannot be inferred from participant training records; separate community evidence is required for AIL donor reporting"),
              ("Programme partners and implementation sites", "PI.23", "New", "Annual", 6, 2027, "CEL MEAL",
               "Site Safeguarding & OHS Certification Record", "Annual review",
               "CEL safeguarding officer reviews signed policy documents at each site annually",
               "Site ID; partner; policy adoption date; certification type; OHS standard met; region",
               "Site-level institutionalisation requires physical certification documentation; cannot be verified through participant records alone"),
              ("Young women programme participants", "PIV.5", "New", "Quarterly", 12, 2026, "Programme Team",
               "E-SAWA Digital Training Register & Platform Enrolment", "Training",
               "E-SAWA platform auto-logs enrolment; facilitator submits paper register for offline participants",
               "Name; training type (digital literacy/mentorship/workshop); date; platform enrolment status; region",
               "Digital literacy is a distinct delivery channel from BDS; platform enrolment data confirms digital activation beyond attendance, evidencing the E-SAWA pathway target"),
              ("Persons with Disabilities (PWDs) placed into D&F employment", "PII.R5", "New", "Quarterly", 9, 2026, "Partner MEAL",
               "PWD Employment Verification Record", "6-month follow-up",
               "Partner MEAL officer verifies employment record; CEL field officer conducts spot-check",
               "Name; disability type; employer/site; start date; role type; region; monthly income (GHS)",
               "Employment verification requires both PWD registry match and employment record; field spot-checks prevent proxy reporting, a documented risk in the SAWA context"),
              ("Young women PWDs in D&F production", "PII.R7", "New", "Quarterly", 9, 2026, "Partner MEAL",
               "PWD Revenue & Sales Record", "6-month follow-up",
               "Partner MEAL collects sales receipts quarterly; CEL MEAL consolidates into programme total",
               "Participant ID; sales amount (USD); product type; buyer; transaction date; PWD status",
               "Revenue cannot be inferred from production volume alone; separate financial records capture price variability and actual economic impact attributable to the programme"),
            ]
            _existing_pids = [
                r[0] for r in conn.execute(
                    text("SELECT DISTINCT project_id FROM data_collection_plan")
                ).fetchall()
            ]
            for _pid in _existing_pids:
                for (_sh, _code, _status, _freq, _cm, _cy, _resp,
                     _iname, _jstep, _integ, _dpts, _rat) in _NEW_DCP:
                    _lf = conn.execute(text(
                        "SELECT id FROM logframe_rows WHERE project_id=:pid AND indicator_code=:c LIMIT 1"
                    ), {"pid": _pid, "c": _code}).fetchone()
                    _lf_id = _lf[0] if _lf else None
                    _row = conn.execute(text(
                        "SELECT id FROM data_collection_plan WHERE project_id=:pid AND instrument_name=:n LIMIT 1"
                    ), {"pid": _pid, "n": _iname}).fetchone()
                    if not _row:
                        conn.execute(text("""
                            INSERT INTO data_collection_plan
                            (project_id, logframe_row_id, stakeholder, indicator_statement,
                             data_points, rationale, instrument_name, instrument_status,
                             instrument_link, journey_step, integration_mechanism,
                             frequency, collection_month, collection_year, responsible_party)
                            SELECT :pid, :lf_id, :sh, lr.indicator_statement,
                                   :dpts, :rat, :iname, :status,
                                   'https://kf.kobotoolbox.org/',
                                   :jstep, :integ, :freq, :cm, :cy, :resp
                            FROM   logframe_rows lr WHERE lr.id = :lf_id
                        """), {"pid": _pid, "lf_id": _lf_id, "sh": _sh,
                               "dpts": _dpts, "rat": _rat, "iname": _iname,
                               "status": _status, "jstep": _jstep, "integ": _integ,
                               "freq": _freq, "cm": _cm, "cy": _cy, "resp": _resp})
                    else:
                        # Backfill data_points/rationale on rows already inserted
                        conn.execute(text("""
                            UPDATE data_collection_plan
                            SET data_points = :dpts, rationale = :rat
                            WHERE id = :rid
                              AND (data_points IS NULL OR data_points = '')
                        """), {"dpts": _dpts, "rat": _rat, "rid": _row[0]})
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
            # A1: seed partner-specific Q1 actual rows (idempotent NOT EXISTS guard).
            _fy = current_fiscal_year()
            for _pname, _code, _q1, _ps, _pl in [
                ("Aglow Farms",  "PI.1",   "461",  "WEO", "Capacity Building & Inclusion"),
                ("NewAge Agric", "LoP.1",  "1456", "D&F", "Programme-wide"),
                ("AgroKings",    "PI.1",   "900",  "WEO", "Capacity Building & Inclusion"),
                ("AFRIGEM",      "PI.1",   "350",  "WEO", "Capacity Building & Inclusion"),
                ("Naple Betta",  "PII.R5", "1850", "YIW", "Production Expansion & Productivity"),
            ]:
                conn.execute(text("""
                    INSERT INTO raw_data_analysis
                           (project_id, logframe_row_id, reporting_year, data_type, partner_id,
                            actual_q1, indicator_status, action_status,
                            progression_stage, pillar, dqa_stage)
                    SELECT pr.project_id,
                           (SELECT id FROM logframe_rows
                            WHERE project_id=pr.project_id AND indicator_code=:code),
                           :fy, 'Performance',
                           (SELECT partner_id FROM partners
                            WHERE project_id=pr.project_id AND name=:pname),
                           :q1,
                           'Data currently being collected/analysed',
                           'No action needed - data reporting only',
                           :ps, :pl, 'Raw'
                    FROM projects pr
                    WHERE pr.name = 'SAWA'
                      AND NOT EXISTS (
                          SELECT 1 FROM raw_data_analysis rda
                          JOIN  logframe_rows lr ON lr.id = rda.logframe_row_id
                          JOIN  partners p        ON p.partner_id = rda.partner_id
                          WHERE rda.project_id = pr.project_id
                            AND lr.indicator_code = :code
                            AND p.name = :pname
                      )
                """), {"pname": _pname, "code": _code, "fy": _fy,
                       "q1": _q1, "ps": _ps, "pl": _pl})
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
            # Populate full text fields for the 6 cross-cutting review protocols.
            # review_scope IS NULL guard makes each UPDATE idempotent.
            for _dt, _scope, _existing, _actual, _issue, _role in [
                (
                    "Safeguarding (SG)",
                    ("All safeguarding and PSEA incidents, near-misses, complaints and "
                     "feedback received in the period — across all programme sites and "
                     "anchor partners.  Covers PI.20 (PSEA awareness training), PI.22 "
                     "(campaigns/roadshows), PI.23 (certified sites).  "
                     "Mandatory cross-cutting section per AIL reporting standard."),
                    ("Safeguarding incident log; CEL safeguarding officer monthly reports; "
                     "community complaints and feedback mechanism records; "
                     "PI.20/PI.22/PI.23 actuals in raw_data_analysis (Module E)"),
                    ("Kobo Safeguarding Monitoring Form (Module E sync — Form 6); "
                     "CEL-managed grievance mechanism register; "
                     "partner safeguarding focal-person reports; "
                     "site certification documentation (PI.23)"),
                    ("Any reported safeguarding incident, PSEA allegation or complaint in the period; "
                     "or PI.20/PI.22 below quarterly target; "
                     "or any partner site without a named focal person; "
                     "or a certified site whose certification lapses"),
                    "CEL Safeguarding Officer",
                ),
                (
                    "Gender & Social Inclusion (GYSI)",
                    ("GYSI data across all six GYSI categories — Reach (applicants & enrolment), "
                     "Accommodation (support provided), Safety (feedback/complaints/incidents), "
                     "Participation (attendance/completion/dropout), "
                     "Outcomes (work/enterprise/earnings/retention), "
                     "Agency (control over income/decisions) — disaggregated by sex, age, "
                     "disability, location and pathway.  Covers PI.9, PI.13, PI.19, PII.R5."),
                    ("GYSI data in raw_data_analysis (Module E); "
                     "previous GYSI narrative section from quarterly report; "
                     "partner GYSI officer monthly briefings"),
                    ("Training attendance registers disaggregated by sex/disability (Module E); "
                     "enrolment register with sex/age/disability flags (Form 1); "
                     "self-efficacy instrument actuals (Module C Bi-annual, Nov cycle); "
                     "dropout check-in actuals (Quarterly, Sep cycle)"),
                    ("Women's share of any output indicator falls below 75%; "
                     "or PWD inclusion below 5% at any partner site; "
                     "or any GYSI focal person position unfilled for >30 days; "
                     "or self-efficacy scores show no improvement at 6-month follow-up"),
                    "CEL GYSI Officer",
                ),
                (
                    "Climate & Environmental Sustainability (CES)",
                    ("Environmental and climate-related risks and practices across all "
                     "programme sites — water quality, pond management, biosecurity, "
                     "feed sourcing, energy use, waste management.  "
                     "SAWA's Good Aquaculture Practices (GAqP) compliance at anchor sites."),
                    ("GAqP compliance reports from Fisheries Commission; "
                     "CSIR water-quality and environmental assessment data; "
                     "anchor partner site-visit records on feed, waste and water management"),
                    ("FC technical audit reports; CSIR demonstration-farm monitoring data; "
                     "partner operational logs on water-quality and feed sourcing; "
                     "field officer observations during site visits"),
                    ("Any GAqP non-compliance flagged by FC at a certified site; "
                     "or water-quality parameter outside acceptable range at >20% of "
                     "monitored ponds; or feed-sourcing practice flagged as environmentally "
                     "unsustainable by CSIR; or a climate event causing >10% production loss"),
                    "Technical Lead + FC/CSIR Liaison",
                ),
                (
                    "Financial Inclusion (FI)",
                    ("Access to and uptake of financial products and services by programme "
                     "participants — micro-grants, catalytic grants, SME facility, savings "
                     "groups, mobile money, insurance.  Tracks burn rate against 70% "
                     "threshold and deliverables against 60% threshold per tranche."),
                    ("TechnoServe grant disbursement tracker; "
                     "Module A Level 1 TechnoServe grant targets (catalytic grantees, micro-grant businesses); "
                     "CEL programme budget records; previous FI section from quarterly report"),
                    ("TechnoServe quarterly finance disbursement report; "
                     "BDS financial literacy training completion records (Tool 2); "
                     "participant savings-group and mobile-money uptake data (Module C income tracking)"),
                    ("Programme burn rate below 70% of annual budget by Q3; "
                     "or deliverables below 60% of annual workplan commitments at mid-year review; "
                     "or TechnoServe grant utilisation below 80% with no documented reason; "
                     "or <40% of BDS graduates accessing any formal financial product within 6 months"),
                    "Programme Manager + TechnoServe Finance Lead",
                ),
                (
                    "Voice & Agency (VA)",
                    ("Women's and youth control over income, business decisions, enterprise "
                     "ownership and participation in leadership forums.  Covers the WAN "
                     "(PI.11, PI.12), cooperative governance (PI.17, PI.18, PIII.6), "
                     "the self-efficacy and market-linkage instruments (Module C Bi-annual)."),
                    ("WAN event attendance and governance records; "
                     "cooperative governance framework adoption data (PI.18 actuals); "
                     "self-efficacy instrument actuals (Bi-annual); "
                     "income-tracking actuals (Module C Bi-annual)"),
                    ("WAN Leadership Events Log (Kobo Form 3 sync); "
                     "Cooperative & Governance Registry (Kobo Form 5 sync); "
                     "market-linkage tracking data; "
                     "6-month follow-up interview responses on agency and decision-making"),
                    ("Fewer than 25% of cooperative/cluster leadership positions held by women; "
                     "or self-efficacy scores static or declining at Bi-annual follow-up; "
                     "or <50% of income reported by participants as independently controlled; "
                     "or WAN forum cancelled with no replacement in the same quarter"),
                    "CEL GYSI Officer + Programme Manager",
                ),
                (
                    "Communications & Visibility (CV)",
                    ("CEL and SAWA visibility obligations to Mastercard Foundation and "
                     "Agri-Impact Limited — branding compliance, SAWA Voices stories, "
                     "social media presence, programme documentation and media coverage.  "
                     "Covers PI.22 (awareness campaigns/roadshows)."),
                    ("Mastercard Foundation branding and communications guidelines; "
                     "CEL SAWA Voices story log; "
                     "partner progress report communications sections; "
                     "PI.22 actuals (awareness campaigns)"),
                    ("SAWA Voices documented success stories (KNUST/e-SAWA platform); "
                     "campaign and roadshow event records (Kobo Form 6); "
                     "social media engagement metrics; "
                     "AIL communications and visibility review checklist"),
                    ("Any SAWA-branded material missing required Mastercard Foundation acknowledgement; "
                     "or PI.22 campaigns below quarterly target; "
                     "or no success story documented in the period; "
                     "or a communications breach flagged by AIL"),
                    "Communications Officer",
                ),
            ]:
                conn.execute(text("""
                    UPDATE review_protocols
                    SET review_scope          = :scope,
                        existing_info_source  = :existing,
                        actual_info_source    = :actual,
                        issue_definition      = :issue,
                        reviewer_role         = :role
                    WHERE data_type = :dt
                      AND review_scope IS NULL
                """), {
                    "dt": _dt, "scope": _scope, "existing": _existing,
                    "actual": _actual, "issue": _issue, "role": _role,
                })
            # Ensure workplan_activities table exists (added after initial schema deploy).
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS workplan_activities (
                    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
                    partner_id      INTEGER REFERENCES partners(partner_id) ON DELETE SET NULL,
                    quarter         INTEGER NOT NULL CHECK(quarter IN (1,2,3,4)),
                    fiscal_year     INTEGER NOT NULL,
                    activity        TEXT    NOT NULL,
                    deliverable     TEXT,
                    due_date        TEXT,
                    responsible     TEXT,
                    status          TEXT    DEFAULT 'Not Started'
                                    CHECK(status IN ('Not Started','In Progress','Complete','Delayed')),
                    logframe_row_id INTEGER REFERENCES logframe_rows(id) ON DELETE SET NULL,
                    notes           TEXT
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_wa_project ON workplan_activities(project_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_wa_partner ON workplan_activities(partner_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_wa_quarter ON workplan_activities(quarter, fiscal_year)"))
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
        "ALTER TABLE data_collection_plan ADD COLUMN instrument_name TEXT",
        "ALTER TABLE data_collection_plan ADD COLUMN logframe_row_id INTEGER",
        "ALTER TABLE raw_data_analysis ADD COLUMN progression_stage TEXT",
        "ALTER TABLE raw_data_analysis ADD COLUMN pillar TEXT",
        "ALTER TABLE raw_data_analysis ADD COLUMN dqa_stage TEXT",
        "ALTER TABLE raw_data_analysis ADD COLUMN disaggregation TEXT",
        "ALTER TABLE raw_data_analysis ADD COLUMN partner_id INTEGER",
    ):
        try:
            conn.execute(stmt)
        except Exception:
            pass  # column already exists
    # Index after ADD COLUMN (schema.sql can't do it safely on existing DBs).
    try:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rda_partner ON raw_data_analysis(partner_id)"
        )
    except Exception:
        pass
    # Ensure workplan_activities table exists (added after initial schema deploy).
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workplan_activities (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
                partner_id      INTEGER REFERENCES partners(partner_id) ON DELETE SET NULL,
                quarter         INTEGER NOT NULL CHECK(quarter IN (1,2,3,4)),
                fiscal_year     INTEGER NOT NULL,
                activity        TEXT    NOT NULL,
                deliverable     TEXT,
                due_date        TEXT,
                responsible     TEXT,
                status          TEXT    DEFAULT 'Not Started'
                                CHECK(status IN ('Not Started','In Progress','Complete','Delayed')),
                logframe_row_id INTEGER REFERENCES logframe_rows(id) ON DELETE SET NULL,
                notes           TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_wa_project ON workplan_activities(project_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_wa_partner ON workplan_activities(partner_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_wa_quarter ON workplan_activities(quarter, fiscal_year)")
    except Exception:
        pass
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
    # A1: seed partner-specific Q1 actual rows (idempotent NOT EXISTS guard).
    for _pname, _code, _q1, _ps, _pl in [
        ("Aglow Farms",  "PI.1",   "461",  "WEO", "Capacity Building & Inclusion"),
        ("NewAge Agric", "LoP.1",  "1456", "D&F", "Programme-wide"),
        ("AgroKings",    "PI.1",   "900",  "WEO", "Capacity Building & Inclusion"),
        ("AFRIGEM",      "PI.1",   "350",  "WEO", "Capacity Building & Inclusion"),
        ("Naple Betta",  "PII.R5", "1850", "YIW", "Production Expansion & Productivity"),
    ]:
        conn.execute(
            """INSERT INTO raw_data_analysis
               (project_id, logframe_row_id, reporting_year, data_type, partner_id,
                actual_q1, indicator_status, action_status,
                progression_stage, pillar, dqa_stage)
               SELECT pr.project_id,
                      (SELECT id FROM logframe_rows
                       WHERE project_id=pr.project_id AND indicator_code=?),
                      ?,
                      'Performance',
                      (SELECT partner_id FROM partners
                       WHERE project_id=pr.project_id AND name=?),
                      ?,
                      'Data currently being collected/analysed',
                      'No action needed - data reporting only',
                      ?, ?, 'Raw'
               FROM projects pr
               WHERE pr.name = 'SAWA'
                 AND NOT EXISTS (
                     SELECT 1 FROM raw_data_analysis rda
                     JOIN  logframe_rows lr ON lr.id = rda.logframe_row_id
                     JOIN  partners p        ON p.partner_id = rda.partner_id
                     WHERE rda.project_id = pr.project_id
                       AND lr.indicator_code = ?
                       AND p.name = ?
                 )""",
            (_code, current_fiscal_year(), _pname, _q1, _ps, _pl, _code, _pname),
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


def recompute_actual_year(row_id: int) -> None:
    """Sum actual_q1..q4 into actual_year for a raw_data_analysis row.

    Called by Module D (Kobo sync), Module D (file upload), and Module E
    (manual data-editor save) whenever a quarterly actual changes, so that
    Module H (which reads only actual_year) always sees a current total.
    Leaves actual_year untouched if no quarter has a parseable numeric value
    yet (annual-frequency indicators entered directly in Module E).
    """
    from utils.num_parse import num_or_none
    row = run_query(
        "SELECT actual_q1, actual_q2, actual_q3, actual_q4 FROM raw_data_analysis WHERE id=:id",
        {"id": row_id},
    )
    if not row:
        return
    quarters = [num_or_none(row[0][f"actual_q{n}"]) for n in (1, 2, 3, 4)]
    parsed = [q for q in quarters if q is not None]
    if not parsed:
        return
    total = sum(parsed)
    year_str = str(int(total)) if total == int(total) else f"{total:.4g}"
    run_write(
        "UPDATE raw_data_analysis SET actual_year=:y WHERE id=:id",
        {"y": year_str, "id": row_id},
    )


def auto_advance_dqa(row_id: int) -> None:
    """Advance dqa_stage from Raw to Completeness Checked when all 4 quarters
    have data; to Traceability Verified when at least one evidence row exists.

    Guards: never demotes a stage that's already ahead; never touches
    Outcome Validated (that requires explicit human sign-off).
    """
    row = run_query(
        """SELECT actual_q1, actual_q2, actual_q3, actual_q4,
                  dqa_stage
           FROM raw_data_analysis WHERE id=:id""",
        {"id": row_id},
    )
    if not row:
        return
    r = row[0]
    current = r["dqa_stage"] or "Raw"
    if current == "Outcome Validated":
        return

    all_quarters_filled = all(
        str(r.get(f"actual_q{n}") or "").strip()
        for n in (1, 2, 3, 4)
    )
    evidence_exists = bool(run_query(
        "SELECT id FROM evidence WHERE logframe_row_id = "
        "(SELECT logframe_row_id FROM raw_data_analysis WHERE id=:id) LIMIT 1",
        {"id": row_id},
    ))

    stage_order = ["Raw", "Completeness Checked", "Traceability Verified", "Outcome Validated"]
    current_idx = stage_order.index(current) if current in stage_order else 0
    new_idx = current_idx

    if all_quarters_filled and new_idx < 1:
        new_idx = 1
    if evidence_exists and new_idx < 2:
        new_idx = 2

    if new_idx > current_idx:
        run_write(
            "UPDATE raw_data_analysis SET dqa_stage=:s WHERE id=:id",
            {"s": stage_order[new_idx], "id": row_id},
        )


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

-- CEL MEL Platform — shared schema
-- SQLite v1; swap connection string in db.py to migrate to Postgres.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    project_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    donor        TEXT,
    budget_total REAL,
    start_date   TEXT,   -- ISO-8601: YYYY-MM-DD
    end_date     TEXT
);

CREATE TABLE IF NOT EXISTS partners (
    partner_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,
    role       TEXT,
    tier       TEXT    CHECK(tier IN ('Anchor','Technical','Implementing'))
);

CREATE TABLE IF NOT EXISTS indicators (
    indicator_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id    INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    pillar        TEXT,
    level         TEXT,   -- 'Impact'|'Outcome'|'Output'|'Activity'
    statement     TEXT    NOT NULL,
    target_value  REAL,
    unit          TEXT
);

-- Append-only log; every module inserts rows, none update or delete.
CREATE TABLE IF NOT EXISTS data_points (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id  INTEGER NOT NULL REFERENCES indicators(indicator_id) ON DELETE CASCADE,
    quarter       INTEGER CHECK(quarter IN (1,2,3,4)),
    year          INTEGER,
    value         REAL,
    source_module TEXT    -- 'C'|'D'|'E'|'F'
);

-- Funnel targets for Module A (Partner Alignment).
-- partner_id is nullable: Levels 2-4 are programme-wide, not partner-specific.
CREATE TABLE IF NOT EXISTS partner_targets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id   INTEGER REFERENCES partners(partner_id) ON DELETE CASCADE,
    project_id   INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    level        INTEGER NOT NULL CHECK(level IN (1,2,3,4)),
    metric_label TEXT    NOT NULL,
    target_value TEXT,
    unit         TEXT,
    time_basis   TEXT    CHECK(time_basis IN ('Life of programme','Year 1','Annual')),
    source_doc   TEXT,
    source_page  TEXT
);

-- Module B: Theory of Change node tree.
CREATE TABLE IF NOT EXISTS toc_nodes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id       INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    level            TEXT    NOT NULL CHECK(level IN ('Impact','Outcome','Intermediate Outcome','Output','Activity','Input')),
    statement        TEXT    NOT NULL,
    parent_id        INTEGER REFERENCES toc_nodes(id),
    source_verified  BOOLEAN DEFAULT 1,
    source_note      TEXT
);

-- Module B: Logframe rows — one row per indicator per result level.
-- indicator_code (e.g. 'PI.1') stored here for human-readable display;
-- indicator_id links to the shared indicators master table when populated.
CREATE TABLE IF NOT EXISTS logframe_rows (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id            INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    indicator_id          INTEGER REFERENCES indicators(indicator_id),
    indicator_code        TEXT,
    result_level          TEXT,
    indicator_statement   TEXT,
    disaggregation        TEXT,
    baseline_value        TEXT,
    target_annual         TEXT,
    target_lop            TEXT,
    means_of_verification TEXT,
    frequency             TEXT,
    responsible           TEXT,
    critical_assumption   TEXT
);

-- Append-only audit trail for every logframe edit.
CREATE TABLE IF NOT EXISTS logframe_changelog (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id       INTEGER NOT NULL REFERENCES logframe_rows(id) ON DELETE CASCADE,
    field_changed TEXT   NOT NULL,
    old_value    TEXT,
    new_value    TEXT,
    changed_by   TEXT    NOT NULL,
    changed_at   TEXT    NOT NULL   -- ISO-8601 datetime
);

-- Module C: Data Collection Plan — one row per instrument in the programme's
-- baseline data collection design. collection_month/year is the FIRST scheduled
-- collection event; the UI expands frequency to generate the full calendar.
CREATE TABLE IF NOT EXISTS data_collection_plan (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id            INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    indicator_id          INTEGER REFERENCES indicators(indicator_id),
    stakeholder           TEXT    NOT NULL,
    indicator_statement   TEXT    NOT NULL,
    data_points           TEXT,
    rationale             TEXT,
    instrument_status     TEXT    CHECK(instrument_status IN ('New', 'Existing')),
    instrument_link       TEXT,
    journey_step          TEXT,
    integration_mechanism TEXT,
    frequency             TEXT,
    collection_month      INTEGER CHECK(collection_month BETWEEN 1 AND 12),
    collection_year       INTEGER,
    responsible_party     TEXT
);

-- Module D: Raw Data Analysis — one row per logframe indicator in the current
-- monitoring cycle. logframe_row_id links back to logframe_rows for the
-- indicator statement and target. Modules F and G join on this table.
CREATE TABLE IF NOT EXISTS raw_data_analysis (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    logframe_row_id     INTEGER REFERENCES logframe_rows(id) ON DELETE SET NULL,
    data_type           TEXT    CHECK(data_type IN (
                            'Process','Performance','Assumption',
                            'Stakeholder','Problem','Solution','Attribution'
                        )),
    target_value        TEXT,
    trigger_value       TEXT,
    problem_definition  TEXT,
    baseline_collected  TEXT    CHECK(baseline_collected IN ('Y','N')),
    baseline_value      TEXT,
    actual_q1           TEXT,
    actual_q2           TEXT,
    actual_q3           TEXT,
    actual_q4           TEXT,
    actual_year         TEXT,
    indicator_status    TEXT    CHECK(indicator_status IN (
                            'Data not collected yet',
                            'Data currently being collected/analysed',
                            'Completed - on track',
                            'Completed - not on track'
                        )),
    action_status       TEXT    CHECK(action_status IN (
                            'No action needed - data reporting only',
                            'Inform decision-maker/confirm next steps',
                            'Follow-up or investigate',
                            'Change/adapt/revise',
                            'Resolved'
                        )),
    action_description  TEXT,
    last_updated        TEXT,
    updated_by          TEXT
);

-- Module E: Kobo form field-to-indicator mapping.
-- One row per (form × Kobo field) pair. logframe_row_id bridges
-- the Kobo field value into raw_data_analysis.actual_q[N].
CREATE TABLE IF NOT EXISTS kobo_form_mapping (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    asset_uid       TEXT    NOT NULL,
    kobo_form_name  TEXT,
    kobo_field_name TEXT    NOT NULL,
    logframe_row_id INTEGER REFERENCES logframe_rows(id) ON DELETE SET NULL,
    transform       TEXT    CHECK(transform IN ('count','sum','mean','latest'))
);

-- Module E: Audit log — one row per sync attempt per form.
CREATE TABLE IF NOT EXISTS kobo_sync_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    asset_uid      TEXT    NOT NULL,
    synced_at      TEXT    NOT NULL,
    records_pulled INTEGER,
    status         TEXT    CHECK(status IN ('success','error','partial')),
    error_message  TEXT
);

-- Module F: Review Protocols — one row per data_type (7 fixed rows).
-- Admin-only editable; next_scheduled_date auto-advances after each log entry.
CREATE TABLE IF NOT EXISTS review_protocols (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id           INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    data_type            TEXT    NOT NULL,
    review_scope         TEXT,
    existing_info_source TEXT,
    actual_info_source   TEXT,
    issue_definition     TEXT,
    review_frequency     TEXT,
    reviewer_role        TEXT,
    next_scheduled_date  TEXT    -- ISO-8601 date: YYYY-MM-DD
);

-- Module F: Review Log — append-only; each row records one conducted review.
-- linked_indicator_ids: comma-separated logframe_rows.id values.
CREATE TABLE IF NOT EXISTS review_log (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    protocol_id          INTEGER REFERENCES review_protocols(id) ON DELETE CASCADE,
    conducted_date       TEXT,
    conducted_by         TEXT,
    summary              TEXT,
    red_flags_found      TEXT,
    linked_indicator_ids TEXT,
    follow_up_required   TEXT    CHECK(follow_up_required IN ('Y','N'))
);

-- Indexes for the join patterns every module uses.
CREATE INDEX IF NOT EXISTS idx_partners_project   ON partners(project_id);
CREATE INDEX IF NOT EXISTS idx_indicators_project ON indicators(project_id);
CREATE INDEX IF NOT EXISTS idx_data_points_ind    ON data_points(indicator_id);
CREATE INDEX IF NOT EXISTS idx_data_points_yr_q   ON data_points(year, quarter);
CREATE INDEX IF NOT EXISTS idx_ptargets_project   ON partner_targets(project_id);
CREATE INDEX IF NOT EXISTS idx_ptargets_partner   ON partner_targets(partner_id);
CREATE INDEX IF NOT EXISTS idx_toc_project        ON toc_nodes(project_id);
CREATE INDEX IF NOT EXISTS idx_lf_project         ON logframe_rows(project_id);
CREATE INDEX IF NOT EXISTS idx_lf_level           ON logframe_rows(result_level);
CREATE INDEX IF NOT EXISTS idx_changelog_row      ON logframe_changelog(row_id);
CREATE INDEX IF NOT EXISTS idx_dcp_project        ON data_collection_plan(project_id);
CREATE INDEX IF NOT EXISTS idx_dcp_journey        ON data_collection_plan(journey_step);
CREATE INDEX IF NOT EXISTS idx_rda_project        ON raw_data_analysis(project_id);
CREATE INDEX IF NOT EXISTS idx_rda_lf_row         ON raw_data_analysis(logframe_row_id);
CREATE INDEX IF NOT EXISTS idx_rda_action         ON raw_data_analysis(action_status);
CREATE INDEX IF NOT EXISTS idx_kfm_project        ON kobo_form_mapping(project_id);
CREATE INDEX IF NOT EXISTS idx_kfm_uid            ON kobo_form_mapping(asset_uid);
CREATE INDEX IF NOT EXISTS idx_ksl_project        ON kobo_sync_log(project_id);
CREATE INDEX IF NOT EXISTS idx_ksl_uid            ON kobo_sync_log(asset_uid);
-- Module G: Decision Reports — one report per investigation finding.
-- logframe_row_id implements the spec's indicator_id for SAWA (indicators table is empty).
CREATE TABLE IF NOT EXISTS decision_reports (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id           INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    created_date         TEXT,
    created_by           TEXT,
    logframe_row_id      INTEGER REFERENCES logframe_rows(id) ON DELETE SET NULL,
    target_value         TEXT,
    indicator_definition TEXT,
    assumed_pattern      TEXT,
    actual_value         TEXT,
    review_category      TEXT,
    specific_focus_area  TEXT,
    investigation_notes  TEXT,
    key_finding          TEXT,
    status               TEXT CHECK(status IN ('Draft','Under review','Approved','Closed'))
);

-- Module G: Actions — one-to-many from decision_reports.
CREATE TABLE IF NOT EXISTS decision_actions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id       INTEGER NOT NULL REFERENCES decision_reports(id) ON DELETE CASCADE,
    decision_maker  TEXT,
    action          TEXT,
    action_due_date TEXT,
    action_status   TEXT CHECK(action_status IN (
                        'No action needed - data reporting only',
                        'Inform decision-maker/confirm next steps',
                        'Follow-up or investigate',
                        'Change/adapt/revise',
                        'Resolved'
                    ))
);

-- Module E: Evidence attachments — one row per document or link per indicator.
-- file_data is nullable; link_url is nullable; at least one must be provided.
CREATE TABLE IF NOT EXISTS evidence (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    logframe_row_id INTEGER REFERENCES logframe_rows(id) ON DELETE CASCADE,
    quarter         TEXT    CHECK(quarter IN ('Q1','Q2','Q3','Q4','Annual')),
    year            INTEGER,
    label           TEXT    NOT NULL,
    link_url        TEXT,
    file_name       TEXT,
    file_mime       TEXT,
    file_data       BLOB,
    uploaded_by     TEXT,
    uploaded_at     TEXT    -- ISO-8601 datetime
);

CREATE INDEX IF NOT EXISTS idx_evidence_project ON evidence(project_id);
CREATE INDEX IF NOT EXISTS idx_evidence_lf_row  ON evidence(logframe_row_id);

CREATE INDEX IF NOT EXISTS idx_rp_project         ON review_protocols(project_id);
CREATE INDEX IF NOT EXISTS idx_rp_data_type       ON review_protocols(data_type);
CREATE INDEX IF NOT EXISTS idx_rl_protocol        ON review_log(protocol_id);
CREATE INDEX IF NOT EXISTS idx_rl_date            ON review_log(conducted_date);
CREATE INDEX IF NOT EXISTS idx_dr_project         ON decision_reports(project_id);
CREATE INDEX IF NOT EXISTS idx_dr_lf_row          ON decision_reports(logframe_row_id);
CREATE INDEX IF NOT EXISTS idx_da_report          ON decision_actions(report_id);
CREATE INDEX IF NOT EXISTS idx_da_status          ON decision_actions(action_status);

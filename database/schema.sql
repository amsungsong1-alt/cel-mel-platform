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
    logframe_row_id       INTEGER REFERENCES logframe_rows(id) ON DELETE SET NULL,
    stakeholder           TEXT    NOT NULL,
    indicator_statement   TEXT    NOT NULL,
    data_points           TEXT,
    rationale             TEXT,
    instrument_name       TEXT,
    instrument_status     TEXT    CHECK(instrument_status IN ('New', 'Existing')),
    instrument_link       TEXT,
    journey_step          TEXT,
    integration_mechanism TEXT,
    frequency             TEXT,
    collection_month      INTEGER CHECK(collection_month BETWEEN 1 AND 12),
    collection_year       INTEGER,
    responsible_party     TEXT,
    last_collected_date   TEXT    -- ISO-8601 date: YYYY-MM-DD; NULL = never recorded
);

-- Module D: Raw Data Analysis — one row per logframe indicator in the current
-- monitoring cycle. logframe_row_id links back to logframe_rows for the
-- indicator statement and target. Modules F and G join on this table.
CREATE TABLE IF NOT EXISTS raw_data_analysis (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    logframe_row_id     INTEGER REFERENCES logframe_rows(id) ON DELETE SET NULL,
    -- Calendar year the programme's fiscal year STARTS in (SAWA: Jul-Jun,
    -- so FY2026 = Jul 2026-Jun 2027). One row per (project, logframe_row,
    -- reporting_year) — without this, a second year's actuals would
    -- overwrite the first year's in the same actual_q1..q4 cells. NULL on
    -- rows created before this column existed; treat NULL as "the only
    -- year that existed at the time" when querying.
    reporting_year      INTEGER,
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
    updated_by          TEXT,
    -- MCF Shared Measures 2.0 progression stage (SM1=WEO, SM5=YIW, SM6=D&F).
    progression_stage   TEXT    CHECK(progression_stage IN ('WEO','YIW','D&F')),
    -- SAWA intervention pillar this indicator belongs to.
    pillar              TEXT    CHECK(pillar IN (
                            'Capacity Building & Inclusion',
                            'Production Expansion & Productivity',
                            'Value Addition & Market Systems',
                            'Ecosystem Strengthening',
                            'Programme-wide'
                        )),
    -- DQA 3-stage verification status per AIL DQA framework.
    dqa_stage           TEXT    CHECK(dqa_stage IN (
                            'Raw',
                            'Completeness Checked',
                            'Traceability Verified',
                            'Outcome Validated'
                        )),
    -- AIL disaggregation (JSON): {"q1":{"f":"","m":"","youth":"","pwd":""},...}
    -- Breakdowns for Total/Female/Male/Youth/PWD per quarter per reporting standard.
    disaggregation      TEXT,
    -- NULL = programme-wide aggregate row; set to a partners.partner_id for
    -- partner-disaggregated rows (X1 — partner-level reporting).
    partner_id          INTEGER REFERENCES partners(partner_id) ON DELETE SET NULL
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
    transform       TEXT    CHECK(transform IN ('count','count_yes','count_no','sum','mean','latest'))
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
-- idx_rda_partner is created in _run_migrations() after ADD COLUMN partner_id
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

-- Module I: Strategic Plan 2025-2030 — links a programme's logframe
-- indicator (or its budget_total) into one of the six CEL strategic
-- outcomes, so the dashboard can auto-aggregate across SAWA and any
-- future programme without code changes. outcome_code values are defined
-- in utils/strategic_outcomes.py.
--
-- Caution on 'project_budget_total': only use it for the FINANCE outcome
-- if the programme's budget is money CEL itself mobilised. A jointly
-- funded programme's total budget (e.g. SAWA, split across several
-- implementing partners) is not attributable to CEL alone — use a manual
-- entry (strategic_outcome_manual) instead in that case.
CREATE TABLE IF NOT EXISTS strategic_outcome_links (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    outcome_code    TEXT    NOT NULL,
    project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    logframe_row_id INTEGER REFERENCES logframe_rows(id) ON DELETE CASCADE,
    source          TEXT    NOT NULL CHECK(source IN ('indicator_actual_year', 'project_budget_total')),
    note            TEXT
);

-- Manually entered figures for outcome/project combinations with no
-- automatic indicator link (e.g. finance mobilised outside the logframe,
-- or enterprise pilots tracked by a separate research team).
-- project_id NULL = an org-wide figure not tied to one programme.
CREATE TABLE IF NOT EXISTS strategic_outcome_manual (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    outcome_code TEXT    NOT NULL,
    project_id   INTEGER REFERENCES projects(project_id) ON DELETE CASCADE,
    value        REAL    NOT NULL,
    note         TEXT,
    updated_by   TEXT,
    updated_at   TEXT
);

CREATE INDEX IF NOT EXISTS idx_sol_outcome       ON strategic_outcome_links(outcome_code);
CREATE INDEX IF NOT EXISTS idx_sol_project       ON strategic_outcome_links(project_id);
CREATE INDEX IF NOT EXISTS idx_som_outcome       ON strategic_outcome_manual(outcome_code);

CREATE INDEX IF NOT EXISTS idx_rp_project         ON review_protocols(project_id);
CREATE INDEX IF NOT EXISTS idx_rp_data_type       ON review_protocols(data_type);
CREATE INDEX IF NOT EXISTS idx_rl_protocol        ON review_log(protocol_id);
CREATE INDEX IF NOT EXISTS idx_rl_date            ON review_log(conducted_date);
CREATE INDEX IF NOT EXISTS idx_dr_project         ON decision_reports(project_id);
CREATE INDEX IF NOT EXISTS idx_dr_lf_row          ON decision_reports(logframe_row_id);
CREATE INDEX IF NOT EXISTS idx_da_report          ON decision_actions(report_id);
CREATE INDEX IF NOT EXISTS idx_da_status          ON decision_actions(action_status);

-- Module A: Workplan Activities — one row per partner deliverable per quarter.
-- partner_id NULL = programme-wide / CEL-led activity.
-- fiscal_year is the start year of the fiscal year (e.g. 2026 = FY 2026/27).
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
);

CREATE INDEX IF NOT EXISTS idx_wa_project ON workplan_activities(project_id);
CREATE INDEX IF NOT EXISTS idx_wa_partner ON workplan_activities(partner_id);
CREATE INDEX IF NOT EXISTS idx_wa_quarter ON workplan_activities(quarter, fiscal_year);

-- Module J: Partner Visitations — one row per scheduled or completed field visit.
CREATE TABLE IF NOT EXISTS partner_visits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id    INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    partner_id    INTEGER REFERENCES partners(partner_id) ON DELETE SET NULL,
    visit_date    TEXT    NOT NULL,   -- ISO-8601: YYYY-MM-DD
    visit_type    TEXT    CHECK(visit_type IN ('In-person','Remote','Joint')),
    conducted_by  TEXT,
    status        TEXT    DEFAULT 'Scheduled'
                  CHECK(status IN ('Pending','Scheduled','Completed','Cancelled')),
    general_notes TEXT,
    created_at    TEXT    NOT NULL
);

-- Module J: Needs assessment — one row per visit capturing partner M&E capability.
CREATE TABLE IF NOT EXISTS visit_findings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id            INTEGER NOT NULL REFERENCES partner_visits(id) ON DELETE CASCADE,
    mel_focal_person    TEXT,
    mel_focal_email     TEXT,
    existing_tools      TEXT,
    data_storage        TEXT,
    disagg_sex          TEXT    CHECK(disagg_sex IN ('Y','N','Partial')),
    disagg_age          TEXT    CHECK(disagg_age IN ('Y','N','Partial')),
    disagg_disability   TEXT    CHECK(disagg_disability IN ('Y','N','Partial')),
    disagg_value_chain  TEXT    CHECK(disagg_value_chain IN ('Y','N','Partial')),
    reporting_frequency TEXT,
    reporting_format    TEXT,
    communities_served  TEXT,
    overlap_risk        TEXT    CHECK(overlap_risk IN ('Low','Medium','High')),
    overlap_notes       TEXT,
    indicators_confirmed TEXT,   -- comma-separated indicator_codes
    discrepancies_found TEXT,
    support_agreed      TEXT,
    support_notes       TEXT
);

-- Module J: Evidence files and links per visit, tagged to logframe indicators.
CREATE TABLE IF NOT EXISTS visit_evidence (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id        INTEGER NOT NULL REFERENCES partner_visits(id) ON DELETE CASCADE,
    project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    logframe_row_id INTEGER REFERENCES logframe_rows(id) ON DELETE SET NULL,
    label           TEXT    NOT NULL,
    link_url        TEXT,
    file_name       TEXT,
    file_mime       TEXT,
    file_data       BLOB,
    uploaded_by     TEXT,
    uploaded_at     TEXT    -- ISO-8601 datetime
);

CREATE INDEX IF NOT EXISTS idx_pv_project  ON partner_visits(project_id);
CREATE INDEX IF NOT EXISTS idx_pv_partner  ON partner_visits(partner_id);
CREATE INDEX IF NOT EXISTS idx_vf_visit    ON visit_findings(visit_id);
CREATE INDEX IF NOT EXISTS idx_ve_visit    ON visit_evidence(visit_id);
CREATE INDEX IF NOT EXISTS idx_ve_project  ON visit_evidence(project_id);

-- Module K: Team Workspace — tasks and evidence files per CEL team role.
CREATE TABLE IF NOT EXISTS team_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    team_role       TEXT    NOT NULL,
    task            TEXT    NOT NULL,
    description     TEXT,
    status          TEXT    DEFAULT 'Not Started'
                    CHECK(status IN ('Not Started','In Progress','Complete','Blocked')),
    due_date        TEXT,
    assigned_to     TEXT,
    logframe_row_id INTEGER REFERENCES logframe_rows(id) ON DELETE SET NULL,
    created_at      TEXT    NOT NULL,
    created_by      TEXT
);

CREATE TABLE IF NOT EXISTS team_files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    team_role       TEXT    NOT NULL,
    label           TEXT    NOT NULL,
    description     TEXT,
    logframe_row_id INTEGER REFERENCES logframe_rows(id) ON DELETE SET NULL,
    link_url        TEXT,
    file_name       TEXT,
    file_mime       TEXT,
    file_data       BLOB,
    uploaded_by     TEXT,
    uploaded_at     TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tt_project ON team_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tt_role    ON team_tasks(team_role);
CREATE INDEX IF NOT EXISTS idx_tf_project ON team_files(project_id);
CREATE INDEX IF NOT EXISTS idx_tf_role    ON team_files(team_role);

-- Module K: Time tracking — one row per time entry per role (for monthly timesheets).
CREATE TABLE IF NOT EXISTS team_time_entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    team_role   TEXT    NOT NULL,
    entry_date  TEXT    NOT NULL,   -- ISO-8601 YYYY-MM-DD
    hours       REAL    NOT NULL CHECK(hours > 0),
    activity    TEXT    NOT NULL,
    task_id     INTEGER REFERENCES team_tasks(id) ON DELETE SET NULL,
    logged_by   TEXT,
    created_at  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tte_project ON team_time_entries(project_id);
CREATE INDEX IF NOT EXISTS idx_tte_role    ON team_time_entries(team_role);
CREATE INDEX IF NOT EXISTS idx_tte_date    ON team_time_entries(entry_date);

-- Module K: auto-logged activity events (task update/add, file add) that
-- drive the Time tab's Daily Activity chart — an action-count proxy, not a
-- time-tracking measurement (Streamlit can't measure page-open duration).
CREATE TABLE IF NOT EXISTS team_activity_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    team_role   TEXT    NOT NULL,
    action_type TEXT    NOT NULL,
    logged_by   TEXT,
    logged_at   TEXT    NOT NULL   -- ISO-8601 timestamp, UTC
);

CREATE INDEX IF NOT EXISTS idx_tal_project ON team_activity_log(project_id);
CREATE INDEX IF NOT EXISTS idx_tal_role    ON team_activity_log(team_role);
CREATE INDEX IF NOT EXISTS idx_tal_date    ON team_activity_log(logged_at);

-- Module L: Participant Register — one row per registered participant.
-- Captures all breakdowns required by the quarterly narrative report
-- (fish type, location type, employment status, primary/secondary, PWD, refugee).
CREATE TABLE IF NOT EXISTS participant_register (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    partner_id          INTEGER REFERENCES partners(partner_id) ON DELETE SET NULL,
    participant_code    TEXT,          -- unique within a programme; Kobo submission_id or registry ID
    registration_date   TEXT NOT NULL, -- YYYY-MM-DD
    fiscal_year         INTEGER,
    quarter             INTEGER CHECK(quarter IN (1,2,3,4)),
    full_name           TEXT,          -- optional (privacy)
    sex                 TEXT CHECK(sex IN ('Female','Male','Prefer not to say')),
    age_group           TEXT CHECK(age_group IN ('Under 18','18-24','25-29','30-35','35+')),
    is_youth            TEXT CHECK(is_youth IN ('Y','N')),
    is_pwd              TEXT CHECK(is_pwd IN ('Y','N')),
    refugee_displaced   TEXT CHECK(refugee_displaced IN ('Y','N','Unknown')),
    fish_type           TEXT CHECK(fish_type IN ('Tilapia','Catfish','Both','Other')),
    value_chain_role    TEXT,          -- Producer / Processor / Trader / Other
    location_type       TEXT CHECK(location_type IN ('Rural','Urban','Peri-urban')),
    region              TEXT,
    district            TEXT,
    community           TEXT,
    employment_status   TEXT CHECK(employment_status IN ('New','Improved','Additional')),
    primary_secondary   TEXT CHECK(primary_secondary IN ('Primary','Secondary')),
    intervention_type   TEXT CHECK(intervention_type IN (
                            'BDS','WAN','Safeguarding','Coaching','E-SAWA','Starter pack','Other'
                        )),
    progression_stage   TEXT CHECK(progression_stage IN ('WEO','YIW','D&F')),
    wan_member          TEXT CHECK(wan_member IN ('Y','N')),
    kobo_submission_id  TEXT,
    registered_by       TEXT,
    notes               TEXT,
    created_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pr_project  ON participant_register(project_id);
CREATE INDEX IF NOT EXISTS idx_pr_partner  ON participant_register(partner_id);
CREATE INDEX IF NOT EXISTS idx_pr_quarter  ON participant_register(fiscal_year, quarter);
CREATE INDEX IF NOT EXISTS idx_pr_fish     ON participant_register(fish_type);
CREATE INDEX IF NOT EXISTS idx_pr_stage    ON participant_register(progression_stage);

-- Module L: MEL Activities log — one row per MEL activity in the quarter.
-- Feeds §3.1 Quarterly MEL Activities in the narrative report.
CREATE TABLE IF NOT EXISTS mel_activities (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    activity_date   TEXT NOT NULL,    -- YYYY-MM-DD
    quarter         INTEGER CHECK(quarter IN (1,2,3,4)),
    fiscal_year     INTEGER,
    activity_type   TEXT CHECK(activity_type IN (
                        'Field visit','FGD','Partner visit','Kobo review',
                        'Pre/post test','Data quality check','Learning session','Other'
                    )),
    location        TEXT,
    partner_id      INTEGER REFERENCES partners(partner_id) ON DELETE SET NULL,
    objective       TEXT NOT NULL,
    participants    TEXT,             -- who was involved (comma-separated roles/names)
    key_findings    TEXT,
    follow_up       TEXT,
    conducted_by    TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ma_project ON mel_activities(project_id);
CREATE INDEX IF NOT EXISTS idx_ma_quarter ON mel_activities(fiscal_year, quarter);

-- Module L: Learnings — covers both §6.1 (programme learnings) and
-- §6.2 (influencing points for Mastercard Foundation).
CREATE TABLE IF NOT EXISTS learnings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    quarter         INTEGER CHECK(quarter IN (1,2,3,4)),
    fiscal_year     INTEGER,
    learning_type   TEXT CHECK(learning_type IN ('Learning','Influencing point')),
    category        TEXT,             -- theme/thematic area
    statement       TEXT NOT NULL,    -- the learning or influencing point itself
    evidence        TEXT,             -- what supports this learning
    implication     TEXT,             -- so what? what does this mean?
    audience        TEXT,             -- for influencing points: Mastercard, donor, etc.
    reason          TEXT,             -- why this matters to the audience
    created_by      TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lrn_project ON learnings(project_id);
CREATE INDEX IF NOT EXISTS idx_lrn_quarter ON learnings(fiscal_year, quarter);
CREATE INDEX IF NOT EXISTS idx_lrn_type    ON learnings(learning_type);

-- Module L: Quarterly Report Actuals — one row per indicator per quarter per
-- fiscal year for the §7 technical reconciliation table. Stores CEL actuals
-- separately from raw_data_analysis because the reconciliation needs tilapia/
-- catfish fish-type breakdowns and a fixed set of CEL-owned indicators.
-- UNIQUE constraint prevents duplicate rows per (project, year, indicator).
CREATE TABLE IF NOT EXISTS qr_actuals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    fiscal_year         INTEGER NOT NULL,
    submitting_org      TEXT NOT NULL DEFAULT 'CEL',  -- 'CEL' | 'TechnoServe' | partner name
    indicator_code      TEXT NOT NULL,    -- e.g. 'PIII.R1', 'I.3', 'II.R7'
    indicator_label     TEXT NOT NULL,    -- human-readable label
    unit                TEXT,             -- persons / MT / USD / groups / enterprises
    target_y1           TEXT,             -- Year 1 annual target
    target_q1           TEXT,             -- Planned Q1 target (from workplan)
    target_q2           TEXT,
    target_q3           TEXT,
    target_q4           TEXT,
    actual_q1           TEXT,
    actual_q1_tilapia   TEXT,
    actual_q1_catfish   TEXT,
    actual_q2           TEXT,
    actual_q2_tilapia   TEXT,
    actual_q2_catfish   TEXT,
    actual_q3           TEXT,
    actual_q3_tilapia   TEXT,
    actual_q3_catfish   TEXT,
    actual_q4           TEXT,
    actual_q4_tilapia   TEXT,
    actual_q4_catfish   TEXT,
    notes               TEXT,
    updated_by          TEXT,
    updated_at          TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_qra_key ON qr_actuals(project_id, fiscal_year, indicator_code, submitting_org);
CREATE INDEX IF NOT EXISTS idx_qra_project  ON qr_actuals(project_id);
CREATE INDEX IF NOT EXISTS idx_qra_year     ON qr_actuals(fiscal_year);

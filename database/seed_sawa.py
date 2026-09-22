"""Seed the database with SAWA project data.

Run once from the project root:
    python -m database.seed_sawa
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, insert_returning_id, run_query, run_write
from projects.sawa import (
    PROJECT, PARTNERS, PARTNER_TARGETS, INDICATORS,
    TOC_NODES, LOGFRAME_ROWS, DATA_COLLECTION_PLAN,
    RAW_DATA_ANALYSIS, KOBO_FORM_MAPPINGS, REVIEW_PROTOCOLS,
    DECISION_REPORTS,
)


def seed():
    init_db()

    # ── Project ───────────────────────────────────────────────────────────────
    existing = run_query(
        "SELECT project_id FROM projects WHERE name = :name", {"name": PROJECT["name"]}
    )
    if existing:
        project_id = existing[0]["project_id"]
        print(f"SAWA project already exists (project_id={project_id}).")
    else:
        project_id = insert_returning_id(
            """INSERT INTO projects (name, donor, budget_total, start_date, end_date)
               VALUES (:name, :donor, :budget_total, :start_date, :end_date)""",
            PROJECT,
        )
        print(f"Project inserted: project_id={project_id}")

    # ── Partners ──────────────────────────────────────────────────────────────
    partner_id_map: dict[str, int] = {}
    for partner in PARTNERS:
        ex = run_query(
            "SELECT partner_id FROM partners WHERE project_id=:pid AND name=:name",
            {"pid": project_id, "name": partner["name"]},
        )
        if ex:
            partner_id_map[partner["name"]] = ex[0]["partner_id"]
        else:
            pid = insert_returning_id(
                """INSERT INTO partners (project_id, name, role, tier)
                   VALUES (:project_id, :name, :role, :tier)""",
                {**partner, "project_id": project_id},
            )
            partner_id_map[partner["name"]] = pid
    print(f"Partners: {len(partner_id_map)} ready.")

    # ── Partner targets ───────────────────────────────────────────────────────
    run_write("DELETE FROM partner_targets WHERE project_id = :pid", {"pid": project_id})
    for pt in PARTNER_TARGETS:
        partner_id = partner_id_map.get(pt["partner_name"]) if pt["partner_name"] else None
        insert_returning_id(
            """INSERT INTO partner_targets
               (partner_id, project_id, level, metric_label, target_value, unit,
                time_basis, source_doc, source_page)
               VALUES (:partner_id, :project_id, :level, :metric_label,
                       :target_value, :unit, :time_basis, :source_doc, :source_page)""",
            {
                "partner_id":   partner_id,
                "project_id":   project_id,
                "level":        pt["level"],
                "metric_label": pt["metric_label"],
                "target_value": pt["target_value"],
                "unit":         pt["unit"],
                "time_basis":   pt["time_basis"],
                "source_doc":   pt["source_doc"],
                "source_page":  pt["source_page"],
            },
        )
    print(f"Partner targets: {len(PARTNER_TARGETS)} inserted.")

    # ── ToC nodes ─────────────────────────────────────────────────────────────
    run_write("DELETE FROM toc_nodes WHERE project_id = :pid", {"pid": project_id})

    key_to_db_id: dict[str, int] = {}
    for node in TOC_NODES:
        parent_db_id = key_to_db_id.get(node["parent_key"]) if node["parent_key"] else None
        db_id = insert_returning_id(
            """INSERT INTO toc_nodes
               (project_id, level, statement, parent_id, source_verified, source_note)
               VALUES (:project_id, :level, :statement, :parent_id,
                       :source_verified, :source_note)""",
            {
                "project_id":      project_id,
                "level":           node["level"],
                "statement":       node["statement"],
                "parent_id":       parent_db_id,
                "source_verified": node.get("source_verified", True),
                "source_note":     node.get("source_note"),
            },
        )
        key_to_db_id[node["key"]] = db_id
    print(f"ToC nodes: {len(TOC_NODES)} inserted.")

    # ── Logframe rows ─────────────────────────────────────────────────────────
    run_write("DELETE FROM logframe_rows WHERE project_id = :pid", {"pid": project_id})
    for row in LOGFRAME_ROWS:
        insert_returning_id(
            """INSERT INTO logframe_rows
               (project_id, indicator_code, result_level, indicator_statement,
                disaggregation, baseline_value, target_annual, target_lop,
                means_of_verification, frequency, responsible, critical_assumption)
               VALUES (:project_id, :indicator_code, :result_level, :indicator_statement,
                       :disaggregation, :baseline_value, :target_annual, :target_lop,
                       :means_of_verification, :frequency, :responsible, :critical_assumption)""",
            {**row, "project_id": project_id},
        )
    print(f"Logframe rows: {len(LOGFRAME_ROWS)} inserted.")

    # ── Indicators master (Module B onward) ───────────────────────────────────
    for indicator in INDICATORS:
        insert_returning_id(
            """INSERT INTO indicators
               (project_id, pillar, level, statement, target_value, unit)
               VALUES (:project_id, :pillar, :level, :statement, :target_value, :unit)""",
            {**indicator, "project_id": project_id},
        )
    if INDICATORS:
        print(f"Indicators: {len(INDICATORS)} inserted.")

    # ── Raw data analysis (Module D) ─────────────────────────────────────────
    run_write("DELETE FROM raw_data_analysis WHERE project_id = :pid", {"pid": project_id})
    # Build indicator_code → logframe_row_id lookup
    lf_lookup: dict[str, int] = {
        r["indicator_code"]: r["id"]
        for r in run_query(
            "SELECT id, indicator_code FROM logframe_rows WHERE project_id=:pid",
            {"pid": project_id},
        )
        if r["indicator_code"]
    }
    for row in RAW_DATA_ANALYSIS:
        lf_id = lf_lookup.get(row["indicator_code"])
        insert_returning_id(
            """INSERT INTO raw_data_analysis
               (project_id, logframe_row_id, data_type, target_value, trigger_value,
                problem_definition, baseline_collected, baseline_value,
                actual_q1, actual_q2, actual_q3, actual_q4, actual_year,
                indicator_status, action_status, action_description)
               VALUES (:project_id, :logframe_row_id, :data_type, :target_value, :trigger_value,
                       :problem_definition, :baseline_collected, :baseline_value,
                       :actual_q1, :actual_q2, :actual_q3, :actual_q4, :actual_year,
                       :indicator_status, :action_status, :action_description)""",
            {
                "project_id":       project_id,
                "logframe_row_id":  lf_id,
                "data_type":        row["data_type"],
                "target_value":     row["target_value"],
                "trigger_value":    row["trigger_value"],
                "problem_definition": row["problem_definition"],
                "baseline_collected": row["baseline_collected"],
                "baseline_value":   row["baseline_value"],
                "actual_q1":        row["actual_q1"],
                "actual_q2":        row["actual_q2"],
                "actual_q3":        row["actual_q3"],
                "actual_q4":        row["actual_q4"],
                "actual_year":      row["actual_year"],
                "indicator_status": row["indicator_status"],
                "action_status":    row["action_status"],
                "action_description": row["action_description"],
            },
        )
    print(f"Raw data analysis: {len(RAW_DATA_ANALYSIS)} rows inserted.")

    # ── Kobo form mappings (Module E) ────────────────────────────────────────
    run_write("DELETE FROM kobo_form_mapping WHERE project_id = :pid", {"pid": project_id})
    for row in KOBO_FORM_MAPPINGS:
        lf_id = lf_lookup.get(row["indicator_code"])
        insert_returning_id(
            """INSERT INTO kobo_form_mapping
               (project_id, asset_uid, kobo_form_name, kobo_field_name,
                logframe_row_id, transform)
               VALUES (:project_id, :asset_uid, :kobo_form_name, :kobo_field_name,
                       :logframe_row_id, :transform)""",
            {
                "project_id":       project_id,
                "asset_uid":        row["asset_uid"],
                "kobo_form_name":   row["kobo_form_name"],
                "kobo_field_name":  row["kobo_field_name"],
                "logframe_row_id":  lf_id,
                "transform":        row["transform"],
            },
        )
    print(f"Kobo form mappings: {len(KOBO_FORM_MAPPINGS)} rows inserted.")

    # ── Decision reports (Module G) ──────────────────────────────────────────
    run_write("DELETE FROM decision_actions WHERE report_id IN "
              "(SELECT id FROM decision_reports WHERE project_id=:pid)", {"pid": project_id})
    run_write("DELETE FROM decision_reports WHERE project_id = :pid", {"pid": project_id})
    for row in DECISION_REPORTS:
        lf_id = lf_lookup.get(row["indicator_code"])
        report_id = insert_returning_id(
            """INSERT INTO decision_reports
               (project_id, created_date, created_by, logframe_row_id,
                target_value, indicator_definition, assumed_pattern, actual_value,
                review_category, specific_focus_area, investigation_notes,
                key_finding, status)
               VALUES (:project_id, :created_date, :created_by, :logframe_row_id,
                       :target_value, :indicator_definition, :assumed_pattern, :actual_value,
                       :review_category, :specific_focus_area, :investigation_notes,
                       :key_finding, :status)""",
            {
                "project_id":          project_id,
                "created_date":        row["created_date"],
                "created_by":          row["created_by"],
                "logframe_row_id":     lf_id,
                "target_value":        row["target_value"],
                "indicator_definition": row["indicator_definition"],
                "assumed_pattern":     row["assumed_pattern"],
                "actual_value":        row["actual_value"],
                "review_category":     row["review_category"],
                "specific_focus_area": row["specific_focus_area"],
                "investigation_notes": row["investigation_notes"],
                "key_finding":         row["key_finding"],
                "status":              row["status"],
            },
        )
        for action in row.get("actions", []):
            insert_returning_id(
                """INSERT INTO decision_actions
                   (report_id, decision_maker, action, action_due_date, action_status)
                   VALUES (:rid, :dm, :action, :due, :status)""",
                {
                    "rid":    report_id,
                    "dm":     action["decision_maker"],
                    "action": action["action"],
                    "due":    action["action_due_date"],
                    "status": action["action_status"],
                },
            )
    total_actions = sum(len(r.get("actions", [])) for r in DECISION_REPORTS)
    print(f"Decision reports: {len(DECISION_REPORTS)} inserted, {total_actions} action(s).")

    # ── Review protocols (Module F) ──────────────────────────────────────────
    run_write("DELETE FROM review_protocols WHERE project_id = :pid", {"pid": project_id})
    for row in REVIEW_PROTOCOLS:
        insert_returning_id(
            """INSERT INTO review_protocols
               (project_id, data_type, review_scope, existing_info_source,
                actual_info_source, issue_definition, review_frequency,
                reviewer_role, next_scheduled_date)
               VALUES (:project_id, :data_type, :review_scope, :existing_info_source,
                       :actual_info_source, :issue_definition, :review_frequency,
                       :reviewer_role, :next_scheduled_date)""",
            {**row, "project_id": project_id},
        )
    print(f"Review protocols: {len(REVIEW_PROTOCOLS)} rows inserted.")

    # ── Data collection plan (Module C) ──────────────────────────────────────
    run_write("DELETE FROM data_collection_plan WHERE project_id = :pid", {"pid": project_id})
    for row in DATA_COLLECTION_PLAN:
        insert_returning_id(
            """INSERT INTO data_collection_plan
               (project_id, stakeholder, indicator_statement, data_points,
                rationale, instrument_status, instrument_link, journey_step,
                integration_mechanism, frequency, collection_month,
                collection_year, responsible_party)
               VALUES (:project_id, :stakeholder, :indicator_statement, :data_points,
                       :rationale, :instrument_status, :instrument_link, :journey_step,
                       :integration_mechanism, :frequency, :collection_month,
                       :collection_year, :responsible_party)""",
            {**row, "project_id": project_id},
        )
    print(f"Data collection plan: {len(DATA_COLLECTION_PLAN)} instruments inserted.")

    # ── Strategic outcome links (Module I) ────────────────────────────────────
    # Wires SAWA's logframe indicators (and programme budget) into CEL's six
    # 2025-2030 strategic outcomes. See utils/strategic_outcomes.py for the
    # target definitions and database/schema.sql for the table shape.
    run_write("DELETE FROM strategic_outcome_links WHERE project_id = :pid", {"pid": project_id})
    STRATEGIC_OUTCOME_LINKS = [
        {"outcome_code": "JOBS", "indicator_code": "LoP.1", "source": "indicator_actual_year",
         "note": "Young women/PWDs engaged in dignified, fulfilling work (LoP target 60,000)."},
        {"outcome_code": "REVENUE", "indicator_code": "PII.R7", "source": "indicator_actual_year",
         "note": "Revenue (USD) generated by PWDs accessing D&F in the aquaculture value chain."},
        {"outcome_code": "REVENUE", "indicator_code": "PIII.R3", "source": "indicator_actual_year",
         "note": "Revenue (USD) from trading value-added aquaculture products (LoP target $90M/yr)."},
        {"outcome_code": "SMES", "indicator_code": "PIII.6", "source": "indicator_actual_year",
         "note": "Proxy only — counts cooperatives/clusters strengthened, not individual SME headcount."},
        {"outcome_code": "FINANCE", "indicator_code": None, "source": "project_budget_total",
         "note": "SAWA programme budget as a proxy for funds mobilised toward this programme."},
    ]
    for link in STRATEGIC_OUTCOME_LINKS:
        lf_id = lf_lookup.get(link["indicator_code"]) if link["indicator_code"] else None
        insert_returning_id(
            """INSERT INTO strategic_outcome_links
               (outcome_code, project_id, logframe_row_id, source, note)
               VALUES (:outcome_code, :project_id, :logframe_row_id, :source, :note)""",
            {
                "outcome_code":    link["outcome_code"],
                "project_id":      project_id,
                "logframe_row_id": lf_id,
                "source":          link["source"],
                "note":            link["note"],
            },
        )
    print(f"Strategic outcome links: {len(STRATEGIC_OUTCOME_LINKS)} inserted.")

    print("Done.")


if __name__ == "__main__":
    seed()

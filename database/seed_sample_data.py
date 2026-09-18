"""
Populate realistic Q1 & Q2 2026 sample data for the SAWA programme.
Run once after seed_sawa.py:   python3 -m database.seed_sample_data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, run_query, run_write

# ── Q1/Q2 actuals by raw_data_analysis row id ────────────────────────────────
#
#  Mix of on-track (green), amber (near-miss), and off-track (red) values
#  so every traffic-light state is exercised in Module D.
#
#  Quarterly targets (estimated from annual):
#   PI.5  → Q1: 95  Q2: 135  (stated explicitly in logframe)
#   PI.6  → ~125/quarter  (500 annual)
#   PI.7  → ~6/quarter    (25 annual)
#   PI.8  → ~125/quarter  (500 annual)
#   PI.9  → ~125/quarter  (500 annual)
#   PII.R5  → ~2/quarter  (8 annual)
#   PII.R6  → ~2.32 MT/quarter  (9.26 MT annual)
#   PII.R7  → ~USD 4,167/quarter (USD 16,667 annual)
#   PIII.R1 → ~25/quarter (100 annual)
#   PIII.R2 → ~28.9 MT/quarter (115.74 MT annual)
#   PIII.R3 → ~USD 52,083/quarter (USD 208,333 annual)
#
#  PI.1-PI.4, PI.12 are annual/bi-annual — no quarterly actuals yet.

_ON  = "Completed - on track"
_OFF = "Completed - not on track"
_NOT = "Data not collected yet"

# Allowed action_status values (CHECK constraint):
#   'No action needed - data reporting only'
#   'Inform decision-maker/confirm next steps'
#   'Follow-up or investigate'
#   'Change/adapt/revise'
#   'Resolved'
_A_NONE    = "No action needed - data reporting only"
_A_INFORM  = "Inform decision-maker/confirm next steps"
_A_FOLLOW  = "Follow-up or investigate"
_A_CHANGE  = "Change/adapt/revise"
_A_RESOLVE = "Resolved"

ACTUALS = [
    # (row_id, code, q1, q2, q3, q4, db_status, action_status, action_desc)
    (61, "PI.1",
     "", "", "", "", _NOT, _A_INFORM,
     "Annual indicator – first measurement Dec 2026. Baseline household survey scheduled Oct 2026."),

    (62, "PI.2",
     "", "18%", "", "", _OFF, _A_CHANGE,
     "Bi-annual: Q2 actual 18% vs milestone 30%. Employability coaching being intensified."
     " Accelerate BDS module delivery with D&F and YiW partners."),

    (63, "PI.3",
     "", "", "", "", _NOT, _A_INFORM,
     "Annual indicator – first measurement Dec 2026. Enterprise registration data to be compiled Q4 2026."),

    (64, "PI.4",
     "", "", "", "", _NOT, _A_INFORM,
     "Annual indicator – first measurement Dec 2026. PWD disaggregation field being added to KoboToolbox survey."),

    (65, "PI.5",
     "82", "141", "", "", _ON, _A_RESOLVE,
     "Q1 shortfall (82 vs trigger 95) recovered in Q2 (141); cumulative 223 on track."
     " Gap addressed via targeted mobilisation in Volta and Brong-Ahafo regions."),

    (66, "PI.6",
     "118", "129", "", "", _ON, _A_NONE,
     "Q1: 118, Q2: 129; cumulative 247 of 500 annual target. On track."),

    (67, "PI.7",
     "6", "8", "", "", _ON, _A_NONE,
     "Q1: 6 (marginal miss vs ~6.25 quarterly pace), Q2: 8; cumulative 14 of 25 annual target. On track."),

    (68, "PI.8",
     "121", "133", "", "", _ON, _A_NONE,
     "Q1: 121, Q2: 133; cumulative 254 of 500 annual target. On track."),

    (69, "PI.9",
     "108", "127", "", "", _ON, _A_NONE,
     "Q1: 108, Q2: 127; cumulative 235 of 500 annual target. Safeguarding engagement strong across all sites."),

    (70, "PI.10",
     "3", "", "", "", _OFF, _A_FOLLOW,
     "Bi-annual: H1 total 3 vs target 4. Disability-inclusive outreach events planned for Q3 across 3 regions."),

    (71, "PI.11",
     "64%", "67%", "", "", _ON, _A_NONE,
     "Q1: 64%, Q2: 67%; both exceed the >=60% threshold. On track."),

    (72, "PI.12",
     "", "", "", "", _NOT, _A_INFORM,
     "In planning – 2 policy sessions confirmed for H2 2026 (Oct & Nov). Agenda being finalised."),

    (73, "PII.R5",
     "1", "2", "", "", _OFF, _A_CHANGE,
     "Cumulative H1 total 3 vs target 4. PWD inclusion mitigation plan active."
     " Additional PWD recruitment drive launched Jul 2026; 5 prospects in pipeline."),

    (74, "PII.R6",
     "1.8", "2.1", "", "", _OFF, _A_CHANGE,
     "Cumulative 3.9 MT vs H1 target 4.63 MT. Fish-feed input delays reported."
     " Emergency fish-feed procurement approved; delivery expected Aug 2026."),

    (75, "PII.R7",
     "3400", "4800", "", "", _OFF, _A_INFORM,
     "Cumulative USD 8,200 vs H1 target USD 8,333 (1.6% shortfall). Q3 recovery expected."
     " Market linkage officer monitoring weekly; price-support sessions added."),

    (76, "PIII.R1",
     "22", "27", "", "", _OFF, _A_FOLLOW,
     "Q1 shortfall (22 vs 25); Q2 near-recovery (27); cumulative 49 vs 50 H1 target."
     " Catch-up cohort of 6 participants being onboarded Aug 2026."),

    (77, "PIII.R2",
     "26.4", "31.8", "", "", _ON, _A_NONE,
     "Q1: 26.4 MT, Q2: 31.8 MT; cumulative 58.2 MT of 115.74 MT annual target. On track."),

    (78, "PIII.R3",
     "48200", "54800", "", "", _OFF, _A_INFORM,
     "Cumulative USD 103,000 vs H1 target USD 104,167 (1.1% below)."
     " Value-chain officer adding market price advisory sessions for trading participants."),

    (79, "PIII.6",
     "", "4", "", "", _ON, _A_NONE,
     "Bi-annual: H1 total 4 vs target 5. Final market linkage expected Aug 2026. On track."),

    (80, "PIV.1",
     "", "1", "", "", _OFF, _A_CHANGE,
     "Bi-annual: H1 total 1 vs target 2. MEL Officer to present SAWA progress report at MoFA Sep 2026."),
]

# ── Review log entries (for the 3 overdue protocols) ─────────────────────────
#  protocol 15 = Performance / Quarterly (next 2026-09-01 → overdue)
#  protocol 17 = Stakeholder / Quarterly (next 2026-09-10 → overdue)
#  protocol 18 = Process     / Monthly   (next 2026-09-05 → overdue)

REVIEW_LOGS = [
    {
        "protocol_id":         15,
        "conducted_date":      "2026-09-14",
        "conducted_by":        "meal_officer",
        "summary":             (
            "Q2 2026 performance review completed. Reviewed 20 output and outcome indicators. "
            "Overall programme on track at 68% of H1 targets achieved. "
            "PI.5 youth mobilisation recovered from Q1 shortfall. "
            "PII.R5 and PII.R6 remain below trigger — mitigation plans active. "
            "FOLLOW-UP: Monthly check-in on PII.R5 and PII.R6 mitigation actions; "
            "escalate to Programme Manager if no improvement by Oct 2026."
        ),
        "red_flags_found":     "PI.5 Q1 shortfall (recovered); PII.R5 PWD inclusion gap; PII.R6 fish production below target",
        "linked_indicator_ids": "65,73,74",
        "follow_up_required":  "Y",
    },
    {
        "protocol_id":         17,
        "conducted_date":      "2026-09-12",
        "conducted_by":        "meal_officer",
        "summary":             (
            "Stakeholder review Q2 completed via virtual session with AGRI-IMPACT MEL team and "
            "3 implementing partner BDS coordinators. Partners confirmed data quality improvements "
            "since KoboToolbox rollout. MoFA district officer provided fish production verification data. "
            "FOLLOW-UP: AGRI-IMPACT to share official Q2 verification report by 30 Sep 2026."
        ),
        "red_flags_found":     "None",
        "linked_indicator_ids": "66,67,68,69",
        "follow_up_required":  "Y",
    },
    {
        "protocol_id":         18,
        "conducted_date":      "2026-09-08",
        "conducted_by":        "asst_meal",
        "summary":             (
            "Monthly process review for August 2026. KoboToolbox data submission compliance: "
            "9 of 10 assigned enumerators submitted on schedule (90%). "
            "One enumerator in Upper West region delayed — data recovered manually. "
            "FOLLOW-UP: Enumerator retraining on submission deadlines; add reminder to WhatsApp MEL group."
        ),
        "red_flags_found":     "Upper West data submission delay (resolved)",
        "linked_indicator_ids": "",
        "follow_up_required":  "Y",
    },
]

# ── Decision reports (open / in-review) ──────────────────────────────────────
#  Linked via indicator_code → logframe_row_id lookup done at runtime.

DECISION_REPORTS = [
    {
        "indicator_code":       "PI.5",
        "created_date":         "2026-05-10",
        "created_by":           "meal_officer",
        "target_value":         "95 (Q1); 135 (Q2–Q4)",
        "indicator_definition": "Number of disadvantaged young women and PWDs mobilised and enrolled in SAWA",
        "assumed_pattern":      "Linear ramp-up; Q1 slower due to programme launch period",
        "actual_value":         "82 (Q1) — 14% below Q1 trigger",
        "review_category":      "Performance",
        "specific_focus_area":  "Youth Mobilisation — Quarterly Output PI.5",
        "investigation_notes":  (
            "Recruitment shortfall concentrated in Brong-Ahafo and Upper East regions. "
            "Implementing partners reported delayed community sensitisation meetings due to local festival season. "
            "Volta region met target (28 of 28 planned). "
            "No structural barrier identified — issue is timing, not reach."
        ),
        "key_finding":          (
            "Q1 shortfall of 13 participants (82 vs 95) is attributed to community sensitisation delay "
            "in 2 of 5 regions. Q2 mobilisation target revised upward to compensate. "
            "No systemic risk to annual target of 500."
        ),
        "status":               "Under review",
        "actions": [
            {
                "decision_maker": "biz_dev",
                "action":         "Coordinate targeted mobilisation drive in Brong-Ahafo and Upper East in Apr–May 2026",
                "action_due_date": "2026-05-31",
                "action_status":  "Resolved",
            },
            {
                "decision_maker": "meal_officer",
                "action":         "Update Q2 enrolment target to 141 in KoboToolbox tracking form and report to AGRI-IMPACT",
                "action_due_date": "2026-06-15",
                "action_status":  "Resolved",
            },
        ],
    },
    {
        "indicator_code":       "PII.R5",
        "created_date":         "2026-08-05",
        "created_by":           "meal_officer",
        "target_value":         "8 (annual); 4 (H1)",
        "indicator_definition": "Number of PWDs employed in aquaculture-related value chain roles",
        "assumed_pattern":      "2 PWD placements per quarter, H1 = 4",
        "actual_value":         "3 (H1 cumulative — Q1: 1, Q2: 2)",
        "review_category":      "Performance",
        "specific_focus_area":  "PWD Inclusion — Output PII.R5",
        "investigation_notes":  (
            "PWD placements are below H1 target by 1 person. "
            "Three placements confirmed: 1 in pond management (Accra region), 2 in fish processing (Volta). "
            "Challenge identified: limited assistive infrastructure at 3 pond sites in Central and Ashanti regions. "
            "Partner disability liaison officer position vacant since June 2026."
        ),
        "key_finding":          (
            "PWD placement gap driven by infrastructure barriers at 3 sites and a staffing gap "
            "in the disability liaison function. Annual target of 8 is at risk if Q3 does not achieve "
            "at least 3 placements. Escalated to Programme Manager and CEL safeguarding focal point."
        ),
        "status":               "Under review",
        "actions": [
            {
                "decision_maker": "biz_dev",
                "action":         "Assess and prioritise pond infrastructure adaptations at 3 sites (ramps, seating) by Sep 2026",
                "action_due_date": "2026-09-30",
                "action_status":  "Follow-up or investigate",
            },
            {
                "decision_maker": "cel_admin",
                "action":         "Recruit interim disability liaison officer; post JD by 20 Aug 2026",
                "action_due_date": "2026-08-20",
                "action_status":  "Change/adapt/revise",
            },
            {
                "decision_maker": "meal_officer",
                "action":         "Add PWD placement pipeline tracker to monthly MEL dashboard",
                "action_due_date": "2026-08-31",
                "action_status":  "Resolved",
            },
        ],
    },
]

# ── Indicators master (Module B / data points) ────────────────────────────────
# A small set of indicators to seed data_points against.

INDICATORS_MASTER = [
    {"pillar": "SAWA", "level": "Output", "statement": "Youth mobilised and enrolled",
     "target_value": 500.0, "unit": "persons"},
    {"pillar": "SAWA", "level": "Output", "statement": "Participants trained in BDS",
     "target_value": 500.0, "unit": "persons"},
    {"pillar": "SAWA", "level": "Output", "statement": "Safeguarding sessions conducted",
     "target_value": 500.0, "unit": "sessions"},
    {"pillar": "SAWA", "level": "Output", "statement": "PWDs employed in value chain",
     "target_value": 8.0,   "unit": "persons"},
    {"pillar": "SAWA", "level": "Output", "statement": "Fish produced by PWD participants (MT)",
     "target_value": 9.26,  "unit": "MT"},
]

# data_points linked to indicator_ids inserted above (mapped by index)
DATA_POINTS = [
    # (indicator_index, quarter, year, value, source_module)
    (0, 1, 2026, 82.0,  "kobo"),
    (0, 2, 2026, 141.0, "kobo"),
    (1, 1, 2026, 118.0, "kobo"),
    (1, 2, 2026, 129.0, "kobo"),
    (2, 1, 2026, 108.0, "kobo"),
    (2, 2, 2026, 127.0, "kobo"),
    (3, 1, 2026, 1.0,   "manual"),
    (3, 2, 2026, 2.0,   "manual"),
    (4, 1, 2026, 1.8,   "manual"),
    (4, 2, 2026, 2.1,   "manual"),
]


def seed():
    init_db()

    project_id = 1  # SAWA

    # ── 1. Fix donor name in projects table ──────────────────────────────────
    run_write(
        "UPDATE projects SET donor=:d WHERE project_id=:pid",
        {"d": "Mastercard Foundation", "pid": project_id},
    )
    print("Projects donor updated to 'Mastercard Foundation'.")

    # ── 2. Update raw_data_analysis actuals ───────────────────────────────────
    updated = 0
    for row in ACTUALS:
        rid, code, q1, q2, q3, q4, status, act_status, act_desc = row
        run_write(
            """UPDATE raw_data_analysis
               SET actual_q1=:q1, actual_q2=:q2, actual_q3=:q3, actual_q4=:q4,
                   indicator_status=:status,
                   action_status=:act_status,
                   action_description=:act_desc
               WHERE id=:rid""",
            {
                "q1": q1, "q2": q2, "q3": q3, "q4": q4,
                "status": status,
                "act_status": act_status,
                "act_desc": act_desc,
                "rid": rid,
            },
        )
        updated += 1
    print(f"raw_data_analysis: {updated} rows updated with Q1/Q2 actuals.")

    # ── 3. Review log ─────────────────────────────────────────────────────────
    run_write("DELETE FROM review_log", {})
    for entry in REVIEW_LOGS:
        run_write(
            """INSERT INTO review_log
               (protocol_id, conducted_date, conducted_by, summary,
                red_flags_found, linked_indicator_ids, follow_up_required)
               VALUES (:protocol_id, :conducted_date, :conducted_by, :summary,
                       :red_flags_found, :linked_indicator_ids, :follow_up_required)""",
            entry,
        )
    print(f"review_log: {len(REVIEW_LOGS)} entries inserted.")

    # ── 4. Decision reports ───────────────────────────────────────────────────
    lf_lookup = {
        r["indicator_code"]: r["id"]
        for r in run_query(
            "SELECT id, indicator_code FROM logframe_rows WHERE project_id=:pid",
            {"pid": project_id},
        )
        if r["indicator_code"]
    }

    # Clear existing open reports (leave any pre-existing closed ones)
    run_write(
        "DELETE FROM decision_actions WHERE report_id IN "
        "(SELECT id FROM decision_reports WHERE project_id=:pid AND status='Under review')",
        {"pid": project_id},
    )
    run_write(
        "DELETE FROM decision_reports WHERE project_id=:pid AND status='Under review'",
        {"pid": project_id},
    )

    for dr in DECISION_REPORTS:
        lf_id = lf_lookup.get(dr["indicator_code"])
        # Get last insert rowid via a SELECT MAX after insert
        run_write(
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
                "created_date":        dr["created_date"],
                "created_by":          dr["created_by"],
                "logframe_row_id":     lf_id,
                "target_value":        dr["target_value"],
                "indicator_definition": dr["indicator_definition"],
                "assumed_pattern":     dr["assumed_pattern"],
                "actual_value":        dr["actual_value"],
                "review_category":     dr["review_category"],
                "specific_focus_area": dr["specific_focus_area"],
                "investigation_notes": dr["investigation_notes"],
                "key_finding":         dr["key_finding"],
                "status":              dr["status"],
            },
        )
        rows = run_query("SELECT MAX(id) as max_id FROM decision_reports")
        report_id = rows[0]["max_id"]
        for action in dr.get("actions", []):
            run_write(
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
        total_actions = len(dr.get("actions", []))
        print(f"  Decision report '{dr['specific_focus_area']}' id={report_id}, {total_actions} action(s).")
    print(f"decision_reports: {len(DECISION_REPORTS)} open reports inserted.")

    # ── 5. Indicators master + data_points ───────────────────────────────────
    run_write("DELETE FROM data_points WHERE indicator_id IN "
              "(SELECT indicator_id FROM indicators WHERE project_id=:pid)", {"pid": project_id})
    run_write("DELETE FROM indicators WHERE project_id=:pid", {"pid": project_id})

    indicator_ids = []
    for ind in INDICATORS_MASTER:
        run_write(
            """INSERT INTO indicators (project_id, pillar, level, statement, target_value, unit)
               VALUES (:project_id, :pillar, :level, :statement, :target_value, :unit)""",
            {**ind, "project_id": project_id},
        )
        rows = run_query("SELECT MAX(indicator_id) as mid FROM indicators")
        indicator_ids.append(rows[0]["mid"])
    print(f"indicators: {len(indicator_ids)} rows inserted.")

    for idx, quarter, year, value, source in DATA_POINTS:
        run_write(
            """INSERT INTO data_points (indicator_id, quarter, year, value, source_module)
               VALUES (:iid, :q, :y, :v, :s)""",
            {
                "iid": indicator_ids[idx],
                "q":   quarter,
                "y":   year,
                "v":   value,
                "s":   source,
            },
        )
    print(f"data_points: {len(DATA_POINTS)} rows inserted.")

    print("\nSample data seeding complete.")


if __name__ == "__main__":
    seed()

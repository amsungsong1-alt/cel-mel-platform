"""Module K — Team Workspace

Role-based folders for the CEL programme team and Partner MEAL focal persons.
Each role has its own task list and evidence file store, independent of
individual partner visits (those live in Module J).

Roles
-----
CEL Programme Team: GYSI | Biz Dev | Biz Coach | Comms | Admin | Finance |
                    MEAL Admin | MEAL Asst
Partner:            Partner MEAL
"""
from __future__ import annotations

import io
from datetime import date as _date, datetime as _datetime, timezone as _timezone

import pandas as pd
import streamlit as st

from database.db import ensure_team_activity_log, init_db, run_query, run_write
from utils.auth import can_write_k_role, refresh_session_permissions
from utils.nav_strip import render_nav_strip
from utils.shared_widgets import project_selector

st.set_page_config(page_title="Team Workspace — CEL MEL", layout="wide")
init_db()
render_nav_strip("Input")

if not st.session_state.get("authentication_status"):
    st.error("Please log in from the main page.")
    st.stop()

refresh_session_permissions()

with st.sidebar:
    project_id = project_selector()
    if project_id is None:
        st.stop()
    st.divider()
    st.caption(f"Role: **{st.session_state.get('role', 'Viewer')}**")

# ── Role catalogue ─────────────────────────────────────────────────────────────
_CEL_ROLES = [
    "GYSI",
    "Biz Dev",
    "Biz Coach",
    "Comms",
    "Admin",
    "Finance",
    "MEAL Admin",
    "MEAL Asst",
]
_PARTNER_ROLES = ["Partner MEAL"]
# Not tied to one functional role — anyone with Module K write access can
# save a worked-on document here, regardless of their own k_role (see
# can_write_k_role's open-role handling in utils/auth.py).
_SHARED_ROLES = ["Shared Documents"]
ALL_ROLES = _CEL_ROLES + _PARTNER_ROLES + _SHARED_ROLES

_ROLE_ICONS = {
    "GYSI":             "♀",
    "Biz Dev":          "📈",
    "Biz Coach":        "🎯",
    "Comms":            "📢",
    "Admin":            "🗂",
    "Finance":          "💰",
    "MEAL Admin":       "📊",
    "MEAL Asst":        "📋",
    "Partner MEAL":     "🤝",
    "Shared Documents": "🗄",
}

_STATUS_COLOUR = {
    "Not Started": "#546E7A",
    "In Progress":  "#E65100",
    "Complete":     "#2E7D32",
    "Blocked":      "#C62828",
}
STATUS_OPTS = ["Not Started", "In Progress", "Complete", "Blocked"]

# ── Reference data ─────────────────────────────────────────────────────────────
logframe_rows = run_query(
    "SELECT id, indicator_code, indicator_statement FROM logframe_rows WHERE project_id=:pid ORDER BY id",
    {"pid": project_id},
)
lf_options = ["None"] + [
    f"[{r['indicator_code']}] {r['indicator_statement'][:60]}"
    for r in logframe_rows
]
lf_code_to_id = {r["indicator_code"]: r["id"] for r in logframe_rows}

_username  = st.session_state.get("username", "Team")

# Self-heals the Daily Activity table on every page load, independent of
# whether _run_migrations()'s own (silently-failable) creation attempt
# succeeded for it — see ensure_team_activity_log()'s docstring.
ensure_team_activity_log()


def _log_activity(role: str, action_type: str) -> None:
    """Record one timestamped activity event (task update/add, file add)
    for the Daily Activity chart on the Time tab. This counts actions, not
    time spent — Streamlit has no way to measure continuous page-open
    duration without custom browser instrumentation, so it's an honest
    activity-frequency proxy rather than tracked hours."""
    run_write(
        """INSERT INTO team_activity_log
           (project_id, team_role, action_type, logged_by, logged_at)
           VALUES (:pid, :role, :action, :by, :at)""",
        {
            "pid":    project_id,
            "role":   role,
            "action": action_type,
            "by":     _username,
            "at":     _datetime.now(_timezone.utc).isoformat(timespec="seconds"),
        },
    )


# ── MEAL task allocation source data (21-row Module B logframe, 29 Sep 2026) ───
# The logframe's Responsible column only names 3 coarse parties (CEL MEAL,
# Programme Team, Partner MEAL) — it does not specify which of Module K's 9
# functional roles owns each indicator. The split below to GYSI / Biz Coach /
# Comms / Admin / MEAL Admin / MEAL Asst is CEL's proposed working assignment
# by subject-matter fit, NOT sourced from the logframe — flagged as such in
# the document intro and pending CEL confirmation/adjustment. Biz Dev and
# Finance currently have no directly-linked logframe indicator.
# "quarter" = the Year 1 SAWA quarter(s) (Q1 Jul-Sep 2026 .. Q4 Apr-Jun 2027) in which
# this indicator's evidence realistically starts being generated, per Module A's Year 1
# Quarterly Delivery Calendar (BDS/WAN concept notes) and the Consolidated Workplan
# cross-reference table (_workplan_xref) — i.e. the same sourced data already vetted
# against the concept notes elsewhere in the app, not a fresh guess for this document.
_MEAL_TASKS_BY_ROLE = {
    "MEAL Admin": [
        {"id": "LoP.1", "indicator": "Number of financially disadvantaged young women and PWDs engaged in dignified and fulfilling work across the aquaculture value chain",
         "mov": "Programme monitoring database; Annual outcome surveys; Partner progress reports", "freq": "Annual", "quarter": "Q4 (annual review)",
         "task": "Maintain the programme monitoring database; commission and administer the annual outcome survey; consolidate partner progress reports"},
        {"id": "PI.20", "indicator": "Number of young women trained to identify and respond to safeguarding issues (PSEA awareness)",
         "mov": "Training records; Safeguarding incident log; CEL safeguarding officer reports", "freq": "Quarterly", "quarter": "Q2–Q4",
         "task": "Maintain the safeguarding incident log; compile safeguarding officer reports"},
        {"id": "PI.23", "indicator": "Number of programme sites/partners with institutionalised safeguarding and occupational health standards",
         "mov": "Site certification documentation; Safeguarding policy adoption records", "freq": "Annual", "quarter": "Q4 (annual review)",
         "task": "Verify and file site certification documentation; track safeguarding policy adoption records"},
    ],
    "MEAL Asst": [
        {"id": "PI.19", "indicator": "Number of persons (participants and community champions) receiving gender-transformative training",
         "mov": "Training attendance registers; Post-training knowledge assessment records", "freq": "Quarterly", "quarter": "Q2–Q4",
         "task": "Collect and verify attendance registers; administer and score post-training knowledge assessments"},
        {"id": "PI.22", "indicator": "Number of safeguarding awareness campaigns and roadshows undertaken in SAWA intervention communities",
         "mov": "Campaign reports; Attendance records; Community feedback forms", "freq": "Quarterly", "quarter": "Q2–Q4",
         "task": "Produce campaign reports; collect attendance records and community feedback forms"},
    ],
    "GYSI": [
        {"id": "PI.9", "indicator": "Number of GYSI focal persons trained in GALS and EMAP (Training of Trainers model, per implementing partner)",
         "mov": "Training completion certificates; Focal person registry; Partner reports", "freq": "Quarterly", "quarter": "Q2–Q3",
         "task": "Issue and file completion certificates; maintain the focal person registry"},
        {"id": "PI.11", "indicator": "Number of women engaged in leadership and mentorship forums under the Women in Aquaculture Network (WAN)",
         "mov": "WAN attendance registers; Forum reports; CEL field officer notes", "freq": "Quarterly", "quarter": "Q3–Q4",
         "task": "Collect WAN attendance registers; compile forum reports from field officer notes"},
        {"id": "PI.12", "indicator": "Number of leadership bootcamps and inter-zonal exchange visits organised under WAN",
         "mov": "Event reports; Attendance lists; CEL field officer notes", "freq": "Quarterly", "quarter": "Q3–Q4",
         "task": "Produce event reports; collect attendance lists"},
        {"id": "PI.13", "indicator": "Number of young female PWDs identified as peer mentors and matched with PWD programme participants",
         "mov": "Mentor registry; Match records; Field verification notes", "freq": "Quarterly", "quarter": "Q1–Q4",
         "task": "Maintain the mentor registry; log mentor-mentee matches and field verification"},
    ],
    "Biz Coach": [
        {"id": "PI.3", "indicator": "Number of young women and PWDs completing Business Development Services (BDS) training",
         "mov": "Training attendance registers; BDS completion records; KoboToolbox Tool 2", "freq": "Quarterly", "quarter": "Q2–Q4",
         "task": "Sync KoboToolbox Tool 2; verify BDS completion records against attendance registers"},
        {"id": "PI.17", "indicator": "Number of women in women-led cooperatives/clusters receiving gender training, financial literacy and business mentoring",
         "mov": "Training registers; Cooperative membership records; Partner reports", "freq": "Quarterly", "quarter": "Q2–Q4",
         "task": "Maintain training registers; verify cooperative membership records"},
        {"id": "PI.18", "indicator": "Number of gender-responsive governance frameworks adopted by women-led cooperatives/clusters",
         "mov": "Signed governance documents; KoboToolbox Tool 3 Governance Checklist; Field verification", "freq": "Quarterly", "quarter": "Q3–Q4",
         "task": "Collect signed governance documents; complete Tool 3 Governance Checklist"},
        {"id": "PIII.6", "indicator": "Number of women-led cooperatives/clusters strengthened across the aquaculture value chain (established and registered entities)",
         "mov": "Cooperative registration documents; Governance Checklist (Tool 3); Field verification", "freq": "Quarterly", "quarter": "Q3–Q4",
         "task": "File cooperative registration documents; complete Tool 3 Governance Checklist"},
    ],
    "Comms": [
        {"id": "PIV.5", "indicator": "Number of young women receiving E-SAWA digital literacy training, mentorship and digital entrepreneurship workshops",
         "mov": "Training attendance registers; E-SAWA platform enrolment data", "freq": "Quarterly", "quarter": "Q2–Q4",
         "task": "Pull E-SAWA platform enrolment data; reconcile against attendance registers"},
    ],
    "Admin": [
        {"id": "PI.1", "indicator": "Number of young women and PWDs mobilised, sensitised and enrolled in SAWA D&F value-chain activities",
         "mov": "Enrolment registers; Mobilisation partner reports; KoboToolbox Tool 2", "freq": "Quarterly", "quarter": "Q1–Q4",
         "task": "Sync KoboToolbox Tool 2; reconcile enrolment registers with partner mobilisation reports"},
    ],
    # "partner" = the Relevant Anchor Partner(s) for this indicator, verbatim from Module A's
    # _workplan_xref table (Consolidated Workplan cross-reference) — Partner MEAL's tasks are
    # the only ones where "which partner" is itself operationally essential to allocate correctly.
    "Partner MEAL": [
        {"id": "PII.R5", "indicator": "Number of Persons with Disabilities (PWDs) accessing D&F in the Aquaculture value chain — programme-wide (YiW)",
         "mov": "Employment records; Partner payroll verification; Field spot-checks; PWD registry", "freq": "Quarterly", "quarter": "Q1–Q4",
         "partner": "Naple Betta — only partner reporting a matching PWD-in-D&F-work figure (15). Other partners' PWD numbers (e.g. AgroKings 170, NewAge Agric 290) measure broader PWD reach, not confirmed D&F job placement.",
         "task": "Verify partner payroll records; maintain the PWD registry; conduct field spot-checks"},
        {"id": "PIII.R1", "indicator": "Number of young women accessing D&F in Aquaculture Value Addition activities (YiW)",
         "mov": "Employment and enterprise records; Field verification", "freq": "Quarterly", "quarter": "Q2–Q4",
         "partner": "AgroKings (1909 processing/retail) · Naple Betta (grill outlets) · Aglow Farms (HQ processing) · TechnoServe (micro-grant businesses)",
         "task": "Collect employment and enterprise records; conduct field verification"},
        {"id": "PII.R6", "indicator": "Quantity (MT) of fish produced by young women PWDs accessing D&F in the Aquaculture value chain",
         "mov": "Production logs; Catch data records; Third-party verification", "freq": "Quarterly", "quarter": "Q1–Q4",
         "partner": "Naple Betta — same PWD-in-D&F cohort as PII.R5",
         "task": "Collect production and catch-data logs; arrange third-party verification"},
        {"id": "PII.R7", "indicator": "Revenue (USD) generated by young women PWDs accessing D&F in the Aquaculture value chain",
         "mov": "Sales receipts; Partner financial records; Income survey", "freq": "Quarterly", "quarter": "Q1–Q4",
         "partner": "Naple Betta — same PWD-in-D&F cohort as PII.R5",
         "task": "Collect sales receipts; verify partner financial records; run the income survey"},
        {"id": "PIII.R2", "indicator": "Quantity (MT) of fish produced or fish-related products traded through SAWA-supported value-addition channels",
         "mov": "Trading and processing records; Market assessment data", "freq": "Quarterly", "quarter": "Q2–Q4",
         "partner": "TechnoServe (1,298+ MT traded) · Naple Betta (110 MT value-added trade)",
         "task": "Collect trading and processing records; conduct the market assessment"},
        {"id": "PIII.R3", "indicator": "Revenue (USD) generated from trading in Value Added Aquaculture products by SAWA-supported enterprises",
         "mov": "Sales records; Market price monitoring; Financial audits", "freq": "Quarterly", "quarter": "Q2–Q4",
         "partner": "TechnoServe ($845,000 from catfish sales) · Naple Betta ($841,500 value-added revenue)",
         "task": "Collect sales records; monitor market prices; support financial audits"},
    ],
}
_MEAL_ROLE_ACCENT = {
    "GYSI":       "8E3B72",
    "Biz Dev":    "1B5E7A",
    "Biz Coach":  "4A6B5C",
    "Comms":      "2E6F9E",
    "Admin":      "5E6A6A",
    "Finance":    "8A6D1E",
    "MEAL Admin": "1E7E76",
    "MEAL Asst":  "2E9E8F",
    "Partner MEAL": "B96A2E",
}
_MEAL_ROLE_SUBTITLE = {
    "GYSI":       "GYSI focal-person training and Women in Aquaculture Network (WAN) delivery evidence.",
    "Biz Dev":    "BDS provider mapping and catalytic grant pipeline — no logframe indicator directly assigned.",
    "Biz Coach":  "BDS training completion and cooperative business mentoring/governance evidence.",
    "Comms":      "E-SAWA digital literacy and digital entrepreneurship evidence.",
    "Admin":      "Partner mobilisation and enrolment coordination evidence.",
    "Finance":    "Budget/burn-rate monitoring and grant disbursement reconciliation — no logframe indicator directly assigned.",
    "MEAL Admin": "Programme-level monitoring, safeguarding officer reporting and the annual outcome survey.",
    "MEAL Asst":  "Routine quarterly attendance, assessment and campaign evidence collection.",
    "Partner MEAL": "Outcome-level D&F jobs, production and revenue data verified at partner level.",
}
_MEAL_ROLE_ORDER = [
    "GYSI", "Biz Dev", "Biz Coach", "Comms", "Admin", "Finance",
    "MEAL Admin", "MEAL Asst", "Partner MEAL",
]

# The 3 example tasks already seeded live per role in Module K (database/db.py
# team_tasks seed block) — mirrored here so the Word export retains a realistic
# example alongside the logframe-derived indicator rows for every K role.
_MEAL_ROLE_EXAMPLE_TASKS = {
    "GYSI": [
        {"task": "Collect disaggregated enrolment data from all 5 anchor partners", "status": "In Progress", "due": "2026-10-31", "assigned": "GYSI Officer", "code": "PI.1"},
        {"task": "Verify PWD inclusion rate against 5% programme target", "status": "Not Started", "due": "2026-11-15", "assigned": "GYSI Officer", "code": "PII.R5"},
        {"task": "Review GALS/EMAP focal person training completion (PI.9)", "status": "Not Started", "due": "2026-11-30", "assigned": "GYSI Officer", "code": "PI.9"},
    ],
    "Biz Dev": [
        {"task": "Map existing BDS providers per district across all anchor sites", "status": "In Progress", "due": "2026-10-31", "assigned": "Biz Dev Lead", "code": ""},
        {"task": "Finalise catalytic grant eligibility criteria with TechnoServe", "status": "Not Started", "due": "2026-11-15", "assigned": "Biz Dev Lead", "code": "PIII.R1"},
        {"task": "Submit Year 1 BDS roll-out plan to AIL", "status": "Not Started", "due": "2026-11-30", "assigned": "Biz Dev Lead", "code": "PI.3"},
    ],
    "Biz Coach": [
        {"task": "Track BDS training completion (Tool 2) for Q1", "status": "In Progress", "due": "2026-10-25", "assigned": "Biz Coach Lead", "code": "PI.3"},
        {"task": "Deploy coaching curriculum to Naple Betta processing hubs", "status": "Not Started", "due": "2026-11-01", "assigned": "Biz Coach Lead", "code": "PII.R6"},
        {"task": "Conduct coaching quality review at AgroKings cluster sites", "status": "Not Started", "due": "2026-11-30", "assigned": "Biz Coach Lead", "code": ""},
    ],
    "Comms": [
        {"task": "Draft Q1 programme impact story for MCF reporting", "status": "In Progress", "due": "2026-11-15", "assigned": "Comms Officer", "code": ""},
        {"task": "Compile SAWA Voices quotes from NewAge Agric Q1 cohort", "status": "Not Started", "due": "2026-11-01", "assigned": "Comms Officer", "code": "LoP.1"},
        {"task": "Update SAWA social media content calendar for Q2", "status": "Not Started", "due": "2026-10-31", "assigned": "Comms Officer", "code": ""},
    ],
    "Admin": [
        {"task": "Process partner MOU renewals — Aglow Farms and AgroKings", "status": "In Progress", "due": "2026-10-31", "assigned": "Programme Admin", "code": ""},
        {"task": "Archive Q1 field visit documents in shared drive", "status": "Not Started", "due": "2026-10-30", "assigned": "Programme Admin", "code": ""},
        {"task": "Coordinate Q1 programme review meeting logistics", "status": "Not Started", "due": "2026-11-07", "assigned": "Programme Admin", "code": ""},
    ],
    "Finance": [
        {"task": "Verify Q1 burn rate against 70% threshold", "status": "In Progress", "due": "2026-10-31", "assigned": "Finance Officer", "code": ""},
        {"task": "Reconcile TechnoServe catalytic grant disbursement tracker", "status": "Not Started", "due": "2026-11-15", "assigned": "Finance Officer", "code": "PIII.R1"},
        {"task": "Submit Q1 financial narrative to AIL", "status": "Not Started", "due": "2026-11-30", "assigned": "Finance Officer", "code": ""},
    ],
    "MEAL Admin": [
        {"task": "Configure KoboToolbox Form 1 across all 5 anchor partners", "status": "Complete", "due": "", "assigned": "MEAL Admin", "code": "PI.1"},
        {"task": "Set up Module E indicator baseline tracking for FY2026", "status": "Complete", "due": "", "assigned": "MEAL Admin", "code": ""},
        {"task": "Complete partner MEAL mapping visits (Modules J and K)", "status": "In Progress", "due": "2026-10-31", "assigned": "MEAL Admin", "code": ""},
    ],
    "MEAL Asst": [
        {"task": "Enter Q1 actual values from partner narrative reports into Module E", "status": "In Progress", "due": "2026-10-25", "assigned": "MEAL Asst", "code": ""},
        {"task": "File Q1 participant registers by partner and quarter", "status": "Not Started", "due": "2026-10-31", "assigned": "MEAL Asst", "code": "PI.1"},
        {"task": "Review data quality on Q1 KoboToolbox Form 1 submissions", "status": "Not Started", "due": "2026-11-07", "assigned": "MEAL Asst", "code": "PI.1"},
    ],
    "Partner MEAL": [
        {"task": "Submit participant register extract to CEL MEAL by 30 Sep 2026", "status": "In Progress", "due": "2026-09-30", "assigned": "Partner MEAL Focal", "code": "PI.1"},
        {"task": "Verify disaggregation fields in KoboToolbox Form 1", "status": "Not Started", "due": "2026-10-15", "assigned": "Partner MEAL Focal", "code": "PI.1"},
        {"task": "Provide list of communities served for overlap mapping", "status": "Not Started", "due": "2026-10-15", "assigned": "Partner MEAL Focal", "code": ""},
    ],
}


def _build_meal_task_word() -> bytes:
    """Build the MEAL task-allocation Word document (21 logframe indicators
    disaggregated by Module K functional role, mapped to Means of
    Verification and a suggested task) for offline review/allocation."""
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Mm, Pt, RGBColor

    teal = RGBColor(0x1E, 0x7E, 0x76)
    muted = RGBColor(0x5E, 0x6A, 0x6A)

    _Q_MONTH_SETS = [
        {(7, 2026), (8, 2026), (9, 2026)},
        {(10, 2026), (11, 2026), (12, 2026)},
        {(1, 2027), (2, 2027), (3, 2027)},
        {(4, 2027), (5, 2027), (6, 2027)},
    ]

    def _quarter_from_date(date_str: str) -> str:
        """Same Q1-Q4 boundaries as Module A's Year 1 Quarterly Delivery Calendar."""
        if not date_str:
            return "Q1 (setup)"
        y, m = int(date_str[:4]), int(date_str[5:7])
        for i, q_set in enumerate(_Q_MONTH_SETS, start=1):
            if (m, y) in q_set:
                return f"Q{i}"
        return "—"

    def _shade_cell(cell, hex_color):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_color)
        tcPr.append(shd)

    def _mini_table(document, headers, widths, rows, accent_hex):
        table = document.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"
        hdr_cells = table.rows[0].cells
        for i, (h, w) in enumerate(zip(headers, widths)):
            hdr_cells[i].width = w
            run = hdr_cells[i].paragraphs[0].add_run(h)
            run.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.size = Pt(9)
            _shade_cell(hdr_cells[i], accent_hex)
        for row in rows:
            row_cells = table.add_row().cells
            for i, (v, w) in enumerate(zip(row, widths)):
                row_cells[i].width = w
                run = row_cells[i].paragraphs[0].add_run(v)
                run.font.size = Pt(8.5)
        return table

    def _add_section(document, heading, subtitle, tasks, examples, accent_hex):
        document.add_heading(heading, level=1)
        p = document.add_paragraph(subtitle)
        p.runs[0].italic = True
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = muted

        has_partner = any("partner" in t for t in tasks)
        if has_partner:
            ind_widths = [Cm(1.5), Cm(3.6), Cm(3.2), Cm(1.4), Cm(1.4), Cm(3.6), Cm(3.6)]
            ind_headers = ["Indicator ID", "Indicator (SMART)", "Means of Verification", "Frequency", "Y1 Quarter", "Relevant Partner(s)", "Suggested Task"]
        else:
            ind_widths = [Cm(1.8), Cm(4.6), Cm(4.0), Cm(1.6), Cm(1.7), Cm(4.0)]
            ind_headers = ["Indicator ID", "Indicator (SMART)", "Means of Verification", "Frequency", "Y1 Quarter", "Suggested Task"]
        if tasks:
            lbl = document.add_paragraph()
            lbl_run = lbl.add_run("Linked logframe indicators")
            lbl_run.bold = True
            lbl_run.font.size = Pt(8.5)
            if has_partner:
                ind_rows = [[t["id"], t["indicator"], t["mov"], t["freq"], t["quarter"], t["partner"], t["task"]] for t in tasks]
            else:
                ind_rows = [[t["id"], t["indicator"], t["mov"], t["freq"], t["quarter"], t["task"]] for t in tasks]
            _mini_table(document, ind_headers, ind_widths, ind_rows, accent_hex)
            document.add_paragraph()

        if examples:
            lbl2 = document.add_paragraph()
            lbl2_run = lbl2.add_run("Example tasks already in Module K")
            lbl2_run.bold = True
            lbl2_run.font.size = Pt(8.5)
            ex_widths = [Cm(6.0), Cm(2.0), Cm(1.8), Cm(1.6), Cm(2.8), Cm(3.5)]
            _mini_table(
                document,
                ["Task", "Status", "Due Date", "Y1 Quarter", "Assigned To", "Linked Indicator"],
                ex_widths,
                [[e["task"], e["status"], e["due"] or "—", _quarter_from_date(e["due"]), e["assigned"], e["code"] or "—"] for e in examples],
                accent_hex,
            )
        document.add_paragraph()

    document = Document()
    section = document.sections[0]
    section.page_width = Mm(297)
    section.page_height = Mm(210)
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)

    title = document.add_heading("SAWA MEAL Task Allocation", level=0)
    title.runs[0].font.color.rgb = teal

    intro = document.add_paragraph(
        "Draft for review and task allocation in Module K (Team Workspace). Every logframe "
        "indicator (21 total) disaggregated by Module K functional role, with the Means of "
        "Verification it depends on, a suggested day-to-day task, and the Year 1 quarter(s) "
        "(Q1 Jul–Sep 2026 .. Q4 Apr–Jun 2027) its evidence realistically starts being generated "
        "in — plus the 3 example tasks already seeded live in each role's Module K folder, each "
        "tagged with its quarter from its due date, for a realistic starting picture."
    )
    intro.runs[0].font.size = Pt(9.5)
    intro.runs[0].font.color.rgb = muted

    flag = document.add_paragraph()
    flag_run = flag.add_run(
        "Proposed, not yet confirmed: the logframe's Responsible column only names 3 coarse "
        "parties (CEL MEAL, Programme Team, Partner MEAL). The split below to GYSI / Biz Coach / "
        "Comms / Admin / MEAL Admin / MEAL Asst is CEL's working assignment by subject-matter fit, "
        "pending confirmation/adjustment — not sourced from the logframe itself. Biz Dev and "
        "Finance currently have no directly-linked logframe indicator, so only their example "
        "tasks from Module K appear below."
    )
    flag_run.italic = True
    flag_run.font.size = Pt(8.5)
    flag_run.font.color.rgb = RGBColor(0xB9, 0x6A, 0x2E)

    for role in _MEAL_ROLE_ORDER:
        tasks = _MEAL_TASKS_BY_ROLE.get(role, [])
        examples = _MEAL_ROLE_EXAMPLE_TASKS.get(role, [])
        n_ind = len(tasks)
        n_ex = len(examples)
        heading_bits = []
        if n_ind:
            heading_bits.append(f"{n_ind} indicator{'s' if n_ind != 1 else ''}")
        if n_ex:
            heading_bits.append(f"{n_ex} example task{'s' if n_ex != 1 else ''}")
        _add_section(
            document,
            f"{role} ({', '.join(heading_bits)})",
            _MEAL_ROLE_SUBTITLE[role],
            tasks,
            examples,
            _MEAL_ROLE_ACCENT[role],
        )

    document.add_paragraph().add_run(
        "Sources: SAWA logframe export, 29 Sep 2026 (21 rows, Module B) for the indicator tables; "
        "database/db.py team_tasks seed for the example-task tables (27 rows, 3 per K role, "
        "already live in Module K); Module A's Year 1 Quarterly Delivery Calendar and Consolidated "
        "Workplan cross-reference (BDS/WAN concept notes, 28 Sep 2026) for the Y1 Quarter column on "
        "indicators; example-task quarters are computed directly from each task's due date using the "
        "same Q1–Q4 date ranges. Frequencies and targets match the live logframe; this document adds "
        "only the functional-role split, Y1 Quarter and Suggested Task phrasing for K allocation."
    ).font.size = Pt(8)

    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


# ── Per-role MEAL Evidence Guide & Templates (auto-seeded into Module K Files) ──
# category id -> reusable evidence-template definition. 16 categories cover all
# 52 distinct Means-of-Verification phrases across the 21 logframe indicators
# (verified 1:1 below — see _role_mov_phrases / the dev script that built this).
_MOV_TEMPLATES = {
    "attendance_register": {
        "title": "Attendance Register", "kind": "table",
        "columns": ["Date", "Community / Site", "Participant Name", "Sex", "Age", "Disability (Y/N)", "Signature / Thumbprint"],
        "guidance": "Use one register per session/cohort. File the completed register in this Module K folder, referencing the linked indicator code in the file name.",
    },
    "knowledge_assessment": {
        "title": "Post-Training Knowledge Assessment", "kind": "table",
        "columns": ["Participant Name", "Pre-test Score (%)", "Post-test Score (%)", "Assessment Date", "Facilitator Notes"],
        "guidance": "Score against the module's standard assessment. Note common gaps to inform future module design.",
    },
    "safeguarding_log": {
        "title": "Safeguarding Incident Log", "kind": "table",
        "columns": ["Date Reported", "Community / Partner", "Incident Type", "Reported By", "Action Taken", "Status", "Closed Date"],
        "guidance": "Confidential — restrict access to the CEL Safeguarding Officer and MEAL Admin only.",
    },
    "safeguarding_officer_report": {
        "title": "Safeguarding Officer Report", "kind": "outline",
        "sections": ["Reporting period", "Sites / partners visited", "Findings", "Policy adoption status per partner", "Follow-up actions", "Sign-off"],
        "guidance": "One report per reporting period (quarterly for incidents; annual for policy adoption review).",
    },
    "site_certification": {
        "title": "Site Certification Checklist", "kind": "table",
        "columns": ["Site / Partner", "Standard", "Certified (Y/N)", "Certification Date", "Certifying Body", "Evidence Reference"],
        "guidance": "Review annually alongside the partner's safeguarding and occupational-health self-assessment.",
    },
    "event_report": {
        "title": "Campaign / Forum / Event Report", "kind": "outline",
        "sections": ["Event name", "Date & location", "Attendance count (disaggregated by sex/age/disability)", "Key messages / topics covered", "Community feedback summary", "Photos / evidence filed"],
        "guidance": "Complete within 5 working days of the event and file alongside the attendance register.",
    },
    "feedback_form": {
        "title": "Community Feedback Form", "kind": "table",
        "columns": ["Date", "Community", "Feedback Theme", "Details", "Follow-up Needed"],
        "guidance": "Collect at the end of each campaign/roadshow. Summarise themes in the linked event report.",
    },
    "registry": {
        "title": "Registry", "kind": "table",
        "columns": ["Name", "Role / Partner", "Contact", "Community", "Date Registered", "Status"],
        "guidance": "Keep as a living document — update status (Active/Inactive) rather than deleting entries.",
    },
    "verification_record": {
        "title": "Field Verification / Spot-Check Record", "kind": "table",
        "columns": ["Date", "Participant / Site", "Verified By", "Method", "Finding", "Follow-up Action"],
        "guidance": "Sample at least 10% of records each quarter, weighted toward higher-risk sites.",
    },
    "cooperative_governance": {
        "title": "Cooperative / Governance Record", "kind": "table",
        "columns": ["Cooperative / Cluster Name", "Registration Status", "Members (n)", "Governance Document Signed (Y/N)", "Date", "Notes"],
        "guidance": "Cross-check against KoboToolbox Tool 3 Governance Checklist submissions before closing out.",
    },
    "partner_report": {
        "title": "Partner Progress Report", "kind": "outline",
        "sections": ["Reporting period", "Partner name", "Key achievements", "Challenges", "Data submitted to CEL (Y/N)", "Next steps"],
        "guidance": "Request from each partner's MEAL focal person on the same cycle as their MoV frequency.",
    },
    "enrolment_register": {
        "title": "Enrolment / Employment Register", "kind": "table",
        "columns": ["Name", "Sex", "Age", "Disability (Y/N)", "Community", "Enrolment / Start Date", "Role / Position", "Status"],
        "guidance": "Reconcile against KoboToolbox Tool 2 submissions before reporting a count.",
    },
    "production_log": {
        "title": "Production / Trade Log", "kind": "table",
        "columns": ["Date", "Site / Partner", "Product", "Quantity (MT / units)", "Unit Price", "Notes"],
        "guidance": "Where available, cross-check against partner internal production/trade records.",
    },
    "financial_record": {
        "title": "Financial / Revenue Record", "kind": "table",
        "columns": ["Date", "Transaction Type", "Amount (USD / GHS)", "Partner / Site", "Verified By", "Evidence Reference"],
        "guidance": "Attach receipts/statements as evidence references rather than transcribing values only.",
    },
    "survey_outline": {
        "title": "Survey Instrument Outline", "kind": "outline",
        "sections": ["Purpose", "Target respondents", "Sample size", "Key questions / modules", "Frequency", "Data owner"],
        "guidance": "Draft the full instrument separately; this outline is the design brief to start from.",
    },
}

# MoV phrase -> template category id; None = lives in a digital system, not a paper template.
_MOV_TEMPLATE_MAP = {
    "Training completion certificates": "registry",
    "Focal person registry": "registry",
    "Partner reports": "partner_report",
    "WAN attendance registers": "attendance_register",
    "Forum reports": "event_report",
    "CEL field officer notes": "verification_record",
    "Event reports": "event_report",
    "Attendance lists": "attendance_register",
    "Mentor registry": "registry",
    "Match records": "verification_record",
    "Field verification notes": "verification_record",
    "Training attendance registers": "attendance_register",
    "BDS completion records": "attendance_register",
    "Training registers": "attendance_register",
    "Cooperative membership records": "cooperative_governance",
    "Signed governance documents": "cooperative_governance",
    "Field verification": "verification_record",
    "Cooperative registration documents": "cooperative_governance",
    "Enrolment registers": "enrolment_register",
    "Mobilisation partner reports": "partner_report",
    "Programme monitoring database": None,
    "Annual outcome surveys": "survey_outline",
    "Partner progress reports": "partner_report",
    "Training records": "attendance_register",
    "Safeguarding incident log": "safeguarding_log",
    "CEL safeguarding officer reports": "safeguarding_officer_report",
    "Site certification documentation": "site_certification",
    "Safeguarding policy adoption records": "safeguarding_officer_report",
    "Post-training knowledge assessment records": "knowledge_assessment",
    "Campaign reports": "event_report",
    "Attendance records": "attendance_register",
    "Community feedback forms": "feedback_form",
    "Employment records": "enrolment_register",
    "Partner payroll verification": "financial_record",
    "Field spot-checks": "verification_record",
    "PWD registry": "registry",
    "Employment and enterprise records": "enrolment_register",
    "Production logs": "production_log",
    "Catch data records": "production_log",
    "Third-party verification": "verification_record",
    "Sales receipts": "financial_record",
    "Partner financial records": "financial_record",
    "Income survey": "survey_outline",
    "Trading and processing records": "production_log",
    "Market assessment data": "survey_outline",
    "Sales records": "financial_record",
    "Market price monitoring": "financial_record",
    "Financial audits": "financial_record",
    "KoboToolbox Tool 2": None,
    "KoboToolbox Tool 3 Governance Checklist": None,
    "Governance Checklist (Tool 3)": None,
    "E-SAWA platform enrolment data": None,
}

_MOV_DIGITAL_NOTES = {
    "Programme monitoring database": "CEL's programme-wide M&E database — Module E (Data Sync & Analysis) is the primary interface.",
    "KoboToolbox Tool 2": "Partner enrolment/training data-collection tool — submissions sync into Module D (Kobo Data Sync).",
    "KoboToolbox Tool 3 Governance Checklist": "Cooperative governance checklist tool — submissions sync into Module D (Kobo Data Sync).",
    "Governance Checklist (Tool 3)": "Same tool as KoboToolbox Tool 3 Governance Checklist — submissions sync into Module D.",
    "E-SAWA platform enrolment data": "E-SAWA digital literacy platform's own enrolment records — request an export from the platform administrator.",
}


def _role_mov_phrases(tasks: list) -> list:
    seen = []
    for t in tasks:
        for phrase in [p.strip() for p in t["mov"].split(";")]:
            if phrase not in seen:
                seen.append(phrase)
    return seen


def _build_role_guide_word(role: str) -> bytes:
    """Build the per-role MEAL Evidence Guide & Templates document: the role's
    linked indicators plus blank evidence templates for each distinct Means
    of Verification they depend on — a starting resource for Module K Files."""
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Mm, Pt, RGBColor

    tasks = _MEAL_TASKS_BY_ROLE.get(role, [])
    teal = RGBColor(0x1E, 0x7E, 0x76)
    muted = RGBColor(0x5E, 0x6A, 0x6A)

    def _shade_cell(cell, hex_color):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_color)
        tcPr.append(shd)

    def _table(document, headers, widths, rows, accent_hex="1E7E76", n_blank=3):
        table = document.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"
        hdr_cells = table.rows[0].cells
        for i, (h, w) in enumerate(zip(headers, widths)):
            hdr_cells[i].width = w
            run = hdr_cells[i].paragraphs[0].add_run(h)
            run.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.size = Pt(9)
            _shade_cell(hdr_cells[i], accent_hex)
        for row in rows:
            row_cells = table.add_row().cells
            for i, (v, w) in enumerate(zip(row, widths)):
                row_cells[i].width = w
                run = row_cells[i].paragraphs[0].add_run(v)
                run.font.size = Pt(8.5)
        for _ in range(n_blank):
            row_cells = table.add_row().cells
            for i, w in enumerate(widths):
                row_cells[i].width = w
        return table

    document = Document()
    section = document.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)

    title = document.add_heading("SAWA MEAL Evidence Guide & Templates", level=0)
    title.runs[0].font.color.rgb = teal
    sub = document.add_heading(role, level=2)
    sub.runs[0].font.color.rgb = muted

    intro = document.add_paragraph(
        f"Starter guide for {role}'s Means of Verification evidence in Module K (Team Workspace). "
        f"{_MEAL_ROLE_SUBTITLE[role]} Use the templates below as a starting point — adapt fields to "
        "your partner's specific context, then save your working version back to this Module K "
        "Files folder."
    )
    intro.runs[0].font.size = Pt(10)

    document.add_heading("Your Linked Indicators", level=1)
    if tasks:
        _table(
            document,
            ["Indicator ID", "Indicator (SMART)", "Frequency", "Y1 Quarter", "Means of Verification"],
            [Cm(2.0), Cm(6.0), Cm(2.0), Cm(2.0), Cm(4.5)],
            [[t["id"], t["indicator"], t["freq"], t["quarter"], t["mov"]] for t in tasks],
            n_blank=0,
        )
    else:
        p = document.add_paragraph(
            "No logframe indicator is directly linked to this role yet — use the example tasks "
            "already in your Module K folder as your starting point."
        )
        p.runs[0].italic = True
    document.add_paragraph()

    mov_phrases = _role_mov_phrases(tasks)
    categories_used: list = []
    digital_phrases: list = []
    for phrase in mov_phrases:
        cat_id = _MOV_TEMPLATE_MAP.get(phrase)
        if cat_id is None:
            digital_phrases.append(phrase)
            continue
        existing = next((c for c in categories_used if c[0] == cat_id), None)
        if existing:
            existing[1].append(phrase)
        else:
            categories_used.append((cat_id, [phrase]))

    if categories_used:
        document.add_heading("Evidence Templates", level=1)
        for cat_id, phrases in categories_used:
            tpl = _MOV_TEMPLATES[cat_id]
            h = document.add_heading(tpl["title"], level=2)
            h.runs[0].font.color.rgb = teal
            used_for = document.add_paragraph()
            used_for_run = used_for.add_run(f"Used for: {', '.join(phrases)}")
            used_for_run.italic = True
            used_for_run.font.size = Pt(8.5)
            used_for_run.font.color.rgb = muted

            if tpl["kind"] == "table":
                n = len(tpl["columns"])
                w = round(16.0 / n, 2)
                _table(document, tpl["columns"], [Cm(w)] * n, [], n_blank=4)
            else:
                for s in tpl["sections"]:
                    p = document.add_paragraph(style="List Bullet")
                    p.add_run(f"{s}: ").bold = True
                    p.add_run("________________________________________")

            g = document.add_paragraph()
            g_run = g.add_run(tpl["guidance"])
            g_run.italic = True
            g_run.font.size = Pt(8.5)
            g_run.font.color.rgb = muted
            document.add_paragraph()

    if digital_phrases:
        document.add_heading("Digital Systems Reference", level=1)
        document.add_paragraph(
            "These Means of Verification live in a digital system rather than a paper template:"
        )
        for phrase in digital_phrases:
            p = document.add_paragraph(style="List Bullet")
            p.add_run(f"{phrase}: ").bold = True
            p.add_run(_MOV_DIGITAL_NOTES.get(phrase, "See Module D/E for this system."))
        document.add_paragraph()

    document.add_paragraph().add_run(
        "Source: SAWA logframe export, 29 Sep 2026 (Module B) for linked indicators and Means of "
        "Verification. Templates are CEL MEAL starting formats, not prescribed instruments — adapt "
        "as needed and keep your working copy in this Module K folder."
    ).font.size = Pt(8)

    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


# Auto-seed one starter guide per role into that role's Files folder, once.
# Idempotent: checks by label before inserting, so this is a no-op after the
# first successful run per project. Runs regardless of the viewer's write
# access — this is a system resource, not a user-authored task/file.
_GUIDE_LABEL_PREFIX = "MEAL Evidence Guide & Templates"
for _guide_role in _MEAL_ROLE_ORDER:
    _guide_label = f"{_GUIDE_LABEL_PREFIX} — {_guide_role}"
    _guide_exists = run_query(
        "SELECT id FROM team_files WHERE project_id=:pid AND team_role=:r AND label=:lbl LIMIT 1",
        {"pid": project_id, "r": _guide_role, "lbl": _guide_label},
    )
    if not _guide_exists:
        run_write(
            """INSERT INTO team_files
               (project_id, team_role, label, description,
                file_name, file_mime, file_data, uploaded_by, uploaded_at)
               VALUES (:pid, :role, :lbl, :desc, :fn, :fm, :fd, :by, :at)""",
            {
                "pid":  project_id,
                "role": _guide_role,
                "lbl":  _guide_label,
                "desc": "Starter guide + blank evidence templates for this role's linked "
                        "indicators — build on it, then save your working version here.",
                "fn":   f"sawa_meal_guide_{_guide_role.lower().replace(' ', '_')}.docx",
                "fm":   "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "fd":   _build_role_guide_word(_guide_role),
                "by":   "System",
                "at":   str(_date.today()),
            },
        )

# ── Layout ────────────────────────────────────────────────────────────────────
st.title("Module K — Team Workspace")
st.caption(
    "Role-based folders for tasks and evidence. "
    "Select a team role to view or add tasks and files."
)

# ── Download all tasks ─────────────────────────────────────────────────────────
_all_tasks_dl = run_query(
    """SELECT tt.team_role AS "Role", tt.task AS "Task",
              tt.description AS "Description", tt.status AS "Status",
              tt.due_date AS "Due Date", tt.assigned_to AS "Assigned To",
              lr.indicator_code AS "Indicator"
       FROM team_tasks tt
       LEFT JOIN logframe_rows lr ON lr.id = tt.logframe_row_id
       WHERE tt.project_id=:pid
       ORDER BY tt.team_role, tt.status, tt.due_date""",
    {"pid": project_id},
)
_dl_col1, _dl_col2 = st.columns(2)
with _dl_col1:
    if _all_tasks_dl:
        _dl_csv = pd.DataFrame(_all_tasks_dl).to_csv(index=False)
        st.download_button(
            "Download all tasks (CSV)",
            data=_dl_csv,
            file_name="sawa_team_tasks.csv",
            mime="text/csv",
        )
with _dl_col2:
    st.download_button(
        "📄 MEAL task allocation (Word)",
        data=_build_meal_task_word(),
        file_name="sawa_meal_task_allocation.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        help="21 logframe indicators mapped to Means of Verification and a suggested task, plus "
             "the 3 example tasks already live per role in Module K, disaggregated by all 9 K "
             "functional roles (GYSI, Biz Dev, Biz Coach, Comms, Admin, Finance, MEAL Admin, "
             "MEAL Asst, Partner MEAL) and tagged with the realistic Year 1 quarter of BDS/WAN "
             "delivery each task falls under — for review and allocation.",
    )

left, right = st.columns([1, 3])

with left:
    st.subheader("Folders")
    st.markdown("**CEL Programme Team**")
    for role in _CEL_ROLES:
        task_count = run_query(
            "SELECT COUNT(*) AS n FROM team_tasks WHERE project_id=:pid AND team_role=:r",
            {"pid": project_id, "r": role},
        )
        n = task_count[0]["n"] if task_count else 0
        label = f"{_ROLE_ICONS.get(role, '')} {role}" + (f"  `{n}`" if n else "")
        if st.button(label, key=f"role_{role}", use_container_width=True):
            st.session_state["k_selected_role"] = role

    st.markdown("**Partner**")
    for role in _PARTNER_ROLES:
        task_count = run_query(
            "SELECT COUNT(*) AS n FROM team_tasks WHERE project_id=:pid AND team_role=:r",
            {"pid": project_id, "r": role},
        )
        n = task_count[0]["n"] if task_count else 0
        label = f"{_ROLE_ICONS.get(role, '')} {role}" + (f"  `{n}`" if n else "")
        if st.button(label, key=f"role_{role}", use_container_width=True):
            st.session_state["k_selected_role"] = role

    st.markdown("**Shared**")
    for role in _SHARED_ROLES:
        task_count = run_query(
            "SELECT COUNT(*) AS n FROM team_tasks WHERE project_id=:pid AND team_role=:r",
            {"pid": project_id, "r": role},
        )
        n = task_count[0]["n"] if task_count else 0
        label = f"{_ROLE_ICONS.get(role, '')} {role}" + (f"  `{n}`" if n else "")
        if st.button(label, key=f"role_{role}", use_container_width=True):
            st.session_state["k_selected_role"] = role

# ── Default role if none selected ─────────────────────────────────────────────
if "k_selected_role" not in st.session_state:
    st.session_state["k_selected_role"] = ALL_ROLES[0]

selected_role = st.session_state["k_selected_role"]
_can_write_selected = can_write_k_role(selected_role)

with right:
    icon = _ROLE_ICONS.get(selected_role, "")
    st.subheader(f"{icon} {selected_role}")
    if not _can_write_selected:
        st.caption("🔒 View only — you don't have edit access to this folder.")

    tab_tasks, tab_files, tab_time = st.tabs(["Tasks", "Files", "Time"])

    # ── Tasks ─────────────────────────────────────────────────────────────────
    with tab_tasks:
        tasks = run_query(
            """SELECT tt.id, tt.task, tt.description, tt.status,
                      tt.due_date, tt.assigned_to, tt.created_by,
                      lr.indicator_code
               FROM team_tasks tt
               LEFT JOIN logframe_rows lr ON lr.id = tt.logframe_row_id
               WHERE tt.project_id=:pid AND tt.team_role=:r
               ORDER BY
                 CASE tt.status
                   WHEN 'In Progress' THEN 1
                   WHEN 'Not Started' THEN 2
                   WHEN 'Blocked'     THEN 3
                   WHEN 'Complete'    THEN 4
                 END,
                 tt.due_date NULLS LAST, tt.id""",
            {"pid": project_id, "r": selected_role},
        )

        if tasks:
            for t in tasks:
                fg = _STATUS_COLOUR.get(t["status"], "#555")
                badge = (
                    f'<span style="background:{fg}22;color:{fg};padding:2px 8px;'
                    f'border-radius:4px;font-size:0.75em;font-weight:700;">'
                    f'{t["status"]}</span>'
                )
                ind_tag = f' · <b style="color:#F5A820;">[{t["indicator_code"]}]</b>' if t.get("indicator_code") else ""
                due_tag = f' · due {t["due_date"]}' if t.get("due_date") else ""
                asgn    = f' · {t["assigned_to"]}' if t.get("assigned_to") else ""
                with st.container():
                    st.markdown(
                        f'{badge}{ind_tag}<br>'
                        f'<span style="font-size:0.95em;font-weight:600;">{t["task"]}</span>'
                        f'<span style="font-size:0.8em;color:#666;">{due_tag}{asgn}</span>',
                        unsafe_allow_html=True,
                    )
                    if t.get("description"):
                        st.caption(t["description"])

                    if _can_write_selected:
                        sc1, sc2 = st.columns([2, 1])
                        with sc1:
                            new_status = st.selectbox(
                                "Status",
                                STATUS_OPTS,
                                index=STATUS_OPTS.index(t["status"]) if t["status"] in STATUS_OPTS else 0,
                                key=f"ts_{t['id']}",
                                label_visibility="collapsed",
                            )
                        with sc2:
                            if st.button("Update", key=f"tu_{t['id']}"):
                                run_write(
                                    "UPDATE team_tasks SET status=:s WHERE id=:id",
                                    {"s": new_status, "id": t["id"]},
                                )
                                _log_activity(selected_role, "task_status_update")
                                st.rerun()
                    st.markdown("---")
        else:
            st.info(f"No tasks for {selected_role} yet.")

        if _can_write_selected:
            with st.expander("Add task", expanded=not tasks):
                with st.form(f"add_task_{selected_role}"):
                    nt_task = st.text_input("Task name", help="A short, specific action — this is what shows in the task list, so make it identifiable at a glance.")
                    nt_desc = st.text_area("Description (optional)", height=72, help="Extra detail or context that doesn't fit in the task name — shown as a caption under the task.")
                    tc1, tc2 = st.columns(2)
                    with tc1:
                        nt_status = st.selectbox("Status", STATUS_OPTS, key="nt_status")
                        nt_due    = st.date_input("Due date (optional)", value=None, key="nt_due", help="Leave blank for tasks with no fixed deadline.")
                    with tc2:
                        nt_asgn   = st.text_input("Assigned to", value=_username, help="Who's doing this specific task — can differ from who created it.")
                        nt_ind    = st.selectbox("Link to indicator (optional)", lf_options, key="nt_ind", help="Ties this task to a logframe indicator so it's traceable back to Module B/E — optional but useful for MEV-related tasks.")
                    if st.form_submit_button("Add task"):
                        if not nt_task.strip():
                            st.warning("Task name is required.")
                        else:
                            lf_id = None
                            if nt_ind != "None":
                                code = nt_ind.lstrip("[").split("]")[0]
                                lf_id = lf_code_to_id.get(code)
                            run_write(
                                """INSERT INTO team_tasks
                                   (project_id, team_role, task, description, status,
                                    due_date, assigned_to, logframe_row_id,
                                    created_at, created_by)
                                   VALUES (:pid, :role, :task, :desc, :st,
                                           :due, :asgn, :lf, :now, :by)""",
                                {
                                    "pid":  project_id,
                                    "role": selected_role,
                                    "task": nt_task.strip(),
                                    "desc": nt_desc.strip() or None,
                                    "st":   nt_status,
                                    "due":  str(nt_due) if nt_due else None,
                                    "asgn": nt_asgn.strip() or None,
                                    "lf":   lf_id,
                                    "now":  str(_date.today()),
                                    "by":   _username,
                                },
                            )
                            _log_activity(selected_role, "task_added")
                            st.success("Task added.")
                            st.rerun()

    # ── Files ─────────────────────────────────────────────────────────────────
    with tab_files:
        files = run_query(
            """SELECT tf.id, tf.label, tf.description, lr.indicator_code,
                      tf.link_url, tf.file_name, tf.uploaded_by, tf.uploaded_at
               FROM team_files tf
               LEFT JOIN logframe_rows lr ON lr.id = tf.logframe_row_id
               WHERE tf.project_id=:pid AND tf.team_role=:r
               ORDER BY tf.id DESC""",
            {"pid": project_id, "r": selected_role},
        )

        if files:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Label":       f["label"],
                        "Indicator":   f["indicator_code"] or "—",
                        "Description": f.get("description") or "—",
                        "Source":      f.get("link_url") or f.get("file_name") or "—",
                        "Uploaded by": f["uploaded_by"] or "—",
                        "Date":        (f["uploaded_at"] or "")[:10],
                    }
                    for f in files
                ]),
                use_container_width=True,
                hide_index=True,
            )
            for f in files:
                if f.get("file_name"):
                    _blob = run_query(
                        "SELECT file_data, file_mime FROM team_files WHERE id=:id",
                        {"id": f["id"]},
                    )
                    if _blob and _blob[0].get("file_data"):
                        st.download_button(
                            f"⬇ {f['label']}",
                            data=_blob[0]["file_data"],
                            file_name=f["file_name"],
                            mime=_blob[0].get("file_mime") or "application/octet-stream",
                            key=f"dl_tf_{f['id']}",
                        )
                elif f.get("link_url"):
                    st.markdown(f"🔗 [{f['label']}]({f['link_url']})")
        else:
            st.info(f"No files for {selected_role} yet.")

        if _can_write_selected:
            with st.expander("Upload file or add link", expanded=not files):
                with st.form(f"add_file_{selected_role}"):
                    nf_label = st.text_input("Label", help="e.g. 'GYSI training attendance Q1 2026'")
                    nf_desc  = st.text_area("Description (optional)", height=60)
                    nf_ind   = st.selectbox("Link to indicator (optional)", lf_options, key="nf_ind", help="Ties this file to a logframe indicator so it shows up as supporting evidence for it.")
                    nf_link  = st.text_input("URL / link (leave blank if uploading a file)", help="Use for a SharePoint/Drive link instead of uploading — avoids duplicating large files in the database.")
                    nf_file  = st.file_uploader(
                        "Upload file",
                        type=["pdf", "xlsx", "xls", "csv", "png", "jpg", "docx"],
                        key=f"nf_file_{selected_role}",
                    )
                    if st.form_submit_button("Save"):
                        if not nf_label.strip():
                            st.warning("Label is required.")
                        else:
                            lf_id = None
                            if nf_ind != "None":
                                code = nf_ind.lstrip("[").split("]")[0]
                                lf_id = lf_code_to_id.get(code)
                            fn, fm, fd = None, None, None
                            if nf_file is not None:
                                fn = nf_file.name
                                fm = nf_file.type
                                fd = nf_file.read()
                            run_write(
                                """INSERT INTO team_files
                                   (project_id, team_role, label, description,
                                    logframe_row_id, link_url,
                                    file_name, file_mime, file_data,
                                    uploaded_by, uploaded_at)
                                   VALUES (:pid, :role, :lbl, :desc,
                                           :lf, :url,
                                           :fn, :fm, :fd,
                                           :by, :at)""",
                                {
                                    "pid":  project_id,
                                    "role": selected_role,
                                    "lbl":  nf_label.strip(),
                                    "desc": nf_desc.strip() or None,
                                    "lf":   lf_id,
                                    "url":  nf_link.strip() or None,
                                    "fn": fn, "fm": fm, "fd": fd,
                                    "by":   _username,
                                    "at":   str(_date.today()),
                                },
                            )
                            _log_activity(selected_role, "file_added")
                            st.success("File saved.")
                            st.rerun()

    # ── Time ──────────────────────────────────────────────────────────────────
    with tab_time:
        _now = _date.today()
        _MONTHS = [
            "January","February","March","April","May","June",
            "July","August","September","October","November","December",
        ]
        tm_col1, tm_col2 = st.columns([3, 1])
        with tm_col1:
            _sel_month = st.selectbox(
                "Month", _MONTHS, index=_now.month - 1, key="time_month",
                label_visibility="collapsed",
            )
        with tm_col2:
            _sel_year = st.number_input(
                "Year", min_value=2026, max_value=2035,
                value=_now.year, step=1, key="time_year",
                label_visibility="collapsed",
            )
        _month_num = _MONTHS.index(_sel_month) + 1
        _month_prefix = f"{int(_sel_year)}-{_month_num:02d}"

        time_entries = run_query(
            """SELECT tte.id, tte.entry_date, tte.hours, tte.activity,
                      tte.task_id, tt.task AS task_name, tte.logged_by
               FROM team_time_entries tte
               LEFT JOIN team_tasks tt ON tt.id = tte.task_id
               WHERE tte.project_id=:pid AND tte.team_role=:r
                 AND tte.entry_date LIKE :pfx
               ORDER BY tte.entry_date DESC, tte.id DESC""",
            {"pid": project_id, "r": selected_role, "pfx": f"{_month_prefix}%"},
        )

        total_hours = sum(e["hours"] for e in time_entries) if time_entries else 0.0
        st.metric(
            f"Total hours — {_sel_month} {int(_sel_year)} ({selected_role})",
            f"{total_hours:.1f} hrs",
        )

        # ── Daily Activity (auto-logged — not a time-tracking measurement) ──
        _activity_rows = run_query(
            """SELECT logged_at, action_type FROM team_activity_log
               WHERE project_id=:pid AND team_role=:r AND logged_at LIKE :pfx
               ORDER BY logged_at""",
            {"pid": project_id, "r": selected_role, "pfx": f"{_month_prefix}%"},
        )
        st.markdown(f"**Daily activity — {_sel_month} {int(_sel_year)} ({selected_role})**")
        _ACT_GAP_CAP_MIN = 30
        _ACT_SOLO_CREDIT_MIN = 1
        st.caption(
            "Auto-logged every time a task is updated, a task is added, or a file/link is "
            "added. Estimated active time per day = time between consecutive actions, "
            f"capped at {_ACT_GAP_CAP_MIN} min per gap so a lunch break or overnight gap "
            "doesn't count as active (an action with nothing nearby adds "
            f"{_ACT_SOLO_CREDIT_MIN} min on its own). Streamlit can't measure how long a "
            "page actually stays open, so this is still an **estimate**, not tracked "
            "time — use **Log time** below for actual hours."
        )
        if _activity_rows:
            _act_df = pd.DataFrame(_activity_rows)
            _act_df["logged_at"] = pd.to_datetime(_act_df["logged_at"])
            _act_df["day"] = _act_df["logged_at"].dt.strftime("%Y-%m-%d")

            def _estimate_active_minutes(times: pd.Series) -> float:
                times = times.sort_values().tolist()
                total = 0.0
                for i, t in enumerate(times):
                    if i + 1 < len(times):
                        gap_min = (times[i + 1] - t).total_seconds() / 60
                        total += min(gap_min, _ACT_GAP_CAP_MIN)
                    else:
                        total += _ACT_SOLO_CREDIT_MIN
                return total

            _days_in_month = pd.Period(_month_prefix, freq="M").days_in_month
            _full_month_index = pd.date_range(
                f"{_month_prefix}-01", periods=_days_in_month, freq="D"
            ).strftime("%Y-%m-%d")
            _daily_minutes = (
                _act_df.groupby("day")["logged_at"].apply(_estimate_active_minutes)
                .reindex(_full_month_index, fill_value=0.0)
            )
            _daily_hours = (_daily_minutes / 60).rename("Estimated hours")
            _daily_hours.index.name = "Day"
            st.line_chart(_daily_hours)
            st.caption(f"Estimated total for the month: **{_daily_hours.sum():.1f} hrs**.")
        else:
            st.caption(f"No activity logged yet for {selected_role} in {_sel_month} {int(_sel_year)}.")

        # Download timesheet for all roles in the selected month
        all_time = run_query(
            """SELECT tte.entry_date AS "Date", tte.team_role AS "Role",
                      tte.activity AS "Activity", tt.task AS "Task",
                      tte.hours AS "Hours", tte.logged_by AS "Logged By"
               FROM team_time_entries tte
               LEFT JOIN team_tasks tt ON tt.id = tte.task_id
               WHERE tte.project_id=:pid AND tte.entry_date LIKE :pfx
               ORDER BY tte.entry_date, tte.team_role""",
            {"pid": project_id, "pfx": f"{_month_prefix}%"},
        )
        if all_time:
            _ts_csv = pd.DataFrame(all_time).to_csv(index=False)
            st.download_button(
                f"Download {_sel_month} {int(_sel_year)} timesheet — all roles (CSV)",
                data=_ts_csv,
                file_name=f"sawa_timesheet_{_month_prefix}.csv",
                mime="text/csv",
            )

        if time_entries:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Date":      e["entry_date"],
                        "Hours":     e["hours"],
                        "Activity":  e["activity"],
                        "Task":      e.get("task_name") or "—",
                        "Logged by": e.get("logged_by") or "—",
                    }
                    for e in time_entries
                ]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                f"No time logged for {selected_role} in {_sel_month} {int(_sel_year)}."
            )

        if _can_write_selected:
            _role_tasks = run_query(
                "SELECT id, task FROM team_tasks WHERE project_id=:pid AND team_role=:r ORDER BY task",
                {"pid": project_id, "r": selected_role},
            )
            _task_opts = ["None"] + [
                f"[{t['id']}] {t['task'][:60]}" for t in _role_tasks
            ]

            with st.expander("Log time", expanded=not time_entries):
                with st.form(f"log_time_{selected_role}_{_month_prefix}"):
                    lt1, lt2 = st.columns(2)
                    with lt1:
                        lt_date = st.date_input("Date", value=_now, key="lt_date")
                        lt_hours = st.number_input(
                            "Hours", min_value=0.5, max_value=24.0,
                            value=1.0, step=0.5, key="lt_hours",
                            help="Hours worked on this single entry — log separate entries for different activities on the same day rather than one combined total.",
                        )
                    with lt2:
                        lt_task = st.selectbox(
                            "Link to task (optional)", _task_opts, key="lt_task",
                            help="Only lists tasks already in this role's own task list — add the task first if it's missing.",
                        )
                    lt_activity = st.text_area(
                        "Activity description", height=80, key="lt_activity",
                        help="Describe what you worked on (used in monthly timesheet).",
                    )
                    if st.form_submit_button("Log time"):
                        if not lt_activity.strip():
                            st.warning("Activity description is required.")
                        else:
                            lt_task_id = None
                            if lt_task != "None":
                                lt_task_id = int(lt_task.lstrip("[").split("]")[0])
                            run_write(
                                """INSERT INTO team_time_entries
                                   (project_id, team_role, entry_date, hours,
                                    activity, task_id, logged_by, created_at)
                                   VALUES (:pid, :role, :dt, :hrs,
                                           :act, :tid, :by, :now)""",
                                {
                                    "pid":  project_id,
                                    "role": selected_role,
                                    "dt":   str(lt_date),
                                    "hrs":  float(lt_hours),
                                    "act":  lt_activity.strip(),
                                    "tid":  lt_task_id,
                                    "by":   _username,
                                    "now":  str(_date.today()),
                                },
                            )
                            st.success(f"{lt_hours:.1f} hrs logged for {selected_role}.")
                            st.rerun()

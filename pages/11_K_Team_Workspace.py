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
from datetime import date as _date

import pandas as pd
import streamlit as st

from database.db import init_db, run_query, run_write
from utils.auth import can_write_module
from utils.nav_strip import render_nav_strip
from utils.shared_widgets import project_selector

st.set_page_config(page_title="Team Workspace — CEL MEL", layout="wide")
init_db()
render_nav_strip("Input")

if not st.session_state.get("authentication_status"):
    st.error("Please log in from the main page.")
    st.stop()

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
ALL_ROLES = _CEL_ROLES + _PARTNER_ROLES

_ROLE_ICONS = {
    "GYSI":         "♀",
    "Biz Dev":      "📈",
    "Biz Coach":    "🎯",
    "Comms":        "📢",
    "Admin":        "🗂",
    "Finance":      "💰",
    "MEAL Admin":   "📊",
    "MEAL Asst":    "📋",
    "Partner MEAL": "🤝",
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

_can_write = can_write_module("K")
_username  = st.session_state.get("username", "Team")

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
    "Partner MEAL": [
        {"id": "PII.R5", "indicator": "Number of Persons with Disabilities (PWDs) accessing D&F in the Aquaculture value chain — programme-wide (YiW)",
         "mov": "Employment records; Partner payroll verification; Field spot-checks; PWD registry", "freq": "Quarterly", "quarter": "Q1–Q4",
         "task": "Verify partner payroll records; maintain the PWD registry; conduct field spot-checks"},
        {"id": "PIII.R1", "indicator": "Number of young women accessing D&F in Aquaculture Value Addition activities (YiW)",
         "mov": "Employment and enterprise records; Field verification", "freq": "Quarterly", "quarter": "Q2–Q4",
         "task": "Collect employment and enterprise records; conduct field verification"},
        {"id": "PII.R6", "indicator": "Quantity (MT) of fish produced by young women PWDs accessing D&F in the Aquaculture value chain",
         "mov": "Production logs; Catch data records; Third-party verification", "freq": "Quarterly", "quarter": "Q1–Q4",
         "task": "Collect production and catch-data logs; arrange third-party verification"},
        {"id": "PII.R7", "indicator": "Revenue (USD) generated by young women PWDs accessing D&F in the Aquaculture value chain",
         "mov": "Sales receipts; Partner financial records; Income survey", "freq": "Quarterly", "quarter": "Q1–Q4",
         "task": "Collect sales receipts; verify partner financial records; run the income survey"},
        {"id": "PIII.R2", "indicator": "Quantity (MT) of fish produced or fish-related products traded through SAWA-supported value-addition channels",
         "mov": "Trading and processing records; Market assessment data", "freq": "Quarterly", "quarter": "Q2–Q4",
         "task": "Collect trading and processing records; conduct the market assessment"},
        {"id": "PIII.R3", "indicator": "Revenue (USD) generated from trading in Value Added Aquaculture products by SAWA-supported enterprises",
         "mov": "Sales records; Market price monitoring; Financial audits", "freq": "Quarterly", "quarter": "Q2–Q4",
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

        ind_widths = [Cm(1.8), Cm(4.6), Cm(4.0), Cm(1.6), Cm(1.7), Cm(4.0)]
        if tasks:
            lbl = document.add_paragraph()
            lbl_run = lbl.add_run("Linked logframe indicators")
            lbl_run.bold = True
            lbl_run.font.size = Pt(8.5)
            _mini_table(
                document,
                ["Indicator ID", "Indicator (SMART)", "Means of Verification", "Frequency", "Y1 Quarter", "Suggested Task"],
                ind_widths,
                [[t["id"], t["indicator"], t["mov"], t["freq"], t["quarter"], t["task"]] for t in tasks],
                accent_hex,
            )
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

# ── Default role if none selected ─────────────────────────────────────────────
if "k_selected_role" not in st.session_state:
    st.session_state["k_selected_role"] = ALL_ROLES[0]

selected_role = st.session_state["k_selected_role"]

with right:
    icon = _ROLE_ICONS.get(selected_role, "")
    st.subheader(f"{icon} {selected_role}")

    tab_tasks, tab_files = st.tabs(["Tasks", "Files"])

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
                ind_tag = f' · <b style="color:#0891B2;">[{t["indicator_code"]}]</b>' if t.get("indicator_code") else ""
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

                    if _can_write:
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
                                st.rerun()
                    st.markdown("---")
        else:
            st.info(f"No tasks for {selected_role} yet.")

        if _can_write:
            with st.expander("Add task", expanded=not tasks):
                with st.form(f"add_task_{selected_role}"):
                    nt_task = st.text_input("Task name")
                    nt_desc = st.text_area("Description (optional)", height=72)
                    tc1, tc2 = st.columns(2)
                    with tc1:
                        nt_status = st.selectbox("Status", STATUS_OPTS, key="nt_status")
                        nt_due    = st.date_input("Due date (optional)", value=None, key="nt_due")
                    with tc2:
                        nt_asgn   = st.text_input("Assigned to", value=_username)
                        nt_ind    = st.selectbox("Link to indicator (optional)", lf_options, key="nt_ind")
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
        else:
            st.info(f"No files for {selected_role} yet.")

        if _can_write:
            with st.expander("Upload file or add link", expanded=not files):
                with st.form(f"add_file_{selected_role}"):
                    nf_label = st.text_input("Label", help="e.g. 'GYSI training attendance Q1 2026'")
                    nf_desc  = st.text_area("Description (optional)", height=60)
                    nf_ind   = st.selectbox("Link to indicator (optional)", lf_options, key="nf_ind")
                    nf_link  = st.text_input("URL / link (leave blank if uploading a file)")
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
                            st.success("File saved.")
                            st.rerun()

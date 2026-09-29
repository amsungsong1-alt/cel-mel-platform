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
# Maps every logframe indicator to its Responsible party, Means of Verification
# and a suggested day-to-day task, for offline review/allocation under Module K.
_MEAL_CEL_TASKS = [
    {"id": "LoP.1", "indicator": "Number of financially disadvantaged young women and PWDs engaged in dignified and fulfilling work across the aquaculture value chain",
     "mov": "Programme monitoring database; Annual outcome surveys; Partner progress reports", "freq": "Annual",
     "task": "Maintain the programme monitoring database; commission and administer the annual outcome survey; consolidate partner progress reports"},
    {"id": "PI.19", "indicator": "Number of persons (participants and community champions) receiving gender-transformative training",
     "mov": "Training attendance registers; Post-training knowledge assessment records", "freq": "Quarterly",
     "task": "Collect and verify attendance registers; administer and score post-training knowledge assessments"},
    {"id": "PI.20", "indicator": "Number of young women trained to identify and respond to safeguarding issues (PSEA awareness)",
     "mov": "Training records; Safeguarding incident log; CEL safeguarding officer reports", "freq": "Quarterly",
     "task": "Maintain the safeguarding incident log; compile safeguarding officer reports"},
    {"id": "PI.22", "indicator": "Number of safeguarding awareness campaigns and roadshows undertaken in SAWA intervention communities",
     "mov": "Campaign reports; Attendance records; Community feedback forms", "freq": "Quarterly",
     "task": "Produce campaign reports; collect attendance records and community feedback forms"},
    {"id": "PI.23", "indicator": "Number of programme sites/partners with institutionalised safeguarding and occupational health standards",
     "mov": "Site certification documentation; Safeguarding policy adoption records", "freq": "Annual",
     "task": "Verify and file site certification documentation; track safeguarding policy adoption records"},
]
_MEAL_PROGRAMME_TASKS = [
    {"id": "PI.1", "indicator": "Number of young women and PWDs mobilised, sensitised and enrolled in SAWA D&F value-chain activities",
     "mov": "Enrolment registers; Mobilisation partner reports; KoboToolbox Tool 2", "freq": "Quarterly",
     "task": "Sync KoboToolbox Tool 2; reconcile enrolment registers with partner mobilisation reports"},
    {"id": "PI.3", "indicator": "Number of young women and PWDs completing Business Development Services (BDS) training",
     "mov": "Training attendance registers; BDS completion records; KoboToolbox Tool 2", "freq": "Quarterly",
     "task": "Sync KoboToolbox Tool 2; verify BDS completion records against attendance registers"},
    {"id": "PI.9", "indicator": "Number of GYSI focal persons trained in GALS and EMAP (Training of Trainers model, per implementing partner)",
     "mov": "Training completion certificates; Focal person registry; Partner reports", "freq": "Quarterly",
     "task": "Issue and file completion certificates; maintain the focal person registry"},
    {"id": "PI.11", "indicator": "Number of women engaged in leadership and mentorship forums under the Women in Aquaculture Network (WAN)",
     "mov": "WAN attendance registers; Forum reports; CEL field officer notes", "freq": "Quarterly",
     "task": "Collect WAN attendance registers; compile forum reports from field officer notes"},
    {"id": "PI.12", "indicator": "Number of leadership bootcamps and inter-zonal exchange visits organised under WAN",
     "mov": "Event reports; Attendance lists; CEL field officer notes", "freq": "Quarterly",
     "task": "Produce event reports; collect attendance lists"},
    {"id": "PI.13", "indicator": "Number of young female PWDs identified as peer mentors and matched with PWD programme participants",
     "mov": "Mentor registry; Match records; Field verification notes", "freq": "Quarterly",
     "task": "Maintain the mentor registry; log mentor-mentee matches and field verification"},
    {"id": "PI.17", "indicator": "Number of women in women-led cooperatives/clusters receiving gender training, financial literacy and business mentoring",
     "mov": "Training registers; Cooperative membership records; Partner reports", "freq": "Quarterly",
     "task": "Maintain training registers; verify cooperative membership records"},
    {"id": "PI.18", "indicator": "Number of gender-responsive governance frameworks adopted by women-led cooperatives/clusters",
     "mov": "Signed governance documents; KoboToolbox Tool 3 Governance Checklist; Field verification", "freq": "Quarterly",
     "task": "Collect signed governance documents; complete Tool 3 Governance Checklist"},
    {"id": "PIV.5", "indicator": "Number of young women receiving E-SAWA digital literacy training, mentorship and digital entrepreneurship workshops",
     "mov": "Training attendance registers; E-SAWA platform enrolment data", "freq": "Quarterly",
     "task": "Pull E-SAWA platform enrolment data; reconcile against attendance registers"},
    {"id": "PIII.6", "indicator": "Number of women-led cooperatives/clusters strengthened across the aquaculture value chain (established and registered entities)",
     "mov": "Cooperative registration documents; Governance Checklist (Tool 3); Field verification", "freq": "Quarterly",
     "task": "File cooperative registration documents; complete Tool 3 Governance Checklist"},
]
_MEAL_PARTNER_TASKS = [
    {"id": "PII.R5", "indicator": "Number of Persons with Disabilities (PWDs) accessing D&F in the Aquaculture value chain — programme-wide (YiW)",
     "mov": "Employment records; Partner payroll verification; Field spot-checks; PWD registry", "freq": "Quarterly",
     "task": "Verify partner payroll records; maintain the PWD registry; conduct field spot-checks"},
    {"id": "PIII.R1", "indicator": "Number of young women accessing D&F in Aquaculture Value Addition activities (YiW)",
     "mov": "Employment and enterprise records; Field verification", "freq": "Quarterly",
     "task": "Collect employment and enterprise records; conduct field verification"},
    {"id": "PII.R6", "indicator": "Quantity (MT) of fish produced by young women PWDs accessing D&F in the Aquaculture value chain",
     "mov": "Production logs; Catch data records; Third-party verification", "freq": "Quarterly",
     "task": "Collect production and catch-data logs; arrange third-party verification"},
    {"id": "PII.R7", "indicator": "Revenue (USD) generated by young women PWDs accessing D&F in the Aquaculture value chain",
     "mov": "Sales receipts; Partner financial records; Income survey", "freq": "Quarterly",
     "task": "Collect sales receipts; verify partner financial records; run the income survey"},
    {"id": "PIII.R2", "indicator": "Quantity (MT) of fish produced or fish-related products traded through SAWA-supported value-addition channels",
     "mov": "Trading and processing records; Market assessment data", "freq": "Quarterly",
     "task": "Collect trading and processing records; conduct the market assessment"},
    {"id": "PIII.R3", "indicator": "Revenue (USD) generated from trading in Value Added Aquaculture products by SAWA-supported enterprises",
     "mov": "Sales records; Market price monitoring; Financial audits", "freq": "Quarterly",
     "task": "Collect sales records; monitor market prices; support financial audits"},
]


def _build_meal_task_word() -> bytes:
    """Build the MEAL task-allocation Word document (21 logframe indicators
    grouped by Responsible party, mapped to Means of Verification and a
    suggested task) for offline review/allocation under Module K."""
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Mm, Pt, RGBColor

    teal = RGBColor(0x1E, 0x7E, 0x76)
    muted = RGBColor(0x5E, 0x6A, 0x6A)

    def _shade_cell(cell, hex_color):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_color)
        tcPr.append(shd)

    def _add_section(document, heading, subtitle, tasks, accent_hex):
        document.add_heading(heading, level=1)
        p = document.add_paragraph(subtitle)
        p.runs[0].italic = True
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = muted

        table = document.add_table(rows=1, cols=5)
        table.style = "Table Grid"
        widths = [Cm(2.0), Cm(5.2), Cm(4.6), Cm(2.0), Cm(4.6)]
        headers = ["Indicator ID", "Indicator (SMART)", "Means of Verification", "Frequency", "Suggested Task"]
        hdr_cells = table.rows[0].cells
        for i, (h, w) in enumerate(zip(headers, widths)):
            hdr_cells[i].width = w
            run = hdr_cells[i].paragraphs[0].add_run(h)
            run.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.size = Pt(9)
            _shade_cell(hdr_cells[i], accent_hex)

        for t in tasks:
            row_cells = table.add_row().cells
            for i, (v, w) in enumerate(zip([t["id"], t["indicator"], t["mov"], t["freq"], t["task"]], widths)):
                row_cells[i].width = w
                run = row_cells[i].paragraphs[0].add_run(v)
                run.font.size = Pt(8.5)
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
        "indicator (21 total) grouped by its Responsible party, with the Means of Verification "
        "it depends on and a suggested day-to-day task. CEL MEAL's tasks are grouped with the "
        "Assistant MEAL Officer, who holds write access to Modules D-G where most of this "
        "verification work happens in practice."
    )
    intro.runs[0].font.size = Pt(9.5)
    intro.runs[0].font.color.rgb = muted

    _add_section(
        document, "CEL MEAL (MEAL Admin + Assistant MEAL Officer)",
        "5 indicators — programme-level monitoring, safeguarding evidence and the annual outcome survey.",
        _MEAL_CEL_TASKS, "1E7E76",
    )
    _add_section(
        document, "Programme Team",
        "10 indicators — mobilisation, training, WAN and cooperative delivery evidence across partners.",
        _MEAL_PROGRAMME_TASKS, "4A6B5C",
    )
    _add_section(
        document, "Partner MEAL",
        "6 indicators — outcome-level D&F jobs, production and revenue data verified at partner level.",
        _MEAL_PARTNER_TASKS, "B96A2E",
    )

    document.add_paragraph().add_run(
        "Source: SAWA logframe export, 29 Sep 2026 (21 rows, Module B). Frequencies and targets "
        "match the live logframe; this document adds only the Suggested Task phrasing for K allocation."
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
        help="21 logframe indicators mapped to Means of Verification and a suggested task, "
             "grouped by CEL MEAL, Programme Team and Partner MEAL — for review and allocation.",
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

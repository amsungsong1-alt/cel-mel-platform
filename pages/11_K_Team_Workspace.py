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
if _all_tasks_dl:
    _dl_csv = pd.DataFrame(_all_tasks_dl).to_csv(index=False)
    st.download_button(
        "Download all tasks (CSV)",
        data=_dl_csv,
        file_name="sawa_team_tasks.csv",
        mime="text/csv",
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

        if _can_write:
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
                        )
                    with lt2:
                        lt_task = st.selectbox(
                            "Link to task (optional)", _task_opts, key="lt_task",
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

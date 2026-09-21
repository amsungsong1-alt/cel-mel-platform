"""Module G — Decision Reports

Structured report generator that assembles directly from Modules D and F —
minimise re-typing by pre-populating from flagged indicator rows or review-log
entries with follow_up_required = 'Y'.

Key behaviours
--------------
• Three clearly bordered sections: Problem Description / Investigation /
  Approved Actions.
• Actions table is an editable sub-table (one-to-many per report).
• Dashboard tab: all reports by status; overdue actions at the top in red.
• Export as Word (.docx) via python-docx — three-section layout, CEL branding.
• Arriving from Module E or F pre-populates indicator, target, definition,
  and actual value so the PM only types investigation notes and actions.

Session state keys consumed
---------------------------
  g_indicator_ids : list[int]  logframe_row_ids forwarded from Module E/F
  g_source        : str        label of the source (e.g. "Module F — Performance review")
  g_edit_report_id: int | None  set by Dashboard "Open" button
"""
from __future__ import annotations

import io
from datetime import date

import pandas as pd
import streamlit as st

from database.db import init_db, run_query, run_write, insert_returning_id
from utils.shared_widgets import project_selector
from utils.auth import can, can_write_module
from utils.nav_strip import render_nav_strip

st.set_page_config(page_title="Decision Reports — CEL MEL", layout="wide")
init_db()
render_nav_strip("Decide")

if not st.session_state.get("authentication_status"):
    st.error("Please log in from the main page.")
    st.stop()

with st.sidebar:
    project_id = project_selector()
    if project_id is None:
        st.stop()
    st.divider()
    st.caption(f"Role: **{st.session_state.get('role', 'Viewer')}**")

# ── Brand colours ─────────────────────────────────────────────────────────────
NAVY = "#0D2B5E"
GOLD = "#C8A951"

# ── Constants ─────────────────────────────────────────────────────────────────
REPORT_STATUSES = ["Draft", "Under review", "Approved", "Closed"]
ACTION_STATUSES = [
    "No action needed - data reporting only",
    "Inform decision-maker/confirm next steps",
    "Follow-up or investigate",
    "Change/adapt/revise",
    "Resolved",
]
STATUS_STYLE = {
    "Draft":        ("#FFF8E1", "#E65100"),
    "Under review": ("#E3F2FD", "#1565C0"),
    "Approved":     ("#E8F5E9", "#2E7D32"),
    "Closed":       ("#F3E5F5", "#6A1B9A"),
}
DATA_TYPES = [
    "Performance", "Assumption", "Stakeholder",
    "Process", "Problem", "Solution", "Attribution",
]

# ── Session state ─────────────────────────────────────────────────────────────
for _k, _v in [("g_edit_report_id", None)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Load logframe rows (used in both tabs) ────────────────────────────────────
lf_rows = run_query(
    """SELECT id, indicator_code, result_level, indicator_statement,
              target_annual, target_lop
       FROM   logframe_rows
       WHERE  project_id = :pid ORDER BY id""",
    {"pid": project_id},
)
lf_by_id    = {r["id"]: r for r in lf_rows}
lf_opts     = [f"{r['indicator_code']} — {(r['indicator_statement'] or '')[:55]}…"
               if len(r.get("indicator_statement") or "") > 55
               else f"{r['indicator_code']} — {r['indicator_statement']}"
               for r in lf_rows]
lf_id_for_opt = {opt: r["id"] for opt, r in zip(lf_opts, lf_rows)}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _section_band(number: str, title: str) -> None:
    border = f"border-left:5px solid {GOLD}"
    st.markdown(
        f'<div style="background:{NAVY};color:white;padding:8px 16px;'
        f'{border};margin:20px 0 6px 0;font-weight:bold;letter-spacing:0.5px;">'
        f"SECTION {number} — {title.upper()}</div>",
        unsafe_allow_html=True,
    )


def _report_header_html(report_id, date_str: str, status: str, created_by: str) -> None:
    rid     = f"RPT-{report_id}" if report_id else "RPT-DRAFT"
    bg, fg  = STATUS_STYLE.get(status, ("#F5F5F5", "#333"))
    st.markdown(
        f'<div style="background:{NAVY};color:white;padding:14px 20px;'
        'border-radius:6px 6px 0 0;">'
        f'<span style="color:{GOLD};font-size:1.2em;font-weight:bold;">'
        'SAWA — DECISION REPORT</span>'
        f'<span style="float:right;font-size:0.8em;opacity:0.85;">'
        f'{rid} &nbsp;|&nbsp; {date_str} &nbsp;|&nbsp; {created_by or "—"}'
        '</span><br>'
        '<span style="font-size:0.75em;opacity:0.65;">CEL MEL Platform · Module G</span>'
        '</div>'
        f'<div style="height:3px;background:{GOLD};"></div>'
        f'<div style="background:{bg};color:{fg};padding:4px 16px;'
        'font-size:0.83em;font-weight:bold;margin-bottom:12px;">'
        f'Status: {status or "Draft"}</div>',
        unsafe_allow_html=True,
    )


def _prefill_from_lf(lf_row_id: int) -> dict:
    """Build pre-fill dict from a logframe_rows + raw_data_analysis row."""
    lf = lf_by_id.get(lf_row_id, {})
    rda = run_query(
        """SELECT actual_q1, actual_q2, actual_q3, actual_q4
           FROM   raw_data_analysis
           WHERE  logframe_row_id = :id AND project_id = :pid LIMIT 1""",
        {"id": lf_row_id, "pid": project_id},
    )
    rda = rda[0] if rda else {}
    q_parts = [f"Q{i}: {rda.get(f'actual_q{i}')}"
               for i in range(1, 5) if rda.get(f"actual_q{i}")]
    return {
        "lf_row_id":           lf_row_id,
        "target_value":        lf.get("target_annual") or lf.get("target_lop") or "",
        "indicator_definition": lf.get("indicator_statement") or "",
        "actual_value":        "; ".join(q_parts) if q_parts else "Not yet collected",
    }


def _load_reports() -> list[dict]:
    return run_query(
        """SELECT id, created_date, created_by, logframe_row_id,
                  target_value, indicator_definition, assumed_pattern, actual_value,
                  review_category, specific_focus_area, investigation_notes,
                  key_finding, status
           FROM   decision_reports
           WHERE  project_id = :pid
           ORDER  BY created_date DESC""",
        {"pid": project_id},
    )


def _parse_date(s) -> "date | None":
    """Convert a YYYY-MM-DD string (or None/empty) to a datetime.date object."""
    if not s:
        return None
    try:
        return date.fromisoformat(str(s))
    except (ValueError, TypeError):
        return None


def _load_actions(report_id: int) -> list[dict]:
    return run_query(
        """SELECT id, decision_maker, action, action_due_date, action_status
           FROM   decision_actions WHERE report_id = :rid ORDER BY id""",
        {"rid": report_id},
    )


def _export_docx(report: dict, actions: list[dict]) -> bytes:
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn as oxml_qn
    except ImportError as exc:
        raise ImportError("python-docx not installed. Run: pip install python-docx") from exc

    def shade_cell(cell, hex_col: str) -> None:
        tc_pr = cell._tc.get_or_add_tcPr()
        shd   = OxmlElement("w:shd")
        shd.set(oxml_qn("w:val"),   "clear")
        shd.set(oxml_qn("w:color"), "auto")
        shd.set(oxml_qn("w:fill"),  hex_col)
        tc_pr.append(shd)

    NAVY_RGB = RGBColor(0x0D, 0x2B, 0x5E)
    GOLD_RGB = RGBColor(0xC8, 0xA9, 0x51)

    doc = Document()
    for sec in doc.sections:
        sec.top_margin    = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin   = Inches(1.0)
        sec.right_margin  = Inches(1.0)

    # Title
    title_para = doc.add_heading("SAWA — Decision Report", 0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title_para.runs:
        run.font.color.rgb = NAVY_RGB

    rid_str = f"RPT-{report.get('id', 'DRAFT')}"
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run(
        f"{rid_str}  ·  {report.get('created_date', '')}  ·  "
        f"Status: {report.get('status', 'Draft')}  ·  "
        f"Created by: {report.get('created_by', '')}"
    ).font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    doc.add_paragraph()

    lf = lf_by_id.get(report.get("logframe_row_id") or -1, {})

    for sect_num, sect_title, fields in [
        ("1", "Problem Description", [
            ("Indicator",            lf.get("indicator_code", "—")),
            ("Target Value",         report.get("target_value") or "—"),
            ("Indicator Definition", report.get("indicator_definition") or "—"),
            ("Assumed Pattern",      report.get("assumed_pattern") or "—"),
            ("Actual Value",         report.get("actual_value") or "—"),
        ]),
        ("2", "Investigation", [
            ("Review Category",      report.get("review_category") or "—"),
            ("Specific Focus Area",  report.get("specific_focus_area") or "—"),
            ("Investigation Notes",  report.get("investigation_notes") or "—"),
            ("Key Finding",          report.get("key_finding") or "—"),
        ]),
    ]:
        hdr = doc.add_heading(f"{sect_num}. {sect_title}", 1)
        hdr.runs[0].font.color.rgb = NAVY_RGB

        tbl = doc.add_table(rows=len(fields), cols=2)
        tbl.style = "Table Grid"
        tbl.columns[0].width = Inches(1.8)
        tbl.columns[1].width = Inches(5.0)
        for i, (label, val) in enumerate(fields):
            shade_cell(tbl.rows[i].cells[0], "D9E2F3")
            tbl.rows[i].cells[0].text = label
            run = tbl.rows[i].cells[0].paragraphs[0].runs[0]
            run.font.bold        = True
            run.font.color.rgb   = NAVY_RGB
            run.font.size        = Pt(10)
            tbl.rows[i].cells[1].text = str(val)
            tbl.rows[i].cells[1].paragraphs[0].runs[0].font.size = Pt(10)
        doc.add_paragraph()

    # Section 3 — Actions
    hdr3 = doc.add_heading("3. Approved Actions", 1)
    hdr3.runs[0].font.color.rgb = NAVY_RGB

    if actions:
        act_tbl = doc.add_table(rows=len(actions) + 1, cols=4)
        act_tbl.style = "Table Grid"
        for j, hd in enumerate(["Decision Maker", "Action", "Due Date", "Status"]):
            c = act_tbl.rows[0].cells[j]
            shade_cell(c, "0D2B5E")
            c.text = hd
            run    = c.paragraphs[0].runs[0]
            run.font.bold      = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.size      = Pt(10)
        for i, act in enumerate(actions, 1):
            act_tbl.rows[i].cells[0].text = act.get("decision_maker") or "—"
            act_tbl.rows[i].cells[1].text = act.get("action") or "—"
            act_tbl.rows[i].cells[2].text = act.get("action_due_date") or "—"
            act_tbl.rows[i].cells[3].text = act.get("action_status") or "—"
    else:
        doc.add_paragraph("No actions recorded.")

    doc.add_paragraph()
    foot = doc.add_paragraph("Generated by CEL MEL Platform — Module G")
    foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    foot.runs[0].font.color.rgb = RGBColor(0xAA, 0xAA, 0xAA)
    foot.runs[0].font.size      = Pt(8)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE
# ═══════════════════════════════════════════════════════════════════════════════
st.title("Module G — Decision Reports")
st.caption(
    "Structured investigation and action reports. "
    "Pre-seeded from Module E (flagged indicators) or Module F (review-log follow-ups) "
    "to minimise re-typing."
)

# Pre-seed banner
incoming_ids = list(st.session_state.get("g_indicator_ids") or [])
incoming_src = st.session_state.get("g_source", "")
if incoming_ids:
    st.success(
        f"📋 Pre-seeded from **{incoming_src or 'Module E/F'}** — "
        f"{len(incoming_ids)} indicator(s) loaded. "
        "Open the **📝 Report Editor** tab below to create a report.",
        icon="📋",
    )

tab_dash, tab_edit = st.tabs(["📊 Dashboard", "📝 Report Editor"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    # ── Overdue actions — most visible element ────────────────────────────────
    overdue_actions = run_query(
        """SELECT da.id, da.decision_maker, da.action, da.action_due_date,
                  da.action_status, dr.id AS report_id, dr.review_category,
                  dr.created_date,
                  lf.indicator_code
           FROM   decision_actions da
           JOIN   decision_reports dr ON dr.id = da.report_id
           LEFT   JOIN logframe_rows lf ON lf.id = dr.logframe_row_id
           WHERE  dr.project_id = :pid
             AND  da.action_due_date < :today
             AND  da.action_status != 'Resolved'
           ORDER  BY da.action_due_date ASC""",
        {"pid": project_id, "today": date.today().isoformat()},
    )

    if overdue_actions:
        st.error(
            f"⛔ **{len(overdue_actions)} overdue action(s)** — "
            "these decision reports have unclosed actions past their due date."
        )
        od_df = pd.DataFrame(overdue_actions).rename(columns={
            "report_id":       "Report",
            "indicator_code":  "Indicator",
            "review_category": "Type",
            "decision_maker":  "Owner",
            "action":          "Action",
            "action_due_date": "Due date",
            "action_status":   "Status",
        }).drop(columns=["id", "created_date"])
        od_df["Report"] = od_df["Report"].apply(lambda x: f"RPT-{x}")

        def _overdue_css(val) -> str:
            return "background-color:#FFEBEE;color:#C62828;" if val != "Resolved" else ""

        try:
            styled_od = od_df.style.map(_overdue_css, subset=["Status"])
        except AttributeError:
            styled_od = od_df.style.applymap(_overdue_css, subset=["Status"])

        st.dataframe(styled_od, hide_index=True, use_container_width=True)
    else:
        st.success("No overdue actions — all decision report actions are on track or resolved.")

    st.divider()

    # ── Reports by status ─────────────────────────────────────────────────────
    st.subheader("All Reports")
    all_reports = _load_reports()

    if not all_reports:
        st.info(
            "No decision reports yet. "
            "Run `python -m database.seed_sawa` to load the SAWA example report, "
            "or create one in the Report Editor tab."
        )
    else:
        for status in REPORT_STATUSES:
            status_reports = [r for r in all_reports if r.get("status") == status]
            if not status_reports:
                continue
            bg, fg = STATUS_STYLE.get(status, ("#F5F5F5", "#333"))
            with st.expander(
                f"**{status}** ({len(status_reports)})",
                expanded=(status in ("Draft", "Under review")),
            ):
                for r in status_reports:
                    lf = lf_by_id.get(r.get("logframe_row_id") or -1, {})
                    ind_code  = lf.get("indicator_code", "—")
                    review_cat = r.get("review_category") or "—"
                    rc1, rc2, rc3 = st.columns([3, 2, 1])
                    with rc1:
                        st.markdown(
                            f"**RPT-{r['id']}** &nbsp;·&nbsp; {review_cat} &nbsp;·&nbsp; "
                            f"`{ind_code}` &nbsp;·&nbsp; {r.get('created_date', '—')}"
                        )
                        kf = r.get("key_finding") or ""
                        st.caption(kf[:120] + "…" if len(kf) > 120 else kf)
                    with rc2:
                        actions = _load_actions(r["id"])
                        n_open  = sum(1 for a in actions if a.get("action_status") != "Resolved")
                        n_total = len(actions)
                        if n_open:
                            st.warning(f"{n_open}/{n_total} action(s) open", icon="⚠️")
                        else:
                            st.success(f"All {n_total} action(s) resolved", icon="✅")
                    with rc3:
                        if st.button("Open", key=f"open_{r['id']}", use_container_width=True):
                            st.session_state["g_edit_report_id"] = r["id"]
                            st.rerun()
                    st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — REPORT EDITOR
# ═══════════════════════════════════════════════════════════════════════════════
with tab_edit:
    if not can_write_module("G"):
        st.info("Viewer access: report editing requires Editor or Admin role.")
        st.stop()

    all_reports  = _load_reports()

    # Report selector
    def _report_label(r: dict) -> str:
        lf   = lf_by_id.get(r.get("logframe_row_id") or -1, {})
        code = lf.get("indicator_code", "?")
        cat  = r.get("review_category") or "?"
        return f"RPT-{r['id']}: {cat} · {code} · {r.get('created_date', '?')} ({r.get('status', '?')})"

    sel_opts = ["— New report —"] + [_report_label(r) for r in all_reports]

    # Default selection from Dashboard "Open" button
    default_idx = 0
    if st.session_state.get("g_edit_report_id") is not None:
        for i, r in enumerate(all_reports, 1):
            if r["id"] == st.session_state["g_edit_report_id"]:
                default_idx = i
                break
        st.session_state["g_edit_report_id"] = None

    sel = st.selectbox("Report", sel_opts, index=default_idx, key="g_report_sel")

    is_new       = (sel == "— New report —")
    active       = {} if is_new else all_reports[sel_opts.index(sel) - 1]
    active_id    = None if is_new else active["id"]
    existing_actions = [] if is_new else _load_actions(active_id)

    # Pre-fill logic: use incoming data only when creating a new report
    prefill: dict = {}
    if is_new and incoming_ids:
        prefill = _prefill_from_lf(incoming_ids[0])

    st.divider()

    # ── REPORT HEADER ─────────────────────────────────────────────────────────
    _report_header_html(
        active_id,
        active.get("created_date") or date.today().isoformat(),
        active.get("status") or "Draft",
        active.get("created_by") or st.session_state.get("username", ""),
    )

    # ── SECTION 1 — PROBLEM DESCRIPTION ──────────────────────────────────────
    _section_band("1", "Problem Description")

    # Indicator selectbox drives auto-fill
    current_lf_id  = active.get("logframe_row_id") or prefill.get("lf_row_id")
    current_lf_opt = next(
        (opt for opt, lid in lf_id_for_opt.items() if lid == current_lf_id),
        lf_opts[0] if lf_opts else "",
    )
    sel_lf = st.selectbox(
        "Indicator",
        options=lf_opts,
        index=lf_opts.index(current_lf_opt) if current_lf_opt in lf_opts else 0,
        key="g_indicator_sel",
    )
    chosen_lf_id = lf_id_for_opt.get(sel_lf)
    pf = prefill if (is_new and chosen_lf_id == prefill.get("lf_row_id")) else (
        _prefill_from_lf(chosen_lf_id) if (is_new and chosen_lf_id) else {}
    )

    s1c1, s1c2 = st.columns(2)
    with s1c1:
        target_value = st.text_input(
            "Target value",
            value=active.get("target_value") or pf.get("target_value") or "",
        )
    with s1c2:
        actual_value = st.text_input(
            "Actual value (at time of investigation)",
            value=active.get("actual_value") or pf.get("actual_value") or "",
        )
    indicator_definition = st.text_area(
        "Indicator definition",
        value=active.get("indicator_definition") or pf.get("indicator_definition") or "",
        height=70,
    )
    assumed_pattern = st.text_area(
        "Assumed pattern — what the data was expected to show",
        value=active.get("assumed_pattern") or "",
        height=90,
        placeholder="Describe the expected pattern and why the gap / mismatch is significant.",
    )

    # ── SECTION 2 — INVESTIGATION ─────────────────────────────────────────────
    _section_band("2", "Investigation")

    s2c1, s2c2 = st.columns(2)
    with s2c1:
        review_category = st.selectbox(
            "Review category (data type)",
            options=DATA_TYPES,
            index=(
                DATA_TYPES.index(active["review_category"])
                if active.get("review_category") in DATA_TYPES
                else 0
            ),
        )
    with s2c1:
        # Strategic alignment badge (Laudon & Laudon, 16e — Ch. 1 strategic objectives)
        _IS_OBJECTIVE_MAP = {
            "Performance": ("Improved Decision Making",
                            "Evidence on results informs programme adjustments.",
                            "#1565C0"),
            "Assumption":  ("Survival / Risk Management",
                            "Testing assumptions reduces strategic and operational risk.",
                            "#6A1B9A"),
            "Stakeholder": ("Customer & Supplier Intimacy",
                            "Understanding stakeholder experience deepens partner relationships.",
                            "#2E7D32"),
            "Process":     ("Operational Excellence",
                            "Process findings identify inefficiencies in delivery.",
                            "#E65100"),
            "Problem":     ("Survival",
                            "Barrier identification is essential for programme continuation.",
                            "#B71C1C"),
            "Solution":    ("New Products / Business Models",
                            "Solution reviews assess whether new approaches are working.",
                            "#00695C"),
            "Attribution": ("Competitive Advantage",
                            "Attribution evidence positions SAWA for scale and investment.",
                            "#4527A0"),
        }
        obj_label, obj_note, obj_colour = _IS_OBJECTIVE_MAP.get(
            review_category,
            ("Operational Excellence", "", "#E65100"),
        )
        st.markdown(
            f'<div style="border:1px solid {obj_colour}60;background:{obj_colour}10;'
            f'border-radius:4px;padding:6px 10px;margin-top:4px;">'
            f'<span style="font-size:0.74em;color:#555;">🎯 IS Strategic Objective</span><br>'
            f'<span style="font-weight:bold;color:{obj_colour};font-size:0.85em;">'
            f'{obj_label}</span>'
            + (f'<br><span style="font-size:0.72em;color:#666;">{obj_note}</span>'
               if obj_note else "")
            + "</div>",
            unsafe_allow_html=True,
        )

    with s2c2:
        specific_focus = st.text_input(
            "Specific focus area",
            value=active.get("specific_focus_area") or "",
            placeholder="e.g. PI.11 target definition — % vs headcount conflict",
        )
    investigation_notes = st.text_area(
        "Investigation notes",
        value=active.get("investigation_notes") or "",
        height=110,
        placeholder=(
            "Document what sources were checked, what was found, and why "
            "this constitutes the finding described below."
        ),
    )
    key_finding = st.text_area(
        "Key finding",
        value=active.get("key_finding") or "",
        height=90,
        placeholder="The single most important conclusion from the investigation.",
    )

    # ── SECTION 3 — APPROVED ACTIONS ─────────────────────────────────────────
    _section_band("3", "Approved Actions")
    st.caption(
        "One row per action. Each action has its own owner and due date — "
        "a single finding often produces parallel actions owned by different people."
    )

    actions_df = pd.DataFrame([
        {
            "_id":            a.get("id"),
            "Decision Maker": a.get("decision_maker") or "",
            "Action":         a.get("action") or "",
            "Due Date":       _parse_date(a.get("action_due_date")),
            "Status":         a.get("action_status") or ACTION_STATUSES[0],
        }
        for a in existing_actions
    ] if existing_actions else [])

    edited_actions = st.data_editor(
        actions_df,
        column_config={
            "_id":            st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "Decision Maker": st.column_config.TextColumn("Decision Maker", width="medium"),
            "Action":         st.column_config.TextColumn("Action", width="large"),
            "Due Date":       st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"),
            "Status":         st.column_config.SelectboxColumn("Status", options=ACTION_STATUSES, width="medium"),
        },
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key=f"g_actions_editor_{active_id or 'new'}",
    )

    # ── STATUS & CONTROLS ─────────────────────────────────────────────────────
    st.divider()
    ctl_c1, ctl_c2, ctl_c3, ctl_c4 = st.columns([2, 2, 1, 1])
    with ctl_c1:
        status_sel = st.selectbox(
            "Report status",
            options=REPORT_STATUSES,
            index=(
                REPORT_STATUSES.index(active["status"])
                if active.get("status") in REPORT_STATUSES
                else 0
            ),
        )
    with ctl_c2:
        created_by = st.text_input(
            "Created / updated by",
            value=active.get("created_by") or st.session_state.get("username", ""),
        )
    with ctl_c3:
        save_clicked = st.button("💾 Save report", type="primary", use_container_width=True)
    with ctl_c4:
        export_clicked = st.button("📄 Export Word", use_container_width=True)

    # ── SAVE ──────────────────────────────────────────────────────────────────
    if save_clicked:
        errors = []
        if not indicator_definition.strip():
            errors.append("Indicator definition is required.")
        if not key_finding.strip():
            errors.append("Key finding is required.")
        if errors:
            for e in errors:
                st.error(e)
        else:
            report_data = {
                "project_id":          project_id,
                "created_date":        active.get("created_date") or date.today().isoformat(),
                "created_by":          created_by.strip(),
                "logframe_row_id":     chosen_lf_id,
                "target_value":        target_value.strip(),
                "indicator_definition": indicator_definition.strip(),
                "assumed_pattern":     assumed_pattern.strip(),
                "actual_value":        actual_value.strip(),
                "review_category":     review_category,
                "specific_focus_area": specific_focus.strip(),
                "investigation_notes": investigation_notes.strip(),
                "key_finding":         key_finding.strip(),
                "status":              status_sel,
            }

            if active_id:
                run_write(
                    """UPDATE decision_reports SET
                       created_by=:created_by, logframe_row_id=:logframe_row_id,
                       target_value=:target_value, indicator_definition=:indicator_definition,
                       assumed_pattern=:assumed_pattern, actual_value=:actual_value,
                       review_category=:review_category, specific_focus_area=:specific_focus_area,
                       investigation_notes=:investigation_notes, key_finding=:key_finding,
                       status=:status
                       WHERE id=:id AND project_id=:project_id""",
                    {**report_data, "id": active_id},
                )
                saved_id = active_id
            else:
                saved_id = insert_returning_id(
                    """INSERT INTO decision_reports
                       (project_id, created_date, created_by, logframe_row_id,
                        target_value, indicator_definition, assumed_pattern, actual_value,
                        review_category, specific_focus_area, investigation_notes,
                        key_finding, status)
                       VALUES (:project_id, :created_date, :created_by, :logframe_row_id,
                               :target_value, :indicator_definition, :assumed_pattern,
                               :actual_value, :review_category, :specific_focus_area,
                               :investigation_notes, :key_finding, :status)""",
                    report_data,
                )

            # Save actions (delete all + re-insert)
            run_write(
                "DELETE FROM decision_actions WHERE report_id=:rid",
                {"rid": saved_id},
            )
            for _, row in edited_actions.iterrows():
                dm_val     = str(row.get("Decision Maker") or "").strip()
                action_val = str(row.get("Action") or "").strip()
                if not action_val:
                    continue
                due_val = row.get("Due Date")
                due_str = due_val.isoformat() if hasattr(due_val, "isoformat") else str(due_val or "")
                insert_returning_id(
                    """INSERT INTO decision_actions
                       (report_id, decision_maker, action, action_due_date, action_status)
                       VALUES (:rid, :dm, :action, :due, :status)""",
                    {
                        "rid":    saved_id,
                        "dm":     dm_val,
                        "action": action_val,
                        "due":    due_str,
                        "status": str(row.get("Status") or ACTION_STATUSES[0]),
                    },
                )

            # Clear incoming pre-seed after save
            st.session_state.pop("g_indicator_ids", None)
            st.session_state.pop("g_source", None)
            st.session_state["g_edit_report_id"] = saved_id
            st.success(f"Report RPT-{saved_id} saved.")
            st.rerun()

    # ── EXPORT WORD ───────────────────────────────────────────────────────────
    if export_clicked:
        report_for_export = {
            "id":                   active_id or "DRAFT",
            "created_date":         active.get("created_date") or date.today().isoformat(),
            "created_by":           created_by,
            "status":               status_sel,
            "logframe_row_id":      chosen_lf_id,
            "target_value":         target_value,
            "indicator_definition": indicator_definition,
            "assumed_pattern":      assumed_pattern,
            "actual_value":         actual_value,
            "review_category":      review_category,
            "specific_focus_area":  specific_focus,
            "investigation_notes":  investigation_notes,
            "key_finding":          key_finding,
        }
        # Use saved actions if available, otherwise use current editor state
        if active_id:
            actions_for_export = _load_actions(active_id)
        else:
            actions_for_export = [
                {
                    "decision_maker":  str(r.get("Decision Maker") or ""),
                    "action":          str(r.get("Action") or ""),
                    "action_due_date": str(r.get("Due Date") or ""),
                    "action_status":   str(r.get("Status") or ""),
                }
                for _, r in edited_actions.iterrows()
                if str(r.get("Action") or "").strip()
            ]

        try:
            docx_bytes = _export_docx(report_for_export, actions_for_export)
            fname      = f"SAWA_Decision_Report_RPT-{active_id or 'DRAFT'}.docx"
            st.download_button(
                label="⬇️ Download Word document",
                data=docx_bytes,
                file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
            )
        except ImportError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Export failed: {exc}")

    # ── PRINT PREVIEW ─────────────────────────────────────────────────────────
    if active_id:
        with st.expander("🖨️ Print preview (read-only)", expanded=False):
            saved_report  = run_query(
                "SELECT * FROM decision_reports WHERE id=:id", {"id": active_id}
            )[0]
            saved_actions = _load_actions(active_id)
            lf = lf_by_id.get(saved_report.get("logframe_row_id") or -1, {})

            def _pf(label: str, value: str) -> str:
                safe_val = (value or "—").replace("<", "&lt;").replace(">", "&gt;")
                return (
                    f'<tr><td style="background:#D9E2F3;color:{NAVY};font-weight:bold;'
                    f'padding:6px 10px;width:22%;vertical-align:top;font-size:0.85em;">'
                    f'{label}</td>'
                    f'<td style="padding:6px 10px;font-size:0.9em;white-space:pre-wrap;">'
                    f'{safe_val}</td></tr>'
                )

            tbl_style = (
                'style="width:100%;border-collapse:collapse;'
                'border:1px solid #ddd;margin-bottom:16px;"'
            )
            rows_s1 = (
                _pf("Indicator",            lf.get("indicator_code", "—"))
                + _pf("Target value",       saved_report.get("target_value") or "—")
                + _pf("Definition",         saved_report.get("indicator_definition") or "—")
                + _pf("Assumed pattern",    saved_report.get("assumed_pattern") or "—")
                + _pf("Actual value",       saved_report.get("actual_value") or "—")
            )
            rows_s2 = (
                _pf("Review category",      saved_report.get("review_category") or "—")
                + _pf("Focus area",         saved_report.get("specific_focus_area") or "—")
                + _pf("Investigation notes", saved_report.get("investigation_notes") or "—")
                + _pf("Key finding",        saved_report.get("key_finding") or "—")
            )
            act_rows = "".join(
                f'<tr><td style="padding:5px 8px;font-size:0.85em;">{a.get("decision_maker","—")}</td>'
                f'<td style="padding:5px 8px;font-size:0.85em;">{a.get("action","—")}</td>'
                f'<td style="padding:5px 8px;font-size:0.85em;">{a.get("action_due_date","—")}</td>'
                f'<td style="padding:5px 8px;font-size:0.85em;">{a.get("action_status","—")}</td></tr>'
                for a in saved_actions
            ) or f'<tr><td colspan="4" style="padding:8px;color:#999;">No actions recorded.</td></tr>'

            act_header = "".join(
                f'<th style="background:{NAVY};color:white;padding:6px 8px;'
                f'text-align:left;font-size:0.85em;">{h}</th>'
                for h in ["Decision Maker", "Action", "Due Date", "Status"]
            )

            section_hdr = (
                f'background:{NAVY};color:white;padding:7px 14px;'
                f'border-left:5px solid {GOLD};font-weight:bold;'
                f'font-size:0.9em;margin:14px 0 0 0;'
            )

            st.markdown(
                f'<div style="background:{NAVY};color:white;padding:14px 20px;'
                'border-radius:6px 6px 0 0;">'
                f'<span style="color:{GOLD};font-size:1.15em;font-weight:bold;">'
                f'SAWA — DECISION REPORT</span>'
                f'<span style="float:right;font-size:0.8em;opacity:0.85;">'
                f'RPT-{saved_report["id"]} · {saved_report.get("created_date","—")} · '
                f'{saved_report.get("created_by","—")}</span></div>'
                f'<div style="height:3px;background:{GOLD};margin-bottom:8px;"></div>'
                f'<div style="{section_hdr}">SECTION 1 — PROBLEM DESCRIPTION</div>'
                f'<table {tbl_style}>{rows_s1}</table>'
                f'<div style="{section_hdr}">SECTION 2 — INVESTIGATION</div>'
                f'<table {tbl_style}>{rows_s2}</table>'
                f'<div style="{section_hdr}">SECTION 3 — APPROVED ACTIONS</div>'
                f'<table {tbl_style}><tr>{act_header}</tr>{act_rows}</table>',
                unsafe_allow_html=True,
            )

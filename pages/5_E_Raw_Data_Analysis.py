"""Module E — Raw Data Analysis

Editable master indicator tracking table: one row per logframe indicator,
covering baseline status, Q1–Q4 actuals, indicator status and action status.

Critical business rule: action_description is REQUIRED whenever action_status
is anything other than 'No action needed - data reporting only'. Save is
blocked if this invariant is violated.

Auto-status suggestion chips compare the latest actual value against the
trigger_value and offer a suggested indicator_status — never applied silently.

The filter preset button "Show Flagged" filters to 'Follow-up or investigate'
rows in one click, the most common real-world use of this page.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone

import streamlit as st
import pandas as pd

from database.db import init_db, run_query, run_write, insert_returning_id
from utils.shared_widgets import project_selector
from utils.auth import can, can_write_module
from utils.nav_strip import render_nav_strip
from utils.fiscal_calendar import current_fiscal_year

_NUM_RE = re.compile(r"-?\d+\.?\d*")


def _num(val):
    """Extract the leading number from a target string (e.g. '500 (Y1) —
    Q1: 95; ...' -> 500.0), same convention as Module H. Returns None if
    no number is found, so callers can skip the comparison rather than
    treating an unparseable value as 0."""
    if val is None or val == "" or val == "—":
        return None
    cleaned = str(val).replace(",", "").replace("$", "").replace("%", "").replace("≥", "").replace("+", "")
    m = _NUM_RE.search(cleaned)
    if not m:
        return None
    try:
        return float(m.group())
    except (ValueError, TypeError):
        return None

st.set_page_config(page_title="Raw Data Analysis — CEL MEL", layout="wide")
init_db()
render_nav_strip("Process")

if not st.session_state.get("authentication_status"):
    st.error("Please log in from the main page.")
    st.stop()

with st.sidebar:
    project_id = project_selector()
    if project_id is None:
        st.stop()
    st.divider()
    st.caption(f"Role: **{st.session_state.get('role', 'Viewer')}**")

# ── Fiscal year selector ────────────────────────────────────────────────────────
# raw_data_analysis has one row per (project, logframe_row, reporting_year) —
# a second year's actuals get their own row rather than overwriting the first.
this_fy = current_fiscal_year()
_year_rows = run_query(
    "SELECT DISTINCT reporting_year FROM raw_data_analysis WHERE project_id=:pid",
    {"pid": project_id},
)
available_years = sorted({r["reporting_year"] for r in _year_rows if r["reporting_year"]}) or [this_fy]
# A just-created year (via the rollover button below) takes priority over the
# usual "current fiscal year" default for one rerun — set as a plain
# session_state value, never written directly into the selectbox's own
# widget-bound key (Streamlit disallows mutating that after the widget runs).
if "rda_pending_year" in st.session_state:
    default_year = st.session_state.pop("rda_pending_year")
    if default_year not in available_years:
        default_year = this_fy if this_fy in available_years else available_years[-1]
    # The selectbox's own persisted value would otherwise win over `index=`
    # below — clear it so the widget re-initialises with the new default.
    st.session_state.pop("rda_selected_year", None)
else:
    default_year = this_fy if this_fy in available_years else available_years[-1]

yr_c1, yr_c2 = st.columns([3, 1])
with yr_c1:
    selected_year = st.selectbox(
        "Fiscal year",
        available_years,
        index=available_years.index(default_year),
        format_func=lambda y: f"FY{y} (Jul {y}–Jun {y + 1})" + ("  •  current" if y == this_fy else ""),
        key="rda_selected_year",
    )
with yr_c2:
    next_year = max(available_years) + 1
    if can("admin"):
        st.write("")  # vertical alignment with the selectbox
        if st.button(f"➕ Start FY{next_year}", use_container_width=True):
            from utils.raw_data_years import start_fiscal_year
            n = start_fiscal_year(project_id, next_year)
            st.success(f"Created {n} FY{next_year} row(s) — targets carried over, actuals blank.")
            st.session_state["rda_pending_year"] = next_year
            st.rerun()

# ── Constants ─────────────────────────────────────────────────────────────────
DATA_TYPES = [
    "Process", "Performance", "Assumption",
    "Stakeholder", "Problem", "Solution", "Attribution",
]
BASELINE_OPTS = ["Y", "N"]
IND_STATUS_OPTS = [
    "Data not collected yet",
    "Data currently being collected/analysed",
    "Completed - on track",
    "Completed - not on track",
]
ACTION_STATUS_OPTS = [
    "No action needed - data reporting only",
    "Inform decision-maker/confirm next steps",
    "Follow-up or investigate",
    "Change/adapt/revise",
    "Resolved",
]
ACTIVE_ACTION_STATUSES = {
    "Inform decision-maker/confirm next steps",
    "Follow-up or investigate",
    "Change/adapt/revise",
}

IND_STATUS_STYLE: dict[str, tuple[str, str]] = {
    "Data not collected yet":                  ("#546E7A", "#ECEFF1"),
    "Data currently being collected/analysed": ("#E65100", "#FFF8E1"),
    "Completed - on track":                    ("#2E7D32", "#E8F5E9"),
    "Completed - not on track":                ("#C62828", "#FFEBEE"),
}
ACTION_STATUS_STYLE: dict[str, tuple[str, str]] = {
    "No action needed - data reporting only":   ("#616161", "#F5F5F5"),
    "Inform decision-maker/confirm next steps": ("#E65100", "#FFF3E0"),
    "Follow-up or investigate":                 ("#F57F17", "#FFFDE7"),
    "Change/adapt/revise":                      ("#C62828", "#FFEBEE"),
    "Resolved":                                 ("#2E7D32", "#E8F5E9"),
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def _badge(text: str, style_map: dict[str, tuple[str, str]]) -> str:
    fg, bg = style_map.get(str(text) if text else "", ("#555", "#eee"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 9px;'
        f'border-radius:4px;font-size:0.77em;font-weight:600;'
        f'white-space:nowrap;">{text}</span>'
    )


def _ind_css(val) -> str:
    fg, bg = IND_STATUS_STYLE.get(str(val) if val else "", ("#333", "#fff"))
    return f"background-color:{bg};color:{fg};"


def _action_css(val) -> str:
    fg, bg = ACTION_STATUS_STYLE.get(str(val) if val else "", ("#333", "#fff"))
    return f"background-color:{bg};color:{fg};"


def _latest_actual(row: dict) -> str | None:
    for col in ("actual_q4", "actual_q3", "actual_q2", "actual_q1", "actual_year"):
        v = row.get(col, "")
        if v and str(v).strip():
            return str(v).strip()
    return None


def _suggest_status(actual: str, trigger: str) -> str | None:
    def _clean(s: str) -> str:
        return s.replace(",", "").replace("$", "").replace("%", "").replace(" ", "")
    try:
        a, t = float(_clean(actual)), float(_clean(trigger))
        return "Completed - on track" if a >= t else "Completed - not on track"
    except (ValueError, TypeError):
        return None


# ── Load data ─────────────────────────────────────────────────────────────────
rda_rows = run_query(
    """SELECT r.id, r.logframe_row_id,
              lf.indicator_code, lf.result_level, lf.indicator_statement, lf.target_annual,
              r.data_type, r.target_value, r.trigger_value, r.problem_definition,
              r.baseline_collected, r.baseline_value,
              r.actual_q1, r.actual_q2, r.actual_q3, r.actual_q4, r.actual_year,
              r.indicator_status, r.action_status, r.action_description,
              r.last_updated, r.updated_by
       FROM   raw_data_analysis r
       LEFT JOIN logframe_rows lf ON r.logframe_row_id = lf.id
       WHERE  r.project_id = :pid AND r.reporting_year = :yr
       ORDER  BY r.id""",
    {"pid": project_id, "yr": selected_year},
)

if not rda_rows:
    st.title("Module E — Raw Data Analysis")
    st.info(
        f"No data found for FY{selected_year} — run `python -m database.seed_sawa` to load "
        "SAWA data, or pick a different fiscal year above."
    )
    st.stop()

# ── Session state for filters and suggestions ─────────────────────────────────
if "rda_action_filter" not in st.session_state:
    st.session_state["rda_action_filter"] = []
if "rda_accepted_suggestions" not in st.session_state:
    st.session_state["rda_accepted_suggestions"] = {}

# ── Status summary ────────────────────────────────────────────────────────────
st.title("Module E — Raw Data Analysis")

from collections import Counter
ind_counts   = Counter(r.get("indicator_status", "") for r in rda_rows)
act_counts   = Counter(r.get("action_status",   "") for r in rda_rows)
flagged_rows = [r for r in rda_rows if r.get("action_status") in ACTIVE_ACTION_STATUSES]

sm_cols = st.columns(4)
_sm_data = [
    ("Total indicators",         len(rda_rows),                                     "#37474F", "#ECEFF1"),
    ("Data not collected",        ind_counts.get("Data not collected yet", 0),       "#546E7A", "#ECEFF1"),
    ("Completed — on track",      ind_counts.get("Completed - on track", 0),         "#2E7D32", "#E8F5E9"),
    ("Completed — not on track",  ind_counts.get("Completed - not on track", 0),     "#C62828", "#FFEBEE"),
]
for col, (label, value, fg, bg) in zip(sm_cols, _sm_data):
    with col:
        st.markdown(
            f'<div style="background:{bg};border-left:4px solid {fg};border-radius:6px;'
            f'padding:10px 14px;margin-bottom:8px;">'
            f'<p style="margin:0 0 4px;font-size:0.72em;color:#555;">{label}</p>'
            f'<p style="margin:0;font-size:1.6em;font-weight:700;color:{fg};">{value}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Flagged action panel ──────────────────────────────────────────────────────
if flagged_rows:
    n_flag = len(flagged_rows)
    with st.expander(f"⚠️ {n_flag} indicator{'s' if n_flag > 1 else ''} require action", expanded=True):
        for r in flagged_rows:
            fg, bg = ACTION_STATUS_STYLE.get(r["action_status"], ("#333", "#fff"))
            adesc = r.get("action_description") or ""
            action_html = (
                '<br><span style="font-size:0.8em;color:#555;">'
                f"Action: {adesc}</span>"
            ) if adesc else ""
            st.markdown(
                f'<div style="background:{bg};border-left:4px solid {fg};'
                f'border-radius:5px;padding:8px 12px;margin:4px 0;">'
                f'<b style="color:{fg};">{r.get("indicator_code","?")}</b>'
                f' &nbsp;{_badge(r["action_status"], ACTION_STATUS_STYLE)}<br>'
                f'<span style="font-size:0.82em;color:#333;">'
                f'{(r.get("indicator_statement") or "")[:90]}…</span>'
                f'{action_html}</div>',
                unsafe_allow_html=True,
            )
            col_a, col_b = st.columns([5, 1])
            with col_b:
                if st.button(
                    "📝 → Module G",
                    key=f"mg_{r['id']}",
                    use_container_width=True,
                    help="Queue this indicator for a decision report in Module G",
                ):
                    queue = st.session_state.get("g_indicator_ids", [])
                    if r["id"] not in queue:
                        queue.append(r["id"])
                    st.session_state["g_indicator_ids"] = queue
                    st.session_state["g_source"] = "raw_data_analysis"
                    st.success(
                        f"{r.get('indicator_code')} queued for Module G. "
                        "Navigate to Module G to draft the report."
                    )

st.divider()

# ── Filter bar ────────────────────────────────────────────────────────────────
preset_c, f1, f2, f3 = st.columns([1.2, 2, 2, 2])

with preset_c:
    st.markdown("&nbsp;", unsafe_allow_html=True)
    if st.button("🚨 Show Flagged", use_container_width=True, type="secondary",
                 help="Filter to 'Follow-up or investigate' rows"):
        st.session_state["rda_action_filter"] = ["Follow-up or investigate"]
        if "rda_action_widget" in st.session_state:
            del st.session_state["rda_action_widget"]
        st.rerun()
    if st.button("☰ Show All", use_container_width=True,
                 help="Clear all filters"):
        st.session_state["rda_action_filter"] = []
        if "rda_action_widget" in st.session_state:
            del st.session_state["rda_action_widget"]
        st.rerun()

with f1:
    sel_type = st.multiselect("Data type", DATA_TYPES, key="rda_type_widget")
with f2:
    sel_ind_status = st.multiselect("Indicator status", IND_STATUS_OPTS, key="rda_ind_widget")
with f3:
    sel_action = st.multiselect(
        "Action status", ACTION_STATUS_OPTS,
        default=st.session_state["rda_action_filter"],
        key="rda_action_widget",
    )
st.session_state["rda_action_filter"] = sel_action

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = [
    r for r in rda_rows
    if (not sel_type       or r.get("data_type")         in sel_type)
    and (not sel_ind_status or r.get("indicator_status")  in sel_ind_status)
    and (not sel_action     or r.get("action_status")     in sel_action)
]
st.caption(f"Showing **{len(filtered)}** of **{len(rda_rows)}** indicators.")

# ── Build display DataFrame ───────────────────────────────────────────────────
Q1_LABEL, Q2_LABEL, Q3_LABEL, Q4_LABEL, YEAR_LABEL = (
    f"Q1 {selected_year}", f"Q2 {selected_year}", f"Q3 {selected_year}",
    f"Q4 {selected_year}", f"Year {selected_year}",
)
_DISPLAY_COLS = {
    "Code":               "indicator_code",
    "Level":              "result_level",
    "Indicator":          "indicator_statement",
    "Type":               "data_type",
    "Target":             "target_value",
    "Trigger":            "trigger_value",
    "Problem Definition": "problem_definition",
    "Baseline?":          "baseline_collected",
    "Baseline Value":     "baseline_value",
    Q1_LABEL:             "actual_q1",
    Q2_LABEL:             "actual_q2",
    Q3_LABEL:             "actual_q3",
    Q4_LABEL:             "actual_q4",
    YEAR_LABEL:           "actual_year",
    "Indicator Status":   "indicator_status",
    "Action Status":      "action_status",
    "Action Description": "action_description",
}
_EDITABLE = [
    "Type", "Trigger", "Problem Definition", "Baseline?", "Baseline Value",
    Q1_LABEL, Q2_LABEL, Q3_LABEL, Q4_LABEL, YEAR_LABEL,
    "Indicator Status", "Action Status", "Action Description",
]

accepted = st.session_state.get("rda_accepted_suggestions", {})


def _build_df(rows: list[dict]) -> pd.DataFrame:
    result = []
    for r in rows:
        ind_status = accepted.get(r["id"], r.get("indicator_status") or "")
        row_dict = {"_id": r["id"]}
        for disp, db in _DISPLAY_COLS.items():
            val = r.get(db) or ""
            if disp == "Indicator Status":
                val = ind_status
            row_dict[disp] = val
        result.append(row_dict)
    return pd.DataFrame(result)


df = _build_df(filtered)

col_config = {
    "_id":               st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "Code":              st.column_config.TextColumn("Code", disabled=True, width="small"),
    "Level":             st.column_config.TextColumn("Level", disabled=True, width="small"),
    "Indicator":         st.column_config.TextColumn("Indicator", disabled=True, width="large"),
    "Type":              st.column_config.SelectboxColumn("Type", options=DATA_TYPES, width="small"),
    "Target":            st.column_config.TextColumn("Target", disabled=True, width="medium"),
    "Trigger":           st.column_config.TextColumn("Trigger", width="small"),
    "Problem Definition":st.column_config.TextColumn("Problem Definition", width="large"),
    "Baseline?":         st.column_config.SelectboxColumn("Baseline?", options=BASELINE_OPTS, width="small"),
    "Baseline Value":    st.column_config.TextColumn("Baseline Value", width="small"),
    Q1_LABEL:            st.column_config.TextColumn(Q1_LABEL, width="small"),
    Q2_LABEL:            st.column_config.TextColumn(Q2_LABEL, width="small"),
    Q3_LABEL:            st.column_config.TextColumn(Q3_LABEL, width="small"),
    Q4_LABEL:            st.column_config.TextColumn(Q4_LABEL, width="small"),
    YEAR_LABEL:          st.column_config.TextColumn(YEAR_LABEL, width="small"),
    "Indicator Status":  st.column_config.SelectboxColumn(
                             "Indicator Status", options=IND_STATUS_OPTS, width="medium"),
    "Action Status":     st.column_config.SelectboxColumn(
                             "Action Status", options=ACTION_STATUS_OPTS, width="large"),
    "Action Description":st.column_config.TextColumn("Action Description", width="large"),
}

if can_write_module("E"):
    st.caption(
        "✏️ **Admin/Editor** — edit highlighted fields then **Save changes**. "
        "Action Description is **required** whenever Action Status is not "
        "'No action needed'."
    )
    disabled_cols = [c for c in df.columns if c not in _EDITABLE]
    edited_df = st.data_editor(
        df,
        column_config=col_config,
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        key="rda_editor",
        num_rows="fixed",
    )

    # ── Save with validation ──────────────────────────────────────────────────
    if st.button("💾 Save changes", type="primary"):
        # CRITICAL BUSINESS RULE: action_description required for active statuses
        errors: list[str] = []
        for _, edit_row in edited_df.iterrows():
            a_status = str(edit_row.get("Action Status") or "").strip()
            a_desc   = str(edit_row.get("Action Description") or "").strip()
            code     = str(edit_row.get("Code") or "")
            if a_status in ACTIVE_ACTION_STATUSES and not a_desc:
                errors.append(
                    f"**{code}**: action_description required for "
                    f"'{a_status}'"
                )
            # A non-empty actual with no digit at all is almost always a typo —
            # it would silently parse to 0 in every downstream dashboard
            # (Module H, Module I) with no indication anything went wrong.
            for q_col in (Q1_LABEL, Q2_LABEL, Q3_LABEL, Q4_LABEL, YEAR_LABEL):
                q_val = str(edit_row.get(q_col) or "").strip()
                if q_val and not any(ch.isdigit() for ch in q_val):
                    errors.append(
                        f"**{code}**: '{q_col}' = \"{q_val}\" has no number in it — "
                        "leave it blank if there's genuinely no data yet"
                    )

        if errors:
            st.error(
                "⛔ **Save blocked** — fix the following before saving:  \n"
                + "  \n".join(f"- {e}" for e in errors)
            )
        else:
            orig_indexed = {r["id"]: r for r in filtered}
            now_iso      = datetime.now(timezone.utc).isoformat(timespec="seconds")
            editor       = st.session_state.get("name", st.session_state.get("username", "unknown"))
            changes      = 0

            for _, edit_row in edited_df.iterrows():
                row_id   = int(edit_row["_id"])
                orig_row = orig_indexed.get(row_id)
                if orig_row is None:
                    continue
                for disp_col in _EDITABLE:
                    db_field = _DISPLAY_COLS[disp_col]
                    old_val  = str(orig_row.get(db_field) or "")
                    new_val  = str(edit_row.get(disp_col) or "")
                    # Also check accepted suggestions
                    if disp_col == "Indicator Status":
                        new_val = str(
                            accepted.get(row_id, edit_row.get(disp_col)) or ""
                        )
                    if old_val == new_val:
                        continue
                    run_write(
                        f"UPDATE raw_data_analysis SET {db_field}=:v, "
                        f"last_updated=:ts, updated_by=:by WHERE id=:id",
                        {"v": new_val, "ts": now_iso, "by": editor, "id": row_id},
                    )
                    changes += 1

            # Clear accepted suggestions after save
            st.session_state["rda_accepted_suggestions"] = {}

            if changes:
                st.success(f"Saved {changes} field change(s).")
                st.rerun()
            else:
                st.info("No changes detected.")

else:
    # ── Viewer: styled read-only table ────────────────────────────────────────
    display_only = df.drop(columns=["_id"])
    try:
        styled = (
            display_only.style
            .map(_ind_css,    subset=["Indicator Status"])
            .map(_action_css, subset=["Action Status"])
        )
    except AttributeError:  # pandas < 2.1
        styled = (
            display_only.style
            .applymap(_ind_css,    subset=["Indicator Status"])
            .applymap(_action_css, subset=["Action Status"])
        )
    st.dataframe(
        styled,
        column_config={k: v for k, v in col_config.items() if k != "_id"},
        hide_index=True,
        use_container_width=True,
    )

st.divider()

# ── Auto-status suggestion chips ─────────────────────────────────────────────
suggestions = []
for r in filtered:
    latest = _latest_actual(r)
    if not latest:
        continue
    trigger = str(r.get("trigger_value") or "").strip()
    if not trigger:
        continue
    current = str(r.get("indicator_status") or "")
    if current in ("Completed - on track", "Completed - not on track"):
        continue
    suggested = _suggest_status(latest, trigger)
    if suggested:
        suggestions.append({
            "id":        r["id"],
            "code":      r.get("indicator_code", ""),
            "actual":    latest,
            "trigger":   trigger,
            "suggested": suggested,
            "accepted":  accepted.get(r["id"]) == suggested,
        })

if suggestions:
    st.subheader("🔮 Auto-Status Suggestions")
    st.caption(
        "Comparing latest actual value against trigger value. "
        "Click **Accept** to pre-populate the suggestion — it is never applied silently. "
        "Accepted suggestions are written to the database when you click **Save changes** above."
    )
    sg_cols = st.columns(min(len(suggestions), 4))
    for i, sg in enumerate(suggestions):
        is_on  = sg["suggested"] == "Completed - on track"
        fg, bg = IND_STATUS_STYLE.get(sg["suggested"], ("#333", "#fff"))
        with sg_cols[i % len(sg_cols)]:
            already = sg["accepted"]
            st.markdown(
                f'<div style="border:1px solid {fg};border-radius:6px;'
                f'padding:8px 10px;background:{bg}22;margin-bottom:6px;">'
                f'<b style="color:{fg};">{sg["code"]}</b><br>'
                f'<span style="font-size:0.8em;color:#555;">'
                f'Actual: {sg["actual"]} | Trigger: {sg["trigger"]}</span><br>'
                f'{_badge(sg["suggested"], IND_STATUS_STYLE)}'
                f'{"&nbsp;✓ accepted" if already else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )
            if not already and can_write_module("E"):
                if st.button(
                    f"Accept for {sg['code']}",
                    key=f"sg_{sg['id']}",
                    use_container_width=True,
                ):
                    st.session_state["rda_accepted_suggestions"][sg["id"]] = sg["suggested"]
                    st.rerun()

# ── Data completeness expander ────────────────────────────────────────────────
with st.expander("📊 Data completeness summary"):
    st.caption(
        f"Shows which FY{selected_year} Q1–Q4 cells have data entered "
        "(across all indicators, unfiltered)."
    )
    total = len(rda_rows)
    q_cols = [(Q1_LABEL, "actual_q1"), (Q2_LABEL, "actual_q2"),
              (Q3_LABEL, "actual_q3"), (Q4_LABEL, "actual_q4"), (YEAR_LABEL, "actual_year")]
    comp_data = {
        label: sum(1 for r in rda_rows if r.get(db) and str(r[db]).strip())
        for label, db in q_cols
    }
    comp_df = pd.DataFrame([
        {"Period": label, "With data": v, "Missing": total - v, "% complete": f"{100*v/total:.0f}%"}
        for label, v in comp_data.items()
    ])
    st.dataframe(comp_df, hide_index=True, use_container_width=True)

# ── Target consistency check ──────────────────────────────────────────────────
# target_value (this table) and target_annual (the logframe, Module B) are two
# independently-editable fields meant to represent the same target — nothing
# previously caught them drifting apart.
_mismatches = []
for r in rda_rows:
    rda_t = _num(r.get("target_value"))
    lf_t  = _num(r.get("target_annual"))
    if rda_t is not None and lf_t is not None and abs(rda_t - lf_t) > max(0.01, 0.005 * lf_t):
        _mismatches.append({
            "Code": r.get("indicator_code") or "?",
            "Module E target_value": r.get("target_value"),
            "Module B target_annual": r.get("target_annual"),
        })

with st.expander(
    f"🎯 Target consistency check"
    + (f" — ⚠️ {len(_mismatches)} mismatch(es)" if _mismatches else " — all match"),
    expanded=bool(_mismatches),
):
    st.caption(
        "Compares the leading number in this table's Target against the logframe's "
        "(Module B) target_annual for the same indicator — they're entered "
        "independently and can drift apart without anyone noticing."
    )
    if _mismatches:
        st.dataframe(pd.DataFrame(_mismatches), hide_index=True, use_container_width=True)
    else:
        st.success("No mismatches — every indicator's target agrees with the logframe.")


# =============================================================================
# Evidence & Means of Verification
# =============================================================================
st.divider()
st.subheader("📎 Evidence & Means of Verification")
st.caption(
    "Attach scanned registers, photos, certificates or paste a SharePoint / Google Drive "
    "link against each indicator and reporting quarter. "
    "Agri-Impact uploads; Mastercard Foundation Viewer role sees all evidence read-only."
)

# ── Indicator selector ────────────────────────────────────────────────────────
ev_ind_options: dict[str, int] = {}
for r in rda_rows:
    lf_id = r.get("logframe_row_id")
    if lf_id:
        code = r.get("indicator_code") or "?"
        stmt = (r.get("indicator_statement") or "")[:65]
        ev_ind_options[f"{code} — {stmt}"] = lf_id

if not ev_ind_options:
    st.info("No indicators with logframe links found.")
else:
    ev_sel_c1, ev_sel_c2 = st.columns([4, 1])
    with ev_sel_c1:
        ev_ind_label = st.selectbox(
            "Indicator",
            list(ev_ind_options.keys()),
            key="ev_ind_sel",
            label_visibility="collapsed",
        )
    with ev_sel_c2:
        ev_qtr_filter = st.selectbox(
            "Quarter",
            ["All quarters", "Q1", "Q2", "Q3", "Q4", "Annual"],
            key="ev_qtr_filter",
            label_visibility="collapsed",
        )

    sel_lf_id = ev_ind_options[ev_ind_label]

    # ── Fetch existing evidence (metadata + data for inline download) ─────────
    ev_rows = run_query(
        """SELECT id, quarter, year, label, link_url, file_name, file_mime,
                  file_data, uploaded_by, uploaded_at
           FROM   evidence
           WHERE  project_id=:pid AND logframe_row_id=:lf
           ORDER  BY uploaded_at DESC""",
        {"pid": project_id, "lf": sel_lf_id},
    )

    if ev_qtr_filter != "All quarters":
        ev_rows = [e for e in ev_rows if e.get("quarter") == ev_qtr_filter]

    # ── Evidence list ─────────────────────────────────────────────────────────
    if ev_rows:
        for ev in ev_rows:
            ev_bg = "#F8FAFB"
            ev_border = "#CFD8DC"
            q_label = f"{ev.get('quarter','')} {ev.get('year','')}"
            up_at   = (ev.get("uploaded_at") or "")[:10]
            up_by   = ev.get("uploaded_by") or "unknown"

            c_info, c_link, c_dl, c_del = st.columns([5, 2, 1, 1])
            with c_info:
                st.markdown(
                    f'<div style="background:{ev_bg};border-left:3px solid {ev_border};'
                    f'border-radius:4px;padding:6px 10px;">'
                    f'<b style="font-size:0.85em;">{q_label}</b> &nbsp; '
                    f'<span style="font-size:0.88em;">{ev.get("label","")}</span><br>'
                    f'<span style="font-size:0.74em;color:#777;">Uploaded by {up_by} · {up_at}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with c_link:
                url = ev.get("link_url") or ""
                if url:
                    st.markdown(f"[🔗 Open link]({url})", unsafe_allow_html=False)
            with c_dl:
                fdata = ev.get("file_data")
                fname = ev.get("file_name") or "evidence"
                fmime = ev.get("file_mime") or "application/octet-stream"
                if fdata:
                    st.download_button(
                        "⬇",
                        data=bytes(fdata),
                        file_name=fname,
                        mime=fmime,
                        key=f"ev_dl_{ev['id']}",
                        help=f"Download {fname}",
                    )
            with c_del:
                if can_write_module("E") and st.button(
                    "🗑", key=f"ev_del_{ev['id']}",
                    help="Delete this evidence record",
                ):
                    run_write("DELETE FROM evidence WHERE id=:id", {"id": ev["id"]})
                    st.rerun()
    else:
        st.info(
            "No evidence uploaded for this indicator"
            + (f" in {ev_qtr_filter}" if ev_qtr_filter != "All quarters" else "")
            + " yet.",
            icon="📂",
        )

    # ── Upload / add evidence form ────────────────────────────────────────────
    if can_write_module("E"):
        with st.expander("➕ Add evidence for this indicator", expanded=False):
            up_c1, up_c2, up_c3 = st.columns([3, 1, 1])
            with up_c1:
                up_label = st.text_input(
                    "Description *",
                    placeholder="e.g. Training attendance sheet — R&B Farms Q2",
                    key="ev_up_label",
                )
            with up_c2:
                up_quarter = st.selectbox(
                    "Quarter *", ["Q1", "Q2", "Q3", "Q4", "Annual"],
                    key="ev_up_qtr",
                )
            with up_c3:
                up_year = st.number_input(
                    "Year *", value=selected_year, min_value=2020, max_value=2040,
                    step=1, key="ev_up_year",
                )

            up_url = st.text_input(
                "SharePoint / Google Drive link (optional)",
                placeholder="https://mastercardfdn.sharepoint.com/…",
                key="ev_up_url",
            )

            up_file = st.file_uploader(
                "Scanned document (PDF, JPEG, PNG, DOCX — max 10 MB)",
                type=["pdf", "jpg", "jpeg", "png", "docx"],
                key="ev_up_file",
            )

            if up_file is not None:
                size_mb = len(up_file.getvalue()) / 1_048_576
                if size_mb > 10:
                    st.error(f"File is {size_mb:.1f} MB — please keep uploads under 10 MB.")
                    up_file = None
                else:
                    st.caption(f"Ready to upload: **{up_file.name}** ({size_mb:.2f} MB)")

            if st.button("📎 Save evidence", type="primary", key="ev_save_btn"):
                if not up_label.strip():
                    st.error("Description is required.")
                elif not up_url.strip() and up_file is None:
                    st.error("Provide at least a link URL or a file upload.")
                else:
                    editor = st.session_state.get(
                        "name", st.session_state.get("username", "unknown")
                    )
                    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
                    file_bytes = up_file.getvalue() if up_file else None
                    file_name  = up_file.name       if up_file else None
                    file_mime  = up_file.type       if up_file else None

                    insert_returning_id(
                        """INSERT INTO evidence
                           (project_id, logframe_row_id, quarter, year, label,
                            link_url, file_name, file_mime, file_data,
                            uploaded_by, uploaded_at)
                           VALUES (:pid, :lf, :qtr, :yr, :label,
                                   :url, :fname, :fmime, :fdata,
                                   :by, :at)""",
                        {
                            "pid":   project_id,
                            "lf":    sel_lf_id,
                            "qtr":   up_quarter,
                            "yr":    int(up_year),
                            "label": up_label.strip(),
                            "url":   up_url.strip() or None,
                            "fname": file_name,
                            "fmime": file_mime,
                            "fdata": file_bytes,
                            "by":    editor,
                            "at":    now_iso,
                        },
                    )
                    st.success(
                        f"Evidence saved: **{up_label.strip()}** "
                        f"({up_quarter} {int(up_year)})"
                    )
                    st.rerun()
    else:
        st.caption("*Editor or Admin role required to add evidence.*")

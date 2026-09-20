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
from datetime import datetime, timezone

import streamlit as st
import pandas as pd

from database.db import init_db, run_query, run_write
from utils.shared_widgets import project_selector
from utils.auth import can, can_write_module
from utils.nav_strip import render_nav_strip

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
              lf.indicator_code, lf.result_level, lf.indicator_statement,
              r.data_type, r.target_value, r.trigger_value, r.problem_definition,
              r.baseline_collected, r.baseline_value,
              r.actual_q1, r.actual_q2, r.actual_q3, r.actual_q4, r.actual_year,
              r.indicator_status, r.action_status, r.action_description,
              r.last_updated, r.updated_by
       FROM   raw_data_analysis r
       LEFT JOIN logframe_rows lf ON r.logframe_row_id = lf.id
       WHERE  r.project_id = :pid
       ORDER  BY r.id""",
    {"pid": project_id},
)

if not rda_rows:
    st.title("Module E — Raw Data Analysis")
    st.info("No data found — run `python -m database.seed_sawa` to load SAWA data.")
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
    "Q1 2026":            "actual_q1",
    "Q2 2026":            "actual_q2",
    "Q3 2026":            "actual_q3",
    "Q4 2026":            "actual_q4",
    "Year 2026":          "actual_year",
    "Indicator Status":   "indicator_status",
    "Action Status":      "action_status",
    "Action Description": "action_description",
}
_EDITABLE = [
    "Type", "Trigger", "Problem Definition", "Baseline?", "Baseline Value",
    "Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026", "Year 2026",
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
    "Q1 2026":           st.column_config.TextColumn("Q1 2026", width="small"),
    "Q2 2026":           st.column_config.TextColumn("Q2 2026", width="small"),
    "Q3 2026":           st.column_config.TextColumn("Q3 2026", width="small"),
    "Q4 2026":           st.column_config.TextColumn("Q4 2026", width="small"),
    "Year 2026":         st.column_config.TextColumn("Year 2026", width="small"),
    "Indicator Status":  st.column_config.SelectboxColumn(
                             "Indicator Status", options=IND_STATUS_OPTS, width="medium"),
    "Action Status":     st.column_config.SelectboxColumn(
                             "Action Status", options=ACTION_STATUS_OPTS, width="large"),
    "Action Description":st.column_config.TextColumn("Action Description", width="large"),
}

if can_write_module("D"):
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

        if errors:
            st.error(
                "⛔ **Save blocked** — action_description is missing for the following "
                "indicators. An action status with no description is the exact failure mode "
                "this module exists to prevent:  \n"
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
            if not already and can_write_module("D"):
                if st.button(
                    f"Accept for {sg['code']}",
                    key=f"sg_{sg['id']}",
                    use_container_width=True,
                ):
                    st.session_state["rda_accepted_suggestions"][sg["id"]] = sg["suggested"]
                    st.rerun()

# ── Data completeness expander ────────────────────────────────────────────────
with st.expander("📊 Data completeness summary"):
    st.caption("Shows which Q1–Q4 cells have data entered (across all indicators, unfiltered).")
    total = len(rda_rows)
    q_cols = [("Q1 2026", "actual_q1"), ("Q2 2026", "actual_q2"),
              ("Q3 2026", "actual_q3"), ("Q4 2026", "actual_q4"), ("Year 2026", "actual_year")]
    comp_data = {
        label: sum(1 for r in rda_rows if r.get(db) and str(r[db]).strip())
        for label, db in q_cols
    }
    comp_df = pd.DataFrame([
        {"Period": label, "With data": v, "Missing": total - v, "% complete": f"{100*v/total:.0f}%"}
        for label, v in comp_data.items()
    ])
    st.dataframe(comp_df, hide_index=True, use_container_width=True)

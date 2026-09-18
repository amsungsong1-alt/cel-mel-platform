"""Module B — Theory of Change & Logframe

Tab 1 — Theory of Change: top-down graphviz tree, level-filter buttons.
Tab 2 — Logframe: filterable/sortable table with inline editing and
         full field-level audit trail in logframe_changelog.
"""
from datetime import datetime, timezone
import streamlit as st
import pandas as pd

from database.db import init_db, run_query, run_write
from utils.shared_widgets import project_selector
from utils.auth import can, can_write_module

st.set_page_config(page_title="ToC & Logframe — CEL MEL", layout="wide")
init_db()

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not st.session_state.get("authentication_status"):
    st.error("Please log in from the main page.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    project_id = project_selector()
    if project_id is None:
        st.stop()
    st.divider()
    st.caption(f"Role: **{st.session_state.get('role', 'Viewer')}**")

# ── Cross-tab filter (set by Tab 1 level buttons, read by Tab 2) ──────────────
if "toc_level_filter" not in st.session_state:
    st.session_state["toc_level_filter"] = []

st.title("Module B — Theory of Change & Logframe")

tab_toc, tab_lf = st.tabs(["🌳 Theory of Change", "📋 Logframe"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Theory of Change
# ═══════════════════════════════════════════════════════════════════════════════
LEVEL_ORDER = ["Impact", "Outcome", "Intermediate Outcome", "Output", "Activity", "Input"]

LEVEL_COLORS = {
    "Impact":               "#004D40",
    "Outcome":              "#4A148C",
    "Intermediate Outcome": "#0D47A1",
    "Output":               "#BF360C",
    "Activity":             "#E65100",
    "Input":                "#37474F",
}


def _wrap(text: str, width: int = 38) -> str:
    """Break text into graphviz left-justified lines (\\l token)."""
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        lines.append(line)
    return "\\l".join(lines) + "\\l"


def _build_dot(nodes: list[dict]) -> str:
    by_level: dict[str, list] = {}
    for n in nodes:
        by_level.setdefault(n["level"], []).append(n)

    lines = [
        "digraph toc {",
        '  rankdir=TB;',
        '  bgcolor="transparent";',
        '  graph [splines=ortho nodesep=0.4 ranksep=0.6];',
        '  node [shape=box style="filled,rounded" fontsize=9 fontcolor=white',
        '        fontname="Helvetica" margin="0.2,0.12" width=3.2 height=0.5];',
        '  edge [color="#90A4AE" arrowsize=0.65];',
        "",
    ]

    # Same-rank groupings keep each level on one horizontal band.
    for lvl in LEVEL_ORDER:
        grp = by_level.get(lvl, [])
        if grp:
            ids = " ".join(f"n{n['id']}" for n in grp)
            lines.append(f"  {{ rank=same; {ids}; }}")
    lines.append("")

    for n in nodes:
        color   = LEVEL_COLORS.get(n["level"], "#607D8B")
        label   = f"{n['level']}\\l{'─'*20}\\l{_wrap(n['statement'])}"
        tooltip = n["statement"].replace('"', '\\"')
        lines.append(
            f'  n{n["id"]} [label="{label}" fillcolor="{color}" tooltip="{tooltip}"];'
        )
    lines.append("")

    for n in nodes:
        if n.get("parent_id"):
            lines.append(f"  n{n['parent_id']} -> n{n['id']};")

    lines.append("}")
    return "\n".join(lines)


with tab_toc:
    toc_nodes = run_query(
        "SELECT id, level, statement, parent_id FROM toc_nodes "
        "WHERE project_id=:pid ORDER BY id",
        {"pid": project_id},
    )

    if not toc_nodes:
        st.info("No ToC nodes found — run `python -m database.seed_sawa` to load SAWA data.")
        st.stop()

    st.graphviz_chart(_build_dot(toc_nodes), use_container_width=True)

    # ── Level filter buttons ──────────────────────────────────────────────────
    st.divider()
    st.caption("Select a level to filter the Logframe tab, or clear to show all:")

    active_filter = st.session_state["toc_level_filter"]
    present_levels = [lvl for lvl in LEVEL_ORDER if any(n["level"] == lvl for n in toc_nodes)]

    btn_cols = st.columns(len(present_levels) + 1)
    for i, lvl in enumerate(present_levels):
        color   = LEVEL_COLORS.get(lvl, "#607D8B")
        is_active = lvl in active_filter
        # Highlight active button with markdown badge.
        badge = f'<span style="background:{color};color:#fff;padding:3px 10px;border-radius:4px;font-size:0.82em;font-weight:{"700" if is_active else "400"}">{lvl}</span>'
        with btn_cols[i]:
            st.markdown(badge, unsafe_allow_html=True)
            if st.button("Select", key=f"lvl_btn_{lvl}", use_container_width=True):
                st.session_state["toc_level_filter"] = [] if is_active else [lvl]
                st.rerun()

    with btn_cols[-1]:
        st.markdown('<span style="font-size:0.82em;color:#888">All levels</span>', unsafe_allow_html=True)
        if st.button("Clear filter", use_container_width=True):
            st.session_state["toc_level_filter"] = []
            st.rerun()

    if active_filter:
        st.info(f"Logframe tab is filtered to: **{', '.join(active_filter)}**. Switch to the Logframe tab or click Clear to reset.")

    # ── Node detail expander ──────────────────────────────────────────────────
    with st.expander("Browse ToC node statements"):
        for lvl in LEVEL_ORDER:
            grp = [n for n in toc_nodes if n["level"] == lvl]
            if not grp:
                continue
            color = LEVEL_COLORS.get(lvl, "#607D8B")
            st.markdown(
                f'<span style="background:{color};color:#fff;padding:2px 10px;'
                f'border-radius:4px;font-size:0.8em;">{lvl}</span>',
                unsafe_allow_html=True,
            )
            for n in grp:
                st.markdown(f"- {n['statement']}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Logframe
# ═══════════════════════════════════════════════════════════════════════════════

# Display column names → DB field names mapping (order = table column order)
_DISPLAY_COLS = {
    "Results Level":          "result_level",
    "Indicator ID":           "indicator_code",
    "Indicator (SMART)":      "indicator_statement",
    "Disaggregation":         "disaggregation",
    "Baseline":               "baseline_value",
    "Target (Annual)":        "target_annual",
    "Target (LOP)":           "target_lop",
    "Means of Verification":  "means_of_verification",
    "Frequency":              "frequency",
    "Responsible":            "responsible",
    "Critical Assumption":    "critical_assumption",
}

_EDITABLE_DISPLAY_COLS = [
    "Baseline", "Target (Annual)", "Target (LOP)",
    "Means of Verification", "Frequency", "Responsible",
    "Disaggregation", "Critical Assumption",
]

_RESULT_LEVEL_OPTIONS = ["Impact", "Outcome", "Output", "Activity", "Input"]

with tab_lf:
    lf_rows = run_query(
        "SELECT id, " + ", ".join(_DISPLAY_COLS.values()) + " "
        "FROM logframe_rows WHERE project_id=:pid ORDER BY id",
        {"pid": project_id},
    )

    if not lf_rows:
        st.info("No logframe rows found — run `python -m database.seed_sawa` to load SAWA data.")
        st.stop()

    # ── Filter row ────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])

    all_levels      = sorted({r["result_level"] for r in lf_rows if r["result_level"]})
    all_responsible = sorted({r["responsible"]   for r in lf_rows if r["responsible"]})

    with col_f1:
        sel_levels = st.multiselect(
            "Results level",
            all_levels,
            default=st.session_state.get("toc_level_filter", []),
            key="lf_level_filter",
        )
    with col_f2:
        sel_resp = st.multiselect("Responsible", all_responsible, key="lf_resp_filter")
    with col_f3:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        if st.button("Clear filters", use_container_width=True):
            st.session_state["toc_level_filter"] = []
            st.rerun()

    # Apply filters
    filtered = [
        r for r in lf_rows
        if (not sel_levels or r["result_level"] in sel_levels)
        and (not sel_resp   or r["responsible"]   in sel_resp)
    ]

    st.caption(f"Showing **{len(filtered)}** of **{len(lf_rows)}** indicators.")

    # ── Build display DataFrame ───────────────────────────────────────────────
    def _to_df(rows: list[dict]) -> pd.DataFrame:
        display_rows = [
            {"_id": r["id"]} | {disp: r[db] for disp, db in _DISPLAY_COLS.items()}
            for r in rows
        ]
        return pd.DataFrame(display_rows)

    df_display = _to_df(filtered)

    col_config = {
        "_id":                    st.column_config.NumberColumn("DB ID", disabled=True, width="small"),
        "Results Level":          st.column_config.SelectboxColumn("Results Level", options=_RESULT_LEVEL_OPTIONS, width="medium"),
        "Indicator ID":           st.column_config.TextColumn("Indicator ID", width="small"),
        "Indicator (SMART)":      st.column_config.TextColumn("Indicator (SMART)", width="large"),
        "Disaggregation":         st.column_config.TextColumn("Disaggregation", width="medium"),
        "Baseline":               st.column_config.TextColumn("Baseline", width="small"),
        "Target (Annual)":        st.column_config.TextColumn("Target (Annual)", width="small"),
        "Target (LOP)":           st.column_config.TextColumn("Target (LOP)", width="small"),
        "Means of Verification":  st.column_config.TextColumn("Means of Verification", width="large"),
        "Frequency":              st.column_config.SelectboxColumn(
                                      "Frequency",
                                      options=["Quarterly", "Bi-annual", "Annual"],
                                      width="small",
                                  ),
        "Responsible":            st.column_config.SelectboxColumn(
                                      "Responsible",
                                      options=["CEL MEAL", "Partner MEAL", "Programme Team"],
                                      width="medium",
                                  ),
        "Critical Assumption":    st.column_config.TextColumn("Critical Assumption", width="large"),
    }

    # ── Render table ──────────────────────────────────────────────────────────
    if can_write_module("B"):
        st.caption(
            "✏️ **Admin/Editor view** — edit any yellow-highlighted field, then click **Save changes**. "
            "Every edit is logged with your name and a timestamp."
        )

        disabled_cols = [
            c for c in df_display.columns
            if c not in _EDITABLE_DISPLAY_COLS
        ]

        edited_df = st.data_editor(
            df_display,
            column_config=col_config,
            disabled=disabled_cols,
            hide_index=True,
            use_container_width=True,
            key="lf_editor",
            num_rows="fixed",
        )

        if st.button("💾 Save changes", type="primary"):
            editor    = st.session_state.get("name", st.session_state.get("username", "unknown"))
            now_iso   = datetime.now(timezone.utc).isoformat(timespec="seconds")
            changes   = 0

            orig_indexed = {r["id"]: r for r in filtered}

            for _, edit_row in edited_df.iterrows():
                row_id   = int(edit_row["_id"])
                orig_row = orig_indexed.get(row_id)
                if orig_row is None:
                    continue

                for disp_col in _EDITABLE_DISPLAY_COLS:
                    db_field  = _DISPLAY_COLS[disp_col]
                    old_val   = str(orig_row.get(db_field) or "")
                    new_val   = str(edit_row.get(disp_col) or "")

                    if old_val == new_val:
                        continue

                    # Write new value
                    run_write(
                        f"UPDATE logframe_rows SET {db_field}=:v WHERE id=:id",
                        {"v": new_val, "id": row_id},
                    )
                    # Write changelog entry
                    run_write(
                        """INSERT INTO logframe_changelog
                           (row_id, field_changed, old_value, new_value, changed_by, changed_at)
                           VALUES (:row_id, :field, :old, :new, :by, :at)""",
                        {
                            "row_id": row_id,
                            "field":  disp_col,
                            "old":    old_val,
                            "new":    new_val,
                            "by":     editor,
                            "at":     now_iso,
                        },
                    )
                    changes += 1

            if changes:
                st.success(f"Saved {changes} field change(s). Audit trail updated.")
                st.rerun()
            else:
                st.info("No changes detected.")

        # ── Changelog viewer ─────────────────────────────────────────────────
        with st.expander("📜 Edit history (logframe changelog)"):
            changelog = run_query(
                """SELECT cl.changed_at, cl.changed_by, lr.indicator_code,
                          cl.field_changed, cl.old_value, cl.new_value
                   FROM   logframe_changelog cl
                   JOIN   logframe_rows lr ON cl.row_id = lr.id
                   WHERE  lr.project_id = :pid
                   ORDER  BY cl.changed_at DESC
                   LIMIT  100""",
                {"pid": project_id},
            )
            if changelog:
                st.dataframe(pd.DataFrame(changelog), hide_index=True, use_container_width=True)
            else:
                st.caption("No edits recorded yet.")

    else:
        # Viewer — read-only, hide internal _id column
        st.dataframe(
            df_display.drop(columns=["_id"]),
            column_config={k: v for k, v in col_config.items() if k != "_id"},
            hide_index=True,
            use_container_width=True,
        )

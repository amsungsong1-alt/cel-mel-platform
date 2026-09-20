"""Module C — Data Collection Plan

Tab 1 — Collection Plan: editable master table of all 11 SAWA instruments.
Tab 2 — Participant Journey: horizontal timeline showing which instruments
         fire at each journey step; non-baseline instruments flagged clearly.
Tab 3 — Collection Calendar: 12-month heatmap with overload detection — the
         May-2027 cluster (8 instruments) is visible at default threshold 5.
"""
from __future__ import annotations
from collections import defaultdict

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from database.db import init_db, run_query, run_write
from utils.shared_widgets import project_selector
from utils.auth import can, can_write_module
from utils.nav_strip import render_nav_strip

st.set_page_config(page_title="Data Collection Plan — CEL MEL", layout="wide")
init_db()
render_nav_strip("Input")

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

st.title("Module C — Data Collection Plan")

# ── Load data ─────────────────────────────────────────────────────────────────
plan_rows = run_query(
    """SELECT id, stakeholder, indicator_statement, data_points, rationale,
              instrument_status, instrument_link, journey_step,
              integration_mechanism, frequency,
              collection_month, collection_year, responsible_party
       FROM   data_collection_plan
       WHERE  project_id = :pid
       ORDER  BY id""",
    {"pid": project_id},
)

if not plan_rows:
    st.info(
        "No data collection plan found — run `python -m database.seed_sawa` to load SAWA data."
    )
    st.stop()

# ── Constants ─────────────────────────────────────────────────────────────────
JOURNEY_ORDER = [
    "Mobilisation",
    "Enrolment",
    "Training",
    "3-month check-in",
    "6-month follow-up",
    "Annual review",
    "Endline",
]
BASELINE_STEPS = {"Mobilisation", "Enrolment", "Training"}

JOURNEY_COLORS = {
    "Mobilisation":      "#1565C0",
    "Enrolment":         "#2E7D32",
    "Training":          "#E65100",
    "3-month check-in":  "#6A1B9A",
    "6-month follow-up": "#C62828",
    "Annual review":     "#37474F",
    "Endline":           "#004D40",
}

FREQ_INTERVALS: dict[str, int | None] = {
    "Once":       None,
    "Monthly":    1,
    "Bi-monthly": 2,
    "Quarterly":  3,
    "Bi-annual":  6,
    "Annual":     12,
}

MONTH_ABR = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

FREQ_OPTIONS        = ["Once", "Quarterly", "Bi-annual", "Annual", "Monthly"]
STATUS_OPTIONS      = ["New", "Existing"]
RESPONSIBLE_OPTIONS = ["CEL MEAL", "Partner MEAL", "Programme Team"]
MONTH_OPTIONS       = list(range(1, 13))


# ── Expand collection schedule to individual events ───────────────────────────
def _expand_events(rows: list[dict], years_ahead: int = 2) -> list[dict]:
    """Generate every collection event from frequency + start month/year."""
    events: list[dict] = []
    for row in rows:
        start_m  = row.get("collection_month") or 1
        start_y  = row.get("collection_year")  or 2026
        freq     = row.get("frequency") or "Annual"
        interval = FREQ_INTERVALS.get(freq)
        base = {
            "stakeholder":         row.get("stakeholder", ""),
            "indicator_statement": row.get("indicator_statement", ""),
            "journey_step":        row.get("journey_step", ""),
            "frequency":           freq,
        }
        if interval is None:
            events.append({"year": start_y, "month": start_m, **base})
        else:
            m, y = start_m, start_y
            cutoff = start_y + years_ahead
            while y <= cutoff:
                events.append({"year": y, "month": m, **base})
                m += interval
                while m > 12:
                    m -= 12
                    y += 1
    return events


# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_plan, tab_journey, tab_cal = st.tabs([
    "📊 Collection Plan",
    "🚶 Participant Journey",
    "📅 Collection Calendar",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Master table
# ═══════════════════════════════════════════════════════════════════════════════
with tab_plan:
    st.caption(
        f"**{len(plan_rows)} instruments** in the SAWA baseline data collection plan.  "
        "Instruments flagged ⚠ are not collectible at baseline — they require the "
        "programme to be underway before data exist."
    )

    # ── Non-baseline notice ───────────────────────────────────────────────────
    non_baseline = [
        r for r in plan_rows
        if r.get("journey_step") not in BASELINE_STEPS
    ]
    if non_baseline:
        labels = "  \n".join(
            f"- **{r['stakeholder']}** — journey step: _{r['journey_step']}_"
            for r in non_baseline
        )
        st.warning(
            "⚠️ **Not baseline-collectible** — these instruments fire at a later "
            "journey stage and cannot produce baseline values at enrolment:  \n" + labels
        )

    # ── Build display DataFrame ───────────────────────────────────────────────
    _DISPLAY_COLS = {
        "Stakeholder":           "stakeholder",
        "Indicator / Statement": "indicator_statement",
        "Data Points":           "data_points",
        "Rationale":             "rationale",
        "Status":                "instrument_status",
        "Instrument Link":       "instrument_link",
        "Journey Step":          "journey_step",
        "Integration Mechanism": "integration_mechanism",
        "Frequency":             "frequency",
        "Month":                 "collection_month",
        "Year":                  "collection_year",
        "Responsible":           "responsible_party",
    }
    _EDITABLE = [
        "Status", "Instrument Link", "Journey Step",
        "Integration Mechanism", "Frequency", "Month", "Year", "Responsible",
    ]

    df = pd.DataFrame([
        {"_id": r["id"]} | {disp: r[db] for disp, db in _DISPLAY_COLS.items()}
        for r in plan_rows
    ])

    col_config = {
        "_id":                    st.column_config.NumberColumn("ID", disabled=True, width="small"),
        "Stakeholder":            st.column_config.TextColumn("Stakeholder", disabled=True, width="medium"),
        "Indicator / Statement":  st.column_config.TextColumn("Indicator / Statement", disabled=True, width="large"),
        "Data Points":            st.column_config.TextColumn("Data Points", disabled=True, width="medium"),
        "Rationale":              st.column_config.TextColumn("Rationale", disabled=True, width="large"),
        "Status":                 st.column_config.SelectboxColumn(
                                      "Status", options=STATUS_OPTIONS, width="small"),
        "Instrument Link":        st.column_config.LinkColumn("Instrument Link", width="medium"),
        "Journey Step":           st.column_config.SelectboxColumn(
                                      "Journey Step", options=JOURNEY_ORDER, width="medium"),
        "Integration Mechanism":  st.column_config.TextColumn("Integration Mechanism", width="large"),
        "Frequency":              st.column_config.SelectboxColumn(
                                      "Frequency", options=FREQ_OPTIONS, width="small"),
        "Month":                  st.column_config.SelectboxColumn(
                                      "Month", options=MONTH_OPTIONS, width="small"),
        "Year":                   st.column_config.NumberColumn(
                                      "Year", min_value=2024, max_value=2035, step=1, width="small"),
        "Responsible":            st.column_config.SelectboxColumn(
                                      "Responsible", options=RESPONSIBLE_OPTIONS, width="medium"),
    }

    if can_write_module("C"):
        st.caption(
            "✏️ **Admin/Editor view** — edit any non-greyed field, then click **Save changes**."
        )
        disabled_cols = [c for c in df.columns if c not in _EDITABLE]
        edited_df = st.data_editor(
            df,
            column_config=col_config,
            disabled=disabled_cols,
            hide_index=True,
            use_container_width=True,
            key="dcp_editor",
            num_rows="fixed",
        )

        if st.button("💾 Save changes", type="primary"):
            orig_indexed = {r["id"]: r for r in plan_rows}
            changes = 0
            for _, edit_row in edited_df.iterrows():
                row_id   = int(edit_row["_id"])
                orig_row = orig_indexed.get(row_id)
                if orig_row is None:
                    continue
                for disp_col in _EDITABLE:
                    db_field = _DISPLAY_COLS[disp_col]
                    old_val  = str(orig_row.get(db_field) or "")
                    new_val  = str(edit_row.get(disp_col) or "")
                    if old_val == new_val:
                        continue
                    run_write(
                        f"UPDATE data_collection_plan SET {db_field}=:v WHERE id=:id",
                        {"v": new_val, "id": row_id},
                    )
                    changes += 1
            if changes:
                st.success(f"Saved {changes} field change(s).")
                st.rerun()
            else:
                st.info("No changes detected.")

    else:
        st.dataframe(
            df.drop(columns=["_id"]),
            column_config={k: v for k, v in col_config.items() if k != "_id"},
            hide_index=True,
            use_container_width=True,
        )

    # ── Instrument detail expander ────────────────────────────────────────────
    with st.expander("📋 Full rationale & data points for each instrument"):
        for row in plan_rows:
            step  = row.get("journey_step", "")
            color = JOURNEY_COLORS.get(step, "#607D8B")
            is_nb = step not in BASELINE_STEPS
            badge = (
                ' <span style="background:#E65100;color:#fff;font-size:0.72em;'
                'padding:1px 6px;border-radius:3px;margin-left:6px;">'
                '⚠ Not baseline-collectible</span>'
                if is_nb else ""
            )
            st.markdown(
                f'<p style="margin:10px 0 2px 0;">'
                f'<span style="background:{color};color:#fff;padding:2px 8px;'
                f'border-radius:4px;font-size:0.8em;">{step}</span>'
                f'<b style="margin-left:8px;">{row["stakeholder"]}</b>{badge}</p>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"*{row['indicator_statement']}*  \n"
                f"**Data points:** {row.get('data_points', '—')}  \n"
                f"**Rationale:** {row.get('rationale', '—')}"
            )
            st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Participant Journey
# ═══════════════════════════════════════════════════════════════════════════════
with tab_journey:
    st.caption(
        "Each column is a journey step. Instruments appear under the step where they "
        "first collect data. Steps outside the baseline window are outlined in orange — "
        "they cannot produce baseline values at programme start."
    )

    # ── Step legend row ───────────────────────────────────────────────────────
    legend_cols = st.columns(len(JOURNEY_ORDER))
    for i, step in enumerate(JOURNEY_ORDER):
        color = JOURNEY_COLORS[step]
        is_nb = step not in BASELINE_STEPS
        border = "2px dashed #E65100" if is_nb else "none"
        with legend_cols[i]:
            st.markdown(
                f'<div style="background:{color}22;border:{border};'
                f'border-radius:4px;padding:3px 6px;text-align:center;'
                f'font-size:0.68em;color:{color};font-weight:700;">'
                f'{"⚠ " if is_nb else ""}{step}</div>',
                unsafe_allow_html=True,
            )
    st.markdown("")

    # ── Group instruments by journey step ─────────────────────────────────────
    step_groups: dict[str, list[dict]] = defaultdict(list)
    for row in plan_rows:
        step_groups[row.get("journey_step", "Unknown")].append(row)

    # ── 7-step layout with arrow gaps ─────────────────────────────────────────
    # Widths: 7 step columns (3) + 6 arrow gaps (0.25)
    widths = []
    for i in range(len(JOURNEY_ORDER)):
        widths.append(3)
        if i < len(JOURNEY_ORDER) - 1:
            widths.append(0.25)

    cols = st.columns(widths)

    for i, step in enumerate(JOURNEY_ORDER):
        col_idx  = i * 2
        color    = JOURNEY_COLORS[step]
        is_nb    = step not in BASELINE_STEPS
        bg_outer = f"{color}10" if not is_nb else "#FFF3E0"
        border_l = f"3px solid {color}"
        insts    = step_groups.get(step, [])

        with cols[col_idx]:
            # Step header tile
            st.markdown(
                f'<div style="background:{color};color:#fff;text-align:center;'
                f'padding:7px 4px;border-radius:6px 6px 0 0;font-size:0.76em;'
                f'font-weight:700;line-height:1.35;">'
                f'{"⚠ " if is_nb else ""}{step}'
                f'<br><span style="font-weight:400;font-size:0.85em;">'
                f'{len(insts)} instrument{"s" if len(insts) != 1 else ""}'
                f'</span></div>',
                unsafe_allow_html=True,
            )

            # Instrument cards
            if not insts:
                st.markdown(
                    f'<div style="background:{bg_outer};border-left:{border_l};'
                    f'border-radius:0 0 6px 6px;padding:8px 10px;font-size:0.72em;'
                    f'color:#aaa;min-height:50px;">—</div>',
                    unsafe_allow_html=True,
                )
            else:
                html = (
                    f'<div style="background:{bg_outer};border-left:{border_l};'
                    f'border-radius:0 0 6px 6px;padding:5px 7px;">'
                )
                for inst in insts:
                    short = inst["indicator_statement"][:60].rstrip() + "…"
                    freq  = inst.get("frequency", "")
                    html += (
                        f'<div style="border:1px solid {color}35;background:#fff;'
                        f'border-radius:4px;padding:4px 6px;margin:3px 0;font-size:0.71em;">'
                        f'<b style="color:{color};">{inst["stakeholder"]}</b>'
                        f'<span style="float:right;background:{color}25;color:{color};'
                        f'font-size:0.85em;padding:0 3px;border-radius:2px;">{freq}</span>'
                        f'<br><span style="color:#555;">{short}</span>'
                        f'</div>'
                    )
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

        # Arrow connector
        if i < len(JOURNEY_ORDER) - 1:
            with cols[col_idx + 1]:
                st.markdown(
                    '<div style="text-align:center;padding-top:28px;'
                    'color:#BDBDBD;font-size:1.2em;">→</div>',
                    unsafe_allow_html=True,
                )

    # ── Non-baseline summary ──────────────────────────────────────────────────
    st.divider()
    nb_list = [r for r in plan_rows if r.get("journey_step") not in BASELINE_STEPS]
    if nb_list:
        st.warning(
            f"**{len(nb_list)} instrument(s) are not collectible at baseline** "
            f"(their journey step falls outside Mobilisation / Enrolment / Training):  \n"
            + "  \n".join(
                f"- **{r['stakeholder']}** — _{r['journey_step']}_ · "
                f"{r['indicator_statement'][:80]}…"
                for r in nb_list
            )
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Collection Calendar
# ═══════════════════════════════════════════════════════════════════════════════
with tab_cal:
    # ── Controls ──────────────────────────────────────────────────────────────
    ctrl_c1, ctrl_c2 = st.columns([3, 1])
    with ctrl_c1:
        threshold = st.slider(
            "Overload threshold (collection events per month)",
            min_value=2, max_value=20, value=5,
            help=(
                "Months at or above this count are flagged as overloaded. "
                "At the default threshold of 5, May 2027 is flagged — 8 instruments "
                "from the SAWA plan all fire in that month. In a fully expanded plan "
                "(multiple partner sites, multi-cohort) this reaches 23+ events."
            ),
        )
    with ctrl_c2:
        years_ahead = st.selectbox("Show years ahead", options=[1, 2, 3], index=1)

    # ── Expand schedule ───────────────────────────────────────────────────────
    events = _expand_events(plan_rows, years_ahead=int(years_ahead))
    df_events = pd.DataFrame(events)

    # ── Pivot: year × month count ─────────────────────────────────────────────
    pivot = (
        df_events
        .groupby(["year", "month"])
        .size()
        .unstack("month", fill_value=0)
    )
    for m in range(1, 13):
        if m not in pivot.columns:
            pivot[m] = 0
    pivot = pivot[sorted(pivot.columns)]
    pivot.columns = [MONTH_ABR[m] for m in pivot.columns]
    pivot.index.name = "Year"

    st.markdown("#### 12-Month Collection Heatmap")
    st.caption(
        "Cell value = number of collection events scheduled in that month. "
        "Darker red = higher load. Hover a cell to see the exact count. "
        "Months reaching the threshold are flagged below."
    )

    z_vals = pivot.values.tolist()
    x_vals = list(pivot.columns)           # month abbreviations
    y_vals = [str(int(y)) for y in pivot.index]  # years as strings

    fig_cal = go.Figure(go.Heatmap(
        z=z_vals,
        x=x_vals,
        y=y_vals,
        colorscale="YlOrRd",
        text=z_vals,
        texttemplate="%{text:.0f}",
        showscale=True,
        colorbar=dict(title="Events", thickness=14, len=0.8),
        hovertemplate="<b>%{y} %{x}</b><br>Collection events: %{z}<extra></extra>",
    ))
    fig_cal.update_layout(
        height=max(130, len(y_vals) * 65 + 90),
        margin=dict(l=60, r=80, t=40, b=10),
        xaxis=dict(side="top", tickfont=dict(size=12)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11),
    )
    st.plotly_chart(fig_cal, use_container_width=True)

    # ── Overload detection ────────────────────────────────────────────────────
    st.markdown("#### Overload Alerts")

    monthly_counts = (
        df_events
        .groupby(["year", "month"])
        .size()
        .reset_index(name="count")
    )
    overloaded = (
        monthly_counts[monthly_counts["count"] >= threshold]
        .sort_values(["year", "month"])
    )

    if overloaded.empty:
        st.success(f"No months reach the threshold of {threshold} collection events.")
    else:
        for _, ov_row in overloaded.iterrows():
            yr, mo, cnt = int(ov_row["year"]), int(ov_row["month"]), int(ov_row["count"])
            month_insts = df_events[
                (df_events["year"] == yr) & (df_events["month"] == mo)
            ]
            inst_parts = "; ".join(
                f"{r['stakeholder']} ({r['frequency']})"
                for _, r in month_insts.iterrows()
            )
            st.error(
                f"⚠️ **{MONTH_ABR[mo]} {yr}** — **{cnt} collection events** "
                f"(threshold: {threshold})  \n"
                f"Instruments: {inst_parts}"
            )

    # ── Detailed schedule breakdown ───────────────────────────────────────────
    with st.expander("📋 Detailed schedule — all events by month"):
        detail = df_events.copy().sort_values(["year", "month"])
        detail["Period"] = (
            detail["year"].astype(str)
            + " "
            + detail["month"].map(MONTH_ABR)
        )
        st.dataframe(
            detail[["Period", "stakeholder", "frequency", "journey_step", "indicator_statement"]]
            .rename(columns={
                "stakeholder":         "Stakeholder",
                "frequency":           "Frequency",
                "journey_step":        "Journey Step",
                "indicator_statement": "Indicator Statement",
            }),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Indicator Statement": st.column_config.TextColumn(width="large"),
            },
        )

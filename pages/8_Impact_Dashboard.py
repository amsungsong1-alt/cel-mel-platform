"""Module H: Impact Dashboard — auto-generated programme impact story.

Reads live data from Modules C–G and assembles a shareable impact summary:
  • Headline KPI cards (output & outcome actuals vs targets)
  • Results chain progress by level (Impact → Outcome → Output)
  • Quarterly delivery trend
  • Partner commitment vs delivery (Level 1 & 2 funnel)
  • Key findings from Decision Reports (Module G)
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date

from database.db import run_query
from utils.auth import require
from utils.shared_widgets import project_selector


def _num(val, default=0):
    """Safely convert a DB value (string, int, float, None) to float."""
    if val is None or val == "" or val == "—":
        return default
    try:
        return float(str(val).replace(",", "").replace("%", "").replace("≥", "").replace("+", "").strip())
    except (ValueError, TypeError):
        return default

st.set_page_config(
    page_title="Impact Dashboard · CEL MEL",
    page_icon="🌟",
    layout="wide",
)

require("read")

NAVY  = "#0D2B5E"
GOLD  = "#C8A951"
GREEN = "#2E7D32"
RED   = "#C62828"
AMBER = "#E65100"
BLUE  = "#1565C0"
PURP  = "#6A1B9A"

LEVEL_COLOUR = {
    "Impact":  PURP,
    "Outcome": BLUE,
    "Output":  GREEN,
    "Activity": AMBER,
}

STATUS_COLOUR = {
    "On Track":   GREEN,
    "At Risk":    AMBER,
    "Off Track":  RED,
    "Not Started": "#757575",
}

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="background:{NAVY};color:white;padding:14px 22px;'
    f'border-left:6px solid {GOLD};border-radius:4px;margin-bottom:4px;">'
    '<span style="font-size:1.4em;font-weight:bold;">🌟 Module H — Impact Dashboard</span>'
    f'<span style="color:{GOLD};font-size:0.85em;margin-left:14px;">'
    'Auto-captured impact story · SAWA Programme</span>'
    '</div>',
    unsafe_allow_html=True,
)

project_id = project_selector()
if not project_id:
    st.stop()

snapshot_date = date.today().strftime("%d %B %Y")
st.caption(
    f"Snapshot: **{snapshot_date}** · Data sourced automatically from "
    "Modules C–G · No manual upload required"
)

# ── Load data ─────────────────────────────────────────────────────────────────
actuals_rows = run_query(
    """
    SELECT lr.indicator_code, lr.indicator_statement, lr.result_level,
           lr.target_lop, lr.target_annual,
           COALESCE(rda.actual_year, 0)  AS actual_year,
           COALESCE(rda.actual_q1, 0)    AS q1,
           COALESCE(rda.actual_q2, 0)    AS q2,
           COALESCE(rda.actual_q3, 0)    AS q3,
           COALESCE(rda.actual_q4, 0)    AS q4,
           rda.target_value              AS rda_target,
           rda.indicator_status,
           rda.data_type
    FROM raw_data_analysis rda
    JOIN logframe_rows lr ON lr.id = rda.logframe_row_id
    WHERE rda.project_id = :pid
    ORDER BY
        CASE lr.result_level
            WHEN 'Impact'   THEN 1
            WHEN 'Outcome'  THEN 2
            WHEN 'Output'   THEN 3
            ELSE 4
        END,
        lr.indicator_code
    """,
    {"pid": project_id},
)

partner_targets = run_query(
    """
    SELECT p.name AS partner, pt.level, pt.metric_label,
           pt.target_value, pt.unit
    FROM partner_targets pt
    LEFT JOIN partners p ON p.partner_id = pt.partner_id
    WHERE pt.project_id = :pid
    ORDER BY pt.level, p.name
    """,
    {"pid": project_id},
)

reports = run_query(
    """
    SELECT dr.review_category, dr.key_finding, dr.specific_focus_area,
           dr.created_date, dr.status, dr.actual_value,
           lr.indicator_statement, lr.result_level
    FROM decision_reports dr
    LEFT JOIN logframe_rows lr ON lr.id = dr.logframe_row_id
    WHERE dr.project_id = :pid
    ORDER BY dr.created_date DESC
    LIMIT 12
    """,
    {"pid": project_id},
)

if not actuals_rows:
    st.info("No performance data yet — enter actuals in Module D (Raw Data Analysis).")
    st.stop()

df = pd.DataFrame(actuals_rows)

# ── Section 1: Headline KPI Cards ─────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Programme Highlights")

output_df  = df[df["result_level"] == "Output"].head(4)
outcome_df = df[df["result_level"] == "Outcome"].head(2)
highlight  = pd.concat([outcome_df, output_df]).head(4)

kpi_cols = st.columns(len(highlight) if len(highlight) > 0 else 1)
for col, (_, row) in zip(kpi_cols, highlight.iterrows()):
    actual  = _num(row["actual_year"])
    target  = _num(row["rda_target"])
    status  = row["indicator_status"] or "Not Started"
    colour  = STATUS_COLOUR.get(status, "#757575")
    level_c = LEVEL_COLOUR.get(row["result_level"], NAVY)
    label   = (row["indicator_statement"] or "")[:60] + ("…" if len(row["indicator_statement"] or "") > 60 else "")
    pct     = round(actual / target * 100, 1) if target > 0 else 0

    col.markdown(
        f'<div style="border:1px solid {level_c}50;border-left:4px solid {level_c};'
        f'border-radius:6px;padding:14px 12px;background:{level_c}08;">'
        f'<div style="font-size:0.7em;color:{level_c};font-weight:bold;text-transform:uppercase;">'
        f'{row["result_level"]} · {row["indicator_code"]}</div>'
        f'<div style="font-size:1.9em;font-weight:bold;color:{NAVY};margin:4px 0;">{actual:,.0f}</div>'
        f'<div style="font-size:0.75em;color:#555;">of {target:,.0f} target ({pct}%)</div>'
        f'<div style="font-size:0.7em;margin-top:4px;color:{colour};font-weight:bold;">● {status}</div>'
        f'<div style="font-size:0.68em;color:#777;margin-top:6px;">{label}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

# ── Section 2: Results Chain Progress ────────────────────────────────────────
st.markdown("---")
st.markdown("#### Results Chain: Progress Against Targets")

col_chart, col_table = st.columns([1, 1])

with col_chart:
    levels = ["Output", "Outcome", "Impact"]
    rows_by_level = []
    for lvl in levels:
        sub = df[df["result_level"] == lvl]
        if sub.empty:
            continue
        for _, r in sub.iterrows():
            t = _num(r["rda_target"])
            a = _num(r["actual_year"])
            pct = min(round(a / t * 100, 1) if t > 0 else 0, 150)
            rows_by_level.append({
                "Code": r["indicator_code"],
                "Level": lvl,
                "% Achieved": pct,
                "Status": r["indicator_status"] or "Not Started",
            })

    if rows_by_level:
        bar_df = pd.DataFrame(rows_by_level)
        colour_map = {s: c for s, c in STATUS_COLOUR.items()}
        fig = px.bar(
            bar_df,
            x="% Achieved",
            y="Code",
            color="Status",
            orientation="h",
            color_discrete_map=colour_map,
            title="% of annual target achieved per indicator",
            height=max(300, len(rows_by_level) * 38),
        )
        fig.add_vline(x=100, line_dash="dash", line_color=NAVY, opacity=0.5)
        fig.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis_title="% of target",
            yaxis_title="",
            legend_title="Status",
        )
        st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**Indicator summary**")
    for lvl in levels:
        sub = df[df["result_level"] == lvl]
        if sub.empty:
            continue
        lvl_c = LEVEL_COLOUR.get(lvl, NAVY)
        st.markdown(
            f'<div style="background:{lvl_c}15;border-left:3px solid {lvl_c};'
            f'padding:3px 8px;font-size:0.78em;font-weight:bold;color:{lvl_c};">'
            f'{lvl}</div>',
            unsafe_allow_html=True,
        )
        for _, r in sub.iterrows():
            t = _num(r["rda_target"])
            a = _num(r["actual_year"])
            pct = round(a / t * 100, 1) if t > 0 else 0
            status = r["indicator_status"] or "Not Started"
            sc = STATUS_COLOUR.get(status, "#757575")
            stmt = (r["indicator_statement"] or "")[:70]
            st.markdown(
                f'<div style="padding:5px 6px 5px 12px;border-bottom:1px solid #eee;font-size:0.75em;">'
                f'<b style="color:{NAVY};">{r["indicator_code"]}</b> — {stmt}<br>'
                f'<span style="color:#555;">{a:,.0f} / {t:,.0f}</span> '
                f'<span style="color:{sc};font-weight:bold;">({pct}%) {status}</span>'
                '</div>',
                unsafe_allow_html=True,
            )

# ── Section 3: Quarterly Delivery Trend ───────────────────────────────────────
st.markdown("---")
st.markdown("#### Quarterly Delivery Trend")

output_rows = df[df["result_level"] == "Output"]
if not output_rows.empty:
    trend_data = []
    for _, r in output_rows.iterrows():
        for q, label in [("q1","Q1"),("q2","Q2"),("q3","Q3"),("q4","Q4")]:
            trend_data.append({
                "Quarter": label,
                "Indicator": r["indicator_code"],
                "Actuals": r[q],
            })
    trend_df = pd.DataFrame(trend_data)
    fig2 = px.line(
        trend_df,
        x="Quarter", y="Actuals", color="Indicator",
        markers=True,
        title="Output-level quarterly actuals",
        height=320,
    )
    fig2.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Section 4: Partner Contribution ───────────────────────────────────────────
st.markdown("---")
st.markdown("#### Partner Commitment Funnel")

if partner_targets:
    pt_df = pd.DataFrame(partner_targets)

    col_l1, col_l2 = st.columns(2)

    with col_l1:
        st.markdown("**Level 1 — Anchor Partner Commitments (Life of Programme)**")
        l1 = pt_df[pt_df["level"] == 1].dropna(subset=["partner"])
        if not l1.empty:
            for _, r in l1.iterrows():
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;'
                    f'padding:5px 8px;border-bottom:1px solid #eee;font-size:0.78em;">'
                    f'<span><b style="color:{NAVY};">{r["partner"]}</b> · {r["metric_label"]}</span>'
                    f'<span style="font-weight:bold;color:{GREEN};">{r["target_value"]} {r["unit"]}</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )

    with col_l2:
        st.markdown("**Level 2 — CEL Year 1 Delivery Targets**")
        l2 = pt_df[pt_df["level"] == 2]
        if not l2.empty:
            for _, r in l2.iterrows():
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;'
                    f'padding:5px 8px;border-bottom:1px solid #eee;font-size:0.78em;">'
                    f'<span>{r["metric_label"]}</span>'
                    f'<span style="font-weight:bold;color:{BLUE};">{r["target_value"]} {r["unit"]}</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )

    # Level 4 impact targets as a summary strip
    l4 = pt_df[pt_df["level"] == 4]
    if not l4.empty:
        st.markdown("**Programme-Level Impact Ambition**")
        imp_cols = st.columns(len(l4))
        for col, (_, r) in zip(imp_cols, l4.iterrows()):
            col.markdown(
                f'<div style="background:{PURP}10;border:1px solid {PURP}40;'
                f'border-radius:6px;padding:10px 8px;text-align:center;">'
                f'<div style="font-size:1.3em;font-weight:bold;color:{PURP};">{r["target_value"]}</div>'
                f'<div style="font-size:0.68em;color:#555;">{r["unit"]}</div>'
                f'<div style="font-size:0.7em;color:{NAVY};margin-top:4px;">{r["metric_label"]}</div>'
                '</div>',
                unsafe_allow_html=True,
            )

# ── Section 5: Key Findings from Decision Reports ─────────────────────────────
st.markdown("---")
st.markdown("#### Key Findings from Evidence Reviews (Module G)")

CATEGORY_COLOUR = {
    "Performance":  BLUE,
    "Assumption":   PURP,
    "Stakeholder":  GREEN,
    "Process":      AMBER,
    "Problem":      RED,
    "Solution":     "#00695C",
    "Attribution":  "#4527A0",
}

if reports:
    r_cols = st.columns(2)
    for i, r in enumerate(reports):
        cat    = r["review_category"] or "Performance"
        colour = CATEGORY_COLOUR.get(cat, NAVY)
        status = r["status"] or "Draft"
        s_col  = GREEN if status == "Approved" else AMBER
        finding = (r["key_finding"] or "No finding recorded.")[:200]
        indicator = (r["indicator_statement"] or "")[:60]
        focus = r["specific_focus_area"] or ""

        with r_cols[i % 2]:
            st.markdown(
                f'<div style="border:1px solid {colour}50;border-left:4px solid {colour};'
                f'border-radius:6px;padding:12px 14px;margin-bottom:10px;background:{colour}06;">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
                f'<span style="font-size:0.72em;font-weight:bold;color:{colour};">{cat}</span>'
                f'<span style="font-size:0.68em;color:{s_col};font-weight:bold;">{status}</span>'
                f'</div>'
                f'<div style="font-size:0.78em;color:{NAVY};margin-bottom:4px;">'
                f'<b>{focus or indicator}</b></div>'
                f'<div style="font-size:0.76em;color:#333;">{finding}</div>'
                f'<div style="font-size:0.67em;color:#888;margin-top:6px;">{r["created_date"] or ""}</div>'
                '</div>',
                unsafe_allow_html=True,
            )
else:
    st.info("No decision reports yet — create them in Module G.")

# ── Section 6: MIS Framework Footer ──────────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<div style="background:{NAVY}0A;border:1px solid {NAVY}20;'
    f'border-radius:6px;padding:10px 16px;font-size:0.75em;color:#444;">'
    f'<b style="color:{NAVY};">MIS Framework (Laudon & Laudon, 16e)</b> · '
    'This dashboard completes the IS cycle: data entered in Modules C–E (Input) → '
    'analysed in Module D (Processing) → quality-checked in Module F (Review) → '
    'surfaced here as decision-ready impact evidence (Output). '
    'Strategic objective: <b>Improved Decision Making</b> + '
    '<b>Customer &amp; Supplier Intimacy</b> (donor reporting).'
    '</div>',
    unsafe_allow_html=True,
)

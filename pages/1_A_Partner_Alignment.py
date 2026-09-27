"""Module A — Partner Alignment

Flat, sortable table view of the SAWA commitment chain, one section per
level of the funnel:
  Level 1 — Anchor Partner Commitments (Life of Programme + confirmed
            partner Year 1 plans — filterable by which basis to show)
  Level 2 — CEL Year 1 Delivery
  Level 3 — Year 1 Results
  Level 4 — Programme Impact

Includes a time-basis reconciliation warning, inline editing for
Admin/Editor roles, and a one-page PDF export for donor decks.
"""
import io
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from database.db import init_db, run_query, run_write
from utils.shared_widgets import project_selector
from utils.auth import can, can_write_module
from projects.sawa import PILLAR_BUDGETS, PROJECT
from utils.nav_strip import render_nav_strip

st.set_page_config(page_title="Partner Alignment — CEL MEL", layout="wide")

# ── Shared visual language (fonts + warm/teal palette) ───────────────────────
# Matches the SAWA Partner Alignment reference: Fraunces for headings, Public
# Sans for body copy, IBM Plex Mono for figures/labels, on a warm-cream
# ground with a teal/sage/clay/ochre accent family instead of a stock
# Material rainbow.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    :root{
        --pa-bg:#F6F3EC; --pa-surface:#FFFFFF; --pa-ink:#16262E;
        --pa-muted:#5E6A6A; --pa-border:#DED7C6; --pa-accent:#1E7E76;
    }
    [data-testid="stAppViewContainer"] { background:var(--pa-bg); }
    .stApp, .stApp p, .stApp li, .stApp label, .stApp span {
        font-family:'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color:var(--pa-ink);
    }
    .stApp h1, .stApp h2, .stApp h3 {
        font-family:'Fraunces', Georgia, serif !important;
        color:var(--pa-ink) !important;
        letter-spacing:-.01em;
        font-weight:600 !important;
    }
    .stApp [data-testid="stCaptionContainer"] p,
    .stApp [data-testid="stCaptionContainer"] span {
        color:var(--pa-muted) !important;
        font-family:'Public Sans', sans-serif !important;
    }
    .stApp [data-testid="stDataFrame"] *,
    .stApp [data-testid="stMetricValue"] {
        font-family:'IBM Plex Mono', monospace !important;
    }
    .stApp button {
        font-family:'Public Sans', sans-serif !important;
        border-radius:8px !important;
    }
    .stApp [data-testid="stExpander"] summary {
        font-family:'Public Sans', sans-serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    st.caption(
        f"Role: **{st.session_state.get('role', 'Viewer')}**  \n"
        "Editors and Admins can edit target values inline."
    )

# ── Load targets ──────────────────────────────────────────────────────────────
targets = run_query(
    """
    SELECT pt.id, pt.level, pt.metric_label, pt.target_value, pt.unit,
           pt.time_basis, pt.source_doc, pt.source_page,
           COALESCE(p.name, 'Programme') AS partner_name
    FROM   partner_targets pt
    LEFT JOIN partners p ON pt.partner_id = p.partner_id
    WHERE  pt.project_id = :pid
    ORDER  BY pt.level, pt.id
    """,
    {"pid": project_id},
)

by_level: dict[int, list[dict]] = {lvl: [] for lvl in (1, 2, 3, 4)}
for t in targets:
    by_level[t["level"]].append(t)

# ── Time-basis reconciliation warning ────────────────────────────────────────
l1_lop  = any(t["time_basis"] == "Life of programme" for t in by_level[1])
l1_yr1  = any(t["time_basis"] == "Year 1" for t in by_level[1])
l23_yr1 = any(t["time_basis"] == "Year 1" for t in by_level[2] + by_level[3])

if l1_lop and l23_yr1:
    st.warning(
        "⚠️ **Do not sum Level 1 LoP totals with Level 2 & 3 Year 1 figures.**  \n"
        "**Level 1 LoP** rows are *Life of Programme* totals (2026–2030) from the "
        "original SAWA proposal.  \n"
        "**Levels 2 & 3** targets are *Year 1 only* (CEL Consolidated Workplan, "
        "Jul 2026 – Jun 2027).  \n"
        "To compare across levels, switch Level 1 to the **Year 1 tab** — those "
        "figures come directly from each partner's Sep 2026 implementation plan "
        "and sit on the same time basis as Levels 2 & 3."
    )

if l1_lop and l1_yr1:
    st.info(
        "ℹ️ **Level 1 has two tabs: LoP totals and confirmed Year 1 targets.**  \n"
        "**LOP badge** — Life of Programme totals from the original SAWA proposal.  \n"
        "**YR 1 badge** — confirmed from each partner's own Sep 2026 implementation "
        "plan. These are not a 1/5 estimate of the LoP — they are the partner's "
        "actual Year 1 commitment. Compare within a badge, not across badges."
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Module A — Partner Alignment")
st.caption(
    "Commitment chain from anchor partners → CEL delivery → Year 1 results → "
    "programme impact. Sort any table by clicking a column header; sources "
    "are their own column, not a hover-only tooltip."
)

editable = can_write_module("A")

# ── Summary stat tiles ────────────────────────────────────────────────────────
_n_partners = len({
    r["partner_name"] for r in by_level[1] if r["partner_name"] != "Programme"
})
_n_lop = sum(1 for r in by_level[1] if r["time_basis"] == "Life of programme")
_n_yr1 = sum(1 for r in by_level[1] if r["time_basis"] == "Year 1")
_span  = f"{PROJECT['start_date'][:4]}–{PROJECT['end_date'][:4]}"
_budget_m = f"${PROJECT['budget_total'] / 1_000_000:.2f}M"


def _stat_tile_html(value: str, label: str) -> str:
    return f"""
    <div style="background:#FFFFFF; border:1px solid #DED7C6; border-radius:10px;
                padding:14px 16px; box-shadow:0 1px 2px rgba(20,30,28,.05); min-height:64px;">
      <p style="margin:0; font-family:'IBM Plex Mono',monospace; font-variant-numeric:tabular-nums;
                font-size:1.35em; font-weight:600; color:#16262E;">{value}</p>
      <p style="margin:2px 0 0 0; font-family:'Public Sans',sans-serif; font-size:0.72em; color:#5E6A6A;">{label}</p>
    </div>"""


_stat_cols = st.columns(5)
for _c, (_val, _lbl) in zip(_stat_cols, [
    (str(_n_partners),      "Anchor partners"),
    (f"{_n_lop} / {_n_yr1}", "LOP rows · Year 1 rows"),
    (_span,                 "Programme span"),
    (_budget_m,              "Total programme budget"),
    (str(len(PILLAR_BUDGETS)), "Budget pillars"),
]):
    with _c:
        st.markdown(_stat_tile_html(_val, _lbl), unsafe_allow_html=True)

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# ── Level configuration (color = left-rule accent, no filled band anymore) ────
BANDS = {
    1: {
        "title": "Level 1 — Anchor Partner Commitments",
        "sub":   "LOP totals (SAWA Proposal, 28 Nov 2025) alongside partners' own "
                  "confirmed Year 1 plans (Sep 2026) — filter by basis below",
        "color": "#1E7E76",   # teal
    },
    2: {
        "title": "Level 2 — CEL Year 1 Delivery",
        "sub":   "Year 1 · Source: CEL Year 1 Consolidated Workplan",
        "color": "#4A6B5C",   # sage
    },
    3: {
        "title": "Level 3 — Year 1 Results",
        "sub":   "Year 1 indicator targets · Source: CEL Year 1 Consolidated Workplan",
        "color": "#B96A2E",   # clay
    },
    4: {
        "title": "Level 4 — Programme Impact",
        "sub":   "Life of Programme (2026–2030) · Source: SAWA Proposal, 28 Nov 2025",
        "color": "#A97C1E",   # ochre
    },
}

PILLAR_COLORS = ["#1E7E76", "#4A6B5C", "#B96A2E", "#A97C1E", "#7A8A93"]


def _section_header(band: dict) -> None:
    st.markdown(
        f"""<div style="border-left:4px solid {band['color']}; padding:2px 0 2px 14px; margin:26px 0 10px 0;">
            <span style="font-family:'Fraunces',Georgia,serif; font-size:1.15em; font-weight:600; color:#16262E;">{band['title']}</span><br>
            <span style="font-family:'Public Sans',sans-serif; font-size:0.78em; color:#5E6A6A;">{band['sub']}</span>
            </div>""",
        unsafe_allow_html=True,
    )


# ── Render each level as one flat, sortable table ─────────────────────────────
for lvl in (1, 2, 3, 4):
    band = BANDS[lvl]
    rows = by_level[lvl]

    _section_header(band)

    # Level 1 is the only level that mixes time bases (LOP totals alongside
    # partners' own Year 1 plans) — let the reader filter to one at a time
    # instead of scanning a mixed table for the basis they want.
    if lvl == 1 and rows:
        basis_filter = st.pills(
            "Show",
            options=["All", "Life of programme", "Year 1"],
            default="All",
            selection_mode="single",
            key="l1_basis_filter",
            label_visibility="collapsed",
        )
        if basis_filter and basis_filter != "All":
            rows = [r for r in rows if r["time_basis"] == basis_filter]

    if not rows:
        st.caption("No data — run `python -m database.seed_sawa` to load SAWA data.")
        continue

    show_partner = lvl == 1
    records = []
    for row in rows:
        rec: dict = {"Partner": row["partner_name"]} if show_partner else {}
        rec.update({
            "Metric":       row["metric_label"],
            "Target Value": row["target_value"],
            "Unit":         row["unit"],
            "Time Basis":   row["time_basis"],
            "Source":       row["source_doc"],
            "id":           row["id"],
        })
        records.append(rec)
    df = pd.DataFrame(records)

    if editable:
        disabled_cols = [c for c in df.columns if c != "Target Value"]
        edited = st.data_editor(
            df,
            key=f"editor_{lvl}",
            disabled=disabled_cols,
            hide_index=True,
            use_container_width=True,
            column_config={"id": None},
        )
        if st.button("💾 Save", key=f"save_{lvl}"):
            for _, r in edited.iterrows():
                run_write(
                    "UPDATE partner_targets SET target_value=:v WHERE id=:id",
                    {"v": str(r["Target Value"]), "id": int(r["id"])},
                )
            st.success("Saved.")
            st.rerun()
    else:
        st.dataframe(
            df, hide_index=True, use_container_width=True,
            column_config={"id": None},
        )

st.divider()

# ── Budget allocation chart ───────────────────────────────────────────────────
st.subheader("Budget Allocation by Pillar")

pillar_names  = list(PILLAR_BUDGETS.keys())
pillar_usd_m  = [v / 1_000_000 for v in PILLAR_BUDGETS.values()]
total_m       = sum(pillar_usd_m)

fig = go.Figure()
for name, val, col in zip(pillar_names, pillar_usd_m, PILLAR_COLORS):
    fig.add_trace(go.Bar(
        name=name,
        x=[val],
        y=["SAWA Budget"],
        orientation="h",
        marker_color=col,
        text=f"${val:.2f}M",
        textposition="inside",
        insidetextanchor="middle",
        hovertemplate=f"<b>{name}</b><br>${val:.2f}M ({100*val/total_m:.1f}%)<extra></extra>",
    ))

fig.update_layout(
    barmode="stack",
    title=dict(
        text=f"SAWA Programme Budget — USD {total_m:.2f}M total",
        font=dict(family="Fraunces, Georgia, serif", size=15, color="#16262E"),
    ),
    height=175,
    margin=dict(l=0, r=0, t=40, b=90),
    xaxis=dict(title=None, showgrid=True, gridcolor="#eee"),
    yaxis=dict(showticklabels=False),
    legend=dict(orientation="h", y=-1.5, x=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono, monospace", size=11, color="#5E6A6A"),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── SAWA Partners on the Map ──────────────────────────────────────────────────
st.subheader("SAWA Partners on the Map")
st.caption(
    "5 implementing partners · 40 communities · 10 of 16 regions  |  "
    "Every pair shares a region · 4 shared districts · "
    "5 hotspots where partners sit ≤15 km apart.  "
    "Source: SAWA Partner Mapping & Alignment (GPS validated), Sep 2026."
)
_map_path = Path(__file__).parent.parent / "assets" / "sawa_partner_map.webp"
if _map_path.exists():
    st.image(str(_map_path), use_container_width=True)
else:
    st.info("Map image not found — ensure assets/sawa_partner_map.webp is present in the repo.")

st.divider()

# ── CEL's Role in SAWA ────────────────────────────────────────────────────────
st.subheader("CEL's Delivery Role in SAWA")
st.caption("Source: CEL SAWA proposal (Value Chain Pathway & Job Roles slide, July 2026)")

rc1, rc2, rc3 = st.columns(3)
with rc1:
    st.markdown(
        '<div style="background:#E7F3F1;border-left:4px solid #1E7E76;'
        'border-radius:10px;padding:12px 16px;box-shadow:0 1px 2px rgba(20,30,28,.05);">'
        '<p style="margin:0 0 6px 0;font-family:\'Public Sans\',sans-serif;font-weight:700;color:#1E7E76;">Jobs Target</p>'
        '<p style="margin:0;font-family:\'IBM Plex Mono\',monospace;font-size:1.28em;font-weight:600;color:#125650;">600 D&amp;F</p>'
        '<p style="margin:0;font-size:0.78em;color:#5E6A6A;">Displaced &amp; Female participants</p>'
        '<p style="margin:8px 0 0 0;font-family:\'IBM Plex Mono\',monospace;font-size:1.28em;font-weight:600;color:#125650;">800 YiW</p>'
        '<p style="margin:0;font-size:0.78em;color:#5E6A6A;">Youth in Work</p>'
        '</div>',
        unsafe_allow_html=True,
    )
with rc2:
    st.markdown(
        '<div style="background:#FBEEE3;border-left:4px solid #B96A2E;'
        'border-radius:10px;padding:12px 16px;box-shadow:0 1px 2px rgba(20,30,28,.05);">'
        '<p style="margin:0 0 6px 0;font-family:\'Public Sans\',sans-serif;font-weight:700;color:#B96A2E;">CEL Delivers</p>'
        '<ul style="margin:0;padding-left:16px;font-size:0.82em;color:#3A2E24;">'
        '<li>BDS support at Grow-Out stage</li>'
        '<li>Training delivery at Hatchery stage</li>'
        '<li>Entrepreneurship &amp; business skills training (Fry→Juvenile)</li>'
        '<li>Business development for grow-out enterprises</li>'
        '<li>Mentorship &amp; enterprise coaching</li>'
        '</ul>'
        '</div>',
        unsafe_allow_html=True,
    )
with rc3:
    st.markdown(
        '<div style="background:#E9F1EC;border-left:4px solid #4A6B5C;'
        'border-radius:10px;padding:12px 16px;box-shadow:0 1px 2px rgba(20,30,28,.05);">'
        '<p style="margin:0 0 6px 0;font-family:\'Public Sans\',sans-serif;font-weight:700;color:#4A6B5C;">National Mandate</p>'
        '<ul style="margin:0;padding-left:16px;font-size:0.82em;color:#28362F;">'
        '<li>Enterprise training (national)</li>'
        '<li>Safeguarding focal point across all IPs</li>'
        '<li>Women in Aquaculture Network (WAN) establishment</li>'
        '<li>Independently manages programme grievance mechanism</li>'
        '<li>PWD target: 30 D&amp;F / 40 YiW</li>'
        '</ul>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── CEL Year 1 Measures — Partner Contributions ──────────────────────────────
st.subheader("CEL Year 1 Measures — Partner Contributions")
st.caption(
    "How each anchor and technical partner feeds into CEL's four Year 1 delivery "
    "measures.  Source: CEL's contribution to SAWA (Sep 2026) pp. 05–16 + "
    "partner Year 1 implementation decks, Sep 2026."
)

_cel_measures = pd.DataFrame([
    {
        "CEL Year 1 Measure":     "Women receiving BDS",
        "Target":                 "500",
        "How Partners Feed This": (
            "CEL coaches inside AgroKings, Aglow Farms, AFRIGEM, Newage and "
            "Naple Betta cohorts.  500 are the 'accelerator / enterprises in "
            "transition' cohort receiving direct BDS coaching.  "
            "TechnoServe reaches 320 young women through its grant mechanism — "
            "these are enterprises already in the BDS pipeline."
        ),
        "Partner Sources": (
            "AgroKings 800 groups → coaching entry · "
            "Aglow Farms 1,200 → 300 Q1 entry · "
            "AFRIGEM 1,000 → Q1 350 · "
            "Newage & Naple Betta hub members · "
            "TechnoServe 320 (grant-pipeline enterprises)"
        ),
    },
    {
        "CEL Year 1 Measure":     "WAN forum engagements",
        "Target":                 "500",
        "How Partners Feed This": (
            "WAN draws members from all partner cohorts; engagements = "
            "forums, bootcamp/exchange, market activities, road shows, "
            "institutionalise occupational health."
        ),
        "Partner Sources": (
            "CEL facilitates · All anchors supply members · "
            "FC provides Regulatory Day · "
            "CSIR contributes value-addition & product market inputs"
        ),
    },
    {
        "CEL Year 1 Measure":     "Women-led cooperatives/clusters strengthened",
        "Target":                 "25",
        "How Partners Feed This": (
            "Aglow Farms cluster model (15 communities), "
            "AFRIGEM cooperatives (4+), "
            "AgroKings groups graduating to cooperative ownership."
        ),
        "Partner Sources": (
            "Aglow Farms community cluster model · "
            "AFRIGEM cooperative formation · "
            "AgroKings rent-to-own group exit"
        ),
    },
    {
        "CEL Year 1 Measure":     "D&F jobs in value addition",
        "Target":                 "100",
        "How Partners Feed This": (
            "AgroKings 1909 processing & retail arm (190 women in roles); "
            "Naple Betta women-led grill outlets; Aglow Farms processing area.  "
            "TechnoServe targets 250 jobs through its micro-grant mechanism "
            "(10 catalytic grantees + 150 micro-grant businesses).  "
            "NewAge Agric targets 5,800 D&F jobs programme-wide; "
            "CEL's 100 tracks the value-addition slice."
        ),
        "Partner Sources": (
            "AgroKings 1909 (190 roles) · "
            "TechnoServe 250 jobs (10 catalytic + 150 micro-grant businesses) · "
            "Naple Betta grill outlets · "
            "Aglow Farms HQ processing · "
            "NewAge Agric (5,800 D&F jobs, 7 regions)"
        ),
    },
])

st.dataframe(
    _cel_measures,
    use_container_width=True,
    hide_index=True,
    column_config={
        "CEL Year 1 Measure": st.column_config.TextColumn("CEL Year 1 Measure", width="medium"),
        "Target":             st.column_config.TextColumn("Target",             width="small"),
        "How Partners Feed This": st.column_config.TextColumn("How Partners Feed This", width="large"),
        "Partner Sources":    st.column_config.TextColumn("Partner Sources",    width="large"),
    },
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Year 1 Quarterly Delivery Calendar ───────────────────────────────────────
st.subheader("Year 1 Quarterly Delivery Calendar")
st.caption(
    "CEL and partner activities by quarter, Jul 2026 – Jun 2027.  "
    "Source: CEL's contribution to SAWA (Sep 2026) + partner Year 1 implementation decks."
)

_QUARTERS = [
    {
        "cel_bds": (
            "Review needs & existing training; mobilise women for BDS; "
            "co-design modules with AFRIGEM, Aglow and AgroKings trainers."
        ),
        "cel_wan": (
            "Map groups and mentors; agree WAN priorities and participation; "
            "identify experienced women for peer mentorship."
        ),
        "agrokings": (
            "**Wave 1 – Greater Accra:** 3 cluster sites commissioned; 900 women recruited; "
            "300 tanks stocked July; first 120 hatchery roles filled; first harvest August."
        ),
        "aglow": (
            "**Foundation & Mobilisation:** confirm communities & sites; stakeholder engagement; "
            "beneficiary mobilisation & screening.  "
            "Q1 actual = 461 onboarded, 11 PWD, 9 communities."
        ),
        "afrigem": (
            "**350 women** onboarded; 3 anchor operators (traders, producers, processors); "
            "community sensitisation & identification."
        ),
        "naple_betta": (
            "**1,850 YW mobilised** — SET UP & MOBILISE: sign contracts; "
            "baseline + GYSI/PWD/safeguarding assessments; "
            "community entry & youth mobilisation; "
            "training in production; feed mill operations."
        ),
        "newage": (
            "**1,456 D&F jobs** created (2,007 reached).  "
            "Adwenepa App deployed — digital backbone for data, monitoring & stock.  "
            "e-Learning Centre live.  Recruitment & first onboarding."
        ),
        "technoserve": (
            "Programme orientation; pipeline mapping with CEL; "
            "identify potential grantee pool from BDS-prepared enterprises; "
            "design micro-grant criteria & screening process."
        ),
        "fc_csir": (
            "**FC:** Inception & stakeholder coordination; aquaculture regulation/licensing "
            "orientation; GAqP planning; broodstock linkages.  "
            "**CSIR:** Community entry; gender & needs assessment; policy review; research setup."
        ),
    },
    {
        "cel_bds": (
            "Co-create BDS modules; Training of Trainers (ToT); start coaching and thematic "
            "workshops — Regulatory Day w/ FC, Financial Literacy, Finance Readiness w/ TechnoServe."
        ),
        "cel_wan": (
            "Prepare WAN membership, representation, market and leadership activities; "
            "connect women's groups to buyer feedback and peer learning."
        ),
        "agrokings": (
            "**Wave 2 – Volta & Oti:** 4 cluster sites live; 1,000 women onboarded; "
            "300 tanks stocked Oct; 1909 intake opens; Wave 1 self-funds Cycle 2."
        ),
        "aglow": (
            "**Infrastructure & Production Readiness:** construct ponds & tarpaulin systems; "
            "ToT; full beneficiary training; safeguarding & GYSI orientation; "
            "stock certified production units."
        ),
        "afrigem": (
            "**350 more women** onboarded (700 cumulative); "
            "3 more anchor operators; door-to-door & group mobilisation."
        ),
        "naple_betta": (
            "**465 YiW** — STRUCTURE & BUILD CAPACITY: "
            "mobilisation of youth in processing; "
            "starter-pack support & fish production begins; "
            "PWD/accessibility and safeguarding actions."
        ),
        "newage": (
            "**+1,884 D&F jobs** (3,340 cumulative — 61.7% of Year 1 delivered).  "
            "Peak intake. Production infrastructure scaled.  "
            "First ~3-month cycles underway."
        ),
        "technoserve": (
            "Finance Readiness workshops with CEL; screen BDS-prepared enterprises; "
            "first **10 catalytic grantees** selected; "
            "micro-grant application process opens for 150 businesses."
        ),
        "fc_csir": (
            "**FC:** GAqP & SOP training; licensing guidance; facility/farm compliance "
            "assessments begin.  "
            "**CSIR:** GESI/shared decision-making; BDS & food-processing mentorship; "
            "feed/BSFL & hatchery training; water assessments."
        ),
    },
    {
        "cel_bds": (
            "Coaching, finance preparation and value-addition support; "
            "TechnoServe finance referrals for prepared enterprises; D&F jobs tracking."
        ),
        "cel_wan": (
            "WAN forums, bootcamp/exchange events, women-led group support; "
            "CEL + CSIR joint value-addition & markets workshop."
        ),
        "agrokings": (
            "**Wave 3 – Northern:** 3 cluster sites live; 350 women onboarded; "
            "200 tanks stocked Jan; mid-year survival & competency audit across all 10 clusters; "
            "graduate-mentor scheme opens."
        ),
        "aglow": (
            "**Production & Value-Chain Development:** intensive production mentoring; "
            "water-quality & fish-health monitoring; develop/commission processing facilities; "
            "establish aggregation; packaging & product specs."
        ),
        "afrigem": (
            "**150 more women** (850 cumulative); 2 anchor operators; "
            "eligibility screening of new cohort."
        ),
        "naple_betta": (
            "**542 YiW** (1,007 cumulative) — PRODUCE & CONNECT TO MARKET: "
            "support participants into fish production; "
            "value-add support; grill outlets live; "
            "marketing activities."
        ),
        "newage": (
            "**+1,218 D&F jobs** (4,558 cumulative).  "
            "Consolidation. First harvests as ~3-month cycles complete.  "
            "Market linkages active. Systems generating live M&E data."
        ),
        "technoserve": (
            "Micro-grants disbursed to **150 businesses**; "
            "catalytic grants fully deployed to 10 grantees; "
            "**250 jobs** creation tracked; "
            "fish trading volumes building toward 1,298+ MT."
        ),
        "fc_csir": (
            "**FC:** Continue technical support & compliance monitoring; "
            "two-tier certification pathway; quality-control & record-keeping support.  "
            "**CSIR:** Demonstration farms/RAS/water-saving practices; tech-transfer workshops; "
            "product development; certification support; adoption monitoring."
        ),
    },
    {
        "cel_bds": (
            "Follow sales, finance decisions and work outcomes; continue mentoring; "
            "review Year 1 BDS results; develop Year 2 modules."
        ),
        "cel_wan": (
            "WAN forums and group support; review member services and Year 2 priorities; "
            "SAWA Voices documents success stories."
        ),
        "agrokings": (
            "**Full cohort operational:** all 800 groups farming; all 400 operational roles filled; "
            "Wave 1 completes Cycle 6 and graduates — 300 tanks transferred to 900 owners; "
            "Year 2 pipeline opened."
        ),
        "aglow": (
            "**Harvest, Market & Consolidation:** harvest market-ready cycles; "
            "aggregate & process fish; supply confirmed markets; "
            "analyse income & job outcomes; Year 1 learning assessment; develop Year 2 scale-up plan."
        ),
        "afrigem": (
            "**150 more women** (1,000 total); 2 more anchor operators (10 total); "
            "follow up on licensing & certification."
        ),
        "naple_betta": (
            "**705 YiW** (1,712 total) — GROW, LEARN & ACCOUNT: "
            "production & input systems scale; "
            "575 participants supported into value addition; "
            "branding/certification + MEL/KPI review.  "
            "Year 1: 110 MT value-added trade · $841,500 revenue · 13 grill outlets."
        ),
        "newage": (
            "**+1,242 D&F jobs** (5,800 cumulative — Year 1 complete).  "
            "Year 1 cohort complete. Repeat cycles running.  "
            "Full-year data & review. Year 2 scale-up prepared."
        ),
        "technoserve": (
            "Monitor grant utilization & job outcomes; "
            "**1,298+ MT** fish collectively traded; "
            "**$845,000** value from catfish sales realised; "
            "Year 1 review; Year 2 pipeline identified."
        ),
        "fc_csir": (
            "**FC:** Technical audits; review GAqP/SOP gaps; policy/ecosystem-strengthening "
            "discussions; consolidate lessons for Year 2.  "
            "**CSIR:** Follow-up coaching; quality/certification; market/route-to-market support; "
            "Year 1 implementation review; next-year priorities."
        ),
    },
]

_q_tabs = st.tabs(["Q1 Jul–Sep 2026", "Q2 Oct–Dec 2026", "Q3 Jan–Mar 2027", "Q4 Apr–Jun 2027"])
for _tab, _qd in zip(_q_tabs, _QUARTERS):
    with _tab:
        _col1, _col2 = st.columns(2)
        with _col1:
            st.markdown("**CEL — BDS Delivery**")
            st.markdown(_qd["cel_bds"])
            st.markdown("**CEL — WAN & Partner Engagement**")
            st.markdown(_qd["cel_wan"])
        with _col2:
            st.markdown("**AgroKings**")
            st.markdown(_qd["agrokings"])
            st.markdown("**Aglow Farms**")
            st.markdown(_qd["aglow"])
        _col3, _col4, _col5 = st.columns(3)
        with _col3:
            st.markdown("**AFRIGEM**")
            st.markdown(_qd["afrigem"])
        with _col4:
            st.markdown("**Naple Betta**")
            st.markdown(_qd["naple_betta"])
        with _col5:
            st.markdown("**NewAge Agric**")
            st.markdown(_qd["newage"])
        _col6, _col7 = st.columns(2)
        with _col6:
            st.markdown("**TechnoServe**")
            st.markdown(_qd["technoserve"])
        with _col7:
            st.markdown("**FC & CSIR**")
            st.markdown(_qd["fc_csir"])

st.markdown("<br>", unsafe_allow_html=True)

# ── Partner Roles & Expectations ─────────────────────────────────────────────
st.subheader("Partner Roles & Expectations")
st.caption("Source: SAWA Partner Roles & Expectations slide — defines the mutual accountability framework.")

pe1, pe2 = st.columns(2)
with pe1:
    st.markdown(
        '<div style="background:#FFFFFF;border:1px solid #DED7C6;border-radius:10px;overflow:hidden;'
        'box-shadow:0 1px 2px rgba(20,30,28,.05);">'
        '<div style="background:#1E7E76;padding:8px 14px;">'
        '<p style="margin:0;color:white;font-family:\'IBM Plex Mono\',monospace;font-weight:600;'
        'letter-spacing:.03em;font-size:0.8em;">WHAT SAWA / AGRI-IMPACT PROVIDES</p>'
        '</div>'
        '<div style="padding:12px 16px;">'
        '<ul style="margin:0;padding-left:16px;font-size:0.84em;color:#16262E;">'
        '<li>Funding and resource mobilisation</li>'
        '<li>Program management and coordination</li>'
        '<li>Training and capacity building support</li>'
        '<li>MEL systems and reporting frameworks</li>'
        '<li>Safeguarding infrastructure</li>'
        '<li>Market linkage facilitation</li>'
        '</ul>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with pe2:
    st.markdown(
        '<div style="background:#FFFFFF;border:1px solid #DED7C6;border-radius:10px;overflow:hidden;'
        'box-shadow:0 1px 2px rgba(20,30,28,.05);">'
        '<div style="background:#B96A2E;padding:8px 14px;">'
        '<p style="margin:0;color:white;font-family:\'IBM Plex Mono\',monospace;font-weight:600;'
        'letter-spacing:.03em;font-size:0.8em;">WHAT IMPLEMENTING PARTNERS COMMIT TO</p>'
        '</div>'
        '<div style="padding:12px 16px;">'
        '<ul style="margin:0;padding-left:16px;font-size:0.84em;color:#16262E;">'
        '<li>Infrastructure and facility access</li>'
        '<li>Technical expertise and last-mile delivery</li>'
        '<li>Participant recruitment and mobilisation</li>'
        '<li>Compliance with safeguarding standards</li>'
        '<li>Data reporting and MEL participation</li>'
        '<li>Co-investment and private sector leverage</li>'
        '</ul>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

st.divider()

# ── PDF export ────────────────────────────────────────────────────────────────
def _build_pdf() -> bytes:
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib import colors as C
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )

    RL_COLORS = {
        1: C.HexColor("#00838F"),
        2: C.HexColor("#6A1B9A"),
        3: C.HexColor("#BF360C"),
        4: C.HexColor("#E65100"),
    }
    LEVEL_TITLES = {
        1: "Level 1 — Anchor Partner Commitments (Life of Programme)",
        2: "Level 2 — CEL Year 1 Delivery (Year 1)",
        3: "Level 3 — Year 1 Results",
        4: "Level 4 — Programme Impact (Life of Programme)",
    }

    def style(name, **kw):
        return ParagraphStyle(name, **kw)

    title_s   = style("T",  fontName="Helvetica-Bold", fontSize=15, spaceAfter=4)
    warning_s = style("W",  fontName="Helvetica",      fontSize=7.5,
                      textColor=C.HexColor("#7B5800"),
                      backColor=C.HexColor("#FFF3CD"), borderPad=5, spaceAfter=8)
    small_s   = style("S",  fontName="Helvetica",      fontSize=7.5)
    h2_s      = style("H2", fontName="Helvetica-Bold", fontSize=9, spaceAfter=3, spaceBefore=10)

    story = [
        Paragraph("SAWA — Partner Alignment Funnel", title_s),
        Paragraph(
            "⚠ Time-basis notice: Level 1 targets are Life of Programme totals; "
            "Levels 2 & 3 are Year 1 only. Do NOT sum across levels.",
            warning_s,
        ),
    ]

    for lvl in (1, 2, 3, 4):
        rows  = by_level[lvl]
        color = RL_COLORS[lvl]

        # Level header row
        header_tbl = Table(
            [[Paragraph(LEVEL_TITLES[lvl],
                        style(f"LH{lvl}", fontName="Helvetica-Bold", fontSize=9,
                              textColor=C.white))]],
            colWidths=[26*cm],
        )
        header_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        story.append(header_tbl)

        if not rows:
            story.append(Paragraph("No data.", small_s))
            continue

        tdata = [["Metric / Partner", "Target", "Unit", "Time Basis"]]
        for r in rows:
            lbl = (f"{r['partner_name']}: {r['metric_label']}"
                   if r["partner_name"] != "Programme" else r["metric_label"])
            tdata.append([lbl, r["target_value"], r["unit"], r["time_basis"]])

        tbl = Table(tdata, colWidths=[13*cm, 3.5*cm, 3.5*cm, 5*cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), C.HexColor("#E0E0E0")),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C.HexColor("#FAFAFA"), C.white]),
            ("GRID",          (0, 0), (-1, -1), 0.3, C.HexColor("#BDBDBD")),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)

    # Budget table
    story.append(Spacer(1, 10))
    story.append(Paragraph("Budget Allocation by Pillar", h2_s))

    total_b = sum(PILLAR_BUDGETS.values())
    bdata   = [["Pillar", "USD", "% of Total"]]
    for pillar, amt in PILLAR_BUDGETS.items():
        bdata.append([pillar, f"${amt/1e6:.2f}M", f"{100*amt/total_b:.1f}%"])
    bdata.append(["TOTAL", f"${total_b/1e6:.2f}M", "100.0%"])

    btbl = Table(bdata, colWidths=[13*cm, 5*cm, 5*cm])
    btbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0),  (-1, 0),  C.HexColor("#263238")),
        ("TEXTCOLOR",     (0, 0),  (-1, 0),  C.white),
        ("FONTNAME",      (0, 0),  (-1, 0),  "Helvetica-Bold"),
        ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND",    (0, -1), (-1, -1), C.HexColor("#ECEFF1")),
        ("FONTSIZE",      (0, 0),  (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, 1),  (-1, -2), [C.HexColor("#FAFAFA"), C.white]),
        ("GRID",          (0, 0),  (-1, -1), 0.3, C.HexColor("#BDBDBD")),
        ("TOPPADDING",    (0, 0),  (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0),  (-1, -1), 3),
        ("LEFTPADDING",   (0, 0),  (-1, -1), 5),
    ]))
    story.append(btbl)

    doc.build(story)
    return buf.getvalue()


col_exp, col_btn = st.columns([4, 1])
with col_btn:
    if st.button("📄 Export PDF", use_container_width=True):
        with st.spinner("Building PDF…"):
            try:
                pdf_bytes = _build_pdf()
                st.download_button(
                    "⬇ Download PDF",
                    data=pdf_bytes,
                    file_name="sawa_partner_alignment.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except ImportError:
                st.error("Install reportlab: `pip install reportlab`")

st.divider()

# ── A2: Year 1 Target Consistency Check ──────────────────────────────────────
with st.expander("📋 Year 1 Target Consistency Check", expanded=False):
    st.caption(
        "Compares three copies of Year 1 targets: "
        "**Module A** (partner_targets Level 2), "
        "**Module B** (logframe target_annual), and "
        "**Module E** (raw_data_analysis target_value).  "
        "Flags mismatches so they can be reconciled before reporting."
    )
    _lf_targets = run_query(
        """SELECT lr.indicator_code, lr.indicator_statement, lr.target_annual
           FROM   logframe_rows lr
           JOIN   projects pr ON pr.project_id = lr.project_id
           WHERE  pr.name = 'SAWA' AND lr.indicator_code IS NOT NULL""",
        {},
    )
    _rda_targets = run_query(
        """SELECT lf.indicator_code, r.target_value AS rda_target
           FROM   raw_data_analysis r
           JOIN   logframe_rows lf ON lf.id = r.logframe_row_id
           JOIN   projects pr ON pr.project_id = r.project_id
           WHERE  pr.name = 'SAWA' AND r.partner_id IS NULL""",
        {},
    )
    _rda_map = {r["indicator_code"]: r["rda_target"] for r in _rda_targets}
    _pt_lvl2 = run_query(
        """SELECT pt.metric_label, pt.target_value
           FROM   partner_targets pt
           JOIN   projects pr ON pr.project_id = pt.project_id
           WHERE  pr.name = 'SAWA' AND pt.level = 2 AND pt.time_basis = 'Year 1'""",
        {},
    )

    _mismatches = []
    for row in _lf_targets:
        code   = row["indicator_code"]
        lf_val = str(row.get("target_annual") or "").strip()
        rda_val = str(_rda_map.get(code) or "").strip()
        if lf_val and rda_val and lf_val != rda_val:
            _mismatches.append({
                "Indicator": code,
                "Statement": (row.get("indicator_statement") or "")[:60],
                "Module B (logframe)": lf_val,
                "Module E (RDA)": rda_val,
                "Source": "B vs E",
            })

    if _mismatches:
        st.warning(f"**{len(_mismatches)} mismatch(es) detected** between Module B and Module E targets.")
        st.dataframe(pd.DataFrame(_mismatches), hide_index=True, use_container_width=True)
    else:
        st.success("✅ Module B and Module E Year 1 targets are consistent.")

    if _pt_lvl2:
        st.markdown("**Module A — Level 2 Year 1 targets (CEL Delivery)**")
        st.dataframe(
            pd.DataFrame(_pt_lvl2).rename(columns={"metric_label": "Metric", "target_value": "Target"}),
            hide_index=True, use_container_width=True,
        )
        st.caption(
            "Module A Level 2 targets use narrative labels — match to indicator codes manually. "
            "Edit in Module A above if targets have been revised."
        )

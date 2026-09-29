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
import re as _re_md
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
    .stApp {
        font-family:'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color:var(--pa-ink);
    }
    .stApp h1, .stApp h2, .stApp h3 {
        font-family:'Fraunces', Georgia, serif !important;
        color:var(--pa-ink) !important;
        letter-spacing:-.01em;
        font-weight:600 !important;
    }
    .stApp [data-testid="stCaptionContainer"] p {
        color:var(--pa-muted) !important;
    }
    .stApp [data-testid="stDataFrame"] *,
    .stApp [data-testid="stMetricValue"] {
        font-family:'IBM Plex Mono', monospace !important;
    }
    .stApp button {
        border-radius:8px !important;
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
    with st.expander("Time-basis note — LoP vs Year 1 figures", expanded=False):
        st.markdown(
            "**Do not sum Level 1 LoP totals with Level 2 & 3 Year 1 figures.**  \n"
            "**Level 1 LoP** rows are *Life of Programme* totals (2026–2030) from the "
            "original SAWA proposal.  \n"
            "**Levels 2 & 3** targets are *Year 1 only* (CEL Consolidated Workplan, "
            "Jul 2026 – Jun 2027).  \n"
            "To compare across levels, switch Level 1 to the **Year 1 tab** — those "
            "figures come directly from each partner's Sep 2026 implementation plan "
            "and sit on the same time basis as Levels 2 & 3."
        )

if l1_lop and l1_yr1:
    with st.expander("Level 1 tabs — LoP totals vs confirmed Year 1 targets", expanded=False):
        st.markdown(
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
        st.caption("No programme data loaded yet. Contact the MEAL Lead to initialise SAWA data.")
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
    pass

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
        '<li>Business development services, training and mentorship to young women entrepreneurs</li>'
        '<li>Tiers and tracks enterprises from foundational training to bankable status</li>'
        '<li>Refers grant-ready entrepreneurs to TechnoServe and mentors promising businesses beyond the core cohort</li>'
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

# ── How CEL Structures BDS & WAN Delivery ────────────────────────────────────
# The two Sep 2026 CEL concept notes are the operating-model detail behind
# the Level 2/3 figures above — every quantity in their own Year 1 tables
# (Women mobilised 95/135/135/135, WAN forum engagements 300/200, D&F jobs in
# value addition 40/30/30, PWD mentors 1/2/2/3) matches this page's existing
# numbers exactly, so this section adds the "how", not new figures.
st.subheader("How CEL Structures BDS & WAN Delivery")
st.caption(
    "Source: Draft CEL SAWA BDS Implementation Concept Note (28 Sep 2026) · "
    "Draft CEL SAWA WAN Concept Note and Initial Actions (28 Sep 2026)."
)

bds1, bds2, bds3 = st.columns(3)
with bds1:
    st.markdown(
        '<div style="background:#E7F3F1;border-left:4px solid #1E7E76;'
        'border-radius:10px;padding:12px 16px;box-shadow:0 1px 2px rgba(20,30,28,.05);">'
        '<p style="margin:0 0 6px 0;font-family:\'Public Sans\',sans-serif;font-weight:700;color:#1E7E76;">BDS Group 1 — Ideation &amp; Early Business Development</p>'
        '<p style="margin:0;font-size:0.82em;color:#28362F;">Partner-led. CEL reviews existing BDS materials, '
        'co-creates cohort-based modules, and provides ToT, co-facilitation and follow-up where needed. '
        'Practical assignments cover customers, costs and running the activity as a business.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
with bds2:
    st.markdown(
        '<div style="background:#FBEEE3;border-left:4px solid #B96A2E;'
        'border-radius:10px;padding:12px 16px;box-shadow:0 1px 2px rgba(20,30,28,.05);">'
        '<p style="margin:0 0 6px 0;font-family:\'Public Sans\',sans-serif;font-weight:700;color:#B96A2E;">BDS Group 2 — Accelerators &amp; Enterprises in Transition</p>'
        '<p style="margin:0;font-size:0.82em;color:#3A2E24;">CEL provides direct coaching and mentoring. '
        'Entry reflects commitment and business need — women do not need to be finance- or scale-ready '
        'before coaching starts. Partner technical staff stay involved in production and quality decisions.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
with bds3:
    st.markdown(
        '<div style="background:#E9F1EC;border-left:4px solid #4A6B5C;'
        'border-radius:10px;padding:12px 16px;box-shadow:0 1px 2px rgba(20,30,28,.05);">'
        '<p style="margin:0 0 6px 0;font-family:\'Public Sans\',sans-serif;font-weight:700;color:#4A6B5C;">Support Across Both Groups</p>'
        '<p style="margin:0;font-size:0.82em;color:#28362F;">Half-day workshops on regulatory requirements, '
        'financial literacy, digital business skills and market access — using participants\' own records or '
        'products, ending in a practical action and a named follow-up contact.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

_bds_finding = pd.DataFrame([
    {"Finding": "Exploring or testing an aquaculture activity",
     "Support & Output": "Partner-led ideation and prototyping, with CEL business modules and trainer support. Output: a tested business idea and practical assignments on customers and costs."},
    {"Finding": "Committed enterprise with gaps in management or market evidence",
     "Support & Output": "CEL diagnosis followed by coaching and mentoring. Output: an enterprise growth plan with priorities, baseline, actions, responsibilities and review dates."},
    {"Finding": "A common issue affecting several groups",
     "Support & Output": "A half-day workshop with the relevant partner, followed by business or regulatory actions. Output: participant action list and referral follow-up."},
    {"Finding": "A justified financing need with supporting business evidence",
     "Support & Output": "CEL prepares the enterprise and agrees a referral to TechnoServe under its criteria. Output: required records and documents, referral and assessment feedback."},
])
st.dataframe(
    _bds_finding, hide_index=True, use_container_width=True,
    column_config={
        "Finding":          st.column_config.TextColumn("Finding", width="medium"),
        "Support & Output": st.column_config.TextColumn("Support & Output", width="large"),
    },
)
st.markdown(
    '<div style="background:#F6F3EC;border-left:3px solid #8A9494;border-radius:8px;'
    'padding:10px 14px;margin-top:6px;">'
    '<p style="margin:0;font-size:0.78em;color:#5E6A6A;">'
    '<strong style="color:#16262E;">Proposed, not yet confirmed:</strong> CEL is separately proposing a '
    'dedicated Finance Department to operationalise the "financing need" row above — financial literacy, '
    'costing/pricing, budgeting and cash-flow, finance-readiness assessment, referral and post-referral '
    'mentoring, feeding into the same TechnoServe referral pathway. Its own KPIs are explicitly described as '
    '"proposed... to be finalised with the consolidated workplan" and validation with partners is still the '
    'first step, so no targets are shown here. '
    '<em>Source: SAWA/CEL Finance Department Concept Note and Partner Questionnaire, Sep 2026.</em></p>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

wan1, wan2, wan3 = st.columns(3)
for _col, (_title, _body, _color, _bg, _txt) in zip(
    (wan1, wan2, wan3),
    [
        ("Access to Markets",
         "Market information, buyer contacts and collective activities where commercially useful. CEL provides "
         "the costing, negotiation and business support needed to act on opportunities.",
         "#1E7E76", "#E7F3F1", "#125650"),
        ("Advocacy & Policy Influence",
         "A practical route to raise recurring barriers, prepare evidence and engage responsible institutions. "
         "The advocacy agenda comes from women's own experience of operating in the sector.",
         "#B96A2E", "#FBEEE3", "#7A3D14"),
        ("Role Modelling & Leadership",
         "Experienced women mentor emerging entrepreneurs and are prepared to chair meetings, represent members "
         "and take part in sector dialogue — with consent, via SAWA Voices and e-SAWA.",
         "#4A6B5C", "#E9F1EC", "#2A3F35"),
    ],
):
    with _col:
        st.markdown(
            f'<div style="background:{_bg};border-left:4px solid {_color};'
            f'border-radius:10px;padding:12px 16px;box-shadow:0 1px 2px rgba(20,30,28,.05);">'
            f'<p style="margin:0 0 6px 0;font-family:\'Public Sans\',sans-serif;font-weight:700;color:{_color};">{_title}</p>'
            f'<p style="margin:0;font-size:0.82em;color:{_txt};">{_body}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
st.caption(
    "WAN membership is open across partner groups and does not depend on admission to CEL's direct BDS coaching."
)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown("**WAN charter — topics under co-creation with women (interim agreement by 30 October 2026)**")

_wan_charter = pd.DataFrame([
    {"Charter Topic": "Membership and purpose",
     "Initial Agreement Required": "Who can participate, how groups affiliate, member rights and the services WAN will initially provide."},
    {"Charter Topic": "Representation and decisions",
     "Initial Agreement Required": "How representatives are chosen, their term and responsibilities, how priorities are agreed and how members can replace or challenge representatives."},
    {"Charter Topic": "Accountability",
     "Initial Agreement Required": "Meeting and financial records, reporting back to members, conflicts of interest and transparent handling of any common resources."},
    {"Charter Topic": "Participation and feedback",
     "Initial Agreement Required": "Accessible channels, response dates for feedback, a named confidential safeguarding route, and separate consent for stories or photographs."},
    {"Charter Topic": "Coordination and continuity",
     "Initial Agreement Required": "CEL's establishment role, partner contributions, arrangements for member management and a date to review the interim structure."},
])
st.dataframe(
    _wan_charter, hide_index=True, use_container_width=True,
    column_config={
        "Charter Topic":               st.column_config.TextColumn("Charter Topic", width="medium"),
        "Initial Agreement Required":  st.column_config.TextColumn("Initial Agreement Required", width="large"),
    },
)

st.markdown(
    '<div style="background:#FBF3DF;border-left:4px solid #A97C1E;border-radius:10px;'
    'padding:12px 16px;margin-top:10px;box-shadow:0 1px 2px rgba(20,30,28,.05);">'
    '<p style="margin:0 0 6px 0;font-family:\'Public Sans\',sans-serif;font-weight:700;color:#7A5A10;">What these figures do not mean</p>'
    '<p style="margin:0 0 4px 0;font-size:0.82em;color:#4A3A10;">'
    '<strong>D&amp;F jobs in value addition (100):</strong> "Attendance or a finance referral alone will not be '
    'reported as a job outcome" — work outcomes depend on production, sales and other partner inputs. '
    '<em>Source: BDS concept note, Targets responsibilities and resources.</em></p>'
    '<p style="margin:0;font-size:0.82em;color:#4A3A10;">'
    '<strong>WAN forum engagements (500) and groups strengthened (25):</strong> "Forum engagements and unique '
    'women will be reported separately... BDS, WAN and work results will not be added together as unique '
    'programme reach." <em>Source: WAN concept note, Year 1 delivery and evidence of progress.</em></p>'
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

# ── Partner Commitments → CEL Results → Programme Impact ────────────────────
# Extends the L1→L2 table above (CEL's own Year 1 delivery measures) with the
# rest of the chain: CEL's Year 1 Results (Level 3) and the Life-of-Programme
# target each ladders toward (Level 4). Grouped by theme, not by a 1:1 metric
# match — partner and CEL figures measure different things at different
# scopes (e.g. Naple Betta's 1,284 D&F jobs vs CEL's own 100, which tracks
# only the value-addition slice CEL itself delivers) — so partner figures are
# shown as contribution context, never summed into CEL's own target.
st.subheader("Partner Commitments → CEL Results → Programme Impact")
st.caption(
    "Groups each partner's Year 1 commitment by theme against CEL's own Year 1 "
    "Results (Level 3) and the Life-of-Programme target it ladders toward "
    "(Level 4). CEL's Level 3 figures are its own specific delivery slice, not "
    "a sum of partner totals — partner figures are shown for contribution "
    "context only, on the same 'do not sum across levels' basis as the "
    "time-basis note above.  Source: partner Year 1 implementation decks "
    "(Sep 2026) + CEL Year 1 Consolidated Workplan + SAWA Proposal (28 Nov 2025)."
)

_contribution_map = pd.DataFrame([
    {
        "Theme": "Jobs & livelihoods (D&F)",
        "Partner Year 1 Commitments": (
            "Naple Betta 1,284 D&F jobs · NewAge Agric 5,800 D&F jobs · "
            "TechnoServe 250 jobs (10 catalytic grantees + 150 micro-grant businesses)"
        ),
        "CEL Year 1 Results (Level 3)": (
            "PIII.R1 D&F jobs (value addition) — 100 jobs · "
            "PII.R5 D&F jobs (PWD, programme-wide) — 8 jobs"
        ),
        "Programme Impact by 2030 (Level 4)": (
            "60,000+ young women & PWDs into D&F work · 86% D&F transition rate"
        ),
    },
    {
        "Theme": "PWD inclusion",
        "Partner Year 1 Commitments": (
            "Fisheries Commission 750 · AgroKings 170 · NewAge Agric 290 · "
            "AFRIGEM 50 · Aglow Farms 45 · Naple Betta 15 · TechnoServe 10"
        ),
        "CEL Year 1 Results (Level 3)": (
            "PII.R5 D&F jobs (PWD) — 8 jobs · "
            "PII.R6 Fish produced by PWDs — 9 MT · "
            "PII.R7 Revenue, PWDs in D&F — $16,667"
        ),
        "Programme Impact by 2030 (Level 4)": (
            "Counted within the 60,000+ young women & PWDs into D&F work "
            "target — no separate PWD-only LoP figure exists"
        ),
    },
    {
        "Theme": "Fish production & value addition",
        "Partner Year 1 Commitments": (
            "TechnoServe 1,298+ MT fish traded, $845,000 from catfish sales · "
            "Naple Betta 110 MT value-added trade, $841,500 revenue"
        ),
        "CEL Year 1 Results (Level 3)": (
            "PIII.R2 Fish produced/traded — 115.74 MT · "
            "PIII.R3 Revenue, value-added trading — $208,333"
        ),
        "Programme Impact by 2030 (Level 4)": (
            "50,000 MT additional fish production/year (Annual) · "
            "$90M additional annual revenue (Annual)"
        ),
    },
    {
        "Theme": "Enterprise & cooperative development",
        "Partner Year 1 Commitments": (
            "AgroKings 800 group enterprises · Fisheries Commission 500 "
            "enterprises supported · TechnoServe 10 catalytic grantees + "
            "150 micro-grant businesses"
        ),
        "CEL Year 1 Results (Level 3)": (
            "No direct Level 3 indicator — feeds Level 2's Women-led "
            "cooperatives/clusters strengthened (25) instead"
        ),
        "Programme Impact by 2030 (Level 4)": (
            "2,500 women-led microenterprises funded"
        ),
    },
    {
        "Theme": "Reach — young women & communities",
        "Partner Year 1 Commitments": (
            "Fisheries Commission 15,000 participants · AgroKings 2,650 · "
            "Aglow Farms 1,200 · Naple Betta 1,850 mobilised · AFRIGEM 1,000 · "
            "TechnoServe 320 · CSIR 100 coached"
        ),
        "CEL Year 1 Results (Level 3)": (
            "No direct Level 3 indicator — feeds Level 2's five 500-target "
            "measures instead (youth mobilised, BDS, coaching & mentorship, "
            "WAN engagements, safeguarding trained)"
        ),
        "Programme Impact by 2030 (Level 4)": (
            "60,000+ young women & PWDs into D&F work"
        ),
    },
])

st.dataframe(
    _contribution_map,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Theme":                             st.column_config.TextColumn("Theme", width="small"),
        "Partner Year 1 Commitments":         st.column_config.TextColumn("Partner Year 1 Commitments", width="large"),
        "CEL Year 1 Results (Level 3)":       st.column_config.TextColumn("CEL Year 1 Results (Level 3)", width="large"),
        "Programme Impact by 2030 (Level 4)": st.column_config.TextColumn("Programme Impact by 2030 (Level 4)", width="large"),
    },
)

st.markdown("<br>", unsafe_allow_html=True)

# ── SAWA Year 1 Consolidated Workplan cross-reference ────────────────────────
# Traces every Level 2/3 figure above back to its exact line item and
# quarterly phasing in the SAWA Programme Year 1 Consolidated Workplan —
# the granular ID-coded source (Pillars I-IV, e.g. "III.R1") that Module A's
# narrative labels ("PIII.R1 D&F jobs (value addition)") summarise. Defined
# here so both this page and the Excel export below read from the same
# table; rendered further down, next to the automated consistency check,
# since both exist to answer "where did this number come from."
_workplan_xref = pd.DataFrame([
    # ── Level 2 — CEL Year 1 Delivery ──
    {"Level": "L2", "CEL Metric": "Youth mobilised", "Value": "500",
     "Workplan ID": "I.1",
     "Activity / Result": "Mobilize youth into the programme (community entry, sensitisation, selection)",
     "Relevant Anchor Partner(s)": "AgroKings · Aglow Farms · AFRIGEM · Naple Betta · NewAge Agric (Q1 mobilisation waves)",
     "Q1": 95, "Q2": 135, "Q3": 135, "Q4": 135, "Year 1 Total": 500},
    {"Level": "L2", "CEL Metric": "Women receiving BDS", "Value": "500",
     "Workplan ID": "I.3",
     "Activity / Result": "Deliver BDS training (entrepreneurship, new business support) for over 2,000 young women & PWDs",
     "Relevant Anchor Partner(s)": "AgroKings · Aglow Farms · AFRIGEM · Newage · Naple Betta · TechnoServe (grant-pipeline enterprises)",
     "Q1": 95, "Q2": 135, "Q3": 135, "Q4": 135, "Year 1 Total": 500},
    {"Level": "L2", "CEL Metric": "Women in coaching & mentorship", "Value": "500",
     "Workplan ID": "I.17",
     "Activity / Result": "Deliver gender training, financial literacy and business mentoring for women-led cooperatives",
     "Relevant Anchor Partner(s)": "AgroKings · Aglow Farms · AFRIGEM · Naple Betta cohorts",
     "Q1": "", "Q2": 150, "Q3": 150, "Q4": 200, "Year 1 Total": 500},
    {"Level": "L2", "CEL Metric": "WAN forum engagements", "Value": "500",
     "Workplan ID": "I.11",
     "Activity / Result": "Facilitate leadership and mentorship forums under the Women in Aquaculture Network (WAN)",
     "Relevant Anchor Partner(s)": "All anchor partners supply members · FC (Regulatory Day) · CSIR (value-addition & market inputs)",
     "Q1": "", "Q2": "", "Q3": 300, "Q4": 200, "Year 1 Total": 500},
    {"Level": "L2", "CEL Metric": "Women-led cooperatives/clusters strengthened", "Value": "25",
     "Workplan ID": "I.18 / III.6",
     "Activity / Result": "Develop gender-responsive governance frameworks / strengthen women-led cooperatives & clusters",
     "Relevant Anchor Partner(s)": "Aglow Farms (cluster model) · AFRIGEM (cooperative formation) · AgroKings (rent-to-own group exit)",
     "Q1": "", "Q2": "", "Q3": 15, "Q4": 10, "Year 1 Total": 25},
    {"Level": "L2", "CEL Metric": "Gender-transformative trained", "Value": "500",
     "Workplan ID": "I.19", "Activity / Result": "Deliver gender transformative trainings",
     "Relevant Anchor Partner(s)": "All anchor cohorts · CSIR (GESI / shared decision-making)",
     "Q1": "", "Q2": 150, "Q3": 150, "Q4": 200, "Year 1 Total": 500},
    {"Level": "L2", "CEL Metric": "Safeguarding trained", "Value": "500",
     "Workplan ID": "I.20",
     "Activity / Result": "Train young women to identify and respond to safeguarding issues",
     "Relevant Anchor Partner(s)": "All anchor cohorts — CEL is safeguarding focal point across all IPs",
     "Q1": "", "Q2": 150, "Q3": 150, "Q4": 200, "Year 1 Total": 500},
    {"Level": "L2", "CEL Metric": "PWD mentors identified", "Value": "8",
     "Workplan ID": "I.13",
     "Activity / Result": "Identify young female PWDs in aquaculture as mentors",
     "Relevant Anchor Partner(s)": "Drawn from partners reporting PWD reach: AgroKings, Fisheries Commission, NewAge Agric, AFRIGEM, Aglow Farms, Naple Betta, TechnoServe",
     "Q1": 1, "Q2": 2, "Q3": 2, "Q4": 3, "Year 1 Total": 8},
    # ── Level 3 — Year 1 Results ──
    {"Level": "L3", "CEL Metric": "PIII.R1 D&F jobs (value addition)", "Value": "100",
     "Workplan ID": "III.R1",
     "Activity / Result": "Young women accessing D&F in Aquaculture Value Addition (YiW)",
     "Relevant Anchor Partner(s)": "AgroKings (1909 processing/retail) · Naple Betta (grill outlets) · Aglow Farms (HQ processing) · TechnoServe (micro-grant businesses)",
     "Q1": "", "Q2": 40, "Q3": 30, "Q4": 30, "Year 1 Total": 100},
    {"Level": "L3", "CEL Metric": "PII.R5 D&F jobs (PWD, programme-wide)", "Value": "8",
     "Workplan ID": "II.R5",
     "Activity / Result": "Persons with Disabilities (PWD) accessing D&F in Aquaculture value chain — programme-wide",
     "Relevant Anchor Partner(s)": "Naple Betta is the only partner reporting a matching \"PWD in D&F work\" figure (15) — other partners' PWD numbers (e.g. AgroKings 170, NewAge Agric 290) measure broader PWD reach, not confirmed D&F job placement, so are not counted here",
     "Q1": 1, "Q2": 2, "Q3": 2, "Q4": 3, "Year 1 Total": 8},
    {"Level": "L3", "CEL Metric": "PII.R6 Fish produced by PWDs in D&F", "Value": "9 MT",
     "Workplan ID": "II.R6",
     "Activity / Result": "Quantity (MT) of fish produced by young women PWDs accessing D&F in aquaculture value chain",
     "Relevant Anchor Partner(s)": "Same PWD-in-D&F cohort as PII.R5 — Naple Betta",
     "Q1": 1, "Q2": 2, "Q3": 2, "Q4": 3, "Year 1 Total": 9},
    {"Level": "L3", "CEL Metric": "PII.R7 Revenue, PWDs in D&F", "Value": "$16,667",
     "Workplan ID": "II.R7",
     "Activity / Result": "Revenue generated by young women PWDs accessing D&F in aquaculture value chain",
     "Relevant Anchor Partner(s)": "Same PWD-in-D&F cohort as PII.R5 — Naple Betta",
     "Q1": "$2,083", "Q2": "$4,167", "Q3": "$4,167", "Q4": "$6,250", "Year 1 Total": "$16,667"},
    {"Level": "L3", "CEL Metric": "PIII.R2 Fish produced/traded", "Value": "115.74 MT",
     "Workplan ID": "III.R2",
     "Activity / Result": "Quantity (MT) of fish produced or fish-related products traded",
     "Relevant Anchor Partner(s)": "TechnoServe (1,298+ MT traded) · Naple Betta (110 MT value-added trade)",
     "Q1": "", "Q2": 46.3, "Q3": 34.7, "Q4": 34.7, "Year 1 Total": 115.7},
    {"Level": "L3", "CEL Metric": "PIII.R3 Revenue, value-added trading", "Value": "$208,333",
     "Workplan ID": "III.R3",
     "Activity / Result": "Revenue generated from trading in Value Added Aquaculture products",
     "Relevant Anchor Partner(s)": "TechnoServe ($845,000 from catfish sales) · Naple Betta ($841,500 value-added revenue)",
     "Q1": "", "Q2": "$83,333", "Q3": "$62,500", "Q4": "$62,500", "Year 1 Total": "$208,333"},
])

# ── Year 1 Quarterly Delivery Calendar ───────────────────────────────────────
st.subheader("Year 1 Quarterly Delivery Calendar")
st.caption(
    "CEL and partner activities by quarter, Jul 2026 – Jun 2027.  "
    "Source: CEL's contribution to SAWA (Sep 2026) + partner Year 1 implementation decks + "
    "Draft CEL SAWA BDS Implementation Concept Note (28 Sep 2026) + "
    "Draft CEL SAWA WAN Concept Note and Initial Actions (28 Sep 2026)."
)

_QUARTERS = [
    {
        "cel_bds": (
            "No BDS delivery yet — the BDS concept note's process runs Oct–Dec: "
            "partner information request, needs assessment and first implementation "
            "actions all begin 1 October. CEL monitors partner Wave 1 mobilisation "
            "(AgroKings, Aglow, AFRIGEM, Naple Betta) for entry points ahead of the "
            "Q2 rollout."
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
            "Partner information request & needs assessment (1–30 Oct), prioritising "
            "Aglow's ToT and AgroKings' stocking; co-create BDS modules with AFRIGEM, "
            "Aglow and AgroKings trainers; Training of Trainers (ToT); start coaching "
            "and thematic workshops — Regulatory Day w/ FC, Financial Literacy, "
            "Finance Readiness w/ TechnoServe."
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

_Q_MONTH_SETS = [
    {(7, 2026), (8, 2026), (9, 2026)},
    {(10, 2026), (11, 2026), (12, 2026)},
    {(1, 2027), (2, 2027), (3, 2027)},
    {(4, 2027), (5, 2027), (6, 2027)},
]

_wp_all = run_query(
    "SELECT wa.id, wa.quarter, wa.activity, wa.deliverable, wa.due_date, "
    "wa.responsible, wa.status, wa.notes, "
    "COALESCE(p.name, wa.responsible) AS partner_display "
    "FROM workplan_activities wa "
    "LEFT JOIN partners p ON p.partner_id = wa.partner_id "
    "WHERE wa.project_id = :pid AND wa.fiscal_year = 2026 "
    "ORDER BY wa.quarter, COALESCE(p.name, wa.responsible), wa.due_date",
    {"pid": project_id},
)

_WP_STATUS_OPTIONS = ["Not Started", "In Progress", "Complete", "Delayed"]
_WP_STATUS_COLORS  = {
    "Not Started": ("#F3F4F6", "#374151"),
    "In Progress": ("#DBEAFE", "#1E40AF"),
    "Complete":    ("#D1FAE5", "#065F46"),
    "Delayed":     ("#FEE2E2", "#991B1B"),
}


def _save_wp(row_id: int) -> None:
    key = f"wp_{row_id}"
    new_status = st.session_state.get(key)
    if new_status:
        run_write(
            "UPDATE workplan_activities SET status = :s WHERE id = :id",
            {"s": new_status, "id": row_id},
        )


_dcp_rows = run_query(
    "SELECT stakeholder, indicator_statement, frequency, collection_month, "
    "collection_year, responsible_party, last_collected_date "
    "FROM data_collection_plan WHERE project_id = :pid "
    "ORDER BY collection_year, collection_month",
    {"pid": project_id},
)


def _bold(text: str) -> str:
    return _re_md.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def _card(label: str, text: str, color: str) -> str:
    return (
        f'<div style="background:#FFFFFF;border:1px solid #DED7C6;border-radius:10px;'
        f'overflow:hidden;box-shadow:0 2px 6px rgba(20,30,28,.09);margin-bottom:2px;">'
        f'<div style="background:{color};padding:6px 14px;">'
        f'<p style="margin:0;color:rgba(255,255,255,.95);font-family:\'IBM Plex Mono\','
        f'monospace;font-weight:700;letter-spacing:.05em;font-size:0.72em;">{label}</p>'
        f'</div>'
        f'<div style="padding:11px 15px;font-size:0.84em;color:#16262E;line-height:1.55;">'
        f'{_bold(text)}'
        f'</div></div>'
    )


def _dcp_in_q(row: dict, q_set: set) -> bool:
    freq = row.get("frequency") or "Once"
    cm, cy = row.get("collection_month"), row.get("collection_year")
    if not cm or not cy:
        return False
    if freq == "Quarterly":
        return True
    if (cm, cy) in q_set:
        return True
    if freq == "Bi-annual":
        m2, y2 = cm + 6, cy
        if m2 > 12:
            m2 -= 12
            y2 += 1
        if (m2, y2) in q_set:
            return True
    return False


def _dcp_section(q_set: set) -> str:
    active = [r for r in _dcp_rows if _dcp_in_q(r, q_set)]
    if not active:
        return ""
    rows_html = ""
    for i, r in enumerate(active):
        collected = r.get("last_collected_date")
        dot   = "#1E7E76" if collected else "#D97706"
        badge_bg = "#E6F4F1" if collected else "#FEF3CD"
        badge_fg = "#0D6B60" if collected else "#92400E"
        status = f"Collected {collected}" if collected else f"Due — {r.get('frequency','')}"
        short = (r.get("indicator_statement") or "")[:68]
        if len(r.get("indicator_statement") or "") > 68:
            short += "…"
        border = "" if i == len(active) - 1 else "border-bottom:1px solid #F0EDE6;"
        rows_html += (
            f'<div style="display:flex;align-items:flex-start;gap:10px;'
            f'padding:6px 2px;{border}">'
            f'<span style="flex-shrink:0;width:7px;height:7px;border-radius:50%;'
            f'background:{dot};margin-top:4px;"></span>'
            f'<div style="flex:1;min-width:0;">'
            f'<span style="font-weight:600;font-size:0.80em;color:#16262E;">'
            f'{r.get("stakeholder","")}</span>'
            f'<span style="font-size:0.77em;color:#5E6A6A;"> · {short}</span>'
            f'</div>'
            f'<span style="flex-shrink:0;font-size:0.74em;color:#5E6A6A;'
            f'white-space:nowrap;padding-right:8px;">{r.get("responsible_party","")}</span>'
            f'<span style="flex-shrink:0;font-size:0.72em;padding:2px 9px;border-radius:10px;'
            f'background:{badge_bg};color:{badge_fg};white-space:nowrap;">{status}</span>'
            f'</div>'
        )
    return (
        '<div style="margin-top:14px;border:1px solid #DED7C6;border-radius:8px;overflow:hidden;">'
        '<div style="background:#F6F3EC;padding:5px 14px;border-bottom:1px solid #DED7C6;">'
        '<p style="margin:0;font-size:0.70em;font-weight:700;letter-spacing:.07em;color:#1E7E76;'
        'font-family:\'IBM Plex Mono\',monospace;">DATA COLLECTION DUE THIS QUARTER</p>'
        '</div>'
        f'<div style="padding:6px 14px 4px;">{rows_html}</div>'
        '</div>'
    )


_Q_COLORS = {
    "cel_bds":     "#1E7E76",
    "cel_wan":     "#1E7E76",
    "agrokings":   "#1565C0",
    "aglow":       "#2E7D32",
    "afrigem":     "#6A1B9A",
    "naple_betta": "#00838F",
    "newage":      "#BF360C",
    "technoserve": "#37474F",
    "fc_csir":     "#263238",
}

_q_tabs = st.tabs(["Q1 Jul–Sep 2026", "Q2 Oct–Dec 2026", "Q3 Jan–Mar 2027", "Q4 Apr–Jun 2027"])
for _tab, _qd, _qms in zip(_q_tabs, _QUARTERS, _Q_MONTH_SETS):
    with _tab:
        _gap = '<div style="height:10px"></div>'
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(_card("CEL — BDS DELIVERY", _qd["cel_bds"], _Q_COLORS["cel_bds"]),
                        unsafe_allow_html=True)
        with c2:
            st.markdown(_card("CEL — WAN & PARTNER ENGAGEMENT", _qd["cel_wan"], _Q_COLORS["cel_wan"]),
                        unsafe_allow_html=True)
        st.markdown(_gap, unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(_card("AGROKINGS", _qd["agrokings"], _Q_COLORS["agrokings"]),
                        unsafe_allow_html=True)
        with c4:
            st.markdown(_card("AGLOW FARMS", _qd["aglow"], _Q_COLORS["aglow"]),
                        unsafe_allow_html=True)
        st.markdown(_gap, unsafe_allow_html=True)
        c5, c6, c7 = st.columns(3)
        with c5:
            st.markdown(_card("AFRIGEM", _qd["afrigem"], _Q_COLORS["afrigem"]),
                        unsafe_allow_html=True)
        with c6:
            st.markdown(_card("NAPLE BETTA", _qd["naple_betta"], _Q_COLORS["naple_betta"]),
                        unsafe_allow_html=True)
        with c7:
            st.markdown(_card("NEWAGE AGRIC", _qd["newage"], _Q_COLORS["newage"]),
                        unsafe_allow_html=True)
        st.markdown(_gap, unsafe_allow_html=True)
        c8, c9 = st.columns(2)
        with c8:
            st.markdown(_card("TECHNOSERVE", _qd["technoserve"], _Q_COLORS["technoserve"]),
                        unsafe_allow_html=True)
        with c9:
            st.markdown(_card("FC & CSIR", _qd["fc_csir"], _Q_COLORS["fc_csir"]),
                        unsafe_allow_html=True)
        _dcp_html = _dcp_section(_qms)
        if _dcp_html:
            st.markdown(_dcp_html, unsafe_allow_html=True)

        # ── Workplan activities ──────────────────────────────────────────────
        _q_num = _Q_MONTH_SETS.index(_qms) + 1
        _q_wp = [r for r in _wp_all if r["quarter"] == _q_num]
        if _q_wp:
            _done = sum(1 for r in _q_wp if r["status"] == "Complete")
            _delayed = sum(1 for r in _q_wp if r["status"] == "Delayed")
            _badge_bg = "#D1FAE5" if _done == len(_q_wp) else ("#FEE2E2" if _delayed else "#F3F4F6")
            _badge_fg = "#065F46" if _done == len(_q_wp) else ("#991B1B" if _delayed else "#374151")
            st.markdown(
                f'<div style="margin-top:14px;border:1px solid #DED7C6;border-radius:8px;overflow:hidden;">'
                f'<div style="background:#F6F3EC;padding:5px 14px 5px 14px;border-bottom:1px solid #DED7C6;'
                f'display:flex;align-items:center;justify-content:space-between;">'
                f'<p style="margin:0;font-size:0.70em;font-weight:700;letter-spacing:.07em;color:#16262E;'
                f'font-family:\'IBM Plex Mono\',monospace;">WORKPLAN ACTIVITIES</p>'
                f'<span style="font-size:0.71em;padding:2px 10px;border-radius:10px;'
                f'background:{_badge_bg};color:{_badge_fg};">{_done}/{len(_q_wp)} complete</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            _by_partner: dict = {}
            for _wr in _q_wp:
                _by_partner.setdefault(_wr["partner_display"], []).append(_wr)
            for _pname, _prows in _by_partner.items():
                st.markdown(
                    f'<p style="margin:6px 0 2px 2px;font-size:0.74em;font-weight:700;'
                    f'letter-spacing:.05em;color:#5E6A6A;">{_pname.upper()}</p>',
                    unsafe_allow_html=True,
                )
                for _wr in _prows:
                    _s = _wr["status"] or "Not Started"
                    _sbg, _sfg = _WP_STATUS_COLORS.get(_s, ("#F3F4F6", "#374151"))
                    _ca, _cd, _cs = st.columns([5, 1.2, 1.6])
                    with _ca:
                        _deliv = _wr.get("deliverable") or ""
                        st.markdown(
                            f'<p style="margin:0;font-size:0.82em;color:#16262E;">{_wr["activity"]}</p>'
                            + (f'<p style="margin:0;font-size:0.74em;color:#5E6A6A;">{_deliv}</p>' if _deliv else ""),
                            unsafe_allow_html=True,
                        )
                    with _cd:
                        _due = _wr.get("due_date") or ""
                        st.markdown(
                            f'<p style="margin:4px 0 0 0;font-size:0.74em;color:#5E6A6A;'
                            f'white-space:nowrap;">{_due[5:] if _due else ""}</p>',
                            unsafe_allow_html=True,
                        )
                    with _cs:
                        st.selectbox(
                            "status",
                            _WP_STATUS_OPTIONS,
                            index=_WP_STATUS_OPTIONS.index(_s) if _s in _WP_STATUS_OPTIONS else 0,
                            key=f"wp_{_wr['id']}",
                            on_change=_save_wp,
                            args=(_wr["id"],),
                            label_visibility="collapsed",
                        )
                st.markdown('<div style="height:2px"></div>', unsafe_allow_html=True)

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


# ── Excel export ──────────────────────────────────────────────────────────────
def _build_excel() -> bytes:
    """One workbook, one sheet per table already built above — reuses the
    same in-memory DataFrames the page renders from, so the export can never
    drift from what's on screen."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        level_sheet_names = {
            1: "L1 Anchor Commitments",
            2: "L2 CEL Delivery",
            3: "L3 Year1 Results",
            4: "L4 Programme Impact",
        }
        for lvl, sheet_name in level_sheet_names.items():
            recs = []
            for row in by_level[lvl]:
                rec: dict = {"Partner": row["partner_name"]} if lvl == 1 else {}
                rec.update({
                    "Metric":       row["metric_label"],
                    "Target Value": row["target_value"],
                    "Unit":         row["unit"],
                    "Time Basis":   row["time_basis"],
                    "Source":       row["source_doc"],
                })
                recs.append(rec)
            (pd.DataFrame(recs) if recs else pd.DataFrame()).to_excel(
                writer, sheet_name=sheet_name, index=False
            )

        _cel_measures.to_excel(writer, sheet_name="CEL Measures x Partners", index=False)
        _contribution_map.to_excel(writer, sheet_name="Partner to Impact Map", index=False)
        _workplan_xref.to_excel(writer, sheet_name="Consolidated Workplan XRef", index=False)

        total_b = sum(PILLAR_BUDGETS.values())
        budget_rows = [
            {"Pillar": k, "USD": v, "% of Total": round(100 * v / total_b, 1)}
            for k, v in PILLAR_BUDGETS.items()
        ]
        budget_rows.append({"Pillar": "TOTAL", "USD": total_b, "% of Total": 100.0})
        pd.DataFrame(budget_rows).to_excel(writer, sheet_name="Budget by Pillar", index=False)

    return buf.getvalue()


col_exp, col_pdf, col_xlsx = st.columns([3, 1, 1])
with col_pdf:
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
with col_xlsx:
    if st.button("📊 Export Excel", use_container_width=True):
        with st.spinner("Building workbook…"):
            xlsx_bytes = _build_excel()
            st.download_button(
                "⬇ Download Excel",
                data=xlsx_bytes,
                file_name="sawa_partner_alignment.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

st.divider()

# ── A2: Year 1 Target Consistency Check ──────────────────────────────────────
with st.expander("Year 1 Target Consistency Check", expanded=False):
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

# ── A3: SAWA Year 1 Consolidated Workplan cross-reference ────────────────────
with st.expander("SAWA Year 1 Consolidated Workplan — source cross-reference", expanded=False):
    st.caption(
        "Every Level 2 and Level 3 figure above traced back to its exact "
        "Pillar-coded line item and quarterly phasing in the SAWA Programme "
        "Year 1 Consolidated Workplan — the source document Module A's "
        "narrative labels summarise.  Source: SAWA Programme — Year 1 "
        "Consolidated Workplan."
    )
    st.dataframe(
        _workplan_xref,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Level":              st.column_config.TextColumn("Level", width="small"),
            "CEL Metric":         st.column_config.TextColumn("CEL Metric (Module A)", width="medium"),
            "Value":              st.column_config.TextColumn("Value", width="small"),
            "Workplan ID":        st.column_config.TextColumn("Workplan ID", width="small"),
            "Activity / Result":  st.column_config.TextColumn("Activity / Result", width="large"),
            "Relevant Anchor Partner(s)": st.column_config.TextColumn("Relevant Anchor Partner(s)", width="large"),
            "Q1": st.column_config.TextColumn("Q1", width="small"),
            "Q2": st.column_config.TextColumn("Q2", width="small"),
            "Q3": st.column_config.TextColumn("Q3", width="small"),
            "Q4": st.column_config.TextColumn("Q4", width="small"),
            "Year 1 Total":       st.column_config.TextColumn("Year 1 Total", width="small"),
        },
    )
    st.caption(
        "Two rows share a Workplan ID pair (I.18 / III.6) — the Consolidated "
        "Workplan reports the same 25 cooperatives/clusters target under both "
        "Pillar I and Pillar III; this is the source document's own structure, "
        "not a duplicate entered in error."
    )

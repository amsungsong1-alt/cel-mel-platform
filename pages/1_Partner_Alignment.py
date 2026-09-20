"""Module A — Partner Alignment

Four-level funnel view of the SAWA commitment chain:
  Level 1 — Anchor Partner Commitments (Life of Programme)
  Level 2 — CEL Year 1 Delivery
  Level 3 — Year 1 Results
  Level 4 — Programme Impact

Includes a time-basis reconciliation warning, inline editing for
Admin/Editor roles, and a one-page PDF export for donor decks.
"""
import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from database.db import init_db, run_query, run_write
from utils.shared_widgets import project_selector
from utils.auth import can, can_write_module, ensure_auth
from projects.sawa import PILLAR_BUDGETS
from utils.nav_strip import render_nav_strip

st.set_page_config(page_title="Partner Alignment — CEL MEL", layout="wide")
init_db()
render_nav_strip("Input")

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not ensure_auth():
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
l23_yr1 = any(t["time_basis"] == "Year 1" for t in by_level[2] + by_level[3])

if l1_lop and l23_yr1:
    st.warning(
        "⚠️ **Time-Basis Mismatch — do not sum these numbers together.**  \n"
        "**Level 1** (Anchor Partner) commitments are *Life of Programme* totals "
        "(2026–2030).  \n"
        "**Levels 2 & 3** targets are *Year 1 only* (CEL Consolidated Workplan).  \n"
        "These figures operate on different time horizons. Never aggregate them or "
        "use them as numerator/denominator in the same ratio without first converting "
        "both to the same basis (e.g. a pro-rata Year 1 share of the LoP total)."
    )

# ── Funnel header ─────────────────────────────────────────────────────────────
st.title("Module A — Partner Alignment")
st.caption(
    "Commitment chain from anchor partners → CEL delivery → Year 1 results → "
    "programme impact.  Source documents shown on hover."
)

editable = can_write_module("A")

# ── Band configuration ────────────────────────────────────────────────────────
BANDS = {
    1: {
        "title":  "Level 1 — Anchor Partner Commitments",
        "sub":    "Life of Programme · Source: SAWA Proposal, 28 Nov 2025",
        "color":  "#00838F",   # teal
        "bg":     "#E0F7FA",
    },
    2: {
        "title":  "Level 2 — CEL Year 1 Delivery",
        "sub":    "Year 1 · Source: CEL Year 1 Consolidated Workplan",
        "color":  "#6A1B9A",   # purple
        "bg":     "#F3E5F5",
    },
    3: {
        "title":  "Level 3 — Year 1 Results",
        "sub":    "Year 1 indicator targets · Source: CEL Year 1 Consolidated Workplan",
        "color":  "#BF360C",   # coral
        "bg":     "#FBE9E7",
    },
    4: {
        "title":  "Level 4 — Programme Impact",
        "sub":    "Life of Programme (2026–2030) · Source: SAWA Proposal, 28 Nov 2025",
        "color":  "#E65100",   # gold/amber
        "bg":     "#FFF8E1",
    },
}

PILLAR_COLORS = ["#0288D1", "#2E7D32", "#E65100", "#6A1B9A", "#455A64"]


def _card_html(label: str, value: str, unit: str, color: str, bg: str,
               source_doc: str) -> str:
    tooltip = f"Source: {source_doc}" if source_doc else ""
    return f"""
    <div title="{tooltip}" style="
        background:{bg}; border-left:4px solid {color};
        border-radius:6px; padding:10px 14px; margin-bottom:6px;
        min-height:82px;">
      <p style="margin:0 0 4px 0; font-size:0.72em; color:#555; line-height:1.3;">{label}</p>
      <p style="margin:0 0 2px 0; font-size:1.3em; font-weight:700; color:{color};">{value}</p>
      <p style="margin:0; font-size:0.68em; color:#777;">{unit}</p>
    </div>"""


# ── Render each level band ────────────────────────────────────────────────────
for lvl in (1, 2, 3, 4):
    band  = BANDS[lvl]
    rows  = by_level[lvl]
    color = band["color"]
    bg    = band["bg"]

    # Band header
    st.markdown(
        f"""<div style="background:{bg}; border-left:6px solid {color};
                        padding:10px 18px; border-radius:5px; margin:18px 0 10px 0;">
            <span style="font-size:1.05em; font-weight:700; color:{color};">{band['title']}</span><br>
            <span style="font-size:0.75em; color:#666;">{band['sub']}</span>
            </div>""",
        unsafe_allow_html=True,
    )

    if not rows:
        st.caption("No data — run `python -m database.seed_sawa` to load SAWA data.")
        continue

    # Metric cards (read-only for all roles)
    n = min(len(rows), 5)
    cols = st.columns(n)
    for i, row in enumerate(rows):
        label = (
            f"**{row['partner_name']}**<br>{row['metric_label']}"
            if row["partner_name"] != "Programme"
            else row["metric_label"]
        )
        with cols[i % n]:
            st.markdown(
                _card_html(
                    label.replace("**", "").replace("<br>", " — "),
                    row["target_value"],
                    row["unit"],
                    color,
                    bg,
                    row["source_doc"],
                ),
                unsafe_allow_html=True,
            )

    # Inline editor (Admin / Editor only)
    if editable:
        with st.expander(f"✏️ Edit Level {lvl} targets", expanded=False):
            df_edit = pd.DataFrame([
                {
                    "id":           row["id"],
                    "Metric":       row["metric_label"],
                    "Target Value": row["target_value"],
                    "Unit":         row["unit"],
                    "Time Basis":   row["time_basis"],
                    "Source Doc":   row["source_doc"],
                }
                for row in rows
            ])
            edited = st.data_editor(
                df_edit,
                key=f"editor_{lvl}",
                disabled=["id", "Metric", "Unit", "Time Basis", "Source Doc"],
                hide_index=True,
                use_container_width=True,
            )
            if st.button(f"💾 Save Level {lvl}", key=f"save_{lvl}"):
                for _, r in edited.iterrows():
                    run_write(
                        "UPDATE partner_targets SET target_value=:v WHERE id=:id",
                        {"v": str(r["Target Value"]), "id": int(r["id"])},
                    )
                st.success("Saved.")
                st.rerun()

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
    title=dict(text=f"SAWA Programme Budget — USD {total_m:.2f}M total", font_size=14),
    height=155,
    margin=dict(l=0, r=0, t=40, b=10),
    xaxis=dict(title="USD Million", showgrid=True, gridcolor="#eee"),
    yaxis=dict(showticklabels=False),
    legend=dict(orientation="h", y=-0.55, x=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(size=11),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── CEL's Role in SAWA ────────────────────────────────────────────────────────
st.subheader("CEL's Delivery Role in SAWA")
st.caption("Source: CEL SAWA proposal (Value Chain Pathway & Job Roles slide, July 2026)")

rc1, rc2, rc3 = st.columns(3)
with rc1:
    st.markdown(
        '<div style="background:#E8F5E9;border-left:4px solid #2E7D32;'
        'border-radius:6px;padding:12px 16px;">'
        '<p style="margin:0 0 6px 0;font-weight:bold;color:#2E7D32;">Jobs Target</p>'
        '<p style="margin:0;font-size:1.3em;font-weight:700;color:#1B5E20;">600 D&amp;F</p>'
        '<p style="margin:0;font-size:0.78em;color:#555;">Displaced &amp; Female participants</p>'
        '<p style="margin:8px 0 0 0;font-size:1.3em;font-weight:700;color:#1B5E20;">800 YiW</p>'
        '<p style="margin:0;font-size:0.78em;color:#555;">Youth in Work</p>'
        '</div>',
        unsafe_allow_html=True,
    )
with rc2:
    st.markdown(
        '<div style="background:#FFF8E1;border-left:4px solid #E65100;'
        'border-radius:6px;padding:12px 16px;">'
        '<p style="margin:0 0 6px 0;font-weight:bold;color:#E65100;">CEL Delivers</p>'
        '<ul style="margin:0;padding-left:16px;font-size:0.82em;color:#444;">'
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
        '<div style="background:#E3F2FD;border-left:4px solid #1565C0;'
        'border-radius:6px;padding:12px 16px;">'
        '<p style="margin:0 0 6px 0;font-weight:bold;color:#1565C0;">National Mandate</p>'
        '<ul style="margin:0;padding-left:16px;font-size:0.82em;color:#444;">'
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

# ── Partner Roles & Expectations ─────────────────────────────────────────────
st.subheader("Partner Roles & Expectations")
st.caption("Source: SAWA Partner Roles & Expectations slide — defines the mutual accountability framework.")

pe1, pe2 = st.columns(2)
with pe1:
    st.markdown(
        '<div style="background:#E8F5E9;border:1px solid #A5D6A7;border-radius:6px;overflow:hidden;">'
        '<div style="background:#BF360C;padding:8px 14px;">'
        '<p style="margin:0;color:white;font-weight:bold;font-size:0.9em;">WHAT SAWA / AGRI-IMPACT PROVIDES</p>'
        '</div>'
        '<div style="padding:12px 16px;">'
        '<ul style="margin:0;padding-left:16px;font-size:0.84em;color:#222;">'
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
        '<div style="background:#E3F2FD;border:1px solid #90CAF9;border-radius:6px;overflow:hidden;">'
        '<div style="background:#BF360C;padding:8px 14px;">'
        '<p style="margin:0;color:white;font-weight:bold;font-size:0.9em;">WHAT IMPLEMENTING PARTNERS COMMIT TO</p>'
        '</div>'
        '<div style="padding:12px 16px;">'
        '<ul style="margin:0;padding-left:16px;font-size:0.84em;color:#222;">'
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

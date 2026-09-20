"""CEL MEL Platform — landing page with auth gate.

All seven module pages share session state set here:
  st.session_state.authentication_status  – bool
  st.session_state.name                   – display name
  st.session_state.username               – credential key
  st.session_state.role                   – 'Admin'|'Editor'|'Viewer'
  st.session_state.project_id             – set by project_selector() in each page

MIS Framework (Laudon & Laudon, 16e)
-------------------------------------
This platform is a management information system: it collects raw data (Modules
C & D), processes it into meaningful indicators (Module E), stores and
distributes reviewed findings (Module F), and outputs decision-ready reports
(Module G) — completing the Input → Processing → Output → Feedback cycle.

It addresses three of Laudon's six strategic business objectives:
  • Operational Excellence    — Modules C, D, E  (streamlined data pipelines)
  • Improved Decision Making  — Modules F, G     (quality-assured evidence)
  • Customer/Supplier Intimacy— Module A         (partner commitments & delivery)
"""
import streamlit as st
from database.db import init_db, run_query, run_write
from utils.nav_strip import render_nav_strip

st.set_page_config(
    page_title="CEL MEL Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()
render_nav_strip()  # home page — no active stage

# ── Auto-seed on first run or when indicator IDs are stale ────────────────────
_needs_seed = (
    not run_query("SELECT 1 FROM projects LIMIT 1", {})
    or run_query(
        "SELECT 1 FROM logframe_rows WHERE indicator_code IN ('PI.2','PI.3','PI.4') LIMIT 1",
        {},
    )
)
if _needs_seed:
    try:
        from database.seed_sawa import seed as _seed
        _seed()
        from database.seed_sample_data import seed as _seed_sample
        _seed_sample()
    except Exception as _e:
        st.warning(f"Auto-seed skipped: {_e}")

# ── Brand ─────────────────────────────────────────────────────────────────────
NAVY = "#0D2B5E"
GOLD = "#C8A951"

# ── Auth ──────────────────────────────────────────────────────────────────────
from utils.auth import get_authenticator, can

try:
    authenticator, config = get_authenticator()
    authenticator.login()
except FileNotFoundError:
    st.error(
        "**credentials.yaml not found.** "
        "Copy `database/credentials.yaml.example` → `database/credentials.yaml` "
        "and fill in bcrypt-hashed passwords, then restart the app."
    )
    st.stop()
except Exception as exc:
    st.error(f"Auth error: {exc}")
    st.stop()

auth_status = st.session_state.get("authentication_status")

if auth_status is False:
    st.error("Incorrect username or password.")
    st.stop()

if not auth_status:
    st.info("Enter your credentials in the login form above.")
    st.stop()

# ── Post-login: attach role to session state ──────────────────────────────────
username = st.session_state.get("username", "")
creds = config.get("credentials", {}).get("usernames", {})
user_record = creds.get(username, {})
st.session_state["role"] = user_record.get("role", "Viewer")
st.session_state["write_modules"] = user_record.get("write_modules", None)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    authenticator.logout("Logout")
    st.caption(f"Signed in as **{st.session_state.get('name')}** ({st.session_state['role']})")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="background:{NAVY};color:white;padding:18px 24px;'
    f'border-left:6px solid {GOLD};border-radius:4px;margin-bottom:6px;">'
    '<span style="font-size:1.5em;font-weight:bold;">📊 CEL MEL Platform</span>'
    f'<span style="color:{GOLD};font-size:0.9em;margin-left:12px;">'
    'Community &amp; Enterprise-Level Monitoring, Evaluation &amp; Learning</span><br>'
    '<span style="font-size:0.78em;opacity:0.7;margin-top:4px;display:block;">'
    'SAWA Programme · Fisheries &amp; Aquaculture Development · Ghana · Funded by Mastercard Foundation</span>'
    '</div>',
    unsafe_allow_html=True,
)

# ── MEL Information System Cycle ──────────────────────────────────────────────
st.markdown("#### MEL Information System Cycle")
st.caption(
    "Based on Laudon & Laudon (2020) Figure 1.4 — an information system "
    "collects data (Input), converts it into meaningful findings (Processing), "
    "distributes them (Output), and channels results back to improve collection (Feedback). "
    "Module H closes the cycle by automatically assembling all outputs into a shareable impact story."
)

cols = st.columns([2, 1, 2, 1, 2, 1, 2, 1, 2])
cycle_steps = [
    ("📥 INPUT", "Collect", "Modules C & D", "#E3F2FD", "#1565C0"),
    ("→", "", "", "white", NAVY),
    ("⚙️ PROCESS", "Analyse", "Module E", "#FFF8E1", "#E65100"),
    ("→", "", "", "white", NAVY),
    ("🔍 REVIEW", "Quality-check", "Module F", "#F3E5F5", "#6A1B9A"),
    ("→", "", "", "white", NAVY),
    ("📋 DECIDE", "Act & Report", "Module G", "#E8F5E9", "#2E7D32"),
    ("→", "", "", "white", NAVY),
    ("🌟 IMPACT", "Tell the Story", "Module H", f"#C8A95120", GOLD),
]
for col, (icon, label, sub, bg, fg) in zip(cols, cycle_steps):
    if icon in ("→", "↩"):
        col.markdown(
            f'<div style="text-align:center;font-size:1.6em;color:{NAVY};'
            f'padding-top:18px;">{icon}</div>',
            unsafe_allow_html=True,
        )
    else:
        col.markdown(
            f'<div style="background:{bg};border:1px solid {fg}40;border-radius:6px;'
            f'padding:10px 8px;text-align:center;">'
            f'<div style="font-size:1.1em;">{icon}</div>'
            f'<div style="font-weight:bold;color:{fg};font-size:0.82em;">{label}</div>'
            f'<div style="font-size:0.72em;color:#555;">{sub}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

st.markdown(
    f'<div style="text-align:center;font-size:0.78em;color:#555;margin-top:6px;">'
    f'<span style="color:{GOLD};font-weight:bold;">↩ Feedback loop</span> — '
    'Impact findings from Module H inform the next data collection cycle '
    '(back to Modules C &amp; E), closing the IS cycle as described in '
    'Laudon &amp; Laudon Figure 1.4.'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# ── Module Table by Management Level ─────────────────────────────────────────
st.markdown("#### Platform Modules by Management Level")
st.caption(
    "Structured around Laudon & Laudon Figure 1.6 — Senior, Middle, and "
    "Operational management each need different information from the system."
)

MODULES = [
    # (level, badge_colour, module, page_name, is_objective, users, nav_hint)
    ("Senior Management", "#1565C0", "H", "Impact Dashboard",
     "Improved Decision Making",
     "Programme Director, Donors, Mastercard Foundation",
     "Auto-captured impact story: KPIs, results chain, partner funnel, key findings"),
    ("Senior Management", "#1565C0", "A", "Partner Alignment",
     "Customer & Supplier Intimacy",
     "Programme Director, Donors",
     "Four-level funnel: commitments → delivery → results → impact"),
    ("Senior Management", "#1565C0", "G", "Decision Reports",
     "Improved Decision Making",
     "Programme Director, Donors, Senior Advisor",
     "Auto-generated evidence reports with action tracking"),
    ("Middle Management", "#6A1B9A", "B", "ToC & Logframe",
     "Competitive Advantage",
     "MEAL Officer, Programme Manager",
     "Theory of Change node tree and indicator logframe"),
    ("Middle Management", "#6A1B9A", "D", "Raw Data Analysis",
     "Operational Excellence",
     "MEAL Officer",
     "Upload and analyse indicator data per quarter"),
    ("Middle Management", "#6A1B9A", "F", "Data Review",
     "Improved Decision Making",
     "MEAL Officer, Senior Advisor",
     "Quality-check and schedule structured data reviews"),
    ("Operational Management", "#2E7D32", "C", "Data Collection Plan",
     "Operational Excellence",
     "Data Officers, Field Staff",
     "Planned vs. actual data collection schedule"),
    ("Operational Management", "#2E7D32", "E", "Kobo Data Sync",
     "Operational Excellence",
     "Data Officers",
     "Pull live data automatically from KoboToolbox forms"),
]

current_level = None
for level, colour, mod, page, objective, users, description in MODULES:
    if level != current_level:
        current_level = level
        st.markdown(
            f'<div style="background:{colour}18;border-left:4px solid {colour};'
            f'padding:4px 12px;margin:16px 0 4px 0;font-weight:bold;color:{colour};">'
            f'{level}</div>',
            unsafe_allow_html=True,
        )
    c1, c2, c3, c4 = st.columns([0.7, 2, 2.5, 3.5])
    c1.markdown(
        f'<div style="background:{NAVY};color:{GOLD};border-radius:4px;'
        f'text-align:center;font-weight:bold;padding:6px 4px;font-size:1em;">'
        f'{mod}</div>',
        unsafe_allow_html=True,
    )
    c2.markdown(f"**{page}**")
    c3.markdown(f"<span style='font-size:0.82em;color:#555;'>🎯 {objective}</span>", unsafe_allow_html=True)
    c4.markdown(f"<span style='font-size:0.8em;'>{description}</span><br><span style='font-size:0.74em;color:#888;'>👤 {users}</span>", unsafe_allow_html=True)

st.markdown("---")

# ── CEL Project Portfolio by Sector ──────────────────────────────────────────
st.markdown("#### CEL Project Portfolio")
st.caption("All programmes and projects grouped by CEL service sector. Admins can register upcoming projects.")

# Static portfolio sourced from CEL presentation slides (July 2026) + celghana.com
_CEL_PORTFOLIO = [
    # ── Aquaculture & Fisheries ───────────────────────────────────────────────
    {"sector": "🐟 Aquaculture & Fisheries",
     "name": "SAWA", "period": "2026–2030", "status": "Active",
     "donor": "Mastercard Foundation",
     "cel_role": "Implementing Partner — BDS, safeguarding focal point, WAN establishment",
     "description": "National aquaculture initiative for 80,000 young women, PWDs & displaced youth across Ghana (Catfish + Tilapia value chain)"},
    # ── Blue Economy ──────────────────────────────────────────────────────────
    {"sector": "🌊 Blue Economy & Marine Innovation",
     "name": "A3MAtlantic", "period": "Ongoing", "status": "Active",
     "donor": "EU / INTERREG MAC",
     "cel_role": "CEL representing Ghana",
     "description": "Strengthening SME competitiveness in the blue economy across the Mid-Atlantic"},
    {"sector": "🌊 Blue Economy & Marine Innovation",
     "name": "RED BEAM", "period": "Ongoing", "status": "Active",
     "donor": "EU",
     "cel_role": "CEL Local Partner in Ghana",
     "description": "Accelerating ocean tech innovation across Macaronesia and West Africa"},
    {"sector": "🌊 Blue Economy & Marine Innovation",
     "name": "Blue Supply Chain", "period": "Ongoing", "status": "Active",
     "donor": "EU",
     "cel_role": "CEL Local Partner",
     "description": "Strengthening regional value chains for offshore renewable energy in West Africa"},
    # ── Digital Innovation ────────────────────────────────────────────────────
    {"sector": "💻 Digital Innovation & Tech",
     "name": "INNOVAMOS", "period": "Ongoing", "status": "Active",
     "donor": "EU / INTERREG MAC",
     "cel_role": "CEL Lead Partner",
     "description": "Connecting researchers and businesses for innovation in agri-food, blue growth, and creative sectors"},
    {"sector": "💻 Digital Innovation & Tech",
     "name": "AFRICANTECH", "period": "Ongoing", "status": "Active",
     "donor": "EU",
     "cel_role": "CEL Local Partner (via Ghana Innovation Hub)",
     "description": "Strengthening SME competitiveness through digital innovation across West Africa and the Canary Islands"},
    # ── Circular Economy ──────────────────────────────────────────────────────
    {"sector": "♻️ Circular Economy & Green Business",
     "name": "OWTVI — Organic Waste-to-Value", "period": "2022–2026", "status": "Active",
     "donor": "GIZ / develoPPP / Invest for Jobs",
     "cel_role": "CEL Implementing Partner (with MDF) — Circular Economy Hub, Nsawam",
     "description": "Creation of 120 new jobs through organic waste-to-value chain in Nsawam District (Eastern Region)"},
    {"sector": "♻️ Circular Economy & Green Business",
     "name": "Greenovations Africa", "period": "Ongoing", "status": "Active",
     "donor": "AfriLabs / UNU",
     "cel_role": "CEL Lead Hub — Waste Management Track",
     "description": "Pan-African initiative empowering young entrepreneurs in green business development"},
    # ── Agribusiness ─────────────────────────────────────────────────────────
    {"sector": "🌾 Agribusiness & Value Chains",
     "name": "Cassava Transformation Project", "period": "2020–2026", "status": "Active",
     "donor": "—",
     "cel_role": "Implementation Partner",
     "description": "Enhance competitiveness and regional integration of Liberia's cassava sector through value chain approach"},
    {"sector": "🌾 Agribusiness & Value Chains",
     "name": "AGROPAL West Africa", "period": "Ongoing", "status": "Active",
     "donor": "Private / CERATH Development",
     "cel_role": "Technical Assistance Provider",
     "description": "Dried fruits processing and export company; CEL supports technical assistance, farmer productivity, and investment readiness"},
    # ── Enterprise Development ────────────────────────────────────────────────
    {"sector": "🏢 Enterprise Development & Incubation",
     "name": "Orange Corners Ghana", "period": "Ongoing", "status": "Active",
     "donor": "Netherlands Embassy / Orange Corners",
     "cel_role": "CEL Lead Implementer (Ghana Innovation Hub)",
     "description": "Youth entrepreneurship incubation with proof-of-concept funding (OCIF). Alumni: SETECH, Dercol Bags, Eazz Foods, Wash King, SAYeTech, Asili Coffee"},
]

# Group by sector
_sectors: dict[str, list] = {}
for _p in _CEL_PORTFOLIO:
    _sectors.setdefault(_p["sector"], []).append(_p)

_STATUS_COLOURS = {"Active": "#2E7D32", "Planned": "#1565C0", "Completed": "#555"}

for _sector, _projects in _sectors.items():
    with st.expander(_sector, expanded=False):
        for _proj in _projects:
            _sc = _STATUS_COLOURS.get(_proj["status"], "#555")
            st.markdown(
                f'<div style="border-left:4px solid {_sc};padding:8px 14px;'
                f'margin-bottom:8px;background:#fafafa;border-radius:4px;">'
                f'<span style="font-weight:bold;">{_proj["name"]}</span>'
                f'&nbsp;<span style="background:{_sc};color:white;padding:1px 7px;'
                f'border-radius:10px;font-size:0.72em;">{_proj["status"]}</span>'
                f'&nbsp;<span style="color:#888;font-size:0.78em;">{_proj["period"]} · {_proj["donor"]}</span><br>'
                f'<span style="font-size:0.82em;color:#444;">{_proj["description"]}</span><br>'
                f'<span style="font-size:0.76em;color:#555;"><em>CEL role:</em> {_proj["cel_role"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

# Admin expander: register a new / future project into the DB ─────────────────
if can("admin"):
    with st.expander("➕ Register a New / Future Project", expanded=False):
        with st.form("new_project_form"):
            np_name   = st.text_input("Project name *")
            np_donor  = st.text_input("Donor / funder")
            np_budget = st.number_input("Budget (USD)", min_value=0, step=10000)
            c1, c2 = st.columns(2)
            np_start  = c1.text_input("Start date (YYYY-MM-DD)")
            np_end    = c2.text_input("End date (YYYY-MM-DD)")
            submitted = st.form_submit_button("Register project")
            if submitted and np_name:
                try:
                    run_write(
                        """INSERT INTO projects (name, donor, budget_total, start_date, end_date)
                           VALUES (:name, :donor, :budget, :start, :end)""",
                        {"name": np_name, "donor": np_donor, "budget": int(np_budget),
                         "start": np_start or None, "end": np_end or None},
                    )
                    st.success(f"Project **{np_name}** registered. It now appears in the project selector.")
                    st.rerun()
                except Exception as _exc:
                    st.error(f"Insert failed: {_exc}")
            elif submitted:
                st.warning("Project name is required.")

st.markdown("---")

# ── Role-Based Quick Start ────────────────────────────────────────────────────
role = st.session_state.get("role", "Viewer")
quick_start_map = {
    "Admin": {
        "icon": "🔧",
        "colour": "#B71C1C",
        "start": "Module A",
        "tip": "Set up partner targets in Module A, seed logframe in Module B, configure Kobo mappings in Module D.",
        "daily": "Check Module F for overdue reviews · Monitor Module G for pending actions.",
    },
    "Editor": {
        "icon": "✏️",
        "colour": "#1565C0",
        "start": "Module E",
        "tip": "Enter quarterly actuals in Module E, then use Module F to log data reviews.",
        "daily": "Module E → enter actuals → Module F → log review → Module G → raise decision report.",
    },
    "Viewer": {
        "icon": "👁",
        "colour": "#2E7D32",
        "start": "Module H",
        "tip": "Impact Dashboard (Module H) gives the full programme picture instantly — KPIs, results chain, partner delivery and key findings in one view.",
        "daily": "Module H → impact snapshot · Module G → approved reports · Module A → partner alignment.",
    },
}
qs = quick_start_map.get(role, quick_start_map["Viewer"])

st.markdown(f"#### {qs['icon']} Quick Start for {role}s")
st.info(f"**Where to begin:** {qs['start']}  \n**Suggested workflow:** {qs['tip']}  \n**Daily check:** {qs['daily']}")

# ── MIS Framework Context (collapsible) ───────────────────────────────────────
with st.expander("📚 MIS Framework Context (Laudon & Laudon, 16e)", expanded=False):
    st.markdown(
        f'<div style="background:{NAVY};color:white;padding:10px 16px;'
        f'border-left:4px solid {GOLD};border-radius:4px;margin-bottom:12px;">'
        "This platform is a <strong>Management Information System (MIS)</strong> "
        "as defined by Laudon &amp; Laudon: <em>a set of interrelated components "
        "that collect (or retrieve), process, store, and distribute information "
        "to support decision making and control in an organisation.</em>"
        "</div>",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Management–Organisation–Technology (MOT) Dimensions**")
        st.markdown("""
| Dimension | SAWA Application |
|-----------|-----------------|
| **Management** | MEAL Officer designs review protocols (F); Programme Director approves decision reports (G) |
| **Organisation** | SAWA programme structure defines partner tiers (A) and result levels in the logframe (B) |
| **Technology** | KoboToolbox mobile data collection synced via API (E); SQLite database; Streamlit dashboards |
""")

    with col_b:
        st.markdown("**Six Strategic Business Objectives addressed**")
        objectives = [
            ("Operational Excellence", "Automated Kobo sync (E) and structured data analysis (D) reduce manual re-entry and error.", "✅"),
            ("New Products / Business Models", "The ToC (B) documents SAWA's theory for creating new market opportunities in Ghanaian fisheries.", "✅"),
            ("Customer & Supplier Intimacy", "Partner Alignment (A) tracks commitment and delivery across all implementing partners.", "✅"),
            ("Improved Decision Making", "Data Review (F) quality-assures evidence; Decision Reports (G) surface actions to decision-makers.", "✅"),
            ("Competitive Advantage", "Rigorous MEAL data positions SAWA for continued donor investment and scale.", "✅"),
            ("Survival", "Structured reporting in Module G ensures compliance with Mastercard Foundation reporting requirements.", "✅"),
        ]
        for obj, note, tick in objectives:
            st.markdown(f"{tick} **{obj}** — {note}")

    st.markdown("---")
    st.markdown("**Information System Cycle (Figure 1.4)**")
    st.markdown("""
```
     ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
     │   INPUT       │ →  │  PROCESSING  │ →  │   OUTPUT     │ →  │   FEEDBACK   │
     │ Kobo Sync (E) │    │ Analysis (D) │    │ Reports (G)  │    │ Review (F)   │
     │ DCP (C)       │    │ Review (F)   │    │ Alignment (A)│    │ → Improve    │
     └──────────────┘    └──────────────┘    └──────────────┘    │   collection │
              ↑                                                    └──────────────┘
              └────────────────── informs next data collection ──────────────────┘
```
_Source: Laudon & Laudon (2020). Management Information Systems, 16e. Ch. 1._
""")

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
C & E), processes it into meaningful indicators (Module D), stores and
distributes reviewed findings (Module F), and outputs decision-ready reports
(Module G) — completing the Input → Processing → Output → Feedback cycle.

It addresses three of Laudon's six strategic business objectives:
  • Operational Excellence    — Modules C, D, E  (streamlined data pipelines)
  • Improved Decision Making  — Modules F, G     (quality-assured evidence)
  • Customer/Supplier Intimacy— Module A         (partner commitments & delivery)
"""
import streamlit as st
from database.db import init_db, run_query

st.set_page_config(
    page_title="CEL MEL Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ── Auto-seed on first run (Streamlit Cloud resets SQLite on restart) ─────────
if not run_query("SELECT 1 FROM projects LIMIT 1", {}):
    try:
        from database.seed_sawa import seed as _seed
        _seed()
    except Exception as _e:
        st.warning(f"Auto-seed skipped: {_e}")

# ── Brand ─────────────────────────────────────────────────────────────────────
NAVY = "#0D2B5E"
GOLD = "#C8A951"

# ── Auth ──────────────────────────────────────────────────────────────────────
from utils.auth import get_authenticator

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
st.session_state["role"] = creds.get(username, {}).get("role", "Viewer")

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
    'SAWA Programme · Fisheries &amp; Aquaculture Development · Ghana</span>'
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
    ("📥 INPUT", "Collect", "Modules C & E", "#E3F2FD", "#1565C0"),
    ("→", "", "", "white", NAVY),
    ("⚙️ PROCESS", "Analyse", "Module D", "#FFF8E1", "#E65100"),
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
     "Programme Director, Donors, FCDO / Gates Foundation",
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

# ── Role-Based Quick Start ────────────────────────────────────────────────────
role = st.session_state.get("role", "Viewer")
quick_start_map = {
    "Admin": {
        "icon": "🔧",
        "colour": "#B71C1C",
        "start": "Module A",
        "tip": "Set up partner targets in Module A, seed logframe in Module B, configure Kobo mappings in Module E.",
        "daily": "Check Module F for overdue reviews · Monitor Module G for pending actions.",
    },
    "Editor": {
        "icon": "✏️",
        "colour": "#1565C0",
        "start": "Module D",
        "tip": "Enter quarterly actuals in Module D, then use Module F to log data reviews.",
        "daily": "Module D → enter actuals → Module F → log review → Module G → raise decision report.",
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
            ("Survival", "Structured reporting in Module G ensures compliance with FCDO/Gates Foundation reporting requirements.", "✅"),
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

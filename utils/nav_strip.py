"""
MEL Information System Cycle — fixed top navigation strip.

Uses st.page_link() so Streamlit's own React Router handles navigation,
keeping the WebSocket alive and session_state (auth) intact.

A unique <span id="is-cycle-marker"> anchors the CSS :has() selector so only
this specific container gets position:fixed — not its parent blocks.
"""
from __future__ import annotations
import streamlit as st

_NAVY = "#0D2B5E"

# (display-label, page-file, stage-key, active-colour)
_STAGES = [
    ("📥 Input",   "pages/1_Partner_Alignment.py",  "Input",   "#2563EB"),
    ("⚙️ Process", "pages/5_Raw_Data_Analysis.py",  "Process", "#D97706"),
    ("🔍 Review",  "pages/6_Data_Review.py",         "Review",  "#0891B2"),
    ("✅ Decide",  "pages/7_Decision_Reports.py",    "Decide",  "#DC2626"),
    ("📊 Impact",  "pages/8_Impact_Dashboard.py",    "Impact",  "#16A34A"),
]


def _active_css(current_stage: str) -> str:
    """Return CSS that highlights the active stage pill."""
    rules = []
    for i, (_, _, stage, color) in enumerate(_STAGES, start=1):
        if stage == current_stage:
            rules.append(f"""
/* Active: {stage} */
div[data-testid="stVerticalBlock"]:has(> div span#is-cycle-marker)
div[data-testid="stColumn"]:nth-child({i})
div[data-testid="stPageLink"] a {{
    background: {color} !important;
    color: #fff !important;
    box-shadow: 0 0 0 2px rgba(255,255,255,0.25);
}}""")
    return "\n".join(rules)


def render_nav_strip(current_stage: str = "") -> None:
    """Inject IS Cycle strip. Call immediately after set_page_config / init_db."""

    st.markdown(f"""
<style>
/* ═══════════════════════════════════════════════════════════════════
   IS Cycle fixed top strip
   Target: the stVerticalBlock that directly wraps our marker span.
   :has(> div span#...) prevents matching ancestor blocks.
═══════════════════════════════════════════════════════════════════ */
div[data-testid="stVerticalBlock"]:has(> div span#is-cycle-marker) {{
    position: fixed !important;
    top: 3.1rem !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 99999 !important;
    background: {_NAVY} !important;
    padding: 0.15rem 0.5rem 0.1rem 0.5rem !important;
    box-shadow: 0 3px 14px rgba(0,0,0,0.30) !important;
    border-bottom: 1px solid rgba(255,255,255,0.07) !important;
}}

/* Push content below the strip */
[data-testid="stMainBlockContainer"] {{
    padding-top: 3rem !important;
}}

/* ── Page link base style ── */
div[data-testid="stVerticalBlock"]:has(> div span#is-cycle-marker)
div[data-testid="stPageLink"] a {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0.26rem 0.5rem !important;
    border-radius: 999px !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    color: rgba(255,255,255,0.68) !important;
    text-decoration: none !important;
    transition: background 0.13s, color 0.13s !important;
    white-space: nowrap !important;
    width: 100% !important;
}}

div[data-testid="stVerticalBlock"]:has(> div span#is-cycle-marker)
div[data-testid="stPageLink"] a:hover {{
    background: rgba(255,255,255,0.14) !important;
    color: #fff !important;
}}

/* ── Active stage ── */
{_active_css(current_stage)}

/* ── Sidebar: stage colour left-border bands ── */
/* Home page is item 1; pages 1-8 are items 2-9 */
[data-testid="stSidebarNavItems"] li:nth-child(2) a,
[data-testid="stSidebarNavItems"] li:nth-child(3) a,
[data-testid="stSidebarNavItems"] li:nth-child(4) a,
[data-testid="stSidebarNavItems"] li:nth-child(5) a {{
    border-left: 3px solid #2563EB !important;
    padding-left: 0.55rem !important;
}}
[data-testid="stSidebarNavItems"] li:nth-child(2)::before {{
    content: "INPUT";
    display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #2563EB;
    padding: .35rem 0 .1rem .9rem; opacity: .85;
}}
[data-testid="stSidebarNavItems"] li:nth-child(6) a {{
    border-left: 3px solid #D97706 !important;
    padding-left: 0.55rem !important;
}}
[data-testid="stSidebarNavItems"] li:nth-child(6)::before {{
    content: "PROCESS";
    display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #D97706;
    padding: .45rem 0 .1rem .9rem; opacity: .85;
}}
[data-testid="stSidebarNavItems"] li:nth-child(7) a {{
    border-left: 3px solid #0891B2 !important;
    padding-left: 0.55rem !important;
}}
[data-testid="stSidebarNavItems"] li:nth-child(7)::before {{
    content: "REVIEW";
    display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #0891B2;
    padding: .45rem 0 .1rem .9rem; opacity: .85;
}}
[data-testid="stSidebarNavItems"] li:nth-child(8) a {{
    border-left: 3px solid #DC2626 !important;
    padding-left: 0.55rem !important;
}}
[data-testid="stSidebarNavItems"] li:nth-child(8)::before {{
    content: "DECIDE";
    display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #DC2626;
    padding: .45rem 0 .1rem .9rem; opacity: .85;
}}
[data-testid="stSidebarNavItems"] li:nth-child(9) a {{
    border-left: 3px solid #16A34A !important;
    padding-left: 0.55rem !important;
}}
[data-testid="stSidebarNavItems"] li:nth-child(9)::before {{
    content: "IMPACT";
    display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #16A34A;
    padding: .45rem 0 .1rem .9rem; opacity: .85;
}}
</style>
""", unsafe_allow_html=True)

    # The strip container — marker anchors the :has() CSS above
    with st.container():
        st.markdown(
            '<div><span id="is-cycle-marker" style="display:none"></span></div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(len(_STAGES))
        for col, (label, page, _stage, _color) in zip(cols, _STAGES):
            with col:
                st.page_link(page, label=label, use_container_width=True)

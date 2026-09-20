"""
MEL Information System Cycle — fixed top navigation strip.

Call render_nav_strip("Stage") at the very top of every page (before any
other st.* call except set_page_config).

Stages and their primary landing pages:
  Input   → /Partner_Alignment   (pages 1–4: setup, logframe, plan, collect)
  Process → /Raw_Data_Analysis   (page 5)
  Review  → /Data_Review         (page 6)
  Decide  → /Decision_Reports    (page 7)
  Impact  → /Impact_Dashboard    (page 8)
"""
from __future__ import annotations
import streamlit as st

_NAVY   = "#0D2B5E"
_ORANGE = "#E87722"

# (label, emoji, page-slug, color, side-bar pages that belong to this stage)
# Page positions in the sidebar nav list (1-indexed, excluding the home entry):
#   1=Partner Alignment, 2=ToC Logframe, 3=Data Plan, 4=Kobo Sync,
#   5=Raw Data Analysis, 6=Data Review, 7=Decision Reports, 8=Impact Dashboard
_STAGES: list[tuple[str, str, str, str]] = [
    ("Input",   "📥", "/Partner_Alignment", "#2563EB"),
    ("Process", "⚙️", "/Raw_Data_Analysis", "#D97706"),
    ("Review",  "🔍", "/Data_Review",        "#0891B2"),
    ("Decide",  "✅", "/Decision_Reports",   "#DC2626"),
    ("Impact",  "📊", "/Impact_Dashboard",   "#16A34A"),
]

# Sidebar stage labels injected above first page in each group.
# nth-child counts the <li> items inside the nav list.
# In Streamlit 1.58 default MPA the home page is item 1, pages 1-8 are 2-9.
_SIDEBAR_CSS = """
/* ── Sidebar: stage colour bands ─────────────────────────────────── */
[data-testid="stSidebarNavItems"] li {{ list-style: none; }}

/* INPUT  – pages 1-4 (sidebar items 2-5) */
[data-testid="stSidebarNavItems"] li:nth-child(2) a,
[data-testid="stSidebarNavItems"] li:nth-child(3) a,
[data-testid="stSidebarNavItems"] li:nth-child(4) a,
[data-testid="stSidebarNavItems"] li:nth-child(5) a {{
    border-left: 3px solid #2563EB;
    padding-left: 0.55rem !important;
}}

/* PROCESS – page 5 (sidebar item 6) */
[data-testid="stSidebarNavItems"] li:nth-child(6) a {{
    border-left: 3px solid #D97706;
    padding-left: 0.55rem !important;
    margin-top: 0.25rem;
}}

/* REVIEW – page 6 (sidebar item 7) */
[data-testid="stSidebarNavItems"] li:nth-child(7) a {{
    border-left: 3px solid #0891B2;
    padding-left: 0.55rem !important;
    margin-top: 0.25rem;
}}

/* DECIDE – page 7 (sidebar item 8) */
[data-testid="stSidebarNavItems"] li:nth-child(8) a {{
    border-left: 3px solid #DC2626;
    padding-left: 0.55rem !important;
    margin-top: 0.25rem;
}}

/* IMPACT – page 8 (sidebar item 9) */
[data-testid="stSidebarNavItems"] li:nth-child(9) a {{
    border-left: 3px solid #16A34A;
    padding-left: 0.55rem !important;
    margin-top: 0.25rem;
}}

/* Stage micro-labels above first page of each non-Input group */
[data-testid="stSidebarNavItems"] li:nth-child(6)::before {{
    content: "PROCESS";
    display: block;
    font-size: 0.58rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    color: #D97706;
    padding: 0.35rem 0 0.1rem 0.9rem;
    opacity: 0.85;
}}
[data-testid="stSidebarNavItems"] li:nth-child(7)::before {{
    content: "REVIEW";
    display: block;
    font-size: 0.58rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    color: #0891B2;
    padding: 0.35rem 0 0.1rem 0.9rem;
    opacity: 0.85;
}}
[data-testid="stSidebarNavItems"] li:nth-child(8)::before {{
    content: "DECIDE";
    display: block;
    font-size: 0.58rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    color: #DC2626;
    padding: 0.35rem 0 0.1rem 0.9rem;
    opacity: 0.85;
}}
[data-testid="stSidebarNavItems"] li:nth-child(9)::before {{
    content: "IMPACT";
    display: block;
    font-size: 0.58rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    color: #16A34A;
    padding: 0.35rem 0 0.1rem 0.9rem;
    opacity: 0.85;
}}
/* INPUT label above first page group */
[data-testid="stSidebarNavItems"] li:nth-child(2)::before {{
    content: "INPUT";
    display: block;
    font-size: 0.58rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    color: #2563EB;
    padding: 0.35rem 0 0.1rem 0.9rem;
    opacity: 0.85;
}}
"""


def render_nav_strip(current_stage: str = "") -> None:
    """Render the IS Cycle strip.  Call once per page before other content."""

    # Build strip link HTML
    items: list[str] = []
    for i, (label, icon, href, color) in enumerate(_STAGES):
        active = label == current_stage
        if active:
            link_style = (
                f"background:{color}; color:#fff; "
                "box-shadow: 0 0 0 2px rgba(255,255,255,0.25);"
            )
        else:
            link_style = "color:rgba(255,255,255,0.68);"
        # Use pushState + popstate so Streamlit's WebSocket stays alive and
        # session_state (auth) is preserved — same mechanism as the sidebar nav.
        onclick = (
            f"window.parent.history.pushState({{}},'','{href}');"
            f"window.parent.dispatchEvent(new Event('popstate'));"
            f"return false;"
        )
        items.append(
            f'<a class="sc-link" href="{href}" onclick="{onclick}" style="{link_style}">'
            f'{icon}&nbsp;{label}</a>'
        )
        if i < len(_STAGES) - 1:
            items.append('<span class="sc-arrow">›</span>')

    strip_html = "\n".join(items)

    st.markdown(
        f"""
<style>
/* ── IS Cycle top strip ───────────────────────────────────────────── */
#is-cycle-strip {{
    position: fixed;
    top: 3.1rem;          /* sits just below Streamlit's own toolbar   */
    left: 0;
    right: 0;
    z-index: 99999;
    background: {_NAVY};
    padding: 0.32rem 1.2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    box-shadow: 0 3px 12px rgba(0,0,0,0.30);
    border-bottom: 1px solid rgba(255,255,255,0.07);
}}
.sc-link {{
    display: inline-flex;
    align-items: center;
    padding: 0.26rem 1.05rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.045em;
    text-decoration: none !important;
    white-space: nowrap;
    transition: background 0.14s, color 0.14s;
}}
.sc-link:hover {{
    background: rgba(255,255,255,0.14) !important;
    color: #fff !important;
}}
.sc-arrow {{
    color: rgba(255,255,255,0.22);
    font-size: 1.05rem;
    padding: 0 0.15rem;
    user-select: none;
    pointer-events: none;
}}
/* Push main content down so strip doesn't overlap it */
.stMainBlockContainer,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewContainer"] section.main {{
    padding-top: 3rem !important;
}}
{_SIDEBAR_CSS}
</style>
<div id="is-cycle-strip">{strip_html}</div>
""",
        unsafe_allow_html=True,
    )

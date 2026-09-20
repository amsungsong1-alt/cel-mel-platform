"""
MEL Information System Cycle — fixed top navigation strip.

Architecture (two-layer):
  VISUAL  — CSS-fixed HTML strip with onclick handlers (no page reload)
  ROUTING — Hidden st.page_link elements; onclick programmatically clicks them
             so Streamlit's React Router handles navigation and session_state
             (authentication) is preserved exactly like sidebar links.
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

_SIDEBAR_CSS = """
[data-testid="stSidebarNavItems"] li:nth-child(2) a,
[data-testid="stSidebarNavItems"] li:nth-child(3) a,
[data-testid="stSidebarNavItems"] li:nth-child(4) a,
[data-testid="stSidebarNavItems"] li:nth-child(5) a {
    border-left: 3px solid #2563EB !important;
    padding-left: 0.55rem !important;
}
[data-testid="stSidebarNavItems"] li:nth-child(2)::before {
    content: "INPUT";
    display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #2563EB;
    padding: .35rem 0 .1rem .9rem; opacity: .85;
}
[data-testid="stSidebarNavItems"] li:nth-child(6) a {
    border-left: 3px solid #D97706 !important; padding-left: 0.55rem !important;
}
[data-testid="stSidebarNavItems"] li:nth-child(6)::before {
    content: "PROCESS";
    display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #D97706;
    padding: .45rem 0 .1rem .9rem; opacity: .85;
}
[data-testid="stSidebarNavItems"] li:nth-child(7) a {
    border-left: 3px solid #0891B2 !important; padding-left: 0.55rem !important;
}
[data-testid="stSidebarNavItems"] li:nth-child(7)::before {
    content: "REVIEW";
    display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #0891B2;
    padding: .45rem 0 .1rem .9rem; opacity: .85;
}
[data-testid="stSidebarNavItems"] li:nth-child(8) a {
    border-left: 3px solid #DC2626 !important; padding-left: 0.55rem !important;
}
[data-testid="stSidebarNavItems"] li:nth-child(8)::before {
    content: "DECIDE";
    display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #DC2626;
    padding: .45rem 0 .1rem .9rem; opacity: .85;
}
[data-testid="stSidebarNavItems"] li:nth-child(9) a {
    border-left: 3px solid #16A34A !important; padding-left: 0.55rem !important;
}
[data-testid="stSidebarNavItems"] li:nth-child(9)::before {
    content: "IMPACT";
    display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #16A34A;
    padding: .45rem 0 .1rem .9rem; opacity: .85;
}
"""


def render_nav_strip(current_stage: str = "") -> None:
    """Inject IS Cycle strip. Call immediately after set_page_config / init_db."""

    # ── Build visual strip HTML ────────────────────────────────────────────
    items: list[str] = []
    for i, (label, _page, stage, color) in enumerate(_STAGES):
        active = stage == current_stage
        link_style = (
            f"background:{color}; color:#fff; "
            "box-shadow:0 0 0 2px rgba(255,255,255,0.25);"
        ) if active else "color:rgba(255,255,255,0.68);"

        # onclick: click the i-th hidden st.page_link anchor.
        # display:none elements are still in the DOM and clickable via JS.
        onclick = (
            f"(function(){{"
            f"var a=document.querySelectorAll("
            f"'div[data-testid=\"stVerticalBlock\"]:has(span#_pl_nav_marker)"
            f" div[data-testid=\"stPageLink\"] a');"
            f"if(a[{i}])a[{i}].click();"
            f"}})();return false;"
        )
        items.append(
            f'<a class="sc-link" href="#" onclick="{onclick}" style="{link_style}">'
            f"{label}</a>"
        )
        if i < len(_STAGES) - 1:
            items.append('<span class="sc-arrow">›</span>')

    strip_html = "\n".join(items)

    st.markdown(
        f"""
<style>
/* ── Visual fixed top strip ──────────────────────────────────────── */
#is-cycle-strip {{
    position: fixed;
    top: 3.1rem;
    left: 0; right: 0;
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
    font-size: 0.79rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-decoration: none !important;
    white-space: nowrap;
    cursor: pointer;
    transition: background 0.13s, color 0.13s;
}}
.sc-link:hover {{
    background: rgba(255,255,255,0.14) !important;
    color: #fff !important;
}}
.sc-arrow {{
    color: rgba(255,255,255,0.22);
    font-size: 1.05rem;
    padding: 0 0.12rem;
    user-select: none;
    pointer-events: none;
}}

/* ── Push main content below strip ──────────────────────────────── */
[data-testid="stMainBlockContainer"] {{
    padding-top: 3rem !important;
}}

/* ── Hide the functional page_link container ─────────────────────
   display:none keeps elements in DOM so JS .click() still works.  */
div[data-testid="stVerticalBlock"]:has(span#_pl_nav_marker) {{
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
    clip: rect(0 0 0 0) !important;
    white-space: nowrap !important;
    pointer-events: none !important;
    opacity: 0 !important;
}}
/* But the anchors inside must stay clickable for JS */
div[data-testid="stVerticalBlock"]:has(span#_pl_nav_marker)
div[data-testid="stPageLink"] a {{
    pointer-events: auto !important;
}}

{_SIDEBAR_CSS}
</style>
<div id="is-cycle-strip">{strip_html}</div>
""",
        unsafe_allow_html=True,
    )

    # ── Hidden st.page_link elements (real routing) ───────────────────────
    with st.container():
        # Unique marker so the CSS :has() selector above targets only this block
        st.markdown(
            '<span id="_pl_nav_marker" style="display:none;position:absolute"></span>',
            unsafe_allow_html=True,
        )
        for label, page, _stage, _color in _STAGES:
            st.page_link(page, label=label)

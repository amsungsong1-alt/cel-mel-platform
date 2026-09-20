"""
MEL Information System Cycle — fixed top navigation strip.

Two-layer architecture
-----------------------
VISUAL  : CSS-fixed HTML strip rendered via st.markdown. Styled pills in
          a navy bar; active stage highlighted.
ROUTING : Hidden st.page_link elements rendered after the visual strip.
          The strip's onclick clicks the corresponding hidden anchor so
          Streamlit's React Router handles the hop and session_state
          (authentication) is preserved — exactly like sidebar links.

CSS hiding strategy
-------------------
We target the hidden container's children DIRECTLY using the sibling
combinator (~) from the marker stMarkdown, rather than trying to hide
the parent container (which kept matching the outer page-level block):

    div[data-testid="stMarkdown"]:has(span#_pl_nav_marker) ~ div[data-testid="stPageLink"]

onclick JS strategy
-------------------
Uses getElementById → parentElement loop (with getAttribute check) to
walk up to the inner stVerticalBlock without relying on closest() with
complex CSS attribute selectors. Then querySelectorAll("a") picks up
all page_link anchors in order.
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
    border-left: 3px solid #2563EB !important; padding-left: 0.55rem !important;
}
[data-testid="stSidebarNavItems"] li:nth-child(2)::before {
    content: "INPUT"; display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #2563EB; padding: .35rem 0 .1rem .9rem; opacity: .85;
}
[data-testid="stSidebarNavItems"] li:nth-child(6) a {
    border-left: 3px solid #D97706 !important; padding-left: 0.55rem !important;
}
[data-testid="stSidebarNavItems"] li:nth-child(6)::before {
    content: "PROCESS"; display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #D97706; padding: .45rem 0 .1rem .9rem; opacity: .85;
}
[data-testid="stSidebarNavItems"] li:nth-child(7) a {
    border-left: 3px solid #0891B2 !important; padding-left: 0.55rem !important;
}
[data-testid="stSidebarNavItems"] li:nth-child(7)::before {
    content: "REVIEW"; display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #0891B2; padding: .45rem 0 .1rem .9rem; opacity: .85;
}
[data-testid="stSidebarNavItems"] li:nth-child(8) a {
    border-left: 3px solid #DC2626 !important; padding-left: 0.55rem !important;
}
[data-testid="stSidebarNavItems"] li:nth-child(8)::before {
    content: "DECIDE"; display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #DC2626; padding: .45rem 0 .1rem .9rem; opacity: .85;
}
[data-testid="stSidebarNavItems"] li:nth-child(9) a {
    border-left: 3px solid #16A34A !important; padding-left: 0.55rem !important;
}
[data-testid="stSidebarNavItems"] li:nth-child(9)::before {
    content: "IMPACT"; display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #16A34A; padding: .45rem 0 .1rem .9rem; opacity: .85;
}
"""

# ── Hide the routing page_link elements ───────────────────────────────────────
# Uses sibling combinator (~) from the marker stMarkdown so only the stPageLink
# elements in OUR inner container are hidden — not the rest of the page.
_HIDE_CSS = """
div[data-testid="stMarkdown"]:has(span#_pl_nav_marker) {
    display: none !important;
}
div[data-testid="stMarkdown"]:has(span#_pl_nav_marker) ~ div[data-testid="stPageLink"] {
    display: none !important;
}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stMarkdown"] span#_pl_nav_marker) {
    padding: 0 !important;
    gap: 0 !important;
    min-height: 0 !important;
    overflow: hidden !important;
}
"""


def render_nav_strip(current_stage: str = "") -> None:
    """Inject IS Cycle strip. Call immediately after set_page_config / init_db."""

    # ── Visual strip HTML ──────────────────────────────────────────────────────
    items: list[str] = []
    for i, (label, _page, stage, color) in enumerate(_STAGES):
        active = stage == current_stage
        link_style = (
            f"background:{color};color:#fff;"
            "box-shadow:0 0 0 2px rgba(255,255,255,0.25);"
        ) if active else "color:rgba(255,255,255,0.68);"

        # onclick uses single-quoted HTML attr so JS strings can use double quotes.
        # Walks up from the marker span until it hits the stVerticalBlock container,
        # then picks the i-th anchor (= the i-th page_link).
        onclick_js = (
            f"(function(){{"
            f'var m=document.getElementById("_pl_nav_marker");'
            f"if(!m)return;"
            f"var b=m.parentElement;"
            f'while(b&&b.getAttribute("data-testid")!=="stVerticalBlock")'
            f"b=b.parentElement;"
            f"if(!b)return;"
            f'var a=b.querySelectorAll("a");'
            f"if(a[{i}])a[{i}].click();"
            f"}})();return false;"
        )
        items.append(
            f"<a class=\"sc-link\" href=\"#\" onclick='{onclick_js}'"
            f" style=\"{link_style}\">{label}</a>"
        )
        if i < len(_STAGES) - 1:
            items.append('<span class="sc-arrow">›</span>')

    strip_html = "\n".join(items)

    st.markdown(
        f"""
<style>
#is-cycle-strip {{
    position: fixed;
    top: 3.1rem; left: 0; right: 0;
    z-index: 99999;
    background: {_NAVY};
    padding: 0.32rem 1.2rem;
    display: flex;
    align-items: center;
    justify-content: center;
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
[data-testid="stMainBlockContainer"] {{
    padding-top: 3rem !important;
}}
{_HIDE_CSS}
{_SIDEBAR_CSS}
</style>
<div id="is-cycle-strip">{strip_html}</div>
""",
        unsafe_allow_html=True,
    )

    # ── Hidden routing layer (real st.page_link navigation) ───────────────────
    with st.container():
        # Marker lets CSS sibling selector target the stPageLink elements below
        st.markdown(
            '<span id="_pl_nav_marker" style="display:none;position:absolute"></span>',
            unsafe_allow_html=True,
        )
        for label, page, _stage, _color in _STAGES:
            st.page_link(page, label=label)

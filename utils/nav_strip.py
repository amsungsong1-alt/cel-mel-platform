"""MEL IS Cycle — horizontal navigation strip using st.columns + st.page_link."""
from __future__ import annotations
import streamlit as st

_NAVY = "#0D2B5E"

_STAGES = [
    ("📥 Input",   "pages/1_Partner_Alignment.py",  "Input",   "#2563EB"),
    ("⚙️ Process", "pages/5_Raw_Data_Analysis.py",  "Process", "#D97706"),
    ("🔍 Review",  "pages/6_Data_Review.py",         "Review",  "#0891B2"),
    ("✅ Decide",  "pages/7_Decision_Reports.py",    "Decide",  "#DC2626"),
    ("📊 Impact",  "pages/8_Impact_Dashboard.py",    "Impact",  "#16A34A"),
]

# CSS targets the stHorizontalBlock IMMEDIATELY after the marker stMarkdown using
# the adjacent-sibling combinator (+).  That combinator works on the DOM tree —
# display:none on the marker does not break it — so this avoids the outer-page-
# container matching problem that caused the earlier blank-page bug.
_CSS = """
<style>
/* ── clear Streamlit ancestor properties that break position:fixed ──
   transform / will-change / contain all create a new containing block,
   which makes fixed children position relative to that element instead
   of the viewport.                                                    */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.block-container,
[data-testid="stMainBlockContainer"],
[data-testid="stVerticalBlock"] {{
    transform: none !important;
    will-change: auto !important;
    contain: none !important;
}}

/* ── hide the tiny marker element ─────────────────────────── */
[data-testid="stMarkdown"]:has(span#_nav_marker) {{
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
/* ── fixed nav row ─────────────────────────────────────────── */
[data-testid="stMarkdown"]:has(span#_nav_marker)
+ [data-testid="stHorizontalBlock"] {{
    position: fixed !important;
    top: 2.875rem !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    z-index: 9999 !important;
    background: {navy} !important;
    padding: 0.32rem 0.8rem !important;
    border-radius: 0 !important;
    gap: 0 !important;
    margin-bottom: 0 !important;
    box-sizing: border-box !important;
}}
/* ── inactive page_link pill ───────────────────────────────── */
[data-testid="stMarkdown"]:has(span#_nav_marker)
+ [data-testid="stHorizontalBlock"] [data-testid="stPageLink"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}}
[data-testid="stMarkdown"]:has(span#_nav_marker)
+ [data-testid="stHorizontalBlock"] [data-testid="stPageLink"] a {{
    color: rgba(255,255,255,0.72) !important;
    font-size: 0.79rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    border-radius: 999px !important;
    padding: 0.22rem 0.7rem !important;
    display: inline-block !important;
    text-decoration: none !important;
    white-space: nowrap !important;
    transition: background 0.12s, color 0.12s !important;
}}
[data-testid="stMarkdown"]:has(span#_nav_marker)
+ [data-testid="stHorizontalBlock"] [data-testid="stPageLink"] a:hover {{
    background: rgba(255,255,255,0.16) !important;
    color: #fff !important;
}}
/* ── sidebar colour bands ──────────────────────────────────── */
[data-testid="stSidebarNavItems"] li:nth-child(2) a,
[data-testid="stSidebarNavItems"] li:nth-child(3) a,
[data-testid="stSidebarNavItems"] li:nth-child(4) a,
[data-testid="stSidebarNavItems"] li:nth-child(5) a {{
    border-left: 3px solid #2563EB !important; padding-left: 0.55rem !important;
}}
[data-testid="stSidebarNavItems"] li:nth-child(2)::before {{
    content: "INPUT"; display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #2563EB; padding: .35rem 0 .1rem .9rem; opacity: .85;
}}
[data-testid="stSidebarNavItems"] li:nth-child(6) a {{
    border-left: 3px solid #D97706 !important; padding-left: 0.55rem !important;
}}
[data-testid="stSidebarNavItems"] li:nth-child(6)::before {{
    content: "PROCESS"; display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #D97706; padding: .45rem 0 .1rem .9rem; opacity: .85;
}}
[data-testid="stSidebarNavItems"] li:nth-child(7) a {{
    border-left: 3px solid #0891B2 !important; padding-left: 0.55rem !important;
}}
[data-testid="stSidebarNavItems"] li:nth-child(7)::before {{
    content: "REVIEW"; display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #0891B2; padding: .45rem 0 .1rem .9rem; opacity: .85;
}}
[data-testid="stSidebarNavItems"] li:nth-child(8) a {{
    border-left: 3px solid #DC2626 !important; padding-left: 0.55rem !important;
}}
[data-testid="stSidebarNavItems"] li:nth-child(8)::before {{
    content: "DECIDE"; display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #DC2626; padding: .45rem 0 .1rem .9rem; opacity: .85;
}}
[data-testid="stSidebarNavItems"] li:nth-child(9) a {{
    border-left: 3px solid #16A34A !important; padding-left: 0.55rem !important;
}}
[data-testid="stSidebarNavItems"] li:nth-child(9)::before {{
    content: "IMPACT"; display: block; font-size: 0.58rem; font-weight: 800;
    letter-spacing: .1em; color: #16A34A; padding: .45rem 0 .1rem .9rem; opacity: .85;
}}
</style>
""".format(navy=_NAVY)


def render_nav_strip(current_stage: str = "") -> None:
    """Render the IS Cycle horizontal strip. Call after set_page_config / init_db."""
    st.markdown(_CSS, unsafe_allow_html=True)

    # Marker — gives the adjacent + combinator its anchor point.
    st.markdown(
        '<span id="_nav_marker" style="display:none;position:absolute"></span>',
        unsafe_allow_html=True,
    )

    # Horizontal columns — st.page_link is the ONLY thing that navigates while
    # preserving session_state (auth). Active stage shows as a static pill.
    cols = st.columns(len(_STAGES))
    for col, (label, page, stage, color) in zip(cols, _STAGES):
        with col:
            if stage == current_stage:
                st.markdown(
                    f'<div style="background:{color};color:#fff;border-radius:999px;'
                    f'padding:0.22rem 0.7rem;font-size:0.79rem;font-weight:800;'
                    f'letter-spacing:0.04em;text-align:center;white-space:nowrap;">'
                    f"{label}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.page_link(page, label=label, use_container_width=True)

    # Spacer so page content clears the fixed strip (fixed removes it from flow).
    st.markdown(
        '<div style="height:2.5rem;line-height:0;font-size:0"> </div>',
        unsafe_allow_html=True,
    )

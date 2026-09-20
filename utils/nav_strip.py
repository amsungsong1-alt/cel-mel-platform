"""MEL IS Cycle navigation — vertical st.page_link bar (reliable, auth-preserving)."""
from __future__ import annotations
import streamlit as st

_STAGES = [
    ("📥 Input",   "pages/1_Partner_Alignment.py",  "Input",   "#2563EB"),
    ("⚙️ Process", "pages/5_Raw_Data_Analysis.py",  "Process", "#D97706"),
    ("🔍 Review",  "pages/6_Data_Review.py",         "Review",  "#0891B2"),
    ("✅ Decide",  "pages/7_Decision_Reports.py",    "Decide",  "#DC2626"),
    ("📊 Impact",  "pages/8_Impact_Dashboard.py",    "Impact",  "#16A34A"),
]

_SIDEBAR_CSS = """
<style>
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
</style>
"""


def render_nav_strip(current_stage: str = "") -> None:
    """Render IS Cycle navigation bar. Call after set_page_config / init_db."""
    st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:0.68rem;font-weight:800;letter-spacing:.12em;'
        'color:#0D2B5E;margin:0;opacity:.6;">MEL IS CYCLE</p>',
        unsafe_allow_html=True,
    )
    for label, page, stage, color in _STAGES:
        active = stage == current_stage
        if active:
            st.markdown(
                f'<div style="border-left:4px solid {color};'
                f'background:{color}12;padding:2px 0 2px 6px;margin-bottom:1px;">'
                f'<span style="font-size:0.75rem;font-weight:800;color:{color};">'
                f'▶ {label}</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.page_link(page, label=label, use_container_width=True)

    st.divider()

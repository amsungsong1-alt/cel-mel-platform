"""MEL IS Cycle — horizontal navigation strip.

Visual fixed bar is injected into document.body via JS (position:fixed
works there — no ancestor transforms/contain to fight). Real st.page_link
elements are kept in a 0-height hidden block so Streamlit's router handles
navigation and session_state is preserved.
"""
from __future__ import annotations
import json
import streamlit as st
import streamlit.components.v1 as components

_NAVY = "#0D2B5E"

_STAGES = [
    ("📥 Input",    "pages/1_Partner_Alignment.py",  "Input",   "#2563EB"),
    ("⚙️ Process",  "pages/5_Raw_Data_Analysis.py",  "Process", "#D97706"),
    ("🔍 Review",   "pages/6_Data_Review.py",         "Review",  "#0891B2"),
    ("✅ Decide",   "pages/7_Decision_Reports.py",    "Decide",  "#DC2626"),
    ("📊 Impact",   "pages/8_Impact_Dashboard.py",    "Impact",  "#16A34A"),
]

# Collapse the real nav to 0-height but keep it in the DOM so the
# st.page_link <a> elements remain clickable via JS.
_CSS = """
<style>
[data-testid="stMarkdown"]:has(span#_nav_marker) {{
    display: none !important;
}}
[data-testid="stMarkdown"]:has(span#_nav_marker)
+ [data-testid="stHorizontalBlock"] {{
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    overflow: hidden !important;
    opacity: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    position: absolute !important;
    pointer-events: none !important;
}}
/* ── sidebar colour bands ─────────────────────────────────── */
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
"""


def _build_js(current_stage: str) -> str:
    stages_data = [
        {"label": label, "stage": stage, "color": color}
        for label, _, stage, color in _STAGES
    ]
    return """
(function() {
    var doc = window.parent.document;
    var STAGES = """ + json.dumps(stages_data, ensure_ascii=False) + """;
    var CURRENT = """ + json.dumps(current_stage, ensure_ascii=False) + """;
    var NAVY = '""" + _NAVY + """';

    // Remove stale bar left by a previous page render
    var old = doc.getElementById('_cel_mel_nav');
    if (old) { old.remove(); }

    function createBar() {
        var bar = doc.createElement('nav');
        bar.id = '_cel_mel_nav';
        bar.style.cssText = 'position:fixed;top:2.875rem;left:0;right:0;' +
            'width:100%;z-index:1000000;background:' + NAVY + ';' +
            'display:flex;align-items:center;padding:0.32rem 0.8rem;' +
            'box-sizing:border-box;gap:0;';

        STAGES.forEach(function(s) {
            var btn = doc.createElement('button');
            btn.setAttribute('data-stage', s.stage);
            btn.textContent = s.label;
            var isActive = (s.stage === CURRENT);
            btn.style.cssText = 'flex:1;border:none;border-radius:999px;' +
                'padding:0.22rem 0.7rem;font-size:0.79rem;font-family:inherit;' +
                'letter-spacing:0.04em;text-align:center;white-space:nowrap;' +
                'line-height:normal;transition:background 0.12s,color 0.12s;' +
                'background:' + (isActive ? s.color : 'transparent') + ';' +
                'color:' + (isActive ? '#fff' : 'rgba(255,255,255,0.72)') + ';' +
                'font-weight:' + (isActive ? '800' : '700') + ';' +
                'cursor:' + (isActive ? 'default' : 'pointer') + ';';

            if (!isActive) {
                btn.addEventListener('mouseenter', function() {
                    btn.style.background = 'rgba(255,255,255,0.16)';
                    btn.style.color = '#fff';
                });
                btn.addEventListener('mouseleave', function() {
                    btn.style.background = 'transparent';
                    btn.style.color = 'rgba(255,255,255,0.72)';
                });
                (function(lbl) {
                    btn.addEventListener('click', function() {
                        var links = doc.querySelectorAll('[data-testid="stPageLink"] a');
                        for (var i = 0; i < links.length; i++) {
                            var t = (links[i].textContent || '').replace(/\\s+/g, ' ').trim();
                            if (t.indexOf(lbl.replace(/\\s+/g, ' ').trim()) >= 0) {
                                links[i].click();
                                return;
                            }
                        }
                    });
                })(s.label);
            }
            bar.appendChild(btn);
        });

        doc.body.appendChild(bar);
    }

    function waitAndCreate() {
        if (doc.querySelector('span#_nav_marker')) {
            createBar();
        } else {
            setTimeout(waitAndCreate, 80);
        }
    }
    waitAndCreate();
})();
"""


def render_nav_strip(current_stage: str = "") -> None:
    """Render the IS Cycle horizontal strip. Call after set_page_config / init_db."""
    st.markdown(_CSS, unsafe_allow_html=True)

    # Marker lets JS confirm the real nav is loaded before injecting the fixed bar.
    st.markdown(
        '<span id="_nav_marker" style="display:none;position:absolute"></span>',
        unsafe_allow_html=True,
    )

    # Real nav — 0-height, invisible, but present in React DOM so st.page_link
    # <a> elements can be found and triggered by the fixed bar's click handlers.
    cols = st.columns(len(_STAGES))
    for col, (label, page, stage, color) in zip(cols, _STAGES):
        with col:
            if stage == current_stage:
                # Active stage has no link target; render invisible placeholder.
                st.markdown(
                    f'<span style="display:none">{label}</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.page_link(page, label=label, use_container_width=True)

    # Spacer — reserves room for the fixed bar so page content starts below it.
    st.markdown(
        '<div style="height:2.5rem;line-height:0;font-size:0"> </div>',
        unsafe_allow_html=True,
    )

    # JS — builds and appends the visual fixed bar to window.parent.document.body.
    # Direct child of <body> means no ancestor transforms/contain to interfere.
    components.html(
        f"<script>{_build_js(current_stage)}</script>",
        height=0,
    )

"""MEL IS Cycle — horizontal navigation strip.

Visual fixed bar is injected into document.body via JS from a same-origin
component iframe. The real st.page_link columns stay in the React DOM
(hidden by JS inline-style) so Streamlit's router handles navigation and
session_state is preserved.

Why JS instead of CSS:
  - position:sticky/fixed are blocked by Streamlit parent contain/transform.
  - The + adjacent-sibling CSS selector fails because Streamlit 1.30+ wraps
    every block in stVerticalBlockBorderWrapper, so stMarkdown and
    stHorizontalBlock are NOT direct siblings in the DOM.
  - JS walks the wrapper to find the real nav block reliably.
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

# Only used for sidebar colour bands — no sticky/fixed rules needed here.
_CSS = """
<style>
[data-testid="stMarkdown"]:has(span#_nav_marker) {
    display: none !important;
}
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


def _build_js(current_stage: str) -> str:
    stages_data = [
        {"label": label, "stage": stage, "color": color}
        for label, _, stage, color in _STAGES
    ]
    return r"""
(function() {
    var doc = window.parent.document;
    var STAGES = """ + json.dumps(stages_data, ensure_ascii=False) + r""";
    var CURRENT = """ + json.dumps(current_stage, ensure_ascii=False) + r""";
    var NAVY = '""" + _NAVY + r"""';

    // Streamlit 1.30+ wraps every block in stVerticalBlockBorderWrapper,
    // so stMarkdown and stHorizontalBlock are NOT direct siblings.
    // We walk up from the marker to the wrapper then check the next wrapper.
    function findNavBlock() {
        var marker = doc.querySelector('span#_nav_marker');
        if (!marker) return null;

        var mdEl = marker.closest('[data-testid="stMarkdown"]');
        if (!mdEl) return null;

        // Case A: direct sibling (older Streamlit without wrapper div)
        var sib = mdEl.nextElementSibling;
        if (sib && sib.getAttribute('data-testid') === 'stHorizontalBlock') {
            return sib;
        }

        // Case B: each block is inside its own stVerticalBlockBorderWrapper
        var wrapper = mdEl.parentElement;
        if (wrapper) {
            var nextWrapper = wrapper.nextElementSibling;
            if (nextWrapper) {
                var hb = nextWrapper.querySelector('[data-testid="stHorizontalBlock"]');
                if (hb) return hb;
            }
        }

        // Case C: deeper nesting — climb to stVerticalBlock, pick first hblock
        var vblock = mdEl.parentElement;
        while (vblock && vblock.getAttribute('data-testid') !== 'stVerticalBlock') {
            vblock = vblock.parentElement;
        }
        if (vblock) {
            return vblock.querySelector('[data-testid="stHorizontalBlock"]');
        }

        return null;
    }

    function hideRealNav(nav) {
        nav.style.cssText += ';height:0!important;min-height:0!important;' +
            'max-height:0!important;overflow:hidden!important;opacity:0!important;' +
            'position:absolute!important;pointer-events:none!important;margin:0!important;padding:0!important;';
    }

    function createBar() {
        var old = doc.getElementById('_cel_mel_nav');
        if (old) old.remove();

        var bar = doc.createElement('nav');
        bar.id = '_cel_mel_nav';
        bar.style.cssText = 'position:fixed;top:2.875rem;left:0;right:0;width:100%;' +
            'z-index:1000000;background:' + NAVY + ';display:flex;align-items:center;' +
            'padding:0.32rem 0.8rem;box-sizing:border-box;';

        STAGES.forEach(function(s) {
            var btn = doc.createElement('button');
            btn.textContent = s.label;
            var isActive = (s.stage === CURRENT);
            btn.style.cssText = 'flex:1;border:none;border-radius:999px;' +
                'padding:0.22rem 0.7rem;font-size:0.79rem;font-family:inherit;' +
                'letter-spacing:0.04em;text-align:center;white-space:nowrap;' +
                'line-height:normal;transition:background 0.12s,color 0.12s;' +
                'background:' + (isActive ? s.color : 'transparent') + ';' +
                'color:'      + (isActive ? '#fff' : 'rgba(255,255,255,0.72)') + ';' +
                'font-weight:' + (isActive ? '800' : '700') + ';' +
                'cursor:'     + (isActive ? 'default' : 'pointer') + ';';

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
                            var t = (links[i].textContent || '').replace(/\s+/g, ' ').trim();
                            var l = lbl.replace(/\s+/g, ' ').trim();
                            if (t.indexOf(l) >= 0 || l.indexOf(t) >= 0) {
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

    function init() {
        var nav = findNavBlock();
        if (!nav) { setTimeout(init, 80); return; }
        hideRealNav(nav);
        createBar();
    }

    // Remove stale bar from a prior page render then reinit
    var stale = doc.getElementById('_cel_mel_nav');
    if (stale) stale.remove();
    init();
})();
"""


def render_nav_strip(current_stage: str = "") -> None:
    """Render the IS Cycle horizontal strip. Call after set_page_config / init_db."""
    st.markdown(_CSS, unsafe_allow_html=True)

    # Marker — lets JS confirm the page has rendered before injecting the bar.
    st.markdown(
        '<span id="_nav_marker" style="display:none;position:absolute"></span>',
        unsafe_allow_html=True,
    )

    # Real nav — kept in React DOM so st.page_link <a> elements can be
    # triggered by the fixed bar's click handlers. JS hides them inline.
    cols = st.columns(len(_STAGES))
    for col, (label, page, stage, color) in zip(cols, _STAGES):
        with col:
            if stage == current_stage:
                st.markdown(
                    f'<span style="display:none">{label}</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.page_link(page, label=label, use_container_width=True)

    # Spacer — reserves room so page content clears the fixed bar.
    st.markdown(
        '<div style="height:2.5rem;line-height:0;font-size:0"> </div>',
        unsafe_allow_html=True,
    )

    # JS — runs in a same-origin component iframe; accesses window.parent.document
    # to inject the fixed <nav> directly into <body> (no ancestor constraints).
    components.html(
        f"<script>{_build_js(current_stage)}</script>",
        height=0,
    )

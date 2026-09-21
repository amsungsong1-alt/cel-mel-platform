"""Module B — Theory of Change & Logframe

Tab 1 — Theory of Change: top-down graphviz tree, level-filter buttons.
Tab 2 — Logframe: filterable/sortable table with inline editing and
         full field-level audit trail in logframe_changelog.
"""
from datetime import datetime, timezone
import streamlit as st
import pandas as pd

from database.db import init_db, run_query, run_write
from utils.shared_widgets import project_selector
from utils.auth import can, can_write_module
from utils.nav_strip import render_nav_strip

st.set_page_config(page_title="ToC & Logframe — CEL MEL", layout="wide")
init_db()
render_nav_strip("Input")

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not st.session_state.get("authentication_status"):
    st.error("Please log in from the main page.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    project_id = project_selector()
    if project_id is None:
        st.stop()
    st.divider()
    st.caption(f"Role: **{st.session_state.get('role', 'Viewer')}**")

# ── Cross-tab filter (set by Tab 1 level buttons, read by Tab 2) ──────────────
if "toc_level_filter" not in st.session_state:
    st.session_state["toc_level_filter"] = []

st.title("Module B — Theory of Change & Logframe")

tab_toc, tab_lf, tab_map = st.tabs(["🌳 Theory of Change", "📋 Logframe", "📍 ToC × Register"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Theory of Change
# ═══════════════════════════════════════════════════════════════════════════════
LEVEL_ORDER = ["Impact", "Outcome", "Intermediate Outcome", "Output", "Activity", "Input"]

LEVEL_COLORS = {
    "Impact":               "#004D40",
    "Outcome":              "#4A148C",
    "Intermediate Outcome": "#0D47A1",
    "Output":               "#BF360C",
    "Activity":             "#E65100",
    "Input":                "#37474F",
}


def _wrap(text: str, width: int = 38) -> str:
    """Break text into graphviz left-justified lines (\\l token)."""
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        lines.append(line)
    return "\\l".join(lines) + "\\l"


def _build_dot(nodes: list[dict]) -> str:
    by_level: dict[str, list] = {}
    for n in nodes:
        by_level.setdefault(n["level"], []).append(n)

    lines = [
        "digraph toc {",
        '  rankdir=TB;',
        '  bgcolor="transparent";',
        '  graph [splines=ortho nodesep=0.4 ranksep=0.6];',
        '  node [shape=box style="filled,rounded" fontsize=9 fontcolor=white',
        '        fontname="Helvetica" margin="0.2,0.12" width=3.2 height=0.5];',
        '  edge [color="#90A4AE" arrowsize=0.65];',
        "",
    ]

    # Same-rank groupings keep each level on one horizontal band.
    for lvl in LEVEL_ORDER:
        grp = by_level.get(lvl, [])
        if grp:
            ids = " ".join(f"n{n['id']}" for n in grp)
            lines.append(f"  {{ rank=same; {ids}; }}")
    lines.append("")

    for n in nodes:
        color   = LEVEL_COLORS.get(n["level"], "#607D8B")
        label   = f"{n['level']}\\l{'─'*20}\\l{_wrap(n['statement'])}"
        tooltip = n["statement"].replace('"', '\\"')
        lines.append(
            f'  n{n["id"]} [label="{label}" fillcolor="{color}" tooltip="{tooltip}"];'
        )
    lines.append("")

    for n in nodes:
        if n.get("parent_id"):
            lines.append(f"  n{n['parent_id']} -> n{n['id']};")

    lines.append("}")
    return "\n".join(lines)


with tab_toc:
    toc_nodes = run_query(
        "SELECT id, level, statement, parent_id FROM toc_nodes "
        "WHERE project_id=:pid ORDER BY id",
        {"pid": project_id},
    )

    if not toc_nodes:
        st.info("No ToC nodes found — run `python -m database.seed_sawa` to load SAWA data.")
        st.stop()

    st.graphviz_chart(_build_dot(toc_nodes), use_container_width=True)

    # ── Level filter buttons ──────────────────────────────────────────────────
    st.divider()
    st.caption("Select a level to filter the Logframe tab, or clear to show all:")

    active_filter = st.session_state["toc_level_filter"]
    present_levels = [lvl for lvl in LEVEL_ORDER if any(n["level"] == lvl for n in toc_nodes)]

    btn_cols = st.columns(len(present_levels) + 1)
    for i, lvl in enumerate(present_levels):
        color   = LEVEL_COLORS.get(lvl, "#607D8B")
        is_active = lvl in active_filter
        # Highlight active button with markdown badge.
        badge = f'<span style="background:{color};color:#fff;padding:3px 10px;border-radius:4px;font-size:0.82em;font-weight:{"700" if is_active else "400"}">{lvl}</span>'
        with btn_cols[i]:
            st.markdown(badge, unsafe_allow_html=True)
            if st.button("Select", key=f"lvl_btn_{lvl}", use_container_width=True):
                st.session_state["toc_level_filter"] = [] if is_active else [lvl]
                st.rerun()

    with btn_cols[-1]:
        st.markdown('<span style="font-size:0.82em;color:#888">All levels</span>', unsafe_allow_html=True)
        if st.button("Clear filter", use_container_width=True):
            st.session_state["toc_level_filter"] = []
            st.rerun()

    if active_filter:
        st.info(f"Logframe tab is filtered to: **{', '.join(active_filter)}**. Switch to the Logframe tab or click Clear to reset.")

    # ── Node detail expander ──────────────────────────────────────────────────
    with st.expander("Browse ToC node statements"):
        for lvl in LEVEL_ORDER:
            grp = [n for n in toc_nodes if n["level"] == lvl]
            if not grp:
                continue
            color = LEVEL_COLORS.get(lvl, "#607D8B")
            st.markdown(
                f'<span style="background:{color};color:#fff;padding:2px 10px;'
                f'border-radius:4px;font-size:0.8em;">{lvl}</span>',
                unsafe_allow_html=True,
            )
            for n in grp:
                st.markdown(f"- {n['statement']}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Logframe
# ═══════════════════════════════════════════════════════════════════════════════

# Display column names → DB field names mapping (order = table column order)
_DISPLAY_COLS = {
    "Results Level":          "result_level",
    "Indicator ID":           "indicator_code",
    "Indicator (SMART)":      "indicator_statement",
    "Disaggregation":         "disaggregation",
    "Baseline":               "baseline_value",
    "Target (Annual)":        "target_annual",
    "Target (LOP)":           "target_lop",
    "Means of Verification":  "means_of_verification",
    "Frequency":              "frequency",
    "Responsible":            "responsible",
    "Critical Assumption":    "critical_assumption",
}

_EDITABLE_DISPLAY_COLS = [
    "Baseline", "Target (Annual)", "Target (LOP)",
    "Means of Verification", "Frequency", "Responsible",
    "Disaggregation", "Critical Assumption",
]

_RESULT_LEVEL_OPTIONS = ["Impact", "Outcome", "Output", "Activity", "Input"]

with tab_lf:
    lf_rows = run_query(
        "SELECT id, " + ", ".join(_DISPLAY_COLS.values()) + " "
        "FROM logframe_rows WHERE project_id=:pid ORDER BY id",
        {"pid": project_id},
    )

    if not lf_rows:
        st.info("No logframe rows found — run `python -m database.seed_sawa` to load SAWA data.")
        st.stop()

    # ── Filter row ────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])

    all_levels      = sorted({r["result_level"] for r in lf_rows if r["result_level"]})
    all_responsible = sorted({r["responsible"]   for r in lf_rows if r["responsible"]})

    with col_f1:
        sel_levels = st.multiselect(
            "Results level",
            all_levels,
            default=st.session_state.get("toc_level_filter", []),
            key="lf_level_filter",
        )
    with col_f2:
        sel_resp = st.multiselect("Responsible", all_responsible, key="lf_resp_filter")
    with col_f3:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        if st.button("Clear filters", use_container_width=True):
            st.session_state["toc_level_filter"] = []
            st.rerun()

    # Apply filters
    filtered = [
        r for r in lf_rows
        if (not sel_levels or r["result_level"] in sel_levels)
        and (not sel_resp   or r["responsible"]   in sel_resp)
    ]

    st.caption(f"Showing **{len(filtered)}** of **{len(lf_rows)}** indicators.")

    # ── Build display DataFrame ───────────────────────────────────────────────
    def _to_df(rows: list[dict]) -> pd.DataFrame:
        display_rows = [
            {"_id": r["id"]} | {disp: r[db] for disp, db in _DISPLAY_COLS.items()}
            for r in rows
        ]
        return pd.DataFrame(display_rows)

    df_display = _to_df(filtered)

    col_config = {
        "_id":                    st.column_config.NumberColumn("DB ID", disabled=True, width="small"),
        "Results Level":          st.column_config.SelectboxColumn("Results Level", options=_RESULT_LEVEL_OPTIONS, width="medium"),
        "Indicator ID":           st.column_config.TextColumn("Indicator ID", width="small"),
        "Indicator (SMART)":      st.column_config.TextColumn("Indicator (SMART)", width="large"),
        "Disaggregation":         st.column_config.TextColumn("Disaggregation", width="medium"),
        "Baseline":               st.column_config.TextColumn("Baseline", width="small"),
        "Target (Annual)":        st.column_config.TextColumn("Target (Annual)", width="small"),
        "Target (LOP)":           st.column_config.TextColumn("Target (LOP)", width="small"),
        "Means of Verification":  st.column_config.TextColumn("Means of Verification", width="large"),
        "Frequency":              st.column_config.SelectboxColumn(
                                      "Frequency",
                                      options=["Quarterly", "Bi-annual", "Annual"],
                                      width="small",
                                  ),
        "Responsible":            st.column_config.SelectboxColumn(
                                      "Responsible",
                                      options=["CEL MEAL", "Partner MEAL", "Programme Team"],
                                      width="medium",
                                  ),
        "Critical Assumption":    st.column_config.TextColumn("Critical Assumption", width="large"),
    }

    # ── Render table ──────────────────────────────────────────────────────────
    if can_write_module("B"):
        st.caption(
            "✏️ **Admin/Editor view** — edit any yellow-highlighted field, then click **Save changes**. "
            "Every edit is logged with your name and a timestamp."
        )

        disabled_cols = [
            c for c in df_display.columns
            if c not in _EDITABLE_DISPLAY_COLS
        ]

        edited_df = st.data_editor(
            df_display,
            column_config=col_config,
            disabled=disabled_cols,
            hide_index=True,
            use_container_width=True,
            key="lf_editor",
            num_rows="fixed",
        )

        if st.button("💾 Save changes", type="primary"):
            editor    = st.session_state.get("name", st.session_state.get("username", "unknown"))
            now_iso   = datetime.now(timezone.utc).isoformat(timespec="seconds")
            changes   = 0

            orig_indexed = {r["id"]: r for r in filtered}

            for _, edit_row in edited_df.iterrows():
                row_id   = int(edit_row["_id"])
                orig_row = orig_indexed.get(row_id)
                if orig_row is None:
                    continue

                for disp_col in _EDITABLE_DISPLAY_COLS:
                    db_field  = _DISPLAY_COLS[disp_col]
                    old_val   = str(orig_row.get(db_field) or "")
                    new_val   = str(edit_row.get(disp_col) or "")

                    if old_val == new_val:
                        continue

                    # Write new value
                    run_write(
                        f"UPDATE logframe_rows SET {db_field}=:v WHERE id=:id",
                        {"v": new_val, "id": row_id},
                    )
                    # Write changelog entry
                    run_write(
                        """INSERT INTO logframe_changelog
                           (row_id, field_changed, old_value, new_value, changed_by, changed_at)
                           VALUES (:row_id, :field, :old, :new, :by, :at)""",
                        {
                            "row_id": row_id,
                            "field":  disp_col,
                            "old":    old_val,
                            "new":    new_val,
                            "by":     editor,
                            "at":     now_iso,
                        },
                    )
                    changes += 1

            if changes:
                st.success(f"Saved {changes} field change(s). Audit trail updated.")
                st.rerun()
            else:
                st.info("No changes detected.")

        # ── Changelog viewer ─────────────────────────────────────────────────
        with st.expander("📜 Edit history (logframe changelog)"):
            changelog = run_query(
                """SELECT cl.changed_at, cl.changed_by, lr.indicator_code,
                          cl.field_changed, cl.old_value, cl.new_value
                   FROM   logframe_changelog cl
                   JOIN   logframe_rows lr ON cl.row_id = lr.id
                   WHERE  lr.project_id = :pid
                   ORDER  BY cl.changed_at DESC
                   LIMIT  100""",
                {"pid": project_id},
            )
            if changelog:
                st.dataframe(pd.DataFrame(changelog), hide_index=True, use_container_width=True)
            else:
                st.caption("No edits recorded yet.")

    else:
        # Viewer — read-only, hide internal _id column
        st.dataframe(
            df_display.drop(columns=["_id"]),
            column_config={k: v for k, v in col_config.items() if k != "_id"},
            hide_index=True,
            use_container_width=True,
        )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ToC × CEL Indicator Register
# ═══════════════════════════════════════════════════════════════════════════════
_LC = {
    "impact":  "#004D40",
    "outcome": "#4A148C",
    "io":      "#0D47A1",
    "output":  "#BF360C",
    "input":   "#37474F",
}


def _badges(formal: list = None, sourced: list = None, proposed: list = None) -> str:
    h = ""
    for i in (formal   or []):
        h += (f'<span style="background:#F9A825;color:#000;border-radius:3px;'
              f'padding:1px 6px;font-size:0.69rem;font-weight:700;margin:1px 2px;'
              f'display:inline-block;">{i}</span>')
    for i in (sourced  or []):
        h += (f'<span style="background:#E65100;color:#fff;border-radius:3px;'
              f'padding:1px 6px;font-size:0.69rem;font-weight:700;margin:1px 2px;'
              f'display:inline-block;">{i}</span>')
    for i in (proposed or []):
        h += (f'<span style="background:#E0E0E0;color:#555;border-radius:3px;'
              f'padding:1px 6px;font-size:0.69rem;font-style:italic;margin:1px 2px;'
              f'display:inline-block;">{i}*</span>')
    return h


def _card(color: str, level_lbl: str, name: str, desc: str,
          formal=None, sourced=None, proposed=None, note: str = "") -> str:
    bhtml = _badges(formal, sourced, proposed)
    note_html = (
        f'<div style="background:#FFF3E0;border-left:3px solid #FF8F00;'
        f'padding:3px 8px;margin-top:6px;font-size:0.68rem;color:#BF360C;'
        f'line-height:1.35;">📌 {note}</div>'
    ) if note else ""
    return (
        f'<div style="background:#FAFAFA;border:1px solid #E0E0E0;'
        f'border-left:4px solid {color};border-radius:5px;padding:9px 11px;margin:2px 0;">'
        f'<div style="color:{color};font-size:0.62rem;font-weight:800;'
        f'letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px;">{level_lbl}</div>'
        f'<div style="font-size:0.8rem;font-weight:700;color:#111;margin-bottom:3px;">{name}</div>'
        f'<div style="font-size:0.72rem;color:#555;margin-bottom:5px;line-height:1.4;">{desc}</div>'
        f'{"<div>" + bhtml + "</div>" if bhtml else ""}'
        f'{note_html}'
        f'</div>'
    )


_ARR = '<div style="text-align:center;color:#90A4AE;font-size:1rem;margin:4px 0 2px;">↓ ↓ ↓</div>'

with tab_map:
    st.caption(
        "**SAWA Programme · Theory of Change × CEL Indicator Register** — "
        "v2, corrected against the SAWA Proposal (28 Nov 2025)."
    )

    # ── IMPACT ───────────────────────────────────────────────────────────────
    st.markdown(_card(
        _LC["impact"], "IMPACT",
        "≥60,000 financially disadvantaged young women & PWDs in dignified D&F work",
        "Over 60,000 young women and PWDs engaged in Ghana's fisheries & aquaculture sector "
        "with improved income and long-term economic resilience.",
        sourced=["D&F WORK", "PRODUCTION", "INCOME", "PWD INCLUSION"],
        note="Real sourced commitments with explicit targets (≥86% D&F, 50,000 MT/yr, income vs baseline, "
             "1%→3%→5% PWD ramp). Lack a formal Pl.x ID — a formalisation gap, not a measurement gap.",
    ), unsafe_allow_html=True)

    st.markdown(_ARR, unsafe_allow_html=True)

    # ── OUTCOMES ─────────────────────────────────────────────────────────────
    oc1, oc2, oc3 = st.columns(3)
    with oc1:
        st.markdown(_card(
            _LC["outcome"], "Outcome 1 — Employment",
            "Increased employment opportunities & sustained income",
            "Young women and PWDs in targeted D&F value chains have increased employment "
            "opportunities and sustained income.",
            formal=["PIII.R1", "PII.R5"],
            note="INCOME sits under Outcome 2 in the source, not here — moved.",
        ), unsafe_allow_html=True)
    with oc2:
        st.markdown(_card(
            _LC["outcome"], "Outcome 2 — Enterprise Growth",
            "Sustained enterprise growth, market access & inclusive employment",
            "D&F enterprises supported by SAWA demonstrate sustained growth and strengthened "
            "market access, with inclusive employment of young women and PWDs.",
            formal=["PII.R6", "PII.R7", "PIII.R2", "PIII.R3"],
            sourced=["PRODUCTIVITY", "ENTERPRISE CREATION", "INCOME"],
            note="Renamed ENTERPRISE_SURVIVAL → ENTERPRISE CREATION (source label). "
                 "INCOME moved here from Outcome 1. INPUT & MARKET LINKAGE moved to Outcome 3.",
        ), unsafe_allow_html=True)
    with oc3:
        st.markdown(_card(
            _LC["outcome"], "Outcome 3 — Resilience",
            "Climate-resilient D&F livelihoods & enabling policy ecosystem",
            "D&F livelihoods of young women and PWDs are more climate-resilient, supported "
            "by an enabling policy and investment ecosystem.",
            sourced=["MINDSET & AGENCY", "INPUT & MARKET LINKAGE"],
            note="NOT uncovered — two sourced indicators exist. 'Climate-resilient' wording is new "
                 "vs the Nov 2025 proposal ('resilience, agency and market position'): definition "
                 "mismatch, not absence of measurement.",
        ), unsafe_allow_html=True)

    st.markdown(_ARR, unsafe_allow_html=True)

    # ── INTERMEDIATE OUTCOMES ────────────────────────────────────────────────
    io1, io2, io3 = st.columns(3)
    with io1:
        st.markdown(_card(
            _LC["io"], "Intermediate Outcome 1 — Skills & Agency",
            "Skills, confidence, networks & resources to enter & succeed in D&F",
            "Young women and PWDs have the skills, confidence, networks and initial resources "
            "to enter and succeed in D&F work.",
            formal=["PI.11", "PI.12"],
            sourced=["MINDSET & AGENCY"],
            proposed=["IO1.1"],
            note="IO1.1 is proposed — not in the current register. This whole tier is a Sept 2026 "
                 "elaboration absent from the Nov 2025 source.",
        ), unsafe_allow_html=True)
    with io2:
        st.markdown(_card(
            _LC["io"], "Intermediate Outcome 2 — Anchor Scale & Linkages",
            "Anchor enterprises scale production & value addition with inclusive hiring",
            "Anchor partner enterprises scale production and value addition with inclusive "
            "hiring practices and strengthened market linkages.",
            proposed=["IO2.1"],
            note="IO2.1 is proposed — not in the current register. "
                 "'Inclusive hiring practices' has no indicator at all.",
        ), unsafe_allow_html=True)
    with io3:
        st.markdown(_card(
            _LC["io"], "Intermediate Outcome 3 — Ecosystem",
            "Policy, private investment & coordination enable inclusive enterprise growth",
            "The D&F sector ecosystem — policy, private investment and coordination — "
            "actively enables inclusive and sustainable enterprise growth.",
            proposed=["IO3.1"],
            note="IO3.1 is proposed. STAKEHOLDER & COORDINATION removed from here — "
                 "source places it at Output 4. 'Private investment catalysed' has no indicator anywhere.",
        ), unsafe_allow_html=True)

    st.markdown(_ARR, unsafe_allow_html=True)

    # ── OUTPUTS ──────────────────────────────────────────────────────────────
    op1, op2, op3, op4 = st.columns(4)
    with op1:
        st.markdown(_card(
            _LC["output"], "Output 1 — Capacity",
            "Youth mobilised; BDS & training; cooperatives & PWD mentoring",
            "Youth mobilised; BDS and gender-transformative training delivered; "
            "cooperatives and PWD mentoring established.",
            formal=["PI.1", "PI.3", "PI.9", "PI.10", "PI.11", "PI.12", "PIII.6"],
        ), unsafe_allow_html=True)
    with op2:
        st.markdown(_card(
            _LC["output"], "Output 2 — Production",
            "Fishpond & aquaculture investment; PWDs in production; output & revenue targets",
            "Investment in fishpond and aquaculture facilities; PWDs integrated into "
            "production roles; fish output and revenue targets met.",
            formal=["PII.R6", "PII.R7"],
            note="Facility investment is anchor partner co-investment — not a CEL output indicator in the register.",
        ), unsafe_allow_html=True)
    with op3:
        st.markdown(_card(
            _LC["output"], "Output 3 — Value Addition",
            "Fish processing & trading enterprises; cold-chain; market linkages formalised",
            "Fish processing and trading enterprises supported; cold-chain and storage "
            "established; market linkages formalised.",
            formal=["PIII.6", "PIV.1"],
            note="'Cold-chain and storage established' has no indicator anywhere — "
                 "OP3 measures cooperatives only, not physical infrastructure.",
        ), unsafe_allow_html=True)
    with op4:
        st.markdown(_card(
            _LC["output"], "Output 4 — Ecosystem",
            "Policy & regulatory engagement; private-sector investment; MoUs & cross-learning",
            "Policy and regulatory engagement conducted; private-sector investment catalysed; "
            "MoUs and cross-learning events delivered.",
            formal=["PI.11", "PI.12"],
            sourced=["STAKEHOLDER & COORDINATION"],
            note="STAKEHOLDER & COORDINATION belongs here (source confirms). "
                 "'Private-sector investment catalysed' and 'MoUs' specifically still have no indicator.",
        ), unsafe_allow_html=True)

    st.markdown(_ARR, unsafe_allow_html=True)

    # ── INPUTS ───────────────────────────────────────────────────────────────
    ip1, ip2, ip3, ip4 = st.columns(4)
    with ip1:
        st.markdown(_card(
            _LC["input"], "Input — People & Systems",
            "GYSI officers, safeguarding focal persons, zonal coordinators; HAPPY D&F, GALS/EMAP, PWD toolkit",
            "Full-time GYSI officer in every IP; safeguarding focal persons; zonal coordinators. "
            "HAPPY D&F instrument, GALS/EMAP curricula, PWD toolkit, safeguarding policy.",
        ), unsafe_allow_html=True)
    with ip2:
        st.markdown(_card(
            _LC["input"], "Input — Finance",
            "USD 39.81M total; micro-grants ≤$800; catalytic ≤$8,000; SME facility ≤$16,000",
            "USD 39.81M total (Pillar II 26.78M · III 7.27M · I 2.41M · IV 0.82M · fee 2.58M). "
            "Starter packs $1,000–$1,400.",
        ), unsafe_allow_html=True)
    with ip3:
        st.markdown(_card(
            _LC["input"], "Input — Partners",
            "Agri-Impact (lead), Fisheries Commission, CEL, TechnoServe, R&B, NewAge, Agro Kings",
            "Consortium: Agri-Impact (lead), Fisheries Commission, CEL, TechnoServe, R&B, NewAge, Agro Kings. "
            "Anchors: R&B, AgroKings, Yedent, NewAge, Aglow. Specialists: KNUST, CSIR-FRI, ISP.",
        ), unsafe_allow_html=True)
    with ip4:
        st.markdown(_card(
            _LC["input"], "Input — Systems & Standards",
            "MIS/HAMIS, KoboToolbox, AQUAMIS/E-SAWA, Agribiz; Good Aquaculture Practices, SOPs, two-tier certification",
            "MIS/HAMIS, KoboToolbox, AQUAMIS/E-SAWA, Agribiz, real-time PMU dashboards. "
            "Good Aquaculture Practices, SOPs, two-tier certification, Green Checklist.",
        ), unsafe_allow_html=True)

    # ── Legend ───────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="margin-top:14px;font-size:0.71rem;color:#666;">'
        '<span style="background:#F9A825;color:#000;border-radius:3px;padding:1px 6px;'
        'font-size:0.68rem;font-weight:700;">Pl.x</span>&nbsp;Formal indicator ID (in register)'
        '&emsp;'
        '<span style="background:#E65100;color:#fff;border-radius:3px;padding:1px 6px;'
        'font-size:0.68rem;font-weight:700;">NAME</span>&nbsp;Sourced commitment (no formal ID — formalisation gap)'
        '&emsp;'
        '<span style="background:#E0E0E0;color:#555;border-radius:3px;padding:1px 6px;'
        'font-size:0.68rem;font-style:italic;">IO*</span>&nbsp;Proposed (not in source)'
        '&emsp;📌 Correction from v1'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Refined Finding ──────────────────────────────────────────────────────
    with st.expander("🔍 Refined Finding — The Picture Is Better Than First Thought, But One Structural Gap Is Real"):
        st.markdown("""
**Checked against the authoritative SAWA proposal source (28 Nov 2025):**

Impact and Outcome 3 are **not uncovered** as the earlier version claimed — both carry real, threshold-bearing measurement commitments. They simply lack a formal Pl.x-style indicator ID: a **formalisation gap, not a measurement gap**.

**The one real structural gap:** The source proposal has no 'Intermediate Outcome' tier — it runs Impact → Outcome (3) → Output (4) → Activities → Inputs. The five-tier version with Intermediate Outcomes is a **later elaboration used in the Sept 2026 partner orientation materials**. IO1.1, IO2.1 and IO3.1 remain genuinely proposed — not in any source — because that whole tier is new.

**Remaining true gaps:**
- 'Climate-resilient' at Outcome 3 (Nov 2025 proposal framed it as agency/market-position, not climate)
- 'Inclusive hiring practices' at Intermediate Outcome 2
- Facility investment as a CEL output metric
- Cold-chain/storage infrastructure at Output 3
- 'Private-sector investment catalysed' and 'MoUs' at Output 4

**Two separate actions follow:**
1. Give D&F WORK, PRODUCTION, INCOME, PWD INCLUSION, MINDSET & AGENCY and INPUT & MARKET LINKAGE formal indicator IDs in the register — documentation task, not new data collection.
2. Confirm whether the five-tier ToC (Sept 2026) is now the official structure superseding the Nov 2025 four-tier version. If so, IO1.1–IO3.1 need formal adoption and the 'climate-resilient' reframing of Outcome 3 needs its own new indicator.

*Source: SAWA ToC diagram (partner orientation, Sept 2026) mapped against the SAWA Proposal Document (28 Nov 2025) — s3.2 ToC, s3.3 Pillars, s3.9 Programme Outcomes, s4.1 MEL, s8.1 Budget — and the SMART-revised Logframe. v2 corrects three placement errors and one overstated coverage claim from v1.*
        """)

"""Module I — Strategic Plan 2025-2030

Org-wide dashboard tracking CEL's six 2025-2030 strategic plan targets.
Progress is aggregated automatically across every programme in the database
via strategic_outcome_links (e.g. SAWA's logframe actuals), with a
manual-entry fallback (strategic_outcome_manual) for outcomes no programme
currently tracks in its logframe — see utils/strategic_outcomes.py.

Access: Admin can view and manage manual entries. CEO and Executive
Director (Viewer role) are granted a scoped view-only exception via
view_modules in credentials.yaml/secrets — see can_view_module() in
utils/auth.py. All other Viewers and Editors are denied.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from database.db import init_db, run_query, run_write, insert_returning_id
from utils.auth import can, can_view_module
from utils.strategic_outcomes import STRATEGIC_OUTCOMES, get_outcome_progress

st.set_page_config(page_title="Strategic Plan · CEL MEL", page_icon="🎯", layout="wide")
init_db()

if not st.session_state.get("authentication_status"):
    st.error("Please log in from the main page.")
    st.stop()

if not can_view_module("I"):
    st.error("Access denied — Module I is restricted to CEL Admin, CEO, and Executive Director.")
    st.stop()

is_admin = can("admin")

NAVY = "#0D2B5E"
GOLD = "#C8A951"

st.markdown(
    f'<div style="background:{NAVY};color:white;padding:14px 22px;'
    f'border-left:6px solid {GOLD};border-radius:4px;margin-bottom:4px;">'
    '<span style="font-size:1.4em;font-weight:bold;">🎯 Module I — Strategic Plan 2025-2030</span>'
    f'<span style="color:{GOLD};font-size:0.85em;margin-left:14px;">'
    'Org-wide targets · CEL Admin, CEO, Executive Director</span>'
    '</div>',
    unsafe_allow_html=True,
)
st.caption(
    "Progress is aggregated automatically from every programme's logframe actuals "
    "(via Module E) where a link exists; outcomes with no programme data source "
    "yet rely on the manual entries below."
)


def _fmt(value: float, unit: str) -> str:
    if unit == "USD":
        return f"${value:,.0f}"
    return f"{value:,.0f} {unit}"


progress = get_outcome_progress()

st.markdown("---")
st.markdown("#### Progress toward 2030 targets")

for outcome in STRATEGIC_OUTCOMES:
    code = outcome["code"]
    p = progress[code]
    pct = p["pct"]
    bar_colour = "#2E7D32" if pct >= 75 else "#D97706" if pct >= 35 else "#B71C1C"

    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{outcome['label']}**")
            st.caption(
                f"{_fmt(p['combined_total'], outcome['unit'])} of "
                f"{_fmt(outcome['target'], outcome['unit'])} target"
                + (" · auto-aggregated only" if p["manual_total"] == 0 and p["auto_total"] > 0 else "")
                + (" · manual entries only" if p["auto_total"] == 0 and p["manual_total"] > 0 else "")
                + (" · no data yet" if p["combined_total"] == 0 else "")
            )
            st.progress(min(pct / 100, 1.0))
        with c2:
            st.markdown(
                f'<div style="text-align:right;font-size:1.8em;font-weight:bold;color:{bar_colour};">'
                f'{pct:.1f}%</div>',
                unsafe_allow_html=True,
            )

        if p["breakdown"]:
            with st.expander(f"Contribution breakdown ({len(p['breakdown'])})"):
                bdf = pd.DataFrame(p["breakdown"])
                bdf["value"] = bdf["value"].map(lambda v: _fmt(v, outcome["unit"]))
                bdf = bdf.rename(columns={
                    "source": "Source", "project": "Programme",
                    "label": "Contributor", "value": "Value", "note": "Note",
                })
                st.dataframe(
                    bdf[["Source", "Programme", "Contributor", "Value", "Note"]],
                    hide_index=True, use_container_width=True,
                )
        else:
            st.caption("No programme data linked or manually entered yet for this outcome.")

# ── Admin: manage manual entries (CEO/Exec Director are view-only) ────────────
if is_admin:
    st.markdown("---")
    st.markdown("#### Manage manual entries")
    st.caption(
        "Use this for outcomes with no automatic indicator link (e.g. finance mobilised "
        "outside the logframe, enterprise pilots tracked by a separate team). Each row is "
        "summed once — delete and re-add to correct a value rather than adding a duplicate."
    )

    existing = run_query(
        """
        SELECT som.id, som.outcome_code, som.value, som.note, som.updated_by, som.updated_at,
               p.name AS project_name
        FROM strategic_outcome_manual som
        LEFT JOIN projects p ON p.project_id = som.project_id
        ORDER BY som.updated_at DESC
        """
    )
    if existing:
        for row in existing:
            outcome_label = next((o["label"] for o in STRATEGIC_OUTCOMES if o["code"] == row["outcome_code"]), row["outcome_code"])
            ec1, ec2 = st.columns([5, 1])
            with ec1:
                st.markdown(
                    f"**{row['outcome_code']}** · {outcome_label}  \n"
                    f"{row['project_name'] or 'Org-wide'} — **{row['value']:,.0f}**"
                    + (f" · _{row['note']}_" if row["note"] else "")
                    + f"  \n<span style='color:#757575;font-size:0.8em;'>"
                    f"updated by {row['updated_by'] or 'unknown'} on {row['updated_at']}</span>",
                    unsafe_allow_html=True,
                )
            with ec2:
                if st.button("🗑 Delete", key=f"del_manual_{row['id']}"):
                    run_write("DELETE FROM strategic_outcome_manual WHERE id = :id", {"id": row["id"]})
                    st.rerun()
            st.divider()
    else:
        st.caption("No manual entries yet.")

    projects = run_query("SELECT project_id, name FROM projects ORDER BY name")
    project_options = ["Org-wide (not tied to one programme)"] + [p["name"] for p in projects]

    with st.expander("➕ Add a manual entry"):
        with st.form("add_manual_entry"):
            mc1, mc2 = st.columns(2)
            with mc1:
                outcome_choice = st.selectbox(
                    "Strategic outcome",
                    options=[o["code"] for o in STRATEGIC_OUTCOMES],
                    format_func=lambda c: next(o["label"] for o in STRATEGIC_OUTCOMES if o["code"] == c),
                )
                project_choice = st.selectbox("Programme", options=project_options)
            with mc2:
                value = st.number_input("Value", min_value=0.0, step=1.0)
                note = st.text_input("Note (source of this figure)")

            if st.form_submit_button("Save entry", type="primary"):
                chosen_project_id = None
                if project_choice != project_options[0]:
                    chosen_project_id = next(p["project_id"] for p in projects if p["name"] == project_choice)
                insert_returning_id(
                    """INSERT INTO strategic_outcome_manual
                       (outcome_code, project_id, value, note, updated_by, updated_at)
                       VALUES (:outcome_code, :project_id, :value, :note, :updated_by, :updated_at)""",
                    {
                        "outcome_code": outcome_choice,
                        "project_id":   chosen_project_id,
                        "value":        value,
                        "note":         note or None,
                        "updated_by":   st.session_state.get("name", "Admin"),
                        "updated_at":   datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    },
                )
                st.success("Manual entry saved.")
                st.rerun()

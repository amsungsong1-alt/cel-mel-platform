"""Module J — Partner Visitations

Field-visit hub for the CEL MEAL team and Partner MEAL focal persons.

Tab 1 — Visits:           Schedule and track partner site visits.
Tab 2 — Needs Assessment: Capture M&E capability findings per visit
                          (focal person, tools, disaggregation, overlap risk).
Tab 3 — Evidence:         Upload files and links as verification evidence,
                          tagged to logframe indicators.
Tab 4 — Report:           Generate a narrative LIP reporting summary.
"""
from __future__ import annotations

from datetime import date as _date

import pandas as pd
import streamlit as st

from database.db import init_db, run_query, run_write
from utils.auth import can_write_module
from utils.nav_strip import render_nav_strip
from utils.shared_widgets import project_selector

st.set_page_config(page_title="Partner Visitations — CEL MEL", layout="wide")
init_db()
render_nav_strip("Input")

if not st.session_state.get("authentication_status"):
    st.error("Please log in from the main page.")
    st.stop()

_VISIT_STATUSES = ["Pending", "Scheduled", "Completed", "Cancelled"]

with st.sidebar:
    project_id = project_selector()
    if project_id is None:
        st.stop()
    st.divider()
    st.caption(f"Role: **{st.session_state.get('role', 'Viewer')}**")

# ── Reference data ─────────────────────────────────────────────────────────────
partners = run_query(
    "SELECT partner_id, name, tier FROM partners WHERE project_id=:pid ORDER BY tier, name",
    {"pid": project_id},
)
partner_name_to_id = {p["name"]: p["partner_id"] for p in partners}
partner_id_to_name = {p["partner_id"]: p["name"] for p in partners}

with st.sidebar:
    st.divider()
    st.caption("Visits tab navigation")
    filter_partner = st.selectbox(
        "Filter by partner",
        ["All partners"] + [p["name"] for p in partners],
        key="vf_partner",
        help="Jumps straight to one partner's visits in the Visits tab table below, instead of scrolling through all of them.",
    )
    filter_status = st.selectbox(
        "Filter by status",
        ["All"] + _VISIT_STATUSES,
        key="vf_status",
    )

st.title("Module J — Partner Visitations")
st.caption(
    "SAWA Programme · Sept–Oct 2026 — "
    "Map partner M&E systems, confirm disaggregation, agree data-sharing frequency, flag overlap risks."
)

logframe_rows = run_query(
    """SELECT id, indicator_code, indicator_statement
       FROM logframe_rows WHERE project_id=:pid ORDER BY id""",
    {"pid": project_id},
)
lf_code_to_id = {r["indicator_code"]: r["id"] for r in logframe_rows}
indicator_codes = [r["indicator_code"] for r in logframe_rows]

visits = run_query(
    """SELECT pv.id, pv.partner_id, p.name AS partner_name, pv.visit_date,
              pv.visit_type, pv.conducted_by, pv.status, pv.general_notes
       FROM partner_visits pv
       LEFT JOIN partners p ON p.partner_id = pv.partner_id
       WHERE pv.project_id = :pid
       ORDER BY pv.visit_date DESC""",
    {"pid": project_id},
)

_can_write = can_write_module("J")
_username  = st.session_state.get("username", "MEAL")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_visits, tab_assess, tab_evidence, tab_report = st.tabs(
    ["Visits", "Needs Assessment", "Evidence", "Report"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — VISITS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_visits:
    visible = [
        v for v in visits
        if (filter_partner == "All partners" or v["partner_name"] == filter_partner)
        and (filter_status == "All" or v["status"] == filter_status)
    ]

    _STATUS_COLOUR = {"Pending": "🟡", "Scheduled": "🔵", "Completed": "🟢", "Cancelled": "⚫"}

    if visible:
        st.dataframe(
            pd.DataFrame([
                {
                    "Partner":      v["partner_name"],
                    "Date":         v["visit_date"],
                    "Type":         v["visit_type"] or "—",
                    "Status":       f"{_STATUS_COLOUR.get(v['status'], '')} {v['status']}",
                    "Conducted by": v["conducted_by"] or "—",
                    "Notes":        (v["general_notes"] or "")[:80],
                }
                for v in visible
            ]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No visits match the filter. Schedule one below.")

    st.divider()

    if _can_write:
        with st.expander("Schedule a new visit", expanded=not visits):
            with st.form("new_visit_form"):
                c1, c2 = st.columns(2)
                with c1:
                    nv_partner   = st.selectbox("Partner", [p["name"] for p in partners], key="nv_partner")
                    nv_date      = st.date_input("Visit date", value=_date.today(), key="nv_date")
                with c2:
                    nv_type      = st.selectbox("Visit type", ["In-person", "Remote", "Joint"], key="nv_type", help="'Joint' = conducted together with another partner or CEL team — note which in General notes below.")
                    nv_conducted = st.text_input("Conducted by", value=_username, key="nv_conducted")
                nv_notes = st.text_area("General notes", key="nv_notes", height=80)
                if st.form_submit_button("Schedule visit"):
                    run_write(
                        """INSERT INTO partner_visits
                           (project_id, partner_id, visit_date, visit_type,
                            conducted_by, status, general_notes, created_at)
                           VALUES (:pid, :par, :dt, :vt, :cb, 'Scheduled', :notes, :now)""",
                        {
                            "pid":   project_id,
                            "par":   partner_name_to_id.get(nv_partner),
                            "dt":    str(nv_date),
                            "vt":    nv_type,
                            "cb":    nv_conducted.strip(),
                            "notes": nv_notes.strip() or None,
                            "now":   str(_date.today()),
                        },
                    )
                    st.success("Visit scheduled.")
                    st.rerun()

        if visits:
            with st.expander("Update visit"):
                visit_labels = [
                    f"{v['partner_name']} — {v['visit_date']} ({v['status']})"
                    for v in visits
                ]
                upd_idx = st.selectbox(
                    "Select visit",
                    range(len(visit_labels)),
                    format_func=lambda i: visit_labels[i],
                    key="upd_visit_sel",
                    help="Choosing a visit here pre-fills its current type, conducted by and notes below.",
                )
                upd_visit = visits[upd_idx]
                # Keys include the visit id so each field re-initialises from
                # *this* visit's data when the selection changes — a fixed key
                # would keep showing whatever was last typed for a different
                # visit, since Streamlit widgets ignore value=/index= once
                # their key already has state from a previous rerun.
                _uk = upd_visit["id"]

                with st.form(f"update_visit_form_{_uk}"):
                    uc1, uc2 = st.columns(2)
                    with uc1:
                        new_status = st.selectbox(
                            "Status",
                            _VISIT_STATUSES,
                            index=_VISIT_STATUSES.index(upd_visit["status"])
                            if upd_visit.get("status") in _VISIT_STATUSES else 0,
                            key=f"upd_status_{_uk}",
                        )
                        new_type = st.selectbox(
                            "Visit type",
                            ["In-person", "Remote", "Joint"],
                            index=["In-person", "Remote", "Joint"].index(upd_visit["visit_type"])
                            if upd_visit.get("visit_type") in ["In-person", "Remote", "Joint"] else 0,
                            key=f"upd_type_{_uk}",
                            help="'Joint' = conducted together with another partner or CEL team — note which in General notes below.",
                        )
                    with uc2:
                        new_conducted = st.text_input(
                            "Conducted by",
                            value=upd_visit.get("conducted_by") or "",
                            key=f"upd_conducted_{_uk}",
                        )
                    new_notes = st.text_area(
                        "General notes",
                        value=upd_visit.get("general_notes") or "",
                        key=f"upd_notes_{_uk}",
                        height=80,
                    )
                    if st.form_submit_button("Update visit"):
                        run_write(
                            """UPDATE partner_visits
                               SET status=:s, visit_type=:vt, conducted_by=:cb, general_notes=:notes
                               WHERE id=:id""",
                            {
                                "s": new_status,
                                "vt": new_type,
                                "cb": new_conducted.strip(),
                                "notes": new_notes.strip() or None,
                                "id": upd_visit["id"],
                            },
                        )
                        st.success("Visit updated.")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — NEEDS ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════════
with tab_assess:
    if not visits:
        st.info("No visits yet — schedule one in the Visits tab first.")
    else:
        visit_labels_a = [
            f"{v['partner_name']} — {v['visit_date']} ({v['status']})"
            for v in visits
        ]
        sel_a_idx = st.selectbox(
            "Select visit",
            range(len(visit_labels_a)),
            format_func=lambda i: visit_labels_a[i],
            key="ass_visit_sel",
        )
        sel_a = visits[sel_a_idx]

        existing_f = run_query(
            "SELECT * FROM visit_findings WHERE visit_id=:vid LIMIT 1",
            {"vid": sel_a["id"]},
        )
        ex = existing_f[0] if existing_f else {}

        _cap = "" if _can_write else " (read-only)"
        with st.form(f"needs_assessment_{sel_a['id']}"):
            st.subheader(f"M&E System{_cap}")
            c1, c2 = st.columns(2)
            with c1:
                f_focal   = st.text_input("M&E focal person",           value=ex.get("mel_focal_person") or "")
                f_tools   = st.text_area("Existing data collection tools", value=ex.get("existing_tools") or "", height=90)
                f_freq    = st.text_input("Reporting frequency",         value=ex.get("reporting_frequency") or "")
            with c2:
                f_email   = st.text_input("Contact (email / phone)",     value=ex.get("mel_focal_email") or "")
                f_storage = st.text_area("Data storage method",          value=ex.get("data_storage") or "", height=90)
                f_format  = st.text_input("Reporting format",            value=ex.get("reporting_format") or "",
                                          help="e.g. Excel, KoboToolbox, Paper register")

            st.divider()
            st.subheader("Disaggregation Capability")
            _opts = ["Y", "N", "Partial"]
            dc1, dc2, dc3, dc4 = st.columns(4)
            with dc1:
                f_sex  = st.selectbox("By sex",             _opts,
                                      index=_opts.index(ex["disagg_sex"])        if ex.get("disagg_sex")        in _opts else 1, key="da_sex")
            with dc2:
                f_age  = st.selectbox("By age",             _opts,
                                      index=_opts.index(ex["disagg_age"])        if ex.get("disagg_age")        in _opts else 1, key="da_age")
            with dc3:
                f_dis  = st.selectbox("By disability",      _opts,
                                      index=_opts.index(ex["disagg_disability"]) if ex.get("disagg_disability") in _opts else 1, key="da_dis")
            with dc4:
                f_vc   = st.selectbox("By value-chain node",_opts,
                                      index=_opts.index(ex["disagg_value_chain"])if ex.get("disagg_value_chain")in _opts else 1, key="da_vc")

            st.divider()
            st.subheader("SAWA Indicators — Confirmed Figures")
            confirmed_default = [
                c.strip() for c in (ex.get("indicators_confirmed") or "").split(",")
                if c.strip() and c.strip() in indicator_codes
            ]
            f_confirmed = st.multiselect(
                "Indicators for which partner can supply confirmed figures",
                indicator_codes,
                default=confirmed_default,
                help="Only select indicators this partner's own M&E system can actually produce a verified number for — not every indicator they're relevant to.",
            )
            f_discrepancies = st.text_area(
                "Discrepancies / gaps found",
                value=ex.get("discrepancies_found") or "",
                height=80,
            )

            st.divider()
            st.subheader("Double-Counting Risk")
            rc1, rc2 = st.columns([1, 2])
            with rc1:
                _risk_opts = ["Low", "Medium", "High"]
                f_risk = st.selectbox(
                    "Overlap risk level", _risk_opts,
                    index=_risk_opts.index(ex["overlap_risk"]) if ex.get("overlap_risk") in _risk_opts else 0,
                    key="da_risk",
                    help="Risk that this partner's reported participants/results double-count with another partner serving the same communities — not a general risk rating.",
                )
            with rc2:
                f_communities = st.text_area("Communities / sites served", value=ex.get("communities_served") or "", height=72)
            f_overlap_notes = st.text_area("Overlap notes", value=ex.get("overlap_notes") or "", height=72, help="Specifically which other partner(s) might overlap here, and what's being done to avoid double-counting — feeds Module A's cross-partner checks.")

            st.divider()
            st.subheader("Agreed MEAL Support")
            f_support = st.text_input(
                "Support type",
                value=ex.get("support_agreed") or "",
                help="e.g. Training, Shared tool, Indicator definitions, None",
            )
            f_support_notes = st.text_area("Details", value=ex.get("support_notes") or "", height=80)

            saved = st.form_submit_button("Save findings", disabled=not _can_write)
            if saved:
                params = {
                    "vid":    sel_a["id"],
                    "fp":     f_focal.strip(),
                    "fe":     f_email.strip(),
                    "tools":  f_tools.strip(),
                    "stor":   f_storage.strip(),
                    "freq":   f_freq.strip(),
                    "fmt":    f_format.strip(),
                    "sex":    f_sex,
                    "age":    f_age,
                    "dis":    f_dis,
                    "vc":     f_vc,
                    "conf":   ",".join(f_confirmed),
                    "disc":   f_discrepancies.strip(),
                    "comm":   f_communities.strip(),
                    "risk":   f_risk,
                    "onotes": f_overlap_notes.strip(),
                    "supp":   f_support.strip(),
                    "snotes": f_support_notes.strip(),
                }
                if ex:
                    run_write("""
                        UPDATE visit_findings
                        SET mel_focal_person=:fp,  mel_focal_email=:fe,
                            existing_tools=:tools, data_storage=:stor,
                            reporting_frequency=:freq, reporting_format=:fmt,
                            disagg_sex=:sex, disagg_age=:age,
                            disagg_disability=:dis, disagg_value_chain=:vc,
                            indicators_confirmed=:conf, discrepancies_found=:disc,
                            communities_served=:comm, overlap_risk=:risk, overlap_notes=:onotes,
                            support_agreed=:supp, support_notes=:snotes
                        WHERE visit_id=:vid
                    """, params)
                else:
                    run_write("""
                        INSERT INTO visit_findings
                        (visit_id, mel_focal_person, mel_focal_email, existing_tools,
                         data_storage, reporting_frequency, reporting_format,
                         disagg_sex, disagg_age, disagg_disability, disagg_value_chain,
                         indicators_confirmed, discrepancies_found,
                         communities_served, overlap_risk, overlap_notes,
                         support_agreed, support_notes)
                        VALUES
                        (:vid, :fp, :fe, :tools, :stor, :freq, :fmt,
                         :sex, :age, :dis, :vc, :conf, :disc,
                         :comm, :risk, :onotes, :supp, :snotes)
                    """, params)
                st.success("Findings saved.")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — EVIDENCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_evidence:
    if not visits:
        st.info("No visits yet — schedule one in the Visits tab first.")
    else:
        visit_labels_e = [
            f"{v['partner_name']} — {v['visit_date']} ({v['status']})"
            for v in visits
        ]
        sel_e_idx = st.selectbox(
            "Select visit",
            range(len(visit_labels_e)),
            format_func=lambda i: visit_labels_e[i],
            key="ev_visit_sel",
        )
        sel_e = visits[sel_e_idx]

        evidence_rows = run_query(
            """SELECT ve.id, ve.label, lr.indicator_code,
                      ve.link_url, ve.file_name, ve.uploaded_by, ve.uploaded_at
               FROM visit_evidence ve
               LEFT JOIN logframe_rows lr ON lr.id = ve.logframe_row_id
               WHERE ve.visit_id = :vid
               ORDER BY ve.id""",
            {"vid": sel_e["id"]},
        )

        if evidence_rows:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Label":         e["label"],
                        "Indicator":     e["indicator_code"] or "—",
                        "Link / File":   e.get("link_url") or e.get("file_name") or "—",
                        "Uploaded by":   e["uploaded_by"] or "—",
                        "Date":          (e["uploaded_at"] or "")[:10],
                    }
                    for e in evidence_rows
                ]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No evidence uploaded for this visit yet.")

        st.divider()

        if _can_write:
            with st.expander("Add evidence", expanded=True):
                with st.form("add_evidence_form"):
                    ev_label = st.text_input(
                        "Label",
                        help="e.g. 'Participant register Q1 2026', 'Kobo data export'",
                    )
                    ev_indicator = st.selectbox(
                        "Link to indicator (optional)",
                        ["None"] + [
                            f"[{r['indicator_code']}] {r['indicator_statement'][:70]}"
                            for r in logframe_rows
                        ],
                        key="ev_indicator",
                    )
                    ev_link = st.text_input(
                        "URL / link (leave blank if uploading a file)"
                    )
                    ev_file = st.file_uploader(
                        "Upload file",
                        type=["pdf", "xlsx", "xls", "csv", "png", "jpg", "docx"],
                        key="ev_file",
                    )

                    if st.form_submit_button("Add evidence"):
                        if not ev_label.strip():
                            st.warning("Please enter a label.")
                        else:
                            lf_id = None
                            if ev_indicator != "None":
                                code = ev_indicator.lstrip("[").split("]")[0]
                                lf_id = lf_code_to_id.get(code)

                            fn, fm, fd = None, None, None
                            if ev_file is not None:
                                fn = ev_file.name
                                fm = ev_file.type
                                fd = ev_file.read()

                            run_write(
                                """INSERT INTO visit_evidence
                                   (visit_id, project_id, logframe_row_id, label,
                                    link_url, file_name, file_mime, file_data,
                                    uploaded_by, uploaded_at)
                                   VALUES (:vid, :pid, :lf, :lbl, :url,
                                           :fn, :fm, :fd, :by, :at)""",
                                {
                                    "vid": sel_e["id"],
                                    "pid": project_id,
                                    "lf":  lf_id,
                                    "lbl": ev_label.strip(),
                                    "url": ev_link.strip() or None,
                                    "fn":  fn, "fm": fm, "fd": fd,
                                    "by":  _username,
                                    "at":  str(_date.today()),
                                },
                            )
                            st.success("Evidence added.")
                            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — REPORT
# ═══════════════════════════════════════════════════════════════════════════════
with tab_report:
    completed_visits = [v for v in visits if v["status"] == "Completed"]
    if not completed_visits:
        st.info(
            "No completed visits yet. "
            "Mark a visit as Completed in the Visits tab to generate a report."
        )
    else:
        comp_labels = [
            f"{v['partner_name']} — {v['visit_date']}" for v in completed_visits
        ]
        sel_r_idx = st.selectbox(
            "Select completed visit",
            range(len(comp_labels)),
            format_func=lambda i: comp_labels[i],
            key="rpt_visit_sel",
        )
        sel_r = completed_visits[sel_r_idx]

        findings = run_query(
            "SELECT * FROM visit_findings WHERE visit_id=:vid LIMIT 1",
            {"vid": sel_r["id"]},
        )
        f = findings[0] if findings else {}

        ev_for_report = run_query(
            """SELECT ve.label, lr.indicator_code, ve.link_url, ve.file_name
               FROM visit_evidence ve
               LEFT JOIN logframe_rows lr ON lr.id = ve.logframe_row_id
               WHERE ve.visit_id = :vid ORDER BY ve.id""",
            {"vid": sel_r["id"]},
        )

        def _yn(val: str | None) -> str:
            return {"Y": "Yes", "N": "No", "Partial": "Partial"}.get(val or "", "—")

        confirmed_codes = [
            c.strip() for c in (f.get("indicators_confirmed") or "").split(",")
            if c.strip()
        ]

        lines = [
            "PARTNER VISITATION REPORT",
            "=" * 60,
            f"Partner:       {sel_r['partner_name']}",
            f"Visit date:    {sel_r['visit_date']}",
            f"Visit type:    {sel_r['visit_type'] or '—'}",
            f"Conducted by:  {sel_r['conducted_by'] or '—'}",
            "",
            "1. PARTNER M&E SYSTEM",
            "─" * 40,
            f"M&E focal person:  {f.get('mel_focal_person') or '—'}",
            f"Contact:           {f.get('mel_focal_email') or '—'}",
            f"Existing tools:    {f.get('existing_tools') or '—'}",
            f"Data storage:      {f.get('data_storage') or '—'}",
            f"Reporting cycle:   {f.get('reporting_frequency') or '—'}",
            f"Reporting format:  {f.get('reporting_format') or '—'}",
            "",
            "2. DISAGGREGATION CAPABILITY",
            "─" * 40,
            f"By sex:              {_yn(f.get('disagg_sex'))}",
            f"By age:              {_yn(f.get('disagg_age'))}",
            f"By disability:       {_yn(f.get('disagg_disability'))}",
            f"By value-chain node: {_yn(f.get('disagg_value_chain'))}",
            "",
            "3. SAWA INDICATORS — CONFIRMED FIGURES",
            "─" * 40,
        ]
        if confirmed_codes:
            for code in confirmed_codes:
                lines.append(f"  [{code}]")
        else:
            lines.append("  None confirmed yet.")
        lines += [
            "",
            "Discrepancies / gaps:",
            f"  {f.get('discrepancies_found') or 'None noted.'}",
            "",
            "4. DOUBLE-COUNTING RISK",
            "─" * 40,
            f"Risk level:         {f.get('overlap_risk') or '—'}",
            f"Communities served: {f.get('communities_served') or '—'}",
            f"Overlap notes:      {f.get('overlap_notes') or '—'}",
            "",
            "5. AGREED MEAL SUPPORT",
            "─" * 40,
            f"Support type: {f.get('support_agreed') or '—'}",
            f"Details:      {f.get('support_notes') or '—'}",
            "",
            "6. EVIDENCE ATTACHED",
            "─" * 40,
        ]
        if ev_for_report:
            for e in ev_for_report:
                ind = f"[{e['indicator_code']}] " if e.get("indicator_code") else ""
                src = e.get("link_url") or e.get("file_name") or ""
                lines.append(f"  {ind}{e['label']}" + (f"  →  {src}" if src else ""))
        else:
            lines.append("  No evidence attached.")

        if sel_r.get("general_notes"):
            lines += ["", "7. GENERAL NOTES", "─" * 40, sel_r["general_notes"]]

        report_text = "\n".join(lines)

        st.text_area(
            "Narrative report",
            value=report_text,
            height=540,
            label_visibility="collapsed",
        )
        st.download_button(
            "Download report (.txt)",
            data=report_text,
            file_name=(
                f"visit_report_{sel_r['partner_name'].replace(' ', '_')}"
                f"_{sel_r['visit_date']}.txt"
            ),
            mime="text/plain",
        )
        st.caption(
            "Copy and paste into the LIP quarterly narrative template, "
            "or download and attach to the reporting pack."
        )

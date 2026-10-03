"""Module L — Quarterly Report Prep

Structured data entry and aggregation for the sections of the SAWA
quarterly narrative report that MEAL owns or supplies data for.

MEAL owns outright (fully in this module):
  §3.1  Quarterly MEL activities
  §3.3  Training outcomes assessment
  §3.4  Monitoring tools and methodology
  §3.5  Data storage
  §6.1  Learnings
  §6.2  Influencing points for Mastercard Foundation
  §7    Technical reconciliation (target vs achieved, tilapia/catfish)
  Summary table totals

MEAL supplies data for (this module provides the evidence views):
  §2.1  Gender (counts, incidents, agency, PWD)
  §2.3  Value addition (BDS completions, YiW)
  §2.4  Ecosystem / WAN
  §5    Risk (data quality)
"""
import io
from datetime import date, datetime
import streamlit as st
import pandas as pd

from database.db import init_db, run_query, run_write
from utils.shared_widgets import project_selector
from utils.auth import can_write_module
from utils.nav_strip import render_nav_strip
from utils.fiscal_calendar import current_fiscal_year

st.set_page_config(page_title="Quarterly Report — CEL MEL", layout="wide")

# ── Brand ─────────────────────────────────────────────────────────────────────
NAVY = "#4A5568"
GOLD = "#F5A820"
TEAL = "#1E7E76"
CLAY = "#B96A2E"
SAGE = "#4A6B5C"

st.markdown(
    f"""
    <style>
    .qr-badge-own {{
        background:#E7F3F1; color:{TEAL}; padding:2px 10px; border-radius:12px;
        font-size:0.75em; font-weight:700; display:inline-block;
    }}
    .qr-badge-supply {{
        background:#FBF3DF; color:#7A5A10; padding:2px 10px; border-radius:12px;
        font-size:0.75em; font-weight:700; display:inline-block;
    }}
    .qr-section-head {{
        border-left:4px solid {GOLD}; padding:2px 0 2px 12px; margin:18px 0 8px 0;
    }}
    .qr-note {{
        background:#F6F3EC; border-left:3px solid #8A9494; border-radius:6px;
        padding:8px 14px; font-size:0.82em; color:#5E6A6A; margin:6px 0;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

init_db()
render_nav_strip("Input")

# ── Auth ──────────────────────────────────────────────────────────────────────
if not st.session_state.get("authentication_status"):
    st.error("Please log in from the main page.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    project_id = project_selector()
    if project_id is None:
        st.stop()
    st.divider()
    _fy_options = [2026, 2027, 2028, 2029]
    _fy = st.selectbox("Fiscal year (start)", _fy_options,
                       index=_fy_options.index(current_fiscal_year())
                       if current_fiscal_year() in _fy_options else 0)
    _qtr = st.selectbox("Quarter", [1, 2, 3, 4],
                        format_func=lambda q: {
                            1: "Q1 Jul–Sep", 2: "Q2 Oct–Dec",
                            3: "Q3 Jan–Mar", 4: "Q4 Apr–Jun",
                        }[q])
    st.divider()
    st.caption(f"Role: **{st.session_state.get('role', 'Viewer')}**")

_can_write = can_write_module("L")
_user = st.session_state.get("name") or st.session_state.get("username") or "Unknown"
_now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# ── Partners lookup ────────────────────────────────────────────────────────────
_partners = run_query(
    "SELECT partner_id, name FROM partners WHERE project_id=:pid ORDER BY name",
    {"pid": project_id},
)
_partner_map = {p["partner_id"]: p["name"] for p in _partners}
_partner_names = ["(none)"] + [p["name"] for p in _partners]

st.title("Module L — Quarterly Report Prep")
st.caption(
    f"Q{_qtr} FY {_fy}/{str(_fy+1)[-2:]} · "
    "Structured data for the sections MEAL owns or supplies. "
    "Use the sidebar to switch quarter and fiscal year."
)

# ── Tabs ──────────────────────────────────────────────────────────────────────
(
    tab_summary,
    tab_participants,
    tab_mel_activities,
    tab_outcomes,
    tab_learnings,
    tab_recon,
    tab_supply,
) = st.tabs([
    "Summary Table",
    "Participant Register",
    "§3.1 MEL Activities",
    "§3.3 Outcomes",
    "§6 Learnings",
    "§7 Reconciliation",
    "Data Supply",
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — SUMMARY TABLE
# ─────────────────────────────────────────────────────────────────────────────
with tab_summary:
    st.markdown(
        '<div class="qr-section-head"><b>Report Summary Table</b> '
        '<span class="qr-badge-own">MEAL owns</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Live totals pulled from the Participant Register and Module E actuals. "
        "These feed the summary table at the top of the quarterly narrative report."
    )

    # ── Counts from Participant Register ──────────────────────────────────────
    _pr_all = run_query(
        "SELECT * FROM participant_register WHERE project_id=:pid AND fiscal_year=:fy",
        {"pid": project_id, "fy": _fy},
    )
    _pr_q = [r for r in _pr_all if r.get("quarter") == _qtr]

    def _cnt(rows, **filters):
        result = rows
        for k, v in filters.items():
            result = [r for r in result if r.get(k) == v]
        return len(result)

    # ── Module E actuals for key indicators ───────────────────────────────────
    _rda_rows = run_query(
        """
        SELECT lr.indicator_code, rda.actual_q1, rda.actual_q2,
               rda.actual_q3, rda.actual_q4, rda.target_value
        FROM raw_data_analysis rda
        JOIN logframe_rows lr ON lr.id = rda.logframe_row_id
        WHERE rda.project_id=:pid AND (rda.reporting_year=:fy OR rda.reporting_year IS NULL)
          AND rda.partner_id IS NULL
        """,
        {"pid": project_id, "fy": _fy},
    )
    _rda = {r["indicator_code"]: r for r in _rda_rows}

    def _rda_val(code, col):
        r = _rda.get(code)
        if not r:
            return "—"
        v = r.get(col) or ""
        return v if v else "—"

    _q_col = f"actual_q{_qtr}"

    # ── Summary tiles ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    _weo_val = _rda_val("PI.1", _q_col)
    _bds_val = _rda_val("PI.3", _q_col)
    _yiw_val = _rda_val("PIII.R1", _q_col)
    _pwd_val = _rda_val("PII.R5", _q_col)

    _reg_female = _cnt(_pr_q, sex="Female")
    _reg_pwd = _cnt(_pr_q, is_pwd="Y")
    _reg_wan = _cnt(_pr_q, wan_member="Y")
    _reg_total = len(_pr_q)

    with c1:
        st.metric("WEO / Mobilised (Module E PI.1)", _weo_val,
                  help="From raw_data_analysis PI.1 programme-wide aggregate")
    with c2:
        st.metric("BDS / Trained (PI.3)", _bds_val)
    with c3:
        st.metric("Youth in Work (PIII.R1)", _yiw_val)
    with c4:
        st.metric("PWDs in Work (PII.R5)", _pwd_val)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric("Registered in Register (Q)", str(_reg_total))
    with c6:
        st.metric("Female (Register)", str(_reg_female))
    with c7:
        st.metric("PWDs (Register)", str(_reg_pwd))
    with c8:
        st.metric("WAN members (Register)", str(_reg_wan))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Geographic reach ──────────────────────────────────────────────────────
    st.markdown("**Geographic reach (from Participant Register)**")
    if _pr_all:
        _regions = {r["region"] for r in _pr_all if r.get("region")}
        _districts = {r["district"] for r in _pr_all if r.get("district")}
        _communities = {r["community"] for r in _pr_all if r.get("community")}
        gc1, gc2, gc3 = st.columns(3)
        with gc1:
            st.metric("Regions", len(_regions))
        with gc2:
            st.metric("Districts", len(_districts))
        with gc3:
            st.metric("Communities", len(_communities))
    else:
        st.info("No participants registered yet. Add participants in the Participant Register tab.")

    st.markdown(
        '<div class="qr-note">⚠ <strong>Fish type breakdown</strong> '
        '(tilapia vs catfish) for YiW and revenue indicators is entered in '
        'the §7 Reconciliation tab, not here.</div>',
        unsafe_allow_html=True,
    )

    # ── §3.4 Tools & §3.5 Storage ─────────────────────────────────────────────
    st.divider()
    st.markdown(
        '<div class="qr-section-head"><b>§3.4 Monitoring Tools</b> '
        '<span class="qr-badge-own">MEAL owns</span></div>',
        unsafe_allow_html=True,
    )
    st.caption("Tools CEL uses and their rationale — drawn from the Data Collection Plan.")

    _tools = run_query(
        """SELECT instrument_name, stakeholder, frequency, responsible_party,
                  instrument_status, journey_step, rationale
           FROM data_collection_plan
           WHERE project_id=:pid AND instrument_name IS NOT NULL
           ORDER BY journey_step, instrument_name""",
        {"pid": project_id},
    )
    if _tools:
        _tools_df = pd.DataFrame(_tools).rename(columns={
            "instrument_name": "Instrument",
            "stakeholder": "Data source / Stakeholder",
            "frequency": "Frequency",
            "responsible_party": "Responsible",
            "instrument_status": "Status",
            "journey_step": "Journey step",
            "rationale": "Why this tool",
        })
        st.dataframe(_tools_df, hide_index=True, use_container_width=True,
                     column_config={
                         "Instrument": st.column_config.TextColumn(width="medium"),
                         "Why this tool": st.column_config.TextColumn(width="large"),
                     })
    else:
        st.info("Data Collection Plan not yet populated (Module C).")

    st.divider()
    st.markdown(
        '<div class="qr-section-head"><b>§3.5 Data Storage</b> '
        '<span class="qr-badge-own">MEAL owns</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Raw data is stored in **KoboToolbox** (field instruments). "
        "Exports, processed data and reports are filed in the **CEL SharePoint / OneDrive** folder. "
        "Paste your SharePoint link below and it will appear in the report."
    )
    _storage_key = f"storage_link_{project_id}_{_fy}"
    _storage_link = st.text_input(
        "SharePoint / OneDrive folder URL",
        value=st.session_state.get(_storage_key, ""),
        key=_storage_key,
        placeholder="https://celglobal.sharepoint.com/sites/SAWA/...",
        disabled=not _can_write,
    )
    if _storage_link:
        st.markdown(f"→ [Open data folder]({_storage_link})", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — PARTICIPANT REGISTER
# ─────────────────────────────────────────────────────────────────────────────
with tab_participants:
    st.markdown(
        '<div class="qr-section-head"><b>Participant Register</b> '
        '<span class="qr-badge-own">MEAL owns</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "One row per participant. Captures the breakdowns the quarterly report requires: "
        "fish type (tilapia/catfish), location type, employment status at entry, "
        "primary/secondary, and refugee/displaced status."
    )

    _pr_rows = run_query(
        """SELECT pr.*, p.name AS partner_name
           FROM participant_register pr
           LEFT JOIN partners p ON p.partner_id = pr.partner_id
           WHERE pr.project_id=:pid AND pr.fiscal_year=:fy AND pr.quarter=:q
           ORDER BY pr.registration_date DESC, pr.id DESC""",
        {"pid": project_id, "fy": _fy, "q": _qtr},
    )

    # ── Summary counts ─────────────────────────────────────────────────────────
    if _pr_rows:
        _df_pr = pd.DataFrame(_pr_rows)
        rc1, rc2, rc3, rc4, rc5 = st.columns(5)
        with rc1:
            st.metric("Total Q registrations", len(_pr_rows))
        with rc2:
            st.metric("Female", len([r for r in _pr_rows if r.get("sex") == "Female"]))
        with rc3:
            st.metric("PWD", len([r for r in _pr_rows if r.get("is_pwd") == "Y"]))
        with rc4:
            st.metric("WAN members", len([r for r in _pr_rows if r.get("wan_member") == "Y"]))
        with rc5:
            ft = pd.DataFrame(_pr_rows)["fish_type"].value_counts()
            st.metric("Tilapia", int(ft.get("Tilapia", 0)))

        # Fish type breakdown
        _fish_counts = pd.DataFrame(_pr_rows)["fish_type"].value_counts().reset_index()
        _fish_counts.columns = ["Fish type", "Count"]
        _loc_counts = pd.DataFrame(_pr_rows)["location_type"].value_counts().reset_index()
        _loc_counts.columns = ["Location type", "Count"]
        f1, f2 = st.columns(2)
        with f1:
            st.markdown("**Fish type**")
            st.dataframe(_fish_counts, hide_index=True, use_container_width=True)
        with f2:
            st.markdown("**Location type**")
            st.dataframe(_loc_counts, hide_index=True, use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Register table ─────────────────────────────────────────────────────────
    if _pr_rows:
        _display_cols = [
            "participant_code", "registration_date", "partner_name", "sex",
            "age_group", "is_pwd", "fish_type", "location_type", "region",
            "community", "employment_status", "primary_secondary",
            "intervention_type", "progression_stage", "wan_member", "refugee_displaced",
        ]
        _df_display = pd.DataFrame(_pr_rows)[
            [c for c in _display_cols if c in pd.DataFrame(_pr_rows).columns]
        ]
        st.dataframe(_df_display, hide_index=True, use_container_width=True)

        # CSV export
        _csv = _df_display.to_csv(index=False)
        st.download_button(
            "⬇ Download register CSV",
            data=_csv,
            file_name=f"participants_Q{_qtr}_FY{_fy}.csv",
            mime="text/csv",
        )
    else:
        st.info(f"No participants registered for Q{_qtr} FY{_fy}/{str(_fy+1)[-2:]} yet.")

    # ── Add participant form ────────────────────────────────────────────────────
    if _can_write:
        with st.expander("➕ Register new participant", expanded=False):
            with st.form("add_participant"):
                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    _p_code = st.text_input("Participant code / Kobo ID *",
                                            placeholder="e.g. SAWA-2026-001")
                    _p_date = st.date_input("Registration date *", value=date.today())
                    _p_partner = st.selectbox("Partner", _partner_names)
                    _p_sex = st.selectbox("Sex", ["Female", "Male", "Prefer not to say"])
                    _p_age = st.selectbox("Age group", ["18-24", "25-29", "30-35", "35+", "Under 18"])
                with fc2:
                    _p_fish = st.selectbox("Fish type *", ["Tilapia", "Catfish", "Both", "Other"])
                    _p_loc = st.selectbox("Location type *", ["Rural", "Urban", "Peri-urban"])
                    _p_region = st.text_input("Region")
                    _p_district = st.text_input("District")
                    _p_community = st.text_input("Community")
                with fc3:
                    _p_emp = st.selectbox("Employment status at entry",
                                          ["New", "Improved", "Additional"])
                    _p_ps = st.selectbox("Primary / Secondary", ["Primary", "Secondary"])
                    _p_int = st.selectbox("Intervention type",
                                          ["BDS", "WAN", "Safeguarding", "Coaching",
                                           "E-SAWA", "Starter pack", "Other"])
                    _p_stage = st.selectbox("Progression stage (MCF)",
                                            ["WEO", "YIW", "D&F"])
                    _p_youth = st.radio("Youth (18–35)?", ["Y", "N"], horizontal=True)
                    _p_pwd = st.radio("PWD?", ["Y", "N"], horizontal=True)
                    _p_wan = st.radio("WAN member?", ["Y", "N"], horizontal=True)
                    _p_refugee = st.selectbox("Refugee/displaced", ["N", "Y", "Unknown"])
                _p_notes = st.text_area("Notes (optional)")
                if st.form_submit_button("Register participant"):
                    if not _p_code.strip():
                        st.error("Participant code is required.")
                    else:
                        _pid_fk = next(
                            (p["partner_id"] for p in _partners if p["name"] == _p_partner),
                            None,
                        )
                        run_write(
                            """INSERT INTO participant_register
                               (project_id, partner_id, participant_code, registration_date,
                                fiscal_year, quarter, sex, age_group, is_youth, is_pwd,
                                refugee_displaced, fish_type, location_type, region,
                                district, community, employment_status, primary_secondary,
                                intervention_type, progression_stage, wan_member,
                                registered_by, notes, created_at)
                               VALUES
                               (:pid, :par, :code, :dt, :fy, :q, :sex, :age, :youth, :pwd,
                                :refugee, :fish, :loc, :region, :district, :community,
                                :emp, :ps, :int, :stage, :wan, :by, :notes, :now)""",
                            {
                                "pid": project_id, "par": _pid_fk,
                                "code": _p_code.strip(), "dt": str(_p_date),
                                "fy": _fy, "q": _qtr, "sex": _p_sex, "age": _p_age,
                                "youth": _p_youth, "pwd": _p_pwd, "refugee": _p_refugee,
                                "fish": _p_fish, "loc": _p_loc, "region": _p_region,
                                "district": _p_district, "community": _p_community,
                                "emp": _p_emp, "ps": _p_ps, "int": _p_int,
                                "stage": _p_stage, "wan": _p_wan,
                                "by": _user, "notes": _p_notes, "now": _now,
                            },
                        )
                        st.success("Participant registered.")
                        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — §3.1 MEL ACTIVITIES
# ─────────────────────────────────────────────────────────────────────────────
with tab_mel_activities:
    st.markdown(
        '<div class="qr-section-head"><b>§3.1 Quarterly MEL Activities</b> '
        '<span class="qr-badge-own">MEAL owns</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "One row per MEL activity: field visits, FGDs, partner visits, Kobo form reviews, "
        "pre/post tests, data quality checks. Feeds Section 3.1 of the quarterly narrative report."
    )
    st.markdown(
        '<div class="qr-note">The template says: one row per MEL activity, with location, '
        'objective and key findings. Evidence sources: field visit notes, Adabraka-style FGDs, '
        'partner visits, Kobo submissions.</div>',
        unsafe_allow_html=True,
    )

    _ma_rows = run_query(
        """SELECT ma.*, p.name AS partner_name
           FROM mel_activities ma
           LEFT JOIN partners p ON p.partner_id = ma.partner_id
           WHERE ma.project_id=:pid AND ma.fiscal_year=:fy AND ma.quarter=:q
           ORDER BY ma.activity_date DESC""",
        {"pid": project_id, "fy": _fy, "q": _qtr},
    )

    if _ma_rows:
        _ma_df = pd.DataFrame(_ma_rows)[[
            "activity_date", "activity_type", "location", "partner_name",
            "objective", "participants", "key_findings", "follow_up", "conducted_by",
        ]]
        st.dataframe(
            _ma_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "objective":    st.column_config.TextColumn("Objective", width="large"),
                "key_findings": st.column_config.TextColumn("Key findings", width="large"),
            },
        )
        _ma_csv = _ma_df.to_csv(index=False)
        st.download_button(
            "⬇ Download §3.1 CSV",
            data=_ma_csv,
            file_name=f"mel_activities_Q{_qtr}_FY{_fy}.csv",
            mime="text/csv",
        )
    else:
        st.info(f"No MEL activities logged for Q{_qtr} FY{_fy}/{str(_fy+1)[-2:]} yet.")

    if _can_write:
        with st.expander("➕ Log MEL activity", expanded=not _ma_rows):
            with st.form("add_mel_activity"):
                ma1, ma2 = st.columns(2)
                with ma1:
                    _ma_date = st.date_input("Activity date *", value=date.today())
                    _ma_type = st.selectbox(
                        "Activity type *",
                        ["Field visit", "FGD", "Partner visit", "Kobo review",
                         "Pre/post test", "Data quality check", "Learning session", "Other"],
                    )
                    _ma_loc = st.text_input("Location (region/district/community)")
                    _ma_partner = st.selectbox("Partner (if applicable)", _partner_names)
                    _ma_by = st.text_input("Conducted by", value=_user)
                with ma2:
                    _ma_obj = st.text_area("Objective *", height=80)
                    _ma_parts = st.text_input("Participants / roles involved")
                    _ma_findings = st.text_area("Key findings", height=80)
                    _ma_followup = st.text_area("Follow-up actions", height=60)
                if st.form_submit_button("Log activity"):
                    if not _ma_obj.strip():
                        st.error("Objective is required.")
                    else:
                        _ma_pid = next(
                            (p["partner_id"] for p in _partners if p["name"] == _ma_partner),
                            None,
                        )
                        run_write(
                            """INSERT INTO mel_activities
                               (project_id, activity_date, quarter, fiscal_year,
                                activity_type, location, partner_id, objective,
                                participants, key_findings, follow_up, conducted_by, created_at)
                               VALUES
                               (:pid,:dt,:q,:fy,:type,:loc,:par,:obj,:parts,:findings,:fu,:by,:now)""",
                            {
                                "pid": project_id, "dt": str(_ma_date),
                                "q": _qtr, "fy": _fy, "type": _ma_type,
                                "loc": _ma_loc, "par": _ma_pid, "obj": _ma_obj.strip(),
                                "parts": _ma_parts, "findings": _ma_findings,
                                "fu": _ma_followup, "by": _ma_by, "now": _now,
                            },
                        )
                        st.success("Activity logged.")
                        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — §3.3 TRAINING OUTCOMES
# ─────────────────────────────────────────────────────────────────────────────
with tab_outcomes:
    st.markdown(
        '<div class="qr-section-head"><b>§3.3 Training Outcomes Assessment</b> '
        '<span class="qr-badge-own">MEAL owns</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Records skills adoption results from pre/post tests, phone calls and field follow-ups. "
        "Report asks: skills adopted, number adopting (by sex, value chain, location), "
        "adoption rate, and method used."
    )
    st.markdown(
        '<div class="qr-note">Evidence sources: PMU pre/post test, follow-up phone calls '
        '(baseline phone-call questionnaire), field visits.</div>',
        unsafe_allow_html=True,
    )

    # Derive outcomes from participant register where possible
    _pr_q_rows = run_query(
        """SELECT pr.*, p.name AS partner_name
           FROM participant_register pr
           LEFT JOIN partners p ON p.partner_id = pr.partner_id
           WHERE pr.project_id=:pid AND pr.fiscal_year=:fy AND pr.quarter=:q""",
        {"pid": project_id, "fy": _fy, "q": _qtr},
    )

    if _pr_q_rows:
        st.markdown("**Participant-level breakdown (from Register)**")
        _df_pr_q = pd.DataFrame(_pr_q_rows)

        # By intervention + sex
        if "intervention_type" in _df_pr_q.columns and "sex" in _df_pr_q.columns:
            _by_int = _df_pr_q.groupby(["intervention_type", "sex"]).size().unstack(
                fill_value=0
            ).reset_index()
            st.dataframe(_by_int, hide_index=True, use_container_width=True)

        # By fish type + intervention
        if "fish_type" in _df_pr_q.columns and "intervention_type" in _df_pr_q.columns:
            _by_fish = _df_pr_q.groupby(["fish_type", "intervention_type"]).size().unstack(
                fill_value=0
            ).reset_index()
            st.dataframe(_by_fish, hide_index=True, use_container_width=True)

        # By location type
        if "location_type" in _df_pr_q.columns:
            _by_loc = _df_pr_q.groupby("location_type").size().reset_index(name="Count")
            st.dataframe(_by_loc, hide_index=True, use_container_width=True)

    st.divider()
    st.markdown("**Manual outcomes entries** (pre/post test results, adoption rates not in register)")

    _outcomes_rows = run_query(
        """SELECT * FROM mel_activities
           WHERE project_id=:pid AND fiscal_year=:fy AND quarter=:q
             AND activity_type='Pre/post test'
           ORDER BY activity_date DESC""",
        {"pid": project_id, "fy": _fy, "q": _qtr},
    )

    if _outcomes_rows:
        st.markdown(f"**{len(_outcomes_rows)} pre/post test activities logged in §3.1:**")
        for _r in _outcomes_rows:
            st.markdown(
                f"- **{_r['activity_date']}** · {_r.get('location','N/A')} · "
                f"{_r.get('key_findings','')}"
            )
    else:
        st.info(
            "No pre/post test activities logged yet. "
            "Add them in §3.1 MEL Activities (activity type = Pre/post test) "
            "and the findings will appear here."
        )

    st.markdown(
        '<div class="qr-note">For a structured adoption-rate table, use the field visit '
        'notes from §3.1 and the pre/post test scores from Kobo (Module D sync). '
        'The adoption rate = (# correctly applying skill after) / (# assessed) × 100.</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — §6 LEARNINGS & INFLUENCING POINTS
# ─────────────────────────────────────────────────────────────────────────────
with tab_learnings:
    st.markdown(
        '<div class="qr-section-head"><b>§6.1 Learnings & §6.2 Influencing Points</b> '
        '<span class="qr-badge-own">MEAL owns</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "§6.1 programme learnings from the quarter. "
        "§6.2 three to five influencing points for Mastercard Foundation, each with a reason."
    )

    _lrn_rows = run_query(
        """SELECT * FROM learnings
           WHERE project_id=:pid AND fiscal_year=:fy AND quarter=:q
           ORDER BY learning_type, id""",
        {"pid": project_id, "fy": _fy, "q": _qtr},
    )

    _learnings_only = [r for r in _lrn_rows if r.get("learning_type") == "Learning"]
    _inf_points = [r for r in _lrn_rows if r.get("learning_type") == "Influencing point"]

    st_l, st_i = st.tabs(["§6.1 Learnings", "§6.2 Influencing Points"])

    # ── §6.1 Learnings ────────────────────────────────────────────────────────
    with st_l:
        if _learnings_only:
            for _r in _learnings_only:
                with st.container(border=True):
                    st.markdown(f"**{_r.get('category', 'General')}**")
                    st.markdown(_r["statement"])
                    if _r.get("evidence"):
                        st.caption(f"Evidence: {_r['evidence']}")
                    if _r.get("implication"):
                        st.caption(f"Implication: {_r['implication']}")
        else:
            st.info(f"No learnings logged for Q{_qtr} FY{_fy} yet.")

        if _can_write:
            with st.expander("➕ Add learning", expanded=not _learnings_only):
                with st.form("add_learning"):
                    _lrn_cat = st.text_input("Category / theme",
                                              placeholder="e.g. Data quality, BDS delivery")
                    _lrn_stmt = st.text_area("Learning statement *", height=80)
                    _lrn_ev = st.text_area("Evidence (what supports this)", height=60)
                    _lrn_impl = st.text_area("Implication (so what?)", height=60)
                    if st.form_submit_button("Add learning"):
                        if not _lrn_stmt.strip():
                            st.error("Statement is required.")
                        else:
                            run_write(
                                """INSERT INTO learnings
                                   (project_id, quarter, fiscal_year, learning_type,
                                    category, statement, evidence, implication,
                                    created_by, created_at)
                                   VALUES (:pid,:q,:fy,'Learning',:cat,:stmt,:ev,:impl,:by,:now)""",
                                {
                                    "pid": project_id, "q": _qtr, "fy": _fy,
                                    "cat": _lrn_cat, "stmt": _lrn_stmt.strip(),
                                    "ev": _lrn_ev, "impl": _lrn_impl,
                                    "by": _user, "now": _now,
                                },
                            )
                            st.success("Learning added.")
                            st.rerun()

    # ── §6.2 Influencing Points ───────────────────────────────────────────────
    with st_i:
        st.caption(
            "3–5 influencing points: each must state the point AND the reason it matters "
            "to Mastercard Foundation (e.g. adaptive management, inclusion gap, scale insight)."
        )
        if _inf_points:
            for _i, _r in enumerate(_inf_points, 1):
                with st.container(border=True):
                    st.markdown(f"**Point {_i}: {_r.get('category', '')}**")
                    st.markdown(_r["statement"])
                    if _r.get("reason"):
                        st.caption(f"Reason for MCF: {_r['reason']}")
                    if _r.get("evidence"):
                        st.caption(f"Evidence: {_r['evidence']}")
        else:
            st.info(f"No influencing points logged for Q{_qtr} FY{_fy} yet.")

        if len(_inf_points) >= 5:
            st.warning("5 influencing points already logged. The template asks for 3–5.")

        if _can_write:
            with st.expander("➕ Add influencing point", expanded=not _inf_points):
                with st.form("add_inf_point"):
                    _ip_cat = st.text_input("Topic / theme",
                                             placeholder="e.g. PWD inclusion, fish type data")
                    _ip_stmt = st.text_area("Influencing point *", height=80)
                    _ip_reason = st.text_area(
                        "Why this matters to Mastercard Foundation *", height=60
                    )
                    _ip_ev = st.text_input("Evidence source")
                    if st.form_submit_button("Add influencing point"):
                        if not _ip_stmt.strip() or not _ip_reason.strip():
                            st.error("Statement and reason are both required.")
                        else:
                            run_write(
                                """INSERT INTO learnings
                                   (project_id, quarter, fiscal_year, learning_type,
                                    category, statement, evidence, reason,
                                    audience, created_by, created_at)
                                   VALUES (:pid,:q,:fy,'Influencing point',
                                           :cat,:stmt,:ev,:reason,'Mastercard Foundation',:by,:now)""",
                                {
                                    "pid": project_id, "q": _qtr, "fy": _fy,
                                    "cat": _ip_cat, "stmt": _ip_stmt.strip(),
                                    "ev": _ip_ev, "reason": _ip_reason.strip(),
                                    "by": _user, "now": _now,
                                },
                            )
                            st.success("Influencing point added.")
                            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6 — §7 TECHNICAL RECONCILIATION
# ─────────────────────────────────────────────────────────────────────────────
with tab_recon:
    st.markdown(
        '<div class="qr-section-head"><b>§7 Technical Reconciliation</b> '
        '<span class="qr-badge-own">MEAL owns</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Target vs achieved for Q1–Q4 and cumulative, with tilapia/catfish breakdown "
        "for fish-related indicators. Edit actuals in the table below."
    )
    st.markdown(
        '<div class="qr-note"><strong>CEL fills:</strong> Youth in Work (100), Female YiW, '
        'PWDs YiW (8), Trained/WEO (500), PWDs trained, Revenue (PIII.R3), '
        'Starter packs (I.10 = 0). Fish produced/traded (PIII.R2, 115.74 MT) — CEL\'s '
        'slice is value-addition trading only. Tilapia and catfish are reported separately '
        'for PIII.R2 and PIII.R3.</div>',
        unsafe_allow_html=True,
    )

    # ── Seed default CEL indicators if not yet in qr_actuals ─────────────────
    _CEL_INDICATORS = [
        ("I.1",      "Youth mobilised / WEO",                        "persons",   "500"),
        ("I.3",      "Women receiving BDS / Trained",                 "persons",   "500"),
        ("I.13",     "PWD mentors identified",                        "persons",   "8"),
        ("I.17",     "Women in coaching & mentorship",                "persons",   "500"),
        ("I.18",     "Women-led cooperatives/clusters strengthened",  "groups",    "25"),
        ("I.20",     "Safeguarding trained (incl. focal persons)",    "persons",   "500"),
        ("I.10",     "Starter packs distributed",                     "packs",     "0"),
        ("PIII.R1",  "D&F jobs in value addition (YiW)",             "jobs",      "100"),
        ("PII.R5",   "PWDs accessing D&F work (programme-wide)",     "jobs",      "8"),
        ("PIII.R2",  "Fish produced/traded (value addition, MT)",    "MT",        "115.74"),
        ("PIII.R3",  "Revenue, value-added trading",                  "USD",       "208,333"),
        ("PII.R7",   "Revenue generated by PWDs in D&F",             "USD",       "16,667"),
    ]

    for _code, _label, _unit, _target in _CEL_INDICATORS:
        run_write(
            """INSERT INTO qr_actuals
               (project_id, fiscal_year, indicator_code, indicator_label, unit, target_y1)
               VALUES (:pid, :fy, :code, :label, :unit, :target)
               ON CONFLICT(project_id, fiscal_year, indicator_code) DO NOTHING""",
            {
                "pid": project_id, "fy": _fy,
                "code": _code, "label": _label,
                "unit": _unit, "target": _target,
            },
        )

    # ── Load reconciliation rows ───────────────────────────────────────────────
    _qra_rows = run_query(
        """SELECT * FROM qr_actuals
           WHERE project_id=:pid AND fiscal_year=:fy
           ORDER BY indicator_code""",
        {"pid": project_id, "fy": _fy},
    )

    # ── Build display dataframe with variance ─────────────────────────────────
    def _to_num(v):
        if not v or v == "—":
            return None
        try:
            return float(str(v).replace(",", ""))
        except (ValueError, TypeError):
            return None

    _recon_display = []
    for _r in _qra_rows:
        _tgt = _to_num(_r.get("target_y1"))
        _q1  = _to_num(_r.get("actual_q1"))
        _q2  = _to_num(_r.get("actual_q2"))
        _q3  = _to_num(_r.get("actual_q3"))
        _q4  = _to_num(_r.get("actual_q4"))
        _qs  = [v for v in [_q1, _q2, _q3, _q4] if v is not None]
        _cum = sum(_qs) if _qs else None
        _var = (_cum - _tgt) if (_cum is not None and _tgt is not None) else None
        _pct = (100 * _cum / _tgt) if (_cum is not None and _tgt and _tgt != 0) else None
        _recon_display.append({
            "Code": _r["indicator_code"],
            "Indicator": _r["indicator_label"],
            "Unit": _r.get("unit", ""),
            "Year 1 Target": _r.get("target_y1", ""),
            "Q1 Actual": _r.get("actual_q1") or "",
            "Q1 Tilapia": _r.get("actual_q1_tilapia") or "",
            "Q1 Catfish": _r.get("actual_q1_catfish") or "",
            "Q2 Actual": _r.get("actual_q2") or "",
            "Q3 Actual": _r.get("actual_q3") or "",
            "Q4 Actual": _r.get("actual_q4") or "",
            "Cumulative": f"{_cum:,.2f}" if _cum is not None else "",
            "Variance": f"{_var:+,.2f}" if _var is not None else "",
            "% Achieved": f"{_pct:.1f}%" if _pct is not None else "",
            "Notes": _r.get("notes") or "",
        })

    _recon_df = pd.DataFrame(_recon_display)
    st.dataframe(_recon_df, hide_index=True, use_container_width=True,
                 column_config={
                     "Indicator": st.column_config.TextColumn(width="large"),
                     "Notes": st.column_config.TextColumn(width="medium"),
                 })

    # CSV export
    _recon_csv = _recon_df.to_csv(index=False)
    st.download_button(
        "⬇ Download §7 reconciliation CSV",
        data=_recon_csv,
        file_name=f"reconciliation_FY{_fy}.csv",
        mime="text/csv",
    )

    # ── Edit actuals ──────────────────────────────────────────────────────────
    if _can_write:
        st.divider()
        st.markdown("**Edit actuals**")
        st.caption(
            "Select an indicator to update its quarterly actuals. "
            "For PIII.R2 and PIII.R3, enter tilapia and catfish values separately."
        )
        _recon_labels = [f"{r['indicator_code']} — {r['indicator_label']}"
                         for r in _qra_rows]
        _sel_label = st.selectbox("Select indicator", _recon_labels)
        _sel_row = _qra_rows[_recon_labels.index(_sel_label)] if _sel_label else None

        if _sel_row:
            _needs_fish = _sel_row["indicator_code"] in ("PIII.R2", "PIII.R3", "PIII.R1")
            with st.form("edit_recon"):
                er1, er2, er3, er4 = st.columns(4)
                with er1:
                    st.markdown("**Q1**")
                    _eq1 = st.text_input("Q1 actual", value=_sel_row.get("actual_q1") or "")
                    if _needs_fish:
                        _eq1t = st.text_input("Q1 Tilapia", value=_sel_row.get("actual_q1_tilapia") or "")
                        _eq1c = st.text_input("Q1 Catfish", value=_sel_row.get("actual_q1_catfish") or "")
                    else:
                        _eq1t, _eq1c = "", ""
                with er2:
                    st.markdown("**Q2**")
                    _eq2 = st.text_input("Q2 actual", value=_sel_row.get("actual_q2") or "")
                    if _needs_fish:
                        _eq2t = st.text_input("Q2 Tilapia", value=_sel_row.get("actual_q2_tilapia") or "")
                        _eq2c = st.text_input("Q2 Catfish", value=_sel_row.get("actual_q2_catfish") or "")
                    else:
                        _eq2t, _eq2c = "", ""
                with er3:
                    st.markdown("**Q3**")
                    _eq3 = st.text_input("Q3 actual", value=_sel_row.get("actual_q3") or "")
                    if _needs_fish:
                        _eq3t = st.text_input("Q3 Tilapia", value=_sel_row.get("actual_q3_tilapia") or "")
                        _eq3c = st.text_input("Q3 Catfish", value=_sel_row.get("actual_q3_catfish") or "")
                    else:
                        _eq3t, _eq3c = "", ""
                with er4:
                    st.markdown("**Q4**")
                    _eq4 = st.text_input("Q4 actual", value=_sel_row.get("actual_q4") or "")
                    if _needs_fish:
                        _eq4t = st.text_input("Q4 Tilapia", value=_sel_row.get("actual_q4_tilapia") or "")
                        _eq4c = st.text_input("Q4 Catfish", value=_sel_row.get("actual_q4_catfish") or "")
                    else:
                        _eq4t, _eq4c = "", ""
                _enotes = st.text_input("Notes", value=_sel_row.get("notes") or "")
                if st.form_submit_button("💾 Save actuals"):
                    run_write(
                        """UPDATE qr_actuals
                           SET actual_q1=:q1, actual_q1_tilapia=:q1t, actual_q1_catfish=:q1c,
                               actual_q2=:q2, actual_q2_tilapia=:q2t, actual_q2_catfish=:q2c,
                               actual_q3=:q3, actual_q3_tilapia=:q3t, actual_q3_catfish=:q3c,
                               actual_q4=:q4, actual_q4_tilapia=:q4t, actual_q4_catfish=:q4c,
                               notes=:notes, updated_by=:by, updated_at=:now
                           WHERE project_id=:pid AND fiscal_year=:fy
                             AND indicator_code=:code""",
                        {
                            "q1": _eq1, "q1t": _eq1t, "q1c": _eq1c,
                            "q2": _eq2, "q2t": _eq2t, "q2c": _eq2c,
                            "q3": _eq3, "q3t": _eq3t, "q3c": _eq3c,
                            "q4": _eq4, "q4t": _eq4t, "q4c": _eq4c,
                            "notes": _enotes, "by": _user, "now": _now,
                            "pid": project_id, "fy": _fy,
                            "code": _sel_row["indicator_code"],
                        },
                    )
                    st.success("Actuals saved.")
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 7 — DATA SUPPLY
# ─────────────────────────────────────────────────────────────────────────────
with tab_supply:
    st.markdown(
        '<div class="qr-section-head"><b>Data Supply — What MEAL Provides to Other Sections</b> '
        '<span class="qr-badge-supply">MEAL supplies</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "MEAL provides the numbers; another team writes these sections. "
        "Use this tab to check what data is available and what is still missing."
    )

    _supply_sections = [
        {
            "section": "§2.1.1 Gender table & incidents",
            "owner": "Gender Lead writes",
            "mel_provides": "Training counts and outcomes by sex. PWD-related incidents (at least 1 per quarter).",
            "where": "Participant Register → sex column; MEL Activities → FGD findings; Review Log.",
            "check": len([r for r in _pr_rows if r.get("sex") == "Female"]) > 0
            if _pr_rows else False,
        },
        {
            "section": "§2.1.2 Safeguarding checklist",
            "owner": "Gender & Safeguarding Lead writes",
            "mel_provides": "Trained counts (I.9: 25 focal persons, I.20: 500 women), complaints received and cases managed.",
            "where": "Participant Register → intervention_type = Safeguarding; Module F Review Log.",
            "check": len([r for r in _pr_rows if r.get("intervention_type") == "Safeguarding"]) > 0
            if _pr_rows else False,
        },
        {
            "section": "§2.1.3 Youth voice & agency",
            "owner": "Gender Lead writes",
            "mel_provides": "Agency and self-efficacy results; short qualitative examples from FGDs.",
            "where": "MEL Activities → FGD findings (activity_type = FGD); outcome harvesting notes.",
            "check": len([r for r in _ma_rows if r.get("activity_type") == "FGD"]) > 0
            if _ma_rows else False,
        },
        {
            "section": "§2.1.4 PWD inclusion",
            "owner": "Gender Lead writes",
            "mel_provides": "PWD mentor register (I.13: 8 mentors), barriers observed, accessibility measures.",
            "where": "Participant Register → is_pwd = Y AND progression_stage = YiW; §7 Reconciliation I.13.",
            "check": len([r for r in _pr_rows if r.get("is_pwd") == "Y"]) > 0
            if _pr_rows else False,
        },
        {
            "section": "§2.3 Value addition (BDS, YiW, businesses)",
            "owner": "BDS & Programme team writes",
            "mel_provides": "BDS completions by sex, jobs by primary/secondary, income proof reference.",
            "where": "Participant Register → intervention_type = BDS; §7 Reconciliation PIII.R1.",
            "check": len([r for r in _pr_rows if r.get("intervention_type") == "BDS"]) > 0
            if _pr_rows else False,
        },
        {
            "section": "§2.4 WAN",
            "owner": "Gender Lead & Programme team write",
            "mel_provides": "WAN members count, forums attended, ambassadors, bootcamps.",
            "where": "Participant Register → wan_member = Y; MEL Activities where objective mentions WAN.",
            "check": len([r for r in _pr_rows if r.get("wan_member") == "Y"]) > 0
            if _pr_rows else False,
        },
        {
            "section": "§2.5.1 E-SAWA",
            "owner": "Programme team writes",
            "mel_provides": "Digital literacy completions (PIV.5: 500 target).",
            "where": "Participant Register → intervention_type = E-SAWA; §7 PIV.5 (add if needed).",
            "check": len([r for r in _pr_rows if r.get("intervention_type") == "E-SAWA"]) > 0
            if _pr_rows else False,
        },
        {
            "section": "§5 Risk",
            "owner": "Programme Lead writes",
            "mel_provides": 'Data quality and double-counting risk evidence ("limited external evidence" risk is MEAL\'s).',
            "where": "Module F Review Log; participant overlap check; DQA stage in Module E.",
            "check": False,
        },
        {
            "section": "§8.1–8.3 Levers, challenges, unintended outcomes",
            "owner": "Programme Lead writes",
            "mel_provides": "Qualitative examples with evidence: FGD notes, field visit findings, outcome harvesting.",
            "where": "MEL Activities → key_findings; §6 Learnings (implication field).",
            "check": len(_ma_rows) > 0 if _ma_rows else False,
        },
    ]

    for _s in _supply_sections:
        _status_badge = (
            '<span style="background:#D1FAE5;color:#065F46;padding:1px 8px;'
            'border-radius:10px;font-size:0.73em;">✓ Data available</span>'
            if _s["check"] else
            '<span style="background:#FEE2E2;color:#991B1B;padding:1px 8px;'
            'border-radius:10px;font-size:0.73em;">⚠ Data needed</span>'
        )
        with st.expander(
            f"{_s['section']} — {_s['owner']}", expanded=not _s["check"]
        ):
            st.markdown(
                f"{_status_badge}",
                unsafe_allow_html=True,
            )
            st.markdown(f"**MEAL provides:** {_s['mel_provides']}")
            st.markdown(f"**Where to find it:** {_s['where']}")

    st.divider()
    st.markdown("**Open notes from the template**")
    st.markdown(
        """
- **§3.2 Work with Anchor Partners**: appears in the ToC but has no heading in the template body —
  confirm with Agri-Impact whether it is a section MEAL needs to contribute to.
- **Investment leveraged**: the §7 reconciliation table has this row, but CEL has no tool to
  capture it. If TechnoServe grants to CEL-referred women count, request the amounts directly
  from TechnoServe.
- **Section 4 (Communication)**: owned by Communications. MEAL's only role is checking that
  story numbers match the data and that participant consent for stories is documented.
        """
    )

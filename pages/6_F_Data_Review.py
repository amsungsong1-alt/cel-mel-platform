"""Module F — Data Review

Structured review-scheduling and review-log tool organised around the seven
CEL MEAL review question types (Process, Performance, Assumption, Stakeholder,
Problem, Solution, Attribution).

Key behaviours
--------------
• Seven review_protocol rows drive a self-maintaining schedule: after each
  logged review, next_scheduled_date auto-advances by review_frequency.
• Overdue detection: if next_scheduled_date is in the past with no matching
  review_log entry filed after it, the protocol is highlighted red.
• Logging a review with follow_up_required = 'Y' surfaces a direct link to
  Module G seeded with the linked indicator IDs.
• Protocol fields are Admin-only; the review log is open to Editor/Admin.
"""
from __future__ import annotations

import calendar
from datetime import date

import pandas as pd
import streamlit as st

from database.db import init_db, run_query, run_write, insert_returning_id
from utils.shared_widgets import project_selector
from utils.auth import can, can_write_module
from utils.nav_strip import render_nav_strip

st.set_page_config(page_title="Data Review — CEL MEL", layout="wide")
init_db()
render_nav_strip("Review")

if not st.session_state.get("authentication_status"):
    st.error("Please log in from the main page.")
    st.stop()

with st.sidebar:
    project_id = project_selector()
    if project_id is None:
        st.stop()
    st.divider()
    st.caption(f"Role: **{st.session_state.get('role', 'Viewer')}**")

# ── Constants ─────────────────────────────────────────────────────────────────
FREQ_MONTHS = {
    "Monthly":   1,
    "Quarterly": 3,
    "Bi-annual": 6,
    "Annual":    12,
}

DT_ICONS = {
    "Performance":  "📊",
    "Assumption":   "🔮",
    "Stakeholder":  "🤝",
    "Process":      "⚙️",
    "Problem":      "⚠️",
    "Solution":     "💡",
    "Attribution":  "🔗",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _advance_date(current: str, frequency: str) -> str:
    """Advance a YYYY-MM-DD string by the given frequency."""
    try:
        d = date.fromisoformat(current)
    except (ValueError, TypeError):
        return current
    add_months = FREQ_MONTHS.get(frequency, 3)
    month = d.month + add_months
    year  = d.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    day   = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day).isoformat()


def _countdown(date_str: str | None) -> tuple[str, str]:
    """Return (display label, CSS hex background) for a date string."""
    if not date_str:
        return "Not scheduled", "#F5F5F5"
    try:
        d     = date.fromisoformat(date_str)
        delta = (d - date.today()).days
    except (ValueError, TypeError):
        return date_str, "#F5F5F5"

    if delta < 0:
        return f"⛔ OVERDUE by {abs(delta)} day(s)", "#FFEBEE"
    if delta == 0:
        return "⚠️ Due TODAY", "#FFF8E1"
    if delta <= 7:
        return f"⚠️ Due in {delta} day(s)", "#FFF8E1"
    if delta <= 30:
        return f"Due in {delta} day(s)", "#E8F5E9"
    return f"Due in {delta} day(s)", "#FFFFFF"


def _is_overdue(protocol: dict) -> bool:
    """True if next_scheduled_date has passed with no log entry covering it."""
    nsd = protocol.get("next_scheduled_date")
    if not nsd:
        return False
    try:
        if date.fromisoformat(nsd) >= date.today():
            return False
    except ValueError:
        return False
    covered = run_query(
        """SELECT id FROM review_log
           WHERE  protocol_id = :pid AND conducted_date >= :nsd
           LIMIT  1""",
        {"pid": protocol["id"], "nsd": nsd},
    )
    return len(covered) == 0


def _load_protocols() -> list[dict]:
    return run_query(
        """SELECT id, data_type, review_scope, existing_info_source,
                  actual_info_source, issue_definition, review_frequency,
                  reviewer_role, next_scheduled_date
           FROM   review_protocols
           WHERE  project_id = :pid
           ORDER  BY CASE data_type
               WHEN 'Performance'  THEN 1
               WHEN 'Assumption'   THEN 2
               WHEN 'Stakeholder'  THEN 3
               WHEN 'Process'      THEN 4
               WHEN 'Problem'      THEN 5
               WHEN 'Solution'     THEN 6
               WHEN 'Attribution'  THEN 7
               ELSE 8 END""",
        {"pid": project_id},
    )


def _load_log(limit: int = 100) -> list[dict]:
    return run_query(
        """SELECT rl.id, rp.data_type, rl.conducted_date, rl.conducted_by,
                  rl.summary, rl.red_flags_found, rl.linked_indicator_ids,
                  rl.follow_up_required
           FROM   review_log rl
           JOIN   review_protocols rp ON rp.id = rl.protocol_id
           WHERE  rp.project_id = :pid
           ORDER  BY rl.conducted_date DESC
           LIMIT  :lim""",
        {"pid": project_id, "lim": limit},
    )


# ── Load logframe rows for the indicator multi-select ─────────────────────────
lf_rows = run_query(
    """SELECT id, indicator_code, indicator_statement
       FROM   logframe_rows
       WHERE  project_id = :pid
       ORDER  BY id""",
    {"pid": project_id},
)
lf_by_id = {r["id"]: r for r in lf_rows}
lf_options = []
lf_id_for_opt: dict[str, int] = {}
for r in lf_rows:
    stmt = r.get("indicator_statement") or ""
    label = (
        f"{r['indicator_code']} — {stmt[:60]}…"
        if len(stmt) > 60
        else f"{r['indicator_code']} — {stmt}"
    )
    lf_options.append(label)
    lf_id_for_opt[label] = r["id"]

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE
# ═══════════════════════════════════════════════════════════════════════════════
st.title("Module F — Data Review")
st.caption(
    "Structured review schedule for all seven SAWA data types. "
    "Protocols define the what, where, who and how-often; the log records "
    "every conducted review and maintains an audit trail of findings and "
    "follow-up actions."
)

protocols = _load_protocols()

if not protocols:
    st.info(
        "No review protocols found. "
        "Run `python -m database.seed_sawa` to load the SAWA review protocols."
    )
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Review Protocols (7 expandable cards)
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📋 Review Protocols")
if not can("admin"):
    st.caption(
        "Protocol content is set by Admins. "
        "Contact your MEAL lead to request changes."
    )

for proto in protocols:
    dt      = proto["data_type"]
    icon    = DT_ICONS.get(dt, "📌")
    label, _bg = _countdown(proto.get("next_scheduled_date"))
    overdue = _is_overdue(proto)
    od_tag  = "  ⛔ OVERDUE" if overdue else ""

    with st.expander(
        f"{icon} **{dt}** — {proto.get('reviewer_role', '—')}  ·  {label}{od_tag}",
        expanded=overdue,
    ):
        if can("admin"):
            with st.form(key=f"proto_form_{proto['id']}"):
                q1 = st.text_area(
                    "1. Review scope — what is being reviewed?",
                    value=proto.get("review_scope") or "",
                    height=80,
                )
                q2 = st.text_area(
                    "2. Existing information source",
                    value=proto.get("existing_info_source") or "",
                    height=70,
                )
                q3 = st.text_area(
                    "3. Actual / current information source",
                    value=proto.get("actual_info_source") or "",
                    height=70,
                )
                q4 = st.text_area(
                    "4. Issue / red-flag definition",
                    value=proto.get("issue_definition") or "",
                    height=70,
                )
                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    freq_opts = list(FREQ_MONTHS.keys())
                    q5 = st.selectbox(
                        "5. Review frequency",
                        options=freq_opts,
                        index=(
                            freq_opts.index(proto["review_frequency"])
                            if proto.get("review_frequency") in freq_opts
                            else 1
                        ),
                        key=f"freq_{proto['id']}",
                    )
                with fc2:
                    q6 = st.text_input(
                        "6. Reviewer role",
                        value=proto.get("reviewer_role") or "",
                        key=f"role_{proto['id']}",
                    )
                with fc3:
                    nsd_val = proto.get("next_scheduled_date") or ""
                    try:
                        nsd_date = date.fromisoformat(nsd_val)
                    except (ValueError, TypeError):
                        nsd_date = date.today()
                    q7 = st.date_input(
                        "7. Next scheduled date",
                        value=nsd_date,
                        key=f"nsd_{proto['id']}",
                    )

                if st.form_submit_button("💾 Save protocol", type="primary"):
                    run_write(
                        """UPDATE review_protocols
                           SET review_scope          = :scope,
                               existing_info_source  = :existing,
                               actual_info_source    = :actual,
                               issue_definition      = :issue,
                               review_frequency      = :freq,
                               reviewer_role         = :role,
                               next_scheduled_date   = :nsd
                           WHERE id = :id""",
                        {
                            "scope":    q1, "existing": q2, "actual": q3,
                            "issue":    q4, "freq":     q5, "role":   q6,
                            "nsd":      q7.isoformat(),
                            "id":       proto["id"],
                        },
                    )
                    st.success("Protocol saved.")
                    st.rerun()

        else:
            fields = [
                ("1. Review scope",                proto.get("review_scope")),
                ("2. Existing information source", proto.get("existing_info_source")),
                ("3. Actual information source",   proto.get("actual_info_source")),
                ("4. Issue / red-flag definition", proto.get("issue_definition")),
                ("5. Review frequency",            proto.get("review_frequency")),
                ("6. Reviewer role",               proto.get("reviewer_role")),
                ("7. Next scheduled date",         proto.get("next_scheduled_date")),
            ]
            for f_label, val in fields:
                st.markdown(f"**{f_label}**")
                st.write(val or "—")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Upcoming Reviews Calendar
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📅 Upcoming Reviews")
st.caption(
    "Sorted by next scheduled date.  "
    "Red rows are overdue — a review is due but no log entry has been filed."
)

cal_rows: list[dict] = []
for p in sorted(protocols, key=lambda x: x.get("next_scheduled_date") or "9999"):
    cnt_label, bg = _countdown(p.get("next_scheduled_date"))
    cal_rows.append({
        "Type":            f"{DT_ICONS.get(p['data_type'], '')} {p['data_type']}",
        "Reviewer":        p.get("reviewer_role") or "—",
        "Frequency":       p.get("review_frequency") or "—",
        "Scheduled":       p.get("next_scheduled_date") or "—",
        "Status":          cnt_label,
        "_bg":             bg,
    })

cal_df     = pd.DataFrame(cal_rows)
display_df = cal_df.drop(columns=["_bg"])
bg_list    = cal_df["_bg"].tolist()

def _cal_row_style(row) -> list[str]:
    return [f"background-color:{bg_list[row.name]};"] * len(row)

try:
    styled_cal = display_df.style.apply(_cal_row_style, axis=1)
except Exception:
    styled_cal = display_df

st.dataframe(styled_cal, hide_index=True, use_container_width=True)

overdue_types = [p["data_type"] for p in protocols if _is_overdue(p)]
if overdue_types:
    st.error(
        f"⛔ **{len(overdue_types)} overdue review(s):** "
        + ", ".join(overdue_types)
        + " — log an entry below to clear the flag."
    )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Log a Review
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📝 Log a Review")

if not can_write_module("F"):
    st.info("Viewer access: review logging requires Editor or Admin role.")
else:
    proto_map = {p["data_type"]: p for p in protocols}

    # Data-type picker outside the form so the issue-definition hint updates live
    sel_c1, sel_c2 = st.columns([1, 2])
    with sel_c1:
        selected_dt = st.selectbox(
            "Data type (review protocol)",
            options=[p["data_type"] for p in protocols],
            key="log_dt_select",
        )
    selected_proto = proto_map.get(selected_dt, {})
    with sel_c2:
        if selected_proto.get("issue_definition"):
            st.info(
                f"**Red-flag definition:** {selected_proto['issue_definition']}"
            )

    with st.form("log_review_form", clear_on_submit=True):
        d1, d2 = st.columns(2)
        with d1:
            conducted_date = st.date_input("Date conducted", value=date.today())
        with d2:
            conducted_by = st.text_input(
                "Conducted by",
                placeholder="e.g. Ama Mensah (MEAL Officer)",
            )

        summary = st.text_area(
            "Review summary",
            placeholder=(
                "What did the review find? Key data points checked, "
                "comparison against targets, overall assessment."
            ),
            height=100,
        )
        red_flags = st.text_area(
            "Red flags found (leave blank if none)",
            placeholder=(
                "Describe each red flag: which indicator, what the data shows, "
                "why it meets the issue definition."
            ),
            height=80,
        )
        linked_opts = st.multiselect(
            "Indicators this review touched (from Module E)",
            options=lf_options,
            placeholder="Select one or more logframe indicators…",
        )
        fu_required = st.radio(
            "Follow-up required?",
            options=["N", "Y"],
            horizontal=True,
            help=(
                "Select Y if a red flag requires a decision report in Module G. "
                "You will be prompted with a direct link after saving."
            ),
        )

        submitted = st.form_submit_button("💾 Save review log", type="primary")

    if submitted:
        proto = proto_map.get(selected_dt)
        if not proto:
            st.error("No protocol found for the selected data type.")
        elif not conducted_by.strip():
            st.error("'Conducted by' is required.")
        else:
            linked_ids = ",".join(
                str(lf_id_for_opt[o]) for o in linked_opts if o in lf_id_for_opt
            )
            new_log_id = insert_returning_id(
                """INSERT INTO review_log
                   (protocol_id, conducted_date, conducted_by, summary,
                    red_flags_found, linked_indicator_ids, follow_up_required)
                   VALUES (:pid, :cd, :cb, :summary, :rf, :li, :fu)""",
                {
                    "pid":     proto["id"],
                    "cd":      conducted_date.isoformat(),
                    "cb":      conducted_by.strip(),
                    "summary": summary.strip(),
                    "rf":      red_flags.strip(),
                    "li":      linked_ids,
                    "fu":      fu_required,
                },
            )

            # Auto-advance next_scheduled_date on the protocol
            new_nsd = _advance_date(
                proto.get("next_scheduled_date") or conducted_date.isoformat(),
                proto.get("review_frequency") or "Quarterly",
            )
            run_write(
                "UPDATE review_protocols SET next_scheduled_date=:nsd WHERE id=:id",
                {"nsd": new_nsd, "id": proto["id"]},
            )

            st.success(
                f"Review logged (ID {new_log_id}). "
                f"Next **{selected_dt}** review auto-scheduled for **{new_nsd}**."
            )

            if fu_required == "Y" and linked_opts:
                g_ids = [lf_id_for_opt[o] for o in linked_opts if o in lf_id_for_opt]
                st.session_state["g_indicator_ids"] = g_ids
                st.session_state["g_source"]        = (
                    f"Module F — {selected_dt} review ({conducted_date.isoformat()})"
                )
                st.warning(
                    "⚡ **Follow-up required** — "
                    "the linked indicators have been forwarded to Module G."
                )
                if st.button("➡️ Open Module G — Decision Report", type="primary"):
                    st.switch_page("pages/7_G_Decision_Reports.py")

            st.rerun()

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Review Log
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📜 Review Log")

log_entries = _load_log()

if not log_entries:
    st.caption("No reviews logged yet.")
else:
    def _expand_ids(id_str: str | None) -> str:
        if not id_str:
            return "—"
        codes = []
        for part in str(id_str).split(","):
            part = part.strip()
            if part.isdigit():
                row = lf_by_id.get(int(part))
                codes.append(row["indicator_code"] if row else part)
            else:
                codes.append(part)
        return ", ".join(codes) if codes else "—"

    df_log = pd.DataFrame(log_entries)
    df_log["Indicators"] = df_log["linked_indicator_ids"].apply(_expand_ids)
    df_log = df_log.rename(columns={
        "data_type":          "Type",
        "conducted_date":     "Date",
        "conducted_by":       "Conducted by",
        "summary":            "Summary",
        "red_flags_found":    "Red flags",
        "follow_up_required": "Follow-up",
    }).drop(columns=["id", "linked_indicator_ids"])

    def _fu_css(val) -> str:
        return (
            "background-color:#FFEBEE;color:#C62828;font-weight:bold;"
            if str(val) == "Y" else ""
        )

    try:
        styled_log = df_log.style.map(_fu_css, subset=["Follow-up"])
    except AttributeError:
        styled_log = df_log.style.applymap(_fu_css, subset=["Follow-up"])

    st.dataframe(styled_log, hide_index=True, use_container_width=True)

    # Resurface Y follow-up entries with a quick link to Module G
    y_entries = [e for e in log_entries if e.get("follow_up_required") == "Y"]
    if y_entries and can_write_module("F"):
        with st.expander(f"⚡ {len(y_entries)} review(s) with outstanding follow-up"):
            for e in y_entries:
                raw_ids   = (e.get("linked_indicator_ids") or "").split(",")
                g_ids     = [int(x.strip()) for x in raw_ids if x.strip().isdigit()]
                codes_str = ", ".join(
                    lf_by_id[i]["indicator_code"]
                    for i in g_ids if i in lf_by_id
                ) or "—"
                st.markdown(
                    f"**{e['data_type']}** review "
                    f"({e['conducted_date']}) — {codes_str}"
                )
                if st.button(
                    "➡️ Open Module G",
                    key=f"g_link_{e['id']}",
                ):
                    st.session_state["g_indicator_ids"] = g_ids
                    st.session_state["g_source"] = (
                        f"Module F — {e['data_type']} review "
                        f"({e['conducted_date']})"
                    )
                    st.switch_page("pages/7_G_Decision_Reports.py")

"""Module D — Kobo Data Sync

Pulls KoboToolbox form submissions into the local database and maps them
into raw_data_analysis.actual_q[N] cells in Module E.

Token is base64-obfuscated in database/.kobo_token — add that path to
.gitignore and never commit it to version control. For production use an
environment variable (KOBO_API_TOKEN) or a proper secrets manager instead.

Background sync caveat: Streamlit's rerun model does not support true
background tasks. For unattended nightly sync, run:
    python -m scripts.kobo_sync --project SAWA
and schedule it with cron (Linux/macOS), Windows Task Scheduler, or a
GitHub Actions nightly workflow. See the Schedule section at the bottom
of this page.
"""
from __future__ import annotations
import io
import os
import random
import re
from datetime import date as _date, datetime, timedelta, timezone
from collections import defaultdict

import streamlit as st
import pandas as pd

from database.db import init_db, run_query, run_write, insert_returning_id, DB_PATH, IS_POSTGRES
from utils.shared_widgets import project_selector
from utils.auth import can, can_write_module
from utils.nav_strip import render_nav_strip
from utils.kobo_client import (
    KoboClient,
    save_api_token,
    load_api_token,
    clear_api_token,
    BASE_URLS,
)

st.set_page_config(page_title="Kobo Data Sync — CEL MEL", layout="wide")
init_db()
render_nav_strip("Input")

if not st.session_state.get("authentication_status"):
    st.error("Please log in from the main page.")
    st.stop()

with st.sidebar:
    project_id = project_selector()
    if project_id is None:
        st.stop()
    st.divider()
    st.caption(f"Role: **{st.session_state.get('role', 'Viewer')}**")

# ── Session state initialisation ──────────────────────────────────────────────
if "kobo_token" not in st.session_state:
    st.session_state["kobo_token"]     = load_api_token() or ""
if "kobo_server" not in st.session_state:
    st.session_state["kobo_server"]    = "global"
if "kobo_connected" not in st.session_state:
    st.session_state["kobo_connected"] = False
if "kobo_forms_cache" not in st.session_state:
    st.session_state["kobo_forms_cache"] = []

# ── Helpers ───────────────────────────────────────────────────────────────────
TRANSFORM_OPTS = ["count", "sum", "mean", "latest"]


def _apply_transform(series: pd.Series, transform: str) -> str:
    nums = pd.to_numeric(series.dropna(), errors="coerce").dropna()
    if transform == "count":
        return str(int(series.dropna().shape[0]))
    if transform == "sum":
        return f"{nums.sum():.4g}" if len(nums) else ""
    if transform == "mean":
        return f"{nums.mean():.4g}" if len(nums) else ""
    if transform == "latest":
        vals = series.dropna()
        return str(vals.iloc[-1]) if len(vals) else ""
    return str(int(series.dropna().shape[0]))


def _current_quarter() -> int:
    """SAWA's fiscal year: Q1=Jul-Sep, Q2=Oct-Dec, Q3=Jan-Mar, Q4=Apr-Jun
    (NOT the calendar year — do not simplify to (month-1)//3+1)."""
    fiscal_month = (datetime.now().month - 7) % 12
    return fiscal_month // 3 + 1


_Q_RE = re.compile(r"q([1-4])", re.IGNORECASE)


def _detect_quarter(text: str, default: int | None) -> int | None:
    """Look for 'Q1'..'Q4' (case-insensitive) in a filename or sheet name."""
    m = _Q_RE.search(text or "")
    return int(m.group(1)) if m else default


def _num_or_none(val) -> float | None:
    if val is None or str(val).strip() in ("", "—"):
        return None
    try:
        return float(str(val).replace(",", "").replace("$", "").replace("%", "").replace("≥", "").replace("+", "").strip())
    except (ValueError, TypeError):
        return None


def _recompute_actual_year(project_id: int, logframe_row_id: int) -> None:
    """Sum actual_q1..q4 into actual_year so Module H (which reads actual_year
    only) reflects quarterly data written here, whether from live Kobo sync
    or the manual upload tab. Leaves actual_year untouched if no quarter has
    a parseable numeric value yet (e.g. annual-frequency indicators entered
    directly in Module E)."""
    row = run_query(
        """SELECT actual_q1, actual_q2, actual_q3, actual_q4
           FROM   raw_data_analysis
           WHERE  project_id=:pid AND logframe_row_id=:lf""",
        {"pid": project_id, "lf": logframe_row_id},
    )
    if not row:
        return
    quarters = [_num_or_none(row[0][f"actual_q{n}"]) for n in (1, 2, 3, 4)]
    parsed = [q for q in quarters if q is not None]
    if not parsed:
        return
    total = sum(parsed)
    year_str = str(int(total)) if total == int(total) else f"{total:.4g}"
    run_write(
        """UPDATE raw_data_analysis SET actual_year=:y
           WHERE  project_id=:pid AND logframe_row_id=:lf""",
        {"y": year_str, "pid": project_id, "lf": logframe_row_id},
    )


# ── Sample data generator (testing only) ─────────────────────────────────────

_SAMPLE_ENUMERATORS = ["Abena K.", "Kofi M.", "Akosua D.", "Yaw A.", "Efua N."]
_SAMPLE_SITES = ["Accra-Tema Hub", "Kumasi Hub", "Takoradi Hub", "Tamale Hub", "Cape Coast Hub"]
_SAMPLE_ANCHORS = ["R&B Farms", "AgroKings", "Yedent/Naple Betta", "Aglow Farms", "NewAge Agric"]
_SAMPLE_QUARTERS = [
    ("Q1 Jul–Sep 2026", "2026-07-01", "2026-09-30"),
    ("Q2 Oct–Dec 2026", "2026-10-01", "2026-12-31"),
    ("Q3 Jan–Mar 2027", "2027-01-01", "2027-03-31"),
    ("Q4 Apr–Jun 2027", "2027-04-01", "2027-06-30"),
]

def _rnd_date(s: str, e: str) -> str:
    sd, ed = _date.fromisoformat(s), _date.fromisoformat(e)
    return str(sd + timedelta(days=random.randint(0, (ed - sd).days)))

def _common(n: int, s: str, e: str) -> dict:
    rng = random.Random(42)
    return {
        "_id":            list(range(1001, 1001 + n)),
        "date_submitted": [_rnd_date(s, e) for _ in range(n)],
        "enumerator":     [rng.choice(_SAMPLE_ENUMERATORS) for _ in range(n)],
        "site":           [rng.choice(_SAMPLE_SITES) for _ in range(n)],
    }

def _cnt(n: int, target: int) -> list:
    rng = random.Random(42)
    v = ["Yes"] * target + [None] * (n - target)
    rng.shuffle(v)
    return v

def _sum_i(total: int, n: int) -> list:
    if total == 0:
        return [None] * n
    base, rem = divmod(total, n)
    v = [base + (1 if i < rem else 0) for i in range(n)]
    random.Random(42).shuffle(v)
    return v

def _sum_f(total: float, n: int) -> list:
    if total == 0:
        return [None] * n
    per = round(total / n, 3)
    v = [per] * (n - 1)
    v.append(round(total - sum(v), 3))
    random.Random(42).shuffle(v)
    return v

def _mean_scores(target: float, n: int = 20) -> list:
    rng = random.Random(42)
    sc = [int(target) + rng.randint(-8, 8) for _ in range(n - 1)]
    last = max(40, min(100, round(target * n - sum(sc))))
    sc.append(last)
    diff = round(sum(sc) / n - target)
    return [max(40, min(100, s - diff)) for s in sc]

def _build_sample_excel(form_idx: int) -> bytes:
    """Return XLSX bytes for the given form (1-indexed). 4 sheets = 4 quarters."""
    rng = random.Random(42)

    def _sheet(data: dict) -> pd.DataFrame:
        return pd.DataFrame(data)

    sheets: list[tuple[str, pd.DataFrame]] = []

    if form_idx == 1:
        params = [(95,1),(135,2),(135,2),(135,3)]
        for (q,s,e), (enr,pwd) in zip(_SAMPLE_QUARTERS, params):
            n = enr
            d = _common(n, s, e)
            d["participant_name"] = [f"Participant-{i:04d}" for i in range(1, n+1)]
            d["gender"] = ["Female"] * n
            d["anchor_partner"] = [rng.choice(_SAMPLE_ANCHORS) for _ in range(n)]
            d["participant_enrolled"] = _cnt(n, enr)
            d["pwd_enrolled"] = _cnt(n, pwd)
            sheets.append((q, _sheet(d)))

    elif form_idx == 2:
        params = [
            (95, 0, 0,   0,   0,   0),
            (135,0, 150, 150, 150, 150),
            (135,15,150, 150, 150, 150),
            (135,10,200, 200, 200, 200),
        ]
        for (q,s,e), (bds,gals,coop,gen,safe,digi) in zip(_SAMPLE_QUARTERS, params):
            n = bds
            d = _common(n, s, e)
            d["training_type"] = ["BDS"] * n
            d["bds_session_completed"] = _cnt(n, bds)
            d["gals_focal_person_trained"] = _cnt(n, gals)
            d["coop_training_attended"] = _sum_i(coop, n)
            d["gender_transformative_attended"] = _sum_i(gen, n)
            d["safeguarding_trained"] = _sum_i(safe, n)
            d["digital_literacy_attended"] = _sum_i(digi, n)
            sheets.append((q, _sheet(d)))

    elif form_idx == 3:
        params = [(0,0),(0,0),(300,1),(200,0)]
        cols = ["_id","date_submitted","enumerator","site","event_name",
                "women_attended_forum","bootcamp_or_exchange_held"]
        for (q,s,e), (wsum,boot) in zip(_SAMPLE_QUARTERS, params):
            if wsum == 0 and boot == 0:
                sheets.append((q, pd.DataFrame(columns=cols)))
                continue
            n = max(boot, 3)
            d = _common(n, s, e)
            d["event_name"] = [f"WAN Forum {i}" for i in range(1, n+1)]
            d["women_attended_forum"] = _sum_i(wsum, n)
            d["bootcamp_or_exchange_held"] = _cnt(n, boot)
            sheets.append((q, _sheet(d)))

    elif form_idx == 4:
        for (q,s,e), cnt in zip(_SAMPLE_QUARTERS, [1,2,2,3]):
            n = max(cnt, 1)
            d = _common(n, s, e)
            d["mentor_name"] = [f"PWD-Mentor-{i:03d}" for i in range(1, n+1)]
            d["disability_type"] = [rng.choice(["Physical","Visual","Hearing"]) for _ in range(n)]
            d["pwd_mentor_identified"] = _cnt(n, cnt)
            sheets.append((q, _sheet(d)))

    elif form_idx == 5:
        params = [(0,0),(0,0),(15,15),(10,10)]
        cols = ["_id","date_submitted","enumerator","site",
                "cooperative_name","cooperative_registered","governance_framework_adopted"]
        for (q,s,e), (co,gov) in zip(_SAMPLE_QUARTERS, params):
            if co == 0 and gov == 0:
                sheets.append((q, pd.DataFrame(columns=cols)))
                continue
            n = max(co, gov)
            d = _common(n, s, e)
            d["cooperative_name"] = [f"Women's Coop {i:02d}" for i in range(1, n+1)]
            d["anchor_partner"] = [rng.choice(_SAMPLE_ANCHORS) for _ in range(n)]
            d["cooperative_registered"] = _cnt(n, co)
            d["governance_framework_adopted"] = _cnt(n, gov)
            sheets.append((q, _sheet(d)))

    elif form_idx == 6:
        params = [(0,0),(0,0),(0,0),(3,2)]
        cols = ["_id","date_submitted","enumerator","site",
                "safeguarding_officer","campaign_roadshow_held","site_certified"]
        for (q,s,e), (cam,site) in zip(_SAMPLE_QUARTERS, params):
            if cam == 0 and site == 0:
                sheets.append((q, pd.DataFrame(columns=cols)))
                continue
            n = max(cam, site)
            d = _common(n, s, e)
            d["safeguarding_officer"] = [f"Officer-{i:02d}" for i in range(1, n+1)]
            d["campaign_roadshow_held"] = _cnt(n, cam)
            d["site_certified"] = _cnt(n, site)
            sheets.append((q, _sheet(d)))

    elif form_idx == 7:
        params = [(1.0,2083),(2.0,4167),(2.0,4167),(3.0,6250)]
        for (q,s,e), (fish,rev) in zip(_SAMPLE_QUARTERS, params):
            n = 2
            d = _common(n, s, e)
            d["pwd_farmer_id"] = [f"PWD-F-{i:03d}" for i in range(1, n+1)]
            d["fish_species"] = [rng.choice(["Tilapia","Catfish"]) for _ in range(n)]
            d["fish_volume_mt_pwd"] = _sum_f(fish, n)
            d["revenue_usd_pwd"] = _sum_i(rev, n)
            sheets.append((q, _sheet(d)))

    elif form_idx == 8:
        params = [(0,0.0,0),(40,46.3,83333),(30,34.7,62500),(30,34.7,62500)]
        cols = ["_id","date_submitted","enumerator","site",
                "enterprise_name","value_addition_jobs","fish_volume_mt_va","revenue_usd_va"]
        for (q,s,e), (jobs,fish,rev) in zip(_SAMPLE_QUARTERS, params):
            if jobs == 0:
                sheets.append((q, pd.DataFrame(columns=cols)))
                continue
            n = 5
            d = _common(n, s, e)
            d["enterprise_name"] = [f"VA-Enterprise-{i:02d}" for i in range(1, n+1)]
            d["enterprise_type"] = [rng.choice(["Processing","Trading","Both"]) for _ in range(n)]
            d["value_addition_jobs"] = _sum_i(jobs, n)
            d["fish_volume_mt_va"] = _sum_f(fish, n)
            d["revenue_usd_va"] = _sum_i(rev, n)
            sheets.append((q, _sheet(d)))

    elif form_idx == 9:
        for (q,s,e), mean_sc in zip(_SAMPLE_QUARTERS, [70,72,78,82]):
            n = 20
            d = _common(n, s, e)
            d["participant_id"] = [f"PMU-{i:03d}" for i in range(1, n+1)]
            d["training_type"] = ["Gender Transformative"] * n
            sc = _mean_scores(mean_sc, n)
            d["pre_test_score"] = [max(30, s - rng.randint(10,20)) for s in sc]
            d["post_test_score"] = sc
            sheets.append((q, _sheet(d)))

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for sheet_name, df in sheets:
            df.to_excel(w, sheet_name=sheet_name, index=False)
    return buf.getvalue()


_SAMPLE_FORMS = [
    (1, "F1_Enrolment_Register_Y1.xlsx",   "Mobilisation & Enrolment Register",       "PI.1 · PII.R5"),
    (2, "F2_Training_Attendance_Y1.xlsx",   "Training Attendance Register",             "PI.3 · PI.9 · PI.17 · PI.19 · PI.20 · PIV.5"),
    (3, "F3_WAN_Events_Y1.xlsx",            "WAN Leadership Events Log",                "PI.11 · PI.12"),
    (4, "F4_PWD_Mentor_Registry_Y1.xlsx",   "PWD Mentor Registry",                      "PI.13"),
    (5, "F5_Cooperative_Registry_Y1.xlsx",  "Tool 3 Cooperative & Governance Registry", "PIII.6 · PI.18"),
    (6, "F6_Safeguarding_Monitor_Y1.xlsx",  "Safeguarding Monitoring Form",             "PI.22 · PI.23"),
    (7, "F7_PWD_Production_Y1.xlsx",        "PWD Production & Revenue Tracker",         "PII.R6 · PII.R7"),
    (8, "F8_Value_Addition_Y1.xlsx",        "Value-Addition Enterprise Tracker",        "PIII.R1 · PIII.R2 · PIII.R3"),
    (9, "F9_PMU_Knowledge_Test_Y1.xlsx",    "PMU Pre/Post Knowledge Test",              "PI.19 (mean score)"),
]


def _do_sync(
    asset_uid: str,
    form_name: str,
    project_id: int,
    token: str,
    server: str,
) -> tuple[int, str, str]:
    """Pull new submissions, apply transforms, write to raw_data_analysis.
    Returns (records_pulled, status, error_message).
    """
    try:
        client = KoboClient(token, server)

        last_log = run_query(
            """SELECT synced_at FROM kobo_sync_log
               WHERE  project_id=:pid AND asset_uid=:uid AND status='success'
               ORDER  BY synced_at DESC LIMIT 1""",
            {"pid": project_id, "uid": asset_uid},
        )
        since = last_log[0]["synced_at"] if last_log else None

        df = client.get_submissions(asset_uid, since_timestamp=since)

        mappings = run_query(
            """SELECT kobo_field_name, logframe_row_id, transform
               FROM   kobo_form_mapping
               WHERE  project_id=:pid AND asset_uid=:uid
               AND    logframe_row_id IS NOT NULL""",
            {"pid": project_id, "uid": asset_uid},
        )

        q_col   = f"actual_q{_current_quarter()}"
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

        for m in mappings:
            field    = m["kobo_field_name"]
            lf_id    = m["logframe_row_id"]
            transf   = m.get("transform") or "count"

            if not df.empty and field in df.columns:
                value = _apply_transform(df[field], transf)
            else:
                value = "0"

            run_write(
                f"""UPDATE raw_data_analysis
                    SET    {q_col}=:v,
                           indicator_status='Data currently being collected/analysed',
                           last_updated=:ts
                    WHERE  project_id=:pid AND logframe_row_id=:lf""",
                {"v": value, "ts": now_iso, "pid": project_id, "lf": lf_id},
            )
            _recompute_actual_year(project_id, lf_id)

        return len(df), "success", ""

    except Exception as exc:  # noqa: BLE001
        return 0, "error", str(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE
# ═══════════════════════════════════════════════════════════════════════════════
st.title("Module D — Kobo Data Sync")
st.caption(
    "Pull KoboToolbox form submissions into the local database and map field "
    "values into Module E (Raw Data Analysis) indicator cells."
)

# ── Load indicator lookup for mapping UI ──────────────────────────────────────
lf_rows = run_query(
    "SELECT id, indicator_code FROM logframe_rows WHERE project_id=:pid ORDER BY id",
    {"pid": project_id},
)
id_to_code = {r["id"]: r["indicator_code"] for r in lf_rows}
code_to_id = {r["indicator_code"]: r["id"] for r in lf_rows}
indicator_codes = list(code_to_id.keys())

tab_sync, tab_upload, tab_storage = st.tabs(["🔄 Sync & Mapping", "📤 Upload", "📦 Storage"])

token_saved = bool(load_api_token())

# =============================================================================
# TAB 1 — Sync & Mapping
# =============================================================================
with tab_sync:
    with st.expander(
        "🔑 API Configuration"
        + (" · ✅ token saved" if token_saved else " · ⚠️ no token"),
        expanded=not token_saved,
    ):
        st.caption(
            "Token stored as base64 in `database/.kobo_token`.  "
            "**Add that file to `.gitignore`** and never commit it.  "
            "For production deployments use an environment variable instead."
        )

        cfg_c1, cfg_c2 = st.columns([1, 3])
        with cfg_c1:
            server = st.selectbox(
                "Server",
                options=list(BASE_URLS.keys()),
                index=list(BASE_URLS.keys()).index(st.session_state["kobo_server"]),
                format_func=lambda s: f"{s}  ({BASE_URLS[s]})",
            )
            st.session_state["kobo_server"] = server

        with cfg_c2:
            tok_input = st.text_input(
                "API Token",
                value=st.session_state["kobo_token"],
                type="password",
                placeholder="Paste your KoboToolbox API token here",
            )

        btn_c1, btn_c2, btn_c3 = st.columns(3)
        with btn_c1:
            if st.button("💾 Save token", use_container_width=True):
                if tok_input.strip():
                    save_api_token(tok_input.strip())
                    st.session_state["kobo_token"] = tok_input.strip()
                    st.success("Token saved to `database/.kobo_token`.")
                    st.rerun()
                else:
                    st.warning("Enter a token before saving.")

        with btn_c2:
            if st.button("🔌 Test connection", use_container_width=True, type="primary"):
                token_to_test = tok_input.strip() or st.session_state.get("kobo_token", "")
                if not token_to_test:
                    st.error("No token provided.")
                else:
                    with st.spinner("Connecting…"):
                        try:
                            client = KoboClient(token_to_test, server)
                            forms  = client.list_forms()
                            st.session_state["kobo_token"]       = token_to_test
                            st.session_state["kobo_connected"]   = True
                            st.session_state["kobo_forms_cache"] = forms
                            st.success(f"Connected — {len(forms)} form(s) accessible.")
                        except Exception as exc:
                            st.session_state["kobo_connected"] = False
                            st.error(f"Connection failed: {exc}")

        with btn_c3:
            if st.button("🗑️ Clear saved token", use_container_width=True):
                clear_api_token()
                st.session_state["kobo_token"]     = ""
                st.session_state["kobo_connected"] = False
                st.info("Saved token deleted.")
                st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════════
    # SECTION 2 — Connected Forms (only when token is live)
    # ═══════════════════════════════════════════════════════════════════════════════
    cached_forms: list[dict] = st.session_state.get("kobo_forms_cache", [])
    if cached_forms:
        with st.expander(f"📋 Forms accessible with this token ({len(cached_forms)} total)"):
            st.caption(
                "Toggle **Activate** to enable sync for a form. "
                "Activating registers the form in Field Mapping so you can map its fields."
            )
            forms_df = pd.DataFrame(cached_forms)
            st.dataframe(forms_df, hide_index=True, use_container_width=True)

            st.divider()
            st.markdown("**Activate a form for this project:**")
            act_c1, act_c2, act_c3 = st.columns([2, 3, 1])
            with act_c1:
                form_opts = [f"{f['asset_uid']} — {f['name']}" for f in cached_forms]
                selected_form_str = st.selectbox("Form", form_opts, label_visibility="collapsed")
            with act_c3:
                if st.button("➕ Activate", use_container_width=True, type="primary"):
                    idx  = form_opts.index(selected_form_str)
                    form = cached_forms[idx]
                    existing = run_query(
                        "SELECT id FROM kobo_form_mapping WHERE project_id=:pid AND asset_uid=:uid LIMIT 1",
                        {"pid": project_id, "uid": form["asset_uid"]},
                    )
                    if existing:
                        st.info(f"Form `{form['asset_uid']}` already has mappings for this project.")
                    else:
                        insert_returning_id(
                            """INSERT INTO kobo_form_mapping
                               (project_id, asset_uid, kobo_form_name, kobo_field_name,
                                logframe_row_id, transform)
                               VALUES (:pid, :uid, :name, :field, NULL, 'count')""",
                            {"pid": project_id, "uid": form["asset_uid"],
                             "name": form["name"], "field": "_placeholder"},
                        )
                        st.success(
                            f"Form `{form['name']}` registered. "
                            "Edit the field mapping in Section 3 below."
                        )
                        st.rerun()

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════════════
    # SECTION 3 — Field Mapping (always visible — uses seeded / DB data)
    # ═══════════════════════════════════════════════════════════════════════════════
    st.subheader("🔗 Field Mapping")
    st.caption(
        "Each row maps one Kobo form field to one SAWA logframe indicator. "
        "**Transform** controls how multiple submissions roll up: "
        "`count` (number of responses), `sum`, `mean`, or `latest` (most recent value)."
    )

    all_mappings = run_query(
        """SELECT id, asset_uid, kobo_form_name, kobo_field_name,
                  logframe_row_id, transform
           FROM   kobo_form_mapping
           WHERE  project_id = :pid
           ORDER  BY asset_uid, id""",
        {"pid": project_id},
    )

    if not all_mappings:
        st.info(
            "No mappings configured. Run `python -m database.seed_sawa` to load SAWA "
            "placeholder mappings, or activate a form above (requires API token)."
        )
    else:
        # Group by form
        form_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for m in all_mappings:
            key = (m["asset_uid"], m.get("kobo_form_name") or m["asset_uid"])
            form_groups[key].append(m)

        for (uid, form_name), form_mappings in form_groups.items():

            # ── Form header ───────────────────────────────────────────────────────
            last_log = run_query(
                """SELECT synced_at, status, records_pulled, error_message
                   FROM   kobo_sync_log
                   WHERE  project_id=:pid AND asset_uid=:uid
                   ORDER  BY synced_at DESC LIMIT 1""",
                {"pid": project_id, "uid": uid},
            )
            if last_log:
                lg = last_log[0]
                sync_line = (
                    f"Last sync: **{lg['synced_at']}** — "
                    f"{'✅' if lg['status']=='success' else '❌'} {lg['status']} "
                    f"({lg.get('records_pulled',0)} records"
                    + (f" · {lg['error_message']}" if lg.get("error_message") else "")
                    + ")"
                )
            else:
                sync_line = "Never synced"

            hdr_c, sync_btn_c = st.columns([5, 1])
            with hdr_c:
                st.markdown(f"**{form_name}**  `{uid}`  \n{sync_line}")
            with sync_btn_c:
                if st.button("🔄 Sync now", key=f"sync_{uid}", use_container_width=True, type="primary"):
                    token = st.session_state.get("kobo_token", "")
                    srv   = st.session_state.get("kobo_server", "global")
                    if not token:
                        st.error("No API token. Configure it in the API Configuration section above.")
                    else:
                        with st.spinner("Syncing…"):
                            n, status, err = _do_sync(uid, form_name, project_id, token, srv)
                        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
                        insert_returning_id(
                            """INSERT INTO kobo_sync_log
                               (project_id, asset_uid, synced_at, records_pulled,
                                status, error_message)
                               VALUES (:pid, :uid, :at, :n, :status, :err)""",
                            {"pid": project_id, "uid": uid, "at": now_iso,
                             "n": n, "status": status, "err": err},
                        )
                        if status == "success":
                            st.success(f"Synced {n} new submission(s). Module E updated.")
                        else:
                            st.error(f"Sync failed: {err}")
                        st.rerun()

            # ── Fetch live field names if connected ───────────────────────────────
            live_fields: list[str] = []
            if st.session_state.get("kobo_connected") and st.session_state.get("kobo_token"):
                try:
                    client = KoboClient(
                        st.session_state["kobo_token"],
                        st.session_state["kobo_server"],
                    )
                    live_fields = client.extract_field_names(uid)
                except Exception:
                    pass  # fall back to text input

            field_col_config: dict = {
                "Kobo Field":  (
                    st.column_config.SelectboxColumn("Kobo Field", options=live_fields, width="medium")
                    if live_fields
                    else st.column_config.TextColumn("Kobo Field", width="medium")
                ),
                "Indicator": st.column_config.SelectboxColumn(
                    "Target Indicator", options=indicator_codes, width="medium"
                ),
                "Transform": st.column_config.SelectboxColumn(
                    "Transform", options=TRANSFORM_OPTS, width="small"
                ),
            }

            # ── Mapping data_editor ───────────────────────────────────────────────
            df_map = pd.DataFrame([
                {
                    "_id":        m["id"],
                    "Kobo Field": m["kobo_field_name"],
                    "Indicator":  id_to_code.get(m.get("logframe_row_id") or -1, ""),
                    "Transform":  m.get("transform") or "count",
                }
                for m in form_mappings
            ])

            if can_write_module("D"):
                edited_map = st.data_editor(
                    df_map,
                    column_config={
                        "_id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                        **field_col_config,
                    },
                    disabled=["_id"],
                    hide_index=True,
                    use_container_width=True,
                    key=f"map_editor_{uid}",
                    num_rows="dynamic",
                )

                if st.button(f"💾 Save mapping", key=f"save_map_{uid}"):
                    run_write(
                        "DELETE FROM kobo_form_mapping WHERE project_id=:pid AND asset_uid=:uid",
                        {"pid": project_id, "uid": uid},
                    )
                    saved = 0
                    for _, row in edited_map.iterrows():
                        field  = str(row.get("Kobo Field", "") or "").strip()
                        code   = str(row.get("Indicator",  "") or "").strip()
                        transf = str(row.get("Transform",  "count") or "count")
                        lf_id  = code_to_id.get(code)
                        if not field or field == "_placeholder":
                            continue
                        insert_returning_id(
                            """INSERT INTO kobo_form_mapping
                               (project_id, asset_uid, kobo_form_name, kobo_field_name,
                                logframe_row_id, transform)
                               VALUES (:pid, :uid, :name, :field, :lf_id, :transform)""",
                            {"pid": project_id, "uid": uid, "name": form_name,
                             "field": field, "lf_id": lf_id, "transform": transf},
                        )
                        saved += 1
                    st.success(f"Saved {saved} mapping row(s).")
                    st.rerun()

            else:
                st.dataframe(
                    df_map.drop(columns=["_id"]),
                    column_config={k: v for k, v in field_col_config.items()},
                    hide_index=True,
                    use_container_width=True,
                )

            st.divider()

    # ── Add new form (manual entry) ───────────────────────────────────────────────
    if can_write_module("D"):
        with st.expander("➕ Register a new form manually"):
            nc1, nc2, nc3 = st.columns(3)
            with nc1:
                new_uid  = st.text_input("Asset UID", placeholder="e.g. aXXXXXXXXXXXXXXXXXXXX")
            with nc2:
                new_name = st.text_input("Form name", placeholder="e.g. SAWA Enrolment Form")
            with nc3:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("Register", use_container_width=True, type="primary"):
                    if new_uid.strip() and new_name.strip():
                        insert_returning_id(
                            """INSERT INTO kobo_form_mapping
                               (project_id, asset_uid, kobo_form_name, kobo_field_name,
                                logframe_row_id, transform)
                               VALUES (:pid, :uid, :name, '_placeholder', NULL, 'count')""",
                            {"pid": project_id, "uid": new_uid.strip(), "name": new_name.strip()},
                        )
                        st.success(f"Registered `{new_name}`. Add field mappings in the section above.")
                        st.rerun()
                    else:
                        st.warning("Both Asset UID and Form name are required.")


    # ═══════════════════════════════════════════════════════════════════════════════
    # SECTION 5 — Sync Log
    # ═══════════════════════════════════════════════════════════════════════════════
    st.subheader("📜 Sync Log")

    sync_log = run_query(
        """SELECT synced_at, asset_uid, status, records_pulled, error_message
           FROM   kobo_sync_log
           WHERE  project_id = :pid
           ORDER  BY synced_at DESC
           LIMIT  200""",
        {"pid": project_id},
    )

    if not sync_log:
        st.caption("No sync attempts recorded yet.")
    else:
        df_log = pd.DataFrame(sync_log)

        def _log_css(val) -> str:
            mapping = {
                "success": "background-color:#E8F5E9;color:#2E7D32;",
                "error":   "background-color:#FFEBEE;color:#C62828;",
                "partial": "background-color:#FFF8E1;color:#E65100;",
            }
            return mapping.get(str(val) if val else "", "")

        try:
            styled_log = df_log.style.map(_log_css, subset=["status"])
        except AttributeError:
            styled_log = df_log.style.applymap(_log_css, subset=["status"])

        st.dataframe(styled_log, hide_index=True, use_container_width=True)

    # ═══════════════════════════════════════════════════════════════════════════════
    # SECTION 5 — Schedule Information
    # ═══════════════════════════════════════════════════════════════════════════════
    with st.expander("⏰ Background / Scheduled Sync"):
        st.markdown("""
    **Streamlit free tier does not support true background tasks.** The "Sync now"
    button above only runs while the browser tab is open. For unattended nightly
    sync, use one of these options:

    **Option A — cron (Linux / macOS)**
    ```bash
    # Run once daily at 06:00
    0 6 * * * cd /path/to/cel_mel_platform && python -m scripts.kobo_sync --project SAWA
    ```

    **Option B — Windows Task Scheduler**
    Create a daily task that runs:
    ```
    python C:\\path\\to\\cel_mel_platform\\scripts\\kobo_sync.py --project SAWA
    ```

    **Option C — GitHub Actions nightly workflow**
    ```yaml
    on:
      schedule:
        - cron: "0 6 * * *"
    jobs:
      sync:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - run: pip install -r requirements.txt
          - run: python -m scripts.kobo_sync --project SAWA
            env:
              KOBO_API_TOKEN: ${{ secrets.KOBO_API_TOKEN }}
    ```

    **Option D — Streamlit Community Cloud**
    Secrets set in the app dashboard (Settings → Secrets) are available as
    `st.secrets["KOBO_API_TOKEN"]`. The app itself still cannot run background
    jobs, but Option C (GitHub Actions) can trigger re-deploys or call the DB
    directly via a scheduled workflow.

    > In all options, store the token in an **environment variable**
    > (`KOBO_API_TOKEN`), not in a file committed to version control.
    """)


# =============================================================================
# TAB 2 — Upload (offline fallback)
# =============================================================================
with tab_upload:
    st.caption(
        "Use this when direct API sync is disrupted. Download your form data from "
        "KoboToolbox (**Project → Downloads → XLS or CSV**), then upload below. "
        "Field mappings configured in the Sync & Mapping tab are applied automatically."
    )

    with st.expander("🧪 Download sample test data (Y1 — all 4 quarters)", expanded=False):
        st.caption(
            "Each file contains **4 sheets** (Q1–Q4) pre-filled with workplan-faithful "
            "target values. Upload the file as-is below — each sheet is written to its "
            "own quarter automatically (adjust if the auto-detected quarter is wrong)."
        )
        cols = st.columns(3)
        for i, (idx, fname, form_name, indicators) in enumerate(_SAMPLE_FORMS):
            with cols[i % 3]:
                st.download_button(
                    label=f"⬇ {fname}",
                    data=_build_sample_excel(idx),
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help=f"Form: {form_name}\nIndicators: {indicators}",
                    key=f"dl_sample_{idx}",
                    use_container_width=True,
                )
                st.caption(f"*{indicators}*")

    upload_forms = run_query(
        """SELECT DISTINCT asset_uid, kobo_form_name
           FROM   kobo_form_mapping
           WHERE  project_id=:pid AND kobo_field_name != '_placeholder'
           ORDER  BY kobo_form_name""",
        {"pid": project_id},
    )

    if not upload_forms:
        st.info("No forms registered yet. Configure field mappings in the Sync & Mapping tab first.")
    else:
        ul_c1, ul_c2 = st.columns([2, 3])
        with ul_c1:
            uf_labels = [f"{f['kobo_form_name']}  ({f['asset_uid']})" for f in upload_forms]
            uf_label  = st.selectbox("Form these files belong to", uf_labels, key="upload_form_sel")
            sel_form  = upload_forms[uf_labels.index(uf_label)]
        with ul_c2:
            up_files = st.file_uploader(
                "KoboToolbox export(s) (CSV or XLSX) — add one file per quarter with the "
                "**+**, or upload a single multi-sheet workbook with one sheet per quarter",
                type=["csv", "xlsx", "xls"],
                accept_multiple_files=True,
                key="kobo_manual_upload",
            )

        if up_files:
            # A CSV or single-sheet workbook is one quarter; a multi-sheet workbook
            # (e.g. the sample Y1 downloads) contributes one quarter per sheet.
            # Quarter is guessed from the sheet name, then the filename, then falls
            # back to the current quarter — always adjustable below before writing.
            quarter_jobs: list[dict] = []
            for f in up_files:
                try:
                    if f.name.lower().endswith(".csv"):
                        df = pd.read_csv(f)
                        q = _detect_quarter(f.name, _current_quarter())
                        quarter_jobs.append({"label": f.name, "quarter": q, "df": df})
                    else:
                        sheets = pd.read_excel(f, sheet_name=None)
                        if len(sheets) == 1:
                            (sheet_name, df), = sheets.items()
                            q = _detect_quarter(f.name, None) or _detect_quarter(sheet_name, _current_quarter())
                            quarter_jobs.append({"label": f.name, "quarter": q, "df": df})
                        else:
                            for sheet_name, df in sheets.items():
                                fallback = _detect_quarter(f.name, _current_quarter())
                                q = _detect_quarter(sheet_name, fallback)
                                quarter_jobs.append({"label": f"{f.name} · {sheet_name}", "quarter": q, "df": df})
                except Exception as exc:
                    st.error(f"Could not read **{f.name}**: {exc}")

            if quarter_jobs:
                st.success(
                    f"{len(quarter_jobs)} quarter file(s)/sheet(s) loaded from "
                    f"{len(up_files)} upload(s) — {sum(len(j['df']) for j in quarter_jobs):,} rows total."
                )

                st.markdown("**Confirm the target quarter for each file** (auto-detected — adjust if wrong):")
                for i, job in enumerate(quarter_jobs):
                    jc1, jc2, jc3 = st.columns([3, 1, 1])
                    with jc1:
                        st.caption(f"📄 {job['label']} — {len(job['df']):,} rows")
                    with jc2:
                        job["quarter"] = st.selectbox(
                            "Quarter", [1, 2, 3, 4], index=job["quarter"] - 1,
                            key=f"q_job_{i}", label_visibility="collapsed",
                        )
                    with jc3:
                        with st.popover("Preview"):
                            st.dataframe(job["df"].head(10), use_container_width=True)

                up_mappings = run_query(
                    """SELECT kobo_field_name, logframe_row_id, transform
                       FROM   kobo_form_mapping
                       WHERE  project_id=:pid AND asset_uid=:uid
                       AND    logframe_row_id IS NOT NULL""",
                    {"pid": project_id, "uid": sel_form["asset_uid"]},
                )

                if not up_mappings:
                    st.warning(
                        "No field→indicator mappings found for this form. "
                        "Assign indicators in the Sync & Mapping tab first."
                    )
                else:
                    preview = []
                    for job in quarter_jobs:
                        for m in up_mappings:
                            field   = m["kobo_field_name"]
                            present = field in job["df"].columns
                            value   = (
                                _apply_transform(job["df"][field], m.get("transform") or "count")
                                if present else "— not in file"
                            )
                            preview.append({
                                "Quarter": f"Q{job['quarter']}",
                                "File": job["label"],
                                "In file": "✅" if present else "❌",
                                "Kobo field": field,
                                "→ Value": value,
                                "Indicator": id_to_code.get(m["logframe_row_id"] or -1, "?"),
                            })
                    st.markdown("**Mapping preview — values that will be written per quarter:**")
                    st.dataframe(pd.DataFrame(preview), hide_index=True, use_container_width=True)

                    if can_write_module("D"):
                        if st.button(
                            "✅ Apply mapping & write to Module E",
                            type="primary",
                            key="apply_manual_upload",
                        ):
                            now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
                            written = 0
                            for job in quarter_jobs:
                                q_col = f"actual_q{job['quarter']}"
                                for m in up_mappings:
                                    field = m["kobo_field_name"]
                                    if field not in job["df"].columns:
                                        continue
                                    value = _apply_transform(
                                        job["df"][field], m.get("transform") or "count"
                                    )
                                    run_write(
                                        f"""UPDATE raw_data_analysis
                                            SET    {q_col}=:v,
                                                   indicator_status=
                                                       'Data currently being collected/analysed',
                                                   last_updated=:ts
                                            WHERE  project_id=:pid
                                            AND    logframe_row_id=:lf""",
                                        {
                                            "v": value, "ts": now_iso,
                                            "pid": project_id, "lf": m["logframe_row_id"],
                                        },
                                    )
                                    _recompute_actual_year(project_id, m["logframe_row_id"])
                                    written += 1
                            insert_returning_id(
                                """INSERT INTO kobo_sync_log
                                   (project_id, asset_uid, synced_at,
                                    records_pulled, status, error_message)
                                   VALUES (:pid, :uid, :at, :n, 'success', :msg)""",
                                {
                                    "pid": project_id,
                                    "uid": sel_form["asset_uid"],
                                    "at": now_iso,
                                    "n": sum(len(j["df"]) for j in quarter_jobs),
                                    "msg": f"Manual upload: {', '.join(f.name for f in up_files)}",
                                },
                            )
                            st.success(
                                f"Written {written} indicator value(s) across "
                                f"{len(quarter_jobs)} quarter file(s)/sheet(s). Module E updated."
                            )
                            st.rerun()
                    else:
                        st.info("Editor or Admin role required to write data.")


# =============================================================================
# TAB 3 — Storage
# =============================================================================
with tab_storage:
    NAVY = "#0D2B5E"
    GOLD = "#C8A951"

    st.caption(
        "Live view of what is stored in the database from Kobo sync activity. "
        "Use **Export / Backup now** to download a full copy of the SQLite database."
    )

    # ── Per-form storage summary ──────────────────────────────────────────────
    st.markdown("#### Per-Form Storage Summary")

    form_storage = run_query(
        """SELECT kfm.kobo_form_name, kfm.asset_uid,
                  COUNT(DISTINCT kfm.kobo_field_name) AS mappings,
                  MAX(ksl.synced_at)                  AS last_synced,
                  COALESCE(SUM(
                      CASE WHEN ksl.status='success' THEN ksl.records_pulled ELSE 0 END
                  ), 0)                               AS total_records,
                  COALESCE(SUM(
                      CASE WHEN ksl.status='error' THEN 1 ELSE 0 END
                  ), 0)                               AS error_count
           FROM   kobo_form_mapping kfm
           LEFT JOIN kobo_sync_log ksl
               ON  ksl.asset_uid   = kfm.asset_uid
               AND ksl.project_id  = kfm.project_id
           WHERE  kfm.project_id   = :pid
             AND  kfm.kobo_field_name != '_placeholder'
           GROUP  BY kfm.asset_uid, kfm.kobo_form_name
           ORDER  BY kfm.kobo_form_name""",
        {"pid": project_id},
    )

    if form_storage:
        for row in form_storage:
            last_lbl = row["last_synced"] or "Never"
            err_tag  = (
                f" &nbsp;·&nbsp; <span style='color:#C62828;'>"
                f"{int(row['error_count'])} error(s)</span>"
                if row["error_count"] else ""
            )
            st.markdown(
                f'<div style="border:1px solid #e0e0e0;border-left:4px solid {NAVY};'
                f'border-radius:6px;padding:10px 14px;margin-bottom:8px;'
                f'background:#F8F9FB;">' 
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;">' 
                f'<div><b style="color:{NAVY};">{row["kobo_form_name"]}</b> '
                f'<span style="font-size:0.75em;color:#888;">· {row["asset_uid"]}</span></div>'
                f'<span style="font-size:0.72em;background:{NAVY};color:#fff;'
                f'padding:1px 7px;border-radius:3px;">→ raw_data_analysis</span>'
                f'</div>'
                f'<div style="margin-top:6px;font-size:0.8em;color:#555;">'
                f'🕐 Last sync: <b>{last_lbl}</b>'
                f' &nbsp;·&nbsp; 📦 Records pulled: <b>{int(row["total_records"])}</b>'
                f' &nbsp;·&nbsp; 🔗 Mappings: <b>{row["mappings"]}</b>{err_tag}'
                f'</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("No forms registered yet — activate a form in the Sync & Mapping tab.")

    # ── Database info ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Database Info")

    total_rows = run_query(
        "SELECT COUNT(*) AS n FROM raw_data_analysis WHERE project_id=:pid",
        {"pid": project_id},
    )
    rda_n = total_rows[0]["n"] if total_rows else 0

    if IS_POSTGRES:
        di1, di2 = st.columns(2)
        di1.metric("Engine", "Postgres (Supabase)")
        di2.metric("RDA rows", rda_n)
    else:
        db_size_kb = round(os.path.getsize(DB_PATH) / 1024, 1) if os.path.exists(DB_PATH) else 0
        di1, di2, di3 = st.columns(3)
        di1.metric("Engine", "SQLite 3")
        di2.metric("DB size", f"{db_size_kb} KB")
        di3.metric("RDA rows", rda_n)

    # ── Export / Backup ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Export / Backup")
    if IS_POSTGRES:
        st.info(
            "Data lives in Supabase Postgres, not a local file — use the Supabase "
            "dashboard (Database → Backups) or `pg_dump` against the connection "
            "string in this app's secrets for a full backup.",
            icon="ℹ️",
        )
    else:
        st.caption(
            "Downloads the entire `cel_mel.db` file — includes logframe, raw data, "
            "sync logs, review protocols and decision reports."
        )
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "rb") as _f:
                _db_bytes = _f.read()
            fname = f"cel_mel_backup_{_date.today().isoformat()}.db"
            st.download_button(
                "📥 Export / Backup now",
                data=_db_bytes,
                file_name=fname,
                mime="application/octet-stream",
                type="primary",
                use_container_width=True,
            )
        else:
            st.warning("Database file not found.")


"""Module E — Kobo Data Sync

Pulls KoboToolbox form submissions into the local database and maps them
into raw_data_analysis.actual_q[N] cells in Module D.

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
from datetime import datetime, timezone
from collections import defaultdict

import streamlit as st
import pandas as pd

from database.db import init_db, run_query, run_write, insert_returning_id
from utils.shared_widgets import project_selector
from utils.auth import can
from utils.kobo_client import (
    KoboClient,
    save_api_token,
    load_api_token,
    clear_api_token,
    BASE_URLS,
)

st.set_page_config(page_title="Kobo Data Sync — CEL MEL", layout="wide")
init_db()

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
    return (datetime.now().month - 1) // 3 + 1


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

        return len(df), "success", ""

    except Exception as exc:  # noqa: BLE001
        return 0, "error", str(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE
# ═══════════════════════════════════════════════════════════════════════════════
st.title("Module E — Kobo Data Sync")
st.caption(
    "Pull KoboToolbox form submissions into the local database and map field "
    "values into Module D (Raw Data Analysis) indicator cells."
)

# ── Load indicator lookup for mapping UI ──────────────────────────────────────
lf_rows = run_query(
    "SELECT id, indicator_code FROM logframe_rows WHERE project_id=:pid ORDER BY id",
    {"pid": project_id},
)
id_to_code = {r["id"]: r["indicator_code"] for r in lf_rows}
code_to_id = {r["indicator_code"]: r["id"] for r in lf_rows}
indicator_codes = list(code_to_id.keys())

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — API Configuration
# ═══════════════════════════════════════════════════════════════════════════════
token_saved = bool(load_api_token())
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
                        st.success(f"Synced {n} new submission(s). Module D updated.")
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

        if can("write"):
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
if can("write"):
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
# SECTION 4 — Sync Log
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

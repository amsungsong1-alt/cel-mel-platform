"""Reusable sidebar widgets and status-badge components.

Full implementations added as each module is built.
"""
from __future__ import annotations
import os
from datetime import datetime, timezone

import streamlit as st
from database.db import run_query, DB_PATH


def _db_status_chip(project_id: int) -> None:
    """Persistent sidebar chip: DB type · record count · last sync age."""
    try:
        last_sync = run_query(
            """SELECT synced_at FROM kobo_sync_log
               WHERE project_id=:pid AND status='success'
               ORDER BY synced_at DESC LIMIT 1""",
            {"pid": project_id},
        )
        total = run_query(
            "SELECT COUNT(*) AS n FROM raw_data_analysis WHERE project_id=:pid",
            {"pid": project_id},
        )
        n = total[0]["n"] if total else 0

        if last_sync:
            ts = last_sync[0]["synced_at"]
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                secs = int((datetime.now(timezone.utc) - dt).total_seconds())
                if secs < 3600:
                    age = f"{secs // 60}m ago"
                elif secs < 86400:
                    age = f"{secs // 3600}h ago"
                else:
                    age = f"{secs // 86400}d ago"
                sync_lbl = f"synced {age}"
            except Exception:
                sync_lbl = "synced"
        else:
            sync_lbl = "never synced"

        st.sidebar.markdown(
            f'<div style="background:#EEF2FF;border:1px solid #C7D2FE;'
            f'border-radius:5px;padding:5px 9px;margin-top:4px;font-size:0.68em;'
            f'color:#374151;line-height:1.6;">'
            f'<b style="color:#0D2B5E;">🗄 SQLite</b>'
            f'&ensp;{n} records&ensp;·&ensp;{sync_lbl}'
            f'</div>',
            unsafe_allow_html=True,
        )
    except Exception:
        pass


def project_selector() -> int | None:
    """Sidebar dropdown — sets st.session_state.project_id and returns it."""
    projects = run_query("SELECT project_id, name FROM projects ORDER BY name")
    if not projects:
        st.sidebar.warning("No projects in database. Run database/seed_sawa.py first.")
        return None

    names = [p["name"] for p in projects]
    ids   = [p["project_id"] for p in projects]

    current = st.session_state.get("project_id")
    default_index = ids.index(current) if current in ids else 0

    chosen = st.sidebar.selectbox("Active project", names, index=default_index, key="_project_select")
    project_id = ids[names.index(chosen)]
    st.session_state["project_id"] = project_id
    _db_status_chip(project_id)
    return project_id


def status_badge(label: str, status: str):
    """Render a coloured inline badge. status: 'ok'|'warn'|'error'|'info'."""
    colours = {"ok": "green", "warn": "orange", "error": "red", "info": "blue"}
    colour = colours.get(status, "grey")
    st.markdown(
        f'<span style="background:{colour};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-size:0.8em">{label}</span>',
        unsafe_allow_html=True,
    )

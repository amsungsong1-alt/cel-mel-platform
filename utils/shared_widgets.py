"""Reusable sidebar widgets and status-badge components.

Full implementations added as each module is built.
"""
import streamlit as st
from database.db import run_query


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

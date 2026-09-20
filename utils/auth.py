"""Role-based access using streamlit-authenticator.

Credential resolution order
---------------------------
1. Streamlit secrets (cloud deployment) — set these in the Streamlit Cloud
   dashboard under App Settings → Secrets:

       [credentials.usernames.admin]
       name     = "MEAL Admin"
       email    = "admin@sawa-programme.org"
       password = "$2b$12$<bcrypt hash>"
       role     = "Admin"

       [credentials.usernames.viewer]
       name     = "Donor Viewer"
       email    = "viewer@sawa-programme.org"
       password = "$2b$12$<bcrypt hash>"
       role     = "Viewer"

       [cookie]
       name        = "cel_mel_auth"
       key         = "<random secret string>"
       expiry_days = 7

2. database/credentials.yaml (local / fallback) — committed with demo
   passwords (admin=admin123 · editor=editor123 · viewer=viewer123).

Roles
-----
Admin  — full access: read + write + admin
Editor — read + write (no user management)
Viewer — read-only (partners / donors)
"""
from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth
import yaml

_CREDS_PATH = Path(__file__).parent.parent / "database" / "credentials.yaml"

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "Admin":  ["read", "write", "admin"],
    "Editor": ["read", "write"],
    "Viewer": ["read"],
}


def _config_from_secrets() -> dict:
    """Build the authenticator config dict from st.secrets."""
    raw = st.secrets
    usernames = {}
    for uname, udata in raw["credentials"]["usernames"].items():
        usernames[uname] = {
            "name":     udata["name"],
            "email":    udata.get("email", ""),
            "password": udata["password"],
            "role":     udata.get("role", "Viewer"),
        }
    return {
        "credentials": {"usernames": usernames},
        "cookie": {
            "name":        raw["cookie"]["name"],
            "key":         raw["cookie"]["key"],
            "expiry_days": int(raw["cookie"].get("expiry_days", 7)),
        },
    }


def _config_from_yaml() -> dict:
    """Load config from the local credentials.yaml file."""
    if not _CREDS_PATH.exists():
        raise FileNotFoundError(str(_CREDS_PATH))
    with open(_CREDS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_authenticator():
    """Return (authenticator, config) from secrets or YAML."""
    config = None

    # 1. Try Streamlit secrets (Streamlit Cloud deployment)
    try:
        if "credentials" in st.secrets and "cookie" in st.secrets:
            config = _config_from_secrets()
    except Exception:
        pass

    # 2. Fall back to credentials.yaml
    if config is None:
        config = _config_from_yaml()

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )
    return authenticator, config


def can(action: str) -> bool:
    """Return True if the current user's role includes *action*."""
    role = st.session_state.get("role", "Viewer")
    return action in ROLE_PERMISSIONS.get(role, [])


def can_write_module(module: str) -> bool:
    """Return True if the current user can write to *module* (e.g. 'D', 'F').

    Admins always pass.  Editors pass only if their write_modules list includes
    the module, or if they have no list (unrestricted editor).  Viewers never pass.
    """
    if not can("write"):
        return False
    write_modules = st.session_state.get("write_modules")
    if write_modules is None:
        return True  # Admin or unrestricted editor
    return module.upper() in [m.upper() for m in write_modules]


def ensure_auth() -> bool:
    """Return True if authenticated.

    Fast path: checks session_state first.
    Slow path: if session was reset by navigation, re-validates from the auth
    cookie so the user doesn't get kicked out just because they clicked a tab.
    """
    if st.session_state.get("authentication_status"):
        return True
    # Try to re-hydrate from cookie without rendering a login form
    try:
        auth, _ = get_authenticator()
        if hasattr(auth, "_check_cookie"):
            auth._check_cookie()
    except Exception:
        pass
    return bool(st.session_state.get("authentication_status"))


def require(action: str):
    """Halt the page with an error if the user lacks *action*."""
    if not can(action):
        st.error(f"Access denied — '{action}' permission required.")
        st.stop()

"""KoboToolbox API client for Module D — Kobo Data Sync.

Token storage: the API token is base64-obfuscated in database/.kobo_token.
This deters casual reading but is NOT true encryption. For production
deployments, store the token in an environment variable or a proper secrets
manager and never commit .kobo_token to version control.
"""
from __future__ import annotations

import base64
from pathlib import Path

import requests
import pandas as pd

# File that holds the obfuscated token — lives beside the DB, outside version control.
_TOKEN_FILE = Path(__file__).resolve().parent.parent / "database" / ".kobo_token"

BASE_URLS: dict[str, str] = {
    "global": "https://kf.kobotoolbox.org/api/v2/",
    "eu":     "https://eu.kobotoolbox.org/api/v2/",
}

# Question types that carry no data — skip when listing field names.
_STRUCTURAL_TYPES = frozenset({
    "begin_group", "end_group", "begin_repeat", "end_repeat",
    "note", "calculate", "hidden",
})


# ── Token helpers ─────────────────────────────────────────────────────────────

def save_api_token(token: str) -> None:
    """Write base64-obfuscated token to .kobo_token (chmod 600 on Unix)."""
    _TOKEN_FILE.write_bytes(base64.b64encode(token.strip().encode("utf-8")))
    try:
        _TOKEN_FILE.chmod(0o600)
    except Exception:
        pass  # Windows doesn't support Unix file modes


def load_api_token() -> str | None:
    """Return previously saved token, or None if not stored."""
    if not _TOKEN_FILE.exists():
        return None
    try:
        return base64.b64decode(_TOKEN_FILE.read_bytes()).decode("utf-8")
    except Exception:
        return None


def clear_api_token() -> None:
    """Delete the stored token file."""
    if _TOKEN_FILE.exists():
        _TOKEN_FILE.unlink()


# ── API client ────────────────────────────────────────────────────────────────

class KoboClient:
    """Thin wrapper around the KoboToolbox REST API v2."""

    def __init__(self, api_token: str, server: str = "global") -> None:
        self.api_token = api_token
        self.base_url  = BASE_URLS.get(server, BASE_URLS["global"])
        self._session  = requests.Session()
        self._session.headers.update({
            "Authorization": f"Token {api_token}",
            "Accept":        "application/json",
        })

    # ── Internal ─────────────────────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> dict:
        url  = self.base_url + path.lstrip("/")
        resp = self._session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ── Public API ────────────────────────────────────────────────────────────

    def list_forms(self) -> list[dict]:
        """Return every survey accessible to this token.

        Each entry: {asset_uid, name, deployment_status, submission_count}.
        """
        data = self._get("assets.json", params={"limit": 200, "asset_type": "survey"})
        return [
            {
                "asset_uid":         a.get("uid", ""),
                "name":              a.get("name", ""),
                "deployment_status": a.get("deployment_status", ""),
                "submission_count":  a.get("deployment__submission_count", 0),
            }
            for a in data.get("results", [])
        ]

    def get_submissions(
        self,
        asset_uid: str,
        since_timestamp: str | None = None,
    ) -> pd.DataFrame:
        """Paginate through all submissions for a form.

        If since_timestamp (ISO-8601) is given, only records with a
        _submission_time strictly after that timestamp are returned — so
        repeat syncs pull only new data, not the whole form.
        """
        records: list[dict] = []
        start, limit = 0, 1000

        while True:
            data  = self._get(
                f"assets/{asset_uid}/data.json",
                params={"limit": limit, "start": start},
            )
            batch = data.get("results", [])
            if not batch:
                break
            records.extend(batch)
            if data.get("next") is None:
                break
            start += limit

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)

        if since_timestamp and "_submission_time" in df.columns:
            df["_submission_time"] = pd.to_datetime(
                df["_submission_time"], utc=True, errors="coerce"
            )
            cutoff = pd.to_datetime(since_timestamp, utc=True, errors="coerce")
            if pd.notna(cutoff):
                df = df[df["_submission_time"] > cutoff].reset_index(drop=True)

        return df

    def get_form_schema(self, asset_uid: str) -> dict:
        """Return the full asset JSON, including content.survey (XLSForm questions)."""
        return self._get(f"assets/{asset_uid}.json")

    def extract_field_names(self, asset_uid: str) -> list[str]:
        """Return a flat list of data-bearing question names from the form schema."""
        schema = self.get_form_schema(asset_uid)
        survey = schema.get("content", {}).get("survey", [])
        names  = []
        for item in survey:
            qtype = item.get("type", "")
            if qtype in _STRUCTURAL_TYPES:
                continue
            name = item.get("name") or item.get("$autoname", "")
            if name:
                names.append(name)
        return names

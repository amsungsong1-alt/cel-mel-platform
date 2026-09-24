"""SAWA's fiscal calendar: Q1=Jul-Sep, Q2=Oct-Dec, Q3=Jan-Mar, Q4=Apr-Jun —
NOT the calendar year. Shared so Module D (writes) and Module E (reads/year
selector) can never disagree on what "the current quarter/year" means.
"""
from __future__ import annotations

from datetime import datetime


def current_quarter(as_of: datetime | None = None) -> int:
    """1-4, per SAWA's Jul-start fiscal year."""
    month = (as_of or datetime.now()).month
    fiscal_month = (month - 7) % 12
    return fiscal_month // 3 + 1


def current_fiscal_year(as_of: datetime | None = None) -> int:
    """Calendar year the current fiscal year STARTED in.
    E.g. "FY2026" runs Jul 2026 - Jun 2027; any date in that span returns 2026."""
    now = as_of or datetime.now()
    return now.year if now.month >= 7 else now.year - 1

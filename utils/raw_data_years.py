"""Shared helpers for raw_data_analysis's per-year rows — used by Module D
(writes from Kobo sync / manual upload) and Module E (the "start next
fiscal year" rollover action), so both agree on exactly how a new year's
row gets created.
"""
from __future__ import annotations

from database.db import run_query, run_write, insert_returning_id


def get_or_create_year_row(project_id: int, logframe_row_id: int, year: int) -> int:
    """Return raw_data_analysis.id for (project, logframe_row, reporting_year),
    creating it if needed — one row per year, so a second year's actuals
    never overwrite the first year's in the same actual_q1..q4 cells.

    An untagged legacy row (reporting_year IS NULL, from before this column
    existed) is adopted as this year rather than duplicated. A genuinely new
    year carries over data_type/target/trigger from the most recent prior
    row for this indicator, leaving actuals blank for the new year.
    """
    existing = run_query(
        """SELECT id FROM raw_data_analysis
           WHERE  project_id=:pid AND logframe_row_id=:lf AND reporting_year=:yr""",
        {"pid": project_id, "lf": logframe_row_id, "yr": year},
    )
    if existing:
        return existing[0]["id"]

    legacy = run_query(
        """SELECT id FROM raw_data_analysis
           WHERE  project_id=:pid AND logframe_row_id=:lf AND reporting_year IS NULL""",
        {"pid": project_id, "lf": logframe_row_id},
    )
    if legacy:
        run_write(
            "UPDATE raw_data_analysis SET reporting_year=:yr WHERE id=:id",
            {"yr": year, "id": legacy[0]["id"]},
        )
        return legacy[0]["id"]

    prior = run_query(
        """SELECT data_type, target_value, trigger_value FROM raw_data_analysis
           WHERE  project_id=:pid AND logframe_row_id=:lf
           ORDER  BY (reporting_year IS NULL) ASC, reporting_year DESC LIMIT 1""",
        {"pid": project_id, "lf": logframe_row_id},
    )
    base = prior[0] if prior else {}
    return insert_returning_id(
        """INSERT INTO raw_data_analysis
           (project_id, logframe_row_id, reporting_year, data_type, target_value,
            trigger_value, indicator_status)
           VALUES (:pid, :lf, :yr, :dt, :tv, :trg, 'Data not collected yet')""",
        {
            "pid": project_id, "lf": logframe_row_id, "yr": year,
            "dt": base.get("data_type"), "tv": base.get("target_value"),
            "trg": base.get("trigger_value"),
        },
    )


def start_fiscal_year(project_id: int, year: int) -> int:
    """Create a row for every one of this project's logframe indicators for
    `year`, for indicators that don't already have one — so targets can be
    set/reviewed before any actual data comes in, rather than a year only
    ever appearing once Module D happens to write to it first. Returns the
    number of rows created (0 if the year was already fully rolled over)."""
    lf_rows = run_query(
        "SELECT id FROM logframe_rows WHERE project_id=:pid",
        {"pid": project_id},
    )
    created = 0
    for lf in lf_rows:
        existing = run_query(
            """SELECT id FROM raw_data_analysis
               WHERE  project_id=:pid AND logframe_row_id=:lf AND reporting_year=:yr""",
            {"pid": project_id, "lf": lf["id"], "yr": year},
        )
        if existing:
            continue
        get_or_create_year_row(project_id, lf["id"], year)
        created += 1
    return created

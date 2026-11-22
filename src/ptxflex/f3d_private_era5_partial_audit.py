"""Independent, offline audit of incomplete private ERA5 monthly acquisition artifacts.

Never accepts a partial collection as a year or as a source-hash match.
No provider data or secrets are emitted.
"""
from __future__ import annotations
import calendar
import hashlib
import json
from pathlib import Path

YEARS = {2022: 8760, 2023: 8760, 2024: 8784}
EXPECTED_2023_SHA = "abbfea17224cd92f694ed26b7a179ef7e35fff5a5bb17c6ee060a674c1977717"


def audit_private_months(root: str | Path, year: int) -> dict:
    """Rehash raw private files, check unique ordered month coverage and reject false annual claims."""
    if year not in YEARS:
        raise ValueError("unsupported calendar year")
    root = Path(root)
    report = json.loads((root / "provenance.json").read_text(encoding="utf-8"))
    if report.get("year") != year:
        raise ValueError("year mismatch")
    rows = report.get("source_monthly_files")
    if not isinstance(rows, list):
        raise ValueError("missing monthly provenance")
    verified = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError("invalid monthly entry")
        name = f"era5_{year}_{index:02d}_u10_v10_u100_v100.nc"
        if row.get("filename") != name:
            raise ValueError("missing, unordered or duplicate month")
        p = root / "original_monthly_netcdf" / name
        if not p.is_file() or p.is_symlink():
            raise ValueError("missing or linked private raw file")
        data = p.read_bytes()
        if len(data) != row.get("bytes") or hashlib.sha256(data).hexdigest() != row.get("sha256"):
            raise ValueError("raw monthly bytes/hash mismatch")
        hours = calendar.monthrange(year, index)[1] * 24
        if row.get("month_UTC_hours") != hours:
            raise ValueError("incorrect UTC month hours")
        if row.get("source_grid_latitude") != 52.5 or row.get("source_grid_longitude") != 3.5:
            raise ValueError("wrong source grid")
        if row.get("u10_v10_u100_v100_complete") is not True:
            raise ValueError("incomplete source fields")
        verified.append({"month": index, "utc_hours": hours, "raw_sha256": row["sha256"]})
    complete = len(verified) == 12
    hours = sum(row["utc_hours"] for row in verified)
    if complete and hours != YEARS[year]:
        raise ValueError("annual calendar inconsistency")
    if not complete and (report.get("status") == "SOURCE_RECONSTRUCTED_NOT_EXTERNALLY_REVIEWED"
                         or report.get("original_2023_wind_float64_reference_match") is True):
        raise ValueError("incomplete collection falsely claims annual acceptance")
    if complete and year == 2023 and report.get("original_2023_wind_float64_reference_match") is True:
        if report.get("normalized_wind_float64_SHA256") != EXPECTED_2023_SHA:
            raise ValueError("claimed 2023 frozen SHA mismatch")
    return {
        "schema_version": "ptxflex.private_era5_partial_independent_audit.v1",
        "year": year, "verified_months": verified,
        "verified_utc_hours": hours, "annual_calendar_complete": complete,
        "frozen_2023_source_match_independently_reproduced": False,
        "admitted_as_observed_full_year": False,
        "industrial_validation": False,
    }

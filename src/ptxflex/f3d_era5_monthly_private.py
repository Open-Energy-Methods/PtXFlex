"""Acquire exactly one ERA5 source month into an isolated private directory.

No annual admission, wind source equivalence or industrial validation is implied.
The existing full-year acquisition remains unchanged until independent review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from ptxflex.f3d_live_era5 import YEARS, request_for, load_original_month, f64sha


def acquire_month(year: int, month: int, output_root: str | Path, client=None) -> dict:
    request = request_for(year, month)
    root = Path(output_root).resolve()
    if root.exists():
        raise ValueError("refuse to overwrite private source directory")
    if client is None:
        key = os.environ.get("ERA5_API_KEY", "").strip()
        if len(key) <= 10:
            raise ValueError("ERA5_API_KEY unavailable")
        import cdsapi
        client = cdsapi.Client(url="https://cds.climate.copernicus.eu/api",
                               key=key, quiet=True, progress=False)
    rawdir = root / "original_monthly_netcdf"
    rawdir.mkdir(parents=True, exist_ok=False)
    target = rawdir / f"era5_{year}_{month:02d}_u10_v10_u100_v100.nc"
    report = {
        "schema_version": "ptxflex.f3d_era5_single_month_private.v1",
        "year": year, "month": month,
        "status": "INCOMPLETE_ORIGINAL_ERA5_SOURCE_COLLECTION",
        "source": "Copernicus ERA5 reanalysis-era5-single-levels",
        "source_monthly_files": [],
        "annual_calendar_complete": False,
        "original_2023_wind_float64_reference_match": None,
        "admitted_as_observed_full_year": False,
        "industrial_validation": False,
    }
    try:
        try:
            client.retrieve("reanalysis-era5-single-levels", request, str(target))
        except Exception as exc:
            raise RuntimeError(f"ERA5 {year}-{month:02d} retrieval failed ({type(exc).__name__}); provider details suppressed") from None
        wind, details = load_original_month(target, year, month)
        report["source_monthly_files"].append({
            "filename": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "bytes": target.stat().st_size, "cds_request": request, **details,
        })
        report["month_wind_float64_SHA256"] = f64sha(wind)
        report["month_UTC_hours"] = len(wind)
        return report
    finally:
        (root / "provenance.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True, choices=sorted(YEARS))
    parser.add_argument("--month", type=int, required=True, choices=range(1, 13))
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = acquire_month(args.year, args.month, args.output)
    print(json.dumps({"year": result["year"], "month": result["month"],
                      "hours": result["month_UTC_hours"],
                      "status": result["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()

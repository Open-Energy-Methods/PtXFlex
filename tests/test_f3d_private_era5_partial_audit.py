"""Offline synthetic regression tests: never imply these bytes are observed ERA5."""
import calendar
import hashlib
import json
from pathlib import Path
import pytest
from ptxflex.f3d_private_era5_partial_audit import audit_private_months


def fixture(root, year=2023, months=4):
    folder = root / "original_monthly_netcdf"
    folder.mkdir()
    rows = []
    for month in range(1, months + 1):
        name = f"era5_{year}_{month:02d}_u10_v10_u100_v100.nc"
        payload = (f"SYNTHETIC_NOT_NETCDF_{year}_{month}" * 10).encode()
        (folder / name).write_bytes(payload)
        rows.append(dict(filename=name, sha256=hashlib.sha256(payload).hexdigest(),
                         bytes=len(payload), month_UTC_hours=calendar.monthrange(year, month)[1] * 24,
                         source_grid_latitude=52.5, source_grid_longitude=3.5,
                         u10_v10_u100_v100_complete=True))
    report = dict(year=year, status="INCOMPLETE_ORIGINAL_ERA5_SOURCE_COLLECTION",
                  original_2023_wind_float64_reference_match=None, source_monthly_files=rows)
    (root / "provenance.json").write_text(json.dumps(report))
    return report


def test_four_months_are_integrity_checked_but_never_admitted(tmp_path):
    fixture(tmp_path)
    audit = audit_private_months(tmp_path, 2023)
    assert [m["month"] for m in audit["verified_months"]] == [1, 2, 3, 4]
    assert audit["verified_utc_hours"] == 2880
    assert audit["annual_calendar_complete"] is False
    assert audit["admitted_as_observed_full_year"] is False
    assert audit["frozen_2023_source_match_independently_reproduced"] is False


def test_leap_year_calendar(tmp_path):
    fixture(tmp_path, 2024, 2)
    assert audit_private_months(tmp_path, 2024)["verified_utc_hours"] == 1440


def test_tampering_detected(tmp_path):
    fixture(tmp_path)
    p = tmp_path / "original_monthly_netcdf" / "era5_2023_02_u10_v10_u100_v100.nc"
    p.write_bytes(p.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="bytes/hash"):
        audit_private_months(tmp_path, 2023)


def test_missing_month_detected(tmp_path):
    fixture(tmp_path)
    (tmp_path / "original_monthly_netcdf" / "era5_2023_02_u10_v10_u100_v100.nc").unlink()
    with pytest.raises(ValueError, match="missing or linked"):
        audit_private_months(tmp_path, 2023)


def test_unordered_month_detected(tmp_path):
    report = fixture(tmp_path)
    report["source_monthly_files"][0], report["source_monthly_files"][1] = report["source_monthly_files"][1], report["source_monthly_files"][0]
    (tmp_path / "provenance.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="unordered"):
        audit_private_months(tmp_path, 2023)


def test_false_annual_claim_rejected(tmp_path):
    report = fixture(tmp_path)
    report["status"] = "SOURCE_RECONSTRUCTED_NOT_EXTERNALLY_REVIEWED"
    (tmp_path / "provenance.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="falsely claims"):
        audit_private_months(tmp_path, 2023)


def test_wrong_grid_rejected(tmp_path):
    report = fixture(tmp_path)
    report["source_monthly_files"][0]["source_grid_longitude"] = 4.0
    (tmp_path / "provenance.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="grid"):
        audit_private_months(tmp_path, 2023)


def test_2023_frozen_sha_false_positive_rejected(tmp_path):
    report = fixture(tmp_path, months=12)
    report["original_2023_wind_float64_reference_match"] = True
    report["normalized_wind_float64_SHA256"] = "0" * 64
    (tmp_path / "provenance.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="frozen SHA"):
        audit_private_months(tmp_path, 2023)


def test_wrong_year_rejected(tmp_path):
    fixture(tmp_path)
    with pytest.raises(ValueError, match="year mismatch"):
        audit_private_months(tmp_path, 2022)

"""Synthetic isolated-month acquisition tests; never real provider observations."""
import json
from pathlib import Path

import numpy as np
import pytest

from ptxflex import f3d_era5_monthly_private as module


class FakeClient:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def retrieve(self, dataset, request, target):
        self.calls.append((dataset, request))
        if self.fail:
            raise RuntimeError("SECRET provider URL")
        Path(target).write_bytes(b"SYNTHETIC-NOT-NETCDF")


def fake_loader(path, year, month):
    assert Path(path).is_file()
    return np.arange(24, dtype=float), {
        "month_UTC_hours": 24, "source_grid_latitude": 52.5,
        "source_grid_longitude": 3.5, "u10_v10_u100_v100_complete": True,
    }


def test_isolated_month_never_admits_year(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "load_original_month", fake_loader)
    client = FakeClient()
    root = tmp_path / "private"
    report = module.acquire_month(2023, 4, root, client)
    assert len(client.calls) == 1
    assert client.calls[0][1]["month"] == ["04"]
    assert report["month_UTC_hours"] == 24
    assert report["annual_calendar_complete"] is False
    assert report["admitted_as_observed_full_year"] is False
    assert report["original_2023_wind_float64_reference_match"] is None
    assert len(report["source_monthly_files"]) == 1
    assert json.loads((root / "provenance.json").read_text()) == report


def test_existing_private_directory_never_overwritten(tmp_path):
    root = tmp_path / "exists"
    root.mkdir()
    (root / "sentinel").write_text("keep")
    with pytest.raises(ValueError, match="overwrite"):
        module.acquire_month(2023, 1, root, FakeClient())
    assert (root / "sentinel").read_text() == "keep"


def test_provider_exception_redacted_and_incomplete_manifest(tmp_path):
    root = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="details suppressed") as error:
        module.acquire_month(2023, 2, root, FakeClient(fail=True))
    assert "SECRET" not in str(error.value)
    report = json.loads((root / "provenance.json").read_text())
    assert report["source_monthly_files"] == []
    assert report["admitted_as_observed_full_year"] is False


@pytest.mark.parametrize("year,month", [(2021, 1), (2023, 0), (2024, 13)])
def test_invalid_calendar_rejected_before_io(tmp_path, year, month):
    with pytest.raises(ValueError):
        module.acquire_month(year, month, tmp_path / "output", FakeClient())
    assert not (tmp_path / "output").exists()

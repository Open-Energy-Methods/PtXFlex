"""F3-D private historical observation admission — synthetic fixtures ONLY.

These fixtures are demonstrably NOT actual ENTSO-E A44 or ERA5 observations.
They exercise the exact temporal/capacity/negative-price admission rules
so the repository never releases fake observed 2022 or leap-year 2024.
"""
from datetime import datetime,timedelta,timezone
import csv
import json
from pathlib import Path

import pytest
import ptxflex.f3d_external_observed_year_private_intake as m


def make_hours(path,year,field,*,value=42.,count=None,missing_at=None,duplicate_at=None):
    n=m.YEARS[year] if count is None else count
    start=datetime(year,1,1,tzinfo=timezone.utc)
    with Path(path).open("w",newline="",encoding="utf8") as f:
        w=csv.writer(f)
        w.writerow(["timestamp_utc",field])
        for i in range(n):
            t=i
            if missing_at is not None and i>=missing_at:t+=1
            if duplicate_at is not None and i==duplicate_at:t=i-1
            dt=start+timedelta(hours=t)
            w.writerow([m._hour_string(dt),value])


@pytest.mark.parametrize("year,count",[(2022,8760),(2024,8784)])
def test_exact_original_UCT_annual_hours_with_leap_feb29_kept(tmp_path,year,count):
    p=tmp_path/"price.csv"
    make_hours(p,year,"day_ahead_eur_mwh",value=-20.)
    x=m.validate_hourly_csv(p,year,"day_ahead_eur_mwh")
    assert x["hours"]==count
    assert x["first_hour_UTC"]==f"{year}-01-01T00:00:00Z"
    assert x["last_hour_UTC"]==f"{year}-12-31T23:00:00Z"
    assert x["negative_prices_retained"]
    assert len(x["float64_le_sha256"])==64


@pytest.mark.parametrize("year", [2022,2024])
def test_source_wind_power_original_turbine_farm_limit_and_nonnegative(tmp_path,year):
    p=tmp_path/"wind.csv"
    make_hours(p,year,"wind_available_mw",value=m.MAX_WIND_MW)
    a=m.validate_hourly_csv(p,year,"wind_available_mw",cap=m.MAX_WIND_MW)
    assert a["max_value_in_original_units"]==pytest.approx(125.685,abs=1e-12)
    assert a["negative_prices_retained"] is None


@pytest.mark.parametrize("year", [2022,2024])
def test_missing_or_shortened_source_year_rejected_even_leap_day(tmp_path,year):
    p=tmp_path/"missing.csv"
    make_hours(p,year,"wind_available_mw",value=50.,count=m.YEARS[year]-1)
    with pytest.raises(m.BadObservedHistoricalSource,match="missing year"):
        m.validate_hourly_csv(p,year,"wind_available_mw",cap=m.MAX_WIND_MW)


def test_duplicate_UTC_hour_rejected_no_dst_repair(tmp_path):
    p=tmp_path/"duplicate.csv"
    make_hours(p,2022,"day_ahead_eur_mwh",duplicate_at=2000)
    with pytest.raises(m.BadObservedHistoricalSource,match="missing/duplicate"):
        m.validate_hourly_csv(p,2022,"day_ahead_eur_mwh")


def test_absent_hour_midyear_rejected_no_forwardfill(tmp_path):
    p=tmp_path/"gap.csv"
    make_hours(p,2022,"wind_available_mw",value=54.,missing_at=2000)
    with pytest.raises(m.BadObservedHistoricalSource,match="missing/duplicate"):
        m.validate_hourly_csv(p,2022,"wind_available_mw",cap=m.MAX_WIND_MW)


@pytest.mark.parametrize("v",[-1.,float("nan"),float("inf"),125.686])
def test_invalid_ERA5_derived_wind_is_not_admissible_observed_generation(tmp_path,v):
    p=tmp_path/"wind.csv"
    make_hours(p,2022,"wind_available_mw",value=v)
    with pytest.raises(m.BadObservedHistoricalSource):
        m.validate_hourly_csv(p,2022,"wind_available_mw",cap=m.MAX_WIND_MW)


@pytest.mark.parametrize("year", [2023,2025])
def test_arbitrary_calendar_year_rejected_without_original_year_programme_registration(tmp_path,year):
    with pytest.raises(m.BadObservedHistoricalSource,match="supported"):
        m.validate_hourly_csv(tmp_path/"nothere.csv",year,"wind_available_mw")


def test_original_public_source_registry_explicitly_has_zero_new_years_no_fake_2022_2024():
    d=json.loads(m.REGISTER.read_text(encoding="utf-8"))
    assert d["schema_version"]=="oem.ptx.f3d_alternative_observed_2022_2024_entsoe_era5_private_source_admission.v1"
    assert d["years_requested"]==[2022,2024]
    assert d["current_total_accepted_alternative_year_price_and_wind_pairs"]==0
    assert not d["independent_historical_year_source_files_downloaded_and_verified"]
    assert not d["provider_price"]["provider_API_access_authorization_verified"]
    assert not d["provider_wind"]["provider_CDS_access_accepted"]
    assert d["year_requirements"]["2022"]["expected_UTC_hours"]==8760
    assert d["year_requirements"]["2024"]["expected_UTC_hours"]==8784
    assert not d["year_requirements"]["2024"]["independently_source_verified_price_and_wind_pair"]
    assert not d["full_F3_and_L3_v1_release_eligible"]


def test_private_source_not_assumed_when_research_provider_originals_unavailable(tmp_path):
    with pytest.raises(FileNotFoundError):
        m.admission(tmp_path/"no_actual_provider_source_manifest.json",tmp_path)


def test_private_source_digest_placeholders_and_bad_directory_rejected(tmp_path):
    f=tmp_path/"mock.txt";f.write_text("not public provider")
    with pytest.raises(m.BadObservedHistoricalSource):
        m.file_evidence(f,"0"*64,tmp_path)

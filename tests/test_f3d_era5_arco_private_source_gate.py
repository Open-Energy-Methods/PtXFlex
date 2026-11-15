"""Offline contract: ARCO is NOT 12 native CDS NetCDFs.

All test hourly weather vectors below are deliberately synthetic. A positive
hermetic test ONLY checks parser behavior and is NEVER evidence that observed
2022/24 Zarr has been retrieved or that original 2023 was independently
matched. Live qualification requires the user's private licensed source.
"""
import json

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from ptxflex import f3d_era5_arco_year as source
from ptxflex import f3d_live_provider_pair_gate as review
from ptxflex.f3d_era5_sharded_acquisition import PY_NEXUS_RECOVERED_2023_MONTH_SHA


def synthetic_source(tmp_path,year=2024):
    root=tmp_path/f"FAKE_LOCAL_SYNTHETIC_ARCO_{year}_NOT_OBSERVED"
    root.mkdir()
    hours=source.YEARS[year]
    arrays={
        "u10":np.full(hours,6.0,dtype=np.float32),
        "v10":np.full(hours,0.0,dtype=np.float32),
        "u100":np.full(hours,9.0,dtype=np.float32),
        "v100":np.full(hours,1.0,dtype=np.float32),
    }
    p=root/source.ARCO_SNAPSHOT_NAME.format(year=year)
    snapshot_sha=source.save_snapshot(p,arrays,year)
    wind=source.original_farm_mw_from_u100_v100(arrays["u100"],arrays["v100"])
    wind_csv_sha=source.write_utc_wind_csv(root/"normalized_UTC_wind.csv",year,wind)
    cal={
        "schema_version":source.SCHEMA_CAL,
        "status":source.CAL_ACCEPTED_STATUS,
        "year":2023,
        "source_url":source.ARCO_URL,
        "original_2023_1W_sha256_from_source_months":source.EXPECTED_2023_WIND_MICROMW_SHA,
        "ARCO_2023_1W_sha256":source.EXPECTED_2023_WIND_MICROMW_SHA,
        "modelled_wind_1W_identical_hours":8760,
        "full_8760h_2023_ARCO_matches_CDS_model_at_1W_and_four_component_tolerance":True,
        "original_source_calendar_UTC_hours":8760,
        "component_equivalence_within_1e_minus_5_m_per_s":{k:True for k in arrays},
        "original_2023_PyNEXUS_monthly_CDS_SHA256":{
            str(m):{"sha256":sha} for m,sha in PY_NEXUS_RECOVERED_2023_MONTH_SHA.items()},
    }
    receipt=root/"ARCO_2023_original_CDS_calibration_receipt.json"
    receipt.write_text(json.dumps(cal,sort_keys=True))
    d={
        "schema_version":source.SCHEMA_YEAR,
        "status":source.ARCO_ACCEPTED_STATUS,
        "year":year,
        "source_url":source.ARCO_URL,
        "source_CDS_netCDF_monthly_original":False,
        "source_ERA5_single_level_ARCO_repackaged_product":True,
        "full_UTC_calendar_year_no_gaps":True,
        "annual_UTC_hours":hours,
        "original_source_calendar_UTC_hours":hours,
        "complete_industrial_site_validation":False,
        "whole_plant_LCA_TEA_or_methanol_economic_release_allowed":False,
        "source_2023_full_calibration_file_SHA256":source.filehash(receipt),
        "source_point_netCDF_snapshot_SHA256":snapshot_sha,
        "source_coordinates_and_variables":{
            "latitude":52.5,"longitude":3.5,
            "field_names":{k:k for k in arrays},
        },
        "source_raw_ARCO_point_component_sha256":{
            k:source.sha_array(v) for k,v in arrays.items()},
        "source_raw_ARCO_point_component_dtype":{
            k:str(v.dtype) for k,v in arrays.items()},
        "normalized_wind_float64_SHA256":source.f64sha(wind),
        "normalized_wind_1W_quantized_SHA256":source.micro_mw_source_sha(wind),
        "normalized_csv_SHA256":wind_csv_sha,
    }
    (root/"provenance.json").write_text(json.dumps(d,sort_keys=True))
    return root,d


def test_arco_2024_leap_source_hermetic_parser_accepts_only_complete_fabricated_contract(tmp_path):
    p,d=synthetic_source(tmp_path,2024)
    r=review.verify_one(p,2024,"wind")
    assert r["full_UTC_hours"]==8784
    assert r["original_documents_count"]==1
    assert r["wind_provider_representation"].startswith("OFFICIAL_CDS_ARCO")
    assert r["actual_original_2022_2024_ARCO_historical_hourly_source_snapshot_verified"]
    assert r["normalized_float64_sha256"]==d["normalized_wind_float64_SHA256"]


def test_ARCO_2022_wrong_calibration_receipt_does_not_pass_source_verification(tmp_path):
    p,d=synthetic_source(tmp_path,2022)
    receipt=p/"ARCO_2023_original_CDS_calibration_receipt.json"
    cal=json.loads(receipt.read_text())
    cal["modelled_wind_1W_identical_hours"]=744
    receipt.write_text(json.dumps(cal))
    # Does not matter whether a manifest checksum is re-signed manually:
    # scientific gate rejects a January-only source calibration.
    d["source_2023_full_calibration_file_SHA256"]=source.filehash(receipt)
    with pytest.raises(ValueError,match="full 2023 source reanalysis"):
        review.verify_arco_alternate_year(p,2022,d)


def test_ARCO_raw_wind_mutation_does_not_bypass_independent_model_replay(tmp_path):
    p,d=synthetic_source(tmp_path,2024)
    src=p/source.ARCO_SNAPSHOT_NAME.format(year=2024)
    with xr.open_dataset(src) as handle:
        changed=handle.load()
    changed["u100"].values[99]+=np.float32(.125)
    src.unlink()
    changed.to_netcdf(src)
    # Even if original-file SHA is manually updated, recorded original U100
    # field SHA and 8760/8784 modelled wind SHA still fail.
    d["source_point_netCDF_snapshot_SHA256"]=source.filehash(src)
    with pytest.raises(ValueError,match="native-component SHA/dtype"):
        review.verify_arco_alternate_year(p,2024,d)


def test_ARCO_forbidden_claim_as_original_monthly_CDS_must_not_pass(tmp_path):
    p,d=synthetic_source(tmp_path,2022)
    d["source_CDS_netCDF_monthly_original"]=True
    with pytest.raises(ValueError,match="classification"):
        review.verify_arco_alternate_year(p,2022,d)


def test_ARCO_original_CDS_2023_month_hash_drift_fails_closed(tmp_path):
    p,d=synthetic_source(tmp_path,2022)
    receipt=p/"ARCO_2023_original_CDS_calibration_receipt.json"
    cal=json.loads(receipt.read_text())
    cal["original_2023_PyNEXUS_monthly_CDS_SHA256"]["4"]["sha256"]="f"*64
    receipt.write_text(json.dumps(cal))
    d["source_2023_full_calibration_file_SHA256"]=source.filehash(receipt)
    with pytest.raises(ValueError,match="twelve frozen CDS"):
        review.verify_arco_alternate_year(p,2022,d)

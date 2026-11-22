"""Observed 2023 wind and electricity-price ingestion from frozen PyNEXUS.

This module DOES NOT produce a solvable methanol scenario. It deliberately
leaves carbon intensity and all physical methanol engineering assumptions
undefined until independently sourced. The original PyNEXUS data represent
weather/market observations processed through a computational dispatch model,
not measurements of a real operating methanol or electrolyser plant.
"""
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

ORIGINAL_E_ZIP_SHA256 = "069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051"
ORIGINAL_E_STAGE_B_SHA256 = "a029a1049641d06afaea9703a7ec5abd5a41994fc0874a93be15348a17efe999"
ORIGINAL_PRICE_CSV_SHA256 = "2dfea4651fce314893201e7b08a4ae0ad24deef6b69ef85d81d9f54428f95bb2"
ORIGINAL_SOURCE_URL = "https://github.com/abhijith-sivaprasadan/PyNEXUS/actions/runs/40229852457"


def import_observed_2023(e_zip):
    raw=Path(e_zip).read_bytes()
    fingerprint=hashlib.sha256(raw).hexdigest()
    if fingerprint != ORIGINAL_E_ZIP_SHA256:
        raise ValueError("not the pinned original PyNEXUS observed-2023 E ZIP")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        manifest=json.loads(z.read("manifest.json"))
        record=json.loads(z.read("E/record.json"))
        if manifest.get("year")!=2023 or manifest.get("hours")!=8760 or not manifest.get("full_year"):
            raise ValueError("original source year/interval invalid")
        if record.get("status") != "VERIFIED_TWO_STAGE_SOLVE":
            raise ValueError("source Stage B not verified")
        if record.get("price_csv_sha256") != ORIGINAL_PRICE_CSV_SHA256:
            raise ValueError("original-price provider hash mismatch")
        b=z.read("E/stage_b.csv")
        if hashlib.sha256(b).hexdigest()!=ORIGINAL_E_STAGE_B_SHA256:
            raise ValueError("original E stage-b contents changed")
        reader=csv.DictReader(io.StringIO(b.decode("utf-8-sig")))
        cols=("timestep","wind_available_mw","electricity_price")
        if not set(cols).issubset(reader.fieldnames or []):
            raise ValueError("missing original measured input columns")
        hourly=[]
        epoch=datetime(2023,1,1,tzinfo=timezone.utc)
        for i,row in enumerate(reader):
            if int(row["timestep"]) != i:
                raise ValueError("missing or misaligned original hourly timestep")
            wind=float(row["wind_available_mw"])
            price=float(row["electricity_price"])
            if not math.isfinite(wind) or wind<0 or not math.isfinite(price):
                raise ValueError("missing or invalid source wind/price observation")
            hourly.append({
                "timestamp_utc":(epoch+timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "wind_available_mwh":wind,  # 1h interval -> MW converted to MWh
                "grid_price_eur_mwh":price,
                "grid_gwp_kgco2e_mwh":None,
                "wind_gwp_kgco2e_mwh":None,
            })
        if len(hourly)!=8760:
            raise ValueError("not 8760 original hourly time steps")
        return {
            "schema_version":"ptxflex.verified_historical_inputs.v0.1",
            "source":"PyNEXUS observed-price WP5 source E, 2023 NL",
            "original_archive_sha256":fingerprint,
            "original_stage_b_sha256":ORIGINAL_E_STAGE_B_SHA256,
            "original_provider_price_sha256":ORIGINAL_PRICE_CSV_SHA256,
            "original_source_url":ORIGINAL_SOURCE_URL,
            "source_license":"PyNEXUS source MIT; original ERA5/ENTSO-E providers retain attribution/data rights",
            "observed_inputs":"ERA5-derived wind, NL ENTSO-E 2023 hourly A44 electricity prices",
            "not_observed":"industrial hydrogen, CO2 or methanol process operation",
            "utc_alignment_warning":manifest.get("hourly_alignment_assumption"),
            "year":2023,"time_step_hours":1,"row_count":8760,
            "hydrogen_system_origin":"wind farm and electricity market input only",
            "source_size_and_units":"wind MWh available (from MW x 1h), price EUR/MWh",
            "missing_required_for_milp":[
                "hourly grid and wind GWP of consistent method and geographic scope",
                "documented methanol reactor capacity, auxiliary load, CO2 source and supply",
                "physical H2 storage, synthesis ramp/min load, delivered methanol service"
            ],
            "solver_ready":False,
            "hourly":hourly,
        }


def write_import(archive, output_file):
    out=Path(output_file)
    if out.exists():
        raise FileExistsError("refusing to overwrite original-evidence import")
    data=import_observed_2023(archive)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return {"output":str(out),"source_sha256":data["original_archive_sha256"],
            "hours":len(data["hourly"]),"solver_ready":False}

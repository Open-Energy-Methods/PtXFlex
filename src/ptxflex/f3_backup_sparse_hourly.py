"""Source-derived sparse 8760-hour H2 demand trace for a prospective backup interface.

Reads the actual original-source 2023 E shortage vector from the hash-pinned
Stage A GitHub Actions artifact. Preserves positive shortage hours as sparse
(index, kg) records; all remaining 8760 indices are exactly zero. Does not
copy any original 2023 wind/price/ENTSO-E provider data. This is a modelled
need, NOT a physically available H2 external supplier dispatch.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SCHEMA="ptxflex.f3_2023_sparse_modelled_backup_hourly_need.v1"
E_SHA="069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051"
ES_SHA="cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9"
EXPECTED_ARTIFACT_ZIP_SHA={
    "max_inventory":"6731bdaeeaa01a531f577150815dcf6638c15d21bc0ccee5e9ac0fa748ffe3c8",
    "usable_service":"18dec140df7cab63dd9cae8836e3f23fd2dcfb0370acd48db0e36e6af81813cd",
}
EXPECTED_BACKUP_SUMMARY_SHA={
    "max_inventory":"c65fda894ef4b30e09339ad88a3972625af78c17802fd0cb9a2fc25d3205882f",
    "usable_service":"d893c6388f14d276b2ef5d4bff4b6c8057dd252067f307f83b9baafcfa1e5308"
}
REFERENCE_TARGET_KG=16335279.317376737
ZERO_THRESHOLD_KG_H=1e-5


class InvalidOriginalHourlyShortage(ValueError):
    pass


def _num(x,label):
    if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x):
        raise InvalidOriginalHourlyShortage(label+" is non-finite source value")
    return float(x)


def _events(mask):
    events=[]
    start=None
    for i,b in enumerate(mask):
        if b and start is None:start=i
        if not b and start is not None:
            events.append([start,i-1]);start=None
    if start is not None:events.append([start,len(mask)-1])
    return events


def extract_verified_sparse_h2_need(mode,source,summary,*,artifact_zip_sha256):
    if mode not in EXPECTED_ARTIFACT_ZIP_SHA or artifact_zip_sha256!=EXPECTED_ARTIFACT_ZIP_SHA[mode]:
        raise InvalidOriginalHourlyShortage("Stage A original 2023 derived source ZIP digest mismatch")
    if (source.get("derived_source_not_original_raw_prices_or_wind") is not True
        or source.get("source_E_delivered_reference_profile_is_modelled") is not True):
        raise InvalidOriginalHourlyShortage("original 2023 H2 data classification missing")
    if (summary.get("schema_version")!="ptxflex.F3_2023_hypothetical_source_hourly_H2_backup_load_envelope.v1"
        or summary.get("capacity_semantics")!=mode
        or summary.get("source_E_zip_sha256")!=E_SHA
        or summary.get("source_EplusS_zip_sha256")!=ES_SHA
        or summary.get("matched_service_LCA_TEA_comparison_permitted") is not False):
        raise InvalidOriginalHourlyShortage("certified historic 2023 E/ES H2 source summary changed")
    if abs(_num(summary.get("source_2023_original_E_reference_delivered_kg"),"reference service")-REFERENCE_TARGET_KG)>.002:
        raise InvalidOriginalHourlyShortage("source 2023 frozen original E delivery target altered")
    vals=source.get("hourly_additional_shortfall_kg")
    if not isinstance(vals,list) or len(vals)!=8760:
        raise InvalidOriginalHourlyShortage("full original 2023 hourly source model must have exactly 8760 rows")
    raw=[_num(v,"hour "+str(i)) for i,v in enumerate(vals)]
    if min(raw)<-1e-5:
        raise InvalidOriginalHourlyShortage("negative source additional H2 shortfall")
    cleaned=[v if v>ZERO_THRESHOLD_KG_H else 0.0 for v in raw]
    cumulative=sum(cleaned)
    annual=_num(summary.get("single_incumbent_hypothetical_topup_annual_kg"),"annual topup")
    if abs(cumulative-annual)>.002:
        raise InvalidOriginalHourlyShortage("sparse 8760 source hourly shortage does not close annual mass")
    active=[{"hour_index_0_based":i,"additional_modelled_H2_kg":v} for i,v in enumerate(cleaned) if v>0]
    if len(active)!=summary.get("single_incumbent_hypothetical_topup_occupied_hours"):
        raise InvalidOriginalHourlyShortage("positive source original hour count inconsistent")
    active_events=_events([x>0 for x in cleaned])
    if active_events!=summary.get("single_incumbent_contiguous_events_0_indexed_inclusive"):
        raise InvalidOriginalHourlyShortage("source interruption sequence changed")
    peak24=max(sum(cleaned[i:i+24]) for i in range(8760-23))
    if abs(peak24-_num(summary.get("single_incumbent_hypothetical_topup_24h_peak_kg"),"peak24"))>.002:
        raise InvalidOriginalHourlyShortage("peak 24h source backup need differs from verified Stage B")
    if abs(max(cleaned)-_num(summary.get("single_incumbent_hypothetical_topup_max_kg_per_hour"),"peak hour"))>.002:
        raise InvalidOriginalHourlyShortage("source hourly peak inconsistent")
    return {
        "schema_version":SCHEMA,
        "source_model_E_zip_sha256":E_SHA,
        "source_model_E_plus_S_zip_sha256":ES_SHA,
        "source_stageA_artifact_zip_sha256":artifact_zip_sha256,
        "source_registered_stageB_derived_summary_sha256":EXPECTED_BACKUP_SUMMARY_SHA[mode],
        "capacity_semantics":mode,
        "original_source_year":2023,
        "reference_delivery_is_original_E_modelled_not_full_18_25Mt_contract":True,
        "original_E_delivered_target_kg":REFERENCE_TARGET_KG,
        "source_8760_hourly_count":8760,
        "source_hour_index_is_zero_based_and_not_fabricated_date_time":True,
        "zero_kg_h_at_all_hours_not_listed":True,
        "numeric_zero_clamping_threshold_kg_h":ZERO_THRESHOLD_KG_H,
        "positive_H2_topup_needed_kg_by_0_based_source_hour":active,
        "modelled_additional_annual_topup_for_feasible_incumbent_kg":cumulative,
        "source_incumbent_peak_kg_h":max(cleaned),
        "source_incumbent_max_rolling_24h_kg":peak24,
        "positive_hours":len(active),
        "event_count":len(active_events),
        "modelled_need_not_actual_hydrogen_supplier_delivery":True,
        "actual_supplier_capacity_and_quality_pressure_checked":False,
        "source_2026_network_not_observed_2023_H2_supply":True,
        "full_LCA_TEA_qualified":False,
        "external_supply_kgCO2e_per_kg":None,
        "external_supply_EUR_per_kg":None
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--hourly",required=True)
    p.add_argument("--summary",required=True)
    p.add_argument("--mode",required=True,choices=tuple(EXPECTED_ARTIFACT_ZIP_SHA))
    p.add_argument("--artifact-zip-sha256",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    dest=Path(a.output)
    if dest.exists():raise FileExistsError("never overwrite original-source-derived 8760h backup model")
    data=extract_verified_sparse_h2_need(a.mode,json.loads(Path(a.hourly).read_text()),
         json.loads(Path(a.summary).read_text()),artifact_zip_sha256=a.artifact_zip_sha256)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(a.mode,"ORIGINAL-SOURCE H2 modelled hourly need source rows:",data["source_8760_hourly_count"],
          "positive hours:",data["positive_hours"],"annual kg:",data["modelled_additional_annual_topup_for_feasible_incumbent_kg"])


if __name__=="__main__":
    main()

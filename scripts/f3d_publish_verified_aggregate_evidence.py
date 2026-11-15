"""Export a PUBLIC, reproducible, independently replayed F3-D evidence summary.

NEVER copy original provider NetCDF/XML/CSV, hourly solver primal, or arbitrary
private JSON. All output is constructed by an explicit field-by-field whitelist.
Private data remain exclusively in ~/PtX_PRIVATE_RESEARCH.

Only local source-verified, fully solved real 2022/2024 cases may be exported.
The physical replay runs again locally from private source arrays and witnesses
via PtXLens; private witness and original sources are hashed, not embedded.
This is NOT native BAFU LCA, manufacturer CAPEX or investment profitability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

from ptxflex.f3d_live_provider_pair_gate import verify_pair
from ptxlens.f3d_external_year_independent_review import (
    check_result,review_four_cases,
)
from ptxlens.f3d_external_year_private_witness_replay import review_private_witness

SCHEMA="oem.ptx.f3d_2022_2024_public_source_aggregate_independent_replay.v1"
PUBLIC_JSON="F3D_ARCO_2022_2024_PUBLIC_VERIFIED_AGGREGATES_v1.json"
PUBLIC_MD="F3D_ARCO_2022_2024_PUBLIC_VERIFIED_RESULTS_v1.md"
YEARS=(2022,2024)
MODES=("max_inventory","usable_service")
REFERENCE_WIND_SHA="9e0e95ddf9c70547ab6ce696f52a82dc312f11d7cd760de5dc779c6ac2b43c9c"
EXPECTED_HOURS={2022:8760,2024:8784}


class PublicExportError(ValueError):
    pass


def require(value,reason):
    if not value:
        raise PublicExportError("F3-D safe public evidence: "+reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as source:
        while block:=source.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def read(path):
    path=Path(path)
    require(path.is_file() and not path.is_symlink(),
            "private review artifact missing/unsafe: "+path.name)
    return json.loads(path.read_text(encoding="utf-8"))


def finite_number(x,label,*,nonnegative=False):
    require(type(x) in (float,int) and math.isfinite(x),
            "invalid numeric aggregate: "+label)
    x=float(x)
    require(not nonnegative or x>=-1e-9,
            "negative physical aggregate: "+label)
    return x


def verify_review_receipt(receipt,year,mode):
    require(receipt.get("year")==year and receipt.get("mode")==mode and
            receipt.get("original_year_UTC_hours")==EXPECTED_HOURS[year] and
            receipt.get("E_source_year_price_blind_service_primal_recomputed") is True and
            receipt.get("E_source_year_E_and_ES_full_hourly_primal_mass_energy_cost_recomputed") is True and
            receipt.get("20_200bar_CoolProp_independent_EOS_extrema_recomputed") is True and
            receipt.get("cost_bounds_and_price_neutral_alpha_global_dual_reoptimized_independently") is False and
            receipt.get("source_hourly_primal_arrays_NOT_in_this_report") is True and
            receipt.get("on_site_industrial_or_native_BAFU_LCA_full_release") is False,
            "independent full-year primal/EOS audit failed or scientific scope changed")
    require(set(receipt.get("case_audits",{}))=={"E","E_plus_S"},
            "both E and E+S original hourly physical audit cases required")


def selected_case(report,metadata,physical,year,mode,source_pair,paths):
    require(report["year"]==year and report["capacity_semantics"]==mode and
            report["year_UTC_hours"]==EXPECTED_HOURS[year],
            "report year/mode/hour mismatch")
    require(report["v1_0_scientific_release_allowed"] is False and
            report["installed_plant_LCOH_or_investment_DCF_certified"] is False and
            report["vendor_200bar_compressor_and_storage_station_BOM_verified"] is False and
            report["native_BAFU_whole_plant_GWP_verified"] is False,
            "cannot publish reports that claim unverified CAPEX/LCA/DCF/v1 scope")
    require(metadata["year"]==year and metadata["capacity_semantics"]==mode and
            metadata["metadata_arithmetic_model_scope_review_passed"] is True and
            metadata["independent_source_NetCDF_XML_or_dispatch_primal_replay_completed"] is False,
            "independent metadata scope changed")
    verify_review_receipt(physical,year,mode)
    require(physical["price_hourly_original_SHA256"]==
            report["source_year_price_f64_sha256"]==
            source_pair["year_price"]["normalized_float64_sha256"] and
            physical["wind_hourly_original_SHA256"]==
            report["source_year_wind_f64_sha256"]==
            source_pair["year_wind"]["normalized_float64_sha256"],
            "private provider price/wind hashes differ across sources and reviewers")
    sel=report["E_price_blind_identical_model_H2_service_selection"]
    require(physical["selected_hourly_H2_sha256"]==
            sel["selected_h2_target_float64_sha256"],
            "selector hourly H2 source target SHA disagrees with reviewer")
    alpha=finite_number(sel["selected_fraction_50t_per_day"],"alpha",nonnegative=True)
    alpha_ub=finite_number(sel["certified_fraction_upper_bound"],"alpha upper",nonnegative=True)
    gap=finite_number(sel["E_price_neutral_mip_relative_gap"],"alpha gap",nonnegative=True)
    require(0<alpha<=alpha_ub+1e-7<=1.01 and gap<=1e-6,
            "price-neutral H2 selection lacks stringent optimality/scope gate")
    annual=finite_number(sel["modelled_E_annual_h2_service_kg"],"annual H2",nonnegative=True)
    require(abs(annual-EXPECTED_HOURS[year]*(50000/24)*alpha)<=0.005,
            "annual selected H2 kg differs from hour-for-hour 50 t/day fraction")
    econ={}
    for name in ("E","E_plus_S"):
        d=report[name]
        auditing=physical["case_audits"][name]
        # The physical dictionary is NOT exported: it contains internal
        # privately-derived scalar extrema, timestamps and data hashes.
        require(auditing["hourly_states_sha256"]==
                d["source_hourly_dispatch_float64_sha256"],
                "hourly dispatch original-private witness mismatch: "+name)
        cost=finite_number(d["modelled_cost_eur_in_source_calendar_not_inflation_adjusted"],name+" cost")
        lower=finite_number(d["solver_cost_lower_bound_eur"],name+" cost lower")
        mip_gap=finite_number(d["mip_relative_gap"],name+" cost gap",nonnegative=True)
        require(lower<=cost+0.1 and mip_gap<=1e-6,
                "solver-reported cost primal/dual not mathematically bounded")
        econ[name]={
            "modelled_nominal_eur_wholesale_cost":cost,
            "solver_reported_cost_dual_lower_bound_eur":lower,
            "solver_reported_relative_mip_gap":mip_gap,
            "modelled_h2_delivered_kg":finite_number(d["modelled_annual_hydrogen_kg"],name+" H2",nonnegative=True),
            "modelled_grid_import_mwh":finite_number(d["modelled_grid_import_mwh"],name+" import",nonnegative=True),
            "modelled_grid_export_mwh":finite_number(d["modelled_grid_export_mwh"],name+" export",nonnegative=True),
            "modelled_compressor_electricity_mwh":finite_number(d["modelled_compressor_electricity_mwh"],name+" compressor",nonnegative=True),
            "modelled_h2_storage_peak_kg":finite_number(d["modelled_hydrogen_storage_peak_kg"],name+" peak",nonnegative=True),
            "maximum_ptxflex_independent_mass_energy_residual":finite_number(d["max_independent_residual"],name+" residual",nonnegative=True),
            "private_hourly_primal_sha256":d["source_hourly_dispatch_float64_sha256"],
        }
        require(abs(econ[name]["modelled_h2_delivered_kg"]-annual)<0.005,
                "E and E+S have unequal H2 delivery")
    s=finite_number(report["cost_savings_E_minus_EplusS_source_calendar_nominal_eur"],
                    "paired cost saving")
    b=report["solver_difference_guaranteed_lower_upper_interval_eur"]
    require(isinstance(b,list) and len(b)==2,"solver-reported savings bounds missing")
    low=finite_number(b[0],"lower paired savings")
    high=finite_number(b[1],"upper paired savings")
    e=econ["E"]; es=econ["E_plus_S"]
    require(abs(s-(e["modelled_nominal_eur_wholesale_cost"]-es["modelled_nominal_eur_wholesale_cost"]))<.01 and
            abs(low-(e["solver_reported_cost_dual_lower_bound_eur"]-es["modelled_nominal_eur_wholesale_cost"]))<.01 and
            abs(high-(e["modelled_nominal_eur_wholesale_cost"]-es["solver_reported_cost_dual_lower_bound_eur"]))<.01 and
            low-.02<=s<=high+.02 and
            abs(s-metadata["paired_operational_savings_2022_or_2024_nominal_eur"])<.01,
            "independent financial cost or reported primal/dual bounds inconsistent")
    require(source_pair["source_price_and_weather_calendar_and_original_hashes_verified"] is True and
            source_pair["year_wind_alternate_ARCO_calibrated_2023_original_8760h"] is True,
            "source-year 2023 original full ARCO calibration missing")
    return {
        "year":year,
        "storage_capacity_semantics":mode,
        "year_utc_hours":EXPECTED_HOURS[year],
        "source_calendar":"ENTSO-E NL A44 electricity price + Copernicus ERA5 ARCO 0.25 degree point",
        "source_year_price_f64_sha256":report["source_year_price_f64_sha256"],
        "source_year_wind_f64_sha256":report["source_year_wind_f64_sha256"],
        "price_neutral_E_uniform_hydrogen_service":{
            "fraction_of_nominal_50_tonnes_per_day":alpha,
            "solver_reported_upper_bound_on_fraction":alpha_ub,
            "solver_reported_relative_optimality_gap":gap,
            "maximum_modelled_delivered_h2_kg_per_hour":
                finite_number(sel["modelled_E_flat_h2_service_kg_per_hour"],"H2/h",nonnegative=True),
            "modelled_delivered_h2_kg_per_year":annual,
            "modelled_delivered_h2_tonnes_per_day":alpha*50,
            "hourly_target_f64_sha256":sel["selected_h2_target_float64_sha256"],
            "selector_certificate_method":str(
                sel.get("E_max_service_global_optimality_certificate_method",
                        "HIGHS_ORIGINAL_FULL_INTEGER_MIP_PRIMAL_DUAL_LEGACY_NOT_RECORDED")),
        },
        "E":e,
        "E_plus_S":es,
        "matched_service_annual_operational_savings_nominal_eur":s,
        "savings_modelled_nominal_eur_per_kg_of_same_h2_service":s/annual,
        "solver_reported_savings_lower_eur":low,
        "solver_reported_savings_upper_eur":high,
        "independent_full_hourly_E_and_EplusS_primal_replay_passed":True,
        "independent_full_hourly_type_I_20_to_200bar_EOS_replay_passed":True,
        "source_original_hash_and_calendar_gate_passed":True,
        "independent_solver_dual_certificates_recomputed":False,
        "source_report_json_sha256":sha(paths["report"]),
        "source_private_primal_json_sha256_only_not_exported":sha(paths["witness"]),
        "source_independent_physical_review_json_sha256":sha(paths["review"]),
        "source_original_provider_pair_receipt_sha256":sha(paths["pair"]),
    }


def require_safe_output_structure(result):
    """Prevent accidental inclusion of long arrays or raw provider files."""
    def visit(node,trail="root"):
        if isinstance(node,list):
            require(len(node)<=4,"unexpected potential hourly array: "+trail)
            for i,x in enumerate(node):visit(x,f"{trail}/{i}")
        elif isinstance(node,dict):
            forbidden=("hourly_states","target_hourly_kg","original_xml",
                       "normalized_UTC_price","normalized_UTC_wind",
                       "cost_optimum_hourly_states","token","api_key","secret")
            for k,v in node.items():
                require(not any(x in k.casefold() for x in forbidden),
                        "non-public raw source key in export: "+k)
                visit(v,trail+"/"+k)
        elif isinstance(node,str):
            require(len(node)<400 and "\n" not in node,
                    "unexpected unbounded private string at "+trail)
        else:
            require(node is None or type(node) in (int,float,bool),
                    "non-serializable or unsafe private source structure")
    visit(result)
    json.dumps(result,allow_nan=False,sort_keys=True)


def make_report(blob):
    cases=blob["cases"]
    header=[
        "# F3-D: Independent replay of historical ARCO/ENTSO-E matched-service calculations",
        "",
        "## Source status and scope",
        "",
        "Observed-data weather and market source years: **2022 and leap-year 2024**. "
        "Official Copernicus ERA5 ARCO is the reanalysis point representation, "
        "**not** original CDS monthly NetCDF bytes or measured site weather. "
        "2023 full-year Copernicus ARCO matched original source CDS-derived "
        "farm power at 1-W resolution over 8,760 UTC hours.",
        "",
        "The export was generated by re-running the source-calendar/hash checks "
        "and independent hourly PtXLens physical/cost replay locally; the "
        "original hourly data, private primal witnesses, provider XML/NetCDF "
        "and authentication tokens were never copied.",
        "",
        "## Matched-service results",
        "",
        "| Source year | Capacity interpretation | Selected modelled H2 (t/day) | "
        "Annual H2 (tonnes) | E minus E+S savings (nominal EUR) | "
        "Savings (EUR/kg H2) | Solver savings bounds (EUR) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in cases:
        m=r["price_neutral_E_uniform_hydrogen_service"]
        header.append(
            f"| {r['year']} | {r['storage_capacity_semantics']} | "
            f"{m['modelled_delivered_h2_tonnes_per_day']:.3f} | "
            f"{m['modelled_delivered_h2_kg_per_year']/1000:.1f} | "
            f"{r['matched_service_annual_operational_savings_nominal_eur']:,.2f} | "
            f"{r['savings_modelled_nominal_eur_per_kg_of_same_h2_service']:.4f} | "
            f"[{r['solver_reported_savings_lower_eur']:,.2f}, "
            f"{r['solver_reported_savings_upper_eur']:,.2f}] |"
        )
    header += [
        "",
        "## Independent validation",
        "",
        "Each of the four original hourly E/E+S primal solutions and the "
        "price-neutral E service-selector witness were re-audited by PtXLens. "
        "The audit checked H2 delivery, mass and electricity balances, "
        "source-year grid settlement, compressor duty and the Type I 20–200 bar "
        "CoolProp hydrogen EOS screening extrema. Both year-specific price and "
        "wind provider source calendars/hashes were rechecked.",
        "",
        "**Limitation:** HiGHS-reported cost lower bounds and the selector's "
        "global optimality gap were checked arithmetically but their optimizer "
        "dual certificates were **not independently solved or reconstructed**. "
        "The interval is a **solver-reported** economic savings bound, not an "
        "independently peer-certified confidence interval.",
        "",
        "## Economic comparability and limitations",
        "",
        "Within one year and one capacity interpretation, E and E+S have "
        "identical hourly modelled H2 service. **Across** years or storage "
        "capacity interpretations, the maximum price-blind feasible service "
        "fraction can differ. Compare EUR/kg of modelled delivered H2 as well "
        "as annual nominal EUR; do not attribute differences solely to prices.",
        "",
        "2022 and 2024 prices are nominal source-calendar EUR, not CPI-normalized. "
        "The figures are operational net-grid electricity-cost differences "
        "**before** incremental storage installation CAPEX, fixed/variable "
        "maintenance OPEX, financing, taxes, plant construction, risk or "
        "decommissioning costs. There are no manufacturer quotes or verified "
        "native BAFU whole-plant inventories in this evidence.",
        "",
        "No measured industrial H2 operation, whole-plant investment NPV, "
        "full LCA/LCIA GWP or scientific v1.0 release is certified. "
        "This is a reproducible numerical source-model study.",
        "",
        "## Machine-readable source record",
        "",
        "The adjacent allowlisted JSON contains exact year/mode scalars, "
        "provider-array SHA256 fingerprints, modelled cost/energy aggregates, "
        "solver-reported cost bounds, and SHA256 checksums of the **private** "
        "replayed reports and primal witnesses (not their contents). "
        "Use it for F3-D scientific reporting and **scenario-only** L3 "
        "discounted-cash-flow sensitivity work.",
        "",
    ]
    return "\n".join(header)


def build(private_root):
    private_root=Path(private_root).resolve(strict=True)
    require(private_root.is_dir(),"private original source directory missing")
    result_root=private_root/"results"
    all_reports=[]
    cases=[]
    for year in YEARS:
        price_root=private_root/f"price-{year}"
        wind_root=private_root/f"wind-arco-{year}"
        pair_cert=result_root/f"source-pair-ARCO-{year}.json"
        require(read(pair_cert).get("source_price_and_weather_calendar_and_original_hashes_verified") is True,
                "year original provider pair receipt absent")
        pair=verify_pair(
            year,price_root,wind_root,private_root/"price-2023",
            private_root/"wind-2023-recovered"/"complete")
        for mode in MODES:
            paths={
                "report":result_root/f"F3D_ARCO_{year}_{mode}.json",
                "witness":result_root/f"PRIVATE_F3D_ARCO_{year}_{mode}_primal.json",
                "review":result_root/f"PtXLens_ARCO_{year}_{mode}_physical.json",
                "pair":pair_cert,
            }
            record=read(paths["report"])
            check=check_result(record)
            fresh=review_private_witness(
                paths["witness"],paths["report"],
                price_root/"normalized_UTC_price.csv",
                wind_root/"normalized_UTC_wind.csv")
            stored=read(paths["review"])
            require(stored==fresh,
                    "existing independent replay differs from new private replay")
            cases.append(selected_case(record,check,fresh,year,mode,pair,paths))
            all_reports.append(paths["report"])
    rechecked=review_four_cases(all_reports)
    stored_review=read(result_root/"PtXLens_four_case_ARCO_years_independent.json")
    require(stored_review==rechecked and
            rechecked["all_four_scenario_metadata_financial_source_scope_gates_passed"] is True and
            rechecked["original_source_lca_tea_safety_and_v1_0_still_blocked"] is True,
            "four-case independent economic scope review does not match stored output")
    source2023=read(private_root/"wind-arco-2023-calibration"/"provenance.json")
    require(source2023.get("status")=="ARCO_FULL_2023_8760H_CDS_NUMERICALLY_EQUIVALENT_1W" and
            source2023.get("modelled_wind_1W_identical_hours")==8760 and
            source2023.get("original_2023_1W_sha256_from_source_months")==REFERENCE_WIND_SHA,
            "full 2023 original CDS-to-ARCO original reference failed")
    out={
        "schema_version":SCHEMA,
        "study":"F3-D PtXFlex-PtXLens 2022/2024 source-year hourly matched-service E vs E+S",
        "2023_CDS_to_ARCO_8760_hour_1W_source_reference_SHA256":REFERENCE_WIND_SHA,
        "2023_CDS_to_ARCO_full_year_original_source_calibration_passed":True,
        "2023_CDS_to_ARCO_private_full_year_provenance_sha256":sha(
            private_root/"wind-arco-2023-calibration"/"provenance.json"),
        "source_calendar_and_source_representation":
            "2022/2024 NL ENTSO-E A44 day-ahead EUR/MWh and Copernicus ERA5 ARCO geo-chunked hourly offshore wind, 52.5N, 3.5E",
        "nominal_reference_h2_contract_tonnes_per_day":50.0,
        "source_original_hourly_arrays_released":False,
        "private_hourly_primal_witnesses_released":False,
        "independent_year_mode_full_hourly_primal_E_EplusS_and_EOS_replay_passed":True,
        "independent_financial_metadata_four_case_review_passed":True,
        "independent_solver_dual_certificates_recomputed":False,
        "original_historical_prices_not_CPI_adjusted":True,
        "manufacturer_storage_incremental_CAPEX_OPEX_verified":False,
        "native_BAFU_2026_whole_plant_LCIA_verified":False,
        "real_industrial_site_H2_validation_completed":False,
        "installed_plant_investment_DCF_certified":False,
        "scientific_v1_0_release_allowed":False,
        "cases":cases,
        "original_private_four_case_metadata_review_SHA256":sha(
            result_root/"PtXLens_four_case_ARCO_years_independent.json"),
    }
    require_safe_output_structure(out)
    return out


def write_outputs(out,output_dir):
    output_dir=Path(output_dir)
    require(output_dir.is_dir() and not output_dir.is_symlink(),
            "explicit public evidence destination must already exist")
    js=json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+"\n"
    md=make_report(out)
    jobs=[(output_dir/PUBLIC_JSON,js),(output_dir/PUBLIC_MD,md)]
    for path,payload in jobs:
        if path.exists():
            require(path.is_file() and not path.is_symlink() and
                    path.read_text(encoding="utf-8")==payload,
                    "existing published aggregate differs; review source changes before new version: "+path.name)
    for path,payload in jobs:
        if not path.exists():
            with path.open("x",encoding="utf-8",newline="\n") as f:
                f.write(payload)
    print("F3D_PUBLIC_AGGREGATE_SAFE_EXPORT_VALIDATED",len(out["cases"]),
          "cases; four PtXLens hourly private replays re-executed; no original arrays or witness copied")
    for path,_ in jobs:
        print("  PUBLIC_REVIEWED_FILE",path)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root",default=str(Path.home()/"PtX_PRIVATE_RESEARCH"))
    parser.add_argument("--public-output-dir",required=True)
    args=parser.parse_args(argv)
    private=Path(args.private_root).resolve(strict=True)
    destination=Path(args.public_output_dir).resolve(strict=True)
    require(private!=destination and
            private not in destination.parents and
            destination not in private.parents,
            "original private source and public destination paths cannot overlap")
    require(destination.name=="research" and
            (destination.parent/"pyproject.toml").is_file(),
            "destination must be repository research/ directory, not a private source folder")
    write_outputs(build(private),destination)


if __name__=="__main__":
    main()

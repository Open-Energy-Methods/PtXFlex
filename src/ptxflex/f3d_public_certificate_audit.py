"""Independent privacy-preserving F3-D public certificate check; no source-data or solver rerun."""
import math

YEARS={2022:8760,2024:8784}
SCHEMA="ptxflex.f3d_2022_2024_equal_hourly_model_service_pressure_screening.v1"

def number(x,label):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):
        raise ValueError(label+": nonfinite/non-numeric")
    return float(x)

def audit(report):
    if report.get("schema_version")!=SCHEMA: raise ValueError("schema")
    year=report.get("year")
    if year not in YEARS or report.get("year_UTC_hours")!=YEARS[year]: raise ValueError("UTC calendar")
    if report.get("capacity_semantics") not in ("max_inventory","usable_service"): raise ValueError("capacity semantics")
    if report.get("mathematically_matched_exact_same_modelled_hourly_H2_target") is not True: raise ValueError("matched service flag")
    s=report["E_price_blind_identical_model_H2_service_selection"]
    alpha=number(s["selected_fraction_50t_per_day"],"fraction")
    upper=number(s["certified_fraction_upper_bound"],"fraction bound")
    if not 0<=alpha<=upper+1e-7 or upper>1.000001: raise ValueError("fraction bounds")
    annual=number(s["modelled_E_annual_h2_service_kg"],"annual service")
    if abs(annual-YEARS[year]*50000/24*alpha)>.01: raise ValueError("annual service")
    h=s["selected_h2_target_float64_sha256"]
    if not isinstance(h,str) or len(h)!=64 or any(c not in "0123456789abcdef" for c in h): raise ValueError("service SHA")
    bounds=[]
    for name in ("E","E_plus_S"):
        c=report[name]
        if c["modelled_hourly_H2_service_sha256"]!=h: raise ValueError("unequal hourly service")
        if abs(number(c["modelled_annual_hydrogen_kg"],name+" annual")-annual)>.01: raise ValueError("unequal annual service")
        primal=number(c["modelled_cost_eur_in_source_calendar_not_inflation_adjusted"],name+" primal")
        dual=number(c["solver_cost_lower_bound_eur"],name+" dual")
        gap=number(c["mip_relative_gap"],name+" gap")
        if dual>primal+.1 or not 0<=gap<=1e-6: raise ValueError("solver certificate")
        bounds.append((dual,primal))
    low,high=bounds[0][0]-bounds[1][1],bounds[0][1]-bounds[1][0]
    estimate=bounds[0][1]-bounds[1][1]
    recorded=report["solver_difference_guaranteed_lower_upper_interval_eur"]
    if len(recorded)!=2 or any(abs(number(recorded[i],"interval")-v)>.01 for i,v in enumerate((low,high))): raise ValueError("difference interval")
    if abs(number(report["cost_savings_E_minus_EplusS_source_calendar_nominal_eur"],"saving")-estimate)>.01: raise ValueError("difference arithmetic")
    if not low-.01<=estimate<=high+.01: raise ValueError("interval inclusion")
    for key in ("actual_industrial_H2_delivery_or_independent_measurements","vendor_200bar_compressor_and_storage_station_BOM_verified","native_BAFU_whole_plant_GWP_verified","installed_plant_LCOH_or_investment_DCF_certified","independent_external_scientific_peer_review_completed","v1_0_scientific_release_allowed"):
        if report.get(key) is not False: raise ValueError("unsafe release claim: "+key)
    return {"year":year,"mode":report["capacity_semantics"],"service_kg":annual,"nominal_saving_eur":estimate,"solver_lower_eur":low,"solver_upper_eur":high,"scope":"modelled wholesale-only; no industrial validation"}

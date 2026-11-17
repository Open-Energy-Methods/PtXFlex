"""F3-D source-year evidence methods and report.

Consumes the exact public Git-blob-pinned F3-D artifact, NOT private hourly
provider price/wind or E/E+S hourly dispatch. Means and year-to-year difference
are descriptive only; never treat two source years as statistical prediction.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

PUBLIC_SCHEMA="oem.ptx.f3d_2022_2024_public_source_aggregate_independent_replay.v1"
EXPECTED_GIT_BLOB="ca07f5ef1e381fa157982bc5a68e46ce3022003a"
MODES=("max_inventory","usable_service")
YEAR_HOURS={2022:8760,2024:8784}
EXPECTED_REFERENCE="9e0e95ddf9c70547ab6ce696f52a82dc312f11d7cd760de5dc779c6ac2b43c9c"

class F3DConsolidationError(ValueError):pass

def need(ok,reason):
    if not ok:raise F3DConsolidationError("F3-D scientific report: "+reason)

def number(x,name):
    need(type(x) in (float,int) and math.isfinite(x),"nonfinite "+name)
    return float(x)

def load_original(path):
    p=Path(path)
    need(p.is_file(),"original source-verified public F3-D JSON missing")
    raw=p.read_bytes().replace(b"\r\n",b"\n")
    blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
    need(blob==EXPECTED_GIT_BLOB,
         "published 2022/2024 four-case source changed; stop for independent review")
    return json.loads(raw.decode("utf-8"))

def consolidate(data):
    need(type(data) is dict and data.get("schema_version")==PUBLIC_SCHEMA and
         data.get("2023_CDS_to_ARCO_full_year_original_source_calibration_passed") is True and
         data.get("2023_CDS_to_ARCO_8760_hour_1W_source_reference_SHA256")==EXPECTED_REFERENCE,
         "original CDS 2023 full-year ERA5 ARCO source anchor absent")
    for k in ("scientific_v1_0_release_allowed",
              "installed_plant_investment_DCF_certified",
              "manufacturer_storage_incremental_CAPEX_OPEX_verified",
              "native_BAFU_2026_whole_plant_LCIA_verified",
              "independent_solver_dual_certificates_recomputed",
              "real_industrial_site_H2_validation_completed"):
        need(data.get(k) is False,"source scope flag cannot be relaxed: "+k)
    need(data.get("independent_financial_metadata_four_case_review_passed") is True and
         data.get("independent_year_mode_full_hourly_primal_E_EplusS_and_EOS_replay_passed") is True,
         "full-year independent original source physics replay absent")
    records=data.get("cases")
    need(type(records) is list and len(records)==4,"require exactly four peer-independent replay cases")
    rows=[]
    for d in records:
        year=d.get("year");mode=d.get("storage_capacity_semantics")
        need(year in YEAR_HOURS and mode in MODES and
             d.get("year_utc_hours")==YEAR_HOURS[year],
             "unknown year, storage definition or UTC hours")
        need(d.get("independent_full_hourly_E_and_EplusS_primal_replay_passed") is True and
             d.get("independent_full_hourly_type_I_20_to_200bar_EOS_replay_passed") is True and
             d.get("independent_solver_dual_certificates_recomputed") is False,
             "missing independent physical replay or unsupported dual claim")
        selector=d.get("price_neutral_E_uniform_hydrogen_service",{})
        alpha=number(selector.get("fraction_of_nominal_50_tonnes_per_day"),"H2 alpha")
        h2=number(selector.get("modelled_delivered_h2_kg_per_year"),"H2 functional unit")
        need(0<alpha<=1 and abs(h2-YEAR_HOURS[year]*50000/24*alpha)<.005,
             "price-independent uniform selected H2 product not self-consistent")
        e=d["E"];es=d["E_plus_S"]
        need(abs(number(e["modelled_h2_delivered_kg"],"E H2")-h2)<.005 and
             abs(number(es["modelled_h2_delivered_kg"],"E+S H2")-h2)<.005,
             "E and E+S must be exactly matched within source year/mode")
        for x in (e,es):
            need(0<=number(x["solver_reported_relative_mip_gap"],"cost MIP gap")<=1e-6,
                 "cost MILP not source gap certified")
            need(number(x["solver_reported_cost_dual_lower_bound_eur"],"dual cost")<=
                 number(x["modelled_nominal_eur_wholesale_cost"],"source primal cost")+.1,
                 "source solver lower bound exceeds source primal")
        saving=number(d["matched_service_annual_operational_savings_nominal_eur"],"saving")
        low=number(d["solver_reported_savings_lower_eur"],"saving low")
        high=number(d["solver_reported_savings_upper_eur"],"saving high")
        need(low-.02<=saving<=high+.02 and
             abs(saving-e["modelled_nominal_eur_wholesale_cost"]+es["modelled_nominal_eur_wholesale_cost"])<.02 and
             abs(low-e["solver_reported_cost_dual_lower_bound_eur"]+es["modelled_nominal_eur_wholesale_cost"])<.02 and
             abs(high-e["modelled_nominal_eur_wholesale_cost"]+es["solver_reported_cost_dual_lower_bound_eur"])<.02,
             "solver-reported paired electricity cost difference interval invalid")
        need(abs(saving/h2-number(d["savings_modelled_nominal_eur_per_kg_of_same_h2_service"],"saving kg"))<1e-8,
             "service-normalized benefit inconsistent with matched-service annual cost")
        rows.append({
            "year":year,"mode":mode,
            "hours":YEAR_HOURS[year],
            "H2_kg_year":h2,
            "H2_tonnes_day":alpha*50.,
            "fraction_50_t_day":alpha,
            "source_price_sha256":d["source_year_price_f64_sha256"],
            "source_wind_sha256":d["source_year_wind_f64_sha256"],
            "h2_profile_sha256":selector["hourly_target_f64_sha256"],
            "E_wholesale_eur":e["modelled_nominal_eur_wholesale_cost"],
            "E_plus_S_wholesale_eur":es["modelled_nominal_eur_wholesale_cost"],
            "saving_eur":saving,
            "saving_eur_per_kg":saving/h2,
            "saving_lower_eur":low,
            "saving_upper_eur":high,
            "bound_width_eur":high-low,
            "extra_EplusS_compression_mwh":
                es["modelled_compressor_electricity_mwh"]-e["modelled_compressor_electricity_mwh"],
            "EplusS_less_grid_import_mwh":
                e["modelled_grid_import_mwh"]-es["modelled_grid_import_mwh"],
            "EplusS_less_grid_export_mwh":
                e["modelled_grid_export_mwh"]-es["modelled_grid_export_mwh"],
            "selected_price_neutral_H2_certificate":selector["selector_certificate_method"],
        })
    need(set((r["year"],r["mode"]) for r in rows)==
         {(year,mode) for year in YEAR_HOURS for mode in MODES},
         "duplicate or missing year/mode case")
    rows.sort(key=lambda r:(r["year"],MODES.index(r["mode"])))
    for year in YEAR_HOURS:
        a,b=[r for r in rows if r["year"]==year]
        need(a["source_price_sha256"]==b["source_price_sha256"] and
             a["source_wind_sha256"]==b["source_wind_sha256"],
             "year model storage-capacity scenarios have inconsistent provider input")
    return rows

def report(rows):
    lines=[
        "# F3-D observed-year E versus E+S scientific consolidation — 2022 and 2024",
        "",
        "**Source:** Copernicus ERA5 single-point geoChunked ARCO hourly 52.5°N 3.5°E "
        "and Netherlands ENTSO-E A44 day-ahead hourly market prices. ARCO 2023 "
        "validated against original twelve CDS NetCDF months (8,760 hourly "
        "modelled-wind values match at 1 W; four component numerical checks). "
        "ARCO is NOT original monthly CDS NetCDF; offshore grid point is NOT a physical site.",
        "",
        "All four full-year service-equal E20t/E+S40t MILP primal witnesses and "
        "source-date/pressure-screen/CoolProp EOS accounting were independently "
        "replayed by PtXLens before these SAFE aggregate numbers were published.",
        "",
        "## Full source-year annual operational results",
        "",
        "| Year | Definition | Same H2 (t/day) | E nominal EUR | E+S nominal EUR | "
        "E−E+S nominal EUR | EUR/kg H2 | Reported solver-bound interval EUR |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['year']} | {r['mode']} | {r['H2_tonnes_day']:.3f} | "
            f"{r['E_wholesale_eur']:,.2f} | {r['E_plus_S_wholesale_eur']:,.2f} | "
            f"{r['saving_eur']:,.2f} | {r['saving_eur_per_kg']:.4f} | "
            f"[{r['saving_lower_eur']:,.2f}, {r['saving_upper_eur']:,.2f}] |"
        )
    lines += [
        "",
        "## Electrical and compression accounting",
        "",
        "| Source year | Capacity semantics | Extra E+S compression MWh | "
        "Less E+S grid import MWh | Less E+S grid export MWh |",
        "|---|---|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['year']} | {r['mode']} | "
            f"{r['extra_EplusS_compression_mwh']:,.2f} | "
            f"{r['EplusS_less_grid_import_mwh']:,.2f} | "
            f"{r['EplusS_less_grid_export_mwh']:,.2f} |"
        )
    lines += [
        "",
        "The modelled increase in compression electricity accompanies an economic "
        "benefit from differing hourly dispatch under the observed prices. "
        "Exports are credited through signed source wholesale grid settlement. "
        "A negative E+S annual net grid cost in 2024 is not an independently "
        "verified electricity-sales business or net project profit.",
        "",
        "## Numerical validation versus environmental/market uncertainty",
        "",
        "The displayed economic bound is formed from HiGHS-reported cost objective "
        "lower bounds and independently recomputed primal E and E+S net "
        "electricity settlement. Their cost MILP gaps are ≤1e-6 and "
        "price-blind annual selected service was solver certified. "
        "PtXLens independently recomputed full-hourly primal conservation, "
        "physical pressure EOS and cost arithmetic, **not independent "
        "optimization dual certificates**. These narrow solver bounds are "
        "**not uncertainty intervals** for future prices, wind, H2 demand, "
        "equipment reliability, manufacturing or installation costs.",
        "",
        "This retrospective two-year source comparison is not a forecast of future "
        "prices, offshore wind generation, H2 service or investment returns. "
        "Only two separate years (2022 and 2024) are represented. They cannot "
        "support a calibrated probability distribution, statistically robust "
        "future market interval, climate uncertainty band or a causal "
        "attribution of savings changes to wind versus price. A matched "
        "price-swap/wind-swap full annual MILP is needed to estimate that "
        "mechanism; original hourly arrays stay private. Existing 2023 "
        "F3-D controlled perturbations are a **different, individually "
        "feasible hourly service definition**; do not merge them into "
        "the four observed-year envelopes.",
        "",
        "## Functional unit and original industrial shortfall",
        "",
        "The same precise hourly H2 target is enforced for E and E+S WITHIN "
        "each year+capacity interpretation. Service differs ACROSS years "
        "and between gross and usable capacity interpretations. The "
        "source-model attainable uniform product is about 30–31 t/day, "
        "not the nominal 50 t/day contract. Therefore the operating "
        "EUR/year figures are not full contracted H2 delivery, and "
        "their cross-scenario differences must be normalized to EUR/kg "
        "with retained source-year labels.",
        "",
        "## Capital, environmental and site boundaries",
        "",
        "The annual E−E+S net wholesale settlement benefit excludes vendor "
        "storage vessel/bank CAPEX, compressor/motor/cooler and safety BoP, "
        "actual incremental OPEX, replacements, tax, finance and whole-project "
        "cashflows. L3-A/L3-D DCF is **only** a hypothetical break-even "
        "CAPEX sensitivity. Native BAFU:2026 v1.1 compatible Type I "
        "stationary storage process inventories, steel material inputs, "
        "real installation location, matched-hour electricity background "
        "and full LCIA GWP remain unverified. The literature vessel empty "
        "equipment mass is NOT the upstream forged/rolled virgin steel input.",
        "",
        "**Release status:** numerical four-case original-year primal/financial "
        "replay PASS; independent dual/reoptimization, primary site "
        "measurement, manufacturer turnkey economics, BAFU native "
        "matched-service LCA and scientific v1.0 NOT PASSED.",
        "",
        "## Reproducibility",
        "",
        "Run the deterministic original-source-bound aggregate analysis: "
        "python -m ptxflex.f3d_historical_source_report "
        "--source research/F3D_ARCO_2022_2024_PUBLIC_VERIFIED_AGGREGATES_v1.json "
        "--output docs/F3_D_2022_2024_SOURCE_YEAR_CONSOLIDATED_GENERATED_v1.md",
        "",
    ]
    return "\n".join(lines)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(argv)
    rows=consolidate(load_original(a.source))
    text=report(rows)
    need(a.output.parent.is_dir(),"destination parent directory does not exist")
    need(not a.output.exists() or a.output.read_text(encoding="utf-8")==text,
         "cannot overwrite different source-verified report")
    if not a.output.exists():
        with a.output.open("x",encoding="utf-8",newline="\n") as f:f.write(text)
    print("F3D_HISTORICAL_2022_2024_4_SOURCE_YEAR_REPORT_READY; "
          "no native BAFU or industry CAPEX v1.0 claims")
if __name__=="__main__":
    main()

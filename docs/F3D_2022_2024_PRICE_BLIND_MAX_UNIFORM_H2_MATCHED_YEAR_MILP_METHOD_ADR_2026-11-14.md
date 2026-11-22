# F3-D external 2022/2024 matched-service optimization — preregistered procedure

**Version:** F3-D YearMatched-0.1, 2026-11-14. **Gate:** pre-v1.0; source-year original ERA5 retrieval remains outstanding as this procedure is authored. Research model is a **source-historical scenario**, not measured site operation.

## Source and unchanged plant model

- PyNEXUS original E and E+S artifacts are byte-frozen at E SHA-256 `069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051` and E+S SHA-256 `cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9`.
- Independent inspection of the 2023 original `E/stage_b.csv` confirms that **all 8,760 original source `h2_demand_kg_h` values are identically 2083.3333333333335 kg/h**, exactly 50,000 kg/day and 18,250,000 kg/year.
- Original E 20,000 kg / E+S 40,000 kg, initial/terminal 10,000 kg each; charging/discharging up to 2,200 kg/h; loss 1e-4 per h; 125 MW PEM at 10–100% load and 50 MW/h ramp; 50 MW signed grid interconnect; linearized source H2 yield 21.086108610861086 kg/MWh; 20 bar(abs) pipeline minimum and 30 bar(abs) PEM source. These source parameters are archived at `research/F3_D_ORIGINAL_PYNEXUS_2023_E_ES_FROZEN_PLANT_PARAMETERS_FOR_2022_2024_v1.json` with pinned source ZIP SHA. No new-year measured plant tuning or fitted coefficient is claimed.
- New year sources: NL ENTSO-E A44 original XML, including A03 source-defined constant blocks, plus ERA5 reanalysis original 10/100m u/v monthly files at the original (52.5° N, 3.5° E) offshore point. The price 2023 SHA and wind 2023 SHA must both reproduce the original PyNEXUS frozen vectors before an alternative calendar can be admitted. 2022 is exactly 8,760 UTC hours; 2024 is exactly 8,784 UTC hours including Feb 29. All raw documents and normalized hourly arrays remain private.
- **Location caveat:** 52.5°N, 3.5°E is a North Sea weather grid cell; it is **not** evidence of an actual 50-tonne/day industrial H2 customer, onshore wind generation or Dutch grid commercial contract.

## Why a price-blind E service-selector must precede the storage comparison

Using the 2023 original E-delivered trajectory as if physically feasible under 2022/2024 weather would conflate source years. Selecting service independently for E and E+S would compare **different products**. Selecting an H2 target after optimizing two cases could bias the savings in favour of the larger bank.

The preregistered reference **within each year × physical inventory interpretation** is one uniform hourly delivered-H2 schedule, at a constant fraction `alpha` of the original 50,000 kg/day: `H2_delivered(t) = alpha * 50000 / 24` for every actual UTC hour, `0 < alpha <= 1`.

**Step A (non-market selection, E only).** Maximize `alpha` over exactly the E(20t) physics- and compressor-screened annual MILP, not using price vectors or any E+S dispatch. Min/maximum PEM unit commitment, linearized yield, 50 MW grid, turbine hourly available energy, curtailment, ramp, pressure-screen bank bounds, equal original initial and final mass, loss, charging/discharging exclusivity, and compressor power are mandatory. A certified integer optimal solution and credible upper bound for `alpha` with relative MIP gap <=1e-6 is required. Independently recompute all physical equations and hourly inventory. **If E cannot establish a certified nonzero feasible `alpha`, stop:** no saving preference is reported. A source-year maximum uniform feasible fraction is a modelled service **shortfall**, not full original customer demand or reliability proof.

**Step B (E and E+S operating cost).** Using the **exact byte-identical** target produced in Step A, solve both full-year mixed-integer cost minimizations at identical hourly market and wind histories, unchanged source PEM and grid constraints. Include a 313 K fixed upper pressure 20→200bar **Type I screen**, original PEM-to-bank charging compressor electricity (RVO/LBST 80% isentropic, 90% motor), real-gas EOS bank limits, standing loss and matched initial/final model state; disclose excluded cooler power, real vendor compressor maps and equipment certification. Original installed 20t/40t reference banks are two *alternative* interpretations, `max_inventory` versus `usable_service`, and are NEVER conflated across cases.

**Step C (independent certification).** Retain full interval-by-interval H2 and mass/energy pressure feasibility checks; independently calculate `objective = sum_t grid_exchange_MW(t) * NL_price_EUR_per_MWh(t)` from the signed hourly grid exchange (import positive, export negative, retains negative spot prices). Require both MILPs to finish with solver MIP gap <=1e-6 and valid finite lower bounds; report only aggregated modelled wholesale cost. For savings `E - E+S`:
- point estimate `U_E - U_ES`, using *audited feasible* costs;
- rigorous lower `L_E - U_ES`;
- rigorous upper `U_E - L_ES`, where `L` is each problem's HiGHS lower bound.
- No point estimate or economic preference when either problem lacks an accepted fully audited *integer* optimum. Feasible LP relaxation does **not** establish feasibility of binary-constrained systems.

**Step D (cross-year interpretation).** Historical calendar-year electricity wholesale amounts are nominal 2022 or 2024 EUR. No pooled investment NPV, inflation-adjusted combined savings, real electricity supply contract, site grid tariff, projected ROI, vendor installation CAPEX, operating costs or whole-plant BAFU GWP is asserted. Compare each year **within itself**, and report E vs E+S quantity/economic differences under both separately named capacity interpretations. If `alpha` or annual service differs across modes/years, do not compare unadjusted annual absolute savings as if the services were identical; report both `alpha` and service quantity and note the limitation. An optional per-kg-H2 normalization can be calculated **only** with explicit model-scope/disclosed denominator and no cross-year monetary normalization claim.

## Reproducibility and execution

- Strict 2023/2022/2024 provider calibration and source pair: `src/ptxflex/f3d_live_provider_pair_gate.py`.
- Source-year H2-selection MILP, independent mass/electric/pressure audit and E/E+S cost certification: `src/ptxflex/f3d_year_matched_service.py`.
- Mathematical checks and negative controls: `tests/test_f3d_year_matched_service.py`.
- Private original source artifact-fed 4-case workflow: `.github/workflows/f3d-matched-year-service-from-private-source.yml`, **manually dispatched only after all 2022/2023/2024 ENTSO-E and ERA5 sources (six jobs) and the private source pair gate have succeeded**. The workflow requires the successful source provider `upstream_run_id` (currently `43617006319`) and produces four aggregated, source-hash-linked JSON reports; raw source ZIP/CSV/NetCDF and hourly dispatch states must NOT be committed.
- PtXLens independent audit: `src/ptxlens/f3d_external_year_independent_review.py`. It checks the aggregate report SHA-parity, 2024 leap calendar, hourly flat target digest, price-neutral service arithmetic, cost primal/dual bounds and unsupported claims. **A metadata review without independently re-solving against the private source arrays is not full physical peer review.**

### Release verdict

Source methodological pipeline implemented and regression-tested; actual 2022/2024 MILP result generation **NOT DONE** until original ERA5 source-year pairs and 2023 wind calibration are complete. 2023 and external years are not equal measured H2 service, geographic operating site, installed pressure equipment, vendor LCA or investment forecasts. P0 two-independent-media private original source backups, permission checks, real site physical validation, full manufacturer BOM and native BAFU remain blockers for scientific v1.0.

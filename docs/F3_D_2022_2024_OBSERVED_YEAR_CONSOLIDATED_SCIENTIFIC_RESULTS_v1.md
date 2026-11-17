# F3-D — independent original-provider-year hydrogen storage economics: 2022 and 2024

**Program:** OEM-PTX-2026-01 · **Date:** 15 November 2026 · **Model scope:** source-registered 2023 PyNEXUS hydrogen E (20t nominal inventory) and E+S (40t nominal inventory), 30-bar PEM boundary, physically screened 200-bar(a) Type I storage at 313 K with 20-bar(a) delivery reserve. **Data scope:** actual 2022 and 2024 Netherlands ENTSO-E NL A44 market prices and Copernicus ERA5 ARCO single-point offshore wind, with 2023 original PyNEXUS CDS reference-year exact 8,760-hour wind-power equivalence.

**Source primary evidence:** [four-case public Git-blob-pinned JSON](../research/F3D_ARCO_2022_2024_PUBLIC_VERIFIED_AGGREGATES_v1.json), commit bdf82be; [source-checked primary results and limitations](../research/F3D_ARCO_2022_2024_PUBLIC_VERIFIED_RESULTS_v1.md). The published JSON was generated locally only after the full 2022/2024 source-pair original calendar/source hash checks and four independent PtXLens original hourly primal E/E+S, source-cost and CoolProp pressure/EOS replays. The original private provider raw arrays and 8,760/8,784-hour hourly primal witnesses are deliberately NOT redistributed.

## 1. Aim and scientific inference boundary

For each year y and physical-capacity interpretation m, first select the **highest constant hourly hydrogen service** that the E-only source model can supply without optimization against price; then independently minimize E and E+S signed annual electricity settlement under the **same precise hourly selected H2 service**. This establishes an observed-input, internally matched-service numerical economics comparison, **not** a real industrial plant comparison, forecast, probabilistic LCOH, new methanol process model or installed storage investment study.

The original nominal H2 customer service is **50,000 kg/day**. Every source-year selected service is only approximately 30–31 tonnes/day; shortfall is not silently declared a valid industrial contract. Between years or gross/usable storage interpretations the modelled functional unit is DIFFERENT; differences cannot simply be attributed to electricity prices or storage hardware.

## 2. Sources, chronology and source-model invariants

- 2022: **8,760 consecutive UTC hours**. 2024: **8,784 UTC hours including 29 February**, without interpolation, shifting hourly market chronology or treating the leap year as 8,760 hours. For a given year, E and E+S use identical source weather and electricity price vectors.
- Wind is derived from ERA5 u10/v10/u100/v100 at **52.5°N, 3.5°E**, through the source PyNEXUS 120-m hub wind/turbine conversion. ARCO is an officially delivered *repackaged* geo-chunked product; the 2022 and 2024 snapshots are **not** the original 12 monthly CDS NetCDF files. Every 2023 hourly modelled wind value matched the original CDS-based wind to **1 W**, and the four wind components passed the recorded 1e-5 m/s numerical tolerance.
- Net electricity settlement is **signed NL A44 hourly price times modelled signed grid exchange**, including modeled export credits and negative prices. No retail tariff, demand charge, network connection fee or market settlement contract was independently verified.
- Fixed model constraints include PEM rated/minimum load and ramps, grid-power limits, charge/discharge exclusivity, hydrogen storage inventory and loss, compression electricity and source 20–200-bar pressure/EOS screen. Storage bank capacity semantics are **separate counterfactual engineering conventions**, not manufacturer-certified physical designs.

## 3. Optimization formulation and acceptance

For year y, hourly index t and capacity semantics m, the **price-independent reference selection** solves:

    maximize alpha in [0,1] for E, subject to delivered_H2[t] = alpha * (50,000/24) kg/h for every t.

For that SAME alpha target, calculate separately:

    C_E   = min sum_t price[y,t] * signed_grid_E[y,m,t]
    C_ES  = min sum_t price[y,t] * signed_grid_ES[y,m,t]
    S_y,m = C_E - C_ES
    S_y,m_perkg = S_y,m / (H2_selected_kg_year).

The original cost optimizer requires relative HiGHS integer MIP gap <= 1e-6. For modelled savings, the **solver-reported economic lower/upper intervals** are:

    lower = reported dual cost lower bound(E) - feasible primal cost(E+S)
    upper = feasible primal cost(E) - reported dual cost lower bound(E+S).

These are **optimization proof bounds conditional on the exact model**, not 95% uncertainty bands. A separate PtXLens reviewer independently replayed each private full-hourly solution's primal H2, power, compressor electricity, pressure/EOS and financial calculations. That reviewer **did not independently reoptimize or reconstruct the HiGHS cost dual certificates**. For 2022 max_inventory the original selector was completed under the pre-certificate solver revision and its method is marked legacy; later three selectors used root-LP global upper bound plus integral fixed-commitment feasible witness with source-reported relative gap about 1.6e-8.

## 4. Independent source-year case results

**Currency warning:** original calendar nominal **2022 EUR** and **2024 EUR** are not inflation adjusted or directly poolable.

| Year | Capacity semantics | Modelled common H2 t/day | E net grid cost EUR | E+S net grid cost EUR | E−E+S savings EUR/year | Savings EUR/kg H2 | Solver-reported savings interval EUR |
|---|---|---:|---:|---:|---:|---:|---:|
| 2022 | max_inventory | 30.481 | 26,670,018.62 | 22,764,385.69 | 3,905,632.94 | 0.3511 | [3,905,623.51, 3,905,639.71] |
| 2022 | usable_service | 30.884 | 27,842,116.44 | 23,938,309.19 | 3,903,807.25 | 0.3463 | [3,903,781.50, 3,903,830.73] |
| 2024 | max_inventory | 30.748 | 1,023,571.70 | -1,223,554.48 | 2,247,126.18 | 0.1997 | [2,247,125.42, 2,247,127.03] |
| 2024 | usable_service | 31.006 | 1,015,598.76 | -1,190,634.76 | 2,206,233.52 | 0.1944 | [2,206,232.54, 2,206,234.02] |

The two E+S 2024 net grid cost figures are negative: this model computes net annual **wholesale electricity credits**, not guaranteed physical revenue from a real contracted buyer, a negative hydrogen manufacturing cost, or plant profitability. This sign is an important reason not to use the source electricity-cost advantage as an installed-project margin.

### 4.1 Electricity and compression balance

| Year | Capacity semantics | Extra E+S modeled compression electricity MWh | Less E+S modeled gross grid import MWh | Less E+S modeled gross grid export MWh |
|---|---|---:|---:|---:|
| 2022 | max_inventory | 454.05 | 11735.59 | 9224.00 |
| 2022 | usable_service | 455.00 | 12134.33 | 10425.51 |
| 2024 | max_inventory | 618.90 | 15461.54 | 10444.10 |
| 2024 | usable_service | 593.02 | 14845.65 | 10845.63 |

Additional storage changes the optimized hourly import/export distribution and increases modeled compressor energy. A lower annual imported volume by itself is not equal to wholesale net settlement saving: hourly electricity price and export credits matter.

## 5. Interpretation, methodological uncertainty and limits

**Directly supported:** all four year/mode E+S cases reduce *modelled wholesale net-grid electricity cost* compared with E under their own identical H2 target, with original-provider source pairing and independent physical primal replay. The min and max modelled annual advantage across four cases are **€2,206,234 (2024 usable_service)** and **€3,905,633 (2022 max_inventory)** in **different nominal price-year euro units**. Their numeric span is **not** a confidence interval or an annual future income distribution.

**Unresolved or not inferred:**

1. **Causality** — with two historical years and changing wind, market and H2 targets, price-only or wind-only contributions to cross-year differences are not identified. A controlled 2022/2024 source-year factor study, holding product target and physical assumptions constant, is still required; re-solving the full MILPs with each counterfactual and an explicit infeasibility/no-savings policy is necessary.
2. **Numerical proof** — accepted solver MIP gaps and small primal residuals do not replace a reviewer who independently reconstructs the original HiGHS dual or re-solves a reference optimization. The source's solver interval is mathematical conditional-model uncertainty, not weather or cost uncertainty.
3. **Weather/site** — single-point offshore ERA5 and cubic PyNEXUS farm reconstruction are not metered power production, real future capacity factor, wind curtailment contracts or physical project location.
4. **Hydrogen hardware** — pressure screen assumes isothermal real gas at 313 K, not vessel manufacturer strength/fatigue, compressor-map, thermohydraulic, cooling-water or PESO/PED site approval. The 20t-to-40t reference hardware is not a verified installed BOM.
5. **Economics** — missing all-in incremental CAPEX, actual extra station OPEX, replacement, safety, insurance, land, construction and taxes. The peer-reviewed bare-vessel reference is NOT an OEM installation quote. Investment NPV/LCOH must not be advertised.
6. **LCA** — native BAFU:2026 v1.1 2023 source reference foreground examples do not provide complete 2022/2024 matched-service emissions or a stationary Type I pressure-vessel manufacturing inventory. Equipment **empty shell mass != virgin steel input**; 18 nonvessel categories remain unquantified and cannot be treated as zero.

## 6. Prespecified next science experiments

**Factor isolation with original sources remaining private:** for each independently source-verified year and capacity semantics, freeze one source-year price-neutral selected hourly H2 target, perform an original baseline E/E+S solve; construct within-year chronological circular-shift and centered price dispersion counterfactuals at fixed observed weather; separately construct capped source wind-availability perturbations at fixed observed prices. Re-optimize both models with the same H2 service on each input. Any missing feasible primal, unverified optimality or fixed H2 incompatibility must be recorded as **NULL/no comparable saving**, not zero or an assumed economic failure. Do NOT blindly swap the 8,760h 2022 and 8,784h 2024 time series or delete 29 February without declaring derived time remapping and a new functional unit.

**L3-D economic response:** feed each of the four independently reviewed operating savings **separately** into the source-year conditional storage investment DCF to obtain properly labeled maximum initial installed CAPEX tolerances, incremental OPEX bounds, discounted cashflow and sensitivity to benefit persistence. These are thresholds under assumptions, **never** a forecast or an actual supplier price.

**Native BAFU:** source-hash-lock the 19-category F2 manufactured hardware ledger per semantics; identify validated material streams, manufacturing yields, real BAFU:2026 v1.1 process/provider/reference flows and actual region, electricity mix, maintenance, replacements and EOL. Perform native openLCA results only after every mapping has independent evidence; publish provider identifiers and source-register metadata if licensing permits, not licensed original database bytes.

## 7. Source code and exact release state

- Source: Open-Energy-Methods/PtXFlex, feature branch feat/milp-methanol-baseline, public evidence commit bdf82be, JSON original Git blob ca07f5ef1e381fa157982bc5a68e46ce3022003a.
- Generator: src/ptxflex/f3d_historical_source_report.py (exact Git blob check, primal/cost/source-year arithmetic and fail-closed report generation).
- Independent reviewer: Open-Energy-Methods/PtXLens original f3d_external_year_private_witness_replay and f3d_external_year_independent_review.
- Future DCF: PtXLens src/ptxlens/l3d_historical_source_dcf.py; all four source-year values remain separate.
- This report **does not raise F3/F2/L1/L2/L3 or programme v1.0 release gates**; all full project claims remain NOT VERIFIED.

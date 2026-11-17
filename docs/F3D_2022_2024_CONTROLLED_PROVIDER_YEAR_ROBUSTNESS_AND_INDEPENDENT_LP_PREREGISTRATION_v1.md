# F3-D next-stage preregistration — source-year observed-input price/wind interventions and independent optimizer evidence

**Project:** Open-Energy-Methods PtXFlex + PtXLens · **Date:** 2026-11-15 · **Stage:** implemented original-provider year model and independent numerical reviewer modules; **source-year perturbation MILPs and independent 2022/2024 cost LPs are NOT YET RUN**. The original four historical source cases have already passed independent hourly primal/pressure/financial replay; the following are *additional experiments*, not retroactive claims.

## Hypotheses and comparators

The E (20,000kg nominal H₂ inventory) and E+S (40,000kg) original source models share identical physically defined annual H₂ product WITHIN each one of the observed source-year (2022 or 2024) × bank-capacity-semantics (`max_inventory` or `usable_service`) references. Their price-blind maximal feasible *constant hourly* H₂ targets are already certified and archived with the exact source-hourly SHA256. **Do not run the maximum-service selector again** for a counterfactual: any adjusted wind that can no longer serve this SAME target must be reported infeasible/uncertified with NULL economic differences, not a different target and favorable €/kg.

Each experiment preserves one of the four original E-vs-E+S hourly H₂ functional units, using the original source-verified ENTSO-E A44 Dutch prices and original Copernicus ERA5 ARCO observed wind-power output, privately held. Conditions:

| Intervention | Change | Held exactly unchanged | What may be concluded if optimized |
|---|---|---|---|
| `price_roll_168h` | Circular right-shift year-specific observed price chronology by 168h | Original hourly wind-power availability, H₂ target, frozen hardware/equipment | Chronology sensitivity under preserved price distribution, NOT an actual observed shifted year |
| `price_spread_150pct` | Price = median(price) + 1.5×(price−median) | Original hourly wind/H₂/plant parameters | Controlled dispersion sensitivity, NOT an empirical forward-price volatility model |
| `wind_power_090` | Wind available electrical POWER = 0.90× original hourly source POWER | Original hourly A44 price and **exact original** delivered H₂ | Robustness/infeasibility for specified **power reduction**, NOT 10% lower meteorological wind speed |
| `wind_power_110_capped` | Wind available electrical POWER = min(1.10× original source POWER, **125.685MW** original registered farm output model limit) | Original hourly A44 price and H₂ target | Controlled source electric availability gain, NOT actual ERA5 new-wind-year or installed turbine redesign |

The 125.685MW cap comes directly from `src/ptxflex/f3d_live_era5.py` `FARM_LIMIT_MW` and the original PyNEXUS wind-resource conversion used for the 2023 source-CDS check. Even with that cap, scaling electrical POWER is **not** a physically observed/certified new 100m/120m wind speed or farm capacity factor.

Within a price intervention, the original wind and H₂ target remain fixed and the solver solves a new annual E and E+S integer dispatch; the original 2022/2024 baseline cost must not simply be repriced using the unchanged incumbent without reoptimization. Within a wind intervention, original market price and H₂ are fixed; both cases first undergo LP-relaxed zero-cost model feasibility screening. If the LP is mathematically infeasible (HiGHS status 2), the integer model cannot satisfy this original H₂ target under the relaxed-model necessary-condition analysis, but it does **not** demonstrate actual hardware or site infeasibility. If the LP is feasible, the ORIGINAL integer dispatch MILP is still required. A solver timeout, RAM error, missing incumbent, inconsistent source hash, or nonpassing 1×10⁻⁶ original MIP gap is **INCONCLUSIVE**, not zero-cost saving and not a proof of model infeasibility.

## Model, source and reproducibility gates

1. Original baseline public aggregate is byte-pinned to Git blob `ca07f5ef1e381fa157982bc5a68e46ce3022003a` from PtXFlex source commit `bdf82be`.
2. The original `C:\Users\prasa\PtX_PRIVATE_RESEARCH` source provider CSVs are checked against independent original-year source pair SHA, UTC 8760/8784 completeness and original CDS/ARCO 2023 calibration. The original registered E/E+S pressure/PEM hardware and hour-by-hour H₂ target are checked against the independently reviewed private annual witness and exact SHA.
3. The new source cost MILP is `solve_ideal_storage` with original 2022/2024 source constraints and `mip_rel_gap <= 1e-6`. Each E and E+S output is written to an individual **PRIVATE** immutable file; a rerun that finds an already source-matched result skips it instead of changing data.
4. The new `PtXLens` reviewer reconstructs altered hourly source arrays separately from the original observed private year CSVs; independently replays EACH new E and E+S signed market settlement, original full hourly H₂ balance, power/PEM minload/ramp, bank pressure inventory and CoolProp 20–200bar EOS. Only a *successful pair* obtains an annual modeled E-minus-E+S electricity-cost difference, a solver-reported bound interval and normalized €/kg. PRIVATE 8-field state vectors and provider arrays are NOT copied to the public output.
5. A mathematically separate `PtXLens` independent LP dual checker builds the original E and E+S annual cost LP relaxation from independently written equations, verifies primal residuals, dual sign, stationarity, complementary slackness and primal–dual objective. If (and **only if**) the independently computed LP global LOWER bound closes original integer primal to the accepted 1×10⁻⁶ gap, this provides an *additional conditional original-MILP global-optimality certificate*. It does **not** reconstruct the original HiGHS integer branch tree. If the bound remains loose, report only a valid LP lower bound, NOT `fully_dual_certified`.

Scientific output cases must be indexed by (year, mode, variant); **never pool** the 2022 and 2024 nominal euro years, or different gross/usable H₂ service targets, or treat 2023 PyNEXUS F3-C source target as identical to 2022/2024.

## Windows PowerShell execution (each original MILP may be computationally expensive)

Update both sibling feature branches, then run *only* hermetic tests first:

    cd C:\Users\prasa\OEM_Research\PtXFlex
    git pull --ff-only
    cd ..\PtXLens
    git pull --ff-only
    .\scripts\F3D_Robustness_Local.ps1 -Phase Test

After tests pass, the most economical first independent cost LP is one source case/mode. It does **not** rerun any original integer dispatch:

    .\scripts\F3D_Robustness_Local.ps1 -Phase IndependentLP -Year 2022 -Mode max_inventory

Inspect the reported KKT metrics and whether its LP lower bound actually closes source HiGHS integer cost optimality at 1×10⁻⁶. A false or missing certificate is not a failure of the original incumbent.

Then choose ONE preregistered source-year experiment, not all 32 expensive year/mode/variant/member combinations:

    .\scripts\F3D_Robustness_Local.ps1 -Phase SolvePair -Year 2022 -Mode max_inventory -Variant price_roll_168h
    .\scripts\F3D_Robustness_Local.ps1 -Phase ReviewPair -Year 2022 -Mode max_inventory -Variant price_roll_168h

For the fixed original H₂ target under weaker wind:

    .\scripts\F3D_Robustness_Local.ps1 -Phase SolvePair -Year 2022 -Mode max_inventory -Variant wind_power_090
    .\scripts\F3D_Robustness_Local.ps1 -Phase ReviewPair -Year 2022 -Mode max_inventory -Variant wind_power_090

Choose `-Phase Status` to see file existence only, not scientific acceptance. No private array may be pushed to GitHub. Only inspect and explicitly stage the new PtXLens sanitized aggregate output(s). If `price_roll_168h` or other source-year full MILP cannot meet strict MIP optimality within computational resources, preserve private artifacts and disclose `INCONCLUSIVE`; do not loosen the scientific gap to obtain prettier figures.

## Decision rules and eventual F3-D scientific interpretation

- Paired annual operating saving (S=C_E-C_{E+S}), *only* for a fully verified paired case; produce solver-report lower and upper cost difference bounds.
- Service-normalized saving (S/sum_t h_t) in source-calendar EUR/kg delivered H₂. Use same private immutable target SHA within year/mode.
- Contrast each intervention's `S` against the **same year/mode original provider** baseline; do not simply compare to another year, and do not interpret a single 168h circular shift as a confidence distribution.
- Independently revalidated LP bound can strengthen optimizer evidence; an LP gap wider than 10⁻⁶ means exact original integer dual remains **NOT independently certified**.
- There are NO vendor installed CAPEX/OPEX quotes, real industrial H₂ service contract, site-specific measured wind/H₂, full native BAFU manufactured equipment inventory, complete LCIA GWP, prospective price forecast or v1.0 scientific release. L3-D 324 DCF cells remain analyst-only *conditional* financial sensitivities.

**Current status:** Experiment methods, original-year provenance/immutability gates, private dispatcher, independent PtXLens physical replay, and an independent LP-dual-checking algorithm are committed. This document is a **preregistration**. No new 2022/2024 counterfactual numerical savings or independent original-year LP KKT result has yet been produced or independently reviewed.

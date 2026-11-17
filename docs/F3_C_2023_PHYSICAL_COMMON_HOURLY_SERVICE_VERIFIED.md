# F3-C — Original 2023 physically screened matched-hourly hydrogen service: equal-duty E and E+S
**OEM-PtXFlex / PtXLens research note · 14 November 2026 · Source-reconstructed full-year numerical benchmark**

**Scientific evidence class:** original 2023 modelled hourly hydrogen delivery; byte-locked original wind/A44 market data; 200 bar(a) Type I real-gas pressure screen; RVO/LBST reference compressor electricity; independently audited 8,760h MILP optimizations and MIP objective bounds.

**Scientific stop:** *not* a measured commercial hydrogen plant, a complete H₂ contract fulfilment, installed storage fabrication design, full BAFU native lifecycle GWP, complete discounted hydrogen production cost or demonstrated net economic benefit from purchasing a second bank. Release gates F3/L1/L2/L3/P0 and coordinated v1.0 remain **NOT PASSED**.

## 1. Question, evidence and falsifiable hypotheses

**Problem:** the original source 2023 E 20t hydrogen-storage dispatch **cannot** reproduce the original modelled E-delivered 8,760h H₂ profile when the storage is subjected to a Type I 200 bar(a) screened finite usable inventory and a compressor electricity penalty. The larger E+S 40t bank has already shown zero additional shortfall for the original-E reference target. Directly comparing 2023 whole-year E/E+S wholesale cost *at the original E target* is scientifically invalid because the E model is physically screened **infeasible** for that specific service.

**F3-C intervention:** identify a **constructively attainable reduced 8,760h hydrogen service** from the authentic original 2023 source-reconstructed **E Stage A feasible incumbent**. Freeze the resulting exact hourly load SHA, then independently re-optimize **both** physical E(20t) and E+S(40t) against that **identical** load, original wind and observed NL A44 day-ahead prices under two *separately treated* source capacity interpretations.

**Pre-registered empirical/model falsification controls:** each 8,760h target must be identical byte-for-byte between E and E+S within an interpretation; no source archive or Stage A shortage trace may deviate from a registered SHA; every hour must independently close electrolysis, electricity, storage, cost, pressure and terminal inventory equations; a feasible MILP incumbent alone is not a proof of cost optimum; no physical claims follow from the 2026 prospective supplier idea. Unmet original industrial H₂ demand is explicitly retained.

Original model source: [PyNEXUS original 2023 archival work](https://github.com/abhijith-sivaprasadan/PyNEXUS); [PtXFlex matched-source MILP](../src/ptxflex/f3_matched_ideal_benchmark.py), [pressure/real-gas source duty](../src/ptxflex/pressure_storage_duty.py), [source-pinned Stage A](../src/ptxflex/f3_pressure_adequacy.py), [this F3-C physically constrained benchmark code](../src/ptxflex/f3_pressure_matched_service.py).

## 2. Physically achievable common H₂ service: exact hourly specification

Let `d_t^E,original` be the **original frozen 2023 PyNEXUS E Stage B modelled hydrogen DELIVERED** to its pipeline/demand node for hour `t = 0…8759` (not full industrial demand). Let `s_t^{E,StageA,feasible,mode}` be the **actual archived Stage A modelled additional E H₂ shortage for one pressure-screened feasible integer dispatch**, from the registered 2023 derivative ZIP for the relevant bank interpretation. Then:

```text
d_common[mode,t] = d_E_original_delivered[t] - source_E_StageA_feasible_shortfall[mode,t]
constraints:   0 <= d_common[mode,t] <= d_E_original_delivered[t]
both cases:    H2_delivered_E[mode,t] = H2_delivered_ES[mode,t] = d_common[mode,t]
annual:        sum(d_common) + sum(source_StageA_E_extra_shortfall)
             = original source E delivered modelled annual hydrogen
             = 16,335,279.317376737 kg/year
full contract: original 50,000 kg/day x 365 = 18,250,000 kg/year
unserved:      18,250,000 - sum(d_common)
```

**This profile is *feasible*, not proven to maximize common deliverable H₂.** The source Stage A E shortfall has verified MILP bounds but the chosen incumbent (66,524.317kg gross / 3,720.371kg usable) is *not globally minimum*. A stronger claim about globally optimal service maximization requires a fully proven original Stage A minimum with a frozen tie-breaking rule for its hourly profile; the initial stage objective `min annual shortage` also need not select a unique hourly service trace. Both source problem variants remain **different sensitivity experiments**, never one mixed E vs E+S denominator.

The full 8,760h original E and E+S source archives have SHA-256:
- **E:** `069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051`
- **E+S:** `cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9`
- **Gross source Stage A ZIP:** `6731bdaeeaa01a531f577150815dcf6638c15d21bc0ccee5e9ac0fa748ffe3c8` (artifact 14084348674)
- **Usable source Stage A ZIP:** `18dec140df7cab63dd9cae8836e3f23fd2dcfb0370acd48db0e36e6af81813cd` (artifact 14084937031)

The derived original 2023 sparse H₂ shortage traces also have separate frozen [gross](../data/results/F3_2023_original_E_sparse_H2_backup_need_max_inventory.json) and [usable](../data/results/F3_2023_original_E_sparse_H2_backup_need_usable_service.json) SHA-256. Every original Stage A full-hourly source value must match the sparse derivative within the explicitly published 1e-5 kg numerical-zero convention; no climate/market hourly input is invented.

Common hourly service `float64` SHA-256:
- **Gross mode** `8e0d55994c7fe5f1abd952771a1b169336893d12698147fb3a93cb61a4ee7a16`.
- **Usable mode** `6a30baf00ddb065cd906dedd711db7cbf67504c50b4fda5809c5dfd29b23fa87`.

Those byte hashes are *identical* between E and E+S **within mode**; do not compare costs across the two different service modes or redefine the service after reading cost outcomes.

## 3. Optimization and independent verification

For both source cases within each mode, the fixed-hourly service constrained SciPy/HiGHS MILP minimizes:

```text
C_grid_wholesale [2023 EUR] = sum_(t=0…8759) price_NL_A44[t] * G_signed_grid_import[t]
G > 0: import; G < 0: export; no simultaneous import/export in signed interface.
```

All source-electrolyser conditions, minimum/maximum on/off, ramp bounds, original grid interconnection capacity, wind availability/curtailment, storage charge and discharge **exclusivity**, source storage standing loss and **original fixed initial/terminal inventory** remain active. A registered Type I steel-gas **200 bar absolute** source pressure screen enforces a minimum inventory corresponding to **20 bar absolute** minimum withdrawal, subject to the original hydrogen storage capacity semantics. Compressor charge electricity uses the documented RVO/LBST source 80% compressor / 90% motor and two ideal intercooled-stage engineering assumption. Real installed compressor efficiency maps, duty cycling, piping, pressure losses, cooling auxiliary electricity, safety controls, maintenance, actual emissions and manufacturing are **excluded**.

Per hour the independently recalculated controls include:

```text
Wind[t] + Grid[t] = PEM[t] + Compressor[t] + Curtailment[t]
H2_target_common[t] = eta_H2 * PEM[t] - Charge[t] + Discharge[t]
S[t] = (1 - hourly_loss) * S[t-1] + Charge[t] - Discharge[t]
       - source_equivalent_gas_heel_loss
S_8760 = source_original_terminal_inventory
Pressure_TypeI_200bar_from_EOS(S[t]) stays in screened bounds
min(Charge[t],Discharge[t]) = 0
```

The first hour uses the original source starting inventory rather than fictitious year-boundary continuity. Original source configurations set **the same initial source storage inventory** for E and E+S; their 20t/40t physical inventory capacities and pressure-dependent heels differ. Stage A and Stage B physical model assumptions are reused, not replaced with a simplified no-buffer or hypothetical hydrogen supplier.

Numerical certification requires source and Stage A ZIP hashes, exactly 8,760 model-hour rows, both E and E+S actual feasible solutions, independently checked H₂/electricity/pressure/cost residuals **< 2×10⁻⁴** in model variable units, and solver reported **relative MIP gap ≤ 1×10⁻⁶**. The true minimum wholesale cost is bounded by `HiGHS dual ≤ optimum ≤ audited feasible incumbent` for each case. The paired wholesale saving range is therefore:

```text
saving = minimum_C_E - minimum_C_ES
certified bracket:
  dual_lower_E - incumbent_upper_ES
  <= saving <=
  incumbent_upper_E - dual_lower_ES
```

**These are deterministic optimization-error intervals, not statistical prediction or engineering uncertainty intervals.** Exact independent solver/energy audit and evidence: [4-job original-source F3-C CI](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43580088115), [PtXLens independent four-source hash/physical audit](https://github.com/Open-Energy-Methods/PtXLens/actions/runs/43580637209), [paired machine-readable comparative certificate](../data/results/F3_C_2023_source_real_gas_equal_H2_hour_E_vs_ES_Lens_operational_bridge.json). PtXLens rejects any changed byte via each frozen original-source result SHA.

## 4. Results — 2023 net wholesale grid-settlement only

| Quantity | Gross physical inventory interpretation | Usable-bank source interpretation |
|---|---:|---:|
| Original modelled E-delivered H₂ reference (kg/year) | 16,335,279.317 | 16,335,279.317 |
| E feasible Stage A **additional** physical shortfall (kg/year) | 66,524.317 | 3,720.371 |
| **New common H₂ service** for BOTH E and E+S (kg/year) | **16,268,755.001** | **16,331,558.946** |
| Unmet original 18.25m kg contract (kg/year) | 1,981,244.999 | 1,918,441.054 |
| E 20t source 2023 wholesale net electricity (€) | 25,587,589.630 | 25,880,392.499 |
| E+S 40t source 2023 wholesale net electricity (€) | 24,463,257.361 | 24,776,928.770 |
| **E+S lower modelled wholesale settlement (€)** | **1,124,332.269** | **1,103,463.729** |
| **HiGHS optimizer bound on saving (€)** | **[1,124,318.034, 1,124,348.115]** | **[1,103,461.954, 1,103,474.625]** |
| E 20t compressor model electricity (MWh/year) | 1,809.723 | 1,854.018 |
| E+S 40t compressor model electricity (MWh/year) | 2,020.742 | 2,057.143 |
| E 20t grid import (MWh/year) | 298,691.881 | 299,228.756 |
| E+S 40t grid import (MWh/year) | 287,138.578 | 287,921.712 |
| E 20t grid export (MWh/year) | 37,715.011 | 35,186.230 |
| E+S 40t grid export (MWh/year) | 25,545.972 | 23,224.334 |

**Interpretation and counterexample to overclaim:** the larger bank consumes **more compressor electricity** in the optimized source dispatch but buys electricity at more favorable modeled source hours, reducing annual wholesale settlement at equal annual **and hourly** delivered H₂. It is **not** automatically more energy-efficient, less polluting, cheaper over a lifetime or better investment. Higher manufacturing steel pressure-vessel burden and annualised capital/cooling/maintenance are absent. Price volatility and source optimization timing control the result; no causally identified field demonstration.

**Important subtlety:** the source 40t system is not merely '20t plus physical extra tank' in a validated manufacturer engineering design. Capacity modes, pressure heels and existing installation details must be reconciled with a physically specified inventory and incremental component BOM before any physically complete incremental CAPEX / production emissions result.

## 5. Provenance and remaining v1.0 release stop

Original source archive Stage A/H2 derivative and E/ES prices/wind were downloaded privately into a CI runner from authenticated original GitHub Actions, SHA checked and processed there. **Raw original provider ENTSO-E XML, wind arrays and 2023 original private source files were not committed to these public repositories.** Source-derived hourly H₂ target signatures and strictly modelled numerical summary results were preserved, with cross-repository matched SHA metadata.

The committed four individual source MILP results (also imported byte-identically into PtXLens) are:
- [gross E](../data/results/F3_C_2023_source_pressure_matched_max_inventory_E.json) SHA `59aaa727416364c2f0f1df1544f32bfc4456550ef14ce3679d78fc9abbff5fed`
- [gross E+S](../data/results/F3_C_2023_source_pressure_matched_max_inventory_E_plus_S.json) SHA `f53039f09b7005280023e6835dce60e5b595b0df76b254f14765e0df5a08e2e9`
- [usable E](../data/results/F3_C_2023_source_pressure_matched_usable_service_E.json) SHA `88597c1cbc5e07b5cbee84129dd64dede410470cc5078a7e8d19d3b5ca616662`
- [usable E+S](../data/results/F3_C_2023_source_pressure_matched_usable_service_E_plus_S.json) SHA `885ebc26c75107d8439aa9a5b29ec7666e1b933ee866f8c63423a22dc05131b6`.
- [Independent PtXLens paired-only operational comparison](../data/results/F3_C_2023_source_real_gas_equal_H2_hour_E_vs_ES_Lens_operational_bridge.json), SHA `dddd07d5c0a3d4f276e80af44e28cf3cfdbc93421107fb5d9e39843a0d1d90e2`.

**Outstanding scientific priorities:**
1. **P0:** make and recover the original E, E+S and A44 ZIPs on lawful long-lived *private* media (all original GitHub Actions artifacts live-verified unexpired on 14 Nov 2026, first scheduled expiry **24 Dec 2026 19:24:29 UTC**; not yet privately escrowed).
2. **F3-C publication:** freeze source/final versions, audit hourly state witness portability and perform alternate price/year/parameter sensitivity; any alternate hourly demand changes the service and must be registered separately.
3. **F2/L1:** manufacturer-constrained physically buildable stationary Type I vessels, weight/steel/cycle life, compressor/cooler/regulator/meter/BoP, full source manufacturing and uncertainty distributions. Type I 20t → 40t includes more than `delta capacity_kg`.
4. **L2/L3:** full source-linked native BAFU 2026 v1.1 installed incremental LCI, geography and chosen attributional/consequential method, maintenance/replacements/end-of-life/uncertainty; lifetime revenue/cost/discount model consistent with the matched-service functional unit. Only then a cautious environmental/economic comparative conclusion. Historical 2023 vs prospective 2026 supplier must not be mixed as an actual 2023 plant.
5. **Independent reviewer:** verify market provenance rights, computer/solver versions, inventory engineering assumptions, the 2023 modelled-service vs full contract distinction, and release-gate satisfaction.

**Decision:** F3-C *numerical physically screened operational equal-hour service* **VERIFIED** for two modes. Full physical manufacturer design, environmental source attribution, financial comparison, P0 and hydrogen/methanol v1.0 **NOT PASSED**.

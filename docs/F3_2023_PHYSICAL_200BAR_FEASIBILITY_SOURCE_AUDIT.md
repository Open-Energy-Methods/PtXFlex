# F2/F3 pressure-bounded 2023 source checkpoint — infeasibility before environmental comparison

**Date:** 2026-11-13. **Programme:** OEM-PTX-2026-01 · F2/F3.  
**Verified execution:** [real 2023 8,760-hour source and real-gas screened Type I study](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43514524449).  
**Code:** [F3 physical-screen solver](../src/ptxflex/f3_matched_ideal_benchmark.py) · [source duty/units](../src/ptxflex/pressure_storage_duty.py) · [source feasibility and evidence recorder](../scripts/f3_physical_pressure_2023.py).  
**Source result:** derived SHA256 \`a8240205a15d905ffe48e8443a69c227b9bfe1b1788229b67b6daeac218a74c1\` of workflow artifact \`pressure_investigation/F3_pressure_screen_incremental_summary.json\`, artifact ID \`14079912306\`. Source archives preserve original E SHA256 \`069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051\` and E+S \`cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9\`.

## Quantitative analysis and methodological changes

- **Genuine input:** original 2023 Netherlands observed day-ahead electricity-price series and ERA5-derived offshore-wind availability; 125 MW PEM, source 50MW grid, 10t initial/terminal inventory, and **same 8,760-hour original E-delivered H₂ modelled profile** (16,335,279.317 kg) as the attempted E/E+S service. This is **not** actual H₂ plant telemetry and does **not** meet the original full 18.25m kg/year demand.
- **Literature source hardware:** Ademollo et al., [DOI 10.1016/j.ijhydene.2025.152849](https://doi.org/10.1016/j.ijhydene.2025.152849), Table 2, *Type I steel, 200 bar* reference 1.8 m³ internal/free volume and 2,400 kg **empty vessel mass**. Source paper reference pressure is treated as absolute for the scenario; its gauge/absolute basis is not independently demonstrated.
- **Real-gas pressure and working inventory:** CoolProp 8.0.0 pure-H₂ equation of state at **313 K** (constant gas-temperature scenario); minimum 20 bar absolute delivery as a no-downstream-boosting reference assumption, with nonzero real-gas heel. The original PyNEXUS numerical 20/40t values are **maximum inventory**, not physically certified withdrawable H₂. A separate *usable_service* scenario asks for 20/40t withdrawable above heel, requiring a different number of vessels and different initial-stock interpretation.
- **Source compressor assumptions:** [Netherlands RVO/LBST report (2023)](https://www.rvo.nl/sites/default/files/2023-12/GHG_EF_including_conversion_efficiencies_for_RFNBO_GHG_calculations_LBST.pdf), **80% compressor and 90% electric motor efficiency; 313 K** suction; in this screening, equal two-stage source-CoolProp real-gas isentropic enthalpy method for **30→200bar**. All storage charge is billed at the **maximum vessel operating pressure** (1.136551 kWh/kg), an explicit conservative pressure-duty approximation, not a measured compressor map, varying tank-pressure work or cooler-power model.
- The 2023 source MILP now enforces hourly wind + grid = PEM electrical power + charging compressor MW + curtailment, gas mass inventory **above EOS pressure heel**, H₂ mass balance including source existing standing loss, and exact same hourly delivered service. Initial/terminal model stock remains 10t. All optimized results require independent mass/energy/cost residuals, EOS pressure limits and HiGHS optimality ≤10⁻⁶. Reference equipment masses **do not** constitute a detailed manufactured-material BOM.

## First actual full-year physical-screen result

| Source-based Type I 200bar screening case | E original maximum **20t** | E+S original maximum **40t** |
|---|---:|---:|
| Vessels at 313K, 20–200bar | 803 | 1,605 |
| Empty reference-vessel mass (tonnes) | 1,927.2 | 3,852.0 |
| EOS minimum retained gas / heel (kg) | 2,213.96 | 4,425.17 |
| Same original E hourly H₂ delivery demand | **INFEASIBLE** | **VERIFIED FEASIBLE** |
| E+S net wholesale grid settlement (EUR2023) | **Not available; model infeasible** | €24,954,564.75 |
| E+S compressor electricity (MWh) | **Not available; model infeasible** | 2,029.67 |

| Revised **physically usable** 20/40t bank alternative | E requested **20t usable** | E+S requested **40t usable** |
|---|---:|---:|
| Source Table 2 vessels | 902 | 1,804 |
| Empty reference-vessel mass (tonnes) | 2,164.8 | 4,329.6 |
| EOS retained gas / heel (kg) | 2,486.92 | 4,973.84 |
| Same original E hourly H₂ delivery demand | **INFEASIBLE** | **VERIFIED FEASIBLE** |
| E+S net wholesale grid settlement (EUR2023) | **Not available** | €24,806,275.87 |
| E+S compressor electricity (MWh) | **Not available** | 2,057.68 |

**Critical result:** The earlier 2023 **ideal** E vs E+S equal-service model showed a net grid wholesale settlement difference of approximately €1.142m/year in favor of E+S. That benefit **does not translate into a valid same-service physical comparison** under either Type I 200bar screening interpretation, because E cannot meet the fixed original E hourly H₂ service once the new pressure and electric constraints apply. Infeasible E has **no true minimum wholesale cost** at that exact service. Do not fill this missing value with the previous ideal-storage E cost.

The E+S results above are **single feasible-source configurations**, not proof that any actual hydrogen storage installation is technically permitted or that E+S is financially/environmentally superior. The additional bank now contains substantial *published reference empty equipment mass*; this is not a manufacturing material allocation, BAFU native GWP, compressor motor/support BOM or installed total cost.

## Source-locked next assessment: Stage A minimum additional shortfall

The important follow-up is a **real original-2023 demand-adequacy experiment**: minimize additional unserved H₂ for the physically screened E and E+S cases *against the same original E-delivered hourly target*, then report precisely **which hours and how many kilograms** cannot be delivered. This is preferable to silently changing original demands, prices, tank lower-pressure bounds, power and compressor efficiency until a desired economic answer appears.

[Actual source-based Stage A code](../src/ptxflex/f3_pressure_adequacy.py) and dedicated real-2023 workflow perform this next assessment. If a scenario cannot meet the original common hourly target, any subsequent TEA/GWP comparison must explicitly match its *actual* product service or price a common externally justified backup. It is scientifically inappropriate to compare per-kg LCA/levelized costs for infeasible, unmatched service.

**Further unresolved F2/F3 gates:** vendor vessel code/certification and manufacturer tank BOM, published pressure-basis confirmation, non-isothermal charging/discharging and pressure drop, actual compressor map/rated electrical power and interstage cooler power, source operating leakage rate, product purity, full original 50t/day service adequacy and PtXLens full manufactured-capacity native BAFU v1.1 characterization. The [PtXLens original BAFU vehicle-tank unit incompatibility](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/wp0-screening-core/docs/L1_BAFU_STATIONARY_H2_TANK_PROVIDER_UNIT_AUDIT.md) remains a hard stop for full climate impact.

**Scientific status:** A reproducible 2023 source-pressure-screened **feasibility finding**, not full project v1.0 validation or industrial comparative LCA/TEA.

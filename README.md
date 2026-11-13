# PtXFlex — weather/market-grounded PtX value-chain optimization research

**F2→F3 physical pressure correction (source-locked 2023):** the new [Type I 200bar real-gas EOS/313K + RVO two-stage compressor full-year study](docs/F3_2023_PHYSICAL_200BAR_FEASIBILITY_SOURCE_AUDIT.md) found the original **E 20t** bank *infeasible* for the original E hour-by-hour delivery target under either max-inventory or physically usable interpretation, while **E+S 40t** met that modelled service in both screens. The previous ideal €1.142m operating-savings result is **not** a valid physically matched cost or GWP comparison. It is a pressure and compressor *screen*, not a dynamic certified plant. [F3 Stage A minimum additional H₂ shortfall workflow](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43515507811) is the next scientific adequacy gate. Source unit/mass-matching to native BAFU remains incomplete.

### 13 November 2026: source-checked F2/F3 technical checkpoints

**Physical source correction:** The frozen PyNEXUS 20/40 tonne limits are **maximum ideal H₂ inventory**, not guaranteed usable H₂; pressure-swing heel must be accounted for. [F2 source-studied vessel/EOS working-volume table](docs/F2_PUBLISHED_STORAGE_PRESSURE_SWING_AUDIT.md) and [25 passing physics tests](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43502681218) compare actual published Type I/II/III/IV example vessel dimensions/masses. These are screening candidates, not actual certified plant hardware.

**Real 2023 full-year F3 pilot:** both independently solved HiGHS MILPs now deliver the **same H₂ amount in every 2023 hour**, fixed to original E-delivered model service (16.335279m kg). Net historical wholesale settlement **€25.7489m (E) vs €24.6070m (E+S)**, or ~€1.142m lower with ideal additional storage, MIP solver gap ≤10⁻⁶ and independently verified physical accounting. [F3 methods and limitations](docs/F3_2023_MATCHED_H2_IDEAL_PILOT_VERIFIED.md) · [machine-readable source result](data/results/F3_original2023_E_ES_ideal_matched_hourly_H2_annual_verified.json). **NOT** full 50t/day contract, pressure-limited storage, compression electricity, complete TEA, or environmental superiority. An actual manufacturer-matched physical BOM, plant losses, pressure-duty and PtXLens full LCA remain open.



## Coordinated scientific v1.0 — adopted research programme

**Start here:** [cross-repository v1.0 master plan](docs/PROGRAMME_MASTER_PLAN_v1.0.md) · [12 engineering decision records](docs/DECISION_REGISTER_v1.0.md) · [machine-readable release gates](research/gates-v1.0.json) · [strict shared exchange schema](contracts/ptx-exchange-v1.schema.json) (identical in PtXLens).

**Executed first-stage evidence:** [F1 source benchmark workflow](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43497912940) independently audited **17,520** frozen E/E+S original hourly PyNEXUS records with common 2023 wind, market price and H₂ demand sequences; both original solved cases have unmet demand and cannot be called matched service. [F2 CoolProp 8 physics workflow](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43498612013) verified real-gas density, usable storage *working volume*, isentropic H₂ compression and mass-balance equations (15 physics tests). Screening pressure points are *not* an approved physical tank specification and **do not include actual tank manufacturing mass**.

**Research scope gate:** PtXFlex owns source-verified physical hydrogen dispatch, storage thermodynamics, 8,760-hour matched-service optimization and a separately source-validated methanol subsystem. PtXLens owns the same-boundary physical equipment BOM, private licensed BAFU native LCA and full financial assessment. No real-data methanol LCA or complete E/E+S physical storage comparison exists yet. The original four-hour methanol MILP is synthetic verification **only**. [F2 equipment/pressure task](https://github.com/Open-Energy-Methods/PtXFlex/issues/4) · [F3 matched service task](https://github.com/Open-Energy-Methods/PtXFlex/issues/5).



**Status: genuine 2023 Netherlands wind and electricity-price inputs independently ingested; methanol-plant physics, hourly carbon data, and real-source optimized production remain unvalidated.**

## Real-source pipeline: executed successfully

Actual GitHub Actions workflow: https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43419654583

It retrieves the archived **original PyNEXUS 2023 E observed-market ZIP** from a registered GitHub Actions artifact, validates the full ZIP SHA256 and Stage B SHA256, and imports **8760 annual hourly** wind availability and Dutch day-ahead market price records. Data are derived from ERA5 wind and observed original 2023 Dutch ENTSO-E A44 prices. They are **not** measurements from an operating methanol plant.

~~~bash
python -m pip install -e ".[dev]"
python -m pytest -q

# Use authentic original ZIP from frozen PyNEXUS evidence artifact 12612294862
ptxflex /path/to/pynexus-original-E-2023.zip \
  --import-pynexus-2023-e \
  --output outputs/real_inputs/nl_market_wind_2023.json
~~~

The import intentionally records hourly grid/wind GWP as **null**, never invented or derived from the price. It explicitly sets solver_ready=false until environmental factors and methanol process assumptions are sourced and validated.

## Separate mathematical MILP proof of concept

The original SciPy/HiGHS optimizer models wind/grid/electrolyser conversion, H2 storage, CO2 availability, ideal methanol reaction, synthesis min load/commitment, ramping and an optional operational-emissions constraint for a fixed methanol delivery target. It independently checks all modeled energy/mass/stoichiometric and cost/impact constraints. The only runnable emissions-constrained example currently uses **fabricated four-hour numeric fixtures for testing the mathematics**, **not scientific findings**.

~~~bash
ptxflex examples/illustrative_methanol.json
ptxflex examples/illustrative_methanol.json --emissions-cap-kgco2e 200
~~~

**Do not confuse tests with a grounded Power-to-X process study.** The methanol pathway still lacks sourced commercial chemistry conversion, recycle, separations, reactor heat, compression, auxiliary loads, validated CO2 supply/fate, realistic storage design, capacity sizing and properly scoped life-cycle impact.

The route to credible 2023 real-input optimization requires a compatible source-verified hourly grid GWP inventory, source-verified reactor/synthesis constraints, documented methanol plant energy and CAPEX, a product-gate specification and subsequent actual LCIA. No negative carbon credit from CO2 incorporation is assumed without sourcing the CO2 origin and end-use. Avoid name-dropping Aspen or treating this as vendor-calibrated.

Upstream evidence: https://github.com/abhijith-sivaprasadan/PyNEXUS (frozen Oct 2026); linked economic/LCA research: https://github.com/Open-Energy-Methods/PtXLens .

The source and MILP development are AI-assisted research software requiring independent scientific review. No plant-validated or ISO 14044-compliant results claimed.

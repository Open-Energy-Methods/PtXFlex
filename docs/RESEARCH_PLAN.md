# PtXFlex methodological boundary and programme

## Initial verified scope, subject to CI

A *hypothetical* four-hour wind/grid-to-electrolyser-to-H2 inventory-to-methanol MILP solved by SciPy/HiGHS, with an independent recomputation of all documented constraints.

- Material conversion: CO2 + 3 H2 -> CH3OH + H2O, ideal stoichiometric mass ratios fixed by molecular masses. Real reactor equilibrium, conversion/yield, recycle and separation are **not yet modelled**.
- Electricity supply: wind used plus grid used feeds electrolysis **and an explicit methanol synthesis auxiliary load**. No process heat integration, compression, oxygen handling or plant pressure simulation yet.
- Electrolyser rated power, fixed kg H2/MWh, grid cap, H2 inventory and terminal stock, synthesis binary commitment/min-load, synthesis hourly ramp and CO2 supply cap.
- Fixed total methanol service; optimize *variable electricity and synthesis operating charges* (not full CAPEX-based production cost). Optional operational kgCO2e epsilon cap with source-labelled hourly factors; independently verify every hourly balance and cost/emissions.
- No hydrogen or CO2 environmental credit, no automatic renewable-hydrogen certification. CO2 remains a feedstock whose origin and end-of-life fate are **unmodelled**.
- All bundled inputs were invented to exercise the model and sensitivity; no physical or economic performance should be attributed to a real plant.
- No OpenPyTEA/openLCA/Brightway tool execution or integration in this repository. PtXLens is the intended future external TEA/LCA assessment engine.

## Acceptance gates

WP0: solver/CI setup, transparent unit/equation tests, feasible and infeasible impact cases, independent balance audit.
WP1: physically supported electrolyser performance including efficiency/load/operating degradation and a sourced auxiliary-power model, not only a single fixed yield.
WP2: validated methanol pathway reaction/CO2 supply boundary, with water, syngas, recycle, separation and storage feasibility.
WP3: representative 8760-hour renewables/market datasets with timestamp + provenance, no silent synthetic-to-observed promotion.
WP4: literature-based full CAPEX/OPEX and cradle-to-gate inventory using PtXLens; no double counting.
WP5: multi-year weather/price uncertainty, dispatch vs capacity design and epsilon frontier, independent comparisons at matched production service.
WP6: peer-review-ready methods and data release after validation.

This is AI-assisted research software. The Aalto application should mention **only completed, tested functionality**, never claim Aspen, commercial-grade process simulation, full PtX value-chain LCA, ISO 14044 conformance or industrial validation from this repo.

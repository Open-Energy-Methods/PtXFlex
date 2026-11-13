# PtXFlex — weather/market-grounded PtX value-chain optimization research

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

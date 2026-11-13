# PtXFlex

**Status: executable hypothetical renewable-H₂-to-e-methanol MILP baseline, pending independent scientific validation.**

PtXFlex models wind and grid electricity, a PEM electrolyser with fixed screening yield, H₂ inventory, limited CO₂ availability, ideal methanol reaction stoichiometry, synthesis min-load/commitment, and ramping. SciPy/HiGHS minimizes specified variable operating cost for a **fixed methanol delivery target**, optionally subject to an operational GWP cap. An independent audit reconstructs electricity, H₂ stock, CO₂, target, commitment, ramp, cost and emissions constraints.

~~~bash
python -m pip install -e ".[dev]"
python -m pytest -q
ptxflex examples/illustrative_methanol.json
ptxflex examples/illustrative_methanol.json --emissions-cap-kgco2e 200
~~~

**All bundled inputs are invented four-hour mathematical fixtures**, not equipment vendor information, industrial operating data, sourced electricity carbon factors, or a full chemical-process simulation. GWP is operational factor accounting, **not** an openLCA/Brightway LCIA. CO₂ source and fate, reaction conversion and recycle, compression, process heat, separation and all plant CAPEX remain unmodelled.

See [method, limitations and evidence gates](docs/RESEARCH_PLAN.md).

The separate [PtXLens repository](https://github.com/Open-Energy-Methods/PtXLens) will eventually evaluate verified dispatch traces with explicit cost, LCI and life-cycle boundaries. **This baseline is not yet cross-validated or connected** to PtXLens or to frozen PyNEXUS data.

Implementation is AI-assisted research software, to be independently reviewed before publication or claims of scientific/industrial predictive accuracy.

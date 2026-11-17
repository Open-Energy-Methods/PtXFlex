# F2/L1 equipment handoff completeness screen — 14 November 2026

Programme OEM-PTX-2026-01; ADR-004/005. This is a **negative-control software increment**, not an approved hydrogen pressure system or a completed BOM.

## Scientific question

Can a partial vessel-only reference mass be mistakenly passed to PtXLens as a complete manufactured storage system? The new `src/ptxflex/f2_l1_handoff.py` requires explicit records for ten component groups: pressure vessels, compressor, aftercooler, manifolds/piping, isolation/control valves, relief/vent, instrumentation, supports/foundations, motor/electrical, and hydrogen detection. It rejects absent groups, zero/negative/nonfinite equipment masses, invalid source SHA-256 metadata, unauthenticated source bytes, missing pressure basis, inverted pressure/temperature windows, and invalid counts. It records open manufacturer, cooling, site, fatigue, hazard, and compressor-map reviews.

A synthetically complete fixture can become **review-ready only**; its outputs always state design_certified=false, native_bafu_lcia_complete=false, industrial_validation=false, v1_release_approved=false. The gate does **not** verify source authenticity itself: bytes_authenticated and review_state are supplied metadata that must be corroborated by an independent human reviewer and preserved documents. Thus no real installation can be qualified solely by this program. A real pressure system also requires standards/code review, drawings, fatigue/embrittlement analysis, relief sizing, layout and operating constraints.

## Sources and scope

- [Published Type I–IV vessel Table 2](https://doi.org/10.1016/j.ijhydene.2025.152849) is a representative *vessel-only* screen; paper pressure gauge/absolute basis and manufacturer conformity remain unresolved.
- [CoolProp hydrogen thermophysical properties](https://coolprop.org/fluid_properties/fluids/Hydrogen.html) supports the separate EOS working-capacity calculation, not a vendor certificate.
- [RVO/LBST RFNBO compression report (2023)](https://www.rvo.nl/sites/default/files/2023-12/GHG_EF_including_conversion_efficiencies_for_RFNBO_GHG_calculations_LBST.pdf) supplies illustrative compression assumptions, not measured plant performance.
- The BAFU vehicle composite-tank reference unit is not a stationary Type I steel-vessel manufacturing functional unit. No BAFU manufacturing impacts are calculated by this screen.

## Reproducibility

`python -m pytest -q tests/test_f2_l1_handoff.py` (requires repository test dependencies). Test data are explicitly synthetic and contain no observations, vendor data or licensed LCI. Expected tests: 10 missing-component cases, six invalid-mass cases, unauthenticated source, missing manufacturer, cooling/map omission, pressure and temperature inversions, and explicit no-release flags. **Do not claim tests passed until the actual workflow finishes.**

## Gate interpretation

F2 and L1 remain NOT_PASSED. The next scientific task is to replace null/unknown manufacturer and pressure-boundary inputs with independently traceable source documents and physical site conditions; then review actual component quantities, real-gas temperature swing, pressure drops, compressor/cooler duties and native BAFU provider units. The review-ready flag is never equivalent to industrial validation or complete LCA.

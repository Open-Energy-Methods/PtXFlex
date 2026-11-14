# F3 fixed-trace backup supplier offer: qualification screen v0.1

**Programme:** OEM-PTX-2026-01. **Date:** 2026-11-14. **Status:** code-verification increment; **F3 NOT_PASSED**.

## Evidence boundary

The original frozen 2023 E-delivered hydrogen profile is a modelled source service, not measured industrial hydrogen. Stage A/Stage B derive feasible-incumbent hourly **additional** shortfall under a specified Type I 200-bar vessel and RVO compressor scenario. The source hourly shortage must be authenticated by its canonical SHA-256 and linked to a frozen PyNEXUS source registry before an actual 2023 supplier assessment. The new `f3_backup_offer_screen.py` does **not** select a hydrogen supplier, assign a price or environmental factor, assert real 2023 availability, or imply that a hypothetical proposed supply profile is physically obtainable.

## Acceptance equations

For each hour t, `q[t]` is the authenticated source-derived top-up requirement at the delivery node and `s[t]` is a separately proposed delivered supplier flow. A fixed-schedule offer must satisfy:

- `s[t] >= q[t]` for all 8760 source-index hours, not merely `sum(s) >= sum(q)`.
- `max(abs(s[t]-s[t-1])) <= R` for t=1..8759, without inventing a 2022/2024 boundary transition.
- Supplied hydrogen pressure at the **delivery node** must meet the named absolute-bar pressure threshold.
- Supplied hydrogen purity at the delivery node must meet the named mole-fraction threshold.
- Pressure/purity documentary evidence must be explicitly marked present. Even if all numerical checks pass, the output still says real supplier/2023 availability **not verified**.

The method recomputes the canonical Stage A trace digest, checks finite nonnegative hourly mass, reports residual hourly/annual shortage and source assumptions, and never upgrades a screening certificate to full-plant approval. A source profile and a proposed supplier offer remain two separate evidence classes. The code has **no upstream buffer**: a different physical system with buffering or co-optimized dispatch requires a new model, not a relaxed pass.

## Verification

`tests/test_f3_backup_offer_screen.py` uses only 8760-hour **synthetic mathematical fixtures**, not fabricated 2023 observations. Tests cover exact-hour identity, annual-equal but hour-shifted offers, source-trace tampering, pressure, purity, ramp, documentary gate, invalid/NaN input and explicit within-year ramp interpretation. Run `python -m pytest -q tests/test_f3_backup_offer_screen.py` and the repository CI suite.

## Unresolved scientific work

A genuine supplier offer needs independently documented country/technology/year, hydrogen composition and delivered pressure, available hourly flow, outages and ramp behavior, transmission and compression, contract and costs, manufacturing/installation inventory and the corresponding native BAFU v1.1 process units. No private BAFU inventory is copied here. The F2 vessel pressure/gauge and compressor maps, L1 stationary manufacturing BOM, F3 full-source service, L2 full GWP, L3 discounted TEA and X1/X2 review gates remain open.

This screen cannot validate an E vs E+S environmental superiority claim, prove a minimum backup rating, or justify a v1.0 release.

## Independent CI failure diagnosis and correction — 2026-11-14

Before this correction, both MILP verification jobs at GitHub Actions run
[43563399469](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43563399469)
failed: **3 failed, 99 passed, 5 skipped**. The three failures were all in
`tests/test_f3_backup_offer_screen.py`, and came from an incorrect *test
oracle*, not a verified physical-supplier failure. The fixture has hourly
shortfalls `[10,20,10,5]` kg/h and zero flow immediately before and after.
Its largest **adjacent hourly change** is 10 kg/h, not its **peak flow**
of 20 kg/h. Consequently, the purported rejection of a 19 kg/h/h ramp
limit was invalid; that limit actually admits the 10 kg/h/h fixture.

The corrected tests use a 10 kg/h/h ramp expectation and a 9 kg/h/h
rejecting threshold. Additional tests independently check the 10 vs 9.999
threshold and confirm the 2023 year is **not** silently treated as a cyclic
2022/2024 boundary. These are synthetic verification fixtures, not original
2023 dispatch. Correcting the test expectation does not establish
industrial compressor/supplier dynamics.

Correction commit:
[58d641c](https://github.com/Open-Energy-Methods/PtXFlex/commit/58d641cdf22a371670bf7d041e3a1ea9a224bf1b).
CI runs:
[43567814582](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43567814582)
and
[43567810981](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43567810981).
They must complete successfully before the regression is called CI-certified.
The F3 scientific gate remains **NOT_PASSED** regardless of test outcome.

**Further qualification limit:** The input `pressure_and_purity_independently_documented=True`
is a caller-supplied Boolean, not independently inspected supplier documentation.
The screening pass therefore describes *mathematical eligibility under claimed
input documentation*, not independent supplier verification. Do not use the
screen's pass flag as a release, LCA, TEA or physical procurement gate.

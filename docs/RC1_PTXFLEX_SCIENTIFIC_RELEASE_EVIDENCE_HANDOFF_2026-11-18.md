# RC1 — PtXFlex scientific software evidence handoff and release blockers

**As-of audited public research commit:** `eb9e6ff` (18 November 2026). **Status:** original pressure/hydrogen reference evidence publication and regressions, **NOT** a full industrial/scientific v1.0.

The authoritative cross-repository [RC1 finding register and tests](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/rc1-release-audit/docs/RC1_PAIRED_SCIENTIFIC_SOFTWARE_RELEASE_AUDIT_2026-11-18.md) are in PtXLens, which checks both checkouts. This PtXFlex handoff freezes the four source-reconstructed L3-F evidence blobs with SHA-256 regression checks and verifies original 12-gate v1.0 release restrictions.

## Scientific scope admitted

- Original F2 2023 Type I reference **20,000 kg added MAXIMUM hydrogen inventory**, distinct from **17,784.924849614785 kg reference withdrawable pressure swing**.
- Source-verified 313K paper reference plus hypothetical 303/323K and 293/333K CoolProp real-gas endpoint sensitivity, not dynamic validated bank operation.
- Original source 1.8 m3 internal-free-volume literature paper vessels; 802 reference incremental positions and 2,400 kg **EMPTY reference equipment per vessel** are neither a supplier-qualified station nor virgin steel manufacturing input.
- Thirteen documentary site/PED/HAZOP/operational review domains and 19 original equipment/BoP/OPEX/EOL categories, all **unverified for an installed site**.
- The paired research comparison maintains 30t/day modelled H2 same hour for E20t/E+S40t in each of 2022 and 2024, with 2022 and leap-year 2024 historical source-year boundaries separate. No vendor all-in installed CAPEX or independently run native BAFU project LCIA is authorized.

## Version and integration

The `pyproject.toml` software version is currently **0.1.0**, not 1.0. This is a research prototype with mathematical verification and source-locked results, not a pressure equipment design package. **All 12 programme science work packages are NOT_PASSED** in the preserved common `research/gates-v1.0.json` source.

The original PtXFlex PR [#1](https://github.com/Open-Energy-Methods/PtXFlex/pull/1) to `main` has hundreds of commits and changed files and is **merge-conflicted/draft** at RC1 inspection. Do not force the original PR through before resolving conflicts and testing an actual integration commit.

The published original 2023 PyNEXUS E/ES/A44 archive expiry is documented as **24 December 2026** (not independently rechecked for ongoing availability here). Priority P0 is lawful two-copy, privately controlled original-source preservation and restoration with SHA/ZIP validation, **not** public GitHub redistribution. Missing site/manufacturer, source escrow, independent research validation and native BAFU remain blockers.

## Tests and publication discipline

`tests/test_rc1_l3f_public_evidence_freeze.py` checks the exact SHA-256 of all four published public research files, guards distinct gross/usable values, 13 domain /19 BOM line scope, and requires that the research does not claim station PED, installed OEM quotes or full programme v1.0.

The PtXLens [paired RC1 module](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/rc1-release-audit/src/ptxlens/rc1_release_audit.py) checks both checkouts' identical master plan, ADR decisions, science gates, shared contract, published ten files and basic tracked filename exclusions. A pass is ONLY a source-scoped **research evidence integrity pass**. It is not historic provider data licence clearance, native product-system LCIA, comprehensive vulnerability scan, independent physical validation or full scientific v1.

**Release result pending reviewer/CI:** bounded RC1 research audit, not a formal v1.0 scientific/industrial release.

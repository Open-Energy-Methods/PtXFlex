# F3 supplier release-admissibility audit — 2026-11-14

Programme OEM-PTX-2026-01. This increment adds a *separate* release-admissibility decision to PtXFlex. It does not alter original 2023 PyNEXUS evidence, physical pressure calculations, supplier source records, or BAFU inventory.

## Scientific distinction

1. The 8,760-hour offer screen checks a proposed numerical delivery trace, pressure/purity thresholds and adjacent-hour ramp. Its caller-supplied documentary boolean is not independent verification.
2. The documentary contract checks the format and completeness of an asserted source record. It explicitly does not authenticate document bytes, issuer, customer exit pressure or actual availability.
3. The new `f3_supplier_release_gate.py` requires **both** upstream checks and an eight-part explicit independent-review checklist before it returns *supplier_release_admissible*. The flags are themselves **not proof**: their source documents, actual hashes, reviewer identities, dates, site/contract records and engineering calculations must be audited externally. The new function always returns `full_programme_v1_gate_passed: false`.

Synthetic-only negative tests verify that each review element is independently necessary, missing/ambiguous flags fail, and upstream self-certification is rejected. A hypothetical all-true checklist is a code-verification fixture, **not a real supplier finding**.

## Scope and open gates

The historical E 20t pressure-screen incremental backup shortfall is distinct from the original model's approximately 1.915 million kg/year unmet contractual demand. Restoring *incremental* service relative to original E dispatch does **not** restore the original 18.25 million kg/year target. A complete matched-service comparison must explicitly choose and source the target service, terminal storage condition, pressure, purity, outages and all backup energy/infrastructure.

F2 lacks qualified installed equipment, pressure losses and compressor/cooler performance; L1 lacks an actual manufacturer BOM and compatible native BAFU supplier; F3 lacks a source-authenticated site-specific supplier with 8,760-hour guaranteed delivery. L2/L3 and downstream gates remain NOT_PASSED. No industrial, ISO-comparative or full lifecycle claim is supported.

## CI

The GitHub PR verification for the new test commit was queued when inspected; do not infer passing tests from this documentation. The last observed pre-change PtXFlex MILP workflow was successful at commit `21c260c`, run 43577047052. Latest new-run link: https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43577239284 . Both PRs remain draft; do not merge or tag.

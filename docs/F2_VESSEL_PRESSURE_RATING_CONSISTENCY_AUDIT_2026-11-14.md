# F2 vessel maximum-pressure consistency audit — 2026-11-14

Programme: OEM-PTX-2026-01. Scope: **numerical screening invariant only**, not a pressure equipment conformity assessment.

## Defect and correction

The F2/L1 review-readiness checker previously accepted a candidate whose `pressure_vessels.rated_pressure_bar_absolute` was positive but **less than** `maximum_storage_bar_absolute`. This is an internal physical inconsistency: a storage vessel's declared rated absolute pressure must not be lower than the stated maximum operating absolute pressure. The checker now raises `HandoffError` on this condition. Negative tests cover under-rating, zero, negative, NaN, infinity and Boolean values; equality is permitted as a *screening* boundary, **not** a safety margin or approved design.

Do not extend this one-vessel constraint indiscriminately to all downstream equipment: a pressure regulator can isolate a genuinely lower-pressure segment. Such a claim requires a separately sourced P&ID, relief sizing, failure-case assessment and independently reviewed segment design pressure. The existing checker does not establish any of these.

## Independent physical and regulatory evidence still required

A real manufacturer datasheet and conformity file must establish whether its published working pressure is gauge or absolute, actual MAWP/PS, allowable temperature and cycling, hydrogen materials and embrittlement assessment, test pressure, protection and relief philosophy, pressure drops and compressor/cooler design envelope. Published catalogue pressure ratings and a 313 K CoolProp pressure swing are not a PED-certified assembled installation. See [European Commission PED 2014/68/EU](https://single-market-economy.ec.europa.eu/sectors/pressure-equipment-and-gas-appliances/pressure-equipment-sector/pressure-equipment-directive_en), [NEN-EN 17533:2025](https://www.nen.nl/en/nen-en-17533-2025-en-338598) and [EIGA DOC 247/24](https://www.eiga.eu/uploads/documents/DOC247.pdf).

This increment adds **no** equipment mass, 2023 supply observation, manufacturer approval, native BAFU process or cost. F2/L1 remain NOT_PASSED; original 2023 modelled hydrogen is not plant measurement; no matched-service environmental or total-cost superiority is claimed. The review-ready Boolean is a metadata screen, not independent physical acceptance.

## Reproduction

Run `pytest -q tests/test_f2_l1_handoff.py` on `feat/milp-methanol-baseline`. The new cases are `test_vessel_rating_cannot_undershoot_maximum_storage_pressure`, `test_equal_vessel_rating_is_mathematical_screen_only`, and `test_downstream_low_pressure_rating_needs_separate_segment_review`. Record actual CI run ID and SHA after completion; do not infer a pass from commit creation.

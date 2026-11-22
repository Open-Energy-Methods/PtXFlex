# F3 supplier evidence review contract — 2026-11-14

**Programme:** OEM-PTX-2026-01. **Status:** INCREMENT IMPLEMENTED; SCIENTIFIC GATE NOT PASSED.

The previous `f3_backup_offer_screen.py` accepts a caller-supplied boolean
`pressure_and_purity_independently_documented`. That boolean is **not**
independent inspection, document authentication or proof of an actual supplier.
Its `fixed_trace_supplier_offer_screen_pass` is a mathematical scenario
screen only, never supplier qualification.

The additional `f3_supplier_evidence_contract.py` requires a structured
documentary record: supplier/facility, issuer, document title, HTTPS locator,
claimed SHA-256, page/table locator, absolute pressure, purity, flow, ramp,
validity dates, geographic/delivery scope and access/license basis.
Negative tests reject missing, nonfinite, impossible and ambiguous fields.
A complete record explicitly returns **false** for independently authenticated
source bytes, verified issuer, 2023 hourly availability, physical delivery
and LCA/TEA eligibility. The tests contain synthetic metadata only.

**Remaining external evidence actions:** obtain actual manufacturer/supplier
documents with authorized access; authenticate source bytes against the
claimed digest; inspect units and absolute/gauge pressure; independently
confirm issuer, delivery-node compatibility, pressure, purity, hour-by-hour
2023 supply, outages, ramp, compression, transport and cooling; obtain
reviewer sign-off. No real supplier has been qualified.

**F2/L1 remain upstream blockers:** Type I reference-vessel scaling is not a
manufacturer-qualified installed stationary storage BOM; neither native
BAFU v1.1 manufacturing provider matching nor complete compressors/coolers
and containment are established. Therefore no matched industrial LCA,
comparative superiority, or v1.0 release is permissible.

**Verification protocol:** `python -m pytest -q tests/test_f3_supplier_evidence_contract.py`;
then confirm branch-head GitHub Actions verification. A green test proves
contract logic only, not independent documentary review.

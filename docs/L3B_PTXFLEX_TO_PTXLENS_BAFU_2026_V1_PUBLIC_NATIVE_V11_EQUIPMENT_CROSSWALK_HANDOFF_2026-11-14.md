# L3-B to PtXLens — BAFU:2026 native material/process handoff, 2026-11-14

**Programme:** OEM-PTX-2026-01 · F2/F3 physical equipment to L1/L2/L3 economic and environmental boundaries.

The source F2 Type I hydrogen-bank model remains a **screening model**, not a manufacturer-approved installed plant. The independent PtXLens process catalogue work is tracked in [the PtXLens BAFU material crosswalk](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/wp0-screening-core/docs/L3B_BAFU_2026_v1_PUBLIC_TO_NATIVE_v11_TYPEI_STATIONARY_MATERIAL_PROCESS_CROSSWALK_2026-11-14.md) and the [source-verified 16-identity shortlist](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/wp0-screening-core/research/L3B_BAFU2026v1_SOURCE_VERIFIED_PUBLIC_PROCESS_SHORTLIST_NOT_NATIVE_v11_2026-11-14.json).

## What has actually been verified

- Full public Swiss FOEN *BAFU:2026 v1* `IPCC 2021/GWP 100` catalogue: exactly **11,947 process identities** under 16 official GraphQL UUID-prefix source partitions, rechecked original raw CSV SHA256 `7a6dc0f2cf43527b1c329dfa0383679abef68e5129859898abc5d11309e08265`. [Independent PtXLens Actions source review](https://github.com/Open-Energy-Methods/PtXLens/actions/runs/43644651127) confirmed 16 selected published UUID/name/geography/unit identities. This is **not** a native BAFU v1.1 foreground inventory or linked product-system validation.
- Candidate examples (still **unapproved for installed equipment**): low-alloy steel RER kg; 18/8 stainless steel RER kg; metal forming service RER kg; generic pipe CH kg; normal concrete CH m³; freight RER t·km; NL high-voltage electricity MJ; industrial heat CH MJ; alternative recycled-content steel-feedstock routes. These source reference units cannot be silently treated as per kg installed pressure-vessel equipment.
- Original EcoSpold BAFU v1 composite-vehicle tank UUID `b4739ad2-aa38-368d-8ada-63f5417c8b55` is **explicitly rejected** as a substitute for a stationary Type I steel vessel mass. Source says per kg H₂ capacity despite a kg product unit; this is not kg of empty Type I equipment.
- Original BAFU v1.1 source ZIP SHA256 `e63b7e7ef5cde04bfe1176a783a55b5f72e2b73f42c36632b6150af39d348c4c` remains registered for permitted **private** native process/reference-flow identity replay. This new crosswalk's native v1.1 process verification **has not run** in the current workspace; the executable independent GreenDelta openLCA 2.7 source verifier is compiled and ready in PtXLens, not yet used to license an OEM background supply graph.

## Frozen physical and equipment assumptions

- Original E 20,000kg vs E+S 40,000kg model capacity, two separate interpretations: `max_inventory` and `usable_service` (with a gas residual heel); 30bar(a) PEM, 20bar(a) delivery floor, 313K constant-temperature gas EOS screen, 200bar(a) upper pressure screen.
- Published Ademollo et al. Type I 1.8m³/2,400kg finished empty-equipment example is specified at **200bar(g)** nominal reference and harmonized **2024 EUR**, not a vendor quote or installed site design. Source incremental reference counts: 802 gross-vs-gross and 902 usable-vs-usable equipment units. Finished mass cannot directly be reinterpreted as virgin steel raw input or as native LCIA mass.
- Actual manufacturer feedstock alloy grade, fabrication material yields/scrap, welding/heat-treatment energy, structural rack, safety equipment, approved pressure compliance, compressor/cooling BoP, site foundations, transports, maintenance/replacement and end-of-life provider flows are not established.

## Interface requirement for any quantitative PtXFlex → PtXLens LCIA

Each of the source 19 equipment classes must provide `quantity`, `reference_unit`, material grade/pressure-service proof, geography, expected life, quantity confidence interval, dated revision-controlled original manufacturer source SHA and any direct fabrication inputs. The native v1.1 target must then be checked for exact original process UUID, **quantitative reference flow UUID**, `PRODUCT_FLOW/WASTE_FLOW` status, correct dimensional units, upstream supplier linkage and technology; PtXLens must independently reject unit mismatches and duplicate material/process accounting. No physical parameter should be selected by back-fitting to a desired GWP or investment result.

Economic/electricity historical-year source dispatch and native hardware GWP are separate calculations. Both must be evaluated against the exact **same hourly H₂ output service** within a comparison; do not combine original unmatched 2023 E/E+S PEM reference impacts with a separate F3 matched-hour cost benefit and claim system superiority. 2022/2024 observed ERA5 weather source pair and independent year-specific MILP results are still pending as of this handoff. No price-vintage conversion or manufacturer CAPEX is supplied by BAFU.

**Decision:** P0 source independent physical backup/rights, L1 OEM bill, L2 native station GWP, L3 actual installed CAPEX/operating OPEX and v1.0 scientific publication all **NOT PASSED**. Provider names, legal use and original source hashes are not substitutes for a measured industrial BOM.

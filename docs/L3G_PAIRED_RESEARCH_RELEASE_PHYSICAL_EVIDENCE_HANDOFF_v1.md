# F2/L3-G PtXFlex scientific evidence handoff to PtXLens

**Scope:** Source-verified, unqualified physical/reference screening evidence for the 2022/2024 original matched-service stationary H2 storage study. The paired L3-G admission code and claim-to-evidence register live in [PtXLens](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/l3g-release-qualification/docs/L3G_PAIRED_SCIENTIFIC_RELEASE_CLAIM_EVIDENCE_PROTOCOL_v1.md).

**Two repository coordination:** This branch is based on the existing feat/milp-methanol-baseline research branch; the corresponding PtXLens work uses feat/l3g-release-qualification based on feat/wp0-screening-core. The same branch names do **not** imply that either existing draft PR to main is merged.

## Required exact PtXFlex research handoff

The paired PtXLens L3-G auditor independently regenerates these four PtXFlex public L3-F reports, cross-checks their source field values and SHA-256 bytes, and refuses any modified file:

- data/results/L3F_H30_TYPEI_REFERENCE_20t_INCREMENTAL_FREE_VOLUME_THERMAL_DISCRETE_SCREEN_NOT_OEM_v1.json
- data/results/L3F_H30_TYPEI_REFERENCE_THERMAL_PRESSURE_DESIGN_SCOPE_NOT_OEM_v1.md
- data/results/L3F_H30_TYPEI_20t_40t_SITE_PED_P_AND_ID_OEM_QUALIFICATION_REQUIREMENTS_NOT_APPROVED_v1.json
- data/results/L3F_H30_SITE_DESIGN_AND_MANUFACTURER_EVIDENCE_GAPS_NOT_APPROVED_v1.md

Source-defined reference **20,000 kg incremental MAXIMUM inventory is NOT identical to 17,784.924849614785 kg reference pressure-swing usable inventory**. Thermal endpoint scenarios are analyst sensitivities; the original 802 hypothetical 1.8 m3 positions and 2,400 kg EMPTY equipment each are not actual installed bank counts, original steel input, site layout, or signed supplier specifications.

The 13 domain site/pressure/COP/HAZOP engineering checklist and 19 original F2 equipment categories have a source-reproducible documentary contract. A source check **does not** authenticate missing site-specific OEM material compatibility, pressure-vessel PED certification, compressor cycle duty, actual process hazards or signed quotation. Pressure in the EOS screen is **bar absolute**, not manufacturer-certified gauge MAWP.

## Unresolved release gates

The corresponding PtXLens economic bridge uses separate 2022 and 2024 historical matched 30 t/day H2 service under original 90% source model wind electrical power. Hypothetical CAPEX zero-NPV boundaries are not future earnings and are not project NPV.

Real OEM and installed site engineering costs, authenticated source-year price/contract rights, 13 site safety approvals, actual manufacturing input masses, native BAFU 2026 v1.1 process/provider/flow mapping and independent native LCIA remain unresolved. Annual electricity deltas do not establish a lifecycle GHG direction.

## Reproduction and publication discipline

In PtXLens run the local `-Phase Test`, `-Phase L3FAuditPublic`, `-Phase L3GPrepare`, `-Phase L3GAuditPublic` workflow (max_inventory only). This checks the four PtXFlex files against source reconstruction plus the four PtXLens L3-F files and two additional PtXLens L3-G manifest reports. No vendor private data or original source-year hourly MILP is rerun.

The four PtXFlex files were untracked at the preceding Windows checkpoint; publication requires exact file inspection and deliberately staged commits. Neither this handoff nor a passed L3-G manifest grants broad scientific v1.0, physically verified station design, cost-bank viability or native LCA claim.

**Handoff decision: publicly scoped source-model research only; industrial and full v1.0 certification BLOCKED.**

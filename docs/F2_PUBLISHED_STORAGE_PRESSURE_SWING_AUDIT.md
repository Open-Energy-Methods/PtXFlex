# F2 scientific checkpoint — original PyNEXUS storage semantics and published vessel pressure-swing audit

**Programme:** OEM-PTX-2026-01, F2 / ADR-004. **Research state:** SOURCE-VERIFIED PRELIMINARY VESSEL SCREENING; no final vessel design, full F2 pass or manufacturing/operating LCA.

## 1. Critical original-source result

The **original SHA-frozen 2023 PyNEXUS WP5 E/E+S config.yaml**, not an assumed hardware model, explicitly specifies:

| Parameter | Both source models | Evidentiary status |
|---|---:|---|
| PEM outlet | 30 bar | Original modeled equipment assumption; reference BAFU 30bar PEM matches |
| Pipeline minimum delivery | 20 bar | Original modeled minimum delivery pressure, not measured industrial offtake |
| Storage bound E / E+S | **20,000 / 40,000 kg H₂** | Maximum numerical stock state, NOT proven *working* gas capacity |
| Initial and minimum terminal stock | 10,000 kg H₂ | Same source assumption for both models |
| H₂ charge / discharge limit | 2,200 kg/h each | Both configured model limits, not an installed compressor curve |
| Storage hourly standing loss | **0.0001 of previous stock** | Existing conceptual gas-loss assumption; no sourced vendor leak test |
| Maximum grid import/export | 50 MW | Original conceptual plant connection |
| PEM rated input | 125 MW | Original numerical plant |
| H₂ demand | 50,000 kg/day | Original nominal hourly demand; original E/E+S both have shortfall |

**Source:** [PyNEXUS frozen original 2023 workflow](https://github.com/abhijith-sivaprasadan/PyNEXUS/actions/runs/40229852457), E ZIP SHA256 069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051, E+S ZIP SHA256 cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9; \`optimization/dispatch.py\` and both original archived \`config.yaml\` define the original stocks and pressure limits.

The original storage state is allowed from zero to configured maximum. Physically, a pressure-vessel inventory cannot be withdrawn down to zero gauge/absolute pressure while maintaining **20-bar minimum delivery**. The model therefore omits physically necessary tank heel/working capacity and may overestimate dispatch flexibility. **This is a model-form gap, not an error in the frozen original optimizer. Do not revise original source artifacts.**

## 2. Representative published pressure-vessel reference (not an approved design)

Scientific reference: [Comparative techno-economic assessment of stationary hydrogen storage technologies](https://doi.org/10.1016/j.ijhydene.2025.152849), **Table 2**, Type I/II/III/IV and pressure/capacity/mass. EOS: [CoolProp Hydrogen](https://coolprop.org/fluid_properties/fluids/Hydrogen.html), version 8.0.0, based on Leachman et al. 2009.

Use **real-gas** density \(\rho(P,T)\) at 298.15 K (screening temperature, not measured original atmospheric/vessel temperature) and assumed **absolute** 20-bar minimum to represent no additional booster on the delivery path. The source literature's pressure basis remains to be independently confirmed. Source Table 2 provides the *actual reference empty vessel equipment mass*, not a conversion from 20 t H₂ to steel mass.

For each reference vessel:

\[
m_{\max}=V\rho(P_{\max},T),\qquad
m_{\mathrm{heel}}=V\rho(P_{\min},T),\qquad
m_{\mathrm{working}}=m_{\max}-m_{\mathrm{heel}}.
\]

Count vessels by \(\lceil m_{\mathrm{source,max}}/m_{\max,\mathrm{vessel}}\rceil\) for original *maximum inventory* interpretation. For an explicit new *20/40t usable service*, instead use \(\lceil m_{\mathrm{required,usable}}/m_{\mathrm{working,vessel}}\rceil\); **do not conflate these two interpretations**.

### Screening results at 298.15 K, 20-bar absolute lower bound: original E nominal 20,000 kg

| Published vessel reference | Number of vessels | Empty vessels (tonnes) | Withdrawable H₂ (tonnes) | H₂ heel (tonnes) |
|---|---:|---:|---:|---:|
| Type I steel, 30 bar, 2.1 m³, 2.30 t/vessel | **3,974** | 9,140.2 | **6.59** | 13.41 |
| Type I steel, 200 bar, 1.8 m³, 2.40 t/vessel | **768** | 1,843.2 | **17.80** | 2.22 |
| Type II composite-overwrapped steel, 350 bar, 1.3 m³, 2.15 t/vessel | 660 | 1,419.0 | 18.63 | 1.38 |
| Type III metal-liner composite, 350 bar, 1.8 m³, 1.30 t/vessel | 477 | 620.1 | 18.64 | 1.38 |
| Type IV polymer-liner composite, 350 bar, 1.8 m³, 1.20 t/vessel | 477 | 572.4 | 18.64 | 1.38 |

**Interpretation:** At original 30-bar storage pressure and 20-bar delivery minimum, the literature-bank *nominal maximum gas inventory of 20t* supplies only ~6.59t of working H₂ without an additional downstream booster. This does **not** prove the original stored H₂ had to be 30 bar: its configuration never specified an actual tank pressure design. **All rows are alternative hypothetical hardware mappings** for the original model capacity.

The common 200bar Type I reference, for example, requires **768** published reference vessels / **1,843 t** empty reference shell/bank mass to hold ~20t maximum inventory, leaving ~2.22t unavailable below 20bar. To provide a true *20t recoverable* service at that pressure swing, the bank requires **864** reference vessels / **2,074t** empty vessels. For original E+S, corresponding 200bar Type I 40t maximum inventory mapping uses **1,535** vessels / **3,684t** empty vessel mass with ~35.57t working; a **40t usable** design would require **1,727** vessels / **4,145t** empty bank mass.

**This bank is not a cost-minimized actual installation**: pressure vessel construction may use different large-cylinder dimensions or different vessel technologies. No fabrication material fractions, supports, manifolds, compressors, cooler, footprint, pressure-cycle fatigue/embrittlement, delivery equipment, operating schedule, or pressure-gauge conversion has been validated. Required additional material/operating GWP is currently **UNKNOWN**, not zero.

### Technical review gates

- [x] Independently inspected both actual original source configs and verified 20/40t **max-stock interpretation**, 10t initial/terminal, 30bar PEM/20bar pipeline, charge/discharge limits and hourly model loss.
- [x] Implemented [published vessel source register and pressure-swing EOS](../src/ptxflex/storage_reference_vessels.py); no fabricated one-to-one H₂-to-vessel-mass factor.
- [x] [25 CoolProp and vessel-specific numerical QA tests](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43502681218) passed and published all **20 candidate bank / semantics combinations** as derived data, with explicit no-full-LCA flags.
- [ ] Confirm source paper pressure gauge/absolute basis and reference metal/composite inventory allocation.
- [ ] Select a *named* product-gate pressure/purity and source actual storage compression and bank temperature dynamics; include pressure/enthalpy lift and cooling duty and dynamic working-capacity constraint.
- [ ] Independently assess ASME/EN code requirements for particular tank types and fatigue/service life. **ISO/FDIS 19884-1 is UNDER DEVELOPMENT as of November 2026**; a draft is not design approval.
- [ ] Obtain actual manufacturer/supplier pressure-vessel BOM / installation, compressor/cooling/valves/supports, mass and economics; validate geometrical internal volume/material scope.
- [ ] Integrate with source-based matched-service 8,760h optimization, run independent residual checks, then hand engineering BOM to PtXLens for suitable BAFU characterization and double-count protection.

**LCA caution:** BAFU 2026 v1 process UUID b4739ad2-aa38-368d-8ada-63f5417c8b55 is a **road/vehicle component** high-pressure composite tank and explicitly says "per 1 kg hydrogen" in its underlying LCI description, though nominal output unit is kg. It must NOT be multiplied by **empty Type I steel vessel mass**. [PtXLens source-unit audit](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/wp0-screening-core/data/results/BAFU2026_v1_storage_tank_source_unit_mismatch_audit.json) records this incompatibility.

**Current publication claim:** Verifiable **reference sensitivity of physical working capacity and published hardware masses**, NOT a vendor-specific stationary hydrogen engineering design, ISO-compliant vessel or full E/E+S cradle-to-gate footprint.

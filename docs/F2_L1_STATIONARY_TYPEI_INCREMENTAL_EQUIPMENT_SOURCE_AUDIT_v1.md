# F2/L1 — incremental 20 t Type I stationary hydrogen equipment: sourced geometry, physical mass and unresolved manufacturing inventory

**Programme OEM-PTX-2026-01 · 14 November 2026 · Status: source-backed preliminary engineering and material-inventory REQUIREMENTS, not a complete vendor-signed BOM, construction specification, native BAFU LCIA or whole-plant TEA.**

## 1. What the original model actually specifies — and what it does not

The original 2023 PyNEXUS E configuration has **20,000 kg maximum modelled H₂ stock**, E+S **40,000 kg**, identical **10,000 kg initial and terminal stock**, and a common maximum **2,200 kg/h modelled charging and discharging** flow. Electrolyser output is assumed **30 bar**, industrial product node **20 bar**. These are source simulation assumptions, not approved physical equipment, site coordinates, measured pressure, cycle-life or vessel steel bills. The source historical wind input coordinate (52.5°N,3.5°E) is an *offshore ERA5 sampling location*, **not a real hydrogen tank site**.

The 2023 [F3-C reference](F3_C_2023_PHYSICAL_COMMON_HOURLY_SERVICE_VERIFIED.md) is now mathematically compared using the same exact hourly reduced H₂ product delivery, original 2023 prices and wind, a real-gas Type I 200bar(a) EOS inventory screen, and compressor charge electricity. Results: E+S has **€1.12433m/yr lower NET WHOLESALE ELECTRICITY settlement** (gross interpretation) or **€1.10346m/yr** (distinct usable interpretation). These are **not** avoided total lifecycle costs; source H₂ service is lower than the original full 18.25mkg industrial demand.

**Key F2/L1 question:** Is this simulated increase from 20 t to 40 t compatible with manufactured hydrogen-rated pressure storage equipment? What source-auditable *equipment masses* can we calculate, and what installed equipment foreground is still unknown? This report takes a conservative **source-led technology-and-mass accounting** approach, never inferring material mix or equipment cost from output capacity alone.

## 2. Source hierarchy, nominal conditions and commercial category distinctions

| Source | Verified public specification | Scope / restriction |
|---|---|---|
| [Ademollo et al., IJHE 2026, DOI 10.1016/j.ijhydene.2025.152849, Table 2](https://doi.org/10.1016/j.ijhydene.2025.152849) | Type I all-metal **200 bar reference**, **1.8 m³ internal volume**, **2,400 kg EMPTY vessel equipment**, **~26 kg nominal H₂ per vessel**, paper reference **25 vessels per container** | Peer-reviewed physical **reference**, not manufacturer product certificate, exact steel alloy/process input, pipe station or installed/site price. Paper pressure gauge vs absolute remains unconfirmed. |
| [heiserTEC COSMOS **Stationary (PED)** manufacturer catalogue](https://www.heisertec.com/products/bundles/) | Type I forged steel bundles **210/330/550 bar**; specific **210-bar class, 36 × 87 L**, **49 kg gross H₂ per module at published nominal conditions**, galvanized structural frame, stainless-steel manifold, integrated thermal safety valve | Actual stationary commercial product architecture and gross H₂ storage rating. **Stationary module empty mass is NOT published**, vendor quality/service/cycle conditions not verified. **210-bar class ≠ research 200bar(a) product approval**. |
| [heiserTEC **Type 1 Hydrogen** individual cylinder product catalogue](https://www.heisertec.com/products/type-1/) | A **distinct 50 L Type I hydrogen cylinder**, **PED**, **EN 1964-1**, **330-bar working pressure catalogue**, 472-bar test catalogue, **85.5 kg empty cylinder mass** | Manufacturer per-*cylinder* empty mass, not an actual 210-bar **36×87 L bundle** or an original 200-bar 1.8m³ reference cylinder. Any calculated use at 200bar(a) is a **derated mathematical sensitivity**, not OEM operating approval. |
| [EIGA Doc 247/24, §7.3.1 and §7.4.3](https://www.eiga.eu/uploads/documents/DOC247.pdf) | Bundles/manifolds/isolation valves, frames, periodic inspection, hydrogen material fatigue/embrittlement, safety and pressure-regulation equipment | Engineering *scope*. Does not provide weights, project geometry or conformity certificates; risk/safety study still needed. |
| [NEN-EN 17533:2025, official Dutch standards publisher](https://www.nen.nl/en/nen-en-17533-2025-en-338598) | Published standard for stationary gaseous H₂ cylinders/tubes of Types 1–4 (up to 10,000 L water volume, <=1,100 bar maximum); **assemblies and external pipework excluded** | An applicable **published standard**, not a claim that these candidate OEM/paper designs satisfy its clauses. Current normative context is not limited to an ISO draft. |
| [European Commission PED 2014/68/EU](https://single-market-economy.ec.europa.eu/sectors/pressure-equipment-and-gas-appliances/pressure-equipment-sector/pressure-equipment-directive_en) | Stationary pressure equipment and assemblies, manufacture/design/conformity; applicable threshold >0.5bar | Regulates site-ready pressure systems; **no project conformity file exists**. |
| [Burckhardt Compression, Hydrogen Mobility & Energy catalogue, Apr 2026, p.2–3](https://www.burckhardtcompression.com/fileadmin/uploads/burckhardt/documents/applications/compression-solutions-hydrogen-mobility-energy-burckhardt-compression-en.pdf) | Real manufacturer industrial **oil-free hydrogen compressors up to 200 bar**, plus compressors' motor/controls, process heat exchangers, cooling/MCC | A **product family**, not a specific 30→200bar, **2,200kg/h**, 313K duty-qualified unit, mass, P&ID or vendor quotation. |
| [heiserTEC Mobile (TPED), hydrogen 12×50 L 200bar; same catalogue](https://www.heisertec.com/products/bundles/) | **935 kg nominal ±6% empty mobile TPED bundle** | **Explicitly excluded** as a *stationary PED* empty mass or raw steel mass; no 935kg multiplication by stationary module count. |

### Source EOS basis

For all calculations here the source F3 model uses **isothermal 313 K**, with hypothesized **200 bar absolute maximum**, **20 bar absolute withdrawal minimum**, real-gas density `CoolProp 8.0.0: Hydrogen`. An actual 200-bar or 210/330-bar OEM rating may be specified in *gauge* terms. We have **NOT reconciled nominal gauge/absolute plate ratings**, dynamic transient temperatures, pressure drop, compressor discharge, maximum cycle count or fault conditions. **None is certified as a buildable installation**.

```text
m_at_max_per_vessel = V_inner × rho_H2(200bar(a), 313K)
m_heel_per_vessel   = V_inner × rho_H2( 20bar(a), 313K)
m_working           = m_at_max - m_heel

E count = ceil(20,000kg / (m_at_max OR m_working))
E+S count = ceil(40,000kg / (same m_at_max OR same m_working))
additional reference cylinders = count(E+S) - count(E)
additional EMPTY EQUIPMENT kg = extra cylinders × published EMPTY vessel mass
```

`max_inventory` uses original gross 20,000/40,000 kg upper model state, `usable_service` represents an *alternative* 20,000/40,000 kg withdrawable above residual heel. **Do not combine these two materially different functional quantities.**

## 3. Primary literature Type I reference — computed source equipment count and *empty* mass

The source [executable code](../src/ptxflex/f2_stationary_incremental_bom.py) uses original 2023 F3-C exact-hour operating case SHA, [published Type I source](../src/ptxflex/storage_reference_vessels.py) and original CoolProp EOS; verified [CI](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43583202468). Results are preserved [as source-verified JSON](../data/results/F2_L1_2023_source_incremental_20t_to_40t_stationary_typeI_200bar_BOM_SCOPE_NOT_complete_native_LCI.json) SHA-256 **`1315d1181b9d1eab6d3368425c9571dbe295c3360935d2972403bf3c60e2dc47`**.

| Literature Type I 200bar 1.8m³ / 2,400kg vessel | 20t E | 40t E+S | **Additional** E+S vs E |
|---|---:|---:|---:|
| **Gross `max_inventory`** vessels | 803 | 1,605 | **802 vessels** |
| Empty reference equipment (t), gross | 1,927.2 | 3,852.0 | **1,924.8t** |
| 25-position source-reference containers, minimum grouping | 33 | 65 | **32 additional containers** |
| **Withdrawable `usable_service`** vessels | 902 | 1,804 | **902 vessels** |
| Empty reference equipment (t), usable | 2,164.8 | 4,329.6 | **2,164.8t** |
| 25-position source-reference containers, minimum grouping | 37 | 73 | **36 additional containers** |

All quantities are anchored in the paper's **reference vessel equipment mass** and explicit source CoolProp EOS; **none is kg hydrogen or a native virgin-steel manufacturing exchange**. The Type I paper's per-container **346m²** includes illustrative clearances and is **NOT multiplied by container count** into a certified site area. The 25-per-rack groupings are literature layout abstractions; *actual rack frame weight, number/geometry/stacking and site area remain unknown*.

**Full-rack subtlety:** the gross variant has 803 E vessels in 33 racks (22 unfilled positions), vs 1605 E+S vessels in 65 racks (20 unfilled positions). It therefore has **802 extra loose vessels but only 32×25 = 800 added rack slots**. The two filled-rack alternatives **do not have the same baseline cylinder procurement**: a calculation using “32 fully stocked extra racks” assumes prefilled E racks and is **not an upper or lower bound on an installation with partially occupied racks**. The source records both alternatives as *different assumptions*. Rack frames and headers are still not quantified.

**Gas heel is NOT vessel material:** at 313K the gross E bank retains approximately **2,214 kg H₂** below 20bar; E+S gross **4,425 kg H₂**. Under the usable interpretation, E needs more absolute vessel volume and retains **2,487 kg heel**, E+S **4,974 kg heel**. These are gas inventory stocks, not pressure-vessel manufacturing inputs.

## 4. Two distinct real OEM product checks, not substitutes for the paper vessel

### A. 210-bar stationary COSMOS 36×87 L 49kg gross-H₂ bundle

Actual manufacturer [COSMOS Stationary PED](https://www.heisertec.com/products/bundles/) provides **3.132m³ water volume per 36-cylinder bundle** and **49kg nominal gross H₂ per bundle at supplier-rated conditions**. Those conditions are not automatically the F3 200bar(a), 313K operating state.

In a **separate 200bar(a), 313K EOS screening of that published volume**, each module would contain about **43.38kg gross**, **38.59kg withdrawable** above 20bar(a). This implies **462 E / 923 E+S modules for gross**, or **519 E / 1,037 E+S modules for usable**. **Those are mathematical volume-based modular counts, NOT physically approved vendor modules.** Manufacturer 210-bar product pressure basis, gas temperature, fatigue/cycle proof, actual usable state and **stationary module empty weight** remain unresolved. In particular, the separate 935kg TPED mobile bundle has **no permission to substitute** for these 36×87L stationary module weights.

### B. Manufacturer's **330-bar-rated PED hydrogen 50 L / 85.5 kg empty cylinder**

An independent heiserTEC [Type 1 cylinder data sheet on its public product page](https://www.heisertec.com/products/type-1/) supplies a *real manufacturer-reported per-cylinder empty weight* for a **different** H₂-compatible 50L PED/EN1964-1/330-bar item. We evaluate its **0.05m³ water volume** using the *same modelled* 313K and 200→20bar(a) EOS pressure swing, and do not assume it is suitable for the 210bar COSMOS modules or certified at the study site.

| Separately rated OEM 50L cylinder at *hypothetical* 200bar(a) screening | E20t | E+S40t | **Additional manufactured empty cylinders** |
|---|---:|---:|---:|
| Gross inventory | 28,878 | 57,756 | **28,878 cylinders ×85.5kg = 2,469.069 t** |
| Usable inventory | 32,468 | 64,936 | **32,468 cylinders ×85.5kg = 2,776.014 t** |

One such manufacturer cylinder stores **about 0.69258kg** at 200bar(a), 313K, of which **about 0.61599kg** is withdrawable down to 20bar(a). The 330bar manufacturer's *pressure class* is **different** from the 200bar modelled operating limit; approval, actual grade, dynamic service, assembly, maintenance, pricing and plant physical constructability are still **unknown**. This is an **independent geometric/weight cross-check**, not an alternative vendor price, a single technology's error bar, or evidence for building tens of thousands of small pressure cylinders.

Proof [OEM source and EN17533 register](../research/F2_L1_INDEPENDENT_OEM_PED_50L_330BAR_H2_CYLINDER_AND_EN17533_SOURCE_v1.json), [OEM EOS code](../src/ptxflex/f2_oem_PED_cylinder_200bar_sensitivity.py), [original-source successful CI](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43583991352), [source-hash-controlled calculated result](../data/results/F2_L1_OEM_heisertec_PED_330bar_50L_85_5kg_source_200bar_313K_NOT_certified_BOM.json) SHA-256 `9db1885bd42cc91049c4d2e7170aaf74782bf0d791ed88b877795e84fa4a8a57`.

## 5. Incremental system equipment BOM — coverage complete, *quantification incomplete*

The following **19-category engineering scope** makes every still-unknown LCI component explicitly visible. It does not assert that 18 unknown items all require entirely new standalone hardware in an existing site; whether existing equipment can be reused is precisely one of the missing engineering decisions.

| Component category | Source / functional duty | Quantity and manufacturing mass |
|---|---|---|
| 1. Additional Type I pressure-vessel reference hardware | Table 2 200bar 1.8m³, 2,400kg/vessel | **802×2,400kg** gross OR **902×2,400kg** usable (paper reference, not OEM grade) |
| 2. Certified material chemistry, heat treatment, nozzles | Manufacturer heat/steel certification, hydrogen cycling, production route | **Unknown** composition/fabrication mass |
| 3. Structural racks/frames/supports/anchors | EIGA stationary rack and inspection access | **Unknown** |
| 4. High-pressure piping and headers | PED hydrogen-compatible pressure and fatigue design | **Unknown** |
| 5. Isolation and actuated valves | Bundle cut-out, emergency shutdown, serviceability | **Unknown** |
| 6. Filters and backflow/check valves | Product cleanliness and backflow prevention | **Unknown** |
| 7. Pressure relief, vent header/stack | H₂ dispersion, API/EN/PED safety design | **Unknown** |
| 8. Pressure regulation/product delivery | 20bar(a) minimum **after** genuine station and line losses | **Unknown** |
| 9. Hydrogen charging compressor | Actual 30→200bar(a) operating map, sealing, H₂ material compatibility | **Unknown incremental machine count/mass** |
| 10. Motor, VFD, MCC, power connection | Source original 2,200 kg/h conceptual charge limit, not OEM nameplate | **Unknown** |
| 11. Intercooler and aftercooler | Non-ideal compressor discharge temperatures, interstage pressure losses | **Unknown** |
| 12. Cooling pumps/fans and auxiliary electricity | Additional thermal management and climate impacts not included in F3-C | **Unknown** |
| 13. Dryer, H₂ purity monitoring/sampling | End-use gas quality specification not stated | **Unknown** |
| 14. Flow, pressure, temperature instrumentation | Traceable metering and pressure-protection monitors | **Unknown** |
| 15. ATEX hydrogen-leak sensors, shutdown and fire/safety | Safety integrity and hazardous area classification | **Unknown** |
| 16. Foundations/concrete/civils | Approved site, loading, footprint, transport access | **Unknown** |
| 17. Inspection, fatigue-cycle life, repair and maintenance | EN17533 individual vessel design, PED assembly; EIGA cycling | **Unknown** |
| 18. Site transport, assembly, construction and commissioning | Regional geography, cranes, energy, welds/pressure tests | **Unknown** |
| 19. Replacement/decommissioning/end of life | Service life, scrap steel routing, recycling and future embodied emissions | **Unknown** |

**Source 2023 capacity ≠ installed compressor:** original maximum *permitted charging* is **2,200 kg/h** (=52.8 tonnes/day). In the F3-C optimized reference source cases, realized modelled maximum charge is ~**552.43 kg/h** and maximum discharge ~**2,083.33 kg/h**. Whether the existing compression plant can use the same machine for a larger bank, needs new parallel trains, different pressure ratios, more coolers, redundancy or pressure control is **undetermined**. The 2026 Burckhardt public 200bar compressor family confirms that an industrial equipment category exists, not any source machine weight/contract/offer.

## 6. Environmental and economic accounting must remain null

A source literature's “empty vessel equipment mass” is **not equal** to mass of virgin low-alloy steel available to allocate to a BAFU native process, nor does it establish forging electricity, machining scrap, paint, inspection, or fabrication location. Likewise, an OEM 85.5kg complete empty cylinder weight does not identify its alloy constituents, secondary steel fraction, melt route or packaging. The [PtXLens original BAFU 2026 v1 tank provider audit](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/wp0-screening-core/data/results/BAFU2026_v1_storage_tank_source_unit_mismatch_audit.json) identifies a composite **road vehicle** tank per kg *H₂ capacity*, **not** per kg stationary Type I steel shell; no naive mass multiplication is permitted.

For an admissible native 2026 BAFU inventory, obtain a pressure-vessel-specific **functional unit and manufacturer material fabrication flow** (kg appropriate steel grade and forging or verified production process), supports/racks/manifolds and EIGA/PED auxiliaries, compressing/cooling process equipment manufacturing and operating loads, transport, repairs, time/geographic assumptions and replacement/EOL. Then map each actual source flow to **compatible BAFU v1.1 provider UUID + unit + geography**, with explicit allocation rules and independent checks; do not insert `0` for unknown items. The existing native Swiss 30bar PEM process and scoped original E/E+S Dutch source LCA remain *different boundaries*. Calculated climate impact: **NULL**.

Any economic comparison needs source-appropriate EUR year, manufacturer installed vessel/station invoices, labor, foundation, connection, maintenance, inspection, compressor replacements, electricity cooling auxiliaries, residual value, depreciation, financing/discount rate, operation and availability, and site H₂ contract service. **F3-C's €1.10–1.12m/year 2023 wholesale settlement advantage alone does not establish a net lifetime advantage.** The cost of installing additional steel and balance-of-plant remains **NULL**, not the paper's approximate technology price silently presumed valid in the 2023 site.

## 7. Evidence, governance and remaining acceptance

- Frozen engineering [OEM+standard source register](../research/F2_L1_STATIONARY_TYPEI_OEM_AND_STANDARDS_SOURCE_REGISTER_v1.json) and [separate manufacturer 330bar cylinder source](../research/F2_L1_INDEPENDENT_OEM_PED_50L_330BAR_H2_CYLINDER_AND_EN17533_SOURCE_v1.json) are mirrored in **both** repositories.
- F2 source code [Type I bank and incremental BOM](../src/ptxflex/f2_stationary_incremental_bom.py) and [independent actual OEM 330bar per-cylinder 200bar screening](../src/ptxflex/f2_oem_PED_cylinder_200bar_sensitivity.py), with adversarial tests, passed independently authenticated CI.
- [PtXLens independent component-coverage and LCI-release gate](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/wp0-screening-core/src/ptxlens/f2_l1_stationary_bom_bridge.py) verifies source SHA, counts, EOS heel, pressure and omitted items; [separate OEM product check](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/wp0-screening-core/src/ptxlens/f2_l1_oem_PED_cylinder_bridge.py) rejects product substitution. **No native full 2026 BAFU LCI/TEA exists**.
- A non-binding [engineering RFI and evidence intake](F2_L1_STATIONARY_H2_VENDOR_RFI_AND_BOM_DATA_REQUIREMENTS_v1.md) lists every manufacturer datum needed to turn this concept into a source-signed BOM. It has **NOT been sent**; no company/site or procurement authority is represented.
- Original PyNEXUS historical E/E+S/A44 source archives live-verified currently available and due to expire **24 December 2026**; **private original archive recovery and independent backup remain P0 NOT PASSED**.

**F2/L1 subgate achieved:** independently reproducible candidate **empty vessel-equipment mass** and a **complete requirements-category scope** for a physically testable stationary H₂ storage design. **Full OEM-certified equipment BOM, installed capital, source-compatible manufacturing LCI, full native BAFU GWP, LCOH, P0 and v1.0 remain NOT PASSED**.

# F3-DESIGN-001 — Physically specified prospective H₂ service-restoration interface (v0.1)

**Programme:** OEM-PTX-2026-01 · **Scope owner:** PtXFlex (dispatch, engineering); PtXLens (LCA/TEA admissibility)  
**Evidence checkpoint:** 14 November 2026 · **Scientific status:** **PROSPECTIVE DESIGN BASIS, NOT A CONNECTED/QUALIFIED BACKUP PLANT**  
**Decision:** Screen a directly contracted, dedicated industrial hydrogen pipeline **if** a real connection and exit-flow guarantee are documented. Keep trucked gaseous H₂ and additional onsite generation as separate conditional alternatives. Do not merge v1.0 from this screening.

## 1. What problem is being solved

The source-locked historical PyNEXUS 2023 baseline contains **8,760 modelled hourly** prices/weather-derived wind and H₂ output, not actual plant telemetry. The original full demand was **18,250,000 kg**; the original E model delivered only **16,335,279.317 kg**, so there was already **1,914,720.683 kg** of original demand unmet before revising H₂ storage physics.

The F3 pressure-corrected Type I 200 bar, 313 K, 20 bar(a) minimum-delivery sensitivity shows:

| 20t E capacity semantics | Proven global minimum extra annual shortage, kg | A feasible but nonoptimal E dispatch extra shortage, kg | Peak incremental hourly replacement, kg/h | Largest 24-hour replacement, kg | Shortage hours |
|---|---:|---:|---:|---:|---:|
| **Gross max inventory** | 65,860.378–66,524.317 | 66,524.317 | 1,029.028 | 2,509.516 | 176 |
| **Usable mass above EOS heel** | 3,718.744–3,720.371 | 3,720.371 | 183.609 | 324.546 | 91 |

For 40t E+S the minimum additional shortage is **zero under both interpretations**, proven by independent 8,760-hour zero-shortfall physically screened dispatch. These sources are independently reconciled in [F3 exact-source register](../data/results/F3_2023_reconciled_research_evidence.json) (SHA-256 `5dead18cfa0c3fecf15562f423e01044bcc6ad4ba4f5212dfb44a010b0d1a0d3`) and the two immutable [backup-load summaries](../data/results/F3_2023_original_E_source_hypothetical_backup_max_inventory.json) and [usable-backup summary](../data/results/F3_2023_original_E_source_hypothetical_backup_usable_service.json).

**Goal of proposed interface:** provide top-up (b_t) at the **same delivery node and service specification**, such that original-source E dispatch (y_t^E + b_t = d_t^{E,mathrm{original delivered}}) for **every** 2023 hour. This is only a mathematical equality at present. It is not an actual supplied H₂ guarantee, and adding (b_t) does **not** restore the separate 18.25m-kg original contract.

## 2. Temporal and geographic scope — scientific control

**Do not backdate infrastructure:** commercial sources from **2026** describe possible future backup arrangements, whereas wind, market price and original modelled target service use **2023**. A supply route developed after 2023 is a **prospective counterfactual with replayed 2023 weather/price**, not a real 2023 operating installation. No site coordinates, nearest actual connection, offtake agreement, trading counterparty or construction/commissioning date has been established.

Gasunie publicly reported completion of the first 32 km Rotterdam national-network section on **20 May 2026** ([operator update](https://www.gasunie.nl/en/news/king-willem-alexander-and-minister-van-veldhoven-inaugurate-first-section-of-the-national-hydrogen-network)). This neither shows the unspecified PyNEXUS test plant is in Rotterdam nor guarantees any pipeline access. The actual access process includes expression of interest, a Connection Study Agreement and connection/investment agreements ([Hynetwork customer contracts](https://www.hynetwork.nl/en/contracts)); none is present.

## 3. Pressure boundary and product compatibility

**Original model inlet/outlet:** BAFU/PyNEXUS PEM source H₂ pressure **30 bar** (source treats absolute for screening) and a **20 bar(a) minimum pipeline-delivery gate** for the physical pressure-screened model. This is a **scenario assumption** about the output of PtXFlex, not a certified industrial pipeline connection or customer offtake contract.

The **2026 Hynetwork Transport Terms Annex 7**, version 2.0, **25 June 2026**, section 2, gives a 30–50 bar(g) temporary operational network pressure and potentially 46.2–66.2 bar(g) future regime, requiring connected-party pressure sufficient for **entry into the Hynetwork transport system**. **It does not promise a 30 bar(g) minimum at an arbitrary customer exit.** See [official Annex 7](https://www.hynetwork.nl/sites/hynetwork/files/2026-07/general-terms-and-conditions-transport-annex-7-pressure-specification.pdf), p.3.

The purely illustrative (p_{mathrm{abs}}=p_{mathrm{gauge}}+p_{mathrm{atmosphere}}) unit conversion gives 30 bar(g) + analyst-selected 1.01325 bar atmosphere = **31.01325 bar(a)**, nominally **11.01325 bar** above the 20 bar(a) delivery requirement. **This is NOT a pressure feasibility calculation:** no guaranteed customer exit pressure, pipe loss, pressure regulation differential, peak-flow hydraulics, temperature, failure mode or flow-meter loss exists. These values must remain `null` until source-validated; the 2026 network *entry* regime cannot be silently reused as customer supply.

For quality, the 2026 Hynetwork **Transport Annex 2**, section 2, requires gas at the network connection to comply with specifications established by the competent authority and amended subsequently; it does not establish a universal plant-end-use purity guarantee ([official Annex 2](https://www.hynetwork.nl/sites/hynetwork/files/2026-07/general-terms-and-conditions-transport-annex-2-quality-and-temperature-specifications.pdf), p.3). [ISO 14687:2025](https://www.iso.org/standard/82660.html) provides application-dependent hydrogen fuel specifications. The PtXFlex end use is not a qualified fuel-cell, combustion or chemical feedstock specification; **do not assert ISO Grade D, 99.5%, 99.97% or other purity as automatically satisfactory**. Obtain customer constituent limits (H₂ index and contaminants incl. O₂, H₂O, CO, CO₂, N₂/inerts, sulfur species), measurement method, sampling location, traceability and nonconformance disposition.

## 4. Three competing delivery concepts

### A. Contracted pipeline import with dedicated customer pressure/quality station — PRIMARY CONDITIONAL CONCEPT

At the real industrial site, require an actual operator and independently verified connected delivery point, hydraulic capacity, minimum exit pressure at peak duty, physical access date, guaranteed 2023 or prospective equivalent uptime and monthly/hourly nomination conditions. The **functional interface** is H₂ source/boundary → legally documented supply point → protected customer isolation → metering and filter/quality sampling → pressure control and relief/ESD → non-return and monitored delivery header → physical 20 bar(a) product node. Scope includes all balance-of-plant and external upstream production, transport, replacements and leakage.

Use [EIGA DOC 15/21, section 10](https://www.eiga.eu/uploads/documents/DOC015.pdf) for industrial gaseous consumer stations: isolation, pressure regulators, relief, indicator, non-return, purge and safety considerations. Apply local requirements, hazard identification and certified detailed engineering. [EU PED 2014/68/EU](https://single-market-economy.ec.europa.eu/sectors/pressure-equipment-and-gas-appliances/pressure-equipment-sector/pressure-equipment-directive_en) covers relevant stationary pressure equipment; [ASME B31.12-2023](https://www.asme.org/codes-standards/find-codes-standards/b31-12-hydrogen-piping-pipelines) is a hydrogen piping *engineering reference*, not a substitute for EU/Dutch conformity.

**Status:** physically relevant architecture class, **site-specific feasibility not demonstrated**, no industrial site and zero vendor quotation. Full 8,760-hour guaranteed delivery remains unknown.

### B. Compressed-gas tube-trailer delivery and local pressure-managed buffer — SECONDARY LOGISTICS CHECK

The [US DOE tube-trailer overview](https://www.energy.gov/cmei/fuels/hydrogen-tube-trailers) describes roughly **380 kg** traditional steel and **560–900 kg** composite H₂ nominal onboard payloads. These are **US-category reference capacities**, not a contractually available Netherlands fleet or usable withdrawal masses at 20 bar(a).

If every shipment delivered a hypothetical full **900 kg** (optimistic reference, excludes gas heel and loss), mathematical *payload equivalents*, **not dispatchable trucks**, would be:

| Gross/usable 20t E | Annual nominal 900kg-load equivalents | Largest 24-hour nominal-load equivalents | Peak single-hour nominal-load equivalents |
|---|---:|---:|---:|
| Gross maximum | 74 | 3 | 2 |
| Usable | 5 | 1 | 1 |

The gross case has 92 shortage events and up to 8 contiguous hours (usable case 87 events, up to 2 hours). Actual number of vehicles **cannot be inferred**: unloading duty, residual pressure, buffer capacity, deliveries while H₂ is consumed, truck turnaround, road capacity, maintenance, compressor/cooling, storage/pressure-vessel code and vendor supply are all missing. **At 1,029 kg/h peak, the nominal 900kg payload-equivalent calculation itself illustrates that a single 900kg trailer's total nominal gas inventory is insufficient to meet an entire such hour without other supply**. It does not say two trailers can physically deliver it in an hour.

### C. Independent supplementary electrolysis — UNMODELED ASSET AND GRID EXPANSION

An extra electrolyser is **not an emergency source "for free"**. The source model already includes a 125 MW PEM and constrained grid; any firm replacement H₂ made by additional PEM requires an independently permitted extra grid connection, firm energy, water, CAPEX/stack replacements, compression and cooling. No extra electrical service or physical buildout is sourced. Do not reuse the E/E+S original grid power or wind twice.

## 5. Functional engineering data contract (mandatory before a comparative run)

| Data item | Required engineering check | Current evidence |
|---|---|---|
| Site and source date | actual NL industrial coordinates, commissioning, supplier and 2023-vs-prospective classification | **Missing** |
| Same H₂ delivery | 8,760-hour source-identified (d_t), delivered (y_t), backup (b_t), (y_t+b_t=d_t), no double count | H₂ **top-up demand** only; not backup physical delivery |
| Product pressure | guaranteed exit min bar(a), regulator differential, pipe friction & peaks, trip pressures | **Missing**; 30–50 bar(g) refers network entry |
| Peak flow/buffer | ≥ applicable incumbent 1,029/184 kg/h plus documented variability/reserve, transporter/regulator/buffer curves | **Missing**; source top-up estimates only |
| Quality & custody | end-user composition limits, contamination, assay standard, fiscal metering, sampling | **Missing** |
| Availability | time-matched guaranteed source, outages, redundancy, startup, minimum take, nomination rules | **Missing** |
| Safety & materials | pipe metallurgy, fatigue/H₂ embrittlement, PED/ATEX, permitting, relief sizing, HAZOP, leak/protection design | **Missing** |
| Environment | independently sourced H₂ origin, upstream production, transmission, tank/BoP, electricity, losses, native LCIA supplier closure | **Missing** |
| Economics | source-backed CAPEX/OPEX, installed station, tariff, logistics, lifetime, price-year and EUR DCF | **Missing** |
| Review | independent technical and LCA checks, source rights, transparency and uncertainty | **Missing** |

Do not assign a null source cost, GWP, capex or delivery efficiency the number zero. For comparison, model the same product-gate boundary and backup burdens for each alternative, or explicitly choose and physically support a different common feasible demand. Preserve both the source-based "gross max" and "usable above heel" sensitivity interpretations; they are not the same installed equipment.

## 6. Acceptance and scientific decision

**Completed here:** (i) original modelled H₂ schedule source hash chain, (ii) literature/2026 operator source register, (iii) three separately bounded supply pathway screens, (iv) delivery pressure/quality/flow/service/temporal admissibility gates, (v) executable non-overclaim regression checks, (vi) source-limited 900kg payload-equivalent arithmetic. A [machine-checked JSON physical design basis](../src/ptxflex/f3_backup_route_screen.py) is generated in CI and mirrored to PtXLens only after verification.

**Not completed:** a site-specific contract, actual 2023 or later supply capacity at pressure and required hydrogen grade, real manufacturer bill of materials, indigenous delivered-H₂ LCIA, cost/CO₂ allocation, operational reliability, full industrial demand, source archival private escrow and independent critical review.

**Decision:** status **PROSPECTIVE_CANDIDATE_ONLY**, **F3 NOT PASSED**, **L1/L2/L3 NOT PASSED**, **full v1.0 release forbidden**. Next engineering experiment must use a sourced site-specific connection/producer and actual rated component/flow specifications. If none is obtainable, publish a transparent incomplete comparison / open functional-unit limitation rather than invented backup data.

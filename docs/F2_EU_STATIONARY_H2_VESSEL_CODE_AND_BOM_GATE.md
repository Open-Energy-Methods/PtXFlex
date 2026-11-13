# F2 — European stationary hydrogen pressure-vessel certification and BOM sourcing gate

**Programme:** OEM-PTX-2026-01 · ADR-004/F2 · researched 2026-11-13  
**Status:** DOCUMENTED ACCEPTANCE CRITERIA — NOT an approval, vendor certification or system-design safety case. No choice of reference Type I/II/III/IV vessel is approved for a real installation.

## Applicable scope is part of the engineering decision

**EU stationary pressure equipment:** The European Commission [Pressure Equipment Directive (2014/68/EU) guidance](https://single-market-economy.ec.europa.eu/sectors/pressure-equipment-and-gas-appliances/pressure-equipment-sector/pressure-equipment-directive_en) states PED applies to **stationary pressure equipment with maximum allowable pressure greater than 0.5 bar**. Its design, manufacture and conformity assessment are required according to the applicable scope/classification; the manufacturer/supplier must establish the correct assessment route, material compliance, notified-body requirements and documentation. The [consolidated Directive text (30 May 2026)](https://eur-lex.europa.eu/eli/dir/2014/68/2026-05-30) supports the requirements for conformity assessment, test and declarations.

**Gas cylinder material qualification:** [ISO 11114-4:2017](https://www.iso.org/standard/64587.html), also published in Sweden as [SS-EN ISO 11114-4:2017](https://www.sis.se/en/produkter/fluid-systems-and-components-for-general-use/fluid-storage-devices/unfired-pressure-vessels/sseniso1111442017/), describes *test methods for selecting steels resistant to hydrogen embrittlement* for **transportable seamless steel gas cylinders up to 3,000 litres**, with documented exclusions. It is **NOT itself a general code for all stationary Type I vessels**, nor a certificate for our hypothetical 1.8m³ reference cylinder. Its existence does not establish any assumed steel alloy, heat treatment, ultimate tensile strength, defect tolerance, fatigue life or hydrogen purity in our study.

### Source library and reported scope

The source geometry/masses used in [F2](F2_PUBLISHED_STORAGE_PRESSURE_SWING_AUDIT.md) and [F3](F3_2023_PHYSICAL_200BAR_FEASIBILITY_SOURCE_AUDIT.md) are from [Ademollo et al. stationary-hydrogen storage Table 2](https://doi.org/10.1016/j.ijhydene.2025.152849), not a supplier-qualified installation package. The adopted Type I reference has **1.8m³** gas volume, **2,400kg empty unit mass** and **200bar** nominal maximum pressure from that paper. Our hypothesis treats 200bar as *absolute* for CoolProp screening; paper rating/gauge reference and model boundary pressure are not verified. The original source PyNEXUS has 30bar PEM outlet and 20bar *pipeline minimum delivery*, but **no evidence** that a gas tank at 20bar absolute can hydraulically deliver 20bar downstream after frictional and valve pressure loss. Actual minimum tank pressure should be **higher** if such losses exist; no empirical pressure drop is established, so do not invent one.

## Mandatory sourced engineering/safety record before selecting a bank

| Review item | Required actual physical/source evidence | Present programme status |
|---|---|---|
| Application and regulatory classification | Stationary vs transportable service and PED/other applicable rules, manufacturer conformity declaration | **Missing** |
| Pressure basis | Bar gauge vs bar absolute for supplier rating and original process outlet; allowable pressure PS | **Unverified** |
| Temperature conditions | Min/max design temperature TS, filling/transient T, intercooler discharge, ambient/site envelope | **No year-resolved source** |
| Material/liner | Actual vessel steel/alloy and heat treatment, H₂ embrittlement/material approval, traceable test certificates | **Unknown** |
| Pressure cycling | Number/amplitude of fill cycles, fatigue/rupture requirements, inspection/NDT and warranted lifetime | **Unknown** |
| Actual vessel design | Supplier dimensions, free volume, thickness, installed empty/material mass and test pressure | **Reference paper only** |
| Safety components | Relief/vent arrangement, valves, manifolds, purge, instrumentation, leak detection, pressure isolation | **No equipment BOM** |
| Compressor/cooling | Model/vendor curves at pressure+flow+temperature, motor efficiency, interstage cooling power, auxiliaries | **RVO source screening only** |
| Delivery product gate | Pressure drop to offtake, guaranteed discharge pressure, purity/quality and hourly reliability | **Numerical source assumption only** |
| Total installation | Supports, civil works, piping, foundations, internal transport, installation losses, end-of-life route | **Missing** |
| LCIA compatibility | Actual BOM materials, source production supplier UUIDs, manufacturing emissions and lifetime/replacements | **Unverified native BAFU** |

**Source mismatch:** PtXLens original BAFU high-pressure tank provider (UUID \`b4739ad2-aa38-368d-8ada-63f5417c8b55\`) is a **composite vehicle tank per kg hydrogen capacity**, not a native climate characterization per 1kg of *empty stationary Type I steel vessel*. This remains a hard functional-unit / material-technology integration rejection.

## Scientific stop conditions

1. No vendor/type decision from Table 2 mass-to-H₂ ratio alone. Comparative pressure screens may be evaluated with source parameters, but they do not constitute a PED conformity assessment.
2. If the actual delivered H₂ pressure requires downstream 20bar, a storage bound set at exactly 20bar without pipeline/valve pressure drop is an **optimistic service-screening constraint**, not proof of physically adequate pressure margin.
3. No unverified material fractions or installed support/compressor mass assigned as zero or based on the old nominal 20/40t H₂ stock bound.
4. No dynamic compressor or storage performance claim from the RVO/LBST 80%/90% two-stage constant upper-pressure energy scenario alone.
5. No complete E/E+S TEA or cradle-to-gate native GWP until all major equipment/replacement material suppliers and operational energy are reconciled with a declared identical H₂ pressure/purity/reliability gate.

**Release sign-off:** a qualified pressure-equipment supplier/engineer must independently establish code conformity. The research model may be physically source-based and transparent without claiming to certify a particular plant; preserve that distinction at v1.0.

# F2 pressure-boundary qualification stop — 2026-11-14

Programme OEM-PTX-2026-01. **Status: engineering evidence gap, NOT_PASSED.** This is a release-blocking source-to-design checklist, not an approved design, plant measurement or vendor qualification.

## Independent boundary audit

The source model defines an illustrative isothermal H₂ storage swing of **20–200 bar absolute at 313 K**, electrolyser nominal output **30 bar**, customer nominal delivery **20 bar**, and an illustrative **2,200 kg/h** charge/discharge ceiling. The published Type I reference vessel and heiserTEC OEM products are **different equipment**. Their nominal pressure ratings cannot be interchanged or assumed absolute without original documentation. A static vessel pressure comparison alone does not establish the allowable working pressure of the assembled system.

| Physical boundary | Required primary evidence | Present status |
|---|---|---|
| Vessel pressure and temperature design | Exact OEM model/serial or traceable design family, MAWP/PS, design temperature range, gauge/absolute definition, PED conformity and hydrogen service | **Missing for the modelled installation** |
| Vessel cycling, fatigue and hydrogen compatibility | OEM cycle spectrum, material specification, hydrogen embrittlement/fatigue assessment, inspection interval | **Missing** |
| Compressor suction/discharge | OEM compressor map and hydrogen gas specification at 30-bar source, pressure losses, discharge maximum, start/stop and turndown | **Missing** |
| Interstage and aftercooling | OEM thermodynamic duty, temperature limits, cooling medium, transient temperatures and installed auxiliaries | **Missing** |
| Piping, valves and manifold | Pressure-segment-specific design ratings, line sizes, isolation/relief architecture, leak detection, P&ID and material certificates | **Missing** |
| Pressure reduction and customer interface | Documented 20-bar delivery requirement (absolute or gauge), purity, flow transients, regulation train, pressure losses and backup supply interface | **Missing** |
| Overpressure and abnormal operation | Independent hazard assessment, relief sizing, credible blocked-in/thermal expansion/compressor failure scenarios and emergency shutdown | **Missing** |
| Installed inventory and footprint | Manufacturer-approved rack/container count, weights, foundations, spacing, access and local permitting | **Missing** |

## Fail-closed acceptance sequence

1. Identify a single candidate *manufacturable* stationary bank, without substituting the literature Type I 1.8 m³/2400 kg vessel, 210-bar stationary COSMOS bundle, or distinct 330-bar 50 L cylinder for each other.
2. Obtain primary manufacturer documentation identifying pressure units and reference temperature. Convert gauge to absolute only with a documented ambient/reference pressure; do not silently compare gauge ratings to 200 bar(a).
3. Verify each component's design pressure and maximum/minimum operating temperatures against *its own* worst-case transient and fault envelope. Vessel PS >= nominal 200 bar(a) is **necessary at most**, not sufficient for conformity.
4. Check actual usable working capacity against residual withdrawal pressure with a documented EOS, site temperature envelope, regulator losses and unavailable reserve. Retain gross and usable inventory semantics separately.
5. Verify charging/discharging mass flow against real compressor curves, installed power/cooling, flow restrictions and customer purity/pressure requirements over the same 8,760-hour service.
6. Obtain manufacturer-approved complete installed equipment quantities and material/process manufacturing information before native BAFU matching. Record every missing component mass as **null**, not zero.
7. Require independent pressure-equipment and LCI review. Do not turn a passing mathematical screen or a supplier metadata checklist into a plant approval.

## Existing traceable sources and interpretation limits

- [European Commission Pressure Equipment Directive 2014/68/EU](https://single-market-economy.ec.europa.eu/sectors/pressure-equipment-and-gas-appliances/pressure-equipment-sector/pressure-equipment-directive_en) — regulatory context, not a certificate for this plant.
- [NEN-EN 17533:2025](https://www.nen.nl/en/nen-en-17533-2025-en-338598) — stationary cylinders/tubes; does not certify the complete manifold/pipe assembly.
- [heiserTEC Type I cylinder catalogue](https://www.heisertec.com/products/type-1/) and [stationary bundles](https://www.heisertec.com/products/bundles/) — distinct actual product classes, not interchangeable pressure or mass evidence.
- [International Journal of Hydrogen Energy Type I vessel reference, DOI 10.1016/j.ijhydene.2025.152849](https://doi.org/10.1016/j.ijhydene.2025.152849) — research geometry and dry equipment mass, not site-approved pressure equipment.
- [F2/L1 existing source audit](F2_L1_STATIONARY_TYPEI_INCREMENTAL_EQUIPMENT_SOURCE_AUDIT_v1.md) — the detailed original-source inventory semantics and null equipment ledger.

**Gate disposition:** F2 and L1 remain NOT_PASSED. No change to master plan, decision register, scientific gates, native LCA, costs, full-service claims or PR draft status is warranted by this checklist alone.

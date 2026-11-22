# F3-CONTRACT-002 — Supplier and Hynetwork **exit** interface: actual source gaps, 8,760-hour proof protocol

**Programme:** OEM-PTX-2026-01 · **Date:** 14 November 2026 · **Evidence class:** Original 2023 numerical H₂-model shortage + separately published 2026 operator/supplier references. **NOT a physical contract, real Netherlands project site, supplier guarantee or complete LCA/TEA.**

## 1. Source-location audit: offshore weather is not the industrial H₂ customer

The **original** [PyNEXUS 8,760-hour `configs/annual.yaml`](https://github.com/abhijith-sivaprasadan/PyNEXUS/blob/main/configs/annual.yaml) expressly labels its `location` coordinates **latitude 52.5, longitude 3.5** as approximately offshore North Sea, used for ERA5 **wind-resource data fetching**. They are *not* an industrial electrolyser site, a customer connection, or a physical hydrogen injection or exit point. The model provides a generic simplified pipeline from electrolyser to demand node and industrial flat demand; no verified Hynetwork customer site or geographic route exists. **Do not plot those weather coordinates as an actual hydrogen pipeline customer or infer branch proximity.** The correct real site field is `null`. The original 2023 full demand **18.250m kg** is distinct from its E-delivered **16.335279m kg** reference profile.

The 2026 Gasunie/Hynetwork newly commissioned 32km Rotterdam/Maasvlakte–Pernis corridor is a *future-prospective design route* relative to the 2023 model. [Gasunie 20 May 2026](https://www.gasunie.nl/en/news/king-willem-alexander-and-minister-van-veldhoven-inaugurate-first-section-of-the-national-hydrogen-network) confirms the network section, but it does not site or supply the model.

## 2. Two entirely different contracts are mandatory

**Contract A – actual H₂ network Exit / Transport Connection:** [Hynetwork Exit Terms v2.0 (25 June 2026)](https://www.hynetwork.nl/sites/hynetwork/files/2026-07/general-terms-and-conditions-connection-exit.pdf), **p. 4 clause 2.1.2**, explicitly says HNS neither produces nor procures gas and does **not** guarantee security of gas supply at customer connections. Clauses 4.1.1–4.1.4 (pp. 7–8) tie pressure/quality to actual Exit Annexes and allow connection closure near a lower operating threshold. The connected party needs the **signed Contract Data Sheet (CDS)**, actual connection point, service dates and agreed exit-pressure regime. A published generic HNS network pressure specification is not a guaranteed source pressure at the PtXFlex final product node.

**Contract B – commercially and technically separate H₂ molecule purchase / scheduling / shipping:** independently identify a producer/trader and shipper, offtake quality, output pressure and flow, hourly firm nominations, outage rights, available commissioning date, certificates, supply-origin LCA, tariff, losses and remedies. An HNS Connection Agreement alone **does not grant H₂ molecules**, nor prove that any merchant H₂ can be bought at the specified hour.

The applicable [Connection Exit **Annex 12**, p.3, section 3](https://www.hynetwork.nl/sites/hynetwork/files/2026-07/general-terms-and-conditions-connection-exit-annex-12-pressure-specification.pdf) describes **open-pipe delivery within current network operating pressure** or **reduced fixed-pressure exit** at a pressure explicitly stipulated in the **customer's Contract Data Sheet**. The 2026 temporary network operational envelope is **30–50 bar gauge**, with a possible future 46.2–66.2 bar(g). Neither the 30bar(g) network pressure nor the [**8bar delivery-pressure example** in Exit Annex 4](https://www.hynetwork.nl/sites/hynetwork/files/2026-07/general-terms-and-conditions-connection-exit-annex-4-pressure-safety-and-temperature-safety-example-8-bar-delivery-pressure.pdf) is the PtXFlex hypothetical customer's actual guaranteed delivery pressure. A connection explicitly rated below 20bar(a) cannot directly meet PtXFlex's 20bar(a) product-node requirement without additional sourced pressure-boost equipment. No site-specific booster is verified.

The official [Exit Annex 3, p.3](https://www.hynetwork.nl/sites/hynetwork/files/2026-07/general-terms-and-conditions-connection-exit-annex-3-quality-and-temperature-specifications.pdf) delegates connection-quality/temperature specifications to the competent authority; it is **not proof** that a given pipeline gas sample satisfies an undefined modelled industrial end use. Physical sampling/assay, contractual impurity limits and end-use supplier approvals are open.

## 3. Hynetwork's own connection-study unit requirement — no silent LHV/HHV error

The publicly available [Hynetwork Connection Study Agreement (CSA) **version 01.26, Annex A**, p.1](https://www.hynetwork.nl/media/t4xd5jjx/connection-study-agreement-template-v0126-with-1-signature-field.pdf) requests actual **entry/exit choice, industrial address/GPS coordinates, desired FID/ready-for-operation dates, and peak transport capacity (kWh/h)** for each planning year, beginning at 2028 in the template. It gives a reference higher heating value **12.74 MJ/Nm³** and hydrogen density **0.090 kg/Nm³** for 100% H₂.

```text
HHV [kWh/kg] = 12.74 MJ/Nm3 / (0.090 kg/Nm3 × 3.6 MJ/kWh)
             = 39.3209876543 kWh_HHV per kg_H2
E 20t gross source shortfall (one feasible modelled incumbent):
  1,029.02790279 kg/h × 39.3209876543 = 40,462.39346 kWh_HHV/h (~40.462 MW_HHV)
E 20t usable source shortfall (different sensitivity interpretation):
    183.60901389 kg/h × 39.3209876543 =  7,219.68777 kWh_HHV/h (~7.220 MW_HHV)
```

These are **incremental backup flow equivalents for two modelled E-incumbent H₂ shortage histories**. They are **NOT** (a) source equipment proof, (b) gas tariff, (c) enough capacity to cover the original full 18.25m-kg/year plant contract, or (d) necessarily the **total** capacity to put on an HNS CSA Annex A. For a **dedicated physically distinct backup-only exit**, an independently proved hourly peak plus appropriate contractual reserve and station hydraulics would form part of the new connection request. For a **combined industrial exit also carrying main production**, the CSA must request peak capacity of **the complete customer's connected exit service**—not just 1,029kg/h or 184kg/h.

Do not sign or submit the CSA on the basis of this hypothetical model: it is a binding study agreement that includes obligations and a conditional **EUR 150,000** study-cost guarantee (body p.2 clause 6). No operating legal entity/site and no user-approved financial commitment exist in this project.

## 4. What the published suppliers actually demonstrate, and do not

Public [Nobian/Air Products (26 Aug 2026)](https://www.nobian.com/news/nobian-and-air-products-sign-long-term-agreement-for-rfnbo-compliant-hydrogen) establishes an **actual long-term H₂ offtake agreement** and RFNBO-certified Rotterdam production, but neither company has offered PtXFlex a delivery contract, firm incremental H₂, a site-specific pressure, purity, price or allocated kg/h. The [Gasunie Holland Hydrogen 1 connection (16 March 2026)](https://www.gasunie.nl/en/news/first-major-hydrogen-plant-connected-to-dutch-hydrogen-network) establishes a **producer's network connection**, not a customer purchase agreement. The [Port of Rotterdam Air Products facility announcement (1 April 2026)](https://www.portofrotterdam.com/en/news-and-press-releases/major-progress-air-products-new-liquid-hydrogen-facility) describes a **future 2027** liquid-H₂ facility; it is not historical 2023 or operating 2026 delivery, and liquefied delivery carries its own capital/energy/transport burdens.

No actual supplier has been approached or qualified by this work. These market participants may inform future sourcing **only if** a real industrial location and end use are defined.

## 5. Verified source-reconstructed adequacy experiment — no fabricated delivery evidence

Actual original-2023 source-derived [gross 176 nonzero shortage hours](../data/results/F3_2023_original_E_sparse_H2_backup_need_max_inventory.json) and [usable 91 nonzero hours](../data/results/F3_2023_original_E_sparse_H2_backup_need_usable_service.json) are SHA-verified against historical Stage A and Stage B. Each source hour index is the model's **0-based sequential 8,760h index**; we do **not** silently assign observed local-clock timestamps across Amsterdam DST changes.

[Executable qualifying test](../src/ptxflex/f3_supplier_hourly_qualification.py) uses three independent 8,760-element nonnegative source-flow capacities (producer, shipper nomination, station outlet), 8,760 customer-header **absolute** pressures, and 8,760 Boolean vectors for acceptable H₂ quality and source/exit uptime. At hour `t`:

```text
adequate_pressure_t = (pressure_customer_header_abs_t >= 20 bar_abs)
qualified_flow_t  = min(supplier_t, transport_nominated_t, station_max_t)
delivered_t       = min(source_model_shortfall_t, qualified_flow_t)
                    ONLY IF adequate_pressure_t AND product_quality_accepted_t
                            AND supplier_and_exit_online_t; otherwise zero
unmet_t           = source_model_shortfall_t - delivered_t >= 0
sum_t[delivered_t + unmet_t] = source_model_annual_shortfall
```

This is a **no-buffer, no-ramp/linepack/pressure-hydraulics mathematical screen**, not an operating system design. It holds pressure as an explicitly independently supplied *customer-header* series; it never infers it from 30–50 bar(g) HNS network pressure. The five scripted **synthetic negative controls** demonstrate:
- **exact peak-flow / exactly 20bar(a) / perfect 8,760h uptime and always-good quality** gives mathematically zero additional shortage **but does not certify real source or plant**;
- **half of the source-incumbent peak firm-flow** fails during some shortage hours;
- **19bar(a) at the customer header** fails the 20bar(a) source-model delivery specification;
- **supply/connection shutdown at the single highest-shortage source hour** fails even with nominal peak capacity;
- **off-specification product quality at the highest-shortage hour** fails even if pressure and flow otherwise pass.

Results recorded in [source-HNS supplier negative control JSON](../data/results/F3_2023_shortage_2026_HNS_exit_and_supplier_boundary_control.json) (source-provenance, mathematical tests only) and [GitHub Actions verification workflow](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43577251078).

## 6. Exact external evidence needed to change state

**For source-backed site-specific technical readiness, acquire the following *separately*, via qualified counterparties, not from generic brochures:**

1. **Industrial site**: actual company/operator, operating plant vs proposed project, coordinates at the customer H₂ exit, source of process H₂ quality, permission to release data, commissioning year and 2023 historical vs 2026+ prospective scope.
2. **Network**: signed HNS Connection Exit Agreement + **customer CDS**, exit pressure and guaranteed pressure regime and customer pressure-safety architecture, historical/planned operational range, hourly nomination & meter capacity, location, route losses, cost/maintenance charges, access and outage/curtailment provisions.
3. **Supplier/shipper**: separately signed H₂ **molecule/shipper/nomination** agreement for that exact connected exit, firm capacity in kg/h or convertible HHV capacity, supplier delivery priority/interruptions, seasonality, quality/contaminant limits & assay, source-origin documentation and tariff.
4. **Station & hydraulics**: physically signed P&ID/BOM, pipe/valve/meter sizing and pressure-drop/temperature/pressure-regulator model at source-incumbent worst-hour and ramp, corrosion/H₂ fatigue and actual standard/authority compliance (EIGA, PED, appropriate NEN etc.), outage and redundancy; station state and usable buffer/linepack verified.
5. **Life cycle/economics**: source production route and verified marginal/attributional upstream H₂ LCI, source geographic mix, shipping losses, source manufacturer stationary H₂ equipment inventories, installed cost/connection fee/capacity tariff, fixed/variable OPEX and actual volume and currency year; independent native BAFU v1.1 inventories, detailed EUR DCF.
6. **Review**: date- and version-pinned supplier contract/source record with actual review signatures, lawful access, traceability, data uncertainty and external critical-review record.

**Release outcome:** Actual product-header `20bar(a)`, actual firm 8,760h supply and actual site are unverified. F3, P0, L1/L2/L3 and programme hydrogen/methanol release remain **NOT PASSED**. The source-based pressure/supplier tests do not change this. A source customer delivery site is the indispensable upstream missing datum; **we must not claim it can be obtained from a wind-resource location**.

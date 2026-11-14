# PtXFlex — weather/market-grounded PtX value-chain optimization research

## 14 November 2026 — F3-C **source-verified physically screened common H₂ service** (narrow operational milestone)

A new source-HASH-registered [F3-C hourly-service and pressure-MILP study](docs/F3_C_2023_PHYSICAL_COMMON_HOURLY_SERVICE_VERIFIED.md) reconstructs one **feasible, not globally minimum-shortfall** original 2023 E 20t Stage A additional H₂ shortage and subtracts it hour-by-hour from the 8,760h original PyNEXUS E-*delivered* H₂ reference. It then independently reoptimizes **both E20t and E+S40t** against the **identical** frozen hourly hydrogen service using original authenticated Dutch A44 prices/ERA5-derived wind, Type I source 200bar(a) real-gas heel, 20bar(a) product delivery minimum and RVO compressor electricity. All **four** original source full-year jobs passed the source SHA, independent H₂/electricity/pressure/terminal/cost audits and **1e-6 MILP gap** ([successful CI](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43580088115)). In the **gross-inventory** mode, each serves **16,268,755.001 kg H₂/year** and E+S has **€1,124,332.269 lower modelled 2023 NET WHOLESALE grid settlement** (solver-bound interval €1,124,318.034–€1,124,348.115). In the independent **usable-bank** interpretation, both serve **16,331,558.946 kg/year**, E+S is **€1,103,463.729** lower (interval €1,103,461.954–€1,103,474.625). These are **different hourly services**; do not compare their costs across modes. [PtXLens independently verified four source result fingerprints and paired cost bounds](https://github.com/Open-Energy-Methods/PtXLens/actions/runs/43580637209); [shared paired certificate](data/results/F3_C_2023_source_real_gas_equal_H2_hour_E_vs_ES_Lens_operational_bridge.json).

**Boundaries:** the same-hour target is sourced from a *feasible incumbent*, not the maximum deliverable source H₂; **neither case satisfies the original 18.25-million-kg industrial contract**. Larger storage may alter import/export timing but its manufacturing, compression station, cooling, labour, replacement, installed CAPEX and full native BAFU LCA/discounted lifetime EUR cost remain **absent**. This is **NOT LCOH, whole-system GWP, overall profitability, or a verified commercial plant**. Exact original provider data remain uncopied into the public research repositories. The [P0 original source private escrow protocol](docs/SOURCE_ESCROW_2023_PRIVATE.md) still requires actual private primary/independent recovery copies before original source Actions artifacts expire on **24 December 2026**. **No overall v1.0 release gates passed.**

---

## 14 November 2026 — source-verified F3 physical backup and 8,760-hour adequacy checkpoint

**Further verified industrial-interface correction (14 Nov):** [Original PyNEXUS annual config](https://github.com/abhijith-sivaprasadan/PyNEXUS/blob/main/configs/annual.yaml) gives 52.5°N,3.5°E for offshore **ERA5 wind weather**, **not** a hydrogen consumer or a pipeline exit site. [Hynetwork 2026 Exit Agreement](https://www.hynetwork.nl/sites/hynetwork/files/2026-07/general-terms-and-conditions-connection-exit.pdf) clause 2.1.2 confirms HNS does **not** produce/procure or guarantee delivered gas; separate **actual customer exit/CDS contract** and **supplier/shipper purchase contract** are needed. [Exit Annex 12](https://www.hynetwork.nl/sites/hynetwork/files/2026-07/general-terms-and-conditions-connection-exit-annex-12-pressure-specification.pdf) confirms the exit may have a reduced agreed delivery pressure; 30–50bar(g) network operation does not prove 20bar(a) at the customer H₂ header. [F3 dual-contract method](docs/F3_HNS_EXIT_AND_SUPPLIER_SEPARATE_CONTRACTS_v1.md), [operator/supplier source register](research/f3_h2_exit_and_supplier_source_evidence_v1.json) and [source-replayed 8,760h flow, pressure, quality and outage negative-control CI](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43577251078) are verified. Hynetwork's 2026 CSA HHV basis makes the **incremental** source-2023 backup peaks ~**40.46MW** (gross) or **7.22MW** (usable), **not** full customer exit-capacity bookings or true supplier offers. [Two non-binding enquiry drafts](docs/F3_TWO_CONTRACT_INFORMATIONAL_OUTREACH_DRAFT_v1.md) remain **unsent**.

**P0 live verification:** [direct GitHub source-artifact API status snapshot](research/P0_2023_PyNEXUS_original_actions_artifacts_live_status_2026-11-14.json) on 14 Nov confirms E, E+S and original A44 source ZIP records are **not expired**, but all are scheduled to expire **24 December 2026**, earliest original A44 **19:24:29 UTC**. There is **still no demonstrated lawful and independently restored private source escrow**; [source preservation protocol](docs/SOURCE_ESCROW_2023_PRIVATE.md). No v1.0 release gate passed.

**Scientific conclusion:** source-locked real-2023 weather/price and original *modelled* E-delivered H₂ reference (16,335,279.317 kg/year) were used to evaluate a real-gas Type I 200-bar pressure screen. The **E 20t bank** has rigorously **positive minimum additional shortage** relative to that hourly reference under both interpretations: gross inventory **65,860.378–66,524.317 kg**; usable stock **3,718.744–3,720.371 kg**. The **E+S 40t bank** has a verified zero-additional-shortfall hourly witness for both. Therefore the pressure-screened E and E+S operating cases do **not** provide matched hourly hydrogen service and do **not** support direct comparative cost or GWP claims.

**Actual hourly timing preserved:** [gross-capacity 176 nonzero source hours](data/results/F3_2023_original_E_sparse_H2_backup_need_max_inventory.json) and [usable-capacity 91 nonzero source hours](data/results/F3_2023_original_E_sparse_H2_backup_need_usable_service.json), independently reconstructed from SHA-verified historical 8,760-hour source outputs without publishing original wind/price records ([successful CI](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43575627251)). The corresponding hypothetical replacement flow needs for one feasible nonoptimal E dispatch are 66,524 kg/year and 1,029 kg/h peak gross; 3,720 kg/year and 184 kg/h peak usable. **These are not verified backup supply capacity or equipment ratings.**

**Prospective physical design evidence:** [scientific reference register](research/f3_backup_physical_source_register_v1.json), [original-source and 2026 supplier-network concept result](data/results/F3_2023_2026_prospective_h2_delivery_architecture.json), [engineering method and limitations](docs/F3_PROSPECTIVE_H2_BACKUP_SYSTEM_DESIGN_BASIS_v1.md), and [site/supplier/quality/cost request requirements](docs/F3_H2_SUPPLIER_SITE_CONNECTION_AND_BOM_RFI_v1.md). A contractual hydrogen pipeline with customer interface station is a **conditional candidate** only. Published 2026 Dutch network **entry** pressure is not guaranteed customer **exit** pressure, nor observed 2023 availability. Actual site, qualified product purity, firm flow, station BOM, full native LCIA and discounted EUR cost **are all unknown** ([physical-route CI passed](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43574828823)).

**P0 original source protection:** [private source escrow and second-copy recovery protocol](docs/SOURCE_ESCROW_2023_PRIVATE.md), with tested scripts for SHA/ZIP CRC and separate private devices. No actual user-specific second recovery copy, source-license approval or independent scientific signoff has been demonstrated. The exact **2026-12-24 artifact expiry is confirmed by live GitHub API metadata on 14 Nov 2026**; no actual private archive recovery has been demonstrated. **Research hydrogen/methanol v1.0 release gates remain NOT PASSED**; this feature PR remains DRAFT. See [machine scientific gates](research/gates-v1.0.json).

---

**F2→F3 physical pressure correction (source-locked 2023):** the new [Type I 200bar real-gas EOS/313K + RVO two-stage compressor full-year study](docs/F3_2023_PHYSICAL_200BAR_FEASIBILITY_SOURCE_AUDIT.md) found the original **E 20t** bank *infeasible* for the original E hour-by-hour delivery target under either max-inventory or physically usable interpretation, while **E+S 40t** met that modelled service in both screens. The previous ideal €1.142m operating-savings result is **not** a valid physically matched cost or GWP comparison. It is a pressure and compressor *screen*, not a dynamic certified plant. [F3 Stage A minimum additional H₂ shortfall workflow](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43515507811) has now been executed and source-verified; source unit/mass-matching to native BAFU remains incomplete.

### 13 November 2026: source-checked F2/F3 technical checkpoints

**Physical source correction:** The frozen PyNEXUS 20/40 tonne limits are **maximum ideal H₂ inventory**, not guaranteed usable H₂; pressure-swing heel must be accounted for. [F2 source-studied vessel/EOS working-volume table](docs/F2_PUBLISHED_STORAGE_PRESSURE_SWING_AUDIT.md) and [25 passing physics tests](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43502681218) compare actual published Type I/II/III/IV example vessel dimensions/masses. These are screening candidates, not actual certified plant hardware.

**Real 2023 full-year F3 pilot:** both independently solved HiGHS MILPs now deliver the **same H₂ amount in every 2023 hour**, fixed to original E-delivered model service (16.335279m kg). Net historical wholesale settlement **€25.7489m (E) vs €24.6070m (E+S)**, or ~€1.142m lower with ideal additional storage, MIP solver gap ≤10⁻⁶ and independently verified physical accounting. [F3 methods and limitations](docs/F3_2023_MATCHED_H2_IDEAL_PILOT_VERIFIED.md) · [machine-readable source result](data/results/F3_original2023_E_ES_ideal_matched_hourly_H2_annual_verified.json). **NOT** full 50t/day contract, pressure-limited storage, compression electricity, complete TEA, or environmental superiority. An actual manufacturer-matched physical BOM, plant losses, pressure-duty and PtXLens full LCA remain open.



## Coordinated scientific v1.0 — adopted research programme

**Start here:** [cross-repository v1.0 master plan](docs/PROGRAMME_MASTER_PLAN_v1.0.md) · [12 engineering decision records](docs/DECISION_REGISTER_v1.0.md) · [machine-readable release gates](research/gates-v1.0.json) · [strict shared exchange schema](contracts/ptx-exchange-v1.schema.json) (identical in PtXLens).

**Executed first-stage evidence:** [F1 source benchmark workflow](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43497912940) independently audited **17,520** frozen E/E+S original hourly PyNEXUS records with common 2023 wind, market price and H₂ demand sequences; both original solved cases have unmet demand and cannot be called matched service. [F2 CoolProp 8 physics workflow](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43498612013) verified real-gas density, usable storage *working volume*, isentropic H₂ compression and mass-balance equations (15 physics tests). Screening pressure points are *not* an approved physical tank specification and **do not include actual tank manufacturing mass**.

**Research scope gate:** PtXFlex owns source-verified physical hydrogen dispatch, storage thermodynamics, 8,760-hour matched-service optimization and a separately source-validated methanol subsystem. PtXLens owns the same-boundary physical equipment BOM, private licensed BAFU native LCA and full financial assessment. No real-data methanol LCA or complete E/E+S physical storage comparison exists yet. The original four-hour methanol MILP is synthetic verification **only**. [F2 equipment/pressure task](https://github.com/Open-Energy-Methods/PtXFlex/issues/4) · [F3 matched service task](https://github.com/Open-Energy-Methods/PtXFlex/issues/5).



**Status: genuine 2023 Netherlands wind and electricity-price inputs independently ingested; methanol-plant physics, hourly carbon data, and real-source optimized production remain unvalidated.**

## Real-source pipeline: executed successfully

Actual GitHub Actions workflow: https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43419654583

It retrieves the archived **original PyNEXUS 2023 E observed-market ZIP** from a registered GitHub Actions artifact, validates the full ZIP SHA256 and Stage B SHA256, and imports **8760 annual hourly** wind availability and Dutch day-ahead market price records. Data are derived from ERA5 wind and observed original 2023 Dutch ENTSO-E A44 prices. They are **not** measurements from an operating methanol plant.

~~~bash
python -m pip install -e ".[dev]"
python -m pytest -q

# Use authentic original ZIP from frozen PyNEXUS evidence artifact 12612294862
ptxflex /path/to/pynexus-original-E-2023.zip \
  --import-pynexus-2023-e \
  --output outputs/real_inputs/nl_market_wind_2023.json
~~~

The import intentionally records hourly grid/wind GWP as **null**, never invented or derived from the price. It explicitly sets solver_ready=false until environmental factors and methanol process assumptions are sourced and validated.

## Separate mathematical MILP proof of concept

The original SciPy/HiGHS optimizer models wind/grid/electrolyser conversion, H2 storage, CO2 availability, ideal methanol reaction, synthesis min load/commitment, ramping and an optional operational-emissions constraint for a fixed methanol delivery target. It independently checks all modeled energy/mass/stoichiometric and cost/impact constraints. The only runnable emissions-constrained example currently uses **fabricated four-hour numeric fixtures for testing the mathematics**, **not scientific findings**.

~~~bash
ptxflex examples/illustrative_methanol.json
ptxflex examples/illustrative_methanol.json --emissions-cap-kgco2e 200
~~~

**Do not confuse tests with a grounded Power-to-X process study.** The methanol pathway still lacks sourced commercial chemistry conversion, recycle, separations, reactor heat, compression, auxiliary loads, validated CO2 supply/fate, realistic storage design, capacity sizing and properly scoped life-cycle impact.

The route to credible 2023 real-input optimization requires a compatible source-verified hourly grid GWP inventory, source-verified reactor/synthesis constraints, documented methanol plant energy and CAPEX, a product-gate specification and subsequent actual LCIA. No negative carbon credit from CO2 incorporation is assumed without sourcing the CO2 origin and end-use. Avoid name-dropping Aspen or treating this as vendor-calibrated.

Upstream evidence: https://github.com/abhijith-sivaprasadan/PyNEXUS (frozen Oct 2026); linked economic/LCA research: https://github.com/Open-Energy-Methods/PtXLens .

The source and MILP development are AI-assisted research software requiring independent scientific review. No plant-validated or ISO 14044-compliant results claimed.

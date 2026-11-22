# L3-A — PtXFlex original 2023 same-hour H2 operating economics source handoff to PtXLens

**Programme:** OEM-PTX-2026-01 · 14 November 2026 · **Purpose:** source-hash audited **original 2023 modelled net WHOLESALE grid settlement** from physically screened E20t vs E+S40t at the same 8,760-hour hydrogen service for each separate pressure-vessel capacity semantics.

**Scientific status:** historical-model operating-cost input **VERIFIED**; site-specific storage plant, customer demand, pressure-rated manufacturer design, real future market savings, actual equipment CAPEX/OPEX, tax and financing, full EUR hydrogen LCOH and native BAFU greenhouse-gas assessment **NOT VERIFIED**.

## 1. Frozen source-2023 physical and financial evidence

The original PyNEXUS 2023 E+E/S source ZIP and Stage A E physically feasible hourly target have original SHA-locked weather, day-ahead NL A44 wholesale electricity and hydrogen production. [F3-C completed source-matched service engineering study](F3_C_2023_PHYSICAL_COMMON_HOURLY_SERVICE_VERIFIED.md) independently re-optimizes source physical E20t/E+S40t for **exactly the same every-hour reduced hydrogen service** within each of two inventory modes (gross stock upper bound versus alternatively defined withdrawable usable capacity). Both 2023 source cases include a 313 K Type I 200bar(a) real-gas EOS screen and compressor electricity (not OEM data), and source operating costs pass independent 8,760-hour mass/energy/cost audit and 1e-6 relative HiGHS MIP gap. Original full 18.25 million kg industrial H₂ obligation **not met**, and the source E feasible Stage-A shortfall used to form each common hourly service is **not proven globally minimum**.

| Source 2023 operating/equipment reference | Gross bank capacity interpretation | Usable bank capacity interpretation |
|---|---:|---:|
| E/E+S identical every-hour delivered H₂ service (annual kg) | **16,268,755.001** | **16,331,558.946** |
| Original 18.25m kg industrial contract remaining unmet (kg/yr) | 1,981,244.999 | 1,918,441.054 |
| Original E−E+S net wholesale electricity saving EUR2023/yr | **€1,124,332.269** | **€1,103,463.729** |
| Original 2023 HiGHS deterministic annual saving interval EUR | [1,124,318.034; 1,124,348.115] | [1,103,461.954; 1,103,474.625] |
| F2 313 K 20→200bar(a) Type I paper ref extra vessels | 802 × 2,400kg empty equipment | 902 × 2,400kg empty equipment |
| Additional empty **REFERENCE** vessel equipment, not virgin steel | **1,924,800 kg** | **2,164,800 kg** |
| Quoted, fully installed marginal H₂ storage CAPEX or true OPEX | **NULL** | **NULL** |
| Actual plant lifetime, replacement events, insurance, taxes and finance | **NULL** | **NULL** |

**No comparison across these two rows as if they provided one common hourly H₂ product:** the pressure/capacity semantics yield different annual H₂ and hourly functional units. [Full F2/L1 manufacturer-source audit and 19 equipment categories](F2_L1_STATIONARY_TYPEI_INCREMENTAL_EQUIPMENT_SOURCE_AUDIT_v1.md) documents 18 missing equipment masses and a separate incompatible 330bar OEM PED cylinder source. The empty paper vessels are not steel LCI/exchange quantities, vendor installation or price.

## 2. Exact export contract and reproducible tests

The [identical 2023 L3-A original-source exchange manifest](../research/L3_A_2023_source_locked_incremental_wholesale_DCF_handoff_v1.json) is mirrored in both repositories. It freezes actual 2023 source E/E+S ZIP hashes; F3-C 2023 common-hourly operational source SHA `dddd07d5c0a3d4f276e80af44e28cf3cfdbc93421107fb5d9e39843a0d1d90e2` and F2 Type I hardware reference SHA `1315d1181b9d1eab6d3368425c9571dbe295c3360935d2972403bf3c60e2dc47`; permitted real 2023 EUR interpretation; two distinct inventory modes; and analyst hypothetical rates/durations/discount/savings-persistence and extra OPEX assumptions. It **does not contain or invent any vendor prices**.

[PtXFlex handoff engine](../src/ptxflex/l3a_source_wholesale_economics_handoff.py) byte-verifies the source F3C/F2 and source manifest, checks exact 2023 8,760h H₂ SHA, 2023 HiGHS lower/upper saving interval, 313K reference shell count/mass and missing station cost/GWP status. [Negative source and financial impersonation tests](../tests/test_l3a_source_wholesale_economics_handoff.py) reject changed original source hashes, misclassified 2023 H₂ service or fabricated actual CAPEX/OPEX. [Source handoff successful CI](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43587841285).

**Canonical byte-frozen result:** [`data/results/L3_A_PtXFlex_2023_source_hourly_equal_service_wholesale_only_financial_handoff.json`](../data/results/L3_A_PtXFlex_2023_source_hourly_equal_service_wholesale_only_financial_handoff.json), SHA `0de22f7ff566dc50101b085366e47ef9965d545dca1dfa9bca3dd6d115274829`, independently preserved in **both repos**.

## 3. Downstream PtXLens L3-A work executed

[PtXLens fully documented reproducible methodology and four scenario figures](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/wp0-screening-core/docs/L3_A_2023_MATCHED_SERVICE_WHOLESALE_DCF_BREAKEVEN_METHODS_RESULTS_v1.md) consumes the source SHA without treating it as full project economics. Its [source-registered pre-tax, unlevered incremental DCF](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/wp0-screening-core/src/ptxlens/l3a_source_wholesale_dcf.py) computes **conditional** incremental all-in installed CAPEX and additional annual OPEX break-even thresholds:

```text
incremental NPV = - C0
  + Σ(t=1..N) [future_factor_t × source_2023_wholesale_saving - extra_OPEX_t - replacements_t] / (1+real_discount_rate)^t
  + [terminal_salvage - terminal_decommission] / (1+real_discount_rate)^N.
```

*Only* this purely hypothetical interpretation permits calculation before manufacturer equipment prices are obtained: **20 years, 8% real discount, repeating the 2023 modelled difference each year, zero extra OPEX/replacements, gives a mathematical CAPEX ceiling €11.03886m gross or €10.83397m usable**; with **illustrative** €250k/year extra OPEX and €1m replacement at year 10, €8.12113m gross or €7.91624m usable. Neither is real installed investment cost, actual net project NPV, calculated LCOH or forecast electricity savings. Full 2023 original contract remains unmet; 2023 future price and site unknown.

**Output and verification:** [full source scenario threshold grid and year-by-year cash flows, SHA `142a1eac...`](../data/results/L3_A_2023_matched_hour_source_only_wholesale_savings_DCF_CAPEX_OPEX_frontiers_NOT_full_LCOH.json), [compact cross-repo summary, SHA `89a10d1f...`](../data/results/L3_A_2023_same_service_2023_wholesale_DCF_break_even_summary_NOT_final_project.json), [PtXLens scientific CI with four original vector SVG/PNG sensitivity figures](https://github.com/Open-Energy-Methods/PtXLens/actions/runs/43587771649) and independently repeated original SVG hash verification in the second run.

**Conclusion:** L3-A conditional **2023 net wholesale-grid DCF threshold** maths, source F2/F3 fingerprints, independent 2023 EUR financial-unit/year indexing and visual sensitivity **VERIFIED as a limited numerical subgate**. P0 source private escrow, physically complete manufacturer incremental storage and all-in installed expense, source-correct full lifecycle climate, whole-plant H₂ selling-price/cash-flow model, full original H₂ demand, F3-D multiple-year operational uncertainty and independent critical review remain unresolved. **PtXFlex and PtXLens PRs remain DRAFT; no L3 full or hydrogen/methanol v1.0 release.**

# F3 numerical checkpoint — source-locked 2023 E/E+S exact hourly hydrogen service, *ideal storage only*

**Programme:** OEM-PTX-2026-01 · F3 part 1 / controlled operating benchmark  
**Execution:** [2023 original-source 8,760 h E + 8,760 h E+S HiGHS workflow](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43505154927)  
**Status:** genuine, solver-verified and independently mass/energy audited **matched-delivery IDEAL-STOCK model**. Physical pressure-limited usable capacity, compressors and tank-embedded LCA **not yet verified**. Therefore this does NOT close the F3 / L1 / L2 / L3 / X1 scientific v1.0 gates.

## 1. Why this comparison is different from the original E/E+S results

The frozen source originally delivered E = **16,335,279.317 kg H₂** and E+S = **16,679,072.088 kg H₂** from the same hourly wind/price input and demand. Its original wholesale grid settlement was E **€25.749 million** and E+S **€27.508 million**, but the extra E+S H₂ service makes direct cost/GWP comparison misleading.

The new comparator fixes **the entire E original 8,760-hour delivered-H₂ trajectory** (not merely annual total) as the common service, and independently re-optimizes both 20,000 and 40,000 kg original source model *maximum storage stock* cases. This reference profile inherits the original E shortfall of **1,914,720.683 kg** below 18,250,000 kg nominal 50,000 kg/day demand; it is not the equivalent of supplying the full industrial contract.

Source originals are untouched:
- E original source ZIP SHA256 \`069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051\`;
- E+S original ZIP SHA256 \`cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9\`;
- each has 8,760 original Stage B rows and registered 2023 NL A44 market input/ERA5 wind; independent input-price/wind/demand sequence hashes are identical.

The source is **real observed price + weather/reanalysis-derived wind and solved hydrogen model**, NOT measured wind farm and hydrogen plant performance.

## 2. Mathematical model / fixed common boundary

A new independently implemented SciPy/HiGHS mixed-integer model is used to avoid simply copying the old PyNEXUS solver's output. Every hour \(t\) has PEM electrical load \(P_t\), binary on/off \(u_t\), signed net grid exchange \(G_t\) (positive import, negative export), wind curtailment \(C_t\), tank stock \(S_t\), charging \(H^{\mathrm{in}}_t\), discharging \(H^{\mathrm{out}}_t\), and exclusive charge/discharge binary \(z_t\). **All source plant bounds** are read from verified original PyNEXUS config and record, not silently overridden.

- Electricity: \(P_t+C_t-G_t=W^{\mathrm{available}}_t\), \(-50\le G_t\le50\) MW, \(0\le C_t\le W_t\), no simultaneous import/export because signed net grid.
- Source PEM: \(12.5u_t\le P_t\le125u_t\) MW, \(|P_t-P_{t-1}|\le50\) MW per hour; source linear H₂ yield **21.086108610861086 kg/MWh**. This is *an original simplified model parameter*.
- **Exact hourly service:** \(yP_t-H_t^{\mathrm{in}}+H_t^{\mathrm{out}}=H^{\mathrm{delivered,E\,original}}_t\).
- Stored H₂: \(S_t=(1-0.0001)S_{t-1}+H_t^{\mathrm{in}}-H_t^{\mathrm{out}}\), 0 ≤ stock ≤ **20,000(E) or 40,000(E+S)** kg, charge/discharge ≤2,200 kg/h each with exclusive mode, starting 10,000 kg and **ending exactly 10,000 kg**.
- Objective: minimize 2023 observed day-ahead net wholesale grid-settlement cost \(\sum_t \pi_t G_t\). No avoided GHG export credit, no invented fixed/variable equipment cost or vendor price.

Note: this model deliberately does **not** convert stock into true pressure-limited working capacity; it omits compressor and cooling electrical energy and all installed equipment manufacturing. That is why it is labeled *ideal*.

## 3. Executed results (actual 8,760-hour original model inputs)

| Independently audited indicator | E 20t max stock | E+S 40t max stock |
|---|---:|---:|
| Exactly identical delivered H₂ (kg, 2023) | **16,335,279.317** | **16,335,279.317** |
| Verified HiGHS MIP relative gap | **2.83×10⁻⁷** | **7.28×10⁻⁸** |
| Net wholesale settlement (EUR2023) | **25,748,907.19** | **24,606,993.56** |
| Solver dual/best bound (EUR2023) | 25,748,899.91 | 24,606,991.77 |
| PEM input (MWh) | 774,961.328 | 775,303.966 |
| Net physical grid imports (MWh) | 298,721.877 | 287,082.657 |
| Net physical grid exports (MWh) | 36,320.066 | 24,331.100 |
| H₂ produced (kg) | 16,340,918.726 | 16,348,143.638 |
| Original *assumed* storage loss (kg/year) | 5,639.408 | 12,864.321 |
| Max model H₂ stock utilized (kg) | 20,000 | 40,000 |

**E+S net wholesale settlement is €1,141,913.63 lower** at the identical H₂ service in the source **ideal-storage** model. The separate solver best-bound results place the numerical optimal saving within **€1,141,906.34 to €1,141,915.42**, before physical/system uncertainties.

**This is NOT overall economic or environmental superiority.** The larger tank incurs additional source-hypothesized stock loss (+7,224.91 kg H₂/year), compressor energy if higher storage pressure, a substantial vessel mass and lifetime burden, and additional installed cost. Those are not modelled here. The model's hourly target is already short of the original full 50t/day demand.

The original E solver wholesale objective is ~€25,748,968.93, and the new independently solved equal-service E is ~€25,748,907.19; close accounting consistency is encouraging, but the two MILP formulations have different grid-exclusivity/stock/target objectives and cannot be described as exact variable-level solver reproduction.

**Wind electricity allocation:** noncurtailed wind includes wind exports. The source model now separately reports wind consumed by PEM = PEM electricity minus positive grid imports, versus wind exported; this correction prevents overstating renewable electricity used by electrolysis.

## 4. Validation and interpretation gates

- [x] Frozen source archive SHA, E and E+S 8,760 row counts, annual delivered profile, original config and exact common wind/price/demand inputs confirmed before solving.
- [x] Distinct MILP built with on/off binary, ramp, source H₂ conversion, single net grid exchange, storage binary exclusive charge/discharge, original leak and terminal-stock state.
- [x] Both full-year HiGHS solvers optimal within preregistered ≤10⁻⁶ MIP relative gap, dual/best bounds captured.
- [x] Hourly independent reconstruction of electricity, delivery, gas stock and price objective; worst numerical residual ~6.1×10⁻¹¹ kg for storage and ~3×10⁻⁸ EUR for objective. All source capacity, grid and ramp constraints hold.
- [x] No invented hourly wind, price, grid marginal carbon intensity, vendor tank design, CO₂ feed, plant manufacturing GWP or upstream plant measurement.
- [ ] **F2 physical pressure mapping:** original model stock can be discharged toward zero although a pressure system needs heel gas. Replace source stock bounds with actual *working* mass as a function of pressure/temperature and design vessel volume, and integrate true compressor electricity/cooling/loss.
- [ ] **F3 production service:** report fixed site/contract 50t/day feasibility and compare identical site gate pressure/purity/reliability or document common external backstop; benchmark E-original delivered profile alone is not full contractual parity.
- [ ] **PtXLens native source-backed L1/L2 equipment LCIA and L3 DCF:** fix actual physical bank BOM and stationary tank supplier technology; native E/E+S GWP and full LCOH need separate full equipment/energy accounting.
- [ ] Add environmental attributional/sensitivity comparison only after actually linked BAFU storage manufacturing and matched physical service; never assign missing impacts zero.

**Primary result:** a reproducible, independent **matched-hourly-H₂ ideal operating benchmark** with a bounded wholesale dispatch saving, not a full validated industrial optimized hydrogen system.

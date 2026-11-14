# F3 Stage B — source-verified 2023 hourly H2 backup-load envelope

**Programme:** OEM-PTX-2026-01 · **Scientific date:** 14 November 2026.
**Evidence level:** Source-locked numerical optimization and analytical postprocessing; **not** measured H2, physically installed backup, complete lifecycle assessment, or formal design approval.

## Research question and precise boundary

The 2023 PyNEXUS E original model served **16,335,279.317 kg H2** against its **18,250,000 kg** original annual demand. Stage A imposed the original **hourly E-delivered schedule** identically on pressure-screened E and E+S with CoolProp real-gas mass heel and an RVO/LBST charging-compressor energy screen.

The 20t E pressure cases cannot meet that same-hour service; 40t E+S can meet it (verified twice by an independent zero-shortfall witness). This makes a direct lifecycle comparative cost or GWP result **inadmissible**.

Stage B asks a narrower and verifiable mathematical question:

> For each *feasible* but nonoptimal Stage A E 20t dispatch with documented hourly additional shortages, what hypothetical source-index hourly hydrogen quantity must an **external delivery-node top-up** provide to reproduce the original E-delivered 2023 hourly profile?

This stage does **not** model or source the backup technology, upstream source mix, compression, purity, delivery gate compliance, transmission, 2023 availability, backup cost or life-cycle impacts. No annual GWP or LCOH can be computed legitimately yet.

## Source and fingerprint chain

- Frozen original source model ZIP SHA E: `069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051`
- Frozen original source E+S ZIP SHA: `cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9`
- Independent six-artifact F3 reconciliation result SHA:
  `5dead18cfa0c3fecf15562f423e01044bcc6ad4ba4f5212dfb44a010b0d1a0d3`
- [Source E pressure shortage artifact certification](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43524738270); source archive ZIP digests are separately pinned.
- [Executed Stage B hourly-source workflow](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43527327817).
- Mode `max_inventory` output SHA:
  `c65fda894ef4b30e09339ad88a3972625af78c17802fd0cb9a2fc25d3205882f`.
- Mode `usable_service` output SHA:
  `d893c6388f14d276b2ef5d4bff4b6c8057dd252067f307f83b9baafcfa1e5308`.

The action verifies SHA-256 of the *source artifact ZIP*, reads all 8,760 source-derived hourly shortage values, checks their sum against the **independently certified Stage A feasible-incumbent** quantity (tolerance 2e-4 kg), verifies shortfall hour count, and measures hourly/24-hour extremes and interruption runs. CI prohibits corrupt or missing source/service/physics claims and overwriting existing outputs. **The source analyses use 2023 Dutch market/weather inputs but hydrogen production and delivery are model results, not actual operating telemetry.**

## Quantitative results

| Source bank interpretation | Source E Stage A optimal deficit lower bound (kg H2) | Feasible incumbent top-up (kg/year) | Max hourly load (kg/h) | Largest rolling 24 h requirement (kg) | Positive shortage hours | Number of distinct runs | Longest run (hours) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 20t **gross maximum gas inventory** | 65,860.378 | **66,524.317** | **1,029.028** | 2,509.516 | 176 | 92 | 8 |
| 20t **usable H2 mass above real-gas heel** | 3,718.744 | **3,720.371** | **183.609** | 324.546 | 91 | 87 | 2 |

All values refer to **additional shortage against the original E-*delivered* profile** under the two specified physical storage models. None is a minimum backup plant rating; only the Stage A certified annual lower bound gives a rigorous minimum cumulative shortage statement. Hourly peaks belong to a particular feasible dispatch and may change under reoptimization with a real backup device, supply cost, and equipment constraints.

The difference in two modes reflects physically different equipment capacity and source inventory semantics; this is a sensitivity result, **not a controlled cost-saving causal estimate**. The original 1.9147 million kg original-model service gap remains even if these *additional* deficits were hypothetically topped up.

## Source-preserving equations

Let `D_E[t]` be original frozen E **modelled delivered H2** [kg/h], `Y_E[t]` be new source-pressure-screened E delivered H2 in a feasible Stage A MILP schedule, and `q_backup[t]` the mathematical shortfall:

```
q_backup[t] = D_E[t] - Y_E[t] >= 0  (8760 original source hourly indices)
Y_E[t] + q_backup[t] = D_E[t]       (mathematical hourly equivalence)
sum(q_backup) = annual shortage of one feasible Stage A incumbent
L_H2 <= min(feasible annual shortage) <= sum(q_backup)
```

The top-up equality is an **identity**, not a demonstrated source of physically available, compressible, delivered H2. There is no measured hydrogen, no verified backup system, and therefore **no valid matched-service cradle-to-gate GWP or EUR discounted cash flow yet**.

## Gate to enable a proper matched-service comparison

1. **Backup product:** specify source technology (e.g. contracted on-site/off-site H2), source country, eligible supply year, production/transfer pressure and hydrogen purity, delivery pipeline/interface, guaranteed flow and availability, storage upstream of the delivery node, and time-resolved profile. Do not silently assume the 20bar source pipeline pressure is delivered by an unspecified supplier.
2. **Physical equality:** prove a full 8760h unified dispatch with the backup option explicitly modelled for both alternatives or verify an independently sourced, equivalent alternative reduced-service schedule. Include compressor duty/coolers, storage pressure dynamics, leakage, standstill/restart, purity and quality.
3. **Data quality:** source full manufacturing/infrastructure/transport/replacement inventory, independent provider links in actual BAFU v1.1 openLCA and original electricity sourcing method; do not substitute original incompatible vehicle composite tank providers for Type I steel.
4. **Economic:** real price-year/FX and source capital/variable backup cost, full installed BoP CAPEX, OPEX, grid tariffs/contracts, lifetime and discount rate, separate energy/opportunity cost; no shortcut from net wholesale electricity settlement to plant LCOH.
5. **Comparison/robustness:** same annual and hourly H2 service, pressure and purity, source-pinned GWP method and DCF with uncertainty and independent critical review; no industrial installation claim.

**Status:** This is an F3 **source-backed backup-service requirement** milestone, not completed F2/L1/L2/L3, not completed comparison, and not v1.0.


## 14 November 2026 — additional source-hourly supply-duty audit (pending rerun)

The Stage B code now computes independent, sliding **1, 6, 24, 72 and 168 consecutive-hour** sums, their first peak 0-indexed source-hour locations, associated average supply flows, and within-year maximum positive/negative adjacent-hour changes. These are deterministic calculations on the same authenticated 8,760-hour source-modelled shortage trace. The implementation checks prefix-sum windows against independent direct convolutions, checks annual mass closure, and explicitly excludes any presumed year-boundary startup/shutdown ramps. No calendar-day approximation is substituted for a rolling 24-hour maximum.

**Interpretation:** The hourly peak and maximum adjacent-hour ramp are required to follow *that specific Stage A feasible-incumbent profile without an upstream buffer*. They are **not** global lower bounds on any supplier rating: a co-optimized backup, an upstream buffer or a different feasible electrolyser dispatch could change the profile. Rolling-window average flows similarly describe that fixed schedule, not a certified equipment design. An externally sourced supplier's 20 bar absolute pressure, purity, deliverability, reserve, transport and emissions remain unknown.

**Verification status:** The new source-pinned Stage B workflow must pass against both existing SHA-verified Stage A artifacts before the new window/ramp values can be reported as original-2023-derived numerical evidence. The earlier published annual/peak-hour findings are not replaced or revised by synthetic tests. Neither F3 nor the full v1.0 scientific gate is passed by this increment.

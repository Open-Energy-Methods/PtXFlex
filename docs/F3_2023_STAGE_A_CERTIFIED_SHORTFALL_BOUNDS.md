# F3 Stage A: source-locked shortage certification and solver reconciliation

**Programme:** OEM-PTX-2026-01 · **Checkpoint:** 2026-11-14 · **Release decision:** OPEN / NOT v1.0.

## 1. Exactly what Stage A measures

The 2023 Netherlands electricity prices and weather-to-wind profile are frozen in the
original PyNEXUS ZIPs (E SHA256 `069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051`;
E+S SHA256 `cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9`).

- **Actual historical input:** price and ERA5-derived wind availability (not metered H2).
- **Original full model demand:** 18,250,000 kg H2 for 8,760 hours.
- **Matched reference target:** 16,335,279.317 kg H2, the original model's hourly E-delivered schedule.
- **Pre-existing demand gap:** approximately 1,914,720.683 kg, before any additional pressure-screened inadequacy.
- **Hardware screen:** published Type I 200 bar reference vessels, constant 313 K,
  20 bar minimum pressure, real-gas EOS heel and charging-compressor electricity.
  Pressure gauge/absolute interpretation, equipment manufacturing and operating
  validation remain unresolved. See
  [F2/F3 physical screen](F3_2023_PHYSICAL_200BAR_FEASIBILITY_SOURCE_AUDIT.md).

Stage A minimizes **additional** shortage against that common *modelled* historical
E-delivered profile. It never claims to satisfy the full 18.25m-kg original contract.

## 2. Observed previous Stage A solver incumbents (13 November 2026)

[Real-source workflow and logs](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43518281116).

| 200 bar reference capacity semantics | E (20t) achieved extra shortage (kg) | E+S (40t) achieved extra shortage (kg) |
|---|---:|---:|
| Gross maximum inventory | 66,524.317 | 2,307.413 |
| Usable mass above EOS heel | 3,720.371 | 0.000 |

**Do not call the positive numbers proven minimum shortfalls.** The solver returned
feasible incumbents without a certified tight gap for three of the four runs.
A known feasible dispatch with positive shortage provides an **upper** bound on
minimum additional unserved H2, not proof of unavoidable inadequacy.
For the 40t-usable zero-shortfall case, nonnegative shortage proves zero is the
minimum, irrespective of which objective bound method was used.

In particular, the earlier
[pressure-screened matched-service study](F3_2023_PHYSICAL_200BAR_FEASIBILITY_SOURCE_AUDIT.md)
verified **zero-shortfall feasible** E+S full-service dispatch for both 40t
interpretations. That is incompatible with *interpreting* the later 2,307.413 kg
gross-inventory Stage A incumbent as an unavoidable deficit. These solver results
must be reconciled against identical demand, plant equations, tank capacity
semantics, source hashes, and pressure audits. Do **not** infer infeasibility of E+S
from that incumbent.

## 3. New auditable certification contract

`src/ptxflex/f3_adequacy_certificates.py` independently reads the original
Stage A output and outputs
`stageA_additional_shortfall_certified_interval.json` alongside it in the
source workflow. It validates original ZIP identifiers, historical target,
solver/case status, physical residuals, EOS pressure checks and delivery closure.

For minimization with shortage `s >= 0`, a verified MILP feasible solution with
objective `U` and valid dual bound `Ldual` yields

```
max(0, Ldual) <= minimum feasible additional shortage <= U
full-demand-shortfall bounds = (18,250,000 - 16,335,279.317...) + [L, U]
```

When the solver does not provide a finite lower bound, `L=0`: the
report must **not** invent positive minimum inadequacy. If the model returns
an invalid or contradictory bound, a broken physical residual or wrong source
hash, certification stops. A zero-shortfall **feasible** MILP result proves
the minimum zero by nonnegativity. Numerical status and solver MIP gap are
preserved; positive incumbents do not become exact physical deficits.

The new [Stage A Actions workflow](../.github/workflows/f3-pressure-adequacy-2023.yml)
runs these certification checks for all four source configurations; its output
is a **derived, source-locked numerical artifact**, not an input original source.

## 4. Cross-repository scientific gate

PtXLens implements `src/ptxlens/f3_adequacy_intake.py`, a hash-checked,
fail-closed intake. A reviewer must independently register the upstream
certificate's own SHA-256; self-generated hashes alone do not prove independent
provenance. Even if *both* configurations can deliver the matched historical
profile, the comparative LCA/TEA gate remains blocked until the same pressure,
purity, additional equipment BOM, compression/cooling, loss, native BAFU LCIA
and discounted cash-flow requirements are met.

## 5. Next decision and falsification tests

1. Reconcile and independently verify the previously feasible 40t E+S
   **zero-shortfall full-service dispatch** under both 200bar interpretations,
   with the same code/parameters as Stage A. An incumbent-only Stage A >0
   cannot override a verified zero-shortfall witness.
2. Publish the Stage A [L,U] shortage certificates with source-run artifact
   ID and SHA-256, and classify E's zero-delivery feasibility only when its
   lower bound is proven strictly positive or an independent infeasibility
   certificate establishes the same.
3. Test stage-conditional alternative *common delivery service* / source-backed
   backup supply. All subsequent comparisons must include backup burdens,
   full operating compressor and cooler electricity, and physical equipment.
4. Do not use any difference in annual wholesale settlement, scoped native
   BAFU kgCO2e/kg, or tank empty mass as the full LCOH/GWP advantage.

**Acceptance:** numerical consistency reconciled, no invented source, positive
shortfall conclusions bounded/proven and independently reviewed; F3 remains
OPEN until same-hour service and physical duty are certified for the chosen
comparison.

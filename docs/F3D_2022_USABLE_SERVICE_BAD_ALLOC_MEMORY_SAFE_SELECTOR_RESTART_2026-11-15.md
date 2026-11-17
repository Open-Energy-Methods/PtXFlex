# F3-D 2022 usable-service HiGHS memory fault: preserving a completed run

Prepared: 15 November 2026. Observed local Windows output: 27 original scientific suite tests passed. 2022 ARCO wind and full original ENTSO-E A44 source pair verified; 2022 max_inventory completed with nominal 2022 price-calendar E minus E+S operational electricity-cost savings of EUR 3,905,632.9363086373. The next, usable_service, failed in the price-neutral maximum feasible H2 service selector with MemoryError: std::bad_alloc in SciPy/HiGHS. No 2022 usable-service result is claimed. Do not delete existing private results.

The selector uses 8 decision variables per hour for 8,760 hours plus the annual uniform-service fraction: 70,081 variables including 17,520 binary on/off and charging-direction decisions. The 3,600-second solver time limit is NOT a memory limit. The failure is not evidence of invalid ERA5, A44 source, model infeasibility or a completed second interpretation.

## Implemented changes

- Windows phase SolveARCO2022 / SolveARCO2024 now takes optional -Mode usable_service, -Mode max_inventory or -Mode both (default). Existing successfully completed year/mode output and private hourly witness are preserved and skipped after coherence checks, not overwritten. Incomplete results fail closed.
- Before a large original selector MILP, the code attempts a GLOBAL LP RELAXATION upper bound on maximum service, followed by an all-binaries-fixed LP with the exact original physical equations to obtain an INTEGER-FEASIBLE primal. This is accepted as a rigorous mixed-integer globally optimal result ONLY if the root LP's certified upper bound and valid integer primal differ by at most the same original 1e-6 relative gap. It retains all source E physical constraints, including commitment minimum load, ramp, mutually exclusive charge/discharge, cyclic original storage, compressor electrical duty, Type I 20–200bar EOS and independent mass/energy audit. It is explicitly labelled LP_GLOBAL_UPPER_BOUND_AND_INTEGER_FIXED_BINARY_FEASIBLE_PRIMAL, not falsely described as a HiGHS branch-and-bound dual result.
- If no certificate at the original tolerance, the solver falls back to the EXACT original integer MILP, with a documented HiGHS node_limit of 500 to bound search-tree growth. This may still run out of memory or fail to converge. The program stops and makes no unsupported scientific claim if it cannot achieve the unchanged 1e-6 tolerance.
- Hermetic tests added for an exact LP/integer certificate, an LP-only infeasible-integer rejection, out-of-memory fail closed and the unchanged original small-hour MILP. GitHub-hosted CI is out of minutes; local rerun is mandatory. The new implementation has not been proven to solve the actual 2022/24 year to completion.

## Minimal local restart

In PowerShell, while no separate instance of the annual source-year MILP is running:

    cd C:\Users\prasa\OEM_Research\PtXFlex
    git pull --ff-only
    .\.venv\Scripts\python.exe -m pytest -q tests/test_f3d_service_selector_memory_safe_lp_certificate.py tests/test_f3d_year_matched_service.py
    .\scripts\F3D_Local_Research.ps1 -Phase SolveARCO2022 -Mode usable_service

Keep the completed 2022 max_inventory report and primal in $HOME\PtX_PRIVATE_RESEARCH\results. If the new tests fail, do not launch the annual run. New log messages identify the GLOBAL LP bound, the fixed binary feasibility trial and any bounded MIP fallback. Never weaken 1e-6 global optimality criterion, alter H2 service definition or fabricate a result to force completion.

Only after 2022 usable_service fully passes, attempt SolveARCO2024. The four completed source-year cases still need independent physical witness replay and year-by-year economic bounds in PtXLens. These are operational source-model nominal EUR costs, not vendor BOM/CAPEX, industrial plant monitoring, inflation-corrected investment NPV, BAFU native LCIA or a complete scientific v1 release.

SciPy official MILP options (node_limit, time_limit, mip_rel_gap): https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html .

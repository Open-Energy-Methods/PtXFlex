# Publish F3-D 2022/2024 independently audited aggregates safely

Date: 15 November 2026. Source datasets and the private integer primal are located under the local Windows directory $HOME\PtX_PRIVATE_RESEARCH, not under either Git checkout.

## Motivation

The 4 source-year F3-D scenarios have been run from real Copernicus ERA5 ARCO wind + ENTSO-E NL A44 market prices. The underlying original raw source-year private price/wind series (8760 and 8784 hours), recovered 2023 PyNEXUS provider NetCDF and private F3-D primal hourly vectors must **never be pushed directly** to this public research repository. The user-visible messages report the numerical results, but publication must bind these figures to the full local evidence, not hard-code those messages as a scientific data artifact.

The source-controlled exporter checks the archived source-year price/wind provider hashes again, replays all four full-year hourly E/E+S primal and independent CoolProp pressure reviews with **PtXLens code**, independently rechecks the complete four-case source arithmetic, then writes an allowlisted public JSON and report. No API access, no host GitHub Actions usage or repeat 70,000-variable solver optimizations are required. Public output includes modelled nominal electricity-cost differences, each capacity semantics, delivered H2 kg/day/year, EUR/kg normalization, modelled grid electricity and compression MWh, privately logged primal hashes, solver-reported dual-cost bounds, and explicit v1.0/LCA/CAPEX limitations.

## Run once on Windows, in PtXFlex

    cd C:\Users\prasa\OEM_Research\PtXFlex
    git pull --ff-only
    .\.venv\Scripts\python.exe -m pytest -q tests/test_f3d_safe_public_evidence_export.py
    .\.venv\Scripts\python.exe .\scripts\f3d_publish_verified_aggregate_evidence.py --public-output-dir .\research

The above command refuses incomplete, corrupted or inconsistent private review artifacts. It refuses to overwrite existing published results with different data; create a new evidence schema/file version if evidence has legitimately changed. It also refuses to read private archives inside the Git checkout. The original provider data and primal remain outside Git.

## Review exactly what will be pushed

    git status --short
    Get-Content .\research\F3D_ARCO_2022_2024_PUBLIC_VERIFIED_RESULTS_v1.md
    Get-Content .\research\F3D_ARCO_2022_2024_PUBLIC_VERIFIED_AGGREGATES_v1.json

Review that all information is appropriate to publish under the applicable dataset licensing and project release plan. The two files should contain only aggregate model results, source hashes and scientific caveats, not raw wind/price samples, private witness/dispatch vectors, tokens, personal information, supplier quotations or native BAFU process inventory.

Stage ONLY these two explicit files:

    git add -- research/F3D_ARCO_2022_2024_PUBLIC_VERIFIED_AGGREGATES_v1.json research/F3D_ARCO_2022_2024_PUBLIC_VERIFIED_RESULTS_v1.md
    git diff --cached --check
    git diff --cached --stat
    git diff --cached

If the staged changes are clean, commit and push the feature branch:

    git commit -m "F3-D: publish independent 2022/2024 matched-service aggregate source evidence"
    git push origin feat/milp-methanol-baseline

Never run git add -A on $HOME\PtX_PRIVATE_RESEARCH or copy the entire private folder to either repository. Publishing source and private-primal SHA256 commitments is not equivalent to publishing the originals; external reviewers cannot re-run licensed source calculations from hashes alone. The exporter preserves this explicit limitation.

## Research enabled by this publication

1. F3-D source-traceable robust outcomes, distinct service normalization, hourly source-calendar provenance, arithmetic savings bounds, and controlled sensitivity designs. Counterfactual hour-by-hour price/wind tests still require private local execution and sanitized results — aggregate evidence alone cannot perform an actual hourly reoptimization.
2. PtXLens L3-A DCF scenarios may treat these 4 individually certified **modelled** electricity-cost differences as historical nominal operating-savings baselines, then scan additional CAPEX/OPEX assumptions and report break-even regions. Do NOT attribute manufacturer-specific prices without written vendor quotes; do NOT report 2022/2024 nominal amounts as same-euro-year without inflation harmonization.
3. Distinct evidence workstream for independent optimizer dual certificate replay or stronger mathematical reference checks, native BAFU 2026 inventory mapping, and traceable publicly reproducible methodological figures. Native BAFU supplier LCI database content and licensed processes must not be copied into the public repo without license review; provenance, flow mappings and original source URLs can be published independently.

The modelled 2022 max_inventory and usable_service estimates were approximately EUR 3.906M and EUR 3.904M; 2024 max_inventory and usable_service approximately EUR 2.247M and EUR 2.206M. Exact figures should always come from the exported JSON, never be entered by hand. None of these figures establishes net installed investment NPV or whole-plant GWP.

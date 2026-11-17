# F3-D source-gated fast ERA5 ARCO: 2023 complete validation to 2022/2024 source years

Prepared 15 November 2026. **Real executed January 2023 pilot:** 744 of 744 UTC hours, 0 MW maximum original CDS-to-ARCO wind power difference, 7.2 s remote ARCO read. **Full 2023 8,760-hour ARCO qualification, 2022/2024 alternate-year ARCO acquisition and E/ES annual optimization have not yet executed.** GitHub-hosted CI is exhausted; all following commands run on Windows and consume no GitHub Actions minutes.

## Scientific source rules

The official [ECMWF ARCO geo-chunked ERA5 product](https://confluence.ecmwf.int/spaces/CKB/pages/505390919/ERA5+hourly+Analysis+Ready+Cloud+Optimised+ARCO+data+on+single+levels+from+1940+to+present+Product+User+Guide+PUG) is **repackaged ERA5**, optimized for time series at a single grid point. It is a different product representation from the original per-month CDS NetCDF. Original source point 52.5N/3.5E; wind fields U/V at 10m/100m; original PyNEXUS float32-to-float64 100m to 120m turbine conversion remains unchanged. The original January 2022 verified native CDS NetCDF remains private and untouched, along with the frozen original 2023 12-month CDS archive.

Required source evidence hierarchy:

1. Full original PyNEXUS 2023 CDS NetCDF monthly SHA replay (12 files and exact 8,760 UTC hours), original 1W reference SHA256 9e0e95ddf9c70547ab6ce696f52a82dc312f11d7cd760de5dc779c6ac2b43c9c.
2. Independently retrieve official ARCO 2023 at the **same original grid cell**, all 8,760 UTC hours, all four original wind components. Qualify only if every hour's modelled wind power matches within exactly 1W-quantized equality, with component max errors each <=1e-5 m/s. The output reports full per-component deviations and float64 non-bit-identity. Never promote an incomplete source.
3. After full-year 2023 PASS, retrieve ARCO **2022 and 2024** as independently hashed private point-extraction NetCDFs, with complete 8,760 and 8,784 UTC hours, strict leap-day check, four component native dtype and SHA, full source URL and immutable source provenance. Preserve complete 2023 verification receipt as a separately hashed original-source binding in each year. These point extractions are NOT twelve native monthly CDS original downloads.
4. Independently reread every point NetCDF and 2023 calibration receipt, recompute the full 120m wind curve and SHA, and pair with full original ENTSO-E NL A44 hourly price vector for each same year. The old original-monthly CDS validation path is **unchanged**.
5. Run both source 20,000kg E and 40,000kg E+S storage interpretations on an identically selected hourly hydrogen target, separately for 2022 and 2024, and independently replay all private MILP witness mass/electricity, CoolProp 20-200bar EOS, nominal EUR price settlement and solver bounds in PtXLens. No industrial validation, full LCA/GWP, manufacturer-grade Type I BOM or economic v1.0 release claim.

## Immediate Windows command sequence

Run in C:\Users\prasa\OEM_Research\PtXFlex and leave the existing private original CDS directories untouched:

    git pull --ff-only
    .\.venv\Scripts\python.exe -m pytest -q tests/test_f3d_era5_arco_pilot.py tests/test_f3d_era5_arco_full_year.py tests/test_f3d_era5_arco_private_source_gate.py
    .\scripts\F3D_Local_Research.ps1 -Phase CalibrateARCO2023
    .\scripts\F3D_Local_Research.ps1 -Phase Status

**STOP** if the full 2023 report status does not equal ARCO_FULL_2023_8760H_CDS_NUMERICALLY_EQUIVALENT_1W; do not proceed to alternate source years and do not delete failed provenance. Inspect full-year matched hours, maximum U/V component m/s deltas, and modelled MW delta. An actual local run is the only way to establish provider equivalence.

If and only if the full original-source 2023 gate passes:

    .\scripts\F3D_Local_Research.ps1 -Phase FetchARCO2022
    .\scripts\F3D_Local_Research.ps1 -Phase FetchARCO2024
    .\scripts\F3D_Local_Research.ps1 -Phase VerifyARCO2022
    .\scripts\F3D_Local_Research.ps1 -Phase VerifyARCO2024
    .\scripts\F3D_Local_Research.ps1 -Phase SolveARCO2022
    .\scripts\F3D_Local_Research.ps1 -Phase SolveARCO2024
    .\scripts\F3D_Local_Research.ps1 -Phase ReviewARCO

All source NetCDF, EU ETS electricity-price XML, source calibration, and private full-hour primal data remain in $HOME\PtX_PRIVATE_RESEARCH, **outside Git**; API secret is requested with a hidden prompt and removed afterward. Existing monthly 2022/24 acquisition can remain dormant. Do not cancel a genuinely active CDS request. Do not run Assemble2022 or Verify2022 on the alternate ARCO source path; the latter strictly expects 12 real CDS monthly original files, by design.

The new independent ARCO source gate validates all four source vectors and complete 2024 leap-year calendar, copy of full-year 2023 ARCO-vs-original CDS evidence, year-specific pricing, and explicit alternate-representation flags. PtXLens's separate metadata review refuses claims that ARCO is native monthly CDS and prevents comparing two storage interpretations with different source representations in the same year. It does not independently solve the optimization again or validate a real installed industrial plant.

Scientific status of v1.0 remains NOT PASSED until all source-year results, original-versus-alternate provenance, manufacturer cost/LCI, native BAFU v1.1 LCA, P0 independently restored backups, and real source model limitations are resolved.

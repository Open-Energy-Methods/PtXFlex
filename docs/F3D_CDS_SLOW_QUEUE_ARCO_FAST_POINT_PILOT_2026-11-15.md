# F3-D — Slow Copernicus CDS queue: official ARCO fast-point pilot (15 November 2026)

## Observation: provider processing queue, not a network-size problem

An original single-month `ERA5 reanalysis-era5-single-levels` source NetCDF for the configured 52.5N, 3.5E reference is about 160–175 kB. In user-supplied Copernicus request history on 2026-11-15, individual submissions took approximately **2 min 35 s to 1 h 39 min**. The historical research code requests **12 months per year** serially and waits for each CDS request; 2022+2024 therefore requires 24 queued provider computations unless an independently source-validated alternate original-data delivery route is found. The original 2023 is already fully recovered and reference-audited.

Copernicus' [current live dashboard](https://cds.climate.copernicus.eu/live) shows thousands of waiting users and queued requests. The original month's ~170kB size is not the bottleneck.

**DO NOT** abandon verified original months, delete a still-active partial month, submit all 24 requests concurrently, or interpret an ACCEPTED request as a downloaded original. The local Windows runner already skips all validated month SHA/UTC receipts.

## Official alternative: ERA5 hourly *time-series* / ARCO geo-chunked

ECMWF officially offers [ERA5 hourly time-series data on single levels](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries?tab=analysis_ready_data), built on the [analysis-ready geo-chunked ERA5 Zarr store](https://confluence.ecmwf.int/spaces/CKB/pages/505390919/ERA5+hourly+Analysis+Ready+Cloud+Optimised+ARCO+data+on+single+levels+from+1940+to+present+Product+User+Guide+PUG). It is specifically optimized for **long time series at one grid point** and includes the four wind fields we require: 10m U/V and 100m U/V. Its single-level atmospheric fields have a 0.25-degree grid.

The reference point remains **52.5°N, 3.5°E**, hourly UTC, the actual PyNEXUS reference turbine wind model. ARCO is a *repackaged data source*, not necessarily original PyNEXUS-NetCDF byte-identical. It must NOT be silently substituted into the existing `f3d_live_provider_pair_gate`, whose provenance expects original `reanalysis-era5-single-levels` month-request NetCDF bytes, without explicitly separate ARCO source credentials, calendar, data-format evidence, and full 2023 reference calibration.

### Pilot command (separate PowerShell window after a finished monthly request)

The pilot reads only January 2023 for the exact original point, **does not submit a monthly CDS original-production job**, and compares all 4 ARCO wind components and 744-hour reconstituted modelled wind production to the recovered original 2023 Jan NetCDF by SHA:

```powershell
cd C:\Users\prasa\OEM_Research\PtXFlex
git pull --ff-only

# Original full 2023 recovery must pass current hash-validation status
.\scripts\F3D_Local_Research.ps1 -Phase Status

# Downloads only ARCO Zarr metadata and 744h original point chunks.
# Asks for CDS token with hidden input, never commits secret or source data.
.\scripts\F3D_Local_Research.ps1 -Phase PilotARCO
```

Output: `$HOME\PtX_PRIVATE_RESEARCH\arco-2023-jan-point-calibration-private.json` with source URL, exact original January NetCDF SHA256, source variable IDs, original vs ARCO 10m/100m component max absolute deviations, max/mean power difference in MW, 1-W-resolution SHA256 match, request elapsed time, and explicit **`ARCO_2022_2024_years_independently_admitted=false`**.

Interpretation:

- `JAN2023_1W_CALIBRATION_PASS_ONLY_FULL_YEAR_NOT_YET_VALIDATED`: a positive **January-only** signal. To switch annual historical research we must still run *the entire original 2023* 8,760-hour matched-power/source-year calibration and construct a separately registered ARCO 2022/2024 source schema, including provider revision, changed native processing, uncertainty and full UTC source integrity. The frozen original 2023 must remain untouched.
- `JAN2023_ARCO_VS_ORIGINAL_CDS_NUMERICALLY_DIFFERENT_STOP`: ARCO cannot be claimed identical to the current original yearly wind convention. Retain the model's original validated ERA5 monthly path or present the alternate source as a **different historical input method** with uncertainty, rather than silently replacing.
- Source auth, connectivity, Zarr metadata failure: no evidence of numerical mismatch; investigate token permissions, data terms and Zarr client, and keep original monthly acquisitions. No official speed guarantee.

The pilot is intentionally **read-only with respect to the current 2022/2024 source archive**; after running it the storage status remains whatever was physically completed before. It cannot establish viability, a vendor quote, native BAFU life-cycle impacts, or an actual industrial site operating value.

## Suggested immediate operational behaviour

If `Fetch2022` is currently in progress, leave its active month's request alone and continue only verified original monthly months. Once you reach a clean break, **test `PilotARCO`** and review its provenance. Alternatively, the manual web form for the [ERA5 time-series dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries?tab=download) can request a long interval at the fixed 52.5N/3.5E grid cell but must undergo the same original 2023 power calibration before any claimed interchangeability.

Do not infer elapsed processing time from file size or attempt to speed the CDS queue via a more powerful computer or faster local broadband. Avoid using GitHub Actions to wait through CDS processing even after the free minutes reset.

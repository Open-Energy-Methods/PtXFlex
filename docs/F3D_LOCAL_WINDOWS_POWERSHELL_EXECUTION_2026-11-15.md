# F3-D — Local-first original ENTSO-E and ERA5 recovery on Windows

**As of 15 November 2026.** GitHub Actions allowance for Open-Energy-Methods is exhausted until **1 December 2026**. The historical original data, model and physical validation must continue **locally**, not by repeatedly rerunning GitHub-hosted Actions. **No ERA5 2022/2024 original full-year weather and no certified 2022/2024 E/E+S actual-source MILPs yet.**

## What you need to install (once)

- Windows 10/11 PowerShell, **Python 3.12** with `py -3.12` launcher, **Git**, [GitHub CLI](https://cli.github.com/) (`gh`), enough local storage, a working Copernicus CDS access token, and a valid Copernicus ERA5 single-levels dataset licence/terms acceptance. Source: [official CDS API setup](https://cds.climate.copernicus.eu/en/how-to-api). A GitHub organization Actions secret does **NOT** automatically appear in your local terminal, and cannot be read back from GitHub.
- Authentication to the two private research repos, `Open-Energy-Methods/PtXFlex` and `Open-Energy-Methods/PtXLens`, and the historical private `abhijith-sivaprasadan/PyNEXUS` repository.
- The setup installs `cdsapi>=0.7.7`, `xarray`, `netCDF4`, `pandas`, `numpy`, `scipy`, `CoolProp==8.0.0`, `pytest`, plus the two scientific repositories in editable mode. The file `scripts/F3D_Local_Research.ps1` never persists an ERA5 token.

Example for a clean, **local** Windows checkout:

```powershell
py -3.12 --version
gh auth login
$repoRoot = Join-Path $HOME "OEM_Research"
New-Item -ItemType Directory -Force $repoRoot | Out-Null
Set-Location $repoRoot

gh repo clone Open-Energy-Methods/PtXFlex
gh repo clone Open-Energy-Methods/PtXLens

Set-Location .\PtXFlex
git switch feat/milp-methanol-baseline
Set-Location ..\PtXLens
git switch feat/wp0-screening-core
Set-Location ..\PtXFlex

# Process-only permission if your PowerShell execution policy blocks local scripts:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\F3D_Local_Research.ps1 -Phase Install
```

The default original-provider storage is **`$HOME\PtX_PRIVATE_RESEARCH`**, explicitly OUTSIDE both Git repositories. Never put original NL market XML, ERA5 NetCDF, private hourly H₂ dispatch witnesses, provider tokens or original supplier documents into Git commits. You can override with `-PrivateRoot "E:\Research_Private"` on **every call**, preferably on a stable healthy drive.

## Step 1 — Download ORIGINAL saved sources first (important expiry)

The exact original 2023 ERA5 re-delivery already exists from the successful 26 October PyNEXUS run. It is not necessary to make a fresh 2023 CDS request. Original 2022/2023/2024 NL electricity prices were already retrieved and verified in PtXFlex on 14 November.

```powershell
.\scripts\F3D_Local_Research.ps1 -Phase Download
.\scripts\F3D_Local_Research.ps1 -Phase Recover2023
.\scripts\F3D_Local_Research.ps1 -Phase Status
```

The script uses `gh run download` and **does not allocate GitHub-hosted Actions minutes**. It downloads:

- `Open-Energy-Methods/PtXFlex` run `43617006319`: each of three `private-F3D-entsoe-original-2022/2023/2024-NOT-releasable` artifacts, with 14 source A44 documents, normalized UTC CSV and original SHA provenance. The artifacts have **short 7-day retention** from 14–15 Nov; **download immediately**, ideally no later than 21 Nov.
- `abhijith-sivaprasadan/PyNEXUS` run `40230838449`, artifact `wp1-cds-2023-primary-monthly-netcdf`: complete original **12 months of 2023 ERA5**. The imported archive is checked month-by-month against frozen **12 original NetCDF SHA256s** and reproduced at 1 W precision against the original `E/stage_b.csv` 8,760-hour wind vector. It does not claim bitwise equality of the new floating-point serialization.
- `2023` original additional audit artifact may be downloaded separately; the local seed source itself uses frozen hash and full original model calibration.

If a source artifact has already expired, **do not replace it with an invented 2022/2024 source**. Recover the actual private ZIP from the earlier owner-only Google Drive archive or report the missing source and halt scientific admission. Keep at least two independent private backups and test restores; simply downloading to the same disk is not an independent backup.

## Step 2 — Run ONE real CDS request first

Before the first call, sign into the Copernicus [ERA5 single-levels dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels) and accept its terms as required by the provider. The PowerShell script prompts for the **CDS personal access token with input hidden**; it passes the token as `ERA5_API_KEY` to `cdsapi.Client` only during that invocation, then removes it from the current script process. Never paste it in chat, into a command line, into a Python file or into a Git commit.

```powershell
# Pilot: one real 2022 calendar month, 4 wind fields, 3×3 grid, UTC
.\scripts\F3D_Local_Research.ps1 -Phase Fetch2022 -Month 1

# Once January has original NetCDF source SHA and month_provenance.json:
.\scripts\F3D_Local_Research.ps1 -Phase Status
.\scripts\F3D_Local_Research.ps1 -Phase Fetch2022
.\scripts\F3D_Local_Research.ps1 -Phase Fetch2024
```

Each month is a separate source request to `reanalysis-era5-single-levels` with original U/V at **10m and 100m**, original point **52.5°N 3.5°E**, all hourly UTC dates; 2024 February correctly has **29 days**. API request starts are explicitly logged as `CDS_API_CALL_START` and original source verification as `CDS_API_CALL_AND_SOURCE_VERIFIED` with month-hour count and SHA256. There is **no GitHub-hosted runner or GitHub usage cost** for these local Python runs.

The complete-month check is idempotent: a byte-valid original month is **not downloaded again**. If a request fails and leaves a partial month directory, the script **refuses to overwrite or silently resume it**; inspect the partial NetCDF and the provenance, move that incomplete directory to an explicitly marked quarantine name, then retry only that month using `-Month N`.

CDS processing is provider-queued and may be slow; do not start 24 requests concurrently. Keep the machine awake and use a stable connection. A failed or cancelled request does not establish a source year.

## Step 3 — Reconstruct all UTC hours and independently admit paired source history

Run **only after 12 monthly originals are verified for the respective year**:

```powershell
.\scripts\F3D_Local_Research.ps1 -Phase Assemble2022
.\scripts\F3D_Local_Research.ps1 -Phase Assemble2024

# Fail unless ALL source-original XML / NetCDF byte hashes,
# chronology and original 2023 reference anchoring are consistent.
.\scripts\F3D_Local_Research.ps1 -Phase Verify2022
.\scripts\F3D_Local_Research.ps1 -Phase Verify2024
```

The annual resolver writes exactly 8,760 UTC hours for 2022 and 8,784 for 2024, preserving leap day; generates original 12-NetCDF archive copied byte-for-byte, a SHA manifest, normalized hourly source wind and the private pair certificate. It pairs the historical wind with the correct matching-year ENTSO-E source price, verified independently against the 2023 original reference. Price and wind source vectors remain private.

## Step 4 — 4 pressure-screened paired E versus E+S annual MILP cases

Proceed only after the private 2022/2024 source-pair certificates passed and their provenance is retained:

```powershell
.\scripts\F3D_Local_Research.ps1 -Phase Solve2022
.\scripts\F3D_Local_Research.ps1 -Phase Solve2024
```

Each year solves the **original E(20t) price-independent maximum uniform feasible H₂ service fraction** (same original 50t/day flat hourly shape), then price-optimizes E and E+S(40t) against the **same exact hourly H₂ target** under two separately named storage semantics, `max_inventory` and `usable_service`. Each solver must satisfy real-gas 20–200 bar source screening, mass and energy closure, relative HiGHS integer MIP gap ≤1e-6, valid cost lower bound, and independent source hash checks. The runner uses 3,600-second limits per optimization; this is a **limit, not a promise that the solver will finish**. If feasible integer convergence is not achieved, the case remains UNRESOLVED, not profitable or zero-savings.

All four **aggregate** reports and four **private full-hour primal** traces go to `$HOME\PtX_PRIVATE_RESEARCH\results`. Never publish them until licence/rights review. A witness is not measured plant operation.

## Step 5 — independent PtXLens mass, electricity, price, pressure replay

```powershell
.\scripts\F3D_Local_Research.ps1 -Phase Review
```

This executes `ptxlens.f3d_external_year_private_witness_replay` separately for all four cases using the local original hourly source price, wind, E/E+S optimizer primal, hydrogen delivery, original source model constants, and independent CoolProp EOS checks, **without importing PtXFlex model/solver code**. It then executes independent `ptxlens.f3d_external_year_independent_review` for all four case source-equal quantity/bound arithmetic reports.

These are source-model checks and neither independent HiGHS re-solves nor site-level engineering qualifications. The user should send only **redacted** stdout from `Status` and/or new aggregate JSON results (no raw XML, NetCDF, full-hour private series, secrets).

## Parallel non-ERA5 work

The [PtXLens native BAFU:2026 v1.1 process identity crosswalk](https://github.com/Open-Energy-Methods/PtXLens/blob/feat/wp0-screening-core/docs/L3B_BAFU_2026_v1_PUBLIC_TO_NATIVE_v11_TYPEI_STATIONARY_MATERIAL_PROCESS_CROSSWALK_2026-11-14.md) requires the original licensed `.zolca`, original UUID candidates artifact and 19-line actual manufacturer foreground BOM. This is **not a weather task** and can be completed on the same local machine separately. Native stationary Type I GWP and quoted CAPEX **must not be fabricated from public BAFU v1 names or a published finished vessel mass**.

## Scientific readiness matrix and practical halt conditions

| Condition | Current status / halt rule |
|---|---|
| 2023 original PyNEXUS ERA5 | **Already recovered**; import without any new API request |
| Original ENTSO-E A44 prices 2022–24 | **Verified**; download short-lived original artifacts immediately |
| Source-year ERA5 2022/2024 | **NOT ACQUIRED** yet; local monthly real CDS requests required |
| 2022/2024 paired calendars | Cannot pass until complete 12 × 2 original NetCDF months |
| Four source-year MILP reports | Cannot be claimed until actual integer solver witnesses exist |
| PtXLens local independent primal review | Cannot pass until actual source and complete solver witnesses exist |
| Source P0 independent backups | Google Drive one private location; second physically independent read-back needed |
| OEM Type I BOM / native whole-plant BAFU | Missing manufacturer quantities and native linked calculations |
| Scientific v1.0 | **NOT PASSED**; real-site validation, economic and inventory gates remain |

**Security:** Original data and machine paths are private; redact any personally identifying information and tokens from logs. The source files may have licence restrictions; never commit raw originals or unpublished equipment/supplier records to the public repository. The script does not automatically upload any original source data to cloud storage.

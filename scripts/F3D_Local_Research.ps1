# Windows PowerShell 5.1/7; original provider data must stay private.
# Launch from the PtXFlex clone or pass -FlexRoot and -LensRoot.
[CmdletBinding()]
param(
 [ValidateSet("Install","Download","Recover2023","PilotARCO","CalibrateARCO2023","FetchARCO2022","FetchARCO2024","VerifyARCO2022","VerifyARCO2024","SolveARCO2022","SolveARCO2024","ReviewARCO","Fetch2022","Fetch2024","Assemble2022","Assemble2024","Verify2022","Verify2024","Solve2022","Solve2024","Review","Status")]
 [string]$Phase="Status",
 [int]$Month=0,
 [string]$PrivateRoot=(Join-Path $HOME "PtX_PRIVATE_RESEARCH"),
 [string]$FlexRoot=(Join-Path $PSScriptRoot ".."),
 [string]$LensRoot=(Join-Path $PSScriptRoot "..\..\PtXLens")
)
Set-StrictMode -Version Latest
$ErrorActionPreference="Stop"
$PrivateRoot=[IO.Path]::GetFullPath($PrivateRoot)
$FlexRoot=[IO.Path]::GetFullPath($FlexRoot)
$LensRoot=[IO.Path]::GetFullPath($LensRoot)
$python=Join-Path $FlexRoot ".venv\Scripts\python.exe"
function Need([bool]$ok,[string]$reason) { if(-not $ok) { throw $reason } }
function Ensure([string]$path) { if(-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path -Force | Out-Null } }
function Run([string]$exe,[string[]]$argv) { & $exe @argv; if($LASTEXITCODE -ne 0) { throw "Command failed; inspect error output (exit $LASTEXITCODE)" } }
function MonthRoot([int]$y,[int]$m) { Join-Path $PrivateRoot ("era5-{0}-{1:d2}" -f $y,$m) }
function Verified2023Recovery() {
  $recovery=Join-Path $PrivateRoot "wind-2023-recovered"
  if(-not (Test-Path $recovery)) { return $false }
  $p=Join-Path $recovery "complete\provenance.json"
  $e=Join-Path $recovery "source_recovery.json"
  Need ((Test-Path $p -PathType Leaf) -and (Test-Path $e -PathType Leaf)) "Partial 2023 recovered source; preserve directory and inspect the original error"
  $j=Get-Content -LiteralPath $p -Raw | ConvertFrom-Json
  $original=Get-Content -LiteralPath $e -Raw | ConvertFrom-Json
  $expectedSHA="9e0e95ddf9c70547ab6ce696f52a82dc312f11d7cd760de5dc779c6ac2b43c9c"
  Need ($j.schema_version -eq "ptxflex.f3d_era5_100m_120m_native_original_monthly_source.v1" -and
        [int]$j.year -eq 2023 -and [int]$j.annual_utc_hours -eq 8760 -and
        $j.status -eq "SOURCE_RECONSTRUCTED_NOT_EXTERNALLY_REVIEWED" -and
        $j.full_UTC_calendar_year_no_gaps -eq $true -and
        $j.original_2023_wind_microMW_reference_match -eq $true -and
        $j.normalized_wind_1W_quantized_SHA256 -eq $expectedSHA) "2023 annual source has not passed original PyNEXUS 8,760-hour 1W SHA verification"
  Need ($original.schema_version -eq "ptxflex.f3d_2023_exact_PyNEXUS_original_CDS_12_month_GitHub_extraction.v1" -and
        $original.original_2023_1W_model_reconstruction_PASSED -eq $true -and
        $original.no_fresh_CDS_requests_made -eq $true) "2023 original PyNEXUS recovery archive receipt is missing or incomplete"
  $csv=Join-Path $recovery "complete\normalized_UTC_wind.csv"
  Need ((Test-Path $csv -PathType Leaf) -and
        (Get-FileHash -LiteralPath $csv -Algorithm SHA256).Hash.ToLowerInvariant() -eq $j.normalized_csv_SHA256) "2023 normalized hourly wind CSV does not match original SHA provenance"
  $raw=Join-Path $recovery "complete\original_monthly_netcdf"
  Need (Test-Path $raw -PathType Container) "2023 original NetCDF directory is missing"
  $monthly=@(Get-ChildItem -LiteralPath $raw -File -Filter "*.nc")
  Need ($monthly.Count -eq 12 -and $j.source_monthly_files.Count -eq 12) "2023 source must contain exactly 12 original monthly NetCDF and manifest records"
  $names=@{}
  foreach($m in $monthly) { $names[$m.Name]=$m }
  foreach($entry in $j.source_monthly_files) {
    Need ($names.ContainsKey($entry.filename)) "2023 source missing original month $($entry.filename)"
    Need ((Get-FileHash -LiteralPath $names[$entry.filename].FullName -Algorithm SHA256).Hash.ToLowerInvariant() -eq $entry.sha256) "2023 source month $($entry.filename) has changed SHA"
  }
  return $true
}
function SourceOK([int]$y,[int]$m) {
  $dir=MonthRoot $y $m
  if(-not (Test-Path $dir)) { return $false }
  $manifest=Join-Path $dir "month_provenance.json"
  Need (Test-Path $manifest) "Partial original month folder at $dir; inspect/quarantine it before retrying"
  $j=Get-Content -Raw $manifest | ConvertFrom-Json
  Need ($j.year -eq $y -and $j.month -eq $m -and $j.status -eq "MONTH_NATIVE_NETCDF_AND_UTC_CALENDAR_VERIFIED_NOT_YEAR") "Unverified original month at $dir"
  $file=Join-Path $dir ("original_monthly_netcdf\era5_{0}_{1:d2}_u10_v10_u100_v100.nc" -f $y,$m)
  Need (Test-Path $file) "Monthly original source file missing: $file"
  Need ((Get-FileHash $file -Algorithm SHA256).Hash.ToLowerInvariant() -eq $j.source_month_original_files[0].sha256) "Monthly original source SHA changed: $file"
  return $true
}
Need (-not $PrivateRoot.StartsWith($FlexRoot + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) "Private original source must NOT be inside PtXFlex Git!"
Need (-not $PrivateRoot.StartsWith($LensRoot + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) "Private original source must NOT be inside PtXLens Git!"
Ensure $PrivateRoot
if($Phase -ne "Install" -and $Phase -ne "Download" -and $Phase -ne "Status") { Need (Test-Path $python) "Run Install first" }
switch($Phase) {
 "Install" {
   Need (Test-Path (Join-Path $FlexRoot "pyproject.toml")) "PtXFlex clone missing"
   Need (Test-Path (Join-Path $LensRoot "pyproject.toml")) "PtXLens clone missing; pass -LensRoot"
   if(-not (Test-Path $python)) { Run "py" @("-3.12","-m","venv",(Join-Path $FlexRoot ".venv")) }
   Run $python @("-m","pip","install","--upgrade","pip")
   Run $python @("-m","pip","install","-e",($FlexRoot+"[dev,physics]"),"-e",($LensRoot+"[dev]"),"cdsapi>=0.7.7","xarray>=2024.0","pandas>=2.0","netCDF4>=1.6")
   Run $python @("-m","pytest","-q",(Join-Path $FlexRoot "tests\test_f3d_era5_sharded_acquisition.py"),(Join-Path $FlexRoot "tests\test_f3d_year_matched_service.py"),(Join-Path $LensRoot "tests\test_f3d_external_year_independent_review.py"))
 }
 "Download" {
   Run "gh" @("auth","status")
   foreach($y in @(2022,2023,2024)) {
     $dest=Join-Path $PrivateRoot "price-$y"
     if(-not (Test-Path $dest)) {
       Ensure $dest
       Run "gh" @("run","download","43617006319","-R","Open-Energy-Methods/PtXFlex","-n","private-F3D-entsoe-original-$y-NOT-releasable","-D",$dest)
     } else { Write-Host "Price folder exists and was NOT overwritten: $dest" }
   }
   $source=Join-Path $PrivateRoot "pynexus-original-2023-netcdf"
   if(-not (Test-Path $source)) {
     Ensure $source
     Run "gh" @("run","download","40230838449","-R","abhijith-sivaprasadan/PyNEXUS","-n","wp1-cds-2023-primary-monthly-netcdf","-D",$source)
   }
   Write-Host "Original ENTSO-E and 2023 ERA5 retrieved. Do not commit private files."
 }
 "Recover2023" {
   $dest=Join-Path $PrivateRoot "wind-2023-recovered"
   if(Test-Path $dest) {
     Need (Verified2023Recovery) "2023 original restoration exists but is not certified: do not overwrite"
     Write-Host "Original 2023 CDS source already recovered and SHA verified (8,760 UTC hours); reused without overwriting"
   } else {
     Run $python @("-m","ptxflex.f3d_era5_sharded_acquisition","--year","2023","--seed-original-2023-folder",(Join-Path $PrivateRoot "pynexus-original-2023-netcdf"),"--output",$dest)
     Need (Verified2023Recovery) "Original 2023 restoration did not pass all source hashes"
     Write-Host "Original 2023 CDS source recovery passed 8,760 UTC hours and 12 monthly NetCDF SHA checks"
   }
 }
 "PilotARCO" {
   # A separate OFFICIAL Copernicus ARCO fast-point access test. Does not
   # replace authoritative 2023 CDS or produce 2022/2024 source artifacts.
   Need (Verified2023Recovery) "Original source-verified 2023 CDS required before testing ARCO"
   $reference=Join-Path $PrivateRoot "wind-2023-recovered\complete\original_monthly_netcdf\era5_2023_01_u10_v10_u100_v100.nc"
   Need (Test-Path $reference -PathType Leaf) "Missing January 2023 original source for ARCO calibration"
   $output=Join-Path $PrivateRoot "arco-2023-jan-point-calibration-private.json"
   Need (-not (Test-Path $output)) "Original ARCO source-comparison report already exists; preserve before a new test"
   Write-Host "Installing Copernicus ARCO Zarr client locally (NO GitHub Actions minutes)"
   Run $python @("-m","pip","install","zarr>=3,<4","fsspec>=2024.0","aiohttp>=3.9")
   $secure=Read-Host "Copernicus CDS API access token for official ARCO point pilot (hidden)" -AsSecureString
   try {
     $credential=[System.Management.Automation.PSCredential]::new("cds",$secure)
     $env:ERA5_API_KEY=$credential.GetNetworkCredential().Password
     Need ($env:ERA5_API_KEY.Length -gt 10) "CDS token missing"
     Run $python @("-m","ptxflex.f3d_era5_arco_pilot","--original-jan",$reference,"--output",$output)
   } finally {
     Remove-Item Env:ERA5_API_KEY -ErrorAction SilentlyContinue
     Remove-Variable secure,credential -ErrorAction SilentlyContinue
   }
   Write-Host "ARCO January 2023 compared to REAL original source, read private report:" $output
 }
 "CalibrateARCO2023" {
   Need (Verified2023Recovery) "The 12 original CDS 2023 NetCDFs must be source verified"
   $pilot=Join-Path $PrivateRoot "arco-2023-jan-point-calibration-private.json"
   Need (Test-Path $pilot -PathType Leaf) "Run PilotARCO original January source comparison first"
   $pilotReport=Get-Content -LiteralPath $pilot -Raw | ConvertFrom-Json
   Need ($pilotReport.status -eq "JAN2023_1W_CALIBRATION_PASS_ONLY_FULL_YEAR_NOT_YET_VALIDATED" -and
         $pilotReport.ARCO_Jan2023_wind_1W_quantized_matches_original_CDS_for_every_hour -eq $true) "The real original January ARCO/Copernicus test has not passed"
   $dest=Join-Path $PrivateRoot "wind-arco-2023-calibration"
   Need (-not (Test-Path $dest)) "Do not overwrite original whole-year ARCO calibration. Review the existing provenance."
   $original=Join-Path $PrivateRoot "wind-2023-recovered\complete\original_monthly_netcdf"
   $secure=Read-Host "CDS API token for ARCO 8760h original-source validation (hidden)" -AsSecureString
   try {
     $credential=[System.Management.Automation.PSCredential]::new("cds",$secure)
     $env:ERA5_API_KEY=$credential.GetNetworkCredential().Password
     Need ($env:ERA5_API_KEY.Length -gt 10) "CDS personal API key missing"
     Run $python @("-m","ptxflex.f3d_era5_arco_year",
       "--year","2023","--reference-original-2023-netcdf-folder",$original,
       "--output",$dest)
   } finally {
     Remove-Item Env:ERA5_API_KEY -ErrorAction SilentlyContinue
     Remove-Variable secure,credential -ErrorAction SilentlyContinue
   }
   $out=Get-Content -LiteralPath (Join-Path $dest "provenance.json") -Raw | ConvertFrom-Json
   Need ($out.status -eq "ARCO_FULL_2023_8760H_CDS_NUMERICALLY_EQUIVALENT_1W" -and
         $out.modelled_wind_1W_identical_hours -eq 8760 -and
         $out.full_8760h_2023_ARCO_matches_CDS_model_at_1W_and_four_component_tolerance -eq $true) "Full original 2023 ARCO source equivalence did not pass; do not use alternative years"
   Write-Host "FULL 2023 ARCO-to-CDS 8,760h and all four wind components verified"
 }
 { $_ -eq "FetchARCO2022" -or $_ -eq "FetchARCO2024" } {
   $year=if($Phase -eq "FetchARCO2022"){2022}else{2024}
   $cal=Join-Path $PrivateRoot "wind-arco-2023-calibration\provenance.json"
   Need (Test-Path $cal -PathType Leaf) "First perform CalibrateARCO2023 across ALL 8,760 original source hours"
   $proof=Get-Content -LiteralPath $cal -Raw | ConvertFrom-Json
   Need ($proof.status -eq "ARCO_FULL_2023_8760H_CDS_NUMERICALLY_EQUIVALENT_1W" -and
         $proof.modelled_wind_1W_identical_hours -eq 8760 -and
         $proof.full_8760h_2023_ARCO_matches_CDS_model_at_1W_and_four_component_tolerance -eq $true) "Not original full-year CDS-to-ARCO calibrated; no alternate source year allowed"
   $target=Join-Path $PrivateRoot "wind-arco-$year"
   Need (-not (Test-Path $target)) "Do not overwrite original $year ARCO point acquisition; inspect and preserve previous output"
   $secure=Read-Host "CDS ARCO personal access token (hidden)" -AsSecureString
   try {
     $credential=[System.Management.Automation.PSCredential]::new("cds",$secure)
     $env:ERA5_API_KEY=$credential.GetNetworkCredential().Password
     Need ($env:ERA5_API_KEY.Length -gt 10) "CDS token missing"
     Run $python @("-m","ptxflex.f3d_era5_arco_year",
       "--year","$year","--verified-2023-ARCO-calibration",$cal,"--output",$target)
   } finally {
     Remove-Item Env:ERA5_API_KEY -ErrorAction SilentlyContinue
     Remove-Variable secure,credential -ErrorAction SilentlyContinue
   }
   Write-Host "Fast ARCO whole-year source acquired: $year. Next VerifyARCO$year; independent source checks are mandatory."
 }
 { $_ -eq "VerifyARCO2022" -or $_ -eq "VerifyARCO2024" } {
   $year=if($Phase -eq "VerifyARCO2022"){2022}else{2024}
   $out=Join-Path $PrivateRoot "results\source-pair-ARCO-$year.json"
   Need (-not (Test-Path $out)) "Cannot overwrite already audited alternative provider year"
   Ensure (Split-Path $out -Parent)
   Run $python @("-m","ptxflex.f3d_live_provider_pair_gate",
     "--year","$year",
     "--price-root",(Join-Path $PrivateRoot "price-$year"),
     "--wind-root",(Join-Path $PrivateRoot "wind-arco-$year"),
     "--reference-price-root",(Join-Path $PrivateRoot "price-2023"),
     "--reference-wind-root",(Join-Path $PrivateRoot "wind-2023-recovered\complete"),
     "--output",$out)
   Write-Host "REAL $year provider A44 price + independent 2023-calibrated ARCO wind pair verified."
 }
 { $_ -eq "SolveARCO2022" -or $_ -eq "SolveARCO2024" } {
   $year=if($Phase -eq "SolveARCO2022"){2022}else{2024}
   Need (Test-Path (Join-Path $PrivateRoot "results\source-pair-ARCO-$year.json")) "VerifyARCO$year must pass before any annual source-year MILP"
   foreach($mode in @("max_inventory","usable_service")){
     $result=Join-Path $PrivateRoot ("results\F3D_ARCO_{0}_{1}.json" -f $year,$mode)
     $witness=Join-Path $PrivateRoot ("results\PRIVATE_F3D_ARCO_{0}_{1}_primal.json" -f $year,$mode)
     Need (-not (Test-Path $result) -and -not (Test-Path $witness)) "Do not overwrite a prior annual source-certified MILP or private primal"
     Run $python @("-m","ptxflex.f3d_year_matched_service",
       "--year","$year","--mode",$mode,
       "--price-root",(Join-Path $PrivateRoot "price-$year"),
       "--wind-root",(Join-Path $PrivateRoot "wind-arco-$year"),
       "--reference-price-root",(Join-Path $PrivateRoot "price-2023"),
       "--reference-wind-root",(Join-Path $PrivateRoot "wind-2023-recovered\complete"),
       "--selection-time-limit","3600","--dispatch-time-limit","3600",
       "--private-witness-out",$witness,"--output",$result)
   }
 }
 "ReviewARCO" {
   $resultroot=Join-Path $PrivateRoot "results"
   $reports=@()
   foreach($year in @(2022,2024)){
     foreach($mode in @("max_inventory","usable_service")){
       $report=Join-Path $resultroot ("F3D_ARCO_{0}_{1}.json" -f $year,$mode)
       $witness=Join-Path $resultroot ("PRIVATE_F3D_ARCO_{0}_{1}_primal.json" -f $year,$mode)
       Need (Test-Path $report -PathType Leaf) "Source-year ARCO MILP aggregate report missing"
       Need (Test-Path $witness -PathType Leaf) "Private ARCO primal witness missing"
       $reports+=@($report)
       $review=Join-Path $resultroot ("PtXLens_ARCO_{0}_{1}_physical.json" -f $year,$mode)
       Need (-not (Test-Path $review)) "Do not overwrite an existing source-year independent physical review"
       Run $python @("-m","ptxlens.f3d_external_year_private_witness_replay",
         "--witness",$witness,"--aggregate-report",$report,
         "--private-price",(Join-Path $PrivateRoot "price-$year\normalized_UTC_price.csv"),
         "--private-wind",(Join-Path $PrivateRoot "wind-arco-$year\normalized_UTC_wind.csv"),
         "--output",$review)
     }
   }
   $combined=Join-Path $resultroot "PtXLens_four_case_ARCO_years_independent.json"
   Need (-not (Test-Path $combined)) "Cannot overwrite an existing independent 4-case review"
   $argv=@("-m","ptxlens.f3d_external_year_independent_review","--files")+$reports+@("--output",$combined)
   Run $python $argv
   Write-Host "Independent source-proven physical/primal and dual economic source-year review completed; no site or v1 release implied."
 }
 { $_ -eq "Fetch2022" -or $_ -eq "Fetch2024" } {
   $year=if($Phase -eq "Fetch2022"){2022}else{2024}
   Need ($Month -ge 0 -and $Month -le 12) "Month must be 0 (all months) or 1..12"
   $range=if($Month -eq 0){@(1..12)}else{@($Month)}
   $secure=Read-Host "Copernicus CDS personal access token (input hidden)" -AsSecureString
   try {
     $credential=[System.Management.Automation.PSCredential]::new("cds",$secure)
     $env:ERA5_API_KEY=$credential.GetNetworkCredential().Password
     Need ($env:ERA5_API_KEY.Length -gt 10) "CDS token missing"
     foreach($month in $range){
       if(SourceOK $year $month){ Write-Host "REUSED verified $year month $month";continue }
       $dest=MonthRoot $year $month
       Write-Host "CDS REAL source request $year month $month; no Github Actions used."
       Run $python @("-m","ptxflex.f3d_era5_sharded_acquisition","--year","$year","--month","$month","--output",$dest)
     }
   } finally {
     Remove-Item Env:ERA5_API_KEY -ErrorAction SilentlyContinue
     Remove-Variable secure,credential -ErrorAction SilentlyContinue
   }
 }
 { $_ -eq "Assemble2022" -or $_ -eq "Assemble2024" } {
   $year=if($Phase -eq "Assemble2022"){2022}else{2024}
   $stage=Join-Path $PrivateRoot "stage-$year"
   $dest=Join-Path $PrivateRoot "wind-$year"
   Need (-not (Test-Path $stage) -and -not (Test-Path $dest)) "Source stage/output already exists. Preserve and inspect existing evidence."
   foreach($month in 1..12) { Need (SourceOK $year $month) "Missing verified original ERA5 month $year/$month" }
   $raw=Join-Path $stage "original_monthly_netcdf"
   Ensure $raw
   foreach($month in 1..12) {
     $name=("era5_{0}_{1:d2}_u10_v10_u100_v100.nc" -f $year,$month)
     $source=Join-Path (MonthRoot $year $month) (Join-Path "original_monthly_netcdf" $name)
     Copy-Item -LiteralPath $source -Destination (Join-Path $raw $name)
     Need ((Get-FileHash $source -Algorithm SHA256).Hash -eq (Get-FileHash (Join-Path $raw $name) -Algorithm SHA256).Hash) "Original NetCDF copy changed bytes"
   }
   Run $python @("-m","ptxflex.f3d_era5_sharded_acquisition","--year","$year","--assemble-input",$stage,"--output",$dest)
 }
 { $_ -eq "Verify2022" -or $_ -eq "Verify2024" } {
   $year=if($Phase -eq "Verify2022"){2022}else{2024}
   $result=Join-Path $PrivateRoot "results\source-pair-$year.json"
   Need (-not (Test-Path $result)) "Source pair audit already exists"
   Ensure (Split-Path $result -Parent)
   Run $python @("-m","ptxflex.f3d_live_provider_pair_gate","--year","$year","--price-root",(Join-Path $PrivateRoot "price-$year"),"--wind-root",(Join-Path $PrivateRoot "wind-$year"),"--reference-price-root",(Join-Path $PrivateRoot "price-2023"),"--reference-wind-root",(Join-Path $PrivateRoot "wind-2023-recovered\complete"),"--output",$result)
 }
 { $_ -eq "Solve2022" -or $_ -eq "Solve2024" } {
   $year=if($Phase -eq "Solve2022"){2022}else{2024}
   Need (Test-Path (Join-Path $PrivateRoot "results\source-pair-$year.json")) "Verify original source price/wind before optimizing"
   foreach($mode in @("max_inventory","usable_service")) {
     $result=Join-Path $PrivateRoot ("results\F3D_{0}_{1}.json" -f $year,$mode)
     $witness=Join-Path $PrivateRoot ("results\PRIVATE_F3D_{0}_{1}_primal.json" -f $year,$mode)
     Need (-not (Test-Path $result) -and -not (Test-Path $witness)) "Do not overwrite result or private original primal"
     Run $python @("-m","ptxflex.f3d_year_matched_service","--year","$year","--mode",$mode,"--price-root",(Join-Path $PrivateRoot "price-$year"),"--wind-root",(Join-Path $PrivateRoot "wind-$year"),"--reference-price-root",(Join-Path $PrivateRoot "price-2023"),"--reference-wind-root",(Join-Path $PrivateRoot "wind-2023-recovered\complete"),"--selection-time-limit","3600","--dispatch-time-limit","3600","--private-witness-out",$witness,"--output",$result)
   }
 }
 "Review" {
   $out=Join-Path $PrivateRoot "results"
   $reports=@()
   foreach($year in @(2022,2024)) {
     foreach($mode in @("max_inventory","usable_service")) {
       $report=Join-Path $out ("F3D_{0}_{1}.json" -f $year,$mode)
       $witness=Join-Path $out ("PRIVATE_F3D_{0}_{1}_primal.json" -f $year,$mode)
       Need ((Test-Path $report) -and (Test-Path $witness)) "All four annual source-year/mode cases required"
       $reports+=@($report)
       $review=Join-Path $out ("PtXLens_{0}_{1}_physical.json" -f $year,$mode)
       Need (-not (Test-Path $review)) "Do not overwrite private independent review"
       Run $python @("-m","ptxlens.f3d_external_year_private_witness_replay","--witness",$witness,"--aggregate-report",$report,"--private-price",(Join-Path $PrivateRoot "price-$year\normalized_UTC_price.csv"),"--private-wind",(Join-Path $PrivateRoot "wind-$year\normalized_UTC_wind.csv"),"--output",$review)
     }
   }
   $meta=Join-Path $out "PtXLens_four_case_metadata.json"
   Need (-not (Test-Path $meta)) "Do not overwrite previously independent source review"
   $args=@("-m","ptxlens.f3d_external_year_independent_review","--files")+$reports+@("--output",$meta)
   Run $python $args
 }
 "Status" {
   Write-Host "Private original provider data: $PrivateRoot"
   Write-Host "PtXFlex Python environment installed:" (Test-Path $python)
   try {
     $ok=Verified2023Recovery
     Write-Host "Original 2023 wind independently source-hash verified:" $ok
   } catch {
     Write-Warning ("Original 2023 source is NOT scientifically admitted: " + $_.Exception.Message)
     Write-Host "Original 2023 wind independently source-hash verified:" $false
   }
   $cal=Join-Path $PrivateRoot "wind-arco-2023-calibration\provenance.json"
   if(Test-Path $cal -PathType Leaf){
     $p=Get-Content -LiteralPath $cal -Raw | ConvertFrom-Json
     Write-Host "ARCO 2023 original full-year 8,760-hour calibration status:" $p.status
     Write-Host "ARCO 2023 original model 1W matched hours:" $p.modelled_wind_1W_identical_hours
   } else {
     Write-Host "ARCO full-year 2023 calibration: NOT RUN (January-only pilot does NOT count)"
   }
   foreach($year in @(2022,2024)){
     $filename=Join-Path $PrivateRoot ("wind-arco-$year\provenance.json")
     if(Test-Path $filename -PathType Leaf){
       $p=Get-Content -LiteralPath $filename -Raw | ConvertFrom-Json
       Write-Host "ARCO $year complete UTC-hour source status:" $p.status
     } else { Write-Host "ARCO $year source: NOT ACQUIRED" }
   }
   foreach($year in @(2022,2024)) {
     $passed=0
     foreach($m in 1..12){ try { if(SourceOK $year $m){$passed++} } catch { Write-Warning ("Unverified source month {0}-{1:d2}: {2}" -f $year,$m,$_.Exception.Message) } }
     Write-Host "ERA5 $year months verified: $passed / 12"
   }
 }
}

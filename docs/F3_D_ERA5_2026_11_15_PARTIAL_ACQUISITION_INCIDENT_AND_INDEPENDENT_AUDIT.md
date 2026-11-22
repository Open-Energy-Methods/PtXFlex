# F3-D ERA5 original-source acquisition incident — 2026-11-15 UTC

**Status: SOURCE BLOCKED; F3 NOT PASSED.** This record is a diagnostic of a private provider workflow, not acceptance of a weather year.

- Workflow: https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43617006319 (attempt 2).
- ERA5 2023 job 132545576772: 2023 Jan (744h), Feb (672h), Mar (744h), Apr (720h) each printed `Verified ERA5 raw month`. Total **2,880 / 8,760 UTC hours**. Job started 2026-11-14 18:32:37 UTC and was **cancelled** 2026-11-15 00:12:54 UTC; log says `The operation was canceled.` at 00:12:50. No May–December acceptance.
- ERA5 2022 job 132545576809: **failure**; ERA5 2024 job 132545576501: **failure**. The log-fetch connector returned 404 BlobNotFound for both, so **their root cause is not independently established**. Do not infer that both were timeouts or provider refusals.
- ENTSO-E 2022/2023/2024 jobs succeeded. Historical source-pair gate skipped.
- The ERA5 2023 cancellation uploaded temporary private **partial** artifact 14138157971, archive SHA256 `b3c5b40fbf0eeb03497e018b23d2e64d5867f7fee4d2de44ad9cc793098a46ab` (ZIP digest reported by GitHub; **not** an annual wind SHA), size 312,023 bytes, retention 7 days. This is neither durable preservation nor a completed annual input.
- The ERA5 workflow has `timeout-minutes: 340`, and retrieves 12 months sequentially per year. The 2023 job reached only four months before cancellation; the exact initiator of cancellation is not established. A fresh identical run is not a scientific resolution of the throughput limitation.

## Independent offline partial integrity control

`src/ptxflex/f3d_private_era5_partial_audit.py` accepts only an authorized local private artifact directory. It independently rehashes every present monthly NetCDF byte stream, checks chronological filenames, month-specific UTC lengths, original grid and four-field completion flags, and rejects incomplete archives falsely claiming annual completion or a 2023 reference match. It **does not** infer that NetCDF contents have been independently redecoded, prove the frozen wind transformation, or expose raw weather observations. Nine hermetic synthetic tests cover four-month chronology, leap February, tampering, missing/unordered months, false annual claim, wrong grid, frozen-hash false positive and wrong year.

**Actual private artifact not downloaded or audited by this increment.** Its logged four-month status is therefore not a verified 2023 source series. The tool always reports `admitted_as_observed_full_year: false` even for a complete file collection, because the separate source-pair gate must authenticate transformed annual values against the frozen PyNEXUS hash.

## Recovery gate

1. Retrieve private temporary partial artifact to user-controlled encrypted storage before its 7-day expiry, separately from original frozen 2023 source preservation (P0).
2. Inspect 2022/2024 failed job logs from an authorized runner or GitHub UI; establish actual failure cause before retry.
3. Redesign acquisition as bounded month-level resumable jobs with per-month checksums, authorized private staging and explicit no-overwrite semantics. Do not use public artifacts for licensed raw observations.
4. Independently reconstruct all 12 months and the exact 2023 SHA `abbfea17224cd92f694ed26b7a179ef7e35fff5a5bb17c6ee060a674c1977717` before admitting 2022/2024, leap-year transformations or MILP comparisons.

F2/L1 physical vessel and complete installed equipment evidence remain outstanding; all complete F3/LCA/TEA/v1.0 gates remain NOT PASSED. No industrial site measurement or environmental comparison is implied.

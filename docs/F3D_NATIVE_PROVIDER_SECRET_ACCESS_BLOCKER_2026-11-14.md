# F3-D native-provider acquisition blocker — 2026-11-14 16:48 UTC

Programme: OEM-PTX-2026-01. This is an execution record, **not** evidence of 2022/2024 observed-year admission, source equivalence, or physical H2 service.

## Reproducible GitHub evidence

At inspection, branch `feat/milp-methanol-baseline` head was `9b86413a3a9e7f0279020ddc70bd07d54c0edccb`.

- [Native-provider workflow run 43617006319](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43617006319) concluded **failure**. The independent no-network test job succeeded.
- The three ENTSO-E jobs (2023, 2022, 2024) each failed at `Require authorized ENTSO-E organization secret`, before provider retrieval.
- The three ERA5 jobs (2023, 2022, 2024) each failed at `Require Copernicus CDS organization secret and dataset authorization`, before provider retrieval.
- The historical source-pair gate was **skipped**.
- [PtXFlex verification run 43617010665](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43617010665) succeeded; this does not override the failed native-provider workflow.
- [PtXLens verification run 43615044005](https://github.com/Open-Energy-Methods/PtXLens/actions/runs/43615044005) succeeded.

## Diagnosis and required custodian action

The workflow `.github/workflows/f3d-live-entsoe-era5-2022-2024.yml` explicitly binds `secrets.ENTSOE_API_KEY` and `secrets.ERA5_API_KEY`. Its preflight exits when the corresponding environment value is empty. This demonstrates **secret unavailability in these jobs**, not absence of secrets from the organization and not provider API rejection. Organization-level secret access policy, selected-repository permissions, and workflow authorization must be checked by a custodian without printing token values. Re-run the same native workflow after correcting access. Only then inspect provider request responses, document original bytes and SHA manifests, and independently verify 2023 float64 source equality before admitting 2022/2024 source pairs.

Do **not** replace official observations with generated arrays or mark F3-D, P0, F3, L2/L3, or v1.0 passed. Private raw provider data and secrets must not be committed. Source artifact recovery and independently verified backups remain separate P0 requirements.

# P0 private PyNEXUS escrow alias integrity — 2026-11-14

Programme OEM-PTX-2026-01. Scope: private archive verification code only; **no original 2023 PyNEXUS data accessed, downloaded, copied to GitHub or redistributed**.

## Defect and correction

The pre-existing `verify_pair` implementation required distinct directories and compared resolved paths, SHA-256 and ZIP CRC. A hard link under a second pathname shares the *same filesystem inode* and can satisfy those checks without creating a second independently recoverable copy. A symbolic link likewise is not a backup. The verifier now rejects archive symlinks and identical `(st_dev, st_ino)` pairs in addition to resolved-path aliases. Synthetic ZIP regression tests cover hard links, symbolic links and real copied files.

This is a **necessary file-alias check, not proof of independent physical media**. Even distinct device IDs can represent virtual mounts or storage sharing a physical failure domain. Human inspection of separate physical devices, independent restore testing, legal access, archive SHA/CRC and scientific signoff remain mandatory. The verifier's `independent_physical_storage_device_verified` and `full_P0_release_gate_passed` remain false.

## Provenance and tests

- Baseline: both repos' master-plan, decision-register and gate JSON Git blob hashes matched on 2026-11-14.
- Before edits, latest checked PtXFlex CI [43591783270](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43591783270) and PtXLens CI [43592026166](https://github.com/Open-Energy-Methods/PtXLens/actions/runs/43592026166) completed successfully.
- Code commit: [1203b720](https://github.com/Open-Energy-Methods/PtXFlex/commit/1203b720e0e58ac508db9b6faa7c66556ab79842).
- Regression commit: [0058425d](https://github.com/Open-Energy-Methods/PtXFlex/commit/0058425dd14de88e93c88d925ebdb293ad02b96c).
- New test commit CI: [43596762269](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43596762269), **queued at initial observation; result must be checked**. No passing assertion for this commit until confirmed.

## Unresolved gate

P0 remains NOT_PASSED. The original E/E+S/A44 archives are not verified in lawful private primary and physically independent recoverable secondary media. The earliest registered original Actions artifact expires 2026-12-24 19:24:29 UTC; archival is time-critical. F2/L1 still lack manufacturer-certified complete station BOM, compressor, pressure-cycle/safety/site qualification and compatible native BAFU steel-vessel manufacturing functional unit. F3 full original 18.25mkg industrial H₂ service, L2/L3 and v1.0 review remain open. This change neither affects the 2023 numerical model nor closes an LCA/TEA gate.

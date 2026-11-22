# F3-D independent observed Dutch price audit — 2022–2024

Date: 2026-11-14. Original 14-document Dutch A44 XML source artifacts were downloaded from [F3-D native provider acquisition workflow run 43617006319](https://github.com/Open-Energy-Methods/PtXFlex/actions/runs/43617006319), attempt 4. The ENTSO-E source download jobs succeeded for all three calendar years; the corresponding source artifacts are private and must not be released without provider licence review.

Independently inspected original artifacts `private-F3D-entsoe-original-{year}-NOT-releasable`: ZIP CRC, 14 original provider documents per year, exact SHA-256 and byte size of every original XML against the archive's own manifest, and strict UTC calendar timestamps of all normalized hourly price records.

| Source-observed year | UTC hours | Mean EUR/MWh | Min EUR/MWh | Max EUR/MWh | Negative price hours | Normalized float64-le SHA-256 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2022 | 8,760 | 241.909755 | -222.36 | 871.00 | 86 | `1a5490fd607d6c786878ca56b5d82ce8568f62b5277bc201206f1e6761b04f28` |
| 2023 | 8,760 | 95.817771 | -500.00 | 463.77 | 315 | `e67f59598079303df0c51a553904d2352a939ed7439af73ccbfb3daab9d667b6` |
| 2024 | 8,784 | 77.289214 | -200.00 | 872.96 | 458 | `834449561032a1c81f76950fd49b1b0276f6cd27b4a0e07e9188a09144574fce` |

The independently read original 2023 price SHA exactly equals the registered frozen original PyNEXUS hourly-market benchmark. These are strictly **descriptive annual source-price observations** (arithmetic hourly means, no demand weighting), not inflation-adjusted prices, predictions, time-series weather matching, operational dispatch simulations or a storage-investment argument. All three market price records include genuine negative prices; optimizer objective treatment must retain these signed values and must not clip them to zero.

## Scientific release gates

- ENTSO-E NL 2022/2023/2024 source-purity and full UTC calendar: **locally verified**.
- Source A03 XML-versus processed hour-by-hour price equality: **independently verified for 2022/2023/2024.** All original source documents were reparsed from XML, source-encoded A03/A01 price blocks expanded to 15-minute resolution, then strictly compared against all 8,760 / 8,760 / 8,784 UTC normalized price hours: **zero mismatches for each year**. Original manifests and all 42 individual XML document hashes were also verified. These checks are independent of the retrieval-side normalized CSV generator.
- ERA5 2023 original wind SHA reproduction: **pending**.
- 2022/2024 complete joint ERA5/A44 observed source-year input: **pending**.
- Proper source-year physically feasible matched hourly H₂ service and independently certified E and E+S MILP solver comparison: **not yet done**.
- Stage F3-D / PtXLens investment viability / whole-plant native BAFU 2026 v1.1: **not released**.

## Preservation

Private source ZIPs uploaded in owner-only Google Drive folder for user's archival access: https://drive.google.com/drive/folders/1DUUCaClrNXnNPrz6XWCGviHWup7NOOP_. This is one storage location (not a demonstrated independent two-media P0 recovery test). All original XML/hourly arrays stay out of the repository.

The complete summary and independent XML comparison are reproducible from original artifact ZIP manifests and `normalized_UTC_price.csv` under strictly private original-source storage. Do not infer observed annual provider sources from the 2023 source-derived F3-D controlled perturbations, and do not claim a full source provenance chain solely from internal manifests.

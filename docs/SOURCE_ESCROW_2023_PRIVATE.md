# P0 — preserve the original 2023 PyNEXUS evidence privately, before archive expiration

## RC2-A — 18 November 2026 readback update

All three already-stored private owner copies were freshly retrieved, SHA256 checked against the original registry, and passed ZIP CRC. All three were also live-verified as unexpired with matching API digests. See the [RC2 custody protocol](RC2_SOURCE_CUSTODY_AND_SCIENTIFIC_GOVERNANCE_2026-11-18.md). The historical record below is retained; new primary readback proof does NOT establish a permanent independent backup or legal rights. Adopt the existing original ZIPs locally with `--adopt-verified-local` and run the secondary recovery with `--restore-into` as documented. P0 remains NOT_PASSED.


## Live GitHub retention verification — 14 November 2026

The three original source ZIP artifact records were queried **directly through GitHub Actions' workflow-run artifact listing API** on 14 November 2026. All three currently report **`expired=false`** with these authoritative point-in-time expiry timestamps (UTC):

| Original source | Artifact ID | Current `expires_at` UTC | `expired` |
|---|---:|---|---|
| 2023 original E model (run 40229852457) | 12612294862 | 2026-12-24 **20:18:09Z** | false |
| 2023 original E+S model (run 40229852457) | 12613045475 | 2026-12-24 **20:21:57Z** | false |
| 2023 original ENTSO-E A44 provider XML (run 40225702504) | 12610917985 | 2026-12-24 **19:24:29Z** | false |

**Earliest documented original-source archive expiry:** **24 December 2026, 19:24:29 UTC** (the A44 original market provider XML). These dates are live-verified repository API metadata **as of 14 November**, not permanent promises of retention and not preservation evidence. Store lawfully in a PRIVATE user-controlled primary location and a physically independently reviewed backup with a tested recovery path well before this date. The GitHub REST artifact ZIP download is a temporary archive wrapper around the original published contents and must be interpreted using the frozen original SHA-256/ZIP verification script, not as a new immutable source.

The cross-repository [machine-readable metadata snapshot](../research/P0_2023_PyNEXUS_original_actions_artifacts_live_status_2026-11-14.json) records the source artifact name/id, size and expiry but contains **no original market/provider data**. **Not yet performed here:** actual long-term private copy/recovery, independent storage-device validation, original source licence clearance or signed independent critical review. **P0 release remains NOT PASSED.**


**Deadline to recover original GitHub Actions artifacts:** **2026-12-24** (per original source registry).  
**Scientific status:** F1 annual electricity/H₂/price/wind source reconstruction is CI-verified. Long-term original-source availability remains a **P0 release gate**, not something source fingerprints alone can guarantee.

### Source archives that must remain byte-identical

| Original | GitHub Actions artifact ID | SHA256 |
|---|---:|---|
| E original 2023 Stage A/B and record | 12612294862 | \`069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051\` |
| E+S original 2023 Stage A/B and record | 12613045475 | \`cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9\` |
| Original Dutch ENTSO-E A44 2023 XML | 12610917985 | \`bc1751b86a3fe712ac2713985c4e189c922a031bacb53a7bd8f422809ba24248\` |

Original [PyNEXUS source workflow](https://github.com/abhijith-sivaprasadan/PyNEXUS/actions/runs/40229852457). Source licensing and permitted redistribution remain with ENTSO-E/ERA5 data providers; the original provider XML must not be published without verifying those conditions.

## Secure local retrieval

**Run on the user's computer** (Windows PowerShell shown), outside the Git checkout, with a GitHub personal token that has sufficient access to the original upstream repository's Actions artifacts:

~~~powershell
# From PtXFlex repo root after cloning the development branch
$env:GH_TOKEN = Read-Host "GitHub token" -AsSecureString |
  ForEach-Object { [System.Net.NetworkCredential]::new("", $_).Password }

python scripts/preserve_pynexus_evidence.py --destination "D:\PrivateResearch\PyNEXUS_original_2023"

# After the first retrieval, confirm exact source ZIP SHA256/CRC offline.
python scripts/preserve_pynexus_evidence.py --destination "D:\PrivateResearch\PyNEXUS_original_2023" --verify-only

# Clear the token from this shell.
Remove-Item Env:GH_TOKEN
~~~

This code **will not** save original data inside the GitHub repository working tree. It rejects unmatched archive hashes, invalid ZIP CRC, unexpected source download and accidental overwriting of an inconsistent source. It does not upload or publish any of the raw source records. The GitHub credential must never be stored in a script, JSON result or git history.

Keep a *second local private backup* with a cryptographically verified checksum on different storage, subject to the original source licences. Re-run \`--verify-only\` after moving the original files. For collaborators who cannot be supplied raw provider data under their licence, publish derived permitted summaries, unit/operation code and a source-acquisition recipe instead.

**Do not call P0 PASSED until** both E and E+S original ZIPs and original A44 provider archive have been independently verified and preserved in appropriate lawful archival storage, with a documented recovery test and who can access them. GitHub Actions' temporary artifact retention is not archival preservation.


## P0 update — two-copy private recovery control (14 November 2026)

The existing [original archive preservation script](../scripts/preserve_pynexus_evidence.py) verifies the **original frozen SHA256 and ZIP CRC** for E, E+S and original A44 XML, and creates a private, non-Git manifest. A [second independent offline verification tool](../scripts/verify_private_pynexus_recovery.py) now checks whether a separate copy of **all three** original archives can be restored byte-identically. It rejects a missing primary manifest, altered SHA, bad ZIP, missing archive, incompatible reference, same/nested directory and unknown licence status. It does **not** upload any provider source records.

From the PtXFlex development branch on Windows PowerShell **after the original private primary archive has been retrieved**:

~~~powershell
# Example: first private copy on D:, second external private volume E:
python scripts/verify_private_pynexus_recovery.py `
  --primary "D:\PrivateResearch\PyNEXUS_original_2023" `
  --secondary "E:\IndependentResearchBackup\PyNEXUS_original_2023" `
  --copy-secondary `
  --strict-different-device

# Repeat without copy, to perform an independent recovery/verification later.
python scripts/verify_private_pynexus_recovery.py `
  --primary "D:\PrivateResearch\PyNEXUS_original_2023" `
  --secondary "E:\IndependentResearchBackup\PyNEXUS_original_2023" `
  --strict-different-device
~~~

**Filesystem-vs-physical-device limitation:** The `--strict-different-device` switch checks that the two paths have *different filesystem device identifiers* (and rejects identical/nested locations). This does **NOT** prove that the files reside on different physical drives: two partitions on one disk can have separate filesystem identifiers, and cloud/synchronized directories may have other storage semantics. The script now explicitly records `independent_physical_storage_device_verified=false` and requires independent/manual inspection of drive identity, versioning, offline restoration and administrative access controls. Use actual independently identifiable physical/cloud media and perform a separate recovery test before claiming redundant storage. It remains a syntactic/cryptographic verification helper, not a certification of disaster recovery.\n\nThe tool deliberately **does not certify legal rights or mark P0 PASSED**: `full_P0_release_gate_passed=false` and `licence_conditions_and_permitted_redistribution_independently_reviewed=false` remain explicit even after two identical copies exist. Separate directories on a single physical filesystem are **not** an independent backup; the `--strict-different-device` flag fails rather than misreporting such a condition. A synchronized cloud location may need separate provider-side version/recovery evidence.

**Current state:** synthetic tests of the two-copy tool pass; no user-specific private destination was supplied, and the three original ZIP files have **not** been demonstrated as durably preserved in two independent private locations in this session. The existing register states a 2026-12-24 artifact expiry; this is the programme's documented retrieval deadline, **not a fresh live verification of GitHub retention policy**. An actual local verified primary + independent recovery copy, dated restoration test and licence review are still urgent P0 acceptance evidence. Never commit original ENTSO-E XML or other provider records to this public programme.

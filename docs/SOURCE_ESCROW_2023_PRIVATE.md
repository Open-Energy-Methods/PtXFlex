# P0 — preserve the original 2023 PyNEXUS evidence privately, before archive expiration

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

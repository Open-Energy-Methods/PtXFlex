# RC3 P0 source custody — execution and acceptance record (2026-11-22)

**Decision: NOT_PASSED.** This is a public metadata-only execution plan, **not** evidence that a user's private source bytes are stored or that legal reuse has been cleared.

## Original upstream material (frozen historical identifiers)

| Original archive | Upstream GitHub Actions artifact ID | Frozen original archive SHA-256 | Historical expiry UTC |
|---|---:|---|---|
| 2023 PyNEXUS E | 12612294862 | `069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051` | 2026-12-24 20:18:09 |
| 2023 PyNEXUS E+S | 12613045475 | `cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9` | 2026-12-24 20:21:57 |
| Original ENTSO-E NL A44 XML | 12610917985 | `bc1751b86a3fe712ac2713985c4e189c922a031bacb53a7bd8f422809ba24248` | 2026-12-24 19:24:29 |

Original workflows: [model source](https://github.com/abhijith-sivaprasadan/PyNEXUS/actions/runs/40229852457); [market source](https://github.com/abhijith-sivaprasadan/PyNEXUS/actions/runs/40225702504).

**Caution:** expiry dates are metadata observed **14 November 2026**, not refreshed here, and are not retention guarantees. The GitHub connector does not grant direct artifact-byte readback in this audit. No archive download, current expiry verification, or local independent restore was performed in this RC3 public review.

## Reconciled audit states

- **14 November, published snapshot:** `research/P0_2023_PyNEXUS_original_actions_artifacts_live_status_2026-11-14.json` correctly reports no verified two-location permanent preservation *as of that checkpoint*. Do not rewrite dated historical records.
- **18 November, RC2-A:** `docs/SOURCE_ESCROW_2023_PRIVATE.md` and `docs/RC2_SOURCE_CUSTODY_AND_SCIENTIFIC_GOVERNANCE_2026-11-18.md` report successful private owner-copy readback and matching frozen SHA256/ZIP CRC for all three files. This is stronger than the dated 14 November snapshot, **but does not establish an independent second physical backup**.
- **22 November, RC3:** public main-branch reproducibility workflows passed; P0 remains blocked for independent recovery evidence, lawful reuse review and external scientific review. CI success does not imply possession of original private bytes.

## Required private execution (Windows PowerShell)

Work only in an up-to-date **PtXFlex** checkout. Use two independently identified storage locations **outside all Git work trees**. Replace the example paths with actual private destinations. Avoid putting access tokens or raw provider sources in messages or public repositories.

```powershell
git switch main
git pull --ff-only origin main
python scripts/preserve_pynexus_evidence.py --help
python scripts/verify_private_pynexus_recovery.py --help

# If the three original, already SHA-verified ZIPs are on primary storage:
python scripts/preserve_pynexus_evidence.py --destination "D:\PrivateResearch\PyNEXUS_original_2023" --adopt-verified-local

# Otherwise follow docs/SOURCE_ESCROW_2023_PRIVATE.md for a
# credentialed upstream retrieval, only if still authorized/available.

python scripts/preserve_pynexus_evidence.py --destination "D:\PrivateResearch\PyNEXUS_original_2023" --verify-only

# Example: recover/copy into a separately verified external drive.
python scripts/verify_private_pynexus_recovery.py `
  --primary "D:\PrivateResearch\PyNEXUS_original_2023" `
  --secondary "E:\IndependentResearchBackup\PyNEXUS_original_2023" `
  --copy-secondary `
  --strict-different-device

# Disconnect/unmount secondary, reconnect it, and run an independent
# second readback rather than relying only on the initial copy step.
python scripts/verify_private_pynexus_recovery.py `
  --primary "D:\PrivateResearch\PyNEXUS_original_2023" `
  --secondary "E:\IndependentResearchBackup\PyNEXUS_original_2023" `
  --strict-different-device
```

**Physical independence is a separate manual finding.** Different filesystem IDs do not prove different physical devices. Record offline media / independent cloud account identity and recoverability through a controlled private inspection, not a public screenshot with device paths or account names. A cloud-synced folder alone is not independent storage.

## P0 acceptance checklist

- [ ] All three original archives verified against frozen original SHA-256 **and** ZIP CRC at the primary archive location; private verification report retained.
- [ ] All three verified at a separate private recovery location; test includes reading restored bytes independently after reconnect/remount.
- [ ] Independent storage hardware/provider, backup versioning and access restoration independently reviewed and documented privately.
- [ ] Provider licence and permissible storage, internal sharing and public redistribution independently reviewed; original ENTSO-E XML remains non-public unless independently authorized.
- [ ] Audit of archive-to-derived claims (E, E+S, A44) links frozen source digests to outputs without publishing protected provider data.
- [ ] Independent scientific reviewer signs evidence and scope; gate owner records decision in both repositories only after substantiation.
- [ ] No secrets, raw XML, source ZIPs, private local paths or privileged storage inventories added to public repository history.

## Public attestation format (metadata only)

When **actually completed**, record a dated, independently reviewed attestation stating: the three artifact IDs and SHA256 values above; primary checksum/CRC verified true; secondary restored checksum/CRC verified true; independent storage reviewed true; licence review conclusion with permissible public claims; reviewer role/date; and evidence retained in a controlled private archive. Do **not** publish drive paths, tokens, raw sources, private filenames beyond those already documented or unverified claims.

Until all required acceptance criteria are satisfied, keep `P0.gate_result = NOT_PASSED`, `P0.status = in_progress` and the scientific v1.0 release blocked. Do not automatically promote gates based on successful hash-only CI.

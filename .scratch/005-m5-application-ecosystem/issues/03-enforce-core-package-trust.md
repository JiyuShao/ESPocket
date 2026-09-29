# 03 — Enforce the Core-owned package trust gate

**What to build:** One public install path that verifies a complete remote package, commits transactionally and revalidates trusted state after reboot.

**Blocked by:** Upstream Core/Store seam and a compatible signed package route.

**Status:** needs-info

- [ ] Signature, member integrity and compatibility fail closed before unpacking.
- [ ] Update rollback and cleanup preserve the last trusted version.
- [ ] Reboot discovery rejects packages without a valid receipt.

## Required transaction shape

The public Core operation must lock or copy one immutable candidate, verify the optional source digest, release signature and signed members from those same bytes, validate compatibility, unpack into a new staging directory, prepare resources, write a pending receipt, atomically switch versions, validate the new App record, commit the receipt and only then remove the backup.

The receipt binds package/version identity, artifact and manifest digests, signing-key identity, policy version, committed members, Platform Baseline and transaction identity. Built-in packages use an explicit build allowlist rather than directory presence.

## Required matrix

- [ ] Reject digest mismatch, missing signature half, unknown key, modified or extra member and incompatible system before activation.
- [ ] Reject verify-to-unpack mutation and path escape.
- [ ] Preserve the old App and private data on every injected update failure or power-loss state.
- [ ] Remove receipt and matching cache on uninstall; clean orphan staging without deleting the committed version.
- [ ] Route Store, USB and any developer installer through the same gate.

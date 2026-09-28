# M5 Package Trust Gate

## Status

- Design: complete for the locked Brookesia 0.8.x baseline
- Enforcement: blocked by upstream integration gaps
- Product implementation: intentionally not added
- Private-key or signing operation: not performed
- M5 remains `BLOCKED`

This document defines the minimum trust boundary required before ESPocket may install remotely supplied Runtime Apps. It does not introduce a private package format, package manager, Store backend, or fork of a managed component.

## Security goal

A remotely supplied Runtime App may become installed or discoverable after reboot only when all of the following are true:

1. the downloaded `.bpk` bytes match the catalog's declared SHA-256;
2. the package contains a complete Brookesia release-signing pair;
3. Core verifies the release signature against an ESPocket-pinned public key;
4. every packaged member matches the signed `META-INF/hash.json`;
5. the manifest permits the exact `espocket` system type;
6. the package passes Core manifest, service, path, and GUI validation;
7. activation commits atomically, retaining the previous installed version until the new version is usable;
8. reboot discovery accepts only a built-in package or an installation carrying a valid Core-owned trust receipt.

TLS remains required, but TLS transport verification is not package publisher verification.

## Locked 0.8.x facts

### Existing reusable mechanisms

System Core 0.8.4 already provides:

```cpp
verify_app_package_release(package_path, {
    .public_key_pem_path = "...",
});
```

The verifier requires both `META-INF/hash.json` and `META-INF/signature.sig`, verifies RSA-PSS-SHA256 over the hash document, and verifies member SHA-256 values. The Kconfig option defaults to enabled, but compiling the function does not enforce it.

Core also provides useful install safeguards:

- exact package `systems` compatibility checking;
- safe manifest ID and extraction-path validation;
- staging under `apps/.installing/...`;
- staged manifest/resource validation before activation;
- cleanup of staging after pre-activation errors;
- caller-owned Runtime storage paths distinct from the App code root.

These mechanisms must be reused rather than replaced.

### Missing enforcement

The following paths do not call `verify_app_package_release()`:

- App Store download/install;
- `SystemApi::install_runtime_app_package()`;
- `System::install_runtime_app_package()`;
- startup scanning of extracted `apps/<id>/manifest.json` trees;
- the optional USB `InstallBpk` bridge.

App Store 0.8.2 parses catalog `hash_sha256` into `StoreEntry::sha256`, but the downloaded package bytes are not hashed or compared before cache rename and install.

`SystemApi::install_runtime_app_package()` calls the non-virtual Core installation method directly. ESPocket cannot override that call in `espocket::System`, and the post-install `on_app_installed()` hook is too late to authenticate the original `.bpk`. Core excludes `META-INF/` while extracting, so the hook cannot reconstruct release verification from the installed tree.

### Reboot bypass

ESPocket currently needs:

```cpp
config.install_package_apps = true;
```

for the build-staged Hello Runtime. At startup Core scans every configured `apps/` root and installs any compatible unpacked manifest. No signature or trusted-install record is required. Therefore a Store-only pre-install check would not establish a persistent trust boundary: after reboot, extracted directories are accepted independently of the `.bpk` that produced them.

### Update rollback gap

Core currently stages the new package, copies private data into staging, then calls `uninstall_app()` for the old Runtime App. `uninstall_app()` removes the old App directory. Only afterward does Core rename the staged directory into place and install the new Runtime App record.

If the rename, GUI preparation, lifecycle hook, or new Runtime installation fails after old-App removal, the old version is not restored. Cryptographic verification must occur before this point, but verification alone does not make updates transactional.

### Cache cleanup gap

App Store renames a completed partial download to its final cached `.bpk` and then schedules installation. A failed Core install does not remove that final cached package. Core uninstall removes the extracted App directory but does not remove Store's cached `.bpk`.

Known official catalog packages are unsigned and declare only `systems: ["super"]`; they cannot satisfy the ESPocket gate.

## Required unified Core contract

The authoritative gate belongs in System Core's common package installation boundary, not in a particular Store UI. Every `.bpk` entry point must converge on the same operation.

A compatible upstream API could extend install options conceptually as follows; exact naming is deliberately left to Brookesia:

```text
install_runtime_app_package(package_path, options)
    expected_package_sha256     optional source digest
    require_release_signature   product policy
    trusted_public_key(s)       product-pinned verification keys
    replace_existing            update policy
    source                      built-in / store / usb / developer
```

Required operation order:

```text
copy or lock immutable candidate bytes
    -> validate expected whole-file SHA-256, when supplied
    -> verify embedded release signature and all signed members
    -> read manifest from the same verified candidate
    -> validate exact system type and service requirements
    -> unpack to a new staging directory
    -> validate staged resources
    -> write a pending Core-owned trust receipt
    -> atomically switch old/new directories
    -> install and validate the new App record
    -> commit receipt and remove backup
```

### Same-bytes requirement

The package must not be verified from one file state and later unpacked from another. Core should either:

- read, verify, and unpack one immutable byte buffer; or
- first copy/rename the candidate into a Core-owned staging location, then verify and unpack only that immutable copy.

Calling the current verifier and unpacker independently on a caller-writable path leaves a time-of-check/time-of-use window.

### Public-key policy

ESPocket requires a public verification key pinned by the firmware/product configuration. The private signing key must never be placed on the device or committed to this repository.

For V0.x, one pinned release key is sufficient. Key rotation may later use a small explicit key set or signed key identifier, but no generic trust store is needed before a real rotation requirement exists.

Missing signature, incomplete signing metadata, unknown key, invalid signature, member mismatch, and disabled verifier must all fail closed.

## Trusted reboot discovery

Core must distinguish two trust sources.

### Built-in source

Firmware/LittleFS build staging is trusted as part of the signed firmware image and explicit product composition. ESPocket's build-staged `espocket.app.hello_runtime` remains a built-in validation App; it is not evidence that arbitrary unpacked directories are trusted.

The built-in allowlist should be explicit and generated by the build, not inferred from any directory that happens to exist under `apps/`.

### Dynamically installed source

A successful dynamic installation must write a Core-owned receipt outside Runtime-writable App storage. The receipt must bind at least:

- manifest ID and version;
- installed volume and normalized App path;
- whole `.bpk` digest;
- signer/key identity or pinned-key policy version;
- signed member hash set or equivalent installed-tree integrity binding;
- committed installation generation/state.

Startup scanning must reject or quarantine dynamic App directories with a missing, pending, mismatched, or invalid receipt. It must not treat an arbitrary extracted `manifest.json` tree as trusted.

If Core guarantees that no untrusted principal can mutate installed code roots, a committed receipt can attest to the verified install transaction. If code roots may be modified outside Core, startup must also compare installed members with the receipt's signed hashes.

## Transactional update and recovery

An update must retain the last-known-good version until the new version is committed.

Minimum state machine:

```text
Downloaded
  -> Verified
  -> Staged
  -> PendingActivation
  -> Committed
```

Failure behavior:

- failure before `PendingActivation`: delete staging; leave old App untouched;
- failure while switching: restore the old directory and old App record;
- failure during new App install/GUI preparation/hook: remove the new directory, restore and reinstall the old version;
- power loss with a pending receipt: deterministically roll back to the committed version on next boot;
- only after successful activation: delete the backup and finalize the receipt.

Preserved `cache/`, `data/`, and `files/` must not be destroyed until commit. The existing pre-copy behavior can be reused, but the old directory must be renamed to a backup rather than deleted before the new version is proven usable.

Version policy must also reject accidental downgrade by default. An explicit developer/recovery operation may opt in to downgrade; Store metadata alone must not silently replace a newer installed version with an older package.

## Store responsibilities

The official Store remains responsible for transport and cache lifecycle, not publisher-key policy.

Before final cache rename or install, Store must:

1. require `hash_sha256` to be exactly a valid SHA-256 value for downloadable entries;
2. hash the completed partial file and compare it in constant-result semantics;
3. reject a metadata/package manifest ID or version mismatch;
4. pass the expected whole-file digest to the Core install operation;
5. report trust failures distinctly from network and capacity failures.

The catalog digest detects corruption or a mismatched download. It is not a replacement for the signed release check because catalog metadata itself does not establish the package publisher identity.

## Cleanup policy

On constrained ESPocket storage, fail closed and reclaim invalid artifacts:

| Failure | Partial download | Final cached BPK | Staging | Existing App |
|---|---|---|---|---|
| Network/incomplete download | delete | unchanged | none | unchanged |
| Catalog SHA mismatch | delete | delete candidate | none | unchanged |
| Missing/invalid signature | delete | delete candidate | delete | unchanged |
| Manifest/system/service rejection | delete | delete candidate | delete | unchanged |
| New install activation failure | delete | delete candidate | delete | none |
| Update activation failure | delete | delete candidate | delete | restore old |
| Successful install/update | delete | product cache policy | delete | commit new |
| Uninstall | none | remove matching Store cache | none | remove App + receipt |

A future diagnostic quarantine is unnecessary until there is a concrete support workflow; deletion is the smaller and safer V0.x policy.

## Interim ESPocket policy

The locked 0.8.x APIs cannot provide this unified gate without an upstream Core/Store change. ESPocket must therefore:

- keep M5 `BLOCKED`;
- treat the current Store as integration/transport validation only, not a production distribution boundary;
- not install arbitrary downloaded or local `.bpk` files;
- not claim that `CONFIG_BROOKESIA_SYSTEM_CORE_ENABLE_PACKAGE_RELEASE_VERIFY=y` means verification is enforced;
- not patch `managed_components/` or add a replacement Store/package framework;
- continue allowing only explicitly build-staged product Runtime Apps;
- require an upstream hook/API before enabling dynamic installation.

A product-side wrapper around `verify_app_package_release()` is insufficient because official Store and USB paths can bypass it, startup scans unpacked trees, and post-install hooks no longer have the signed package metadata. The minimum honest local containment would be to disable dynamic installation entirely; implementing a second installer solely to work around 0.8.x is rejected.

## Acceptance matrix

Host/unit tests must cover:

- valid package, correct catalog digest, correct key: installs;
- catalog digest mismatch: rejected before unpack and deleted;
- unsigned package: rejected;
- only one of `hash.json` / `signature.sig`: rejected;
- wrong key or corrupted signature: rejected;
- modified manifest, Runtime code, or resource after signing: rejected;
- extra or missing signed member: rejected according to release format rules;
- package changed between verification and unpack attempt: rejected;
- `systems: ["super"]` on ESPocket: rejected;
- missing/incompatible service: rejected without changing the old App;
- update activation failure: old version and private data restored;
- downgrade without explicit authorization: rejected;
- uninstall: App directory and trust receipt removed; matching Store cache removed;
- boot with valid committed receipt: discovered;
- boot with missing/mismatched/pending receipt: not installed;
- simulated power loss at each transaction state: deterministic rollback or commit;
- Store, USB, and any future developer installer all exercise the same Core gate.

Device acceptance, after an upstream implementation exists, must add:

- signed ESPocket-compatible install, launch, Home, reboot, relaunch;
- signed update with preserved private data;
- induced failed update with old version recovery;
- uninstall followed by reboot with no rediscovery;
- repeated install/update/uninstall without cache or staging growth;
- no TLS, panic, reboot, or Runtime isolation failure during the complete flow.

## Required upstream unblock

M5 package trust can proceed only after official Brookesia provides all of the following, or an equivalent common contract:

1. enforced whole-package digest and release verification in every Core `.bpk` install path;
2. an immutable verify-to-unpack boundary;
3. trusted reboot discovery rather than unconditional unpacked-directory acceptance;
4. transactional update rollback;
5. Store cleanup and error propagation for trust failures;
6. at least one officially supported, signed package whose `systems` permits `espocket`, plus a supported publication/update route.

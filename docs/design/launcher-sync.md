# M5 Launcher Synchronization Policy

## Status

- Policy: defined for the locked Brookesia 0.8.x APIs
- Implementation: deferred until the M5 package trust gate is enforceable
- M6: not entered

This policy defines how Circular Shell reflects installed Runtime Apps without turning ESPocket into a generic Shell framework or duplicating Brookesia's App manager.

## Goals

- Keep product-owned entries stable.
- Show dynamically installed Runtime Apps only after trusted Core installation commits.
- Update Launcher deterministically after install, update, uninstall, and reboot discovery.
- Never cache an `AppId` across package replacement or reboot.
- Keep all Core calls on the Shell/System app-task path.
- Fail closed without breaking Launcher, Home, Settings, or Store.

## Entry ownership

### Fixed product entries

The following remain statically authored in Circular Shell's JSON:

- Hello Native, while retained as platform validation;
- Hello Runtime, while retained as the build-staged Runtime validation App;
- Settings;
- App Store.

Their placement, styling, and actions are product composition. Dynamic synchronization must not delete, reorder, shadow, or replace them.

A fixed manifest-ID set is therefore the sole exclusion list:

```text
espocket.app.hello
espocket.app.hello_runtime
brookesia.general.settings
brookesia.general.app_store
espocket.shell.circular
```

Do not add a provider registry or a second Launcher model for these five entries.

### Dynamic entries

A dynamic Launcher entry is derived only from a Core `AppInfo` that is:

- `manifest.kind == Runtime`;
- `manifest.visible == true`;
- not in the fixed manifest-ID set;
- admitted by the package trust policy and present in Core's committed App list.

Native Apps are never admitted dynamically in V0.x. Adding another product Native App remains an explicit composition change.

Until `package-trust.md` is enforceable, no downloaded or local `.bpk` is eligible for this dynamic section.

## Source of truth

Core's `list_apps()` is the only live Launcher source of truth. Circular Shell must not infer installation from:

- Store catalog/cache files;
- a downloaded `.bpk` existing on storage;
- directories found by Shell itself;
- stale App Store UI state;
- previously cached `AppId` values.

Store reports requested operations; Core reports committed installed state.

## Synchronization model

Use a full deterministic reconciliation, not a custom event registry or incremental App database.

1. `espocket::System::on_app_installed()` and `on_app_uninstalled()` increment a shared launcher-sync generation after the Core operation has committed.
2. Circular Shell receives only a generation provider or narrow dirty notifier from the composition root. Apps and services do not gain a dependency on Circular Shell.
3. The existing Shell-owned periodic timer observes generation changes on the Core app task.
4. On a change, Shell calls `context.system_service().list_apps()`, filters the eligible dynamic Apps, builds a complete desired snapshot, and reconciles the dynamic container.
5. Shell records the generation only after every create/bind/destroy step succeeds.
6. On failure, Shell keeps or restores the last complete view, logs no package secrets, and retries on a later timer tick.

The Shell should also perform one reconciliation in `on_start()` after its GUI document is ready. This covers reboot discovery and any package Apps installed before the Shell itself.

A full snapshot is preferred because the expected V0.x App count is small and it naturally repairs missed/coalesced hook notifications. No persistent Launcher index is required.

## GUI implementation boundary

Reuse Brookesia JSON UI templates and the existing public APIs:

```cpp
context.gui().create_view(template_id, parent_path, instance_id);
context.gui().destroy_view(absolute_path);
context.gui().set_binding_values(...);
context.gui().subscribe_action(action, handler);
```

Add one dynamic, scrollable container and one Runtime App row/button template to Circular Shell's existing JSON document. Do not create dynamic entries with Native LVGL, patch the GUI backend, or regenerate the entire Shell JSON at runtime.

The fixed product area remains present even if the dynamic section is empty or synchronization fails.

### Stable instance identity

GUI `instance_id` must not embed a manifest ID verbatim. Encode the manifest ID with a deterministic collision-resistant identifier suitable for a JSON view path, for example:

```text
app_<first 16 bytes of SHA-256(manifest_id), lowercase hex>
```

Maintain an in-memory map from instance ID to manifest ID for the current complete snapshot. If a collision is detected, fail that reconciliation instead of showing or launching the wrong App.

Do not use `std::hash`, because its stability is not a persistence/API guarantee. The map is rebuilt from `list_apps()` and is never persisted.

## Ordering and labels

Dynamic entries sort by:

1. resolved display name using the current Core language;
2. manifest ID as a deterministic tie-breaker.

Name resolution reuses `resolve_app_display_name(manifest, language)`. An empty localized name falls back through Core's existing rules to English, another non-empty name, `manifest.name`, then manifest ID.

Updates that change name, language, visibility, or icon are reflected by the next full reconciliation. Do not preserve user-defined ordering in V0.x; there is no demonstrated requirement for folders, favorites, recents, or drag-and-drop.

## Icon policy

Use Core's globally scoped App icon resource only when `has_app_icon_image(manifest)` is true and the resource was registered during Core install. Otherwise render the standard text-only Runtime row.

An absent or failed icon must not hide an otherwise eligible App. Dynamic icon preload/release must follow the Shell view lifetime and must not outlive the corresponding dynamic entry.

## Action routing

Use one shared dynamic action, such as:

```text
shell.open_dynamic_runtime
```

The action handler uses the GUI `Event.path` to resolve the current snapshot's instance ID to a manifest ID. It records a pending manifest ID only; it does not call Core directly from the GUI callback.

The existing Shell timer consumes the pending launch on the app-task path:

1. call `list_apps()` again;
2. resolve the manifest ID to the current visible Runtime `AppInfo`;
3. reject if absent, hidden, no longer Runtime, or no longer trust-admitted;
4. call `start_app()` with the **current** `AppId`;
5. clear the pending request exactly once.

This protects against uninstall/update between tap and dispatch. Package replacement may assign a new `AppId`; manifest ID is the stable Launcher identity.

Only one pending dynamic launch is retained. A second tap while one is pending is ignored. This is sufficient for the single-foreground-app V0.x model.

## Operation semantics

### Install

- Core trust verification and activation commit first.
- Core invokes `on_app_installed()` only after GUI/resource preparation succeeds.
- System increments the generation.
- Shell reconciliation adds the eligible App.
- If Launcher rendering fails, the App remains installed but is not partially exposed; retry does not reinstall it.

### Update

- The trust gate's transaction retains the old App until the new version commits.
- Core emits uninstall/install lifecycle hooks as defined by the final upstream transaction API.
- Multiple hook notifications may coalesce into one generation change.
- Shell's full snapshot must show either the last committed old version or the committed new version, never both.
- The row identity remains manifest ID; label/icon may change.
- A pending tap is re-resolved to the committed current `AppId`.

### Uninstall

- If the App is foreground, Core must stop it before uninstall commits.
- Core removes the App and then invokes `on_app_uninstalled()`.
- System increments the generation.
- Shell destroys the dynamic row and releases any Shell-owned icon preload.
- If a pending tap targets the removed manifest ID, dispatch rejects and clears it.
- Store cache cleanup and trust-receipt cleanup follow the package trust policy; Launcher does not manage files.

### Reboot

- Core completes trusted built-in and dynamic discovery before Shell start.
- Shell's initial reconciliation uses the resulting `list_apps()` snapshot.
- No Launcher state file is read or restored.
- Apps rejected by trust, compatibility, or receipt checks never enter `list_apps()` and never appear.

### Install/update failure

- No `on_app_installed()` commit notification means no new row.
- A failed transactional update retains the old committed App, so reconciliation retains its row.
- Store messages may explain the failure; Launcher does not display cached or pending packages.

### Runtime lifecycle failure

- Start failure leaves the row installed and returns to Launcher through existing lifecycle restoration.
- Stop failure continues to use ESPocket's existing fail-closed keyboard latch.
- A lifecycle failure is not equivalent to uninstall and does not remove the row.

## Hook and startup timing

Core invokes install hooks while mutating its App records. Hook implementations must not synchronously call `list_apps()` or mutate Shell GUI. They only mark the generation dirty and return.

Shell reconciliation occurs later from its own timer after the hook stack has unwound. This keeps ownership and task ordering simple and avoids reentrant Core access.

During current System setup, ESPocket's `on_init()` installs Circular Shell before Core scans package Apps, but those package `on_app_installed()` hooks still arrive before the Shell is started and its GUI context exists. The shared generation counter can safely record those early commits; Shell's initial full reconciliation makes the exact early count unimportant.

## Reconciliation failure rules

A reconciliation must not leave a mixed old/new list.

For V0.x, use the smallest safe approach:

1. build and validate the desired model in memory;
2. create/bind replacement instances under a temporary dynamic container or generation-specific subtree;
3. after all instances succeed, swap visibility/mount ownership and destroy the old subtree;
4. on any failure, destroy the temporary subtree and retain the old one;
5. update `applied_generation` only after commit.

If the current GUI API cannot atomically swap two subtrees, retain the previous list until a complete replacement subtree is ready; a brief empty dynamic section is acceptable only if rollback restores the previous snapshot in the same timer turn. Fixed product entries must remain usable throughout.

Repeated failure should be rate-limited in logs and retried only when the generation changes or after a modest backoff. It must not spin every 50 ms.

## Capacity and layout policy

The 466×466 product UI needs a bounded visible area, not a phone-style grid.

- fixed entries remain at the top;
- dynamic entries use a vertical scrollable section;
- row text is ellipsized to the safe width;
- no animations, folders, recents, badges, or drag ordering in M5;
- no hard App-count security limit in Launcher—the package/storage policy controls admission—but rendering must remain lazy enough for the measured memory budget.

For the first implementation, create only the rows required by the current full snapshot. Add viewport virtualization only if measured App counts or PSRAM usage require it.

## Concurrency and ownership invariants

- System owns App lifecycle and the dirty generation.
- Circular Shell owns Launcher presentation and its dynamic view map.
- Store owns catalog/download UI but never writes Launcher state.
- Runtime Apps cannot register Launcher entries directly.
- GUI callbacks record intent only; Shell timer calls Core.
- Manifest ID is stable identity; `AppId` is resolved at dispatch time.
- Hidden Apps and the hidden Shell never appear.
- No dynamic App appears without the package trust gate.

## Acceptance matrix

Host/static tests:

- filtering excludes hidden, Native, fixed, incompatible, and untrusted Apps;
- deterministic ordering and display-name fallback;
- deterministic instance IDs and collision rejection;
- initial snapshot creates exactly one row per eligible manifest ID;
- duplicate/coalesced install notifications remain idempotent;
- update changes metadata without duplicate rows and resolves the new `AppId`;
- uninstall removes the row and cancels a pending launch;
- tap/uninstall race cannot start a stale `AppId`;
- reconciliation failure retains the previous complete snapshot;
- language change triggers label reorder/rebuild;
- Shell restart rebuilds from Core without persistent Launcher state.

Device acceptance after package trust and online HTTP are unblocked:

1. install a signed ESPocket-compatible Runtime App; row appears once;
2. launch it; Home returns to Launcher;
3. update it; row remains singular and launches the new version;
4. force an update failure; old row/version still launches;
5. reboot; trusted row reappears without Store opening;
6. uninstall; row disappears and stays absent after reboot;
7. repeat install/update/uninstall while monitoring heap/PSRAM and GUI cleanup;
8. verify fixed Hello/Settings/Store entries remain functional throughout.

## Implementation gate

Do not implement dynamic Launcher exposure before all of these are true:

- package trust gate is enforced by the common Core install/discovery path;
- update rollback semantics are defined by the actual upstream API;
- at least one signed package supports `systems: ["espocket"]`;
- online Store cancellation is fixed and device-regressed.

Until then, the current fixed Launcher is the correct fail-closed product behavior.

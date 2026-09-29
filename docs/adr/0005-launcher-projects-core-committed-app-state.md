# ADR-0005: Launcher projects Core-committed App state

- Status: `accepted`
- Date: 2026-09-29

## Context

Catalog entries, download requests, filesystem remnants and install events do not prove that Core has committed an App that can be launched. A separate Launcher database would create another installation truth.

## Decision

`Core::list_apps()` is the authoritative live source for dynamic Launcher entries. Shell maintains a deterministic display projection and reconciles it from complete Core snapshots. Fixed product entries remain explicit and separate.

## Consequences

- Events can mark the projection dirty but cannot mutate installation truth.
- A failed refresh preserves the last complete view.
- Manifest identity is stable; runtime `AppId` is resolved at dispatch.
- Dynamic entries stay hidden until package trust and online stability permit exposure.

## Alternatives rejected

- Store Catalog as an installed-App database.
- Directory scanning in Shell.
- A persistent Launcher index.
- Incremental event state as the sole source of truth.

See [application discovery contract](../design/product/application-discovery.md) and [M5 acceptance](../milestones/m5/acceptance.md).

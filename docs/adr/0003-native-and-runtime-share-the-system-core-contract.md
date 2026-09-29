# ADR-0003: Native and Runtime Apps share the System Core contract

- Status: `accepted`
- Date: 2026-09-29

## Context

Native and Runtime Apps use different loading adapters, but users should not receive different navigation, display or lifecycle behavior based on an implementation detail.

## Decision

Both execution models use the System Core App state machine and the same product contract for Root, Detail, Back, Home, Screen Off, wake, reclaim and GUI/keyboard ownership. Runtime-specific loading remains behind the Brookesia backend.

## Consequences

- Product code maintains one foreground and recovery model.
- Native and Runtime acceptance uses the same behavior vocabulary while retaining separate evidence.
- Runtime integration cannot introduce a second product navigation or lifecycle manager.

## Alternatives rejected

- A Runtime-specific product lifecycle.
- Separate navigation and recovery semantics for packaged Apps.

See [App contract](../design/product/app-contract.md) and [App lifecycle architecture](../design/architecture/04-boot-lifecycle.md).

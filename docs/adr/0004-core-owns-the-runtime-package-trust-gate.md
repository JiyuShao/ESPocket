# ADR-0004: Core owns the Runtime package trust gate

- Status: `accepted`
- Date: 2026-09-29

## Context

Runtime packages can arrive through more than one product entry and can be rediscovered after reboot. Validation in Store or after unpacking can be bypassed and cannot provide a single install truth.

## Decision

Every remotely sourced Runtime package must pass one fail-closed trust gate at the Core-owned public install boundary before unpacking or activation. The gate covers artifact identity, release signature, member integrity, product compatibility, transactional activation and trusted reboot discovery.

Dynamic installation remains disabled while the public Core boundary cannot enforce the contract. ESPocket will not create a private installer to bypass that limitation.

## Consequences

- Store download success is not installation success.
- Verification and unpacking share one immutable input.
- Activation must either commit completely or preserve the previous trusted version.
- A missing upstream seam can keep the application-ecosystem Milestone blocked.

## Alternatives rejected

- Store-only validation.
- A product wrapper around an otherwise permissive Core path.
- Post-install verification.
- A second ESPocket package manager or installer.

See [Runtime package trust contract](../design/product/runtime-package-trust.md) and [M5 acceptance](../milestones/m5/acceptance.md).

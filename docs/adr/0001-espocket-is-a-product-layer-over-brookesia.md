# ADR-0001: ESPocket is a product layer over Brookesia

- Status: `accepted`
- Date: 2026-09-29

## Context

Brookesia already owns App, Runtime, GUI, Timer, Package, Service and HAL infrastructure. Recreating those facilities in ESPocket would split state and lifecycle ownership and make upstream upgrades harder.

## Decision

ESPocket composes product behavior through Brookesia public seams. It does not fork Core or create product-owned replacements for framework managers, package formats, installers or device abstractions.

Circular Shell uses a hidden Native `IApp` as its Brookesia carrier while remaining a system Shell in the product model. ESPocket will add a Shell abstraction only after a second real implementation proves the seam.

## Consequences

- Product policy belongs in `espocket::System`, Shell and focused adapters.
- Framework gaps can block a Milestone rather than be bypassed with a second framework.
- Managed components remain upstream-owned; compatibility code stays explicit and removable.

## Alternatives rejected

- Fork Brookesia or patch managed components as the product baseline.
- Copy framework managers into ESPocket.
- Build a private installer, Runtime or Shell framework before a second implementation exists.

See [product overview](../design/product/overview.md) and [layered architecture](../design/architecture/02-layered-architecture.md).

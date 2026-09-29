# ADR-0009: AI Native is a foundational design dimension

- Status: `accepted`
- Date: 2026-09-29

## Context

Adding AI access only after a subsystem is complete tends to expose UI mechanics or low-level APIs, then retrofit authorization and lifecycle rules. That produces inconsistent semantics and makes AI a parallel integration layer.

## Decision

Every new or changed product capability and system design must make an explicit AI Native Exposure Decision alongside its human interaction and ownership design. The decision records the Owner, possible Context/Action/Event semantics, authorization, Action Risk and lifecycle.

The valid outcomes are: register a stable semantic capability, explicitly keep it unexposed with a reason, or defer it with a ticket. Internal modules are not required to expose an AI capability, and raw framework or hardware APIs are not Semantic Registrations.

## Consequences

- Design review treats the Exposure Decision as part of completeness.
- Registration occurs at product-semantic Owner boundaries.
- Human UI and Assistant paths can converge on the same Action without sharing authority.
- Deferral remains visible in `.scratch/` rather than disappearing from the design.

## Alternatives rejected

- Completing traditional subsystems first and adding AI adapters later.
- Requiring every internal class or method to be exposed.
- Allowing AI integration to bypass product semantics because a framework API exists.

See [product overview](../design/product/overview.md) and [AI Native architecture](../design/architecture/07-ai-native.md).

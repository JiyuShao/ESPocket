# ADR-0006: AI semantic access stays with real Owners

- Status: `accepted`
- Date: 2026-09-29

## Context

System, Shell, Service and App already own product state, side effects and lifecycles. Moving those responsibilities into a global AI manager would create conflicting state and failure recovery.

## Decision

AI Native is a semantic access dimension over existing Owners. Context, Action and Event are registered at an Owner boundary, and focused adapters translate product semantics to public Brookesia interfaces. AI Native does not add a second global manager, registry of state, event bus or lifecycle system.

Product UI and Assistant may share a semantic Action entry, but authorization is evaluated for the actual caller.

## Consequences

- The Owner remains the source of state and side effects.
- Assistant does not automate GUI controls or call HAL directly.
- A first capability receives a focused adapter; common abstractions wait for a second real capability.
- Brookesia version details remain behind the adapter.

## Alternatives rejected

- A global AI Manager that owns system capabilities.
- Duplicated state or a parallel Event Bus.
- Direct Assistant access to Brookesia internals or HAL.

See [AI Native architecture](../design/architecture/07-ai-native.md).

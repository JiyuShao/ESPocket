# ADR-0008: App AI capabilities follow the Running Instance

- Status: `accepted`
- Date: 2026-09-29

## Context

An App can stop, crash, restart or be reclaimed. Keeping its Context, Action or Event handles alive beyond that instance would leave stale objects and conflict with System Core lifecycle truth.

## Decision

Capabilities registered by a Native or Runtime App belong to one Running Instance. Its handles and subscriptions are invalidated when that instance ends. A new start receives a new identity and new registrations. Capabilities that must survive App lifetime belong to a Brookesia Service.

## Consequences

- Assistant must launch a stopped App or use a persistent Service.
- Native and Runtime cleanup follows one semantic rule.
- AI Native does not extend App lifetime or create a second App state machine.

## Alternatives rejected

- Permanent global registration of App-owned objects.
- Reusing handles across App restarts.
- Keeping Apps resident solely to preserve AI access.

See [App lifecycle architecture](../design/architecture/04-boot-lifecycle.md) and [AI Native architecture](../design/architecture/07-ai-native.md).

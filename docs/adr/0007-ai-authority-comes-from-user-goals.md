# ADR-0007: AI authority comes from confirmed user goals

- Status: `accepted`
- Date: 2026-09-29

## Context

An App or Agent can request an Action without representing the user's wishes. Treating any prompt or capability request as authority would permit privilege escalation and confused-deputy behavior.

## Decision

AI authority originates in a confirmed User Intent or a valid Scoped Grant. Execution is allowed only within the intersection of that product authorization, the actual caller, Action Risk, the target Owner's admission rules and Brookesia permissions. High-impact steps require their own confirmation.

## Consequences

- App or Agent text is input, not proof of user authorization.
- Grants have capability, target, duration and caller bounds.
- Permission is reevaluated at execution.
- An uncertain submitted result is reported rather than blindly retried or assumed rolled back.

## Alternatives rejected

- Treating App prompts or clicks as User Intent.
- Letting Assistant proxy any capability it can technically reach.
- One approval that authorizes unrelated future operations.

See [AI Native architecture](../design/architecture/07-ai-native.md).

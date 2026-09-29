# AI Native foundation

Sequence: 009

Status: planned-after-m8

## Problem Statement

ESPocket needs AI access to be part of product and architecture design without creating a second state, authorization or lifecycle system.

## Solution

Make every system design record an Exposure Decision, establish one brightness tracer bullet through a real Owner and public Brookesia seam, then extend the proven semantics to App and Service capabilities.

## User Stories

1. As a user, I want Assistant actions to represent my confirmed goal.
2. As a system Owner, I want to retain state and side-effect ownership.
3. As an App author, I want semantic capabilities with explicit lifetime and permissions.
4. As a product designer, I want every new capability to consider human and AI access together.
5. As a security reviewer, I want caller, grant, risk and framework admission evaluated together.
6. As a maintainer, I want version-specific Brookesia details behind focused adapters.

## Implementation Decisions

- AI Native is a foundational design dimension and not an App type or manager layer.
- Context, Action and Event register at real Owner boundaries.
- User Intent or Scoped Grant is required; App/Agent requests are not authority.
- App capability registrations belong to one Running Instance.
- Brightness is the first capability seam; abstractions wait for a second real capability.

## Testing Decisions

- Verify the same brightness semantic Action from product UI and Assistant with separate caller authorization.
- Cover read, set, Event, denied, canceled-before-submit, uncertain-after-submit and Owner failure outcomes.
- Prove no duplicated brightness state or direct HAL access.
- Add Native and Runtime lifecycle tests only after the first seam is trusted.

## Out of Scope

Selecting a model provider, XiaoZhi/ESP-Claw integration, a global AI Manager, GUI automation and remote Runtime AI capability exposure before M5 trust passes.

## Further Notes

Architecture: [AI Native](../../docs/design/architecture/07-ai-native.md). Decisions: [ADR index](../../docs/adr/README.md).

The original A0–A5 sequence is preserved as ticket groups: A0 = 01, A1 = 02, A2 = 03–05, A3 = 06, A4 = 07, A5 = 08. A1 → A2 is the minimum mainline; A3–A5 branch when their own dependencies are available.

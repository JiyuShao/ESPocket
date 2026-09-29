# M8 — App Interaction Contract

Sequence: 008

Status: planned

## Problem Statement

The Native navigation model must become a stable shared contract for Native, Runtime and third-party Apps, including reclaim and invalid-source behavior.

## Solution

Validate Root/Detail/Back, direct Launch Source, Home, Screen Off, wake, reclaim and gesture ownership with real Native and Runtime Apps under one product contract.

## User Stories

1. As an App author, I want one interaction contract regardless of execution model.
2. As a user, I want Native and Runtime Back/Home behavior to match.
3. As a user, I want reclaimed Apps to restart at Root rather than restore stale pages.
4. As an App, I want ordinary scroll, horizontal swipe and long press preserved.
5. As a tester, I want separate Native and Runtime physical evidence.

## Implementation Decisions

- Both models share System Core lifecycle and product navigation semantics.
- App tasks store one direct Launch Source.
- Reliable long-lived work belongs to Service or persisted business state.
- App-provided AI Native capabilities follow the same Running Instance lifetime.

## Testing Decisions

- Require M7 `PASS` and retain M3 Runtime evidence as a dependency, not a substitute.
- Run Native and Runtime navigation/reclaim paths five times each.
- Use a real Runtime App rather than a Native mock.

## Out of Scope

Four template frameworks, arbitrary navigation history, background residency guarantees, a low-memory killer and new Runtime or Shell abstractions.

## Further Notes

Fixed acceptance gates: [M8 acceptance](../../docs/milestones/m8/acceptance.md).

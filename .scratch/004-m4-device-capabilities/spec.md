# M4 — Device Capabilities

Sequence: 004

Status: retrospective-active
Historical basis: reconstructed on 2026-09-29 from completed work and open M4 gates; accepted results remain historical, unresolved gates remain current.

## Problem Statement

ESPocket needed official Settings and real device capabilities on the round target without copying upstream Apps or enabling hardware features outside the product boundary.

## Solution

Integrate official Settings and required Services through Brookesia, provide the product keyboard seam, verify available hardware capabilities, and keep unsupported playback-only Audio fail closed.

## User Stories

1. As a user, I want Settings pages to work on the round display.
2. As a user, I want Wi-Fi, brightness, time, battery and device information to reflect real state.
3. As a Settings App, I want a system keyboard with correct masking and completion semantics.
4. As a product owner, I want playback-only Audio without silently enabling recording.
5. As a tester, I want each unverified capability to remain visibly open.

## Implementation Decisions

- Reuse the official Settings and Audio components without managed-component patches.
- ESPocket System owns the keyboard provider; Circular Shell owns its transient Overlay.
- Wi-Fi initialization must satisfy the target's real buffer and NVS behavior.
- Audio remains blocked until official interfaces support playback-only composition.
- Storage and Developer remain open until physical checks exist.

## Testing Decisions

- Separate host build/static evidence from physical semantics.
- Verify official resources and clean staging.
- Exercise Settings layout, capability pages, keyboard behavior, Wi-Fi reconnect and SNTP.
- Keep Sound/Volume blocked based on direct released/current-upstream inspection.

## Out of Scope

A private Settings implementation, private Audio framework, recorder enablement and claims about untested Storage/Developer behavior.

## Further Notes

Current status and evidence index: [M4 acceptance](../../docs/milestones/m4/acceptance.md).

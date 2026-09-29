# M6 — Home and Display State

Sequence: 006

Status: active

## Problem Statement

ESPocket must replace Launcher-as-home behavior with a complete Watch Face Home, PWR and Screen Off state model verified on the target device.

## Solution

Use Watch Face as Home, route PWR short press through the defined Home/Off/Wake state machine, keep Display State orthogonal to navigation and fall back safely when a resume target is invalid.

## User Stories

1. As a user, I want every boot and Home action to reach Watch Face.
2. As a user, I want PWR to mean Home, Off or Wake according to the visible state.
3. As a user, I want wake to restore a valid App page without inventing lost state.
4. As a user, I want an invalid resume target to fall back to Watch Face.
5. As a tester, I want fixed repetition counts and physical evidence.

## Implementation Decisions

- Home, Back and Display State remain separate.
- PWR long press remains hardware-owned; BOOT remains reserved.
- Screen Off ignores touch and does not mutate navigation.
- Reclaim fallback may use a focused test seam rather than a general memory manager.

## Testing Decisions

- Run the four fixed hardware paths five times each.
- Include Overlay, touch-while-off, BOOT, long-press and fatal-signal checks.
- Require physical screen and button observations alongside serial evidence.

## Out of Scope

Cards, Quick Settings, Edge Back, dynamic Launcher and arbitrary background scheduling.

## Further Notes

Fixed acceptance gates: [M6 acceptance](../../docs/milestones/m6/acceptance.md).

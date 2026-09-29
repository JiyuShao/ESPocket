# M7 — Navigation Surfaces

Sequence: 007

Status: planned

## Problem Statement

ESPocket needs a watch-centered navigation loop across Cards, Quick Settings, Launcher and Native Apps after M6 establishes Home and Display State.

## Solution

Implement real Surface content, Edge Back and one direct Launch Source while preserving App horizontal gestures and routing PWR Home to Watch Face.

## User Stories

1. As a user, I want Cards around Watch Face with stable non-wrapping boundaries.
2. As a user, I want Quick Settings to change real device state.
3. As a user, I want Back to return to the direct Surface that launched an App.
4. As an App, I want normal horizontal swipes without false Edge Back.
5. As a tester, I want brightness and Wi-Fi changes proven on hardware.

## Implementation Decisions

- Cards remain single-page content rather than nested Apps.
- One direct Launch Source is stored; invalid sources fall back to Watch Face.
- Battery, Brightness, Wi-Fi and Settings provide the minimum real content.
- Brightness uses the selected real Display output rather than a fixed ID.

## Testing Decisions

- M6 `PASS` gates stage acceptance.
- Verify complete navigation loops and each edge path physically.
- Prove real Wi-Fi and brightness changes, not only control labels.

## Out of Scope

Runtime App contract validation, generic Card SDK, Card editor, arbitrary App-to-App history and dynamic Launcher.

## Further Notes

Fixed acceptance gates: [M7 acceptance](../../docs/milestones/m7/acceptance.md).

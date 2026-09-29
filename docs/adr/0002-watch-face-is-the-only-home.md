# ADR-0002: Watch Face is the only Home

- Status: `accepted`
- Date: 2026-09-29

## Context

ESPocket targets a small round watch display. A phone-style Launcher Home, a shared Home/Back history stack and navigation changes during Screen Off would conflict with the watch interaction model and make recovery ambiguous.

## Decision

Watch Face is the fixed Home target and the center of Home Space. Launcher, Quick Settings, Cards and App are other Surfaces. Home, Back and Screen Off have separate semantics.

An App task records one direct Launch Source. Root Back returns to that source, an invalid source falls back to Watch Face, and the product does not maintain an arbitrary cross-App history chain.

## Consequences

- PWR Home always reaches Watch Face and can end the current navigation task.
- Screen Off preserves navigation state and wake restores it on a best-effort basis.
- Launcher is an App finder rather than the system root.
- More complex future cross-App workflows require an explicit continuation model.

## Alternatives rejected

- Launcher as Home.
- Home and Back as the same operation.
- Screen Off as a navigation transition.
- An unbounded phone-style task history for the initial product contract.

See [interaction model](../design/product/interaction-model.md) and [App contract](../design/product/app-contract.md).

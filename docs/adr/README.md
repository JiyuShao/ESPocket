# Architecture Decision Records

ADRs record durable ESPocket choices whose alternatives have meaningful cost. Product behavior remains authoritative in `docs/design/product/`; current structure remains authoritative in `docs/design/architecture/`.

| ADR | Status | Decision |
|---|---|---|
| [0001](0001-espocket-is-a-product-layer-over-brookesia.md) | accepted | ESPocket remains a product layer over Brookesia. |
| [0002](0002-watch-face-is-the-only-home.md) | accepted | Watch Face is the only Home. |
| [0003](0003-native-and-runtime-share-the-system-core-contract.md) | accepted | Native and Runtime Apps share one product lifecycle contract. |
| [0004](0004-core-owns-the-runtime-package-trust-gate.md) | accepted | Core owns one fail-closed Runtime package trust gate. |
| [0005](0005-launcher-projects-core-committed-app-state.md) | accepted | Launcher projects Core-committed App state. |
| [0006](0006-ai-semantic-access-stays-with-real-owners.md) | accepted | AI semantic access stays with real Owners. |
| [0007](0007-ai-authority-comes-from-user-goals.md) | accepted | AI authority comes from confirmed user goals. |
| [0008](0008-app-ai-capabilities-follow-the-running-instance.md) | accepted | App AI capabilities follow one Running Instance. |
| [0009](0009-ai-native-is-a-foundational-design-dimension.md) | accepted | AI Native is a foundational design dimension. |

When a decision changes, add a superseding ADR and link both records. Do not silently rewrite an accepted decision into a different choice.

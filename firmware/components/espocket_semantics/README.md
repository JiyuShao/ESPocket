# Owner semantic interfaces

## Contract

`semantic_contract.hpp` defines stable discovery metadata, actual caller identity,
Owner identity, operation, risk, cancellation boundary and result vocabulary.
Discovery grants no access. `Permission` is a trusted admission conclusion, not a
request field. No state registry, event bus or authorization database is introduced.

A System/Service capability belongs to its Owner lifetime; an App declaration must
carry a nonzero Running Instance identity. The actual Owner invalidates its
`LifetimeScope` when ending that lifetime. Every copied weak handle then fails;
creating a new scope cannot revive old handles. A handle is an availability check,
not a synchronization lock. The concrete adapter must serialize invalidation with
execution and must not let raw implementation pointers bypass that check.

Exposure Decision: these contract types are internal seams, **unexposed** as AI
capabilities. They describe registered product capabilities; they do not export
arbitrary methods or inspect internal objects.

## Brightness

`Brightness` binds one selected Display target to public service read and absolute
set calls. Its read/write/admission callbacks are trusted composition and may not
reenter the adapter. Calls and invalidation are serialized. No brightness cache
exists. UI and future Assistant calls use the same interface with their actual
caller; this slice admits only the internally composed Shell caller. Assistant and
App remain denied in the device until user-goal admission is implemented.

Set validates 0–100 finite percent, checks admission, reads actual state, rechecks
admission and cancellation immediately before submission, and observes state after
acknowledged submission. A returned value may differ from the requested value due
to Owner normalization. A service error after submission or failed observation is
`Uncertain`, with no automatic retry, cancellation claim or rollback claim. A
pre-submit read failure is `Failed`; denied/invalid requests are `NotExecuted`.

The optional `BrightnessChanged` result is a fact observed during this Action,
containing target, previous/observed values and caller. It is provided only when
Event observation is admitted and the observed value changed. It is not a global
subscription or a claim to capture changes from every other client. Full Event
subscription and Assistant entry are separate work; no background bus is added.

Exposure Decision: register `display.brightness.context`,
`display.brightness.set` and `display.brightness.changed` under the real Brookesia
Display Owner. Brightness set is reversible; admission must be evaluated at access
and immediately before submission. System deinit revokes the binding. The current
UI route has no implicit Assistant grant.

## Verification

Public-interface host tests cover instance declarations, permission intersection,
Owner revocation, actual caller, observed normalization, no-change Event omission,
pre-submit cancellation and withdrawal, pre-submit Owner failure, uncertain writes
and observations, and absence of retries. Firmware checks and full builds remain
separate from physical brightness verification.

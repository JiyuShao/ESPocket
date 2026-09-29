# M2 — Native App Validation

Sequence: 002

Status: retrospective-resolved
Historical basis: reconstructed on 2026-09-29 from accepted M2 evidence; it does not claim these tickets existed during implementation.

## Problem Statement

The M1 shell baseline did not prove that a real visible Native App could be installed, launched, updated, stopped and cleaned repeatedly through System Core.

## Solution

Add one minimal Hello Native tracer bullet through installation, Launcher discovery, GUI Action, Home stop, Shell restoration and a 50-cycle device lifecycle/heap gate.

## User Stories

1. As a user, I want a visible App to launch from Launcher and return Home reliably.
2. As an App author, I want stable manifest identity and ordinary AppContext GUI behavior.
3. As a platform maintainer, I want Core to own App lifecycle and cleanup.
4. As a tester, I want repeated lifecycle evidence with measurable heap gates.
5. As a debugger, I want superseded images identified so that they are not flashed accidentally.

## Implementation Decisions

- Hello Native is the smallest real product App and uses stable manifest identity.
- System Core resolves the runtime App identity and owns start/stop state.
- Home intent is consumed in the Core App task rather than calling lifecycle code from the display callback.
- Shell and status callbacks have explicit cleanup ownership.
- The stress runner is disabled in normal builds.

## Testing Decisions

- Test the complete Launcher → Hello → Increment → Home → Launcher path.
- Require 50 successful cycles with explicit Running/Stopped and GUI unload probes.
- Compare early and late heap medians with a 1,024-byte loss gate.
- Treat cleanup warnings, resets and malformed evidence protocol as failures.

## Out of Scope

Runtime Apps, dynamic installation, Settings, Store and generalized App templates.

## Further Notes

Current historical judgment and evidence index: [M2 acceptance](../../docs/milestones/m2/acceptance.md).

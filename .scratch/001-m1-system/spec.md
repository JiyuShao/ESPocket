# M1 — ESPocket System

Sequence: 001

Status: retrospective-resolved
Historical basis: reconstructed on 2026-09-29 from the accepted M1 record; sequence, owners and timing not present in evidence remain unknown.

## Problem Statement

ESPocket needed a reproducible product System that could boot the Waveshare target through Brookesia, present a usable Circular Shell and preserve diagnosable failures without becoming a framework fork.

## Solution

Compose ESPocket System on the locked Brookesia public seams, generate the board configuration, start required services and the hidden Shell App in deterministic order, and accept the baseline only after clean build and physical stability gates.

## User Stories

1. As a device user, I want the product to boot into a usable system UI, so that the device has a stable starting point.
2. As a maintainer, I want a clean build from declared dependencies, so that generated local state is not part of the baseline.
3. As a debugger, I want fatal startup failures to stop with serial evidence, so that failures are diagnosable.
4. As a product developer, I want ESPocket to reuse Brookesia managers, so that product work does not create a framework fork.
5. As a release owner, I want repeated cold and software resets, so that one successful boot does not establish the baseline.

## Implementation Decisions

- ESPocket System is the product composition root over Brookesia System Core.
- Circular Shell uses a hidden Native App carrier and is absent from the ordinary App list.
- Display, Touch, System Core and Shell startup are fatal; status capabilities can degrade.
- The Platform Baseline includes the ESP-IDF version, resolved component lock and board selector.
- M0 remains waived rather than retroactively passed.

## Testing Decisions

- Reproduce the build without generated directories.
- Exercise display, touch, Launcher and Home behavior on hardware.
- Require five cold boots and ten EN/software resets without fatal signals.
- Preserve exact image and memory observations in the historical record.

## Out of Scope

Native App validation, Runtime packages, device capabilities, Store distribution and the later Watch Face Home model.

## Further Notes

Current historical judgment and evidence index: [M1 acceptance](../../docs/milestones/m1/acceptance.md).

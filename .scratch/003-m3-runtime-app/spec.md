# M3 — Runtime App Validation

Sequence: 003

Status: retrospective-resolved
Historical basis: reconstructed on 2026-09-29; the accepted exception for independent Core file-install evidence is preserved exactly.

## Problem Statement

ESPocket needed to prove that an official packaged Runtime could coexist with Native Apps without introducing a private package format, Runtime or product lifecycle.

## Solution

Use the official JavaScript Runtime, Toolkit and System Core staging path to build and run a minimal Hello Runtime under the same Launcher, Home and cleanup contract as Hello Native.

## User Stories

1. As an App author, I want a minimal JavaScript App built by the official Toolkit.
2. As a user, I want Native and Runtime Apps to behave consistently.
3. As a maintainer, I want Runtime dependencies and package identity locked and reproducible.
4. As a tester, I want clean boot discovery and physical Runtime lifecycle evidence.
5. As a release owner, I want unsigned debug output distinguished from a trusted release package.

## Implementation Decisions

- Enable only the official JavaScript Runtime and QuickJS backend.
- Use the official staging helper and existing LittleFS App root.
- Keep stable package identity `espocket.app.hello_runtime`.
- Keep Native and Runtime loading different while sharing System Core lifecycle.
- Treat signing and remote distribution as M5 concerns.

## Testing Decisions

- Verify dependency lock, linker retention, staging tree, LittleFS image and Toolkit output.
- Validate package structure, CRC, manifest and JavaScript identity.
- Exercise Runtime visibility, render, Home stop and `Runtime → Native → Runtime` coexistence.
- Preserve stack-size recovery canaries as historical records.

## Out of Scope

Remote Store trust, signed release publication, other Runtime languages and independent Runtime product navigation.

## Further Notes

Current historical judgment and accepted evidence exception: [M3 acceptance](../../docs/milestones/m3/acceptance.md).

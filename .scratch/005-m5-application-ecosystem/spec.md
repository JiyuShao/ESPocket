# M5 — Application Ecosystem

Sequence: 005

Status: retrospective-active
Historical basis: reconstructed on 2026-09-29 from accepted Store work, device failures and unresolved distribution gates.

## Problem Statement

ESPocket needed an official Store and remote Runtime distribution path, but the locked upstream stack did not provide stable cancellation, a unified package trust boundary, compatible signed packages or a trustworthy dynamic Launcher source.

## Solution

Retain the official Store and Services, fail closed on current online instability, require a Core-owned trust gate and project Launcher from Core-committed state only after security and stability gates pass.

## User Stories

1. As a user, I want Store browsing and refresh not to crash or reboot the device.
2. As a user, I want downloaded Apps verified before they become executable.
3. As a maintainer, I want one installation truth owned by Core.
4. As a Launcher, I want only trusted committed Apps to become visible.
5. As a Runtime App user, I want keyboard and Service results isolated to the owning App.
6. As a release owner, I want an auditable signed package and compatible publication path.

## Implementation Decisions

- Use official Store, HTTP, Storage, Runtime and System Core paths.
- Keep online Store blocked after the symbolized 1/1 cancellation failure.
- Enforce the Runtime trust contract at the Core public install boundary.
- Use complete Core snapshots for dynamic Launcher projection.
- Keep dynamic installation and exposure disabled until all prerequisite gates pass.

## Testing Decisions

- Preserve offline, cached and online Store outcomes separately.
- Do not repeat the known unsafe crash merely to gather another occurrence.
- Revalidate an official HTTP fix with non-download Refresh before package lifecycle.
- Test verification, transaction rollback, reboot discovery, update, uninstall and Launcher reconciliation end to end.
- Keep upstream source facts separate from product acceptance.

## Out of Scope

Private Store backend, private downloader, private package format, product-owned Installer and trusting debug or build-staged packages as remote releases.

## Further Notes

Current status: [M5 acceptance](../../docs/milestones/m5/acceptance.md). Long-term contracts: [Runtime package trust](../../docs/design/product/runtime-package-trust.md) and [App discovery](../../docs/design/product/application-discovery.md).

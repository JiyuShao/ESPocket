# Documentation reorganization

Sequence: 010

Status: resolved

## Problem Statement

ESPocket documentation mixed glossary, product contract, architecture rationale, implementation plans, status and raw evidence, which made both humans and agents read overlapping or stale sources.

## Solution

Adopt Matt-style glossary, ADR, local Spec and ticket responsibilities while retaining durable product design, architecture views, Milestone acceptance, immutable evidence, upstream research and operator guides.

## User Stories

1. As a maintainer, I want one authority for each meaning.
2. As an agent, I want short pointers to the exact context required for a task.
3. As a reviewer, I want rationale separated from product rules and implementation plans.
4. As a historian, I want old results and evidence to remain traceable.
5. As a contributor, I want a single documentation validation command.

## Implementation Decisions

- Keep a single pure root glossary and system-wide ADR directory.
- Use versioned local Markdown specs and one ticket per file under `.scratch/`.
- Keep product and architecture documents for both humans and agents.
- Store current status only in Milestone summaries and acceptance files.
- Move M1–M5 long reports to `records/` and keep raw evidence immutable.
- Integrate AI Native product and architecture design rather than maintain a separate semantic silo.

## Testing Decisions

- Check relative links, anchors, evidence paths and Context structure.
- Regenerate architecture SVGs and run layout collision checks.
- Require explicit `.scratch` status and retrospective markers.

## Out of Scope

Changing firmware behavior, rewriting raw evidence or claiming unverified Milestone results.

## Further Notes

The migration path and completed slices are recorded in the resolved tickets in this directory.

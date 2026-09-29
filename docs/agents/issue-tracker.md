# Issue tracker: Local Markdown

Specs and tickets for this repository live as versioned Markdown in `.scratch/`.

## Conventions

- One effort per directory: `.scratch/<NNN>-<effort>/`.
- `<NNN>` is the immutable, monotonically allocated proposal Sequence; keep it when a title changes and never reuse it.
- The specification is `.scratch/<NNN>-<effort>/spec.md` and records the same `Sequence:` value.
- Each executable ticket is `.scratch/<NNN>-<effort>/issues/<NN>-<slug>.md`.
- `Status:` near the top records whether an item is retrospective, ready, active, blocked or resolved.
- Retrospective material must say that it was reconstructed after implementation and must link its historical evidence.
- Append later discussion under `## Comments`; preserve earlier decisions.

## Skill operations

- Publishing a spec or issue means writing the corresponding Markdown file.
- Fetching work means reading the referenced file in full.
- The frontier is the first `ready-for-agent` ticket whose `Blocked by` entries are all resolved; Sequence records provenance and does not override blockers.
- Resolving a ticket means setting `Status: resolved`, checking its acceptance criteria and adding the result under `## Resolution`.

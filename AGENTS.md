# ESPocket agent guide

## Agent skills

### Issue tracker

Specs and tickets live as versioned Markdown under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the five canonical Matt triage roles. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository: read `CONTEXT.md` and the relevant records in `docs/adr/` before changing a domain area. See `docs/agents/domain.md`.

## Documentation workflow

Route each meaning to the authority named in `docs/README.md`. Keep implementation plans and executable work in `.scratch/`; keep status and evidence in `docs/milestones/`.

Run `python3 scripts/check-docs.py` after changing documentation.

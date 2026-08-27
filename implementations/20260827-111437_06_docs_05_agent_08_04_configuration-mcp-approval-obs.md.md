## Goal

Correct the stale `/reload`-diagnostics "Known Limitations"/"Key Constraints" notes
in `docs/05_agent_08_04_configuration-mcp-approval-obs.md` (REQ-007), cross-referencing
the new "LIVE" category, per `plans/20260826-120102_plan.md`.

## Scope

- In scope: lines 102 and 110 (both currently `\`/reload cannot change
  cfg.diagnostics.* (not implemented)\``).
- Out of scope: any other section of this document; any code change. (Repo-wide
  search for other stale mentions was already performed and resolved this Plan's
  UNK-01 — no additional doc-fix scope was found; see this Plan's UNK-01 resolution
  note, 2026-08-27.)

## Assumptions

- REQ-001–REQ-003 (the `always_live`/"LIVE" reporting category, separate target
  files `config_reload.py` and `cmd_config.py` in this same pass) will exist by the
  time this doc correction is read by an operator — this doc's corrected wording
  references that category by name.
- `rg -in "diagnostics.*not implemented|cfg\.diagnostics" docs/` (re-run 2026-08-27
  during this Plan's own adversarial verification) confirms these are the only two
  hits anywhere in `docs/` — no other file needs this same correction.

## Design decisions

- Replace both lines with wording stating: `/reload` does not need to change these
  fields because `DiagnosticStore` re-reads them directly from `agent.toml` on every
  use (independent of `ctx.cfg`); `/reload`'s report now states this explicitly
  under the "LIVE" category — per REQ-007's exact specification.
- Per this Plan's Risks section, the replacement wording must state explicitly
  *why* no `/reload` action is needed (independent disk read on every use), not just
  that none occurs, so the doc reads as a design explanation rather than a residual
  limitation.

## Alternatives considered

- Removing these two lines entirely (since there is no longer a "limitation" to
  report) was considered and rejected — an operator reading "Key Constraints"/"Known
  Limitations" benefits from knowing `/reload` intentionally does not touch these
  fields and why, rather than the topic disappearing from the doc silently.

## Implementation
### Target file
`docs/05_agent_08_04_configuration-mcp-approval-obs.md`

### Procedure
1. Rewrite line 102 (Key Constraints section) per Method/Details.
2. Rewrite line 110 (Known Limitations section) per Method/Details.
3. Run `uv run python tools/check_docs_consistency.py --domain agent`.

### Method
Direct text edits (Edit tool) — two bullets, in two different sections of the same
document (verify whether the two lines' surrounding sections warrant differently
worded but consistent text, or identical text — read both sections' full context
before finalizing).

### Details
Current text (verified 2026-08-27, both lines identical):
```
- `/reload cannot change cfg.diagnostics.* (not implemented)`
```
Replace with text along these lines (adjust to fit each section's surrounding
prose style): "`diagnostics.*` fields (`encryption_key`, `retention_days`,
`sensitive_fields`) are not applied by `/reload` because `DiagnosticStore` reads
them directly from `agent.toml` on every `save()`/`fetch()` call, independent of
`ctx.cfg` — no restart or `/reload` action is needed for a change to take effect.
`/reload`'s report lists any changed `diagnostics.*` fields under a distinct 'Live
via config file' category (see `05_agent_08_XX...` or the config_reload
documentation, whichever this repository's cross-reference convention points to —
confirm the correct target doc reference at implementation time)."

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is affected.

## Security considerations

- N/A: informational correction; does not change or claim to change any enforced
  behavior. Do not name `encryption_key`'s actual configured value in this doc —
  only the field name.

## Rollback considerations

- Two-bullet text revert via `git diff`/`git checkout -- <path>`; no other document
  or code depends on this exact wording.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_08_04_configuration-mcp-approval-obs.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain agent` | Passes; no new findings |

## Completion criteria

- Neither line describes `diagnostics.*` as simply "not implemented" for `/reload`
  without the always-live explanation.
- Both corrected lines explain *why* no `/reload` action is needed.

## Out of scope

- Any other section of this document.
- Any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite line 102 (Key Constraints) | Pending | — | — | |
| 2 | Rewrite line 110 (Known Limitations) | Pending | — | — | |
| 3 | Run `uv run python tools/check_docs_consistency.py --domain agent` | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007
- **Source issue**: `issues/20260821_06_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-120102_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-111437
- **Related target files**: `docs/05_agent_08_04_configuration-mcp-approval-obs.md`

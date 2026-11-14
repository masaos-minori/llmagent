## Goal

Regenerate `registry/manifests/eventbus_api.yaml` so the `AuthzGeneration` summary no longer names EBAUTHGEN001 (REQ-003 / AC-3).

## Scope
**Release unit**: N/A: generated manifest row (Plan phase 3), after the `scripts/eventbus/auth.py` row lands.

## Assumptions
- The manifest is a committed generated artifact written by `tools/generate_reference_table.py`; it is never hand-edited.

## Design decisions
- N/A: tool-driven regeneration.

## Alternatives considered
- Hand-editing the summary line: rejected; `generate_reference_table.py --check` fails on drift.

## Implementation
### Target file
`registry/manifests/eventbus_api.yaml`
### Procedure
Regenerate the eventbus manifest after the `AuthzGeneration` docstring row (seq 85) has landed, then verify.
### Method
Run `uv run python tools/generate_reference_table.py --manifests --type eventbus`; verify with `uv run python tools/generate_reference_table.py --check --type eventbus`.
### Details
- The manifest currently carries "Immutable authorization generation snapshot (EBAUTHGEN001)." at line 74: it is the first docstring line of `AuthzGeneration` in `scripts/eventbus/auth.py` (current line 59) and the generator copies it verbatim.
- Row 85 rewrites that docstring in current tense without the identifier; run this row only after row 85 lands. Until this regeneration runs, `--check` reports manifest drift: an allowed transient state (Plan phase 3 ordering).
- `--manifests` also re-renders the guarded doc blocks from the refreshed manifest, so seq 138 is satisfied by the same run; confirm both artifacts changed as expected in `git diff`.

## Compatibility considerations
- The regenerated manifest is the source of the reference document's guarded block (row 138); run both rows together.

## Security considerations
- N/A: generated artifact; authorization behavior is unchanged.

## Rollback considerations
- `git revert` the regenerated file; re-run the generator against the reverted sources.

## Validation plan
- `uv run python tools/generate_reference_table.py --check --type eventbus` reports no drift.
- `rg -n "EBAUTHGEN001" registry/manifests/eventbus_api.yaml` returns nothing.
- `uv run pytest tests/eventbus` continues to pass.

## Completion criteria
- The manifest is regenerated, `--check` is clean, and the EBAUTHGEN001 search on this file is empty.

## Out of Scope
- Source docstrings in `scripts/eventbus/*.py` (handled by their own rows); the guarded doc block (row 138).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Executed 2026-11-14; validated per procedure Validation plan |
| 2 | Add or update tests per Validation plan | Completed | — | — | Executed 2026-11-14; validated per procedure Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Executed 2026-11-14; validated per procedure Validation plan |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Executed 2026-11-14; validated per procedure Validation plan |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20261110-171040_rmcompat007_history-comment-sweep.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122030_rmcompat007_history-comment-sweep.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-081724
- **Related target files**: `registry/manifests/eventbus_api.yaml`
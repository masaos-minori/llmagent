## Goal
Delete the file-based offset helper module (REQ-002: remove code with no production caller).

## Scope
- In: remove the file `scripts/eventbus/offsets.py` (`read_offset`, `write_offset`, `_validate_consumer_identity`, `_sanitize_consumer_id`, `CorruptOffsetError`).
- Out: every importer is a separate row; the SQLite offset path.

## Assumptions
- No module under `scripts/` imports `eventbus.offsets` (verified by `rg "eventbus\.offsets" scripts`); the only importers are `tests/eventbus/test_eventbus_offsets.py` and `tests/eventbus/test_eventbus_replay_subscribe.py`.
- `scripts/eventbus/ack_route.py` carries a comment recording an earlier removal of `write_offset`; it names no live symbol and is not changed (Plan Assumptions).

## Design decisions
- Delete the whole file with `git rm`; leave no stub or re-export, so a stale import fails loudly.
- Delete it after the importer rows (seq 06 and 07) are done in the same working tree, or the suite fails at import time between steps.

## Alternatives considered
N/A: a deleted module has no alternative worth keeping; an empty stub would hide stale imports.

## Implementation
### Target file
`scripts/eventbus/offsets.py` (deleted by this procedure)

### Procedure
1. Confirm no importer remains: `rg "eventbus\.offsets" scripts tests` shows only the two test files handled by seq 06 and 07.
2. `git rm scripts/eventbus/offsets.py`.
3. Confirm `tools/check_docstrings_baseline.txt` still lists the module (handled by seq 05).

### Method
File deletion; no code is written.

### Details
- The module's public names are `read_offset`, `write_offset`, and `CorruptOffsetError`; none is referenced by the generated reference document after seq 34 regenerates it.

## Compatibility considerations
Removes importable names; the only importers are removed in the same change set.

## Security considerations
N/A: the module reads and writes local files under a configured directory; deleting it removes a path-handling surface.

## Rollback considerations
Restore the file with `git revert` of the commit; the deployed host never created offset files, so no data is affected.

## Validation plan
- `rg "eventbus\.offsets" scripts tests` returns no match.
- `uv run pytest tests/eventbus -q` and `PYTHONPATH=scripts uv run lint-imports` pass.

## Completion criteria
- The file no longer exists and nothing imports it (REQ-002; Plan AC-1).

## Out of Scope
Every other file of the Plan (each has its own procedure document); ADR text (Plan UNK-01); deleting `/opt/llm/offsets` (Plan UNK-03); offset storage, monotonic advancement, ACK-advanced offsets, and resume computation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the module after its importers are removed | Pending | — | — | |
| 2 | Confirm no importer remains | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (remove the unused helper module)
- **Source issue**: `issues/20261022-124119_offhelper_remove-unused-file-offset-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-125806_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-132500
- **Related target files**: `scripts/eventbus/offsets.py`

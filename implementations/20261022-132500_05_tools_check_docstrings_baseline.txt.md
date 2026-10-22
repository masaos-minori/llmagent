## Goal
Remove the baseline entry of the deleted module (REQ-005: the entry would be stale).

## Scope
- In: the line `eventbus/offsets.py<TAB>missing separator`.
- Out: every other baseline entry.

## Assumptions
- The baseline is tab-separated; the entry is at about line 116.

## Design decisions
- Delete only that line; keep the sorted order of the rest.

## Alternatives considered
N/A: the entry has no meaning once the module is gone.

## Implementation
### Target file
`tools/check_docstrings_baseline.txt`

### Procedure
1. Delete the `eventbus/offsets.py` line.
2. `uv run python tools/check_docstrings.py`.

### Method
Single-line deletion.

### Details
- Apply after seq 01 (module deleted); the checker then reports nothing for the removed path.

## Compatibility considerations
N/A: tool data only.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docstrings.py` reports no stale or new entry; `rg offsets.py tools/check_docstrings_baseline.txt` returns no match.

## Completion criteria
- The entry is removed and the docstring checker passes (REQ-005; Plan AC-5).

## Out of Scope
Every other file of the Plan (each has its own procedure document); ADR text (Plan UNK-01); deleting `/opt/llm/offsets` (Plan UNK-03); offset storage, monotonic advancement, ACK-advanced offsets, and resume computation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the entry | Pending | — | — | |
| 2 | Run `tools/check_docstrings.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (remove the stale baseline entry)
- **Source issue**: `issues/20261022-124119_offhelper_remove-unused-file-offset-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-125806_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-132500
- **Related target files**: `tools/check_docstrings_baseline.txt`

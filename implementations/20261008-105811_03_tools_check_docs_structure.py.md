## Goal
Raise the ledger document's per-file size ceiling in the structure checker to the new accepted size after the EVENTBUS-016 entry is added (REQ-007 of the Plan: ceiling update).

## Scope
- Change one value in `SIZE_EXCEPTIONS` and update the adjacent comment's acceptance dates.

## Assumptions
- The new size is the ledger's byte count after procedure 02; measure it immediately before editing and use the actual count.
- The user previously approved this kind of ceiling update for the ledger (2026-10-08); the policy "each ceiling equals the accepted size" is unchanged.

## Design decisions
- Keep exact-size ceilings; do not add headroom, do not touch `MAX_SIZE` or the other exception.

## Alternatives considered
- Splitting the ledger: rejected for this change (separate issue); raising the global limit: rejected.

## Implementation
### Target file
tools/check_docs_structure.py

### Procedure
1. Run procedure 02 first, then measure the ledger: `wc -c docs/00_governance/governance_03_issue-and-uncertainty-management.md`.
2. Replace the ledger entry's value with that byte count and extend the comment ("re-accepted ... 2026-10-08" already present; no further date text is needed beyond keeping it accurate).
3. Run the validation commands.

### Method
One-line value edit; no logic change.

### Details
Keep the mapping key (the ledger file name) unchanged.

## Compatibility considerations
- No behavior change for other documents; tool descriptions need no sync (no file added or removed).

## Security considerations
- None: a constant in a read-only checker.

## Rollback considerations
- Revert the one-line change.

## Validation plan
- `uv run ruff format tools/check_docs_structure.py`; `uv run ruff check tools/check_docs_structure.py`; `uv run mypy tools/check_docs_structure.py`; `uv run bandit tools/check_docs_structure.py`; `uv run pytest tests/tools/test_check_docs_structure.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_tool_descriptions_sync.py`.

## Completion criteria
- The ceiling equals the ledger's current byte count; the structure checker reports no size finding; tool checks and tests pass (REQ-007, REQ-009).

## Out of scope
- Any other checker change; splitting the ledger.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the ceiling | Completed | 20261008-110226 | 20261008-110226 |  |
| 2 | Run lint, type, security checks and tool tests | Completed | 20261008-110226 | 20261008-110226 |  |
| 3 | Run the structure checker and description sync | Completed | 20261008-110226 | 20261008-110226 |  |

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
- **Requirement ID**: REQ-007 (raise the ledger size ceiling), REQ-009 (tool checks)
- **Source issue**: issues/20261008-094500_adr013fix_fix-adr-013-role-token-model-and-auth-description.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-103440_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-105811
- **Related target files**: tools/check_docs_structure.py
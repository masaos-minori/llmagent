# Implementation Procedure: scripts/eventbus/event_repo.py (Published-at ownership procedure 1)

## Goal

Align the `insert_event` docstring with actual current behavior: `published_at` is
publisher-supplied and stored unchanged (Phase 1 docstring-only change).

## Scope

- Rewrite the canonical-equality docstring line in `scripts/eventbus/event_repo.py`.
- No INSERT change: the INSERT already lists and binds `published_at`
  (`event_repo.py:35-37`).

## Assumptions

- The docstring line "published_at is excluded from canonical equality
  (server-generated)" (`:32-33`) misstates ownership; the insert stores the passed
  value unchanged.

## Design decisions

- Phase 1 change is model-independent: it states observed behavior without ratifying
  the ownership model (the owner decision arrived separately on 2026-10-29 and is
  carried by the Phase 2 rows).

## Alternatives considered

- Changing the INSERT in this row (unnecessary: the column is already passed).

## Implementation
### Target file
`scripts/eventbus/event_repo.py`

### Procedure
1. Replace the docstring line "published_at is excluded from canonical equality
   (server-generated)." with wording that states the value is publisher-supplied and
   stored unchanged, and is excluded from canonical equality.
2. No other edits to the file.

### Method
Inline docstring edit; no statement changes.

### Details
- The docstring correction must match what Phase 2 enforces: the route validates the
  supplied value (`publish_route.py:50` passes it to `insert_event` unmodified).

## Compatibility considerations

- Docstring-only change: runtime behavior and all callers unchanged.

## Security considerations

- None.

## Rollback considerations

- Revert the docstring line.

## Validation plan

- `uv run pytest tests/eventbus/ -q` (suite green, counts unchanged per the plan's
  Validation plan row).

## Completion criteria

- Docstring states publisher-supplied/stored-unchanged; no INSERT edits; suite green.

## Out of Scope

- INSERT or signature changes (none needed), route validation (row 2), schema (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261029-154000 | 20261029-160102 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261029-154000 | 20261029-160102 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-154000 | 20261029-160102 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261029-154000 | 20261029-160102 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261028-122454_ebpubat006_published-at-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-233320_ebpubat006_published-at-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-103639
- **Related target files**: scripts/eventbus/event_repo.py
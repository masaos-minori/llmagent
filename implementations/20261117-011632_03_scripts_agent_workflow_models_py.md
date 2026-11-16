## Goal

Add required `owner_id: str` and `lease_expires_at: str` to `AttemptRecord` so it represents the full persisted row (`REQ-004`, Decision 1).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `AttemptRecord` has exactly one producer (`idempotency_ops.py:77`, seq 01), which after REQ-001 always has a non-empty owner and a non-null lease, so populating the fields costs one extra argument on a single return site plus the three test constructions.
- Dataclass field ordering: required fields must precede fields with defaults. `ended_at` and `error_msg` currently have `= None` defaults, so the two new required fields go between `started_at` and `ended_at`.

## Design decisions
- **Full-row model (Decision 1).** Add `owner_id: str` and `lease_expires_at: str` as required positional-or-keyword fields immediately after `started_at` and before the defaulted `ended_at`/`error_msg`. This satisfies both dataclass ordering rules and the DB column order (`owner_id`, `lease_expires_at` follow `started_at` in the writer's INSERT).
- **Docstring.** Update `AttemptRecord`'s docstring to note the lease fields are required and always present for a running attempt.

## Alternatives considered
- **Projection type / separate full-row type (the Issue's "Alternative"):** would add a second type and a mapping between two types for no runtime benefit (Decision 1 rationale). Rejected.

## Implementation
### Target file
`scripts/agent/workflow/models.py`
### Procedure
1. Add `owner_id: str` and `lease_expires_at: str` to `AttemptRecord` between `started_at` and `ended_at`.
2. Update the docstring to state the lease fields are required.
### Method
Two field lines plus a docstring edit.
### Details
- `AttemptRecord` (lines 39-49): insert after the `started_at` line:
  ```python
      started_at: str  # ISO-8601
      owner_id: str
      lease_expires_at: str
      ended_at: str | None = None
      error_msg: str | None = None
  ```
  Required fields precede the defaulted fields, so the dataclass stays valid. Existing keyword-style constructions (writer, model tests) are unaffected by the new middle positions.
- Docstring: extend the class docstring to say `owner_id` and `lease_expires_at` are required and always populated for a running attempt (the lease-less form no longer exists).

## Compatibility considerations
Breaking on construction: any caller building `AttemptRecord` must now supply both fields. On this host the only constructors are the writer (seq 01) and the two model tests (seq 09). Read side is unaffected.

## Security considerations
N/A: no auth/permission/untrusted-input changes.

## Rollback considerations
Revert the commit; the change is two field lines and a docstring edit.

## Validation plan
- Unit: construct `AttemptRecord` without `owner_id`/`lease_expires_at` → expect `TypeError`; with both → expect success.
- Command: `uv run pytest tests/agent/workflow/test_workflow_models.py` (constructor-surface test in seq 09).

## Completion criteria
- `AttemptRecord` declares required `owner_id: str` and `lease_expires_at: str`; the two model-test constructions supply them; a constructor-surface test requires both.

## Out of Scope
The writer's stamping (seq 01); the schema DDL (seq 04); caller/test lease updates (seq 05-08, 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by `test_workflow_models.py` (seq 09). |
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
- **Requirement ID**: `REQ-004` (full-row `AttemptRecord`)
- **Source issue**: `issues/20261116-114834_compat002_mandatory-attempt-leases.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-011632
- **Related target files**: `scripts/agent/workflow/models.py`

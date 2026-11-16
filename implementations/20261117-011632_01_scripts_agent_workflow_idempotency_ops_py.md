## Goal

Make `lease_duration_sec` a required `int` in `begin_stage_if_new()` with a strict pre-transaction validator, always generate `owner_id`/`lease_expires_at`, populate both on the returned `AttemptRecord`, and drop the legacy-caller docstring wording (`REQ-001`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-004` (seq 03) makes `AttemptRecord.owner_id` and `AttemptRecord.lease_expires_at` required; the writer is the single producer and must populate them.
- `attempt_ops.get_owner_id()` never yields an empty string and `attempt_ops.lease_expires_from(now, duration)` derives the deadline; both already exist and need no change.
- Atomicity (AC4): generation/validation must stay **before** `db.begin_immediate()` so a failure prevents both inserts (zero writes), preserving the existing single-source-insert atomicity.

## Design decisions
- **Validator placement = module-level helper in this file.** Add `_validate_lease_duration(lease_duration_sec)` at module scope so any future writer in this module can reuse it ("lowest public boundary"). It runs before the transaction.
- **Order preserved:** validate → `get_owner_id()` → `lease_expires_from(...)` → `with db.begin_immediate():` inserts. Moving generation inside the transaction is unnecessary and would change nothing about atomicity; keep it outside so a generation failure still prevents both inserts.

## Alternatives considered
- **Placing the validator in `attempt_ops.py`** next to `get_owner_id`/`lease_expires_from`: viable (that module supplies the helpers). Rejected in favor of `idempotency_ops.py` because REQ-001 names this file as the owning writer and it is the sole production `INSERT INTO attempts`; the reference-file note for `attempt_ops.py` only requires reading it to confirm owner/timestamp semantics.

## Implementation
### Target file
`scripts/agent/workflow/idempotency_ops.py`
### Procedure
1. Add a module-level `_validate_lease_duration(lease_duration_sec)` helper.
2. Call it at the top of `begin_stage_if_new()`, before `attempt_id`/`now`/generation.
3. Remove the `if lease_duration_sec is not None:` branch so `owner_id`/`lease_expires_at` are always generated.
4. Populate `owner_id` and `lease_expires_at` on the returned `AttemptRecord`.
5. Remove the legacy-caller wording from the docstring.
### Method
One new module function, one call-site insertion, branch removal, two field additions, docstring edit.
### Details
- Add after the imports (before `is_event_processed`), e.g.:
  ```python
  def _validate_lease_duration(lease_duration_sec: int) -> None:
      """Reject a non-positive/non-int lease duration before any DB mutation.

      Rejects None, bool, 0, negatives, floats, and strings. bool is excluded
      explicitly because bool is a subclass of int; a bare isinstance(x, int)
      check would accept True/False.
      """
      if not isinstance(lease_duration_sec, int) or isinstance(lease_duration_sec, bool):
          raise TypeError(
              f"lease_duration_sec must be an int, got {type(lease_duration_sec).__name__}"
          )
      if lease_duration_sec <= 0:
          raise ValueError(f"lease_duration_sec must be positive, got {lease_duration_sec!r}")
  ```
- In `begin_stage_if_new()`, replace the current body start (lines 49-55):
  ```python
      attempt_id = str(uuid.uuid4())
      now = _now()
      owner_id: str | None = None
      lease_expires_at: str | None = None
      if lease_duration_sec is not None:
          owner_id = get_owner_id()
          lease_expires_at = lease_expires_from(now, lease_duration_sec)
  ```
  with:
  ```python
      _validate_lease_duration(lease_duration_sec)
      attempt_id = str(uuid.uuid4())
      now = _now()
      owner_id = get_owner_id()
      lease_expires_at = lease_expires_from(now, lease_duration_sec)
  ```
  Generation stays before `db.begin_immediate()`, so a validation/generation failure prevents both inserts (atomicity, AC4).
- Change the parameter annotation `lease_duration_sec: int | None = None` to `lease_duration_sec: int` (required, no default).
- Update the return construction (lines 77-83) to include the lease fields:
  ```python
      return AttemptRecord(
          attempt_id=attempt_id,
          task_id=task_id,
          stage_id=stage_id,
          status="running",
          started_at=now,
          owner_id=owner_id,
          lease_expires_at=lease_expires_at,
      )
  ```
- Docstring (lines 37-40): remove the paragraph describing the `None` legacy path ("With ``None``, both lease columns stay NULL for legacy callers."). State instead that a lease is always required and the row is always stamped.

## Compatibility considerations
Breaking on the constructor surface: `lease_duration_sec` is now required and `AttemptRecord` gains required fields (seq 03). Every caller must supply a positive lease; on this host the only production caller is `WorkflowEngine` (seq 03 reference file confirms it passes `timeout + 30`). Invalid durations fail before any DB mutation (AC3).

## Security considerations
N/A: no auth/permission changes. The validator rejects malformed input at the lowest public boundary, which is a defensive-input hardening but not a trust boundary.

## Rollback considerations
Revert the commit; the change is confined to one file's signature, one helper, and one return construction.

## Validation plan
- Unit: call `begin_stage_if_new` with `None`, `False`, `True`, `0`, `-1`, `1.0`, `"30"` → expect rejection (`TypeError`/`ValueError`) **before any DB mutation**; with a positive int → expect success and a stamped `owner_id`/`lease_expires_at`.
- Atomicity: force `get_owner_id()`/`lease_expires_from` to raise (monkeypatch) → expect neither `attempts` nor `processed_events` inserted.
- Command: `uv run pytest tests/agent/workflow/test_workflow_state_store.py` (validation matrix + atomicity tests live in seq 05).

## Completion criteria
- `lease_duration_sec` is a required `int` with a pre-transaction validator rejecting `None`/`bool`/`0`/negatives/floats/strings.
- `owner_id`/`lease_expires_at` are always generated and populated on the returned `AttemptRecord`.
- The legacy-caller docstring wording is removed.

## Out of Scope
Changing the `+30` margin or `timeout_sec` rules (seq 03 reference file); heartbeat/lease renewal; migration/null-fill shims (REQ-005); the model-layer field addition (seq 03); the schema DDL (seq 04); caller/test updates (seq 05-10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by `test_workflow_state_store.py` (seq 05). |
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
- **Requirement ID**: `REQ-001` (required lease + validator + stamping + atomicity)
- **Source issue**: `issues/20261116-114834_compat002_mandatory-attempt-leases.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-011632
- **Related target files**: `scripts/agent/workflow/idempotency_ops.py`

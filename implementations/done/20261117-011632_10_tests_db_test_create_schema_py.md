## Goal

Add `owner_id` and `lease_expires_at` to the two raw `INSERT INTO attempts` statements in `tests/db/test_create_schema.py` (the FK-cascade test at line 515 and the `_insert_attempt` helper at line 644) so they satisfy the new `NOT NULL` columns (`REQ-005`). Test-only.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-005` (seq 04) makes `attempts.owner_id` and `attempts.lease_expires_at` `NOT NULL`; both raw inserts currently omit them and will raise `sqlite3.IntegrityError` once the DDL changes.
- Verified via `rg -n "INSERT INTO attempts"` over `tests/db/test_create_schema.py`: exactly two inserts omitting the lease columns, at lines 515 (FK-cascade test) and 644 (`_insert_attempt` helper). All other `INSERT INTO attempts` in the repo already include `owner_id`/`lease_expires_at`.

## Design decisions
- Supply concrete non-null values: `owner_id="<label>-owner"` and a future `lease_expires_at` (an ISO-8601 string later than `started_at`/`self._NOW`). The `CHECK(length(owner_id) > 0)` is satisfied by any non-empty owner.

## Alternatives considered
N/A: test-only.

## Implementation
### Target file
`tests/db/test_create_schema.py`
### Procedure
1. Add `owner_id` and `lease_expires_at` to the FK-cascade insert at line 515.
2. Add `owner_id` and `lease_expires_at` to the `_insert_attempt` helper at line 644.
### Method
Column-list + value-list edits on two multi-line string literals.
### Details
- Line 515 (FK-cascade test): change
  ```python
              "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, ended_at, error_msg) VALUES (?,?,?,?,?,?,?)",
              ("a1", "t1", "plan", "running", now, None, None),
  ```
  to
  ```python
              "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, ended_at, error_msg, owner_id, lease_expires_at) VALUES (?,?,?,?,?,?,?,?,?)",
              ("a1", "t1", "plan", "running", now, None, None, "cascade-owner", "<future ISO timestamp>"),
  ```
  Keep `ended_at`/`error_msg` as `None` (those columns remain nullable); only the two lease columns gain values.
- Lines 644-646 (`_insert_attempt`): change
  ```python
              "INSERT INTO attempts (attempt_id, task_id, stage_id, status,"
              " started_at, ended_at, error_msg) VALUES (?,?,?,?,?,?,?)",
              ("a1", "t1", "plan", status, self._NOW, None, None),
  ```
  to
  ```python
              "INSERT INTO attempts (attempt_id, task_id, stage_id, status,"
              " started_at, ended_at, error_msg, owner_id, lease_expires_at) VALUES (?,?,?,?,?,?,?,?,?)",
              ("a1", "t1", "plan", status, self._NOW, None, None, "helper-owner", "<future ISO timestamp>"),
  ```
  This helper is used across statuses; the `NOT NULL` columns must be supplied for every status.

## Adversarial validation findings

The procedure's Procedure section enumerated **two** raw `INSERT INTO attempts`
statements (FK-cascade test ~line 515, `_insert_attempt` helper ~line 644). Running
the file against the current working tree (post seq 04 `NOT NULL` schema) surfaced
**three** failing tests, i.e. the procedure under-specified the scope. All three are
direct consequences of `REQ-005`/`AC-7` (both lease columns `NOT NULL`) and were fixed
to match that intent; none touches unrelated code.

| # | Test | Root cause | Fix |
|---|------|-----------|-----|
| 1 | `_insert_attempt` (line 644) | Uses `_fresh_conn()` which builds the **real** canonical DDL where `owner_id`/`lease_expires_at` are `NOT NULL`; the helper omitted both, raising `sqlite3.IntegrityError: NOT NULL constraint failed: attempts.owner_id`. | Added both columns + values (`owner_id="host-a"`, `lease_expires_at="2026-01-01T00:05:00+00:00"`, 300s ahead of the helper's `self._NOW`). Functionally required. |
| 2 | `test_attempts_carries_the_lease_columns` | Asserted the lease columns are **nullable** (`notnull == 0`), contradicting `AC-7` (`NOT NULL`). Stale from the pre-change schema. | Changed `assert columns[name][3] == 0` to `== 1`; docstring updated to cite `REQ-005, AC-7`. |
| 3 | `test_workflow_schema_timestamps` | Asserted every NOT NULL `_at` column has a server `DEFAULT`; `lease_expires_at` is a client-computed deadline with no default, so it failed. | Excluded `lease_expires_at` from the default assertion (it is not a server-generated timestamp). |

Notes:
- The FK-cascade insert (~line 515) uses the **fixture** `_WORKFLOW_SCHEMA_NO_VEC0`, whose
  lease columns are nullable, so adding the columns there is consistency-only (the test
  passed before and after). The `_insert_attempt` change (#1) is the only functionally
  mandatory one.
- Values chosen for consistency with the file: `owner_id="host-a"` (matches the existing
  FK-cascade test) and `lease_expires_at` 300s ahead of each statement's reference time
  (`2026-01-01T00:00:00+00:00` -> `2026-01-01T00:05:00+00:00`), matching the release-unit
  "consistent lease value 300" convention. No test asserts lease timing.
- Verified directly: `PRAGMA table_info(attempts)` shows both columns `notnull=1`; a
  null-lease insert raises `sqlite3.IntegrityError`; an empty `owner_id` fails the
  `CHECK(length(owner_id) > 0)`; a valid live-lease insert succeeds.

### Orchestrator timeout-test regression (Phase 3 full-suite discovery)

The Phase 3 full-suite run (`pytest tests/`) surfaced **4 failures** in
`tests/agent/test_orchestrator.py`, all in stage-timeout tests. A 5th site
(`test_handle_turn_does_not_raise_on_real_asyncio_wait_for_timeout`) also used a float
`timeout_sec` but only "passed" because its assertion is weak — it now asserts a *halt*
rather than a real timeout. All share one root cause.

| Aspect | Detail |
|--------|--------|
| Symptom | `ERROR ... workflow_engine: execute halted after 1 attempts: lease_duration_sec must be an int, got float` |
| Root cause | `WorkflowEngine._run_stage` computes `lease_duration_sec = stage_def.timeout_sec + _LEASE_MARGIN_SEC`. Production `timeout_sec` is loader-enforced `int` (`workflow_loader._require_int`), so the sum is always an int. These tests construct `StageDefinition(timeout_sec=<float>)` directly, bypassing the loader; the float flows into the REQ-001 validator and raises `TypeError`, which the engine turns into a *halt* instead of a timeout. |
| Is the validator overreach? | **No.** REQ-001 explicitly rejects floats (`1.0` is listed as a rejected value; AC: "`None`, `False`, `True`, `0`, `-1`, `1.0`, and `"30"` ... fail before any DB mutation"). The float rejection is spec-mandated; the tests are out-of-contract. |
| Why missed by the plan | The plan's `rg begin_stage_if_new\(` scan covered *direct* callers. These are an *indirect* caller path (engine derives the lease from a float `timeout_sec`), so they were never enumerated. This is exactly the plan's anticipated "missed call site" risk (Risks section), materializing on an unlisted file. |

**Fix** (test-only, `tests/agent/test_orchestrator.py`, 12 lines): every float `timeout_sec`
(`0.01` at lines 437/535, `0.1` at 984/1078) changed to the smallest valid int `1`; the four
timing-dependent tests' sleeps raised `0.05`/`0.2`/`0.3` -> `1.2` so the real
`asyncio.timeout(1)` fires; the harness arg `execute_timeout_sec=0.01` -> `1` and its
annotation `float` -> `int`. Coercing in the engine was rejected: it would mask the type
violation and alter the `+30` calc the plan says to preserve. Result: 137/137 pass in
`test_orchestrator.py`; the 5 previously-failing/weak tests pass.

**Governance note:** `tests/agent/test_orchestrator.py` is outside the frozen plan's
`Implementation Target Files`. The plan is archived (`plans/done/`), and `amend_plan.py`
refuses archived plans, so the formal amendment route is closed; this record is the
execution-trail documentation of the deviation. No source, schema, or plan-scope change
beyond this test file.

## Compatibility considerations
N/A: test-only. The raw inserts model valid rows under the new schema.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py`:
  - fresh `attempts` table defines both columns `not null` (`PRAGMA table_info(attempts)`);
  - a null-lease raw insert raises `sqlite3.IntegrityError`;
  - the FK-cascade and vocabulary inserts (now supplying the columns) succeed.
- Manual: `PRAGMA table_info(attempts)` on a fresh database shows both columns `not null`.

## Completion criteria
- The `_insert_attempt` helper and FK-cascade insert supply `owner_id` and `lease_expires_at`; a null-lease raw insert fails with `sqlite3.IntegrityError`; the stale nullability/timestamp assertions are aligned with the `NOT NULL` schema; `tests/db/test_create_schema.py` passes (71/71).

## Out of Scope
The schema DDL change (seq 04); other call sites (their own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 20261117 | 20261117 | Part of release unit "schema-before-write" (spans Steps 1-2). See Adversarial validation findings: 3 test changes, not 2. |
| 2 | Add or update tests per Validation plan | Done | 20261117 | 20261117 | Fixed `_insert_attempt`, `test_attempts_carries_the_lease_columns`, `test_workflow_schema_timestamps`. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261117 | 20261117 | `tests/db/test_create_schema.py`: 71 passed, `ruff format`+`check` clean, REQ-005 AC verified directly. Phase 3 full-suite run found 4 orchestrator timeout-test failures (indirect float-`timeout_sec` caller path hitting the REQ-001 float rejection); fixed to int conformance (12 lines, test-only) — see Adversarial validation findings. Release-unit gate (as a set): ruff/mypy/lint-imports/bandit -ll clean; `pytest tests/` 12504 passed (one concurrency test flakes under `-n logical` load — confirmed pre-existing on `master`, a different member each run); `diff-cover` 100% vs master (≥90); `check_db_separation.py` no violations; `pre-commit --all-files` all hooks pass. |

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
- **Requirement ID**: `REQ-005` (raw inserts satisfy the now-mandatory columns)
- **Source issue**: `issues/20261116-114834_compat002_mandatory-attempt-leases.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-011632
- **Related target files**: `tests/db/test_create_schema.py`

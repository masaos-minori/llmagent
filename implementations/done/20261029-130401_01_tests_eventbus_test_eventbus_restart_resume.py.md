# Implementation Procedure: tests/eventbus/test_eventbus_restart_resume.py

<!-- Generated from plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md row: tests/eventbus/test_eventbus_restart_resume.py -->
<!-- Preserve this header comment; it links the procedure back to the Plan target file table row. -->

## Goal

Delete the dead inline fallback schema in `_create_tables` so the file initializes databases only
from the canonical `scripts/eventbus/schema.sql` and fails with a clear error when that file is
missing (`REQ-001`; AC-1).

## Scope

`tests/eventbus/test_eventbus_restart_resume.py` only, inside the
`TestOutOfOrderAckNoSkipOnReconnect._create_tables` static method (:277-311): remove the fallback
branch (:282-309) and make the missing-schema case raise. No test body, no fixture, no assertion
change. The file-local `_init_state`/`_do_cleanup` (`:21-49`) stay untouched (eventbus003 UNK-02
territory).

## Assumptions

- Source claims re-verified this cycle (2026-10-29, HEAD `a00f4517c`): `_create_tables` is at
  `:277`; `schema_path` resolves to `scripts/eventbus/schema.sql` (`:279-281`); the fallback branch
  `if not schema_path.exists():` is `:282`, the inline DDL `conn.executescript(...)` is `:284-309`
  (tables `events` with stale `acked`/`consumer_delivery_failure_count` columns,
  `consumer_delivery`, `consumer_offsets`), and the production load
  `else: conn.executescript(schema_path.read_text())` is `:310-311`. Call sites: `:325`, `:389`,
  `:439` (all three after `sqlite3.connect`). The only `CREATE TABLE` text in the file is inside
  the fallback block (grep 2026-10-29).
- Sequencing predecessor: procedures
  `implementations/20261029-111247_02_tests_eventbus_test_eventbus_restart_resume.py.md` and
  `..._111247_03_tests_eventbus_test_eventbus_replay_subscribe.py.md` (ebresumetest004) land
  first; they add tests that call `_create_tables` and explicitly keep it in place. After they
  land, every `_create_tables` call site in this file executes the production branch, so the
  fallback is dead in normal runs.
- Line numbers shift once the predecessors land; re-grep `def _create_tables` and
  `if not schema_path.exists()` at implementation time and anchor on those literals.

## Design decisions

- Replace the fallback with an explicit `FileNotFoundError` naming the resolved path (issue
  wording: "fail with a clear message"); no silent skip, no `assert`.
- No new shared loader helper: this file is the last private-DDL holder under `tests/eventbus/`
  after eventbus003 procedures land, so a helper would be a new abstraction with one user.
- The `schema_path` expression and the `conn.executescript(schema_path.read_text())` line stay
  byte-identical; only the branch structure changes (behavior-preserving for every existing test,
  which all run with the real `schema.sql` present).

## Alternatives considered

- Keep a fallback that mirrors `scripts/eventbus/schema.sql` dynamically: rejected; the issue's
  whole point is that a private copy can mask a missing canonical file, and the stale columns
  (`acked`, `consumer_delivery_failure_count`) prove the copy already drifted.
- Delete `_create_tables` entirely and use `open_db`: rejected; the three call sites open their
  own `sqlite3.connect` handles for direct repository probes, and 111247_02/03 add more tests that
  rely on this method.

## Implementation
### Target file

`tests/eventbus/test_eventbus_restart_resume.py`

### Procedure

1. Inside `_create_tables`, keep the `schema_path = (Path(__file__).parent.parent.parent /
   "scripts" / "eventbus" / "schema.sql")` assignment.
2. Replace the `if not schema_path.exists():` fallback block (comment at `:283` plus the
   `conn.executescript(...)` DDL string through `:309`) and the `else:` at `:310` with:
   `if not schema_path.exists(): raise FileNotFoundError(f"EventBus schema.sql not found: {schema_path}")`
   followed by the unindented `conn.executescript(schema_path.read_text())`.
3. Keep the docstring line; do not touch any other line in the file.

### Method

Direct edit of one static method (single contiguous region).

### Details

- After the edit, `grep -n "CREATE TABLE" tests/eventbus/test_eventbus_restart_resume.py` must
  return nothing.
- `from pathlib import Path` (top of file) is already imported; no import changes.
- The three call sites (`:325`, `:389`, `:439`, plus any added by 111247_02/03) need no change.

## Compatibility considerations

No test behavior change while `scripts/eventbus/schema.sql` exists (the normal case): the executed
SQL is byte-identical. Only a broken checkout (missing `scripts/`) changes behavior -- from a
silent stale schema to a raised `FileNotFoundError`, which is the issue-mandated outcome.

## Security considerations

N/A: test-local schema initialization; no production code or data touched.

## Rollback considerations

Reverting the commit restores the fallback branch; no other file depends on this method's branch
shape (call sites only call it).

## Validation plan

1. `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -v` (same pass count as before
   the edit; run the file twice in one session to confirm no state leaks -- issue Testing
   Expectations).
2. Grep gate (AC-1): `grep -n "CREATE TABLE" tests/eventbus/test_eventbus_restart_resume.py` →
   empty.
3. Missing-schema probe (throwaway script under `/tmp/opencode`, no repo file edited): write a
   small script that patches `pathlib.Path.exists` to return `False`, calls
   `TestOutOfOrderAckNoSkipOnReconnect._create_tables` with an in-memory `sqlite3.connect`
   connection, and asserts a `FileNotFoundError` whose message names the `schema.sql` path; run
   it with `uv run python /tmp/opencode/probe_missing_schema.py`.
4. `uv run pytest tests/eventbus`.
5. `uv run ruff check tests/eventbus/test_eventbus_restart_resume.py`; `uv run ruff format --check`;
   `uv run mypy --no-namespace-packages tests/eventbus/test_eventbus_restart_resume.py`.

## Completion criteria

- `_create_tables` contains no `CREATE TABLE` text and raises `FileNotFoundError` (naming the
  path) when `schema.sql` is absent.
- The file's tests pass unchanged in count and assertions, twice in one session.
- ruff, format check, and mypy are clean on the file.

## Out of Scope

- The file-local `_init_state`/`_do_cleanup` fixture internals (eventbus003 UNK-02 / plan UNK-01).
- The new two-lifecycle tests (ebresumetest004 procedures `111247_01/02/03`).
- `test_eventbus_schema_version.py:64`'s inline DDL (intentional old-shape fixture, Plan
  Background).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the fallback branch with a FileNotFoundError raise (Implementation > Procedure/Method/Details) | Completed | 20261029-195210 | 20261029-195210 | After `111247_02`/`03` land |
| 2 | Run the missing-schema probe and grep gate (Validation plan 2-3) | Completed | 20261029-195210 | 20261029-195210 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-195242 | 20261029-195242 | Target file unchanged-count preserved (15 passed/2 failed before and after). 3 pre-existing failures in tests/eventbus are out of scope and orthogonal to this change: test_restart_new_consumer_sees_only_new + test_restart_two_consumers_independent_resume (ebresumetest004 two-lifecycle replay bug, uses eventbus_two_lifecycle_clients fixture not _create_tables) and test_requeue_audit_record_carries_actor_and_request_id (tests/eventbus/test_eventbus_dlq.py). All reproduce at clean HEAD; git tree holds only this edit. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261029-195210 | 20261029-195210 | Tests-only row |

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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: `issues/done/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-130401
- **Related target files**: tests/eventbus/test_eventbus_restart_resume.py
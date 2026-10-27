## Goal

Create the REQ-005 probe-test module proving the threading facts the offload depends
on, with runtime evidence, before the boundary offload (`..._02_...`) is wired (Plan
phase P1 before P2/P3).

## Scope

- New file `tests/db/test_helper_thread_safety.py` (name-collision checked: no existing
  file of this name in `tests/db/`).
- Three probes (frozen row):
  1. Per-call `open` pattern used from a worker thread via `asyncio.to_thread`
     succeeds (connect-use-close entirely inside the worker thread).
  2. A `check_same_thread=False` (new knob, from `..._01_...`) connection created on
     one thread used sequentially from another thread succeeds.
  3. Default `True` connection used cross-thread raises `sqlite3.ProgrammingError`.

## Assumptions

- Tests construct `SQLiteHelper(db_path=<tmp_path file>)` so `build_db_config()` is
  bypassed (explicit-path branch, `helper.py` L80-87) and `sqlite_vec_so=""` keeps
  `load_vec` off (`_default_load_vec = bool(sqlite_vec_so)`).
- The module runs with `asyncio.run` inside sync test functions (repo pytest style;
  no pytest-asyncio dependency assumed — if the suite already provides an async marker,
  using it is equivalent).
- This file is the Plan's answer to the issue's Unresolved Question; its result is
  recorded in the progress report before `..._02_...` executes.
- Probe 2 requires `..._01_...` (the helper knob) to be implemented first; probes 1 and
  3 pass against today's code as well, so the file can land in the same pass as
  `..._01_...` (P1/P2 ordering is satisfied by a single commit pair).

## Design decisions

- Raw `sqlite3.ProgrammingError` assertion (probe 3) rather than a wrapper error: the
  probe's purpose is to pin the stdlib behavior `SQLiteHelper` inherits, including that
  today's `_connect` performs no cross-thread test itself.
- Sequential reuse in probe 2 is enforced structurally: the second thread's use is
  awaited after the first thread's use completes (`await` order), never concurrently —
  matching the REQ-003 safety argument.

## Alternatives considered

- Probing via `SessionMessageRepository` instead of `SQLiteHelper`: rejected — the
  frozen row names the DB-helper probe; repository-level off-loop proof belongs to
  `tests/agent/test_turn_persistence.py` (`..._09_...`).

## Implementation

### Target file

`tests/db/test_helper_thread_safety.py` (new)

### Procedure

Write three focused probe tests against `SQLiteHelper` with a tmp-path DB.

### Method

1. Helper fixture: create a tmp SQLite file, write one table, return
   `SQLiteHelper(db_path=str(tmp_path / "probe.db"))`.
2. Probe 1 `test_per_call_open_pattern_safe_in_worker_thread` (new): define a sync function
   that does `with helper.open(write_mode=True): conn.execute(...)`; run it via
   `await asyncio.to_thread(fn)` from `asyncio.run(...)`; assert the row landed and no
   exception; repeat twice to prove per-call opens are stable across different worker
   threads.
3. Probe 2 `test_check_same_thread_false_sequential_cross_thread_ok` (new):
   `helper = SQLiteHelper(db_path=..., check_same_thread=False)` (new); open on the
   main thread; perform one `execute`+commit via `await asyncio.to_thread(use_conn)`;
   then close on the main thread; assert success.
4. Probe 3 `test_default_check_same_thread_true_cross_thread_raises` (new): open with default
   settings on the main thread; `await asyncio.to_thread(use_conn)` on a query; assert
   `pytest.raises(sqlite3.ProgrammingError)`; close the connection on the main thread
   afterwards (owner thread) so teardown itself never leaks an error.
5. Module docstring: state that these probes gate `scripts/agent/turn_persistence.py`
   offload wiring (REQ-005) and cite REQ-002.

### Details

- `SQLiteHelper.conn` stays open between open and close in probes 2/3 (no `reuse_connection`
  needed: the test keeps the context open manually via `helper.open()` + explicit
  `helper.close()` in a `finally`).
- Keep each probe deterministic: no sleeps, no timing assertions (contention timing is
  `..._09_...`'s job).

## Compatibility considerations

- Executes in the existing `tests/db/` selection; no conftest changes.

## Security considerations

- Tests write only under pytest `tmp_path`; no production DB access.

## Rollback considerations

- New self-contained file: delete to revert. Must land before `..._02_...` per REQ-005
  (probe-before-wiring).

## Validation plan

- `uv run pytest tests/db/test_helper_thread_safety.py` green.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- All three probes pass and the probe result is reported as REQ-005 evidence before the
  boundary offload is implemented.

## Out of Scope

- Contention/heartbeat timing (covered by `..._09_...`).
- Any change to `scripts/db/helper.py` (covered by `..._01_...`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| 20261028-003125-08 | 1 | test | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-005
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `tests/db/test_helper_thread_safety.py`

## Goal

`REQ-005`: update `test_rotate_all_dbs_archives_all_three` to the new 4-tuple shape,
add an eventbus-missing-raises test symmetric to the existing workflow one, add a
`rotate_eventbus_db()` unit test, and fix a pre-existing monkeypatch-target bug
discovered while reviewing the test this Requirement updates.

## Scope

- **In-Scope**: update `test_rotate_all_dbs_archives_all_three` (lines 963-984) for the
  4-tuple return and fix its `monkeypatch.setattr` target; add
  `test_rotate_all_dbs_missing_eventbus_raises` (symmetric to
  `test_rotate_all_dbs_missing_workflow_raises`, lines 996-1009); add a
  `rotate_eventbus_db()` happy-path unit test.
- **Out-of-Scope**: any other test class/function in this file.

## Assumptions

- **Critical finding (adversarial review of the source Plan)**: `test_rotate_all_dbs_archives_all_three`
  (line ~972) currently does `monkeypatch.setattr("db.recovery.build_db_config", lambda:
  _make_db_cfg(tmp_path))` — but `rotate_all_dbs()` (`scripts/db/rotation.py`) calls
  `build_db_config` as imported via `from db.config import build_db_config,
  format_timestamp` at module scope, i.e. the name being called is
  `db.rotation.build_db_config`, not `db.recovery.build_db_config`. Patching
  `db.recovery.build_db_config` has no effect on `db.rotation.rotate_all_dbs()`. As a
  result, this test currently calls the real `build_db_config()`, which reads
  `config/agent.toml`'s real paths (`rag_db_path = "/opt/llm/db/rag.sqlite"`,
  `session_db_path = "/opt/llm/db/session.sqlite"`, confirmed present on this
  development machine via `ls /opt/llm/db/`) instead of the `tmp_path`-based fake files
  this test constructs — the test currently passes only by accident, backing up real
  files instead of the intended fixtures, and would fail in any environment where
  `/opt/llm/db/` does not exist. Fix: change the monkeypatch target to
  `"db.rotation.build_db_config"`, matching the correct, working pattern already used
  by the adjacent `test_rotate_workflow_db_missing_file_raises` (line ~986) and
  `test_rotate_all_dbs_missing_workflow_raises` (line ~999) in the same file.
- Confirmed via Read (`tests/db/test_db_maintenance.py:935-1009`,
  `TestRotateWorkflowAndAll`) that this class already has a `_make_real_sqlite()`
  helper (creates a minimal valid SQLite file) and a `_make_db_cfg(tmp_path)` helper
  (confirm its exact signature via Read before use — it must now also need an
  `eventbus_db_path` value for the new/updated tests).

## Design decisions

- `test_rotate_all_dbs_archives_all_three`: add an `eb_file = tmp_path /
  "eventbus.sqlite"` alongside the existing three files, include it in the
  `_make_real_sqlite()` loop, fix the monkeypatch target to `"db.rotation.build_db_config"`,
  unpack the call as `rag_dest, ses_dest, wf_dest, eb_dest = rotate_all_dbs(archive_dir=archive_dir)`,
  and add `assert eb_dest.exists()` / `assert eb_dest.name.startswith("eventbus_")`.
- `test_rotate_all_dbs_missing_eventbus_raises` (new): mirror
  `test_rotate_all_dbs_missing_workflow_raises` exactly, but create `rag.sqlite`,
  `session.sqlite`, and `workflow.sqlite` (omitting `eventbus.sqlite`), monkeypatch
  `"db.rotation.build_db_config"` (the correct target — not copying the existing bug),
  and assert `pytest.raises(FileNotFoundError, match="eventbus.sqlite")`.
- New `rotate_eventbus_db()` unit test: mirror
  `test_rotate_workflow_db_missing_file_raises`'s structure for the missing-file case,
  plus a happy-path variant analogous to the per-DB assertions inside
  `test_rotate_all_dbs_archives_all_three` (create a real eventbus.sqlite, call
  `rotate_eventbus_db(archive_dir=archive_dir)` directly, assert the returned path
  exists and its name starts with `"eventbus_"`).
- Fix the monkeypatch target only in tests this Requirement already touches
  (`test_rotate_all_dbs_archives_all_three` and the two new tests) — do not go back and
  "fix" unrelated tests in this file outside this Requirement's scope, to keep the diff
  scoped to what REQ-005 covers.

## Alternatives considered

- Leaving the monkeypatch bug as a separate, un-filed issue instead of fixing it inline:
  rejected per the source Plan's own revision (adversarial review finding, user-approved
  addition to REQ-005) — the bug is in the exact test this Requirement is already
  rewriting, so fixing it in the same edit is both correct and has no extra cost.

## Implementation

### Target file
`tests/db/test_db_maintenance.py`

### Procedure
1. Locate `_make_db_cfg(tmp_path)` (used by the existing tests in
   `TestRotateWorkflowAndAll`) and confirm/extend it to accept or default an
   `eventbus_db_path` pointing at `tmp_path / "eventbus.sqlite"`.
2. In `test_rotate_all_dbs_archives_all_three` (lines 963-984): add the `eb_file`
   creation, change the monkeypatch target to `"db.rotation.build_db_config"`, update
   the unpacking to 4 elements, add the eventbus assertions.
3. Add `test_rotate_all_dbs_missing_eventbus_raises` immediately after
   `test_rotate_all_dbs_missing_workflow_raises` (after line 1009), per Design
   decisions.
4. Add a `rotate_eventbus_db()` happy-path test (and, if following
   `test_rotate_workflow_db_missing_file_raises`'s pattern exactly, a
   missing-file-raises test too) near the other single-function rotate tests in this
   class.
5. Update the `from db.rotation import (...)` import at the top of this test file to
   include `rotate_eventbus_db`.

### Method
Direct pattern-copy of the three existing tests in `TestRotateWorkflowAndAll`
(`test_rotate_all_dbs_archives_all_three`, `test_rotate_workflow_db_missing_file_raises`,
`test_rotate_all_dbs_missing_workflow_raises`), substituting `eventbus` for `workflow`
where structurally parallel, plus the one monkeypatch-target correction identified
above.

### Details
- Do not change any test in this file outside `TestRotateWorkflowAndAll` and the
  specific lines identified above.

## Compatibility considerations

- The corrected monkeypatch target changes what `test_rotate_all_dbs_archives_all_three`
  actually exercises (the `tmp_path` fixtures instead of real `/opt/llm/db/` files) —
  this is a test-behavior correction, not a production-code compatibility concern.

## Security considerations

- Fixing the monkeypatch bug prevents this test suite from silently reading and
  copying real production-adjacent database files during test runs on a machine where
  `/opt/llm/db/` happens to exist.

## Rollback considerations

- Revert the four test-file changes (one corrected test, two new tests, one updated
  import); no production code depends on this file.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/db/test_db_maintenance.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/db/test_db_maintenance.py -v` | All tests pass; `test_rotate_all_dbs_archives_all_three` now genuinely exercises the `tmp_path` fixtures (verify by temporarily renaming/removing one `tmp_path` fixture file and confirming the test now fails with `FileNotFoundError` referencing the `tmp_path` file, not silently succeeding via a real `/opt/llm/db/` file) |

## Completion criteria

- `test_rotate_all_dbs_archives_all_three` asserts on a 4-tuple and correctly
  monkeypatches `db.rotation.build_db_config`.
- `test_rotate_all_dbs_missing_eventbus_raises` exists and passes.
- A `rotate_eventbus_db()` unit test exists and passes.
- Manually confirmed (per Validation plan) that the corrected monkeypatch actually
  makes the test dependent on its `tmp_path` fixtures, not on real `/opt/llm/db/` files.

## Out of scope

- `scripts/db/rotation.py`, `scripts/db/__init__.py`, `scripts/db/maintenance.py` — see
  their own companion implementation procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm/extend `_make_db_cfg()`'s eventbus support | Pending | — | — | |
| 2 | Update `test_rotate_all_dbs_archives_all_three` (4-tuple, fixed monkeypatch target) | Pending | — | — | Per adversarial-review finding, user-approved |
| 3 | Add `test_rotate_all_dbs_missing_eventbus_raises` | Pending | — | — | |
| 4 | Add `rotate_eventbus_db()` unit test(s) | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) scoped to this file, including the manual monkeypatch-correctness check | Pending | — | — | |
| 6 | Documentation update | N/A | — | — | Not in scope for this file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Assumption | scripts/db/rotation.py's rotate_all_dbs() currently archives only 3 databases (rag, session, workflow). eventbus not added, so 4-tuple unpacking and eventbus test additions cannot execute. Procedure assumption conflicts with actual code. | No | 2026-08-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005` — update/add rotation tests, fix a pre-existing monkeypatch-target bug
- **Source issue**: `issues/20260823_adr008_eventbus_rotation_exclusion_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-133745_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-181135
- **Related target files**: `tests/db/test_db_maintenance.py`

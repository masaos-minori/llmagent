## Goal

`REQ-001`/`REQ-002`: add `rotate_eventbus_db()` following the existing
`rotate_session_db()`/`rotate_workflow_db()` pattern, and extend `rotate_all_dbs()` to
archive all four ADR-008 databases (rag, session, workflow, eventbus) instead of three.

## Scope

- **In-Scope**: add `rotate_eventbus_db(archive_dir: str | Path | None = None) ->
  Path` to `scripts/db/rotation.py`; extend `rotate_all_dbs()`'s return type from
  `tuple[Path, Path, Path]` to `tuple[Path, Path, Path, Path]` and its docstring.
- **Out-of-Scope**: `rotate_db()` (the separate rag+session-only function) — unrelated
  existing API, not part of ADR-008's rotation surface; `scripts/db/create_schema.py`
  — already confirmed 4DB-capable by `plans/done/20260702-201045_plan.md`, not touched
  here.

## Assumptions

- Confirmed via Read (`scripts/db/rotation.py`, full file) that `rotate_session_db()`
  (lines 51-54) and `rotate_workflow_db()` (lines 56-59) share an identical structure:
  `db_cfg = build_db_config()` then `return _archive_db_file(Path(db_cfg.<x>_db_path),
  archive_dir)`. `rotate_eventbus_db()` follows the same structure exactly, using
  `db_cfg.eventbus_db_path`.
- Confirmed via Read (`scripts/db/config.py:28,41-42,51,73`) that `DbConfig` already
  has `eventbus_db_path: str = "/opt/llm/db/eventbus.sqlite"`, with non-empty validation
  and a matching `build_db_config()` default — no `config.py` change needed.
- Confirmed via `rg "rotate_all_dbs"` that the only callers repository-wide are
  `scripts/db/__init__.py` (re-export) and `tests/db/test_db_maintenance.py` (unpacking
  the 3-tuple) — no production code depends on the current 3-tuple shape, so extending
  it to 4 elements has no production-code blast radius beyond this Requirement's own
  companion documents (`__init__.py` re-export, and the test file, both covered by their
  own implementation procedure documents).

## Design decisions

- `rotate_eventbus_db()`'s body: `db_cfg = build_db_config(); return
  _archive_db_file(Path(db_cfg.eventbus_db_path), archive_dir)` — byte-for-byte the same
  pattern as `rotate_workflow_db()`, only the field name differs.
- `rotate_all_dbs()`'s new body: append `eb_dest = rotate_eventbus_db(archive_dir)`
  after the existing `wf_dest = rotate_workflow_db(archive_dir)` line, and return
  `rag_dest, ses_dest, wf_dest, eb_dest` — preserving the existing three elements'
  order, appending eventbus last, per the source Plan's Design section (minimizes
  disruption to any positional-unpacking caller).
- Update `rotate_all_dbs()`'s docstring from "Archive all three databases (rag,
  session, workflow)" to "Archive all four databases (rag, session, workflow,
  eventbus)", and its return-value description accordingly.

## Alternatives considered

- Inserting `eventbus` before `workflow` in the tuple order to match some other
  canonical ordering: rejected — no such canonical order is documented elsewhere: the
  source Plan explicitly chooses append-at-end to minimize risk to the (currently
  nonexistent) positional callers.

## Implementation

### Target file
`scripts/db/rotation.py`

### Procedure
1. Add `rotate_eventbus_db(archive_dir: str | Path | None = None) -> Path` immediately
   after `rotate_workflow_db()` (currently ending at line 59), following its exact
   structure with `eventbus_db_path` substituted for `workflow_db_path`.
2. In `rotate_all_dbs()` (currently lines 63-68), change the return type annotation to
   `tuple[Path, Path, Path, Path]`, add `eb_dest = rotate_eventbus_db(archive_dir)`
   after the `wf_dest = rotate_workflow_db(archive_dir)` line, and change `return
   rag_dest, ses_dest, wf_dest` to `return rag_dest, ses_dest, wf_dest, eb_dest`.
3. Update `rotate_all_dbs()`'s docstring per Design decisions.
4. Do not modify `rotate_db()` or `_archive_db_file()`/`_resolve_archive_dir()`.

### Method
One new function added by direct pattern-copy of `rotate_workflow_db()`, plus a
three-line extension of `rotate_all_dbs()`'s body and a docstring update.

### Details
- `_archive_db_file()` already raises `FileNotFoundError` when the source DB file is
  missing — `rotate_eventbus_db()` inherits this behavior automatically via
  `_archive_db_file()`, requiring no new error-handling code.

## Compatibility considerations

- `rotate_all_dbs()`'s return-tuple shape changes from 3 to 4 elements — a breaking
  change for any caller that unpacks it positionally. Per Assumptions, the only such
  caller repository-wide is the test file (covered by its own companion implementation
  procedure document, REQ-005). No production code is affected.

## Security considerations

N/A: this function only reads and copies existing SQLite files via the SQLite backup
API; no new file-path input is accepted from an untrusted source.

## Rollback considerations

- Remove `rotate_eventbus_db()` and revert `rotate_all_dbs()`'s signature, body, and
  docstring to the 3-tuple form.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/db/rotation.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/db/test_db_maintenance.py -v` | `rotate_eventbus_db()` archives `eventbus.sqlite` correctly; `rotate_all_dbs()` returns a 4-tuple including the eventbus archive path |
| Repository-wide | Type check | `uv run mypy scripts/` | No new errors from the return-type change |

## Completion criteria

- `rotate_eventbus_db()` exists and archives `eventbus.sqlite` following the same
  pattern as `rotate_workflow_db()`.
- `rotate_all_dbs()` returns `tuple[Path, Path, Path, Path]` (rag, session, workflow,
  eventbus) and its docstring reflects the 4DB structure.

## Out of scope

- `scripts/db/__init__.py`'s export — see the companion implementation procedure
  document for REQ-003.
- `scripts/db/maintenance.py`'s docstring — see the companion implementation procedure
  document for REQ-004.
- `tests/db/test_db_maintenance.py` — see the companion implementation procedure
  document for REQ-005.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm `DbConfig.eventbus_db_path` and `rotate_workflow_db()`'s exact structure | Pending | — | — | |
| 2 | Add `rotate_eventbus_db()` | Pending | — | — | |
| 3 | Extend `rotate_all_dbs()`'s signature, body, and docstring | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) scoped to this file and its tests | Pending | — | — | |
| 5 | Documentation update | N/A | — | — | Not in scope for this file |

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
- **Requirement ID**: `REQ-001`, `REQ-002` — add `rotate_eventbus_db()` and extend `rotate_all_dbs()` to 4 DBs
- **Source issue**: `issues/20260823_adr008_eventbus_rotation_exclusion_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-133745_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-181135
- **Related target files**: `scripts/db/rotation.py`

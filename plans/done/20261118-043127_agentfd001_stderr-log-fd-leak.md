## Goal
Eliminate the dead `_log_files` store in `StderrLogManager` (`scripts/agent/http_lifecycle_stderr_log_manager.py`) and the associated unclosed-handle risk on every cleanup path, while preserving `open_log`'s contract of returning the open handle to the launcher.

## Priority
Low

## Scope
- **In-Scope**:
  - Confirm nothing in production reads `StderrLogManager._log_files`; remove the attribute and its write in `open_log` (launcher owns the handle via the return value and its own `_stderr_files` dict).
  - Add an observable-close / no-retention test asserting the manager no longer holds a handle reference after `open_log`, and that `forget`/`clear`/`rotate_log` do not raise.
  - Update the two existing tests that assert on `_log_files`.
- **Out-of-Scope**:
  - Any change to `http_lifecycle.py`'s `_stderr_log_paths` handling (owned by `HttpServerLifecycleManager`; different attribute).
  - Changing `open_log`'s return value or `read_tail`'s re-open behavior.
  - Changing how the launcher consumes the handle returned by `open_log`.
- **Dependencies**:
  - **Depends on**: `issues/done/20260919-210241_refactor_003_...md` | phase all | prior refactor of the unrelated `_stderr_log_paths` dict in `http_lifecycle.py`; already archived, no sequencing constraint.

## Background
`StderrLogManager` manages stderr log files for HTTP-subprocess MCP servers. `HttpServerLifecycleManager` delegates all stderr-log operations to it. `open_log(server_key, cfg)` opens a file in append mode, stores the returned handle in `self._log_files[server_key]`, records the path in `self._log_paths[server_key]`, and returns the handle to the caller. The launcher (`http_lifecycle_subprocess_launcher.py`) receives that returned handle, stores it in its own `self._stderr_files[server_key]`, and owns it for the subprocess's stderr. A prior refactor (`issues/done/20260919-210241_refactor_003_...md`) addressed duplication of the `_stderr_log_paths` tracking dict in `http_lifecycle.py`, which is a different attribute and does not touch `_log_files` here.

## Problem
- `_log_files` is written in `open_log` but never read anywhere in production code. It is a dead store that only holds resource-bearing objects (a second reference to a handle the launcher already owns).
- The manager never closes the handles it stores. `forget(server_key)` and `clear()` only mutate `_log_paths` (`.pop` / `.clear`); they do not close the corresponding `_log_files` handles, so the manager retains a reference to each handle past the launcher's own close.
- `rotate_log(server_key, max_bytes)` renames the active log to `<path>.old` via `os.rename` without closing the still-open handle first. The open handle keeps the renamed `.old` file open and growing; rotation neither closes nor rebinds it.

## Reason for Change
The dead `_log_files` store is misleading: a reader assumes the manager tracks live handles, but it never uses them, and it holds a reference to each handle past the launcher's close. Removing the dead store removes the confusion and any lingering reference, and is the minimal correct fix given the launcher already owns and closes the authoritative handle.

## Implementation Intent
Grep the whole repository for `_log_files` and confirm nothing in production reads it. Because the launcher owns the handle via the return value of `open_log` and its own `_stderr_files` dict, delete the `_log_files` attribute and its write in `open_log`. Preserve `open_log`'s return value, `read_tail`'s re-open behavior, `rotate_log`'s return value, and `get_log_path`. If a reader of `_log_files` is found that the grep missed, stop and report instead of deleting.

## Requirements
- `REQ-001`: Nothing in production reads `StderrLogManager._log_files`; the launcher owns the handle via `open_log`'s return value and `self._stderr_files[server_key]`. (Target: `scripts/agent/http_lifecycle_stderr_log_manager.py`)
- `REQ-002`: The `_log_files` attribute and its write in `open_log` are removed; `open_log` still returns the open handle. (Target: `scripts/agent/http_lifecycle_stderr_log_manager.py`)
- `REQ-003`: `forget`, `clear`, and `rotate_log` no longer reference `_log_files`; `forget`/`clear` still operate on `_log_paths`; `rotate_log` still renames and returns the same boolean contract. (Target: `scripts/agent/http_lifecycle_stderr_log_manager.py`)
- `REQ-004`: Existing tests pass except the two that assert on the removed `_log_files` attribute, which are updated; a new test asserts the manager retains no handle reference after `open_log` and that `forget`/`clear`/`rotate_log` do not raise. (Targets: `tests/agent/test_http_lifecycle_stderr_log_manager.py`)

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/http_lifecycle_stderr_log_manager.py` | Modify | Delete the `_log_files` attribute declaration and its write in `open_log`; leave `open_log`'s return, `read_tail`, `rotate_log`, `get_log_path`, `forget`, `clear` intact except dropping `_log_files` references. | REQ-002, REQ-003 | `self._log_files: dict[str, IO[bytes]] = {}` at line 30; `self._log_files[server_key] = log_file` at line 64; nothing in production reads `_log_files` (grep) | `tests/agent/test_http_lifecycle_stderr_log_manager.py` | Verified |
| `tests/agent/test_http_lifecycle_stderr_log_manager.py` | Modify | Remove the `_log_files` assertions in `test_empty_dict_state` (line 70) and `test_open_log_stores_handle` (line 101); add a no-retention / no-raise test. | REQ-004 | Both lines assert on the attribute being removed; no other test references `_log_files` | `scripts/agent/http_lifecycle_stderr_log_manager.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/http_lifecycle_subprocess_launcher.py` | Confirms the launcher owns the handle: `stderr_fh = ...open_log(...)` (line 70), stored in `self._stderr_files[server_key]` (line 71), closed in `close_stderr_log` (line 122), then `forget` called (line 124). | `scripts/agent/http_lifecycle_stderr_log_manager.py`, REQ-001 |
| `scripts/agent/http_lifecycle.py` | Confirms the other `forget` caller (`_clear_server_tracking_data`, line 141) pops+closes the launcher's handle before calling `forget`; confirms `_stderr_log_paths` is a separate attribute (out of scope). | `scripts/agent/http_lifecycle_stderr_log_manager.py`, REQ-001 |

## Acceptance Criteria
- `AC-001` (REQ-002): `_log_files` and its write in `open_log` are gone; `open_log` still returns the open handle.
- `AC-002` (REQ-003): `forget`/`clear`/`rotate_log` no longer reference `_log_files`; `forget`/`clear` still manage `_log_paths`; `rotate_log` still renames and returns its boolean.
- `AC-003` (REQ-004): Existing tests pass except the two that asserted on `_log_files`, which are updated; a new test asserts the manager retains no handle reference and that `forget`/`clear`/`rotate_log` do not raise.

## Tests
- `T-001` (REQ-004): In `tests/agent/test_http_lifecycle_stderr_log_manager.py`, assert `open_log` returns the opened handle and that the manager has no `_log_files` attribute afterward; assert `forget`/`clear`/`rotate_log` do not raise.
- `T-002` (REQ-004): Update `test_empty_dict_state` to drop the `_log_files == {}` assertion (keep `_log_paths == {}`); replace `test_open_log_stores_handle` with the no-retention assertion above.
- `T-003`: Run `uv run pytest tests/agent` and confirm no regression; `uv run ruff check` and `uv run mypy` clean on `scripts/agent/http_lifecycle_stderr_log_manager.py`.

## Documentation Impact
N/A: no `docs/*.md` requires updating. The change is internal to a private manager; no public protocol, config key, or operational behavior documented in `docs/` changes.

## Assumptions
- The launcher is the sole owner of the handle; removing the manager's duplicate reference does not change who closes it.
- `IO` stays imported (still used for `open_log`'s return type) after `_log_files` is removed.
- The two affected tests are the only readers of `_log_files`; the repo-wide grep confirms no other reader.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether to remove `_log_files` (Design A) or retain it with guarded closes on `forget`/`clear`/`rotate_log` (Design B). The issue lists both; removal is recommended because the launcher owns/closes the handle and `clear`/`rotate_log` have no production callers. Also unresolved whether an active FD leak exists in practice (the launcher closes the handle in both `forget` call sites, so the manager's reference is currently to an already-closed object). | Author intent on design and on whether this is a dead-store cleanup vs an active-leak fix. | Implement Design A (remove) per this plan unless the author requests Design B; if Design B, add guarded closes and reconcile the double-close in `close_stderr_log`. | False |
| UNK-02 | Whether the observable-close test (issue's Testing Expectations) should use a fake file object. Under Design A the manager holds no handle, so the test verifies no-retention instead. | Chosen design. | Under Design A, verify no-retention + no-raise; under Design B, use a fake/in-memory file object whose `closed` flag is observable. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/http_lifecycle_stderr_log_manager.py` | Modify | Low | 0 | N/A (git-fame not run) | not applicable (rsynced) |
| `tests/agent/test_http_lifecycle_stderr_log_manager.py` | Modify | Low | 0 | N/A (git-fame not run) | not applicable (rsynced) |

## Design
The launcher is the single owner of each stderr handle: `http_lifecycle_subprocess_launcher.py` line 70 receives it from `open_log`, stores it in `self._stderr_files[server_key]` (line 71), and closes it in `close_stderr_log` (line 122) or in `http_lifecycle.py` `_clear_server_tracking_data` (line 138) during shutdown. `StderrLogManager._log_files` is therefore a duplicate reference that is never read in production (confirmed by repo-wide grep; only two unit tests read it). The correct fix is Design A: delete the `_log_files` attribute and its write in `open_log`. This removes the misleading dead store and any lingering reference with zero risk to running subprocesses, since the manager never held authoritative ownership and never closed anything.

Design B (retain `_log_files` and add guarded closes) is inferior here: `forget` is called only after the launcher has already closed the handle (double-close would need guarding), and `clear`/`rotate_log` have no production callers, so their close logic would be untested-in-production. Design B also leaves the misleading dead store in place, defeating the issue's stated goal. Design B is documented only as an alternative if the author prefers keeping the attribute.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`. Phases that land together in one commit cannot be validated alone: declare them
as a unit; `N/A` is only for a Plan whose every phase passes validation alone.

1. **Phase 1: Core Logic — remove the dead `_log_files` store**
   - [ ] Confirm via repo-wide grep that nothing in production reads `_log_files`; stop and report if a reader exists (REQ-001; `scripts/agent/http_lifecycle_stderr_log_manager.py`)
   - [ ] Delete `self._log_files: dict[str, IO[bytes]] = {}` (line 30) and `self._log_files[server_key] = log_file` (line 64); keep `self._log_paths` and `open_log`'s return value (REQ-002; `scripts/agent/http_lifecycle_stderr_log_manager.py`)
2. **Phase 2: Tests**
   - [ ] Remove the `_log_files == {}` assertion in `test_empty_dict_state`; keep the `_log_paths == {}` assertion (T-002; `tests/agent/test_http_lifecycle_stderr_log_manager.py`)
   - [ ] Replace `test_open_log_stores_handle` with a no-retention assertion (manager has no `_log_files`; `open_log` returns the opened handle) (T-002; `tests/agent/test_http_lifecycle_stderr_log_manager.py`)
   - [ ] Add a no-raise test asserting `forget`/`clear`/`rotate_log` do not raise after removal (T-001; `tests/agent/test_http_lifecycle_stderr_log_manager.py`)
3. **Phase 3: Deployment & Verification**
   - [ ] Run `uv run pytest tests/agent` and confirm no regression (T-003)
   - [ ] Run `uv run ruff check` and `uv run mypy` on `scripts/agent/http_lifecycle_stderr_log_manager.py`; fix any findings (T-003)

### Release units
N/A: no release unit. Each phase passes validation on its own.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle_stderr_log_manager.py` + `tests/agent/test_http_lifecycle_stderr_log_manager.py` | Unit | `uv run pytest tests/agent` | green; `_log_files` gone; no-retention + no-raise test present; existing tests pass except the two updated assertions |
| Full suite | Integration | `uv run pytest` | no regression anywhere |
| Changed files | Lint / type | `uv run ruff check` and `uv run mypy` on `scripts/agent/http_lifecycle_stderr_log_manager.py` | clean (no new findings) |

## Risks
- **Risk**: Removing `_log_files` could break a production reader the grep missed (e.g. dynamically accessed via `getattr`). → **Mitigation**: repo-wide literal grep for `_log_files` before editing; the issue's AI Implementation Instruction mandates stopping and reporting if a reader exists. Only two unit tests read it.
- **Risk**: The issue's Testing Expectations ask for an observable-close test using a fake file object, which only applies to Design B. Under Design A there is no handle to observe. → **Mitigation**: under Design A the new test verifies no-retention + no-raise instead; documented in UNK-02.
- **Risk**: A double-close if Design B is chosen and `forget` closes a handle the launcher already closed. → **Mitigation**: not applicable to Design A; under Design B guard close with `getattr(fh, "closed", False)` and reconcile `close_stderr_log`.
- **Risk**: The `_log_files` reference currently keeps a (already-closed) file object alive. → **Mitigation**: removal drops the reference, allowing GC; verified the launcher closes the actual FD.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Core Logic — remove the dead `_log_files` store (`scripts/agent/http_lifecycle_stderr_log_manager.py`) | In Progress | — | — | REQ-002 |
| 2 | Tests (`tests/agent/test_http_lifecycle_stderr_log_manager.py`) | In Progress | — | — | REQ-004 |
| 3 | Deployment & Verification | Pending | — | — | REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-070524_01_scripts_agent_http_lifecycle_stderr_log_manager.py.md | 1, 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261118-025717_agentfd001_stderr-log-fd-leak.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-11-18T04:31:27
- **Related target files**: `scripts/agent/http_lifecycle_stderr_log_manager.py`, `tests/agent/test_http_lifecycle_stderr_log_manager.py` — the full list of `File Path` values from
  `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-070524 -->

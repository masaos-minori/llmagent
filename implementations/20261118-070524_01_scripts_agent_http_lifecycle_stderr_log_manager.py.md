## Goal

Eliminate the dead `_log_files` store in `StderrLogManager` and the associated unclosed-handle risk on every cleanup path, while preserving `open_log`'s contract of returning the open handle to the launcher (REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The launcher is the sole owner of each stderr handle: it receives the handle from `open_log`'s return value, stores it in `self._stderr_files[server_key]`, and closes it (`close_stderr_log`). Removing the manager's duplicate reference does not change who closes it.
- `IO` stays imported (still used for `open_log`'s return type) after `_log_files` is removed.
- The two affected tests are the only readers of `_log_files`; the repo-wide grep confirms no other reader.

## Design decisions
- Delete the `_log_files` attribute declaration and its write in `open_log`; leave `open_log`'s return, `read_tail`, `rotate_log`, `get_log_path`, `forget`, `clear` intact except dropping `_log_files` references.

## Alternatives considered
- Design B (retain `_log_files` with guarded closes on `forget`/`clear`/`rotate_log`): rejected — `forget` is called only after the launcher already closed the handle (double-close would need guarding), and `clear`/`rotate_log` have no production callers. Removal is the minimal correct fix.

## Implementation
### Target file
`scripts/agent/http_lifecycle_stderr_log_manager.py`

### Procedure
1. Confirm via repo-wide grep that nothing in production reads `_log_files`; stop and report if a reader exists (REQ-001).
2. Delete `self._log_files: dict[str, IO[bytes]] = {}` (line 30) and `self._log_files[server_key] = log_file` (line 64); keep `self._log_paths` and `open_log`'s return value (REQ-002).
3. Ensure `forget`/`clear`/`rotate_log` no longer reference `_log_files`; they still operate on `_log_paths` and preserve their boolean contracts (REQ-003).

### Method
- Remove the attribute declaration and the single write in `open_log`. Verify no other method references `_log_files`. Preserve `open_log`'s return value (the open handle), `read_tail`'s re-open behavior, `rotate_log`'s rename+return, and `get_log_path`.

### Details
- The repo-wide grep shows the only other `_log_files` matches are `max_stderr_log_files` in `scripts/shared/mcp_config.py`, a distinct config attribute — not `StderrLogManager._log_files`. Confirmed safe to remove.

### Companion test files
- `tests/agent/test_http_lifecycle_stderr_log_manager.py`
  - Procedure: remove the `_log_files == {}` assertion in `test_empty_dict_state` (keep `_log_paths == {}`); replace `test_open_log_stores_handle` with a no-retention assertion; add a no-raise test for `forget`/`clear`/`rotate_log` (T-001, T-002; REQ-004)
  - Validation: `uv run pytest tests/agent` green

## Compatibility considerations
- No production behavior change: the launcher owns and closes the authoritative handle; the manager never held authoritative ownership.

## Security considerations
- Removing the dead store drops a lingering reference to a (possibly already-closed) handle, eliminating a resource-leak surface. Do not reintroduce an untracked handle reference.

## Rollback considerations
- Revert the commit; the change is confined to this manager.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle_stderr_log_manager.py` + `tests/agent/test_http_lifecycle_stderr_log_manager.py` | Unit | `uv run pytest tests/agent` | green; `_log_files` gone; no-retention + no-raise test present; existing tests pass except the two updated assertions |
| Full suite | Integration | `uv run pytest` | no regression anywhere |
| Changed files | Lint / type | `uv run ruff check` + `uv run mypy` on `http_lifecycle_stderr_log_manager.py` | clean |

## Completion criteria
- `_log_files` and its write in `open_log` are gone; `open_log` still returns the open handle; `forget`/`clear`/`rotate_log` no longer reference `_log_files`; a new test asserts the manager retains no handle reference and that `forget`/`clear`/`rotate_log` do not raise (AC-001, AC-002, AC-003).

## Out of Scope

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
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (remove the dead `_log_files` store and its write in `open_log`), `REQ-003` (`forget`/`clear`/`rotate_log` no longer reference `_log_files`)
- **Source issue**: issues/20261118-025717_agentfd001_stderr-log-fd-leak.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-043127_agentfd001_stderr-log-fd-leak.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-070524
- **Related target files**: `scripts/agent/http_lifecycle_stderr_log_manager.py`, `tests/agent/test_http_lifecycle_stderr_log_manager.py`

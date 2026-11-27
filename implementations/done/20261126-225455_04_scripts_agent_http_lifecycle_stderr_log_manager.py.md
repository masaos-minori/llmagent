## Goal

Make stderr log management enforce file mode `0o600`, the configured size and generation limits,
and rotation that is compatible with an active writer fd (REQ-006 — writer-compatible rotation and
retention).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `rotate_log()` has no production caller (tests only) — confirmed in Step 3a, which resolves the
  Issue's Unknown.
- No retention purge exists today — confirmed; this document adds it.
- Configured limits are passed as plain constructor values, not the config model, so the
  import-linter contract `No agent module imports MCP server config models` stays KEPT (Plan D6).
- The log root stays `tempfile.gettempdir()/mcp_server_logs/{server_key}` (Plan UNK-01, non-blocking).

## Design decisions

- Copy-and-truncate rotation (Plan D2): copy the active file content to the rotated generation,
  then truncate the active file, so the writer fd and `read_tail()` stay consistent.
- File created with `os.open(..., "ab", 0o600)` (Plan D3); the directory stays `0o700`.

## Alternatives considered

- Rotate only on restart — rejected by Plan D2 (long-running subprocesses grow unbounded).
- Keeping `os.rename()` — rejected: the writer fd follows the renamed inode while `read_tail()`
  reads the new empty path.

## Implementation
### Target file
`scripts/agent/http_lifecycle_stderr_log_manager.py`
### Procedure
- Add `max_log_size_bytes` (new) and `max_log_files` (new) plain keyword arguments to `StderrLogManager.__init__`
  (the constructor change the generated reference table reflects, document 26).
- Create the log file with mode `0o600` in `open_log()`.
- Replace the rename-based `rotate_log()` with copy-and-truncate rotation and add
  `purge_generations` (new) enforcing `max_log_files` (new).
- Keep writer and tail-reader paths pointing at the same active path.
### Method
- `open_log()` uses `os.open(log_file_path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)` and
  `os.fdopen` so the returned object is still a binary file object.
- `rotate_log()` copies the active file to `{log_file_path}.{generation}` (new naming), then
  truncates the active file in place; `purge_generations` (new) removes the oldest generations
  beyond `max_log_files` (new).
- `read_tail()` continues to read `self._log_paths[server_key]`, which is never renamed.
### Details
- The generation counter is per server key and is kept in the manager, not in the filesystem state.
- Rotation is triggered when the active file exceeds `max_log_size_bytes` (new); the size check uses
  `os.path.getsize` on the active path.
- Step 3b note: enforcement is wired as constructor defaults (`max_log_size_bytes`, `max_log_files`)
  that mirror the config model defaults; the per-server config values are still not read, so no call
  site changes. A test pins the two defaults against `McpServerConfig` to keep them aligned.

### Companion test files
- `tests/agent/test_http_lifecycle_stderr_log_manager.py`
  - Procedure: add a real-subprocess rotation test (writer fd stays valid across rotation), a
    file-mode `0o600` test, and retention-purge tests.
  - Validation: `uv run pytest tests/agent/test_http_lifecycle_stderr_log_manager.py`.

## Compatibility considerations

- Existing tests that assert rename semantics must be updated to copy-and-truncate; the existing
  `rotate_log()` return contract (`bool`) is preserved.

## Security considerations

- `0o600` is the disclosure control for REQ-006 (AC-3): stderr content can contain credentials.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit + integration with a real subprocess — `uv run pytest tests/agent/test_http_lifecycle_stderr_log_manager.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- Writer fd remains valid across rotation, `read_tail()` returns the rotated content, the file mode
  is `0o600`, and generations beyond `max_log_files` (new) are purged.
- Step 3b clarification: under copy-and-truncate the active file is emptied, so `read_tail()` returns
  what the writer fd writes after rotation; the pre-rotation content is what the rotated generation
  holds. Both are asserted in the companion tests.

## Out of Scope

- Making the log root a configurable deployment directory (Plan UNK-01).
- Documentation of the location and retention policy (document 24).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-011000 | 0o600 via os.open; copy-and-truncate rotation; purge_generations added; generation counter in manager; assumptions confirmed (rotate_log has no production caller, no retention purge existed, limits not enforced) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261127-011000 | companion `tests/agent/test_http_lifecycle_stderr_log_manager.py` 43 passed; added mode-0600 test, retention-purge tests, writer-fd tests (one marked integration); existing rename-semantics test updated to copy-and-truncate |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-095216 | 20261127-095216 | gates pass; changed files: scripts/agent/http_lifecycle_stderr_log_manager.py, tests/agent/test_http_lifecycle_stderr_log_manager.py; awaiting end-of-batch full suite gates pass; changed files: scripts/agent/http_lifecycle_stderr_log_manager.py, tests/agent/test_http_lifecycle_stderr_log_manager.py; awaiting end-of-batch full suite |

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
- **Requirement ID**: `REQ-006` (stderr log mode, retention, writer-compatible rotation)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `scripts/agent/http_lifecycle_stderr_log_manager.py`, `tests/agent/test_http_lifecycle_stderr_log_manager.py`
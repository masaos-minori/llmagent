## Goal

Correct the stale module docstring so the documented stderr log location matches the actual location (REQ-002;
AC-2).

## Scope
**Release unit**: N/A: no release unit

## Assumptions

- Confirmed in Step 3a: the docstring at `scripts/agent/http_lifecycle.py:71-72` states
  `/opt/llm/logs/mcp_servers/{server_key}.stderr.log`; the actual path is built at
  `scripts/agent/http_lifecycle_stderr_log_manager.py:67` as
  `tempfile.gettempdir()/mcp_server_logs/{server_key}/stderr.log`.
- `scripts/agent/http_lifecycle_stderr_log_manager.py` is a modification target of the cliplc009 plan and must
  not be changed here; the corrected wording states the location that plan also documents, so the two plans do
  not contradict each other.
- `tests/agent/test_http_lifecycle.py` is a validation reference, not a modification target: it is not a row of
  the Plan's target table.

## Design decisions

- The docstring states the actual location as built by the manager, rather than hardcoding a path constant, so
  the wording stays correct if `tempfile.gettempdir()` differs at runtime.

## Alternatives considered

- Changing the code to write to `/opt/llm/logs/mcp_servers/` — rejected: the Issue's scope is cleanup, and the
  log location is owned by the stderr plan's design.

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`
### Procedure

- Replace the path in the docstring at `:71-72` with the actual location.

### Method

- Docstring-only change; no code path is touched.

### Details

- Keep the surrounding sentence about per-server stderr redirect (H-1) unchanged.

## Compatibility considerations

- No runtime behavior changes; the doc gate and the targeted tests are the only checks affected.

## Security considerations

- N/A: documentation-only change inside a source file.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Docstring — `uv run python tools/check_docstrings.py` (read-only verification per `rules/tool-gates.md`).
- Unit — `uv run pytest tests/agent/test_http_lifecycle.py -v`.
- Sequence: format → lint → type → arch → security → test → coverage (`rules/toolchain.md`).

## Completion criteria

- The docstring names the actual stderr log location, the docs/docstring gate reports no finding, and the
  targeted tests pass unchanged.

## Out of Scope

- Rotation enforcement and the log-path implementation (owned by the cliplc009 plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the docstring per Procedure/Method/Details | Completed | 20261127-115829 | 20261127-115829 | Plan Phase 2 Plan Phase 2 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-115829 | 20261127-115829 | Plan Phase 4 Plan Phase 4 |

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
- **Requirement ID**: `REQ-002` (stale docstring corrected)
- **Source issue**: `issues/20261119-145311_cliplc013_api-field-cleanup.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-221206_cliplc013_api-field-cleanup.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-235847
- **Related target files**: `scripts/agent/http_lifecycle.py`
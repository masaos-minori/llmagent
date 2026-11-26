## Goal

Make the public process snapshot carry a logical identifier instead of the internal absolute stderr
log path (REQ-007 — public snapshots omit internal log paths).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Only the snapshot builder is touched; the module is 20449 B against the 24576 B size gate, so a
  split row would be required if the change pushed it over (Plan Risk).
- Overlap with `plans/20261126-221206_cliplc013_api-field-cleanup.md` on this file is compatible:
  that Plan corrects the module docstring's stderr log location, this document changes the snapshot
  builder. Sequencing dependency only — this Plan runs first per `tools/plan_dependency_order.py`.
- The logical identifier is produced by `redact_path` (document 01).

## Design decisions

- Keep the `stderr_log` field name and change only its value (Plan D4), so dict-shape consumers and
  pinned tests are unaffected.

## Alternatives considered

- Renaming the field to an identifier-specific name — rejected by Plan D4 (breaks dict-shape consumers).

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`
### Procedure
- In the snapshot builder, replace `self._stderr_log_manager.get_log_path(server_key) or ""` with a
  logical identifier produced by `redact_path` (document 01).
### Method
- `stderr_log = redact_path(self._stderr_log_manager.get_log_path(server_key) or "")`; an empty
  path still yields an empty string.
### Details
- No other use of the log path in this module changes; the writer and tail-reader continue to use
  the real path.

## Compatibility considerations

- `scripts/agent/lifecycle_router.py` delegates the snapshot dict without field-specific code, so it
  is not affected (Plan Reference Files).

## Security considerations

- AC-4 boundary: the snapshot is public display data.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_lifecycle.py tests/agent/test_http_lifecycle.py`.
- Sequence: format → lint → type → arch → security; `uv run python tools/check_module_size.py`.

## Completion criteria

- The snapshot value contains no absolute path, and the field name is unchanged.

## Out of Scope

- Field semantics in `scripts/agent/services/models.py` (document 06).
- The stale module docstring, handled by plan cliplc013.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | assertions in `tests/agent/test_http_lifecycle.py` (its own document) |
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
- **Requirement ID**: `REQ-007` (public process snapshots omit internal log paths)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `scripts/agent/http_lifecycle.py`

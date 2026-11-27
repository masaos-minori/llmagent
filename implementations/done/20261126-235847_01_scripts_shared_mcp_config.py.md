## Goal

Remove the four confirmed unused public properties (REQ-001) and keep the stderr rotation pair (REQ-003 — the
decision is resolved to keep).

## Scope
**Release unit**: N/A: no release unit

## Assumptions

- Confirmed in Step 3a: the four properties are defined at `scripts/shared/mcp_config.py:99`
  (`StartupMode.is_persistent`), `:109` (`StartupMode.requires_subprocess`), `:150`
  (`McpServerConfig.needs_health_check`), `:166` (`McpServerConfig.requires_cmd`), and no call site exists in
  `scripts/` or `tests/` — the only matches are the definitions themselves.
- Confirmed in Step 3a: `max_stderr_log_size_mb` and `max_stderr_log_files` are declared at `:140-141` and
  validated at `:275-282`; `rotate_log` has no production caller (`scripts/agent/http_lifecycle_stderr_log_manager.py:111`
  is called only from `tests/agent/test_http_lifecycle_stderr_log_manager.py`), so the fields are read only by
  tests until the cliplc009 plan's REQ-006 enforcement lands.
- REQ-002's clause "align field descriptions in `scripts/shared/mcp_config.py`" resolves to no change: the field
  comments at `:140-141` already match runtime behavior, and no other field description in this file is stale.
  Recorded as a Step 3a finding; the actionable part of REQ-002 is the docstring in document 02.
- `McpServerConfig.tool_names` is already removed by agentcfg002 and must not be reintroduced.

## Design decisions

- Deletion only: no rename, no replacement accessor, and no wiring of the rotation fields, since enforcement is
  the cliplc009 plan's REQ-006 and wiring it here would duplicate that plan.
- The retained pair keeps its validation at `:275-282`; AC-3 is evaluated after that plan's enforcement lands.

## Alternatives considered

- Removing the rotation pair now — rejected by REQ-003: the frozen plan's REQ-006 gives each field a documented
  runtime effect, so removing it would delete a contract that another plan is implementing.

## Implementation
### Target file
`scripts/shared/mcp_config.py`
### Procedure

- Delete the four `@property` blocks at `:99`, `:109`, `:150`, `:166`.
- Leave the dataclass fields, the validation block at `:275-282`, and the loader at `:461-464` unchanged.

### Method

- No signature change: the removed members are properties, so no caller signature is affected.

### Details

- The module docstring and the remaining property `is_disabled` (`:143-145`) stay as they are.

## Compatibility considerations

- Zero callers confirmed, so no import or call site needs updating; the full suite must still pass unchanged.
- `tests/shared/test_mcp_config_validation.py` is a validation reference, not a modification target: it is not a
  row of the Plan's target table.

## Security considerations

- N/A: removal of unused accessors only; no change to credential or validation behavior.

## Rollback considerations

- N/A: revert the commit; the properties are independent of one another, so a partial revert is safe.

## Validation plan

- Static — `uv run vulture scripts/shared/mcp_config.py --min-confidence 60`: no unused public property remains
  (AC-1).
- Unit — `uv run pytest tests/shared/test_mcp_config_validation.py -v`: passes unchanged.
- Docstring — `uv run python tools/check_docstrings.py`.
- Sequence: format → lint → type → arch → security → test → coverage (`rules/toolchain.md`).

## Completion criteria

- The four properties are gone, vulture reports no unused public property in the file, the retained pair is
  unchanged, and the full suite passes.

## Out of Scope

- Wiring the rotation enforcement (owned by the cliplc009 plan's REQ-006).
- `scripts/shared/runtime_tool_registry.py` and `scripts/agent/session_persister.py` (disconfirmed claims, no
  target row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the four properties per Procedure/Method/Details | Completed | 20261127-115829 | 20261127-115829 | Plan Phase 1 Plan Phase 1 |
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
- **Requirement ID**: `REQ-001` (remove the four unused public properties), `REQ-003` (keep the rotation pair)
- **Source issue**: `issues/20261119-145311_cliplc013_api-field-cleanup.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-221206_cliplc013_api-field-cleanup.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-235847
- **Related target files**: `scripts/shared/mcp_config.py`
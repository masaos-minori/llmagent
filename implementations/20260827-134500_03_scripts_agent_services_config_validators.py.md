## Goal

Remove the now-orphaned `validate_tool_cache_max_size()` function, per
`plans/20260827-121312_plan.md`'s `REQ-003`.

## Scope

- In scope: `scripts/agent/services/config_validators.py::validate_tool_cache_max_size`
  (verified at lines 126-128 as of 2026-08-27).
- Out of scope: every other `validate_*` function in this file, including the
  neighboring `validate_tool_error_retry_max` (line 131).

## Assumptions

- `REQ-001` (`config_dataclasses.py`) lands in the same commit — this function's
  sole caller (`_v_tool_cms` in `ToolConfig.__post_init__`) is removed by
  `REQ-001`; without `REQ-001`, removing this function would leave a dangling
  import (`NameError`/`ImportError` at module load).
- No other module imports `validate_tool_cache_max_size` — confirmed via `rg -n
  "validate_tool_cache_max_size" scripts/` showing only this definition and the
  `config_dataclasses.py` import site targeted by `REQ-001`.

## Design decisions

- Delete the function definition and its blank-line spacing as a single unit,
  matching the shared `_require_non_negative`-style pattern used by the
  neighboring validators (no shared state to disentangle).

## Alternatives considered

- N/A: single-function removal with no other consumer.

## Implementation
### Target file
`scripts/agent/services/config_validators.py`

### Procedure
1. Re-run `rg -n "validate_tool_cache_max_size"
   scripts/agent/services/config_validators.py` immediately before editing to
   confirm the line number has not drifted since 2026-08-27.
2. Delete the `validate_tool_cache_max_size` function definition (including its
   docstring and body).
3. Confirm no blank-line or spacing anomaly is introduced between the preceding
   and following function definitions.

### Method
Direct text edit (Edit tool) — remove one function.

### Details
Current text (verified 2026-08-27, lines 126-131):
```python
def validate_tool_cache_max_size(cfg: ToolConfig) -> None:
    """Validate that tool_cache_max_size is non-negative."""
    _require_non_negative("tool_cache_max_size", cfg.tool_cache_max_size)


def validate_tool_error_retry_max(cfg: ToolConfig) -> None:
```
Change to:
```python
def validate_tool_error_retry_max(cfg: ToolConfig) -> None:
```
(i.e., delete lines 126-129 — the function definition, its docstring/body, and
the two blank lines that separated it from the next function — leaving exactly
one blank line before `validate_tool_error_retry_max`, matching the file's
existing spacing convention between functions.)

## Compatibility considerations

- N/A: private-module function, no public interface.

## Security considerations

- N/A: dead-code removal, no security-relevant behavior change. Note the
  Plan's Reason for change: removing this validator does not weaken any live
  guarantee — `tool_cache_max_size` was already unenforced in any way that
  affects running behavior (its only effect was a `ToolConfig` field value that
  `REQ-001` deletes in the same commit).

## Rollback considerations

- Single-file revert via `git diff` / `git checkout --
  scripts/agent/services/config_validators.py`.
- Must be rolled back together with `REQ-001`/`REQ-002` if any of the three is
  reverted, per Design.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_validators.py` | Static | `rg -n "validate_tool_cache_max_size" scripts/agent/services/config_validators.py scripts/agent/config_dataclasses.py` | No matches |
| `tests/agent/` | Regression | `uv run pytest tests/agent/ -k "config_validators" -v` | No new failures |

## Completion criteria

- `rg -n "validate_tool_cache_max_size" scripts/agent/services/config_validators.py
  scripts/agent/config_dataclasses.py` returns no matches.

## Out of scope

- Any other `validate_*` function in this file.
- `config_dataclasses.py` (`REQ-001`, separate implementation procedure) and
  `config_builders.py` (`REQ-002`, separate implementation procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm current line number | Pending | — | — | |
| 2 | Delete `validate_tool_cache_max_size` | Pending | — | — | |
| 3 | Confirm spacing correctness | Pending | — | — | Coordinate with REQ-001/REQ-002 commits |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/done/20260827_toolexecutor_cache_removal_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260827-121312_plan.md`
- **Source implementation procedure**: supersedes
  `implementations/20260825-224356_09_scripts_agent_services_config_validators_py_config_dataclasses_py.md`,
  `implementations/20260826_02_scripts_agent_services_config_validators.py.md`
  (both left Pending/Blocked, neither executed)
- **Generated at**: 20260827-134500
- **Related target files**: `scripts/agent/services/config_validators.py`

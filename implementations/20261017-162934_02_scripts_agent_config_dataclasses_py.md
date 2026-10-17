# Implementation Procedure — `scripts/agent/config_dataclasses.py`

## Goal

Document the `> 0` enables / `<= 0` disables semantics on the two `ToolConfig` fields
`tool_error_retry_max` (line 172) and `tool_empty_result_max_repeats` (line 176) so the
gating semantics live next to the config fields (`REQ-005`). Keep defaults unchanged
(`REQ-004`).

## Scope

Modify only the docstrings/comments of `tool_error_retry_max` (line 172) and
`tool_empty_result_max_repeats` (line 176) in `scripts/agent/config_dataclasses.py`. Do NOT
change the default values or any other field. This is a docstring-only change.

## Assumptions

- `ToolConfig.tool_error_retry_max: int = 1` (line 172) with comment
  `# Max retries for an (name, args) combo that returned an error; 0 = disabled`.
- `ToolConfig.tool_empty_result_max_repeats: int = 0` (line 176) with comment
  `# Max consecutive empty tool results within a turn; 0 = disabled`.
- Gating reads these fields as `<= 0` disables (see `tool_loop_guard.py`, separate row).

## Adversarial verification findings (plan discrepancies)

- **No discrepancy.** Verified: both fields exist with the stated defaults and existing
  `0 = disabled` comments. The plan's doc line numbers (117–118) refer to the *doc* file,
  not this file — this file's fields are at lines 172 and 176. No material discrepancy.

## Design decisions

- Extend the existing inline comment for each field to state the semantics explicitly:
  `> 0` enables the guard; `<= 0` disables it. Keep the existing `0 = disabled` note.
- Do NOT alter the default value or type annotation.

## Alternatives considered

- Adding a full docstring vs. extending the inline comment: extend the existing inline
  comment (minimal, stays next to the field).

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

1. At `tool_error_retry_max` (line 172), extend the inline comment to:
   ```python
   # Max retries for an (name, args) combo that returned an error; > 0 enables
   # retry suppression, <= 0 disables it. Default 1 (enabled).
   tool_error_retry_max: int = 1
   ```
2. At `tool_empty_result_max_repeats` (line 176), extend the inline comment to:
   ```python
   # Max consecutive empty tool results within a turn; > 0 enables
   # empty-result repeat detection, <= 0 disables it. Default 0 (disabled).
   tool_empty_result_max_repeats: int = 0
   ```
3. Confirm both default values are unchanged (`1` and `0`) (REQ-004).
4. Confirm no other field was modified.

### Method

Edit the two inline comments only; re-run the default-value regression.

### Details

- Keep the default literals (`1`, `0`) exactly as-is.
- Match the phrasing style of neighboring comments.

## Compatibility considerations

Docstring/comment-only; no runtime effect. REQ-004 (defaults unchanged) preserved.

## Security considerations

N/A (documentation only).

## Rollback considerations

Revert the commit to `scripts/agent/config_dataclasses.py`.

## Validation plan

- Static: `uv run python -c "from agent.config_dataclasses import ToolConfig as T; c=T(); print(c.tool_error_retry_max, c.tool_empty_result_max_repeats)"` → `1 0` (REQ-004).
- Lint/type: `uv run ruff check scripts/agent/config_dataclasses.py` and `uv run mypy
  scripts/agent/config_dataclasses.py` clean.

## Completion criteria

Both field comments describe the `> 0` enables / `<= 0` disables semantics; the default
values remain `1` and `0`.

## Out of scope

Default values, other fields, the guard code (separate row), the test file (separate row),
and the Known Limitations doc update (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document >0/>=0 semantics on the two ToolConfig field comments | Pending | — | — | docstring-only; keep defaults |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: test file is a separate row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: doc is a separate row |

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
- **Requirement ID**: `REQ-005` (`> 0`/`<= 0` semantics documented on the two fields)
- **Source issue**: `issues/done/20261017-123510_retrysup01_make-retry-suppression-and-empty-result-defaults-observable.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-153234_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162934
- **Related target files**: `scripts/agent/config_dataclasses.py`

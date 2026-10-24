## Goal
- Change the `ToolConfigBuilder.build` fallback default of `masked_fields` to `["content", "old_text", "new_text"]` so it matches the dataclass default (`REQ-001`: lockstep code defaults).

## Scope
- Change the fallback list at `scripts/agent/config_section_builders.py:204-205` (`_get_or_default(cfg, "masked_fields", _get_list, ["file_content"])`).

## Assumptions
- Lines 204-205 confirmed 2026-10-24. Row `01` (`scripts/agent/config_dataclasses.py`) changes the dataclass default in the same cycle.
- The fallback only applies when the key is absent from the config mapping.

## Design decisions
- Same literal list as the dataclass default; no shared constant (YAGNI, two call sites).

## Alternatives considered
N/A: one-line value change; lockstep rationale is in the Plan Design.

## Implementation
### Target file
`scripts/agent/config_section_builders.py`

### Procedure
1. Replace `["file_content"]` in the `_get_or_default` call with `["content", "old_text", "new_text"]`.

### Method
- Single-line edit; let `ruff format` re-wrap the call if the line exceeds 88 characters.

### Details
- Do not touch other `_get_or_default` calls in `ToolConfigBuilder.build`.

## Compatibility considerations
- Explicit `masked_fields` in TOML wins over the fallback; only configs without the key change.

## Security considerations
- Strictly more redaction in logs and audit rows; approval previews unchanged.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -q`
- `uv run ruff format scripts/agent/config_section_builders.py`, `uv run ruff check scripts/agent/config_section_builders.py`, `uv run mypy --no-namespace-packages scripts/`.
- `rg -n "file_content" scripts/agent/config_section_builders.py` returns nothing.

## Completion criteria
- Building a config without `masked_fields` yields `["content", "old_text", "new_text"]`, equal to `ToolConfig().masked_fields`.

## Out of Scope
- Other builder defaults and `mask_args` behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the fallback list at lines 204-205 | Completed | — | 20261025-003203 |  |
| 2 | Run the targeted config tests | Completed | — | 20261025-003203 |  |
| 3 | Run the standard validation sequence | Completed | — | 20261025-003203 |  |

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
- **Requirement ID**: `REQ-001` (lockstep code defaults)
- **Source issue**: `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-221904_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235437
- **Related target files**: `scripts/agent/config_section_builders.py`
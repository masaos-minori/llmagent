## Goal
- Replace the inert `["file_content"]` default of `ToolConfig.masked_fields` with the real file-write argument keys `["content", "old_text", "new_text"]` (`REQ-001`: lockstep code defaults; `REQ-003`: replace outright).

## Scope
- Change the one default factory at `scripts/agent/config_dataclasses.py:182` (`masked_fields: list[str] = field(default_factory=lambda: ["file_content"])`).

## Assumptions
- Line 182 confirmed 2026-10-24. The builder fallback in `scripts/agent/config_section_builders.py` (row `02`) MUST change in the same cycle so the two defaults agree.
- Tests that pin the old value are handled by rows `04` to `06`; all other fixtures override `masked_fields` explicitly (grep 2026-10-24).

## Design decisions
- Same literal list in both code defaults; no new constant, no ordering change.

## Alternatives considered
- Keep `file_content` alongside the new names: rejected, it names no argument key in any registered tool schema (Plan REQ-003).

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
1. Replace the lambda's list with `["content", "old_text", "new_text"]`.

### Method
- Single-line edit; keep the `field(default_factory=lambda: [...])` form.

### Details
- Keep the line within 88 characters; let `ruff format` wrap it if needed.

## Compatibility considerations
- Deployments that set `masked_fields` explicitly keep their value; deployments on the default gain redaction of `content`, `old_text`, `new_text` in audit rows and logs only (strictly more redaction).

## Security considerations
- The change increases redaction of file bodies in logs and audit events; approval previews stay unmasked by the closed-Plan decision.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -q`
- `uv run ruff format scripts/agent/config_dataclasses.py`, `uv run ruff check scripts/agent/config_dataclasses.py`, `uv run mypy --no-namespace-packages scripts/`.
- `rg -n "file_content" scripts/agent/config_dataclasses.py` returns nothing.

## Completion criteria
- `ToolConfig().masked_fields == ["content", "old_text", "new_text"]` and no `file_content` default remains in this file.

## Out of Scope
- `mask_args`, its callers, `plan_blocked_tools`, and any other `ToolConfig` field.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the default factory list at line 182 | Pending | — | — | |
| 2 | Run the targeted config tests | Pending | — | — | |
| 3 | Run the standard validation sequence | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (lockstep code defaults), `REQ-003` (replace `file_content` outright)
- **Source issue**: `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-221904_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235437
- **Related target files**: `scripts/agent/config_dataclasses.py`

## Goal

Correct `ToolDefinition`'s docstring in `scripts/shared/tool_registry.py` to document a current compatibility requirement (none exists today, confirmed by zero call sites) and a removal condition (per `rules/coding.md` Deprecation policy: eligible for removal the next time this file is touched for an unrelated reason, subject to a fresh zero-caller `rg` re-check) for the unused `description`/`input_schema` fields, replacing the current unqualified "reserved for future use" statement.

## Scope

- Correct the docstring for `ToolDefinition` (lines 49-55) in `scripts/shared/tool_registry.py`
- No other files are modified in this row

## Assumptions

- Zero call sites across `scripts/`/`tests/` ever pass `description=`/`input_schema=` to `ToolDefinition(...)` (confirmed via `rg -n "ToolDefinition\(" scripts/ tests/`).
- The sole construction site (`scripts/shared/tool_registry.py:233` and all `tests/` construction sites) omits `description=`/`input_schema=`, confirming zero current consumers.
- This is a docstring-only change — no import, signature, schema, or control-flow change.

## Design decisions

- Documenting the compatibility requirement and removal condition rather than removing the fields outright: the Issue's "document" alternative was preferred over structural dataclass-shape change, to stay strictly within the Issue's "documentation/wording correction, not a behavior change" framing. Removing them would be a deferred structural-cleanup candidate for a future dedicated issue.

## Alternatives considered

- Removing `description`/`input_schema` outright — rejected: a structural dataclass-shape change beyond this Issue's declared "documentation/wording correction, not a behavior change" scope.
- Adding a deprecation warning on access — rejected: the fields are immutable dataclass defaults, not properties; adding such warnings would require behavioral changes inconsistent with this Issue's scope.

## Implementation

### Target file

`scripts/shared/tool_registry.py`

### Procedure

Correct `ToolDefinition`'s docstring to add the compatibility-requirement/removal-condition statement for `description`/`input_schema`.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `scripts/shared/tool_registry.py` lines 48-59.
2. Correct the docstring for `ToolDefinition` (lines 49-55):
   - Replace the current unqualified "reserved for future use" wording with a statement documenting a current compatibility requirement (none exists today) and a removal condition (per `rules/coding.md` Deprecation policy).

### Details

```python
# Lines 49-55: correct the docstring:
# Before:
"""Immutable tool definition owned by a single server.

`description` and `input_schema` are reserved for future use: they are never
populated by `_populate_default_registry()` and are not read by any caller today.
LLM-visible tool schemas are sourced from each server's own `tools.py` `TOOL_LIST`,
not from this registry.
"""

# After:
"""Immutable tool definition owned by a single server.

`description` and `input_schema` have no current consumers: none of the callers
that construct `ToolDefinition` (see `scripts/shared/tool_registry.py:233` and
all test construction sites) populate these fields. They remain present as a
compatibility shim for servers that may supply them in their `/v1/tools` payloads.
Per `rules/coding.md`'s Deprecation policy, these fields are eligible for removal
the next time this file is touched for an unrelated reason, subject to a fresh
zero-caller `rg` re-check at that time.

LLM-visible tool schemas are sourced from each server's own `tools.py` `TOOL_LIST`,
not from this registry.
"""
```

## Compatibility considerations

- No production code depends on the specific docstring text being changed.
- The fields themselves remain unchanged — only the docstring is corrected.
- `tests/shared/test_tool_registry.py` must continue to pass unmodified — no test change in this Plan.

## Security considerations

- No security impact. This is a docstring correction, not a security boundary change.

## Rollback considerations

- Reverting this change restores the original docstring. If needed later, the docstring should be corrected again to match the current state of the fields.

## Validation plan

- Regression: run `uv run pytest tests/shared/test_tool_registry.py -v` to confirm no failures introduced.
- Static analysis: `uv run ruff check scripts/shared/tool_registry.py`, `uv run mypy scripts/shared/tool_registry.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `ToolDefinition`'s docstring correctly states a current compatibility requirement (none exists today) and a removal condition for `description`/`input_schema`.
- The fields themselves remain unchanged (no removal or renaming).
- All existing tests in `tests/shared/test_tool_registry.py` continue to pass without modification.
- No new lint/type errors introduced.

## Out of scope

- Removing `description`/`input_schema` — a structural dataclass-shape change beyond this Issue's declared "documentation/wording correction, not a behavior change" scope.
- Changes to `docs/*.md` — not applicable to this row.
- Modifying any other file — covered by separate rows (REQ-001, REQ-003, REQ-004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct ToolDefinition docstring to add compatibility requirement/removal condition | Completed | 20260917-201714 | 20260917-201714 |  |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-201715 | 20260917-201715 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260914-103349_mcpagent09_routing-discovery-test-config-documentation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-131528_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-231122
- **Related target files**: scripts/shared/tool_registry.py
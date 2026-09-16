## Goal

Correct `AgentConfig`'s class docstring in `scripts/agent/config_dataclasses.py` (8 → 9), matching its module docstring (line 16) and the nine declared fields (lines 442-450: `llm`, `rag`, `tool`, `memory`, `mcp`, `approval`, `obs`, `diagnostics`, `messages`).

## Scope

- Correct the class docstring for `AgentConfig` (line 433) in `scripts/agent/config_dataclasses.py`
- No other files are modified in this row

## Assumptions

- The nine declared fields are exactly: `llm`, `rag`, `tool`, `memory`, `mcp`, `approval`, `obs`, `diagnostics`, `messages` (confirmed by direct field count).
- This is a docstring-only change — no import, signature, schema, or control-flow change.
- The sub-configuration count (9, confirmed by direct field count in this cycle) will not change between this Plan's creation and its implementation, since no other in-flight Plan in this batch adds or removes an `AgentConfig` sub-config field.

## Design decisions

- Keeping a concrete "9" in `config_dataclasses.py`'s own class docstring (matching its adjacent module docstring and field list, where drift is easy to catch on the next edit to the same class), while the three `docs/*.md` locations drop the count entirely per `skills/DESIGN.md` "No implementation counts".

## Alternatives considered

- Removing the numeric count here too — rejected: this location is immediately adjacent to the actual field list it describes, so keeping a concrete "9" makes drift easy to catch on the next edit to the same class.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

Correct `AgentConfig`'s class docstring from "8" to "9" sub-configurations.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `scripts/agent/config_dataclasses.py` line 433.
2. Correct the class docstring for `AgentConfig` (line 433):
   - Change: `Composes 8 domain-specific sub-configs.`
   - To: `Composes 9 domain-specific sub-configs.`

### Details

```python
# Line 433: correct the count:
# Before:
    Composes 8 domain-specific sub-configs.

# After:
    Composes 9 domain-specific sub-configs.
```

## Compatibility considerations

- No production code depends on the specific docstring text being changed.
- `tests/agent/test_config_builders.py` must continue to pass unmodified — docstring-only change, no test edit required.

## Security considerations

- No security impact. This is a docstring correction, not a security boundary change.

## Rollback considerations

- Reverting this change restores the original docstring. If needed later, the docstring should be corrected again to match the current field count.

## Validation plan

- Regression: run `uv run pytest tests/agent/test_config_builders.py -v` to confirm no failures introduced.
- Static analysis: `uv run ruff check scripts/agent/config_dataclasses.py`, `uv run mypy scripts/agent/config_dataclasses.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `AgentConfig`'s class docstring correctly states "9" sub-configurations, matching its module docstring and field count.
- All existing tests in `tests/agent/test_config_builders.py` continue to pass without modification.
- No new lint/type errors introduced.

## Out of scope

- Changes to `docs/*.md` — covered by separate rows (REQ-003, docs-only rows).
- Modifying any other file — covered by separate rows (REQ-001, REQ-002, REQ-004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct AgentConfig class docstring from 8 to 9 sub-configurations | Pending | — | — | |
| 2 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Source issue**: issues/20260914-103349_mcpagent09_routing-discovery-test-config-documentation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-131528_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-231122
- **Related target files**: scripts/agent/config_dataclasses.py

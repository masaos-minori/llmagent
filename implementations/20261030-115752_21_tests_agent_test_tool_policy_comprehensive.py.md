# Implementation Procedure: `tests/agent/test_tool_policy_comprehensive.py`

## Goal

Migrate this file's 1 `RuntimeToolRegistry(` constructions to explicit allowlists with assertion meaning unchanged (REQ-006: mechanical test migration per the plan's measured 45-construction inventory).

## Scope

- `tests/agent/test_tool_policy_comprehensive.py`: constructions at lines 197 (measured at HEAD).
- No production-code edits (row 3 owns the constructor change); no other test files (separate rows).

## Assumptions

- Lightweight row: mechanical kwarg addition only.
- Row 3 lands first; this file is expected red until migrated - run `uv run pytest tests/agent/test_tool_policy_comprehensive.py` immediately after editing (plan Phase 2 per-file rule).

## Design decisions

- Same migration rule as row 11: `allowed_servers=frozenset(<server keys of the tools built by this test>)`; deny-all cases (none today in this file) would use `frozenset()`.
- Single site; comprehensive policy fixture tools determine the allowlist.

## Alternatives considered

- N/A: mechanical migration identical to row 11's rule.

## Implementation

### Target file

`tests/agent/test_tool_policy_comprehensive.py`

### Procedure

1. At each listed site add `allowed_servers=frozenset([...])` computed from the tools the test constructs.
2. `git diff` review: only `allowed_servers=` additions appear; no assertion line changes (REQ-006).

### Method

Row 11's rule applied file-locally; keep surrounding fixture code byte-identical.

### Details

Single site; comprehensive policy fixture tools determine the allowlist.

## Compatibility considerations

- Green per-file before the next migration file (plan Phase 2); full-suite gate listed in the plan Validation plan.

## Security considerations

- N/A: kwarg migration; routing assertions stay as fail-closed locks.

## Rollback considerations

- Revert with row 3 as one commit group.

## Validation plan

- `uv run pytest tests/agent/test_tool_policy_comprehensive.py` then `uv run pytest tests/shared tests/agent` (plan Phase 2 "Done when").
- Gates: `uv run ruff check tests`, mypy test conventions per `rules/toolchain.md`.

## Completion criteria

- Every construction in this file is explicit; assertions byte-identical; file green (plan AC-6).

## Out of Scope

- Other test files (rows 11-22); constructor change (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate the 1 constructions per Procedure | Pending | - | - | Needs row 3 |
| 3 | Run this file, then the Phase 2 suite | Pending | - | - | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Row 3 (constructor) must land first | No | - |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| - | - | - | - | - | - |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006 (migrate 1 constructions without changing assertion meaning)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `tests/agent/test_tool_policy_comprehensive.py`

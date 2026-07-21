# Implementation Procedure: Remove dead code gitops_force_push_blocked and gitops_protected_branches

## Goal

Remove dead code `gitops_force_push_blocked` and `gitops_protected_branches` from source and documentation to eliminate security-relevant inconsistency between documented branch protection behavior and actual runtime behavior.

## Scope

- `scripts/agent/config_dataclasses.py` — remove `gitops_force_push_blocked` and `gitops_protected_branches` fields
- `docs/05_agent_06_02_tool-execution-and-approval-approval.md` — remove references
- `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md` — remove references
- `docs/99_documentation_sync_report.md` — remove references
- `docs/05_agent_08_04_configuration-mcp-approval-obs.md` — remove references

## Assumptions

1. The REMOVED comments in `config_builders.py` indicate deliberate removal of these fields, not an accidental omission
2. No external operator relies on `gitops_force_push_blocked` or `gitops_protected_branches` as documented protections
3. The existing `gitops_push_blocked` field provides sufficient branch protection coverage
4. No test assertions depend on default values of the removed fields

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

1. Locate the target fields in `config_dataclasses.py` at approximately lines 351-355:
   - `gitops_force_push_blocked` field definition
   - `gitops_protected_branches` field definition with default_factory

2. Delete both field definitions and their associated comments

3. Update documentation files to remove references to these fields:
   - `docs/05_agent_06_02_tool-execution-and-approval-approval.md` — update lines 106-107
   - `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md` — update lines 33-36
   - `docs/99_documentation_sync_report.md` — update lines 67, 101
   - `docs/05_agent_08_04_configuration-mcp-approval-obs.md` — update lines 83-84

### Method

Use targeted line-range edits to delete only the specific field definitions. Do not modify surrounding code. For documentation files, remove or rewrite the sections referencing these fields while preserving surrounding context.

### Details

- Only remove `gitops_force_push_blocked` and `gitops_protected_branches`; do NOT touch `gitops_push_blocked` (actively used in tool_approval.py:118, config_builders.py:241)
- After removal, verify no remaining references: `grep -rn "gitops_force_push_blocked\|gitops_protected_branches" . --include="*.md" --include="*.py"` should return zero results
- This is a pure cleanup — zero churn on these fields in git history (they were never wired up)

## Validation plan

1. Run grep to verify no remaining references: `grep -rn "gitops_force_push_blocked\|gitops_protected_branches" . --include="*.md" --include="*.py"`
2. Run type check: `uv run mypy scripts/agent/config_dataclasses.py`
3. Run full test suite: `uv run pytest`
4. Manual review of updated documentation for accuracy

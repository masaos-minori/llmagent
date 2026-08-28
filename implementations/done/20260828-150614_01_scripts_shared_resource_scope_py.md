## Goal

Remove the stale "(not wired up yet)" qualifier from the `_scopes_conflict()` usage description in `scripts/shared/resource_scope.py`'s module docstring, so the docstring accurately states that `_scopes_conflict()` is used by `tool_scheduler.py`'s conflict-graph grouping without a stale pending/future-tense qualifier.

## Scope

- **In-Scope**: Update the module docstring in `scripts/shared/resource_scope.py` line 8-9.
- **Out-of-Scope**: Change `_scopes_conflict()`'s logic, signature, or function-level docstring. Modify `scripts/agent/tool_scheduler.py`. Update design docs listed in the issue — they are already accurate.

## Assumptions

- The replacement wording should match the current usage pattern: `_scopes_conflict()` is imported and called directly in `tool_scheduler.py`'s conflict-graph grouping loop.
- No other references to "(not wired up yet)" exist elsewhere in the codebase that would require similar updates (to be confirmed during implementation).

## Design decisions

- Only remove the explicit "(not wired up yet)" qualifier; preserve all other prose in the sentence.
- Use present-tense wording reflecting current usage rather than future-tense language.

## Alternatives considered

- Adding a note about future API stability. Not needed — the qualifier itself is the only stale element.
- Replacing "(not wired up yet)" with a reference to the specific function (`build_execution_groups()`) in `tool_scheduler.py`. Chose simpler wording unless context demands specificity.

## Implementation

### Target file

`scripts/shared/resource_scope.py`

### Procedure

1. Re-confirm `scripts/agent/tool_scheduler.py` still imports and calls `_scopes_conflict()` (per issue instruction).
2. Run `rg -n "not wired up yet"` to check for other stale instances (UNK-01).
3. Replace `(not wired up yet)` in the module docstring with wording that reflects current usage.
4. Confirm no functional code changes in the diff.

### Method

Direct edit of the module docstring text only. No code changes, no new lines added.

### Details

- Current docstring text (lines 8-9): `_scopes_conflict()` is the overlap predicate consumed later by `scripts/agent/tool_scheduler.py`'s conflict-graph grouping (not wired up yet).
- Replacement: Remove "(not wired up yet)" parenthetical; keep the rest of the sentence intact.
- Example replacement: `_scopes_conflict()` is the overlap predicate consumed by `scripts/agent/tool_scheduler.py`'s conflict-graph grouping.

## Compatibility considerations

- This is a comment/docstring-only change; no runtime behavior impact.
- Verify that the replacement wording does not introduce claims that cannot be verified against current code.

## Security considerations

- None applicable. No security-relevant behavior changes.

## Rollback considerations

- Simple revert: restore the previous version of the module docstring. No data migration or schema rollback needed.

## Validation plan

| Target File | Testing Strategy | Expected Outcome |
|---|---|---|
| `scripts/shared/resource_scope.py` | Manual verification: diff review + grep for `_scopes_conflict` in `tool_scheduler.py` | Docstring updated, no code changes, usage confirmed |

## Completion criteria

- AC-001: `scripts/shared/resource_scope.py`'s module docstring no longer states or implies that `_scopes_conflict()` is unused or pending integration.
- AC-002: No functional code changes are present in the diff — comment/docstring text only.

## Out of scope

- Changing `_scopes_conflict()`'s logic, signature, or function-level docstring.
- Modifying `scripts/agent/tool_scheduler.py`.
- Updating design docs that are already accurate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm `_scopes_conflict()` usage in `tool_scheduler.py` | Completed | — | — | Confirmed active use at line 171 |
| 2 | Check for other stale "(not wired up yet)" instances | Completed | — | — | Only instance found in resource_scope.py:9 |
| 3 | Replace stale qualifier in module docstring | Completed | — | — | Removed "(not wired up yet)" parenthetical |
| 4 | Verification: confirm no functional changes | Completed | — | — | Docstring text only, no code changes |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: `issues/20260828-131043_doc003_resource_scope_not_wired_comment_stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260828-142755_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260828-150614
- **Related target files**: `scripts/shared/resource_scope.py`

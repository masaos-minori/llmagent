## Goal

Remove the stale `TurnCoordinator.handle_turn_start` planning comment (docstring) from `scripts/agent/workflow_engine_adapter.py` at line 173 (REQ-003; AC-3).

## Scope

`scripts/agent/workflow_engine_adapter.py` only — remove the no-op placeholder docstring at line 173. The `return None` on line 174 is kept.

## Assumptions

- Only the docstring at line 173 references `TurnCoordinator.handle_turn_start`; the `return None` on line 174 does not.
- Removing the docstring leaves a valid no-op `plan_fn` whose body is unchanged.

## Design decisions

- Remove only the docstring line, not the whole `plan_fn`: the plan's minimal scope removes the misleading `TurnCoordinator` mention; judging the entire `plan_fn` dead is a separate edit outside this plan.
- Surgical one-line edit keeps the diff to exactly the stale token.

## Alternatives considered

- Deleting the whole `plan_fn` (lines 172-174): rejected, outside this plan's minimal scope; the plan removes only the comment referencing `TurnCoordinator`.
- Rewriting the docstring to something accurate: rejected, no planning work is actually delegated here; the plan drops the reference entirely rather than rewording it.

## Implementation

### Target file

`scripts/agent/workflow_engine_adapter.py`

### Procedure

1. Locate the stale docstring: `rg -n "TurnCoordinator" scripts/agent/workflow_engine_adapter.py` → line 173.
2. Delete line 173: `"""No-op placeholder: planning work is done by TurnCoordinator.handle_turn_start before engine.run()."""`, keeping the following `return None` (line 174) intact.
3. Confirm `rg -n "TurnCoordinator" scripts/agent/workflow_engine_adapter.py` returns nothing.

### Method

Open `workflow_engine_adapter.py` around lines 172-174; delete only the docstring line 173; verify with `rg`.

### Details

- Current state (verified): line 172 `async def plan_fn() -> str | None:`, line 173 the docstring referencing `TurnCoordinator.handle_turn_start`, line 174 `return None`.
- The edit touches only the docstring; the no-op `return None` body is preserved.

## Compatibility considerations

- Docstring-only change; no runtime behavior change. `plan_fn` remains a valid no-op.

## Security considerations

- N/A.

## Rollback considerations

- Restore line 173 via `git checkout <commit> -- scripts/agent/workflow_engine_adapter.py` or revert the commit.

## Validation plan

- `rg -n "TurnCoordinator" scripts/agent/workflow_engine_adapter.py` returns nothing (AC-3).
- Full suite + static checks introduce no new findings (REQ-006).

## Completion criteria

- `scripts/agent/workflow_engine_adapter.py` no longer contains the `TurnCoordinator.handle_turn_start` planning comment; the diff touches only line 173.

## Out of scope

- Deleting the whole no-op `plan_fn` (separate edit, outside this plan).
- Deleting the module / removing the re-export (sibling docs, REQ-001/REQ-002).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261012-133424 | 20261012-133444 | stale_detector clean changed: scripts/agent/workflow_engine_adapter.py (stale docstring line removed; diff touches one line) |
| 2 | Add or update tests per Validation plan | Completed | 20261012-133444 | 20261012-133444 | N/A: docstring-only; covered by full suite N/A: docstring-only; 21 engine-adapter tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261012-133444 | 20261012-133444 | ruff, mypy, bandit (no high severity), lint-imports pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261012-133444 | 20261012-133444 | N/A: no doc edit in this row N/A: no doc edit in this row |

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
- **Source issue**: issues/done/20261008-150555_turncoord01_remove-or-wire-the-unused-turncoordinator-class.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261009-162655_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-113135
- **Related target files**: scripts/agent/workflow_engine_adapter.py
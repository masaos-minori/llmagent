## Goal

Delete the dead-code `TurnCoordinator` module `scripts/agent/turnd_coordinator.py` so that no `TurnCoordinator` class definition remains anywhere in `scripts/` or `tests/` (REQ-001; AC-1).

## Scope

Deletion of `scripts/agent/turnd_coordinator.py` only. The entire module file is removed; no file is edited in place.

## Assumptions

- `TurnCoordinator` has zero construction, call, and dynamic-use (`importlib`/`pkgutil`/`getattr`) sites across `scripts/` and `tests/` (confirmed via `rg`).
- The module's own imports (`shared.json_utils`, `agent.audit_event_emitter`, `agent.context`) are intra-package and unaffected by deletion, so no `import-linter` contract is violated.
- No test instantiates `TurnCoordinator`.

## Design decisions

- Delete the file rather than emptying it: a deleted module is unambiguously gone from imports, the generated API reference, and `rg` scans; an emptied module would still resolve as importable and could resurrect the symbol.
- Deletion is a single-file removal, permitted without separate confirmation under `AGENTS.md` Execution policy.

## Alternatives considered

- Emptying the module (removing the class body): rejected, because an empty-but-present module still imports cleanly and leaves a live-looking import target.
- Keeping the module and removing only the class: rejected; the plan deletes the module entirely (REQ-001), and any remaining symbol would reappear in the regenerated API reference.

## Implementation

### Target file

`scripts/agent/turnd_coordinator.py` — delete the file.

### Procedure

1. Confirm zero live references: `rg -n "TurnCoordinator|turnd_coordinator" scripts/ tests/` returns only the class definition (`turnd_coordinator.py:23`) and its own module docstring (`turnd_coordinator.py:2`) — no construction, call, or dynamic-use site.
2. Delete `scripts/agent/turnd_coordinator.py` (single-file removal; record it with `git rm` so the deletion is captured in history).
3. Confirm `rg TurnCoordinator` in `scripts/` and `tests/` now finds no `class TurnCoordinator:` definition.

### Method

Locate `scripts/agent/turnd_coordinator.py`; run the `rg` confirmation above; `git rm scripts/agent/turnd_coordinator.py`.

### Details

- The class is defined at `turnd_coordinator.py:23` (`class TurnCoordinator:`); the module docstring at line 2 also matches `turnd_coordinator`.
- After deletion, `rg TurnCoordinator` in `scripts/`/`tests/` still matches the package re-export (`__init__.py`, handled by the sibling procedure doc) and the adapter comment (sibling) — no class definition remains.
- The module's imports are intra-package (`shared.json_utils`, `agent.audit_event_emitter`, `agent.context`); deleting it violates no import-boundary contract.

## Compatibility considerations

- `TurnCoordinator` is re-exported from `scripts/agent/__init__.py` (import line 18, `__all__` entry line 33); that export is removed by the sibling procedure doc (`_02`). This doc does not touch `__init__.py`.
- No production code constructs or calls `TurnCoordinator`; deleting the module changes no runtime behavior.

## Security considerations

- N/A: no auth/authorization or trust-boundary change; removing unused code reduces attack surface.

## Rollback considerations

- Restore the file with `git checkout <commit> -- scripts/agent/turnd_coordinator.py` (or `git revert` of the deletion commit). The class definition and module are fully preserved in history.

## Validation plan

- Static: `rg TurnCoordinator` finds no class definition in `scripts/` or `tests/` (AC-1).
- Import smoke: `tests/agent/test_import_smoke.py` still passes after the sibling export removal.
- Full suite + static checks pass (REQ-006).

## Completion criteria

- `scripts/agent/turnd_coordinator.py` is absent; `rg TurnCoordinator` finds no `class TurnCoordinator:` definition in `scripts/` or `tests/`.

## Out of scope

- Removing the `TurnCoordinator` re-export from `scripts/agent/__init__.py` (sibling doc, REQ-002).
- Removing the stale adapter comment (sibling doc, REQ-003).
- Any backward-compatibility shim.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: deletion-only; covered by import smoke + full suite |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no doc edit in this row |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20261008-150555_turncoord01_remove-or-wire-the-unused-turncoordinator-class.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261009-162655_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-113135
- **Related target files**: scripts/agent/turnd_coordinator.py

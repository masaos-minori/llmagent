## Goal

Implement **REQ-001**: enforce `require_approval: true` on workflow definitions at load time in `workflow_loader.py`, so a misconfigured workflow fails startup instead of silently defaulting to no workflow-level approval gate. Closes AGENT-001.

## Scope

Modify `scripts/agent/workflow/workflow_loader.py` `_validate()`. Reference read only: `scripts/agent/workflow/models.py` (`WorkflowDef.require_approval`), `config/workflows/default.json` (updated in seq 01).

## Assumptions

- `_validate()` is called from `load()` before any `WorkflowDef` is constructed (line 117).
- Only `config/workflows/default.json` exists; setting it to `true` keeps it valid.
- `WorkflowDef.require_approval` is already parsed at `load()` line 136.

## Design decisions

- Enforce inside `_validate()` (structural validation), co-located with the other structural rules, so the check raises `WorkflowLoadError` uniformly.
- Require the value to be exactly `True` (`is not True` rejects absent and `false`), matching the plan decision matrix: a workflow cannot silently default to no approval.
- Error message names the policy: `"require_approval must be true for this workflow"`.

## Alternatives considered

- Checking in `load()` after parsing: rejected — `_validate()` is the single structural gate and its `WorkflowLoadError` is the documented contract; a second path in `load()` would duplicate it.
- Tool-intersection check against `APPROVAL_REQUIRING_TOOLS`: rejected — `WorkflowDef` has no tool field; workflows cannot be classified by tools (see plan `Design > Design details`).

## Implementation
### Target file
`scripts/agent/workflow/workflow_loader.py`

### Procedure
Add a `require_approval` truthiness check at the end of `_validate()`, after the `retry_policy` checks.

### Method
1. Locate `_validate()` (lines 60-95).
2. After the `backoff_sec` check (line 95), insert:
   ```python
   if data.get("require_approval") is not True:
       raise WorkflowLoadError("require_approval must be true for this workflow")
   ```
3. No import changes needed — `WorkflowLoadError` is already defined (line 56).

### Details
- `data` is typed `_WorkflowJson` (`require_approval: bool`, total=False); `data.get("require_approval")` returns `None` when absent, `True`/`False` when present. `is not True` rejects both `None` and `False`.
- Do NOT touch `load()` line 136 (`bool(data.get("require_approval", False))`); with `_validate()` gating, valid workflows always carry `true`, so this stays correct.
- Place the check after the stage/retry_policy checks so those errors surface first for structurally broken files.

## Compatibility considerations

- Existing tests that load a workflow JSON without `require_approval: true` will now raise. Add/adjust tests per the Validation plan.
- `default.json` is set to `true` in the sibling procedure (seq 01), so shipped config stays valid.

## Security considerations

- This is the security-relevant change: it makes the mandatory workflow-level approval gate actually enforced. A weaker check (e.g. requiring only key presence) would let `require_approval: false` pass and defeat the policy.

## Rollback considerations

- Revert the `_validate()` edit and restore `default.json` to `false`. Note reverting reopens AGENT-001.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `_validate()` rejection | Unit: workflow missing key / `false` | pytest | `WorkflowLoadError` raised |
| `_validate()` accept | Unit: `require_approval: true` | pytest | loads OK |
| `default.json` | Integration: startup load | pytest | loads OK |
| lint/type | ruff, mypy | ruff, mypy | clean |

## Completion criteria

- `_validate()` raises `WorkflowLoadError` when `require_approval` is absent or `false`.
- `_validate()` passes when `require_approval: true`.
- Unit tests cover all three cases; ruff/mypy clean.

## Out of scope
- Changing `require_approval` semantics/behavior itself.
- `ProductionConfigValidator` (out of scope per plan correction notes).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `require_approval` check in `_validate()` | Completed | — | 20261009-122445 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261009-122445 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261009-122445 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261009-122445 |  |

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
- **Source issue**: `issues/done/20261007-154046_approval01_enforce-approval-policy-in-configuration-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-161457_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-120153
- **Related target files**: `scripts/agent/workflow/workflow_loader.py`
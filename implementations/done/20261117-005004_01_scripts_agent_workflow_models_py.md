## Goal

Make the workflow-definition contract explicit at the model layer: `RetryPolicy.retry_on`, `WorkflowDef.stages`, and `WorkflowDef.retry_policy` become required constructor arguments, and `WorkflowDef` owns empty-stage validation. A missing field now fails at construction with `TypeError` (missing argument) or `AssertionError` (empty `stages`) instead of silently taking an implicit default. Shipped retry behavior is unchanged (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `RetryPolicy` and `WorkflowDef` are re-exported from `scripts/agent/workflow/__init__.py`; making their constructor arguments required is a breaking change for external callers, but on this host the only callers are `workflow_loader.py` and the test files listed in the Plan (`confirmed by repository evidence`).
- `WorkflowDef` currently has no `__post_init__`, so adding one does not override or conflict with existing initialization.
- Decision 1 (Plan `Design`): the model owns empty-stage validation via `__post_init__`; the loader keeps its own `'stages' must be a non-empty list` guard as the config-path error surface.

## Design decisions
- **Empty-stage owner = model `__post_init__`**: direct model construction is exercised by the orchestrator and five test files, so a model-level guard closes the bypass path that makes loader-only strictness not a real guarantee. The loader's existing check stays because a test pins its message (`test_empty_stages_list` matches `"non-empty list"`).
- **`AssertionError` for empty `stages`**: the model raises `AssertionError` on an empty `stages` list; the three now-required positional/keyword arguments raise `TypeError` when omitted (dataclass default).

## Alternatives considered
- **Loader-only empty-stage ownership**: viable (the loader is the sole production constructor) and smaller, but leaves a construction-bypass path open for direct `WorkflowDef(...)` callers. Rejected in favor of the model owning the invariant.

## Implementation
### Target file
`scripts/agent/workflow/models.py`
### Procedure
1. `RetryPolicy` (`REQ-003`): remove the default from `retry_on`.
2. `WorkflowDef.stages` (`REQ-003`): remove the `default_factory`.
3. `WorkflowDef.retry_policy` (`REQ-003`): remove the `default_factory`.
4. `WorkflowDef.__post_init__` (`REQ-004`): add empty-stage validation.
### Method
Three field-signature edits plus one new dataclass method. No import changes (`field` stays imported and used by nothing else here, but keep the import — it is still referenced by the type annotations' `field` usage removal; verify `field` is unused after and drop the import only if the linter confirms).
### Details
- Line 80: change
  `    retry_on: tuple[str, ...] = ("exception",)`
  to
  `    retry_on: tuple[str, ...]`
  (required; no default).
- Line 89: change
  `    stages: list[StageDefinition] = field(default_factory=list)`
  to
  `    stages: list[StageDefinition]`
  (required).
- Lines 90-92: change
  `    retry_policy: RetryPolicy = field(`
  `        default_factory=lambda: RetryPolicy(max_attempts=3, retry_wait_sec=1)`
  `    )`
  to
  `    retry_policy: RetryPolicy`
  (required).
- After the dataclass fields (e.g., right after line 92, before `get_stage`), add:
  ```python
      def __post_init__(self) -> None:
          """Reject a definition with no stages."""
          assert self.stages, "WorkflowDef requires at least one stage"
  ```
- Verify `from dataclasses import field` is still needed; if `field` is now unused, remove that name from the import (`from dataclasses import dataclass`). Do not remove `dataclass`.

## Compatibility considerations
Additive. Existing valid definitions always carry `stages` and `retry_policy`, and the shipped `config/workflows/default.json` supplies `retry_on`, so shipped behavior is unchanged. Only construction sites that omitted the three arguments now raise.

## Security considerations
N/A: no auth, permission, or untrusted-input handling changes.

## Rollback considerations
Revert the commit; the change is confined to one file's constructor signatures and one added method.

## Validation plan
- Unit: `RetryPolicy(max_attempts=3, retry_wait_sec=1)` without `retry_on` → `TypeError`; `WorkflowDef(name="x", version="1.0.0")` without `stages`/`retry_policy` → `TypeError`; construct with all args → success; `WorkflowDef(stages=[], ...)` → `AssertionError`.
- Command: `uv run pytest tests/agent/workflow/test_workflow_models.py`.
- Regression: `uv run pytest tests/agent/workflow tests/agent/test_orchestrator.py` (every call site updated in the companion rows).

## Completion criteria
- `RetryPolicy.retry_on`, `WorkflowDef.stages`, `WorkflowDef.retry_policy` have no defaults in the source.
- `WorkflowDef.__post_init__` asserts non-empty `stages`.
- Constructor-surface tests in `test_workflow_models.py` require all three arguments and the empty-stage owner; `test_default_retry_policy` and `test_stages_default_empty` removed.

## Out of Scope
Changing retry semantics, retry kinds, or `max_attempts`/`retry_wait_sec` handling; the loader's empty-stages guard (kept intact); the `test_default_retry_policy`/`test_stages_default_empty` removal is covered by the test row, not this file's behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-092806 | 20261117-092806 | Implementation applied. Static validation passed (ruff format/check, mypy, lint-imports, bandit). ~14 test-call-site failures across batch-owned companion test files (seq 04-09) are expected; resolved by those companion procedures; full-suite validated once at batch end. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by `tests/agent/workflow/test_workflow_models.py` (seq 05). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docs handled by seq 03. |

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
- **Requirement ID**: `REQ-003` (make the three arguments required), `REQ-004` (empty-stage owner)
- **Source issue**: `issues/20261116-114753_compat001_workflow-definition-strict-contract.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261116-214100_compat001_workflow-definition-strict-contract.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-005004
- **Related target files**: `scripts/agent/workflow/models.py`
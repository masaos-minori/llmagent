## Goal
Rename the `RetryPolicy` field `backoff_sec` to `retry_wait_sec` in `scripts/agent/workflow/models.py` — the dataclass field and the `WorkflowDef` default policy factory — so the name states the fixed-delay semantics the engine actually implements (`REQ-003`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 3 only: `scripts/agent/workflow/models.py`.

## Assumptions
- This procedure defines `retry_wait_sec` (new); it lands first in the plan's Phase 3 rename chain (models -> loader -> engine -> config -> tests), before procedures 02, 04, 06 and the test procedures.
- The dataclass has no positional-construction callers that would break on a keyword-name change in an unsafe way: the census found construction only via keyword arguments (`workflow_loader.py` L170-173, test fixtures); `dataclass` field order otherwise unchanged.

## Design decisions
- Pure rename of the field `backoff_sec` -> `retry_wait_sec` (new); type `int`, position (between `max_attempts` and `retry_on`), and the `RetryPolicy` docstring's `max_attempts`/`retry_on` wording stay as-is except the field name the docstring/comment references.
- `WorkflowDef` default_factory `RetryPolicy(max_attempts=3, backoff_sec=1)` -> `RetryPolicy(max_attempts=3, retry_wait_sec=1)` (L91): the shipped default wait stays numerically 1 (`REQ-004`).

## Alternatives considered
- Keep `backoff_sec` and add a property alias: rejected — a second name for one value is exactly the dead-alias pattern the sibling wfaudit008 plan removes elsewhere, and `tools/check_compat_shims.py` policy forbids renamed-key shims (plan UNK-02 decision).

## Implementation
### Target file
`scripts/agent/workflow/models.py`

### Procedure
Rename the `RetryPolicy` field and the default-factory keyword.

### Method
1. `RetryPolicy` body: `backoff_sec: int` -> `retry_wait_sec` (new) declared as `retry_wait_sec: int` (field line at HEAD L79).
2. `WorkflowDef.retry_policy` default_factory (HEAD L91): `RetryPolicy(max_attempts=3, backoff_sec=1)` -> `RetryPolicy(max_attempts=3, retry_wait_sec=1)`.

### Details
- `grep -n backoff_sec scripts/agent/workflow/models.py` must return nothing after the edits.
- The docstring above `RetryPolicy` (retry_on kinds text) names no policy wait field; no other text in the file references the old name.

## Compatibility considerations
- Every keyword caller of `RetryPolicy(backoff_sec=...)` must land in the same release unit (rows 2, 4, 7-11); until they land, the tree is mid-rename — the plan sequences them inside one unit (`REQ-004` numerics preserved by value 1 everywhere).
- No serialized form of `RetryPolicy` exists (it is not JSON-persisted; the persisted surfaces are attempts/lease rows), so no data migration.

## Security considerations
- No data-handling change.

## Rollback considerations
- Revert the commit together with the rest of the release unit; nothing persists the old or new field name.

## Validation plan
- `tests/agent/workflow/test_workflow_models.py` fixture/default assertions (procedure 09) pin the renamed field and the numeric default 1.
- `uv run pytest tests/agent/workflow/ -q` after rows 2-4 and 6-12 have landed; interim runs before the full chain lands are expected to fail on call sites, which is why the plan's Phase 3 lands as one chain before the completion gate.

## Completion criteria
- `REQ-003` for this file: no `backoff_sec` token remains in `models.py`; `REQ-004`: default wait value unchanged (1).

## Out of Scope
- `workflow_loader.py` key validation (row 4) and the `RetryEvent` DTO field (row 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-092921 | 20261109-092921 | — |
| 2 | Add or update tests per Validation plan | Completed | 20261109-092921 | 20261109-092921 | N/A: tests covered by procedures 07-12 and 15 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-092921 | 20261109-092921 | Full suite 11904 passed; 3 pre-existing env errors in test_workflow_status_vocabulary.py (/tmp/opencode missing); diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-092921 | 20261109-092921 | N/A: docs covered by procedures 13-14 |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-211937
- **Related target files**: scripts/agent/workflow/models.py

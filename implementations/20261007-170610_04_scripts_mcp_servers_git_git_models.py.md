# Implementation Procedure

## Goal

Make `branch` a required field in the `GitPullRequest` / `GitPushRequest` Pydantic
models (`scripts/mcp_servers/git/git_models.py`): drop `default=""` and correct the
descriptions, mirroring the schema change in `git_tools.py`. Driven by `REQ-004`.

## Scope

Modifies only `scripts/mcp_servers/git/git_models.py`. Cross-file effects are
dependencies, not targets:

- `scripts/mcp_servers/git/git_tools.py` — the JSON schema must require `branch`
  too; own document.
- Tests constructing `GitPullRequest`/`GitPushRequest` with `branch=""` or omitting
  `branch` will now fail Pydantic validation and must be updated (own documents).

## Assumptions

- A `Field(...)` with no default makes the field mandatory under Pydantic; omitting
  the `default=` keyword is sufficient.
- The model and the JSON schema must agree (both require `branch`).

## Design decisions

- **Mirror the schema.** Same field order, same required semantics as
  `git_tools.py`. Keep the `remote: str = Field(default="origin", ...)` and
  `dry_run` fields unchanged.
- **Description must not imply emptiness is valid.** Replace the "empty = current
  branch/tracking branch" wording.

## Alternatives considered

- **Keep `branch=""` and fix only the description.** Rejected: the plan's REQ-004
  requires the field to be required, so the default must be removed (via the
  `Field(...)` required marker), not merely reworded.
- **Add a Pydantic `field_validator` rejecting an empty string.** Rejected as beyond
  scope: the contract is a *required* field (presence enforced by `Field(...)` and the
  `git_tools.py` schema `required` list). Rejecting the literal empty string is
  already covered by the write-tool validators; a separate validator would duplicate
  that contract.

## Implementation

### Target file

`scripts/mcp_servers/git/git_models.py`

### Procedure

- `GitPullRequest.branch` (lines 183-186):

  ```python
  branch: str = Field(description="Branch name to pull (required)")
  ```

- `GitPushRequest.branch` (line 197):

  ```python
  branch: str = Field(description="Branch name to push (required)")
  ```

### Details

- Do not touch any other model field. Leave `GitCheckoutRequest` unchanged (its
  `branch` is already required).

## Compatibility considerations

- Any construction of `GitPullRequest`/`GitPushRequest` without `branch` now raises
  a Pydantic validation error. Update affected test constructions (own documents).

## Security considerations

- Removes the misleading empty-branch default; no new attack surface.

## Rollback considerations

- Revert the single commit touching `git_models.py`.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `branch` required in models | Unit | `uv run pytest tests/mcp_servers/git/test_git_models.py -v` | `git_pull`/`git_push` without `branch` fail Pydantic validation |
| Whole git-mcp module | Full suite | `uv run pytest tests/mcp_servers/git/ -v` | no new failures |
| Toolchain | Static/type/security | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | clean per `rules/toolchain.md` |

## Completion criteria

- `GitPullRequest.branch` and `GitPushRequest.branch` have no `default` and require
  a value.
- Full git-mcp suite and toolchain pass with no new failures.

## Out of scope

- Schema change in `git_tools.py` — REQ-004, own document.
- `format_push()` fallback removal — REQ-004, own document.
- Audit record / error-path changes (separate issue).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261008-073225 | REQ-004: branch required in GitPullRequest/GitPushRequest Post-hoc archive: code landed in fbfa4d416; verified vs source; 307 tests pass |
| 2 | Add or update tests per Validation plan | Completed | — | 20261008-073225 | test_git_models.py own row Post-hoc archive: code landed in fbfa4d416; verified vs source; 307 tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261008-073225 | Post-hoc archive: code landed in fbfa4d416; verified vs source; 307 tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261008-073225 | N/A: doc updates are Rows 8-10 Post-hoc archive: code landed in fbfa4d416; verified vs source; 307 tests pass |

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
- **Requirement ID**: `REQ-004` (make `branch` required in `git_pull`/`git_push` Pydantic models; fix descriptions)
- **Source issue**: `issues/20261007-153840_gitref01_fix-git-mcp-ref-validation-and-protected-branch-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261007-162035_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261007-170610
- **Related target files**: `scripts/mcp_servers/git/git_models.py`
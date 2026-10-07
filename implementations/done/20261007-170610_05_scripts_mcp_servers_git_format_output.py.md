# Implementation Procedure

## Goal

Remove the unreachable `branch = req.branch or state.active_branch` fallback in
`format_push()` (`scripts/mcp_servers/git/format_output.py`). With `branch` now
required (REQ-004), `req.branch` is always present, so the `or state.active_branch`
fallback can never evaluate. Driven by `REQ-004`.

## Scope

Modifies only `scripts/mcp_servers/git/format_output.py`. Cross-file effects are
dependencies, not targets:

- The removal is only safe once `GitPushRequest.branch` is required
  (`git_models.py`, own document) and the schema requires it (`git_tools.py`, own
  document). Implement after those.

## Assumptions

- `format_push()` is only reached through the write path where `req.branch` is now
  guaranteed non-empty.

## Design decisions

- **Collapse to the direct access.** Replace the fallback expression with a plain
  assignment so the branch used for push/dry-run/output is exactly `req.branch`.

## Alternatives considered

- **Raise when `req.branch` is empty.** Rejected: with `branch` now required
  (REQ-004, `git_models.py`), `req.branch` is always present at this call site, so a
  runtime guard is dead code. Removing the unreachable fallback is sufficient.
- **Leave the fallback and silence the linter.** Rejected: the expression is
  genuinely unreachable once `branch` is required; leaving it misleads readers into
  thinking an implicit-HEAD push is possible.

## Implementation

### Target file

`scripts/mcp_servers/git/format_output.py`

### Procedure

In `format_push()` (line 207), change:

```python
    branch = req.branch or state.active_branch
```

to:

```python
    branch = req.branch
```

Leave the rest of `format_push()` (the dry-run message, the `git.push` call, the
rejection-marker check, the return) unchanged.

### Method

- This is a one-line edit at line 207 only.
- Do not touch `format_pull()` (its `pull_args` already guards `if req.branch`).

## Compatibility considerations

- Only safe after `branch` becomes required in the schema and model. If
  `format_push()` is ever called with a request lacking `branch`, `req.branch` will
  be whatever the caller passed; the required-field contract now prevents the
  empty case at validation.

## Security considerations

- No security impact; removes dead fallback logic.

## Rollback considerations

- Revert the single commit touching `format_output.py`.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `format_push()` uses `req.branch` directly | Unit | `uv run pytest tests/mcp_servers/git/ -k "push"` | push tests pass; no `state.active_branch` fallback |
| Whole git-mcp module | Full suite | `uv run pytest tests/mcp_servers/git/ -v` | no new failures |
| Toolchain | Static/type/security | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | clean per `rules/toolchain.md` |

## Completion criteria

- `format_push()` assigns `branch = req.branch` with no `or state.active_branch`
  fallback.
- Full git-mcp suite and toolchain pass with no new failures.

## Out of scope

- Other `format_*` functions.
- Schema/model `branch`-required changes — own documents.
- Audit record / error-path changes (separate issue).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261008-073825 | REQ-004: remove unreachable fallback in format_push() REQ-004: removed dead 'or state.active_branch' fallback; updated two obsolete push tests; 306 tests pass, ruff+mypy clean |
| 2 | Add or update tests per Validation plan | Completed | — | 20261008-073825 | REQ-004: removed dead 'or state.active_branch' fallback; updated two obsolete push tests; 306 tests pass, ruff+mypy clean |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261008-073825 | REQ-004: removed dead 'or state.active_branch' fallback; updated two obsolete push tests; 306 tests pass, ruff+mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261008-073825 | N/A: doc updates are Rows 8-10 REQ-004: removed dead 'or state.active_branch' fallback; updated two obsolete push tests; 306 tests pass, ruff+mypy clean |

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
- **Requirement ID**: `REQ-004` (remove unreachable `req.branch or state.active_branch` fallback in `format_push()`)
- **Source issue**: `issues/20261007-153840_gitref01_fix-git-mcp-ref-validation-and-protected-branch-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261007-162035_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261007-170610
- **Related target files**: `scripts/mcp_servers/git/format_output.py`
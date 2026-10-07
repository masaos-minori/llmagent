# Implementation Procedure

## Goal

Make `branch` a required field in the `git_pull` and `git_push` JSON schemas
(`scripts/mcp_servers/git/git_tools.py`): drop the `default: ""`, add `branch` to
each tool's `required` array, and correct the descriptions so the schema no longer
advertises an empty-branch default that `_validate_protected("")` rejects. Driven
by `REQ-004`.

## Scope

Modifies only `scripts/mcp_servers/git/git_tools.py`. Cross-file effects are
dependencies, not targets:

- `scripts/mcp_servers/git/git_models.py` — the Pydantic models must mirror the
  schema (`branch` required, no `default=""`); own document.
- Tests constructing `GitPullRequest`/`GitPushRequest` with `branch=""` or omitting
  `branch` will now fail Pydantic validation and must be updated (own documents).

## Assumptions

- `git_checkout`'s schema already lists `branch` in `required` (no `default`), so it
  needs no change for REQ-004.
- The Pydantic models and the JSON schema are the two faces of the same contract;
  both MUST require `branch` consistently.

## Design decisions

- **Schema-only change here.** This document changes only the JSON `inputSchema`.
  The Pydantic model change is a separate target file (own document) — do not fold
  it in.
- **Description must not imply emptiness is valid.** Replace the "empty = current
  branch/tracking branch" wording, which encodes the now-invalid default.

## Alternatives considered

- **Add a `minLength: 1` schema constraint in addition to `required`.** Rejected as
  unnecessary: a missing field already fails JSON Schema validation via `required`,
  and the Pydantic model (`git_models.py`) enforces non-emptiness at runtime. Adding
  `minLength` would duplicate the contract in the schema without a corresponding test
  benefit; keep the change minimal and schema-only.
- **Make `branch` required on all write tools.** Rejected: `git_checkout` allows an
  implicit current-branch target and keeps its `branch` optional; only
  `git_pull`/`git_push` require it per REQ-004.

## Implementation

### Target file

`scripts/mcp_servers/git/git_tools.py`

### Procedure

For BOTH `git_pull` and `git_push`:

1. In the `branch` property, delete the `"default": ""` line.
2. Replace the `description` with a required-field wording, e.g.
   `"Branch name to pull (required)"` for `git_pull` and
   `"Branch name to push (required)"` for `git_push`.
3. Add `branch` to the tool's `required` array:
   - `git_pull` (line 233): `"required": ["repo_path"]` →
     `"required": ["repo_path", "branch"]`.
   - `git_push` (line 265): `"required": ["repo_path"]` →
     `"required": ["repo_path", "branch"]`.

Leave every other tool's schema unchanged.

### Method

- `git_pull` `branch` property (lines 222-226):

  ```json
  "branch": {
      "type": "string",
      "description": "Branch name to pull (required)"
  },
  ```

- `git_push` `branch` property (lines 254-258):

  ```json
  "branch": {
      "type": "string",
      "description": "Branch name to push (required)"
  },
  ```

### Details

- Do not touch `git_checkout` (already requires `branch`), nor the read tools'
  `branch`/`commit`/`ref` fields (they keep their empty-default semantics).

## Compatibility considerations

- Callers must now supply `branch` for `git_pull`/`git_push`; an omitted/empty
  value fails JSON-schema / Pydantic validation instead of silently meaning
  "current branch". This is the REQ-004 contract change.

## Security considerations

- An empty-branch default that always failed `_validate_protected("")` was a
  contract contradiction, not a security issue; this change removes the misleading
  default. No new attack surface.

## Rollback considerations

- Revert the single commit touching `git_tools.py`. Schema-only change; no runtime
  logic affected.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `branch` required in schema | Unit | `uv run pytest tests/mcp_servers/git/test_git_models.py -v` | `git_pull`/`git_push` without `branch` fail Pydantic validation |
| Whole git-mcp module | Full suite | `uv run pytest tests/mcp_servers/git/ -v` | no new failures |
| Toolchain | Static/type/security | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | clean per `rules/toolchain.md` |

## Completion criteria

- `git_pull` and `git_push` schemas list `branch` in `required` and carry no
  `default: ""`, with corrected descriptions.
- `git_pull`/`git_push` without `branch` fail Pydantic validation.
- Full git-mcp suite and toolchain pass with no new failures.

## Out of scope

- Pydantic model changes in `git_models.py` — REQ-004, own document.
- `format_push()` unreachable-fallback removal — REQ-004, own document.
- Audit record / error-path changes (separate issue).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261008-072031 | REQ-004: branch required in git_pull/git_push schemas Post-hoc archive: code landed in fbfa4d416; 307 tests pass; ruff+mypy clean |
| 2 | Add or update tests per Validation plan | Completed | — | 20261008-072031 | test_git_models.py own row Post-hoc archive: code landed in fbfa4d416; 307 tests pass; ruff+mypy clean |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261008-072031 | Post-hoc archive: code landed in fbfa4d416; 307 tests pass; ruff+mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261008-072031 | N/A: doc updates are Rows 8-10 N/A: no docs/00_index.md task-scope mapping for changed file |

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
- **Requirement ID**: `REQ-004` (make `branch` required in `git_pull`/`git_push` schemas; fix descriptions)
- **Source issue**: `issues/20261007-153840_gitref01_fix-git-mcp-ref-validation-and-protected-branch-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261007-162035_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261007-170610
- **Related target files**: `scripts/mcp_servers/git/git_tools.py`
## Goal

Create the test for ADR-012 INV-04: Git MCP validation neither assumes nor requires Agent-side approval state (AAL-036).

## Scope
**Release unit**: N/A: not part of a release unit

One new test module. No production change.

## Assumptions

- The validation path is `RepositoryState` (`verify_authorization`) and `WriteProtectionPipeline.run` (`scripts/mcp_servers/git/repository_state.py:129`, `write_protection_pipeline.py:154`; re-read in Step 3a).
- The Git package has no `agent` import and no approval identifier today (rg in Step 3a).

## Design decisions

- Real temporary repository tests: a protected-branch checkout is denied with and without approval-shaped input, and a non-protected checkout is allowed with none.
- An AST scan of `scripts/mcp_servers/git/` for an `agent` import and `approv`, `grant`, `plan_mode` identifiers, asserting it scanned the package files.

## Alternatives considered

Rely on the import-linter contract only: rejected, it does not run in the test suite.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_approval_independence.py` (new)

### Procedure
1. Read `tests/mcp_servers/git/test_repository_state.py` for the real-repository fixtures.
2. Create `tests/mcp_servers/git/test_git_approval_independence.py` (new).
3. Add the behavioral tests through `RepositoryState` and the pipeline with forged approval-shaped arguments.
4. Add the `repo_scan` AST test.

### Method
- Use `git.Repo.init` in `tmp_path`; set the protected-branch configuration the existing tests use.
- Treat any name containing `approv`, `grant`, or `plan_mode` in a function, argument, or attribute as a finding.

### Details
- Mutation check: add `import agent` to a Git module temporarily, confirm failure, revert.
- Cite the tests in ADR-012's INV-04 row in procedure 09.

## Compatibility considerations

N/A: adds a test only; no production behavior changes.

## Security considerations

N/A: the test only reads a temporary repository; the forged inputs are inert dummy values.

## Rollback considerations

N/A: revert the commit (the file is new).

## Validation plan

- `uv run pytest tests/mcp_servers/git/test_git_approval_independence.py -q`
- ruff and mypy on the file

## Completion criteria

- Behavioral and scan tests pass and fail under the mutation.
- Only the new file was added.

## Out of Scope

- Any file other than the target file (and its companions, if any); any change under `scripts/` or `config/`.
- Approval text: no approver, date, or approval sentence is written.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Mutation-check the new test: break the invariant temporarily, confirm the test fails, revert the break | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (Git MCP validation independent of Agent approval state (ADR-012 INV-04)), `REQ-008` (no production change, every test mutation-checked)
- **Source issue**: issues/20261123-164658_gov006_restore-blocking-verification-rows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-165432_gov006_restore-blocking-verification-rows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-165833
- **Related target files**: `tests/mcp_servers/git/test_git_approval_independence.py`

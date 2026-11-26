## Goal

Add the integration suite that performs each Git write on a real temporary repository and verifies the postcondition against the fresh post-operation snapshot the pipeline produces, plus the resource-close tests for the five execution paths (REQ-005, REQ-006, AC-2, AC-5).

## Scope
**Release unit**: postcondition-tests-and-implementation

## Assumptions

- Written in Phase 1 against the unmodified pipeline; the postcondition cases fail until procedures 01, 02, 03, 04 land, which is why this row is in the `postcondition-tests-and-implementation` unit.
- The resource-close cases for the timeout path depend on the subprocess path from procedure 04, so they are written against the vocabulary outcome, not against a `wait_for` timeout.
- `tests/mcp_servers/git/` already has real-repository fixtures (`test_repository_state.py:39` `working_repo`, `test_git_service_dispatch.py:615`); this file defines its own fixtures so the write cases do not depend on another module's fixtures.
- Handle-leak detection uses the observable state of the `git.Repo` handle (`_repo is None` after `close()`) rather than a process-wide file-descriptor count, which is not stable under parallel test execution.

## Design decisions

- One test class per write tool, each with a passing case and a designed failing case, so a failing postcondition is proven, not only the passing path (REQ-006).
- Push uses a bare repository as the remote, so the remote-tracking ref comparison (AC-2) is exercised without network access.

## Alternatives considered

- Extend `tests/mcp_servers/git/test_repository_state.py` instead of creating a new file — rejected: that file is the unit-level suite for `RepositoryState`, and integration cases that run the full pipeline belong in a separate file so the pipeline's own post-state is what the assertions read.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_write_postconditions.py` (new)

### Procedure
- Fixtures: a temporary working repository with one commit, and a bare repository registered as the `origin` remote.
- Per-tool cases for `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push`: run `WriteProtectionPipeline.run()` with the tool's formatter op, then assert `result.post_state` is a distinct object from `result.repository_state` and that the postcondition reflects the real effect.
- Designed failing cases: add with no staged entry, commit that does not advance HEAD, checkout that does not move HEAD, pull with unmerged blobs, push where the remote ref does not equal the local commit.
- Resource-close cases for the five paths: success, policy rejection, dry-run, exception, timeout.

### Method
- Assert the handle is released by checking `state._repo is None` after the pipeline call, on each of the five paths.
- Use `subprocess`-driven paths only through the service layer for the timeout case; the direct pipeline cases call the formatter op.
- Keep assertions on the rejection stage (`result.rejected_at_stage == "Stage 7"`) rather than on message wording.

### Details

- No network access: the bare repository is a local remote added with `git remote add origin <path>`.
- Each case is deterministic: no sleeps, no reliance on wall-clock timing except the timeout case, which uses a short configured timeout.
- The file is added to the existing `tests/mcp_servers/git/` suite; no `conftest.py` change is needed because the fixtures are local to this file.

## Compatibility considerations

- `tests/mcp_servers/git/test_repository_state.py:371` (`test_pipeline_result_ok_has_post_state`) currently passes `post_state=state` explicitly; the distinct-object assertion is added there by procedure 08, and this file covers the same condition through the pipeline.
- `tests/mcp_servers/git/test_git_security_compliance.py:763` (ADR-012 INV-06) must stay green; this file does not replace it (UNK-02).

## Security considerations

- The cases run against temporary repositories only; `allowed_repo_paths` is set to the temporary path so the path-containment guard is exercised, not bypassed.

## Rollback considerations

- Delete the file; no other test file depends on it.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Postcondition integration cases | `uv run pytest tests/mcp_servers/git/test_git_write_postconditions.py -v` | Each tool's passing and failing case behaves as designed |
| Resource-close cases | `uv run pytest tests/mcp_servers/git/test_git_write_postconditions.py -v` | No leaked `git.Repo` handle on the five paths |
| Full suite | `uv run pytest` | No regression |
| Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Changed-line coverage | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% |

## Completion criteria

- Each Git write has a proven postcondition on a real repository (AC-1, AC-2).
- Repeated execution does not leak repository handles or file descriptors on success, rejection, dry-run, exception, and timeout (AC-5).

## Out of Scope

- The pipeline implementation (procedure 01) and the postcondition branches (procedure 02).
- The timeout process-group cases (`tests/mcp_servers/git/test_git_service_dispatch.py`, procedure 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the integration and resource-close cases against the unmodified pipeline and record which fail | Pending | — | — | Phase 1 |
| 2 | Re-run after procedures 01-04 land | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation is procedure 11 |

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
- **Requirement ID**: `REQ-005` (handle release on every path), `REQ-006` (postcondition tests on real repositories)
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-004921_mcpai008_git-postcondition-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-111533
- **Related target files**: `tests/mcp_servers/git/test_git_write_postconditions.py`

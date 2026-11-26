## Goal

Move the postcondition assertions in this suite from mock states to real repositories that perform the write and are verified against a fresh post-operation snapshot, so the postcondition behavior is proven by an actual repository effect (REQ-006, AC-1, AC-2).

## Scope
**Release unit**: postcondition-tests-and-implementation

## Assumptions

- Phase 1 writes these cases against the unmodified pipeline and records which fail; they pass only after procedures 01 and 03 land, which is why this row is part of the `postcondition-tests-and-implementation` unit.
- The existing `working_repo` fixture at line 39 and `bare_repo` at line 30 are reused; a second repository is added for the push cases as a bare remote.
- Needs confirmation (UNK-02, non-blocking): the Plan's default is to supplement the ADR-cited mock postcondition tests, not replace them. The mock cases that pin authorization behavior only (line 298, `_make_mock_repo()` at line 557) stay as they are; only the mock cases that pin postcondition behavior are converted.
- `tests/mcp_servers/git/test_git_security_compliance.py:763` (`TestPostConditionBypassPrevention`, ADR-012 INV-06) is a reference file and is not modified.

## Design decisions

- Characterization tests that pin the current behavior are converted rather than deleted, so the suite keeps a record of the behavior change: `test_verify_postcondition_passes_for_any_push_result` (line 171) and `TestStage7RejectionCharacterization` (line 945, `assert result.post_state is state` at line 970) are rewritten against the new behavior.
- Real-repository cases use the pipeline, not the state object alone, so the fresh post-state produced by procedure 01 is what the assertions read.

## Alternatives considered

- Keep the mock cases and add parallel real-repository cases in a new file — rejected: the new file is procedure 10's scope, and duplicating the same assertions in two files would leave the mock cases pinning behavior this Plan changes.

## Implementation
### Target file
`tests/mcp_servers/git/test_repository_state.py`

### Procedure
- Rewrite `test_verify_postcondition_passes_for_any_push_result` (line 171) as a real-repository push case that asserts the remote-tracking ref equals the local commit, and add the designed failure case where the remote ref does not match.
- Rewrite `TestStage7RejectionCharacterization` (line 945) to run `WriteProtectionPipeline.run()` against `working_repo` and assert `result.post_state` is a distinct object from `result.repository_state` and that a failed postcondition rejects at Stage 7.
- Convert the mock-state pipeline case at line 656 to a real-repository pipeline run for the postcondition path; keep the authorization assertions that the mock state pins.
- Add per-operation cases for `git_add`, `git_commit`, `git_checkout`, `git_pull` against `working_repo`, each with one passing and one designed-failing case.

### Method
- Use the fixtures at lines 30 and 39; add a `push_remote` (new) fixture that creates a bare repository and registers it as a remote of `working_repo`.
- Assert through `verify_postcondition(post_state, tool)` where `post_state` comes from the pipeline result, not from a hand-built `RepositoryState`.
- Keep the existing stage-name assertions (`[stage.name for stage in pipeline.stages]`) so the stage order pinned by ADR-012 INV-09 stays covered.

### Details

- Message-text assertions are kept only where the test already asserts them; the Plan states callers must not depend on message text, so new assertions check the rejection stage rather than the wording.
- Detached-HEAD and protected-branch assertions stay in their existing classes.

## Compatibility considerations

- Eight test files import `scripts/mcp_servers/git/repository_state.py`; only the assertions named above pin the behavior this Plan changes.
- `tests/mcp_servers/git/test_git_write_postconditions.py` (procedure 10) covers the integration cases; this file keeps the unit-level per-operation branches.

## Security considerations

- No authorization behavior is changed; the ADR-cited bypass-prevention tests must stay green unchanged.

## Rollback considerations

- Revert the commit; converted cases revert to their mock form together with the implementation they pin.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Converted postcondition cases | `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` | Each per-operation case passes against a real repository |
| ADR-cited bypass prevention unchanged | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` | No change |
| Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Changed-line coverage | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% |

## Completion criteria

- Every write tool's postcondition is asserted against a real repository effect, and the two characterization tests reflect the new behavior (AC-1, AC-2).
- No postcondition assertion in this file depends on a mock repository.

## Out of Scope

- The implementation of the postcondition branches (`scripts/mcp_servers/git/repository_state.py`, procedure 02).
- The resource-close tests (`tests/mcp_servers/git/test_git_write_postconditions.py`, procedure 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the converted cases against the unmodified pipeline and record which fail | Pending | — | — | Phase 1 |
| 2 | Re-run after procedures 01 and 03 land | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` (postcondition tests on real repositories)
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-004921_mcpai008_git-postcondition-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-111533
- **Related target files**: `tests/mcp_servers/git/test_repository_state.py`

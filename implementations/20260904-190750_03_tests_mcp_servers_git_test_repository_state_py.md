## Goal

Add unit tests for the fixed `verify_postcondition()`, `post_state` capture, and `record_stage()` wiring.

## Scope

- `tests/mcp_servers/git/test_repository_state.py`: add unit tests for the fixed `verify_postcondition()`, `PipelineResult.post_state`, and `record_stage()` wiring.

## Assumptions

- Existing file already covers `RepositoryState`/pipeline unit-level behavior — natural home for the fixed unit-level logic.
- Tests should follow existing patterns (e.g., `TestGuardDelegation`-style test classes targeting pipeline internals).
- The companion document for `repository_state.py` defines the exact behavioral changes these tests validate.

## Design decisions

- **Real-repo vs. mock**: Use `unittest.mock.patch` to inject controlled `RepositoryState` instances into `WriteProtectionPipeline.run()` and `PipelineResult` methods. Avoid real repos unless absolutely necessary for verifying the postcondition logic.
- **Isolation**: Each test verifies one specific aspect (postcondition rejection, post_state distinction, stage recording) without depending on other tests' state.
- **Failure simulation**: Inject `PipelineStage` objects with `failed=True` results to simulate stage failures and verify `all_stages_succeeded`/`last_failed_stage` behavior.

## Alternatives considered

- Using real temp repos for all tests — rejected because unit tests should be fast and deterministic; real repos add unnecessary I/O and flakiness risk.
- Testing through HTTP dispatch (`POST /v1/call_tool`) — rejected because that is covered by the companion document for `test_git_security_compliance.py`.

## Implementation

### Target file

`tests/mcp_servers/git/test_repository_state.py`

### Procedure

1. Add test class `TestVerifyPostcondition` with tests:
   - `test_verify_postcondition_rejects_failed_checkout`: assert `verify_postcondition()` rejects a simulated failed-checkout state.
   - `test_verify_postcondition_accepts_successful_checkout`: assert success when conditions are met.
   - `test_verify_postcondition_rejects_unresolved_conflicts`: assert rejection for pull with unresolved conflicts.
   - `test_verify_postcondition_rejects_push_failure`: assert rejection for push with rejection markers.
2. Add test class `TestPipelineResultPostState` with tests:
   - `test_post_state_differs_from_pre_state_after_mutating_operation`: assert `PipelineResult.post_state` differs from `repository_state` (pre-state) after a mutating operation.
   - `test_post_state_none_for_non_mutating_result`: assert `post_state` is None for non-mutating operations.
3. Add test class `TestRecordStage` with tests:
   - `test_record_stage_populates_stages_list`: assert `stages` list reflects actual execution and ordering.
   - `test_all_stages_succeeded_false_on_injected_failure`: assert `all_stages_succeeded` reports accurate results from recorded stages, not vacuous defaults.
   - `test_last_failed_stage_returns_correct_stage`: assert `last_failed_stage` returns the correct failed stage.
4. Add integration test class `TestPipelineRunWithRecording` with tests:
   - `test_run_records_all_stages_and_captures_post_state`: assert complete pipeline records all stages and captures post-state.
   - `test_run_rejects_on_stage_failure`: assert a failed stage prevents all subsequent unsafe stages from running.

### Method

- Create mock `RepositoryState` instances with controlled properties (`active_branch`, `_repo.index.unmerged_blobs()`, etc.).
- Patch `WriteProtectionPipeline.run()` to inject these mocks and verify the expected behavior.
- Use `pytest.raises(GitServiceError)` for failure assertions.
- For `PipelineResult` tests, directly instantiate `PipelineResult` with different field combinations and assert field values.

### Details

**1. TestVerifyPostcondition:**

```python
class TestVerifyPostcondition:
    def test_verify_postcondition_rejects_failed_checkout(self):
        """AC-3: verify_postcondition() no longer returns unconditional success."""
        # Arrange: create a mock RepositoryState where active_branch doesn't match request
        mock_state = MagicMock(spec=RepositoryState)
        mock_state.active_branch = "main"
        mock_state._requested_branch = "feature"
        
        # Act
        ok, msg = mock_state.verify_postcondition(None, mock_state, "git_checkout")
        
        # Assert
        assert ok is False
        assert "expected branch" in msg
    
    def test_verify_postcondition_accepts_successful_checkout(self):
        ok, msg = mock_state.verify_postcondition(None, mock_state, "git_checkout")
        assert ok is True
        assert msg == ""
    
    def test_verify_postcondition_rejects_unresolved_conflicts(self):
        """REQ-005: pull postcondition detects unresolved conflicts."""
        mock_repo = MagicMock()
        mock_repo.index.unmerged_blobs.return_value = {"conflict_file": ["a", "b", "c"]}
        mock_state = MagicMock(spec=RepositoryState)
        mock_state._repo = mock_repo
        
        ok, msg = mock_state.verify_postcondition(None, mock_state, "git_pull")
        assert ok is False
        assert "unresolved merge conflicts" in msg.lower()
    
    def test_verify_postcondition_rejects_push_failure(self):
        """REQ-006: push postcondition detects rejected outcomes."""
        mock_state = MagicMock(spec=RepositoryState)
        result_str = "error: failed to push some refs"
        
        ok, msg = mock_state.verify_postcondition(result_str, mock_state, "git_push")
        assert ok is False
        assert "push postcondition failed" in msg.lower()
```

**2. TestPipelineResultPostState:**

```python
class TestPipelineResultPostState:
    def test_post_state_differs_from_pre_state_after_mutating_operation(self):
        """AC-4: Pre-operation and post-operation states are separate snapshots."""
        pre_state = MagicMock(spec=RepositoryState)
        post_state = MagicMock(spec=RepositoryState)
        result = PipelineResult.ok_result(pre_state, "output", post_state=post_state)
        
        assert result.post_state is post_state
        assert result.repository_state is pre_state
        assert result.post_state is not result.repository_state
    
    def test_post_state_none_for_non_mutating_result(self):
        result = PipelineResult.ok_result(MagicMock(spec=RepositoryState), "output")
        assert result.post_state is None
```

**3. TestRecordStage:**

```python
class TestRecordStage:
    def test_record_stage_populates_stages_list(self):
        """AC-5: The pipeline's stages list reflects actual execution and ordering."""
        pipeline = WriteProtectionPipeline(MagicMock(spec=RepositoryState))
        pipeline.record_stage(PipelineStage(name="Stage 3", index=3, result=(True, "")))
        pipeline.record_stage(PipelineStage(name="Stage 5", index=5, result=(True, "")))
        
        assert len(pipeline.stages) == 2
        assert pipeline.stages[0].name == "Stage 3"
        assert pipeline.stages[1].name == "Stage 5"
    
    def test_all_stages_succeeded_false_on_injected_failure(self):
        """AC-6: all_stages_succeeded and last_failed_stage report accurate results."""
        pipeline = WriteProtectionPipeline(MagicMock(spec=RepositoryState))
        pipeline.record_stage(PipelineStage(name="Stage 3", index=3, result=(True, "")))
        pipeline.record_stage(PipelineStage(name="Stage 5", index=5, result=(False, "denied")))
        
        assert pipeline.all_stages_succeeded is False
        assert pipeline.last_failed_stage.name == "Stage 5"
    
    def test_all_stages_succeeded_true_when_all_pass(self):
        pipeline = WriteProtectionPipeline(MagicMock(spec=RepositoryState))
        pipeline.record_stage(PipelineStage(name="Stage 3", index=3, result=(True, "")))
        pipeline.record_stage(PipelineStage(name="Stage 5", index=5, result=(True, "")))
        
        assert pipeline.all_stages_succeeded is True
        assert pipeline.last_failed_stage is None
```

**4. TestPipelineRunWithRecording:**

```python
class TestPipelineRunWithRecording:
    @patch.object(WriteProtectionPipeline, 'run')
    def test_run_records_all_stages_and_captures_post_state(self, mock_run):
        """Integration: complete pipeline records all stages and captures post-state."""
        mock_state = MagicMock(spec=RepositoryState)
        mock_state.verify_authorization.return_value = (True, "")
        mock_state.verify_preconditions.return_value = (True, "")
        mock_state.verify_postcondition.return_value = (True, "")
        mock_state.snapshot.return_value = MagicMock(spec=RepositoryState)
        
        pipeline = WriteProtectionPipeline(mock_state)
        op = MagicMock(return_value="checkout output")
        
        result = pipeline.run("git_checkout", op)
        
        # Verify record_stage was called for each stage
        assert pipeline.state.record_stage.call_count >= 1
        # Verify post_state was captured
        assert result.post_state is not None
    
    def test_run_rejects_on_stage_failure(self):
        """AC-2: A failed stage prevents all subsequent unsafe stages from running."""
        mock_state = MagicMock(spec=RepositoryState)
        mock_state.verify_authorization.return_value = (False, "authorization denied")
        
        pipeline = WriteProtectionPipeline(mock_state)
        op = MagicMock(return_value="should not execute")
        
        result = pipeline.run("git_checkout", op)
        
        assert result.ok is False
        assert result.rejected_at_stage == "Stage 3"
        # Stage 5 should not have been reached
        assert not any(s.name == "Stage 5" for s in pipeline.stages)
```

## Compatibility considerations

- New test class names must not conflict with existing test classes in the file.
- Mock objects must implement the same interface as real `RepositoryState` instances to avoid false positives.
- Tests should be deterministic and not depend on external Git repositories or network access.

## Security considerations

- Tests validate security-critical postcondition enforcement — ensure they cover edge cases (detached HEAD, option-like refs, partial failures).
- Mock injection must not bypass the authorization checks being tested.

## Rollback considerations

- If new tests cause regressions due to behavioral changes in production code, revert the test additions while keeping the source fixes.
- If mock interfaces don't match production code, update mocks rather than reverting tests.

## Validation plan

- Run specific test classes: `uv run pytest tests/mcp_servers/git/test_repository_state.py::TestVerifyPostcondition -v`
- Run specific test classes: `uv run pytest tests/mcp_servers/git/test_repository_state.py::TestPipelineResultPostState -v`
- Run specific test classes: `uv run pytest tests/mcp_servers/git/test_repository_state.py::TestRecordStage -v`
- Run specific test classes: `uv run pytest tests/mcp_servers/git/test_repository_state.py::TestPipelineRunWithRecording -v`
- Full suite: `uv run pytest tests/mcp_servers/git/ -v` — no new failures.
- Static analysis: `uv run ruff check scripts/mcp_servers/git/`, `uv run mypy scripts/mcp_servers/git/`, `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- All new unit tests pass against the post-change code.
- Each new test fails against the pre-change code (verifies it catches the bug).
- `verify_postcondition()` rejects a simulated failed-checkout state.
- `PipelineResult.post_state` differs from `repository_state` (pre-state) after a mutating operation.
- `record_stage()` populates `stages` such that `all_stages_succeeded`/`last_failed_stage` reflect an injected failure.
- No new static analysis findings.

## Out of scope

- HTTP dispatch path tests (`POST /v1/call_tool`) — covered by companion document for `test_git_security_compliance.py`.
- Real-repo checkout regression test — covered by companion document for `test_format_output.py`.
- Known Issue documentation entry — covered by companion document for `docs/00_governance_03_issue-and-uncertainty-management.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-008
- **Source issue**: issues/20260902-144908_gitpipeline_enforce_complete_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-190750_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-190750
- **Related target files**: tests/mcp_servers/git/test_repository_state.py

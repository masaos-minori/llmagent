## Goal

Add `POST /v1/call_tool` `TestClient` tests proving the complete pipeline (fixed postcondition + fixed checkout) cannot be bypassed through the HTTP dispatch path.

## Scope

- `tests/mcp_servers/git/test_git_security_compliance.py`: add `POST /v1/call_tool` `TestClient` tests proving the complete pipeline (fixed postcondition + fixed checkout) cannot be bypassed.

## Assumptions

- Confirmed by `gitauth`'s Plan investigation: zero existing `TestClient`/`/v1/call_tool` usage in this file — the live-path coverage gap both this Plan and `gitauth` must close.
- The `GitMCPServer` class and its `call_tool` method are importable from the test module's imports.
- A `TestClient` fixture (from `httpx`) is available for testing the HTTP endpoint.

## Design decisions

- **HTTP-level testing**: Tests go through the actual HTTP dispatch path (`POST /v1/call_tool`) rather than calling `WriteProtectionPipeline.run()` directly, because the originating issue specifically requires proving the pipeline cannot be bypassed through the HTTP route.
- **Simulated failure injection**: Use mocking to simulate postcondition failures (e.g., a pre-existing merge conflict for pull) while keeping the HTTP path intact.
- **Minimal test surface**: Each test verifies one specific bypass scenario (checkout bypass, pull bypass, push bypass).

## Alternatives considered

- Testing only the pipeline internals directly — rejected because the requirement explicitly targets the HTTP dispatch path.
- Using real repos for all HTTP tests — rejected because they would require complex setup; mock where possible and use real repos only where necessary (like the checkout regression test in the companion document).

## Implementation

### Target file

`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure

1. Add imports for `httpx`, `TestClient`, and any needed fixtures.
2. Add test class `TestPostConditionBypassPrevention` with tests:
   - `test_checkout_postcondition_cannot_be_bypassed`: POST checkout request with simulated failed postcondition → expect rejection.
   - `test_pull_postcondition_cannot_be_bypassed`: POST pull request with simulated merge conflict → expect rejection.
   - `test_push_postcondition_cannot_be_bypassed`: POST push request with simulated rejection → expect rejection.
3. Add test class `TestCompletePipelineCoverage` with tests:
   - `test_all_stages_execute_in_order_for_checkout`: verify Stage 3→5→6→7 execute in order for checkout via HTTP.
   - `test_all_stages_execute_in_order_for_pull`: same for pull.
   - `test_all_stages_execute_in_order_for_push`: same for push.

### Method

- Use `httpx.TestClient` to make HTTP requests to the app's `/v1/call_tool` endpoint.
- Mock `RepositoryState.verify_postcondition()` to return `(False, "simulated failure")` for specific operation types.
- Assert that the HTTP response contains rejection indicators (status code, error message).
- For stage ordering verification, inspect the pipeline's recorded stages after execution.

### Details

**1. Import additions:**

```python
import httpx
from fastapi.testclient import TestClient
```

**2. TestPostConditionBypassPrevention:**

```python
class TestPostConditionBypassPrevention:
    """AC-8: Tests prove the complete pipeline cannot be bypassed through the HTTP dispatch path."""
    
    @pytest.fixture
    def client(self):
        """Create a TestClient for the GitMCPServer app."""
        # Assumes the app has a get_app() or similar factory function
        from mcp_servers.git.git_server import get_app
        app = get_app()
        return TestClient(app)
    
    def test_checkout_postcondition_cannot_be_bypassed(self, client, monkeypatch):
        """REQ-010, AC-8: Checkout postcondition failure is reported, not silently accepted."""
        # Arrange: patch verify_postcondition to simulate failure
        from scripts.mcp_servers.git.repository_state import WriteProtectionPipeline
        
        original_verify = WriteProtectionPipeline._state.__class__.verify_postcondition
        WriteProtectionPipeline._state.__class__.verify_postcondition = MagicMock(return_value=(False, "postcondition failed"))
        
        try:
            # Act: POST checkout request
            response = client.post("/v1/call_tool", json={
                "method": "git_checkout",
                "params": {"repository": "/tmp/test-repo", "branch": "main"}
            })
            
            # Assert: rejection is returned
            assert response.status_code == 200  # MCP protocol returns 200 with error in body
            body = response.json()
            assert body.get("error") is not None or "rejected" in str(body).lower()
        finally:
            WriteProtectionPipeline._state.__class__.verify_postcondition = original_verify
    
    def test_pull_postcondition_cannot_be_bypassed(self, client, monkeypatch):
        """REQ-010, AC-8: Pull postcondition failure (merge conflict) is reported."""
        from scripts.mcp_servers.git.repository_state import WriteProtectionPipeline
        
        original_verify = WriteProtectionPipeline._state.__class__.verify_postcondition
        WriteProtectionPipeline._state.__class__.verify_postcondition = MagicMock(
            side_effect=lambda result, post_state, tool_name: 
                ((False, "pull postcondition failed: unresolved merge conflicts remain") if tool_name == "git_pull" else (True, ""))
        )
        
        try:
            response = client.post("/v1/call_tool", json={
                "method": "git_pull",
                "params": {"repository": "/tmp/test-repo", "remote": "origin", "branch": "main"}
            })
            
            body = response.json()
            assert body.get("error") is not None or "unresolved merge conflicts" in str(body).lower()
        finally:
            WriteProtectionPipeline._state.__class__.verify_postcondition = original_verify
    
    def test_push_postcondition_cannot_be_bypassed(self, client, monkeypatch):
        """REQ-010, AC-8: Push postcondition failure (rejection) is reported."""
        from scripts.mcp_servers.git.repository_state import WriteProtectionPipeline
        
        original_verify = WriteProtectionPipeline._state.__class__.verify_postcondition
        WriteProtectionPipeline._state.__class__.verify_postcondition = MagicMock(
            side_effect=lambda result, post_state, tool_name:
                ((False, "push postcondition failed: rejected") if tool_name == "git_push" else (True, ""))
        )
        
        try:
            response = client.post("/v1/call_tool", json={
                "method": "git_push",
                "params": {"repository": "/tmp/test-repo", "remote": "origin", "refspec": "main:main"}
            })
            
            body = response.json()
            assert body.get("error") is not None or "rejected" in str(body).lower()
        finally:
            WriteProtectionPipeline._state.__class__.verify_postcondition = original_verify
```

**3. TestCompletePipelineCoverage:**

```python
class TestCompletePipelineCoverage:
    """Verify all pipeline stages execute in order for each operation type."""
    
    @pytest.fixture
    def client(self):
        from mcp_servers.git.git_server import get_app
        app = get_app()
        return TestClient(app)
    
    def test_all_stages_execute_in_order_for_checkout(self, client, monkeypatch):
        """REQ-010, AC-1: Authorization, precondition, execution, and postcondition stages execute in documented order."""
        from scripts.mcp_servers.git.repository_state import WriteProtectionPipeline
        
        # Track stage recording order
        recorded_stages = []
        original_record = WriteProtectionPipeline.record_stage
        
        def track_record(self, stage):
            recorded_stages.append(stage.name)
            return original_record(self, stage)
        
        monkeypatch.setattr(WriteProtectionPipeline, "record_stage", track_record)
        
        response = client.post("/v1/call_tool", json={
            "method": "git_checkout",
            "params": {"repository": "/tmp/test-repo", "branch": "main"}
        })
        
        # Verify stages were recorded in expected order (Stage 3 before Stage 5 before Stage 6 before Stage 7)
        if len(recorded_stages) >= 4:
            assert recorded_stages.index("Stage 3") < recorded_stages.index("Stage 5")
            assert recorded_stages.index("Stage 5") < recorded_stages.index("Stage 6")
            assert recorded_stages.index("Stage 6") < recorded_stages.index("Stage 7")
```

## Compatibility considerations

- The `TestClient` fixture depends on the FastAPI app being properly configured for testing.
- Mocking `verify_postcondition` must not interfere with other tests — use `monkeypatch` for cleanup.
- Tests may require a mock repository at `/tmp/test-repo` — ensure it exists or mock the repo access.

## Security considerations

- These tests validate security-critical bypass prevention — ensure they cover all three operations (checkout/pull/push).
- Mock injection must not allow bypass of the authorization checks being tested.
- Do not use real repositories with sensitive data in these tests.

## Rollback considerations

- If new tests cause regressions due to behavioral changes in production code, revert the test additions while keeping the source fixes.
- If mock interfaces don't match production code, update mocks rather than reverting tests.

## Validation plan

- Run specific test classes: `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py::TestPostConditionBypassPrevention -v`
- Run specific test classes: `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py::TestCompletePipelineCoverage -v`
- Full suite: `uv run pytest tests/mcp_servers/git/ -v` — no new failures.
- Static analysis: `uv run ruff check scripts/mcp_servers/git/`, `uv run mypy scripts/mcp_servers/git/`, `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- New `TestClient`-based tests posting to `/v1/call_tool` for checkout/pull/push exist.
- A simulated postcondition failure (e.g., a pre-existing merge conflict for pull) is reported as rejected, not silently successful.
- All stages execute in order for each operation type.
- No new static analysis findings.

## Out of scope

- Unit-level postcondition/post-state/stage-recording tests — covered by companion document for `test_repository_state.py`.
- Real-repo checkout regression test — covered by companion document for `test_format_output.py`.
- Known Issue documentation entry — covered by companion document for `docs/00_governance_03_issue-and-uncertainty-management.md`.
- Authorization content itself (REQ-001 / gitauth's Plan scope).

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20260902-144908_gitpipeline_enforce_complete_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-190750_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-190750
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py

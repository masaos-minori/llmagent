## Goal

Extend `tests/test_mcp_server_health_status.py` to assert `restart_recommended`, `operator_action_required`, and `liveness` fields in both healthy and degraded responses.

## Scope

- In-Scope:
  - Add field assertions to all existing degraded-state test cases: `data["restart_recommended"] is False` and `data["operator_action_required"] is True`
  - Add field assertions to all existing healthy-state test cases: `data["restart_recommended"] is False`, `data["operator_action_required"] is False`, `data["liveness"] is True`
  - Update the shape-check test `test_health_response_shape_when_healthy` to assert all seven keys are present
  - Update the shape-check test `test_health_response_shape_when_degraded` similarly
- Out-of-Scope:
  - Adding new test scenarios (server types not already tested)
  - Changing how the apps are set up or how `_build_health_deps` is patched

## Assumptions

1. Steps 1 and 2 must be complete before these assertions can pass — the concrete server health endpoints and the base class must return the new fields.
2. The existing tests use `response.json()` to access body fields; the new assertions follow the same pattern.
3. `data["restart_recommended"] is False` uses `is` not `==` because JSON `false` maps to Python `False` singleton.
4. The `test_git_health_returns_503_when_git_not_in_path` test has a conditional branch (`if response.status_code == 503`) — assertions for new fields must also be placed inside the `if` branch.

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_mcp_server_health_status.py`

### Procedure

1. Open `/home/masaos/llmagent/tests/test_mcp_server_health_status.py`.

2. **`test_web_search_health_returns_200_when_healthy`** (lines 18-28):
   Add after the existing assertions:
   ```python
   assert data["liveness"] is True
   assert data["restart_recommended"] is False
   assert data["operator_action_required"] is False
   ```

3. **`test_git_health_returns_503_when_git_not_in_path`** (lines 30-44):
   Inside the `if response.status_code == 503:` branch, add:
   ```python
   assert data["restart_recommended"] is False
   assert data["operator_action_required"] is True
   ```
   Inside the `else:` branch (healthy), add:
   ```python
   assert data["liveness"] is True
   assert data["restart_recommended"] is False
   assert data["operator_action_required"] is False
   ```

4. **`test_cicd_health_returns_503_when_github_token_not_set`** (lines 46-65):
   After `assert "github_token" in data["dependencies"]`, add:
   ```python
   assert data["restart_recommended"] is False
   assert data["operator_action_required"] is True
   ```

5. **`test_health_response_shape_when_healthy`** (lines 67-78):
   Add assertions for all seven keys:
   ```python
   assert "liveness" in data
   assert "restart_recommended" in data
   assert "operator_action_required" in data
   assert data["liveness"] is True
   assert data["restart_recommended"] is False
   assert data["operator_action_required"] is False
   ```

6. **`test_health_response_shape_when_degraded`** (lines 80-101):
   After the existing shape checks, add:
   ```python
   assert "liveness" in data
   assert "restart_recommended" in data
   assert "operator_action_required" in data
   assert data["restart_recommended"] is False
   assert data["operator_action_required"] is True
   ```

7. **`TestFileServerHealth`** — degraded tests (`test_file_read_health_degraded_when_workspace_missing`, `test_file_write_health_degraded_when_workspace_missing`, `test_file_delete_health_degraded_when_workspace_missing`):
   After `assert "filesystem" in data["dependencies"]` (or after `assert data["ready"] is False`), add:
   ```python
   assert data["restart_recommended"] is False
   assert data["operator_action_required"] is True
   ```

8. **`TestFileServerHealth`** — healthy tests (`test_file_read_health_ok_when_workspace_exists`, `test_file_write_health_ok_when_workspace_exists`, `test_file_delete_health_ok_when_workspace_exists`):
   After `assert data["status"] == "ok"` (or after `assert data["ready"] is True`), add:
   ```python
   assert data["liveness"] is True
   assert data["restart_recommended"] is False
   assert data["operator_action_required"] is False
   ```

9. **`TestRagPipelineServerHealth`** — `test_degraded_when_embed_url_not_configured`:
   After `assert "embed_url" in data["dependencies"]`, add:
   ```python
   assert data["restart_recommended"] is False
   assert data["operator_action_required"] is True
   ```

10. **`TestRagPipelineServerHealth`** — `test_ok_when_embed_url_configured`:
    After `assert data["status"] == "ok"`, add:
    ```python
    assert data["liveness"] is True
    assert data["restart_recommended"] is False
    assert data["operator_action_required"] is False
    ```

### Method

- All new assertions use `is True` / `is False` (not `==`) for boolean field checks, consistent with existing assertions such as `assert data["ready"] is True`.
- No test structure changes; only assertion lines are added.
- No new imports are needed.

### Details

- File: `tests/test_mcp_server_health_status.py`
- Existing assertion pattern example (line 27): `assert data["ready"] is True` — match this style.
- `test_file_*_health_degraded_*` tests use `patch("mcp.file.*.server._build_health_deps", return_value={"filesystem": ...})`; the patched `_build_health_deps` controls `deps`, and the health endpoint computes `operator_action_required = not ready` from `deps`. After Step 2, the new field will be `True` in the degraded branch.

## Validation plan

```bash
# Run the extended test file
uv run pytest tests/test_mcp_server_health_status.py -v

# Full test suite
uv run pytest tests/ -x -q

# Lint
uv run ruff check tests/test_mcp_server_health_status.py
```

Expected outcomes:
- All existing tests still pass.
- All new assertions pass (fields are present and have expected values).
- No ruff lint errors.

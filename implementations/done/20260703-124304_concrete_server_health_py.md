## Goal

Add `liveness`, `restart_recommended`, and `operator_action_required` fields to the `/health` route function in each of the nine concrete MCP server files, classifying dependency failures as `operator_action_required=True, restart_recommended=False`.

## Scope

- In-Scope:
  - Update the `health()` route function in each of these files:
    - `scripts/mcp/cicd/server.py` — `github_token` missing
    - `scripts/mcp/git/server.py` — `git` not in PATH
    - `scripts/mcp/github/server.py` — `_GITHUB_TOKEN` not set
    - `scripts/mcp/shell/server.py` — `sh` not in PATH
    - `scripts/mcp/rag_pipeline/server.py` — `embed_url` not configured
    - `scripts/mcp/file/read_server.py` — filesystem missing (uses `_build_health_deps()`)
    - `scripts/mcp/file/write_server.py` — filesystem missing (uses `_build_health_deps()`)
    - `scripts/mcp/file/delete_server.py` — filesystem missing (uses `_build_health_deps()`)
    - `scripts/mcp/mdq/health_check.py` — db_file / db_schema / config failures
  - Also add `liveness=True` to all healthy responses
  - Also update `mcp/web_search/server.py` (always-healthy) to include the new fields for schema consistency
- Out-of-Scope:
  - Changes to `mcp/file/common.py`'s `_build_health_deps()` function
  - Changes to service dispatch, tool listing, or any non-health endpoints
  - Changes to the `MCPServer` base class (covered in Step 1)

## Assumptions

1. All nine concrete server health functions build their response dict manually (confirmed by reading each file); they do not call `super().health()`.
2. The `github/server.py` health endpoint currently returns a plain `dict` (not `JSONResponse`); it will need its return type updated to `JSONResponse` to carry the HTTP status code, or the dict can keep the existing shape and FastAPI will serialize it — but since we need to add fields, we will keep the same pattern (dict return is fine, FastAPI will use 200 by default; the 503 for degraded was handled differently — check current behavior).
3. The `mdq/health_check.py` `_degraded_response()` helper must also be updated to include the new fields.
4. `test_mcp_server_health_status.py` currently does NOT assert the new fields; it will pass without changes after Step 2, but Step 8 will add those assertions. The current tests must not regress.

## Implementation

### Target file

Multiple files (treat as one logical step):
- `/home/masaos/llmagent/scripts/mcp/cicd/server.py`
- `/home/masaos/llmagent/scripts/mcp/git/server.py`
- `/home/masaos/llmagent/scripts/mcp/github/server.py`
- `/home/masaos/llmagent/scripts/mcp/shell/server.py`
- `/home/masaos/llmagent/scripts/mcp/rag_pipeline/server.py`
- `/home/masaos/llmagent/scripts/mcp/file/read_server.py`
- `/home/masaos/llmagent/scripts/mcp/file/write_server.py`
- `/home/masaos/llmagent/scripts/mcp/file/delete_server.py`
- `/home/masaos/llmagent/scripts/mcp/mdq/health_check.py`
- `/home/masaos/llmagent/scripts/mcp/web_search/server.py`

### Procedure

**Pattern to apply for all servers that return `JSONResponse` directly:**

For each degraded response dict, add:
```python
"liveness": True,
"restart_recommended": False,
"operator_action_required": True,
```

For each healthy response dict (where `ready=True`), add:
```python
"liveness": True,
"restart_recommended": False,
"operator_action_required": False,
```

**Step-by-step per file:**

1. `scripts/mcp/cicd/server.py` (lines 102-120, `async def health() -> JSONResponse`):
   - In the `JSONResponse(...)` body dict, add the three fields.
   - When `ready=True`: `liveness=True, restart_recommended=False, operator_action_required=False`.
   - When `ready=False` (github_token missing): `liveness=True, restart_recommended=False, operator_action_required=True`.
   - Since the dict is constructed once using `ready` as the selector, use conditional expressions:
     ```python
     "liveness": True,
     "restart_recommended": False,
     "operator_action_required": not ready,
     ```

2. `scripts/mcp/git/server.py` (lines 85-102, `async def health() -> JSONResponse`):
   - Same pattern: `operator_action_required=not ready`.

3. `scripts/mcp/github/server.py` (lines 89-101, `async def health() -> dict[str, Any]`):
   - This returns a plain `dict`, not `JSONResponse`. The function signature is `-> dict[str, Any]`.
   - Note: this endpoint does NOT set HTTP 503 on degraded — it returns 200 always (FastAPI default). This is a pre-existing inconsistency noted in the affected areas table.
   - Add the three fields using `operator_action_required=not ready`.
   - Do NOT fix the missing HTTP 503 status code in this step (out of scope).

4. `scripts/mcp/shell/server.py` (lines 86-105, `async def health() -> JSONResponse`):
   - Same pattern: `operator_action_required=not ready`.

5. `scripts/mcp/rag_pipeline/server.py` (lines 114-137, `async def health() -> JSONResponse`):
   - Same pattern: `operator_action_required=not ready`.

6. `scripts/mcp/file/read_server.py` (lines 136 area, `async def health() -> JSONResponse`):
   - Uses `deps = _build_health_deps()`. Add the three fields:
     ```python
     "liveness": True,
     "restart_recommended": False,
     "operator_action_required": not ready,
     ```

7. `scripts/mcp/file/write_server.py` — same as read_server.

8. `scripts/mcp/file/delete_server.py` — same as read_server.

9. `scripts/mcp/mdq/health_check.py`:
   - Update `_degraded_response()` helper (lines 22-33) to include:
     ```python
     "liveness": True,
     "restart_recommended": False,
     "operator_action_required": True,
     ```
   - Update the final healthy `JSONResponse` (end of `check_health()`, lines 128-135) to include:
     ```python
     "liveness": True,
     "restart_recommended": False,
     "operator_action_required": False,
     ```

10. `scripts/mcp/web_search/server.py` (lines 61-74, `async def health() -> JSONResponse`):
    - Always healthy; add: `liveness=True, restart_recommended=False, operator_action_required=False`.

### Method

- Pure dict update; no new imports needed in any file.
- Use `"operator_action_required": not ready` as a concise expression to avoid duplicating the dict.
- For `mdq/health_check.py`, the `_degraded_response()` helper is called multiple times from multiple early-return branches; updating it once propagates to all degraded paths automatically.
- The `github/server.py` health endpoint returns a plain dict (FastAPI auto-serializes). Leave the return type as `dict[str, Any]` unchanged.

### Details

- `cicd/server.py` health function: `deps["github_token"] = "not_set"` when `os.environ.get("GITHUB_TOKEN", "")` is empty.
- `git/server.py` health function: `deps["git"] = "git not found in PATH"` when `shutil.which("git") is None`.
- `github/server.py` health function: `deps["github_token"] = "not_set"` when `not _GITHUB_TOKEN` (module-level constant from `service_init`).
- `shell/server.py` health function: `deps["shell"] = "sh not found in PATH"` when `shutil.which("sh") is None`.
- `rag_pipeline/server.py` health function: `deps["embed_url"] = "not configured"` when embed_url is missing.
- `file/*/server.py` health functions: use `_build_health_deps()` from `mcp.file.common` which sets `deps["filesystem"]` when `/workspace` stat fails.
- `mdq/health_check.py`: `_degraded_response()` is called for `db_file`, `db_schema`, `fts5`, and `config` failures.

## Validation plan

```bash
# Run existing health status tests — must not regress
uv run pytest tests/test_mcp_server_health_status.py -v

# Run mdq health tests
uv run pytest tests/test_mdq_health_endpoint.py tests/test_mdq_health_stale.py -v

# Lint all modified files
uv run ruff check scripts/mcp/cicd/server.py scripts/mcp/git/server.py \
  scripts/mcp/github/server.py scripts/mcp/shell/server.py \
  scripts/mcp/rag_pipeline/server.py scripts/mcp/file/read_server.py \
  scripts/mcp/file/write_server.py scripts/mcp/file/delete_server.py \
  scripts/mcp/mdq/health_check.py scripts/mcp/web_search/server.py

# Type check
uv run mypy scripts/mcp/cicd/server.py scripts/mcp/git/server.py \
  scripts/mcp/github/server.py scripts/mcp/shell/server.py \
  scripts/mcp/rag_pipeline/server.py scripts/mcp/mdq/health_check.py
```

Expected outcomes:
- All existing `TestHealthHTTPStatusCodes` and `TestFileServerHealth` tests pass.
- All mdq health tests pass.
- No new ruff or mypy errors.

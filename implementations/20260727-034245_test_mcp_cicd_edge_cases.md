## Goal

Add guard tests for MCP servers layer dead code and error handling to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- MCP-1: Verify dead code status of `_ensure_error_tracking` / `_record_tool_error` — delete if confirmed dead
- MCP-2: Add OSError capture around stat() call in read_single_file
- MCP-3: Create tests for non-2xx fail-fast and max_bytes truncation on job log retrieval
- MCP-4: Verify important directory guards exist for recursive deletion

**Out-of-Scope:**
- Changes beyond the four specific gaps listed above

## Assumptions

1. The MCP servers layer needs characterization tests due to multiple coverage gaps
2. Dead code should be deleted rather than tested if confirmed unused
3. Tests should verify current behavior, not expected future behavior

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for MCP edge cases | Search for `mcp_servers` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/mcp_servers/server.py` — possibly delete dead code
  - `scripts/mcp_servers/file/read_business.py` — add OSError capture
  - New file: `tests/test_mcp_cicd_edge_cases.py` — job log edge case tests
  - `scripts/mcp_servers/file/delete_service.py` — verify/add directory guards

- **Blast Radius:**
  - Low churn — minor edits + new test file
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the MCP servers layer:
```python
# Key behaviors:
# - _ensure_error_tracking / _record_tool_error: potentially dead code in server.py
# - read_single_file: stat() call without OSError handling
# - Job log retrieval: needs non-2xx fail-fast and max_bytes truncation tests
# - Recursive deletion: needs directory guards verification
```

The implementation will address all four gaps: dead code removal, OSError capture, edge case tests, and directory guard verification.

## Implementation

### Target files
- `scripts/mcp_servers/server.py`
- `scripts/mcp_servers/file/read_business.py`
- New file: `tests/test_mcp_cicd_edge_cases.py`
- `scripts/mcp_servers/file/delete_service.py`

### Procedure
1. Phase 1: Search for callers of `_ensure_error_tracking` / `_record_tool_error`
2. Phase 2: Address each gap (MCP-1 through MCP-4)
3. Phase 3: Verify with lint and tests

### Method
Address each gap sequentially, starting with dead code verification.

### Details
1. **MCP-1**: Search for callers of `_ensure_error_tracking` and `_record_tool_error`. If none found, delete both functions from `server.py`.

2. **MCP-2**: In `read_business.py`, wrap stat() call:
   ```python
   # Before:
   stat_result = os.stat(path)
   
   # After:
   try:
       stat_result = os.stat(path)
   except OSError as e:
       raise FileNotFoundError(f"Cannot access {path}: {e}") from e
   ```

3. **MCP-3**: Create `tests/test_mcp_cicd_edge_cases.py`:
   ```python
   """Edge case tests for MCP CICD job log retrieval."""
   
   @pytest.mark.asyncio
   async def test_non_2xx_fail_fast():
       ...
   
   @pytest.mark.asyncio
   async def test_max_bytes_truncation():
       ...
   ```

4. **MCP-4**: Verify directory guards in `delete_service.py`. Add if missing.

## Compatibility considerations

N/A — changes are defensive only

## Security considerations

These changes improve security by removing dead code and adding error handling.

## Rollback considerations

- Simple revert: restore original files from git history

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/server.py` | Dead code removal verified | Manual inspection | No callers remain |
| `scripts/mcp_servers/file/read_business.py` | OSError captured | `uv run pytest -k "read" -v` | Test passes |
| `tests/test_mcp_cicd_edge_cases.py` | Edge case tests pass | `uv run pytest -k "cicd" -v` | All tests pass |
| `scripts/mcp_servers/file/delete_service.py` | Directory guards verified | Manual inspection | Guards present |

## Out of scope

- Changes beyond the four specific gaps listed above

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-130801_require.md
- Source plan: plans/20260726-172856_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/mcp_servers/server.py, scripts/mcp_servers/file/read_business.py, scripts/mcp_servers/cicd/service_github_actions_job.py, scripts/mcp_servers/file/delete_service.py

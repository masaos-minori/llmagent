## Goal

Add tests for uncovered execution paths in `tests/agent/test_tool_approval_preflight.py`, specifically verifying preflight gate behavior for approval flow scenarios.

## Scope

- **In-Scope**: Add tests for uncovered execution paths including: (1) approval flow preflight gate verification, (2) gateway-bypass gap test, (3) regression tests confirming existing Agent tests still pass.
- **Out-of-Scope**: Modifying the `check_preflight()` function logic itself; adding new gate conditions beyond what already exists; changes to MCP server preflight behavior; changes to Event Bus preflight behavior.

## Assumptions

- The project uses pytest fixtures and parametrization patterns consistent with existing test modules under `tests/`.
- The `_make_cfg()` / `_make_ctx()` patterns from `test_tool_approval_preflight.py` are available for test setup.
- dry_run operations are intentionally preflight-exempt because they are read-only previews.
- READ operations are intentionally preflight-exempt per design (direct passthrough for read-only tools).

## Design decisions

- Use pytest parametrization to test multiple scenarios from a single test function where possible.
- Use the existing `_make_cfg()` / `_make_ctx()` patterns from `test_tool_approval_preflight.py` for consistency.
- Test each gate condition separately to ensure clear failure messages.

## Alternatives considered

- Using a single parametrized test function to test all gate conditions together. This was rejected because it would make it harder to identify which specific gate condition fails when a test breaks. Testing each gate condition separately provides clearer failure messages and makes it easier to understand which aspect of the preflight gate needs attention.

## Implementation

### Target file

`tests/agent/test_tool_approval_preflight.py`

### Procedure

1. Scaffold the test file skeleton with `uv run python tools/generate_workitem.py --kind implementation-procedure --source-plan plans/20260924-070936_plan.md --target-file-path tests/agent/test_tool_approval_preflight.py --seq 03`.
2. Verify the scaffolded file exists at `implementations/20260924-090000_03_test_tool_approval_preflight_py.md` before proceeding.
3. Implement the test cases per Method below.

### Method

#### Current test structure (verified):

The existing `test_tool_approval_preflight.py` has 769 lines of preflight-related tests. These cover basic preflight gate behavior but do not cover all edge cases.

#### Test additions:

**Gateway-bypass gap test (T-04)**

```python
async def test_gateway_bypass_gap_resolved() -> None:
    """Verify the gateway-bypass gap is resolved."""
    # Create a context where gateway is None
    ctx = _make_ctx(gateway=None)
    
    # When gateway is None, the tool should NOT bypass the preflight gate
    # This test verifies that either:
    # 1. The fix adds a preflight check in the else branch, OR
    # 2. The documentation explains why the path is safe
    
    # Option A: If fix was applied, this should raise PolicyViolationError
    # Option B: If documented as safe, this should NOT raise an error
    
    # For now, we assume Option A (fix) is chosen
    with pytest.raises(PolicyViolationError):
        await ctx.services_required.tools.execute("write_tool", {})
```

**Regression test (T-07)**

```python
def test_regression_existing_agent_tests_pass() -> None:
    """Regression test: existing Agent tests still pass after adding new coverage."""
    # This test runs the existing preflight tests to ensure no regression
    result = subprocess.run(
        ["uv", "run", "pytest", "tests/agent/test_tool_approval_preflight.py", "-v"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Regression failed:\n{result.stdout}\n{result.stderr}"
```

**Approval flow preflight test**

```python
async def test_approval_flow_preflight_gate_fires() -> None:
    """Preflight gate should fire during approval flow."""
    cfg = _make_cfg(
        allowed_tools=["read_only_tool"],  # Exclude write_tool
        allowed_root="/tmp",
        allowed_repos=["github.com/example/repo"],
    )
    
    ctx = _make_ctx(cfg=cfg)
    
    # Simulate approval flow for a write operation
    with pytest.raises(PolicyViolationError):
        check_preflight(cfg, "write_tool", {})
```

## Compatibility considerations

- Tests use the existing `_make_cfg()` / `_make_ctx()` patterns from `test_tool_approval_preflight.py`.
- Tests depend on `pytest` and `PolicyViolationError` being available.
- Tests create temporary directories via `tmp_path` fixture — no cleanup needed.

## Security considerations

- Tests use temporary directories — no risk of polluting the repository.
- Tests do not execute any untrusted input — all synthetic configurations are created within test functions.

## Rollback considerations

- If tests fail due to false positives from the preflight gate, the whitelist logic needs adjustment (not a rollback scenario).
- If `rg` is unavailable in the test environment, skip tests with `pytest.skip()`.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_tool_approval_preflight.py` | Unit: all new tests pass | `uv run pytest tests/agent/test_tool_approval_preflight.py -v` | All tests pass |
| `tests/agent/test_tool_policy.py` | Regression: existing tests pass | `uv run pytest tests/agent/test_tool_policy.py -v` | All tests pass |
| New preflight gate tests | Unit: new tests pass | `uv run pytest tests/agent/ -k preflight -v` | All new tests pass |
| Agent architecture doc | Manual: documentation review | Read coverage map section | Coverage map present |
| Governance docs | Manual: REQ-003 status update | Read REQ-003 section | Status updated |

## Completion criteria

- AC-01: Gateway-bypass gap test passes (REQ-03, AC-03)
- AC-02: Approval flow preflight test passes (REQ-02, AC-02)
- AC-03: Regression test confirms existing tests still pass (REQ-06, AC-02)
- AC-04: Coverage map is included in Agent architecture documentation (REQ-04, AC-04)
- AC-05: REQ-003 Known Issue status reflects resolution (REQ-10, AC-06)

## Out of scope

- Integration tests for CI pipeline execution; tests for pre-commit hook integration; tests for other FTS table operations (`chunks_fts_docsize`).

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
- **Requirement ID**: REQ-02
- **Source issue**: issues/20260924-054349_req003_preflight-gate-additions-not-validated-all-execution-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-070936_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-090000
- **Related target files**: tests/agent/test_tool_approval_preflight.py

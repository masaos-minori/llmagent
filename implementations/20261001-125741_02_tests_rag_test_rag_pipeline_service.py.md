## Goal

Add a marker-lock guard in `tests/rag/test_rag_pipeline_service.py` that asserts `ResultSource.FALLBACK` / `in_process_fallback` arises only via the sanctioned RAG augment path (`call_rag_service()` → None → in-process RAG), resolving UNK-01.

## Scope

- **In-Scope**: Add a new test (or modify existing test) in `tests/rag/test_rag_pipeline_service.py` that verifies `ResultSource.FALLBACK` is never set outside the sanctioned augment path.
- **Out-of-Scope**: Changing any fallback behavior itself; modifying other test files beyond running existing tests; adding new source files.

## Assumptions

- The sanctioned augment path is: `call_rag_service()` → `HttpAugment.run()` → `result.result is None` → `result_source = ResultSource.FALLBACK` in `augment.py` line 87.
- `in_process_fallback` in `http_augment.py` is the internal mechanism name for the same concept (HTTP error → local RAG).
- The existing tests (`test_401_no_fallback`, `test_403_no_fallback`, `test_json_parse_error_does_not_call_set_fallback_reason`) already cover the negative case (non-transport errors do NOT trigger fallback).
- A marker-lock guard should prevent future regressions where `ResultSource.FALLBACK` could be set by an unauthorized code path.

## Design decisions

- Add a new test method `test_fallback_marker_only_via_sanctioned_path` that uses monkeypatching to intercept any attempt to set `ResultSource.FALLBACK` outside the sanctioned augment path.
- The test patches `scripts/rag/augment.py`'s `ResultSource.FALLBACK` assignment site and verifies it only occurs within the expected call chain.
- Alternative approach considered: patching `_set_fallback_reason` callback to track all invocations and verifying they only come from the sanctioned path. This was chosen instead because it directly validates the observable outcome (the marker being set) rather than relying on callback tracking.

## Alternatives considered

- **Callback tracking**: Patch `_set_fallback_reason` and verify it's only called from the sanctioned path. Less direct because it tracks the symptom (callback invocation) rather than the root cause (marker assignment).
- **Monkeypatching `ResultSource` enum**: Not feasible because `ResultSource` is an enum; cannot override its member assignments.
- **Integration-level test**: Run the full pipeline with a mock RAG service and verify the marker is set correctly. Too broad; the unit-level marker-lock guard is more precise.

## Implementation

### Target file

`tests/rag/test_rag_pipeline_service.py`

### Procedure

1. Identify the exact location where `ResultSource.FALLBACK` is assigned in the production code (`scripts/rag/augment.py` line 87).
2. Create a new test method that monkeypatches the assignment site or the surrounding logic to verify it only occurs within the sanctioned augment path.
3. Ensure the test covers both the positive case (in-process RAG fallback IS triggered for transport errors like HTTP 5xx and connection timeouts) and the negative case (in-process RAG fallback is NOT triggered for non-transport errors such as HTTP 401/403 authentication errors and JSON parse errors). Note: for 401/403, `ResultSource.FALLBACK` IS set via `augment.py` line 87 (because `result.result is None`), but in-process RAG does NOT execute because `http_augment.py` line 141-148 checks `status_code in (401, 403)` before calling `_set_fallback_reason`. The test must distinguish between these two scenarios.
4. Run existing tests to confirm no regression.

### Method

#### Current state

`scripts/rag/augment.py` line 87:
```python
if result.result is not None:
    result_source = ResultSource.REMOTE
else:
    result_source = ResultSource.FALLBACK
```

This is the ONLY place in the repository where `ResultSource.FALLBACK` is assigned (confirmed by grep).

#### Required changes

Add a new test method in `tests/rag/test_rag_pipeline_service.py`:

```python
class TestFallbackMarkerLockGuard:
    """Verify ResultSource.FALLBACK/in_process_fallback arises only via sanctioned augment path."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_fallback_marker_only_via_sanctioned_path(self) -> None:
        """ResultSource.FALLBACK must only be set through call_rag_service() -> HttpAugment.run()."""
        # Arrange: simulate an HTTP error that triggers fallback
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        
        # Track whether fallback marker was set
        fallback_marker_set = False
        
        # Monkeypatch the assignment site to detect unauthorized access
        original_augment_module = importlib.import_module("scripts.rag.augment")
        original_result_source = original_augment_module.ResultSource.FALLBACK
        
        def patched_fallback_assignment(value):
            nonlocal fallback_marker_set
            # Verify we're in the sanctioned path by checking the call stack
            import traceback
            stack = traceback.extract_stack()
            # Check that the caller is within scripts/rag/augment.py
            callers = [frame.filename for frame in stack]
            sanctioned_path_found = any(
                "scripts/rag/augment.py" in f for f in callers
            )
            assert sanctioned_path_found, (
                f"ResultSource.FALLBACK assignment detected outside sanctioned path. "
                f"Callers: {callers}"
            )
            fallback_marker_set = True
            return value
        
        # Apply patch
        with unittest.mock.patch.object(
            original_augment_module.ResultSource,
            "__new__",
            side_effect=lambda cls, value, *args, **kwargs: (
                patched_fallback_assignment(value) if value == "FALLBACK" else original_result_source.__class__.__new__(cls, value, *args, **kwargs)
            ),
        ):
            async with httpx.AsyncClient() as client:
                result, status, latency = await call_rag_service(
                    client,
                    RAG_URL,
                    "q",
                    "",
                    set_fetch_result=_noop_fetch,
                    set_fallback_reason=_noop_fallback_reason,
                )
        
        # Assert: fallback marker was set (positive case)
        assert fallback_marker_set, "ResultSource.FALLBACK was not set despite HTTP error"
        assert result == ""  # Fallback returns empty string
        assert status == 500  # Original HTTP error status
```

Alternative simpler approach using callback tracking:

```python
class TestFallbackMarkerLockGuard:
    """Verify ResultSource.FALLBACK/in_process_fallback arises only via sanctioned augment path."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_fallback_marker_only_via_sanctioned_path(self) -> None:
        """ResultSource.FALLBACK must only be set through call_rag_service() -> HttpAugment.run()."""
        # Arrange: simulate an HTTP error that triggers fallback
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        
        # Track fallback reason callbacks — these are only invoked from the sanctioned path
        fallback_reasons: list[str] = []
        
        async with httpx.AsyncClient() as client:
            result, status, latency = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
                set_fallback_reason=fallback_reasons.append,
            )
        
        # Assert: fallback was triggered (positive case)
        assert len(fallback_reasons) > 0, (
            "Expected fallback to be triggered for HTTP 500, but no fallback reason was recorded. "
            "This may indicate ResultSource.FALLBACK is not being set correctly."
        )
        assert result == ""  # Fallback returns empty string
        assert status == 500  # Original HTTP error status
        
        # Additional assertion: verify the fallback reason format matches expected pattern
        for reason in fallback_reasons:
            assert reason.startswith("http_max_retries:"), (
                f"Unexpected fallback reason format: {reason}. "
                "Expected format: 'http_max_retries:<count>'"
            )
        
        # NOTE: For 401/403 auth errors, ResultSource.FALLBACK IS set via augment.py line 87
        # (because result.result is None), but in-process RAG does NOT execute because
        # http_augment.py line 141-148 checks status_code in (401, 403) before calling
        # _set_fallback_reason. This test verifies the positive case (transport error →
        # in-process RAG); the negative case (non-transport error → no in-process RAG) is
        # covered by existing tests test_401_no_fallback / test_403_no_fallback.

    @pytest.mark.asyncio
    @respx.mock
    async def test_non_transport_errors_do_not_trigger_fallback(self) -> None:
        """Non-transport errors (4xx auth errors, JSON parse errors) must NOT trigger fallback."""
        # Test with HTTP 401
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        
        fallback_reasons: list[str] = []
        
        async with httpx.AsyncClient() as client:
            result, status, latency = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
                set_fallback_reason=fallback_reasons.append,
            )
        
        # Assert: NO fallback was triggered for 401
        assert len(fallback_reasons) == 0, (
            "Expected NO fallback for HTTP 401, but got fallback reasons: "
            f"{fallback_reasons}. This indicates ResultSource.FALLBACK is incorrectly set."
        )
        assert result == ""  # Empty result for failed request
        assert status == 401  # Original HTTP error status
```

### Details

**Step 1: Verify current state of ResultSource.FALLBACK assignment**

Run `rg 'ResultSource\\.FALLBACK' scripts/` to confirm there is exactly one assignment site (line 87 of `augment.py`). Current evidence shows this is the only occurrence.

**Step 2: Implement the marker-lock guard test**

Add the new test class `TestFallbackMarkerLockGuard` to `tests/rag/test_rag_pipeline_service.py`. Two approaches available:
- Primary: Callback tracking approach (simpler, directly validates the observable outcome)
- Alternative: Stack-trace inspection approach (more rigorous but more complex)

**Step 3: Run existing tests**

Run `uv run pytest tests/rag/test_rag_pipeline_service.py -x -q` to confirm no regression.

**Step 4: Run the new test**

The new test should pass immediately after implementation, confirming the marker-lock guard works.

## Compatibility considerations

- No behavioral change. Only adding a new test.
- The callback tracking approach is backward compatible because `_set_fallback_reason` is already used by existing tests.
- The stack-trace inspection approach requires Python 3.11+ for `traceback.extract_stack()` reliability.

## Security considerations

- No security implications. Adding a test that validates correct behavior.
- The marker-lock guard prevents future regressions where `ResultSource.FALLBACK` could be set by an unauthorized code path, which could lead to incorrect fallback decisions.

## Rollback considerations

- To rollback, remove the new test class from git history: `git checkout HEAD~1 -- tests/rag/test_rag_pipeline_service.py`.
- The rollback removes the marker-lock guard without affecting other tests.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/rag/test_rag_pipeline_service.py` | New marker-lock guard test | `uv run pytest tests/rag/test_rag_pipeline_service.py::TestFallbackMarkerLockGuard -x -q` | All new tests pass |
| `tests/rag/test_rag_pipeline_service.py` | Regression (existing tests) | `uv run pytest tests/rag/test_rag_pipeline_service.py -x -q` | All existing tests pass |
| `scripts/rag/augment.py` | Verify single FALLBACK assignment | `rg 'ResultSource\\.FALLBACK' scripts/` | Exactly 1 match at line 87 |

## Completion criteria

- AC-001: A new test class `TestFallbackMarkerLockGuard` exists in `tests/rag/test_rag_pipeline_service.py`.
- AC-002: The test verifies that in-process RAG fallback is only triggered for transport errors (not non-transport errors like 401/403 auth errors). Note: `ResultSource.FALLBACK` IS set for 401/403 via augment.py line 87; the distinction is whether in-process RAG executes, which is controlled by http_augment.py line 141-148.
- AC-003: The test includes both positive (HTTP 500 → in-process RAG executed) and negative (HTTP 401 → no in-process RAG execution) cases.
- AC-004: All existing tests in `test_rag_pipeline_service.py` continue to pass.
- AC-005: `rg 'ResultSource\\.FALLBACK' scripts/` confirms exactly one assignment site remains unchanged.

## Out of scope

- Changing how approvals are requested or resolved during a live session.
- Altering the approval table schema.
- Unifying the two validation implementations into one.
- Re-wiring `_fetch_server_tools()` as the live path.
- Modifying source files beyond running existing tests.

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
| — | — | N/A: no blockers | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: N/A: the Plan's own Traceability section carries `{path}` placeholder (not filled)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260930-212727_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-132025
- **Related target files**: tests/rag/test_rag_pipeline_service.py

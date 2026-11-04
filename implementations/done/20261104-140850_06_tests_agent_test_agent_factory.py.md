## Goal
- Rewrite the characterization test that pins `None` for a router start after `shutdown_all()`, so it asserts the new contract: the start entry raises `StartSuppressedError` (new) and never reaches the subprocess layer (`REQ-002`: suppression is a typed signal; `REQ-006`: characterization tests follow the new contract).

## Scope
**Release unit**: startup-start-contract

- One test in `TestRouterPostShutdownGuards` of `tests/agent/test_agent_factory.py`, plus one name added to the file's existing import from `agent.lifecycle_router`.

## Assumptions
- `test_start_http_subprocess_returns_none_after_shutdown_all` currently calls `shutdown_all()`, awaits `router.start_http_subprocess("srv", cfg)`, asserts `result is None`, and asserts the subprocess layer's `start` was not called (checked in Step 3a).
- `StartSuppressedError` (new) is declared by the sibling procedure for `scripts/agent/lifecycle_router.py` (earlier `seq`).
- The file already imports `pytest`, `AsyncMock`, `MagicMock`, `patch`, and uses `_make_router()` for the router and its subprocess manager.
- The Plan's table names this test file in two rows (the router row and its own row), so it is not a companion and keeps its own procedure.
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it.

## Design decisions
- Replace the test in place with `test_start_http_subprocess_raises_after_shutdown_all` (new): the same setup, `pytest.raises(StartSuppressedError)` instead of the `None` assertion, and the same assertion that the subprocess layer was not called.

## Alternatives considered
N/A: one in-place rewrite fixed by the Plan's characterization-test requirement.

## Implementation
### Target file
`tests/agent/test_agent_factory.py`

### Procedure
1. Add `StartSuppressedError` (new) to the existing `from agent.lifecycle_router import (...)` block and run `uv run ruff check --fix` on the file so the names stay ordered.
2. Replace the one test method below.

### Method
Before:

```python
    @pytest.mark.asyncio
    async def test_start_http_subprocess_returns_none_after_shutdown_all(self) -> None:
        router, subprocess_mgr = _make_router()
        await router.shutdown_all()
        cfg = router._server_configs["srv"]

        result = await router.start_http_subprocess("srv", cfg)

        assert result is None
        subprocess_mgr._http_mgr.start.assert_not_called()
```

After:

```python
    @pytest.mark.asyncio
    async def test_start_http_subprocess_raises_after_shutdown_all(self) -> None:
        router, subprocess_mgr = _make_router()
        await router.shutdown_all()
        cfg = router._server_configs["srv"]

        with pytest.raises(StartSuppressedError):
            await router.start_http_subprocess("srv", cfg)

        subprocess_mgr._http_mgr.start.assert_not_called()
```

### Details
- Keep the class docstring and the neighbouring `shutdown_idle` test unchanged.
- The test method name is under the 88-character limit with the signature; keep the `-> None` annotation.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: the subprocess layer is faked; no credential, network, or process.

## Rollback considerations
Revert the commit; this file is part of the release unit, so reverting only it leaves the old test asserting `None` against the new router behavior.

## Validation plan
- `uv run pytest tests/agent/test_agent_factory.py -q` passes in full (collected at least the file's existing tests).
- `uv run ruff format --check tests/agent/test_agent_factory.py`, `uv run ruff check tests/agent/test_agent_factory.py`, and `uv run python tools/check_mock_patch_targets.py` report no findings.

## Completion criteria
- The old `None` assertion is gone; the new test asserts the typed raise and that the subprocess layer was not called (`AC-3`).
- The whole file passes.

## Out of Scope
- The router, starter, and protocol code, and the other test files (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the test and update the import as described in Implementation > Procedure/Method | Done | 20261104 | Added `StartSuppressedError` to the import; rewrote the post-shutdown start test to assert the typed raise. |
| 2 | Run the whole file and confirm it passes | Done | 20261104 | Whole file passes. |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Validation plan | Done | 20261104 | ruff format/check + check_mock_patch_targets clean; full suite 11467 passed. |

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
- **Requirement ID**: `REQ-002` (suppression is a typed signal), `REQ-006` (characterization test follows the new contract)
- **Source issue**: `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095204_startretry001_startup-retry-blocked-cooldown.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-140850
- **Related target files**: `tests/agent/test_agent_factory.py`

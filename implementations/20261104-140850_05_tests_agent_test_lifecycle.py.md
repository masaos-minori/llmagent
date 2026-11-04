## Goal
- Rewrite the characterization test that pins `None` for a start inside the cooldown, so it asserts the new contract: the router's start entry ignores the cooldown, while `ensure_ready` and `restart` still honor it (`REQ-004`: runtime cooldown unchanged; `REQ-006`: characterization tests follow the new contract).

## Scope
**Release unit**: startup-start-contract

- One test in `TestCooldownCharacterization` of `tests/agent/test_lifecycle.py`. The other cooldown tests (`test_ensure_ready_raises_cooldown_error`, `test_restart_skips_when_in_cooldown`, and the `_in_cooldown` tests) stay unchanged.

## Assumptions
- `test_start_http_subprocess_returns_none_in_cooldown` currently pre-seeds `_failed_starts["s"]` and asserts `result is None`; it is the only test of the file that relies on the cooldown veto of the start entry (checked in Step 3a).
- After the router change (sibling procedure, earlier `seq`) the start entry runs `_run_lifecycle_transition`, so a successful start clears the failure entry.
- The file already imports `time`, `AsyncMock`, `MagicMock`, `pytest`, and `_ServerLifecycleRouter`, and has the helper `_http_subprocess_cfg` and the class helper `_mgr()`.
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it.

## Design decisions
- Replace the test in place with `test_start_http_subprocess_ignores_cooldown` (new): seed the cooldown, replace `mgr._subprocess_mgr.start_http_subprocess` with an `AsyncMock` that returns a fake process, call the router's start entry, and assert the call reached the subprocess layer and returned the process.
- Assert the observable outcome (result, call, cleared failure entry) and keep the neighbouring tests as the proof that the runtime paths still refuse inside the cooldown.

## Alternatives considered
N/A: a single in-place rewrite fixed by the Plan's characterization-test requirement.

## Implementation
### Target file
`tests/agent/test_lifecycle.py`

### Procedure
In `TestCooldownCharacterization`, replace the one test method below with the new test; leave every other method and import as they are.

### Method
Before:

```python
    @pytest.mark.asyncio
    async def test_start_http_subprocess_returns_none_in_cooldown(self) -> None:
        mgr = self._mgr()
        mgr._failed_starts["s"] = time.monotonic()

        result = await mgr.start_http_subprocess("s", _http_subprocess_cfg())

        assert result is None
```

After (the shape; names `proc` and `start` are local):

```python
    @pytest.mark.asyncio
    async def test_start_http_subprocess_ignores_cooldown(self) -> None:
        mgr = self._mgr()
        mgr._failed_starts["s"] = time.monotonic()
        proc = MagicMock()
        start = AsyncMock(return_value=proc)
        mgr._subprocess_mgr.start_http_subprocess = start

        result = await mgr.start_http_subprocess("s", _http_subprocess_cfg())

        assert result is proc
        start.assert_awaited_once()
        assert "s" not in mgr._failed_starts
```

### Details
- Do not touch `test_ensure_ready_raises_cooldown_error` or `test_restart_skips_when_in_cooldown`; they prove `AC-4`.
- Run the whole file, not only the class, to confirm no other case depended on the cooldown veto (the Plan's Risks).

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no credential, network, or process; the subprocess layer is faked.

## Rollback considerations
Revert the commit; this file is part of the release unit, so reverting only it leaves the old test asserting `None` against the new router behavior.

## Validation plan
- `uv run pytest tests/agent/test_lifecycle.py -q` passes in full (collected at least the file's existing tests).
- `uv run ruff format --check tests/agent/test_lifecycle.py`, `uv run ruff check tests/agent/test_lifecycle.py`, and `uv run python tools/check_mock_patch_targets.py` report no findings.

## Completion criteria
- The old `None` assertion is gone; the new test asserts that the start entry ignores the cooldown (`AC-4`).
- `ensure_ready` and `restart` cooldown tests pass unchanged, and the whole file passes.

## Out of Scope
- The router, starter, and protocol code, and the other test files (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the test as described in Implementation > Procedure/Method | Pending | — | — | |
| 2 | Run the whole file and confirm the neighbouring cooldown tests pass unchanged | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (runtime cooldown unchanged), `REQ-006` (characterization test follows the new contract)
- **Source issue**: `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095204_startretry001_startup-retry-blocked-cooldown.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-140850
- **Related target files**: `tests/agent/test_lifecycle.py`

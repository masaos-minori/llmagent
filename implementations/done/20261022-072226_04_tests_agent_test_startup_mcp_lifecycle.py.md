## Goal

Add two focused tests to `TestStartupOrchestratorStartServers` in
`tests/agent/test_startup_mcp_lifecycle.py`:

- **T-001** (`REQ-002`): a `StartupInterrupted` raised from a mocked subprocess start
  propagates out of `start_servers()` WITHOUT invoking the retry helper.
- **T-002** (`REQ-005`): a genuine `RuntimeError` from `_start_http_subprocess_once()` still
  triggers exactly one retry (guards against accidental `RuntimeError` removal from the
  first-attempt tuple).

## Scope

- **In-Scope**:
  - Append `test_startup_interrupted_propagates_without_retry` (new) (T-001) and
    `test_genuine_runtime_error_still_retries` (new) (T-002) to
    `TestStartupOrchestratorStartServers` in `tests/agent/test_startup_mcp_lifecycle.py`.
- **Out-of-Scope**:
  - Any change to `scripts/agent/startup_mcp_starter.py` (the guard is a separate
    procedure) or `scripts/agent/startup.py`.

## Assumptions

- **ASM-001**: The sibling `startup_mcp_starter.py` procedure adds an
  `except StartupInterrupted: raise` guard before the first-attempt tuple while keeping
  `RuntimeError` in it, so T-001 (no retry) and T-002 (one retry) are both satisfiable.
- **ASM-002**: `start_servers()` reads `ctx.cfg.mcp.mcp_servers.items()`; `_make_startup()`
  supplies a real dict, so the loop iterates the single configured server.

## Design decisions

- T-001 patches `retry_once_with_delay` (in `agent.startup_mcp_starter`) with an
  `AsyncMock` and asserts `assert_not_awaited()`, directly proving the guard short-circuits
  before the retry helper.
- T-002 patches `retry_once_with_delay` with an `AsyncMock` returning a fake proc and
  asserts `assert_awaited_once()`, directly proving a `RuntimeError` still routes to the
  retry helper.

## Alternatives considered

- Relying on the existing `test_retry_success_appends_to_spawned_subprocesses` for T-002:
  sufficient but not explicit about the retry-helper call; the plan wants a dedicated
  guard test.

## Implementation

### Target file

`tests/agent/test_startup_mcp_lifecycle.py`

### Procedure

1. Append the two methods below to `class TestStartupOrchestratorStartServers` (after
   `test_shutdown_event_passed_but_never_set_is_no_op`, before the
   `# ── StartupOrchestrator._verify_mcp_health` section marker).

### Method

Both tests use `_make_startup({"web": cfg})` (real dict, `shutdown_event=None`) and patch
`_start_http_subprocess_once` on the orchestrator's internal starter
(`startup._mcp_starter._start_http_subprocess_once`), since `start_servers()` calls it via
`self`. `retry_once_with_delay` is patched via `patch("agent.startup_mcp_starter
.retry_once_with_delay", ...)`.

```python
    @pytest.mark.asyncio
    async def test_startup_interrupted_propagates_without_retry(self) -> None:
        """REQ-002/T-001: a StartupInterrupted raised from a mocked subprocess start
        propagates out of start_servers() without invoking the retry helper."""
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )
        startup._mcp_starter._start_http_subprocess_once = AsyncMock(
            side_effect=StartupInterrupted("shutdown requested")
        )

        with patch(
            "agent.startup_mcp_starter.retry_once_with_delay", new=AsyncMock()
        ) as retry_mock:
            with pytest.raises(StartupInterrupted, match="shutdown requested"):
                await startup._start_servers()

        retry_mock.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_genuine_runtime_error_still_retries(self) -> None:
        """REQ-005/T-002: a genuine RuntimeError from _start_http_subprocess_once()
        still triggers exactly one retry via the retry helper."""
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )
        retried_proc = MagicMock(spec=subprocess.Popen)
        startup._mcp_starter._start_http_subprocess_once = AsyncMock(
            side_effect=[RuntimeError("port busy"), retried_proc]
        )

        with patch(
            "agent.startup_mcp_starter.retry_once_with_delay",
            new=AsyncMock(return_value=retried_proc),
        ) as retry_mock:
            result = await startup._start_servers()

        retry_mock.assert_awaited_once()
        assert result == [retried_proc]
```

## Compatibility considerations

These tests exercise `McpServerStarter.start_servers()` through `StartupOrchestrator._start_servers()`.
They require the sibling `startup_mcp_starter.py` guard (T-001) and the retained
`RuntimeError` in the tuple (T-002); both are provided by that procedure.

## Security considerations

N/A.

## Rollback considerations

Revert the two appended methods — a single logical commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_startup_mcp_lifecycle.py` | Behavior: interrupt propagates without retry (T-001); genuine RuntimeError retries (T-002) | `pytest` | AC-002, AC-005 |
| `tests/agent/` (full) | Regression | `pytest` | All green |

## Completion criteria

- T-001 passes: `pytest.raises(StartupInterrupted)` and `retry_once_with_delay` not awaited
  (AC-002).
- T-002 passes: `retry_once_with_delay` awaited once and the retried proc is returned
  (AC-005).

## Out of Scope

Source changes to `startup_mcp_starter.py` / `startup.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261022-095438 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261022-095438 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261022-095438 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261022-095438 | N/A: no docs map to this test |

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
- **Requirement ID**: REQ-002, REQ-005
- **Source issue**: `issues/20261021-220332_star002_make-startupinterrupted-distinguishable-from-ordinary-runtimeerror-in-broad-startup-handlers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261021-232426_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-072226
- **Related target files**: `tests/agent/test_startup_mcp_lifecycle.py`
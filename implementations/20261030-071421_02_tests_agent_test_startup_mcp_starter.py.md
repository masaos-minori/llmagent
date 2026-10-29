## Goal

Add unit tests covering both branches of the non-200 + `liveness` decision in
`_verify_single_health` (`tests/agent/test_startup_mcp_starter.py`): a 503 with
`liveness == true` must not raise, while a 503 with `liveness == false` and a
non-503 non-200 must still raise `RuntimeError` (REQ-002).

## Scope

Modify only `tests/agent/test_startup_mcp_starter.py` — append three tests. No
source file change (that is covered by the sibling procedure for
`scripts/agent/startup_mcp_starter.py`).

## Assumptions

- `respx` is available (already used by the existing health-check tests in this file).
- `httpx.Response(status, json=...)` sets `content-type` to `application/json`,
  which `is_degraded_but_live` requires before parsing the body.
- Mocking the `/health` route with a fixed `return_value` bypasses the auth
  handler, so no valid bearer token is required for these cases.

## Design decisions

- Drive each case with a dedicated respx route returning a fixed
  `httpx.Response` (status, JSON body, content-type), mirroring the existing
  `test_verify_single_health_fails_with_wrong_token` respx pattern.
- Assert "no raise" via bare `await` for the degraded-but-live case, and
  `pytest.raises(RuntimeError)` for the two fatal cases.

## Alternatives considered

N/A: single test module, Path A; no interface or fixture changes needed.

## Implementation
### Target file

`tests/agent/test_startup_mcp_starter.py`

### Procedure

Append the three tests below immediately after
`test_verify_single_health_fails_with_wrong_token` (end of the current health
section).

### Method

Each test builds a starter via the existing `_starter_ctx` helper, mocks the
`GET /health` route with a fixed `httpx.Response`, awaits
`_verify_single_health`, and asserts the expected outcome.

### Details

```python
@pytest.mark.asyncio
async def test_verify_single_health_degraded_but_live_does_not_raise():
    import httpx
    import respx

    from agent.startup_mcp_starter import McpServerStarter

    ctx, _ = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(
                503, json={"liveness": True}, headers={"content-type": "application/json"}
            )
        )
        # Must not raise: degraded-but-live is treated as ready.
        await starter._verify_single_health("srv", ctx.cfg.mcp.mcp_servers["srv"])


@pytest.mark.asyncio
async def test_verify_single_health_degraded_but_live_false_raises():
    import httpx
    import respx

    from agent.startup_mcp_starter import McpServerStarter

    ctx, cfg = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(
                503, json={"liveness": False}, headers={"content-type": "application/json"}
            )
        )
        with pytest.raises(RuntimeError, match="HTTP 503"):
            await starter._verify_single_health("srv", cfg)


@pytest.mark.asyncio
async def test_verify_single_health_non_503_non_200_raises():
    import httpx
    import respx

    from agent.startup_mcp_starter import McpServerStarter

    ctx, cfg = _starter_ctx("s3cret")
    starter = McpServerStarter(ctx, MagicMock())
    with respx.mock as router:
        router.get("http://localhost:9999/health").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"})
        )
        with pytest.raises(RuntimeError, match="HTTP 401"):
            await starter._verify_single_health("srv", cfg)
```

## Compatibility considerations

The pre-existing `test_verify_single_health_fails_with_wrong_token` is unchanged.
The new degraded-but-live test uses a fixed response (no auth check), so it does
not depend on the bearer token.

## Security considerations

N/A: no auth, secret, or credential-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy (Unit) | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_startup_mcp_starter.py` | Run the three new tests plus the existing health tests | `uv run pytest tests/agent/test_startup_mcp_starter.py` | All pass, including `test_verify_single_health_fails_with_wrong_token` |

## Completion criteria

- `test_verify_single_health_degraded_but_live_does_not_raise` (new) passes (no
  raise on 503 + `liveness: true`).
- `test_verify_single_health_degraded_but_live_false_raises` (new) passes (raises
  on 503 + `liveness: false`).
- `test_verify_single_health_non_503_non_200_raises` (new) passes (raises on 401).
- Existing tests in the file still pass.

## Out of Scope

Changing `verify_health` retry semantics, delays, or retry count; spawn-phase
`poll_until_ready` behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the three unit tests described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (unit tests asserting both branches of the non-200 + `liveness` decision)
- **Source issue**: issues/20261029-220520_mcphc001_degraded-but-live-retry.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-000009_mcphc001_degraded-but-live-retry.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071421
- **Related target files**: tests/agent/test_startup_mcp_starter.py

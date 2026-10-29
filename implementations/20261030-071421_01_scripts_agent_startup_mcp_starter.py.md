## Goal

Make `_verify_single_health` in `scripts/agent/startup_mcp_starter.py` treat a
non-200 `/health` response whose body indicates `liveness == true` as
degraded-but-live (tolerated) instead of fatal, reusing the exact
`HealthChecker.is_degraded_but_live` predicate that `poll_until_ready` uses
(REQ-001, REQ-003).

## Scope

Modify only `_verify_single_health` (and its docstring) in
`scripts/agent/startup_mcp_starter.py`. No other file.

## Assumptions

- Only HTTP 503 counts as degraded-but-live, mirroring `is_degraded_but_live`
  (which returns `False` for any other status). Other non-200 statuses stay fatal.
- Returning normally from `_verify_single_health` on a degraded-but-live body makes
  `retry_once_with_delay` treat the retry as success, consistent with
  `verify_health`'s direct-path `continue`.
- Importing `HealthChecker` from `agent.http_lifecycle_health_checker` introduces no
  import cycle: the health checker depends only on `shared.mcp_config` and
  `agent.secrets_masker`, neither of which imports the starter (verified in Step 3a).

## Design decisions

- Call `HealthChecker.is_degraded_but_live(resp)` rather than re-implementing the
  status / content-type / JSON / `liveness` check, so spawn and post-startup phases
  share one source of truth.
- Keep `RuntimeError` for genuinely dead / non-degraded endpoints; the existing
  exception type on this path is `RuntimeError`, unchanged by this change.

## Alternatives considered

N/A: single-function Path A change; reimplementing the predicate inline would
duplicate the source of truth and reintroduce the drift this change removes.

## Implementation
### Target file

`scripts/agent/startup_mcp_starter.py`

### Procedure

1. Add `from agent.http_lifecycle_health_checker import HealthChecker` to the agent
   import block at the top of the file.
2. In `_verify_single_health`, on the non-200 branch, call
   `HealthChecker.is_degraded_but_live(resp)`; if `True`, log a degraded-but-live
   warning and `return`; otherwise raise `RuntimeError(f"HTTP {resp.status_code}")`
   as before.
3. Update the `_verify_single_health` docstring to describe the `liveness`-based
   degradation path.

### Method

Inside the existing `if resp.status_code != httpx.codes.OK:` block, insert the
`is_degraded_but_live` branch before the unconditional `raise`.

### Details

Current (lines 204-205):

```python
            if resp.status_code != httpx.codes.OK:
                raise RuntimeError(f"HTTP {resp.status_code}")
```

Replace with:

```python
            if resp.status_code != httpx.codes.OK:
                if HealthChecker.is_degraded_but_live(resp):
                    logger.warning(
                        "Post-startup health check degraded-but-live for %r "
                        "(after retry); treating as ready",
                        server_key,
                    )
                    return
                raise RuntimeError(f"HTTP {resp.status_code}")
```

Add the import to the agent import block (after line 25,
`from agent.secrets_masker import _mask_secrets`):

```python
from agent.http_lifecycle_health_checker import HealthChecker
```

Update the docstring from `"""Verify health of a single MCP subprocess server."""` to:

```python
        """Verify health of a single MCP subprocess server.

        A non-200 /health response whose body indicates liveness == true is
        degraded-but-live (the server started but an optional dependency is
        unavailable) and is tolerated: this returns normally so the retry
        helper treats the retry as success. Any other non-200 still raises
        RuntimeError.
        """
```

## Compatibility considerations

The pre-existing `test_verify_single_health_fails_with_wrong_token` asserts a 401
raises `RuntimeError` matching `"HTTP 401"`. A 401 is not 503, so
`is_degraded_but_live` returns `False` and the assertion still holds.

## Security considerations

N/A: no auth, secret, or credential-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy (Unit) | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_mcp_starter.py::_verify_single_health` | Mock httpx response via respx for 503 + `{"liveness": true}`, 503 + `{"liveness": false}`, and 401 | `uv run pytest tests/agent/test_startup_mcp_starter.py` | 503+liveness:true does not raise; 503+liveness:false and 401 raise `RuntimeError` |

## Completion criteria

- A mocked 503 + `{"liveness": true}` body returns without raising.
- A mocked 503 + `{"liveness": false}` body raises `RuntimeError`.
- A mocked non-503 non-200 body (e.g. 401) raises `RuntimeError`.
- Existing tests in `tests/agent/test_startup_mcp_starter.py` still pass, including
  the pre-existing wrong-token assertion.

## Out of Scope

The retry loop, delays, and retry count in `verify_health`; the spawn-phase
`poll_until_ready` behavior; consolidating `verify_health`'s inline
degraded-but-live block into `is_degraded_but_live`; any non-MCP health checks.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (align `_verify_single_health` non-200 handling with the degraded-but-live predicate), `REQ-003` (keep `RuntimeError` for non-degraded/non-503 responses)
- **Source issue**: issues/20261029-220520_mcphc001_degraded-but-live-retry.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-000009_mcphc001_degraded-but-live-retry.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071421
- **Related target files**: scripts/agent/startup_mcp_starter.py

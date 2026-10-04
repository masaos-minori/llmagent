## Goal

Document the current HTTP client reuse strategy as intentional — connection cleanup on failure takes priority over connection pooling benefits.

## Scope

- Modify `scripts/agent/http_lifecycle.py`: add docstring comment explaining why new client per session is intentional
- No code changes needed — documentation only

## Assumptions

- Option B (document as intentional) is preferred unless benchmarking shows measurable impact
- The current approach prioritizes correctness (no leaked connections) over performance (connection pooling)
- Connection pooling benefits are marginal for short-lived health checks against localhost

## Design decisions

- Add inline comment/docstring explaining the rationale for creating a new AsyncClient per health-poll session
- Document the trade-off: connection cleanup on failure vs connection pooling overhead
- Keep the existing behavior unchanged

## Alternatives considered

- Implementing a shared HTTP client for health checks (Option A) — requires careful lifetime management, risk of connection leaks
- Adding a class-level `_health_client` attribute — adds complexity without clear benefit for localhost health checks

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

Add docstring comment explaining why new client per session is intentional.

### Method

1. Locate lines 393-395, 466-468 in `scripts/agent/http_lifecycle.py` (new AsyncClient per session)
2. Add inline comment explaining the rationale for the current approach

### Details

```python
# Before (around line 393-395):
async def _health_poll_until_ready(
    self, server_key: str, timeout: float = 30.0
) -> bool:
    """Poll the health endpoint until the server becomes healthy."""
    async with httpx.AsyncClient() as client:
        ...

# After:
async def _health_poll_until_ready(
    self, server_key: str, timeout: float = 30.0
) -> bool:
    """Poll the health endpoint until the server becomes healthy.
    
    Note: A new AsyncClient is created per call rather than reusing a shared
    instance. This prioritizes correctness (no leaked connections on failure)
    over connection pooling benefits, which are marginal for short-lived
    health checks against localhost.
    """
    async with httpx.AsyncClient() as client:
        ...
```

The key change is adding an inline comment/docstring explaining the rationale for the current approach. This prevents future developers from "optimizing" by introducing a shared client that could leak connections.

## Compatibility considerations

This change is backward-compatible — it's documentation-only. No existing behavior is changed.

## Security considerations

N/A: No security impact.

## Rollback considerations

Remove the added comment if the shared client approach is adopted later.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Verification — confirm comment explains rationale | Manual inspection | Comment present and accurate |

## Completion criteria

- [ ] Behavior documented as intentional (REQ-001)
- [ ] Comment explains trade-off between correctness and performance

## Out of scope

- Changes to the health-check polling interval or timeout
- Changes to the HTTP client configuration
- Creating new test file (handled in separate document)

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261004-143011_hlm012_http_client_reuse.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182819_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-200103
- **Related target files**: scripts/agent/http_lifecycle.py

# Implementation and Test Procedure: Correct HttpTransport retry backoff documentation

## Goal

Correct the HttpTransport retry backoff documentation in `04_mcp_03_routing_lifecycle_and_execution.md` to accurately describe the actual implementation behavior (decreasing delay pattern, not exponential backoff).

## Scope

**In-Scope**:
- Update retry description in `04_mcp_03_routing_lifecycle_and_execution.md` line 203: change "exponential backoff" to "decreasing delay"
- Clarify that delays are 4s → 2s → 1s (not 1s → 2s → 4s)
- Clarify non-retryable errors: HTTP timeout and HTTPStatusError for non-429/502/503/504

**Out-of-Scope**:
- Changes to the actual implementation code
- Adding new tests (existing tests already cover retry behavior)

## Assumptions

1. The implementation is correct as-is — decreasing delays are intentional
2. No implementation changes are needed
3. Existing tests (TC-A04, TC-A13, TC-A14, TC-A15, TC-A16, TC-A17) already cover retry behavior

## Implementation

### Target file

`docs/04_mcp_03_routing_lifecycle_and_execution.md`

### Procedure

1. Read the file to locate line 203
2. Change "exponential backoff" to "decreasing delay" in the retry description
3. Update the delay values from "1s → 2s → 4s" to "4s → 2s → 1s"
4. Clarify non-retryable errors section

### Method

The current implementation uses `2 ** (self._RETRY_MAX - attempt - 1)` which produces:
- attempt=0: 2^(3-0-1) = 4 seconds
- attempt=1: 2^(3-1-1) = 2 seconds
- attempt=2: 2^(3-2-1) = 1 second

This is a **decreasing** delay pattern, not exponential backoff.

### Details

**Before** (line ~203):
```
Retry: retries on HTTP 429/502/503/504, up to 3 attempts with exponential backoff (1s → 2s → 4s). Only the final outcome (success or TransportError after all retries exhausted) is recorded in HealthRegistry.
```

**After**:
```
Retry: retries on HTTP 429/502/503/504, up to 3 attempts with decreasing delay (4s → 2s → 1s). Only the final outcome (success or TransportError after all retries exhausted) is recorded in HealthRegistry.
```

**Non-retryable errors** — also update the same paragraph:
- HTTP timeout (`httpx.TimeoutException`) — immediately propagated without retry
- HTTPStatusError for non-429/502/503/504 status codes — immediately propagated without retry

## Validation plan

| Check | Tool/Method | Target |
|---|---|---|
| Documentation accuracy | Read updated file, verify delay values match implementation | Delays are 4s → 2s → 1s |
| Implementation unchanged | `git diff` on `scripts/shared/tool_executor.py` | No changes to implementation |
| Existing tests pass | `pytest tests/integration/test_agent_mcp_integration.py -v` | All TC-A01 through TC-A17 pass |
| Non-retryable errors documented | Verify HTTPStatusError section mentions non-429/502/503/504 | Correct status codes listed |

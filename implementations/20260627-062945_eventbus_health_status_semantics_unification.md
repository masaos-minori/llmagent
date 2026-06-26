## Goal

Unify the `/health` HTTP status semantics to fail closed on degraded states — correct documentation that says `/health` always returns HTTP 200, since runtime behavior already returns HTTP 503 for degraded/unhealthy states.

## Scope

**In-Scope**:
- Correct documentation that says `/health` always returns HTTP 200 (06_eventbus_02_http_api_and_runtime.md)
- Update tests for all health states if needed (runtime behavior and tests already correct)
- Ensure `06_eventbus_02_http_api_and_runtime.md`, `06_eventbus_05_configuration_deploy_and_operations.md`, and `06_eventbus_90_inconsistencies_and_known_issues.md` are consistent

**Out-of-Scope**:
- Adding authentication to `/health`
- Changing the health response JSON schema unless required for consistency

## Assumptions

1. Runtime behavior already returns HTTP 503 for degraded states — confirmed by app.py:151
2. Tests already expect HTTP 503 for degraded states — confirmed by test_eventbus_health.py:103
3. Only documentation needs correction — no code changes required

## Implementation

### Target file: docs/06_eventbus_02_http_api_and_runtime.md

**Procedure**: Correct health endpoint documentation to reflect actual HTTP status semantics.

**Method**: Modify the HTTP API and runtime documentation.

**Details**:
1. Line 67: Replace "Always HTTP 200" with "HTTP 200 for ok, HTTP 503 for degraded/unhealthy"
2. Add detail about which states return which status codes:
   - ok → HTTP 200
   - degraded → HTTP 503
   - unhealthy → HTTP 503

### Target file: docs/06_eventbus_05_configuration_deploy_and_operations.md

**Procedure**: Verify consistency with corrected health endpoint documentation.

**Method**: Cross-check all three Event Bus docs for health endpoint documentation.

**Details**:
1. Line 55: Already shows 503 for unhealthy (correct)
2. No changes needed if already consistent

### Target file: docs/06_eventbus_90_inconsistencies_and_known_issues.md

**Procedure**: Verify consistency with corrected health endpoint documentation.

**Method**: Cross-check all three Event Bus docs for health endpoint documentation.

**Details**:
1. Line 15: Already says "Resolved" (correct)
2. No changes needed if already consistent

### Target file: docs/06_eventbus_02_http_api_and_runtime.md

**Procedure**: Add monitoring guidance for `/health` endpoint.

**Method**: Add section about health monitoring best practices.

**Details**:
1. Document that monitoring should alert on HTTP status code, not only JSON body fields
2. Add note about fail-closed operational monitoring

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| 06_eventbus_02_http_api_and_runtime.md | Verify health endpoint docs correctly describe HTTP status semantics | Check /health section | No "Always HTTP 200" claim; correct mapping of status→HTTP code |
| All Event Bus docs | Verify no contradictory claims remain | Search for "always HTTP 200" across docs | Zero contradictory claims |
| tests/test_eventbus_health.py | Verify tests still pass with current behavior | Run pytest | Tests pass unchanged (tests already correct) |

## Risks

- **Risk**: No risks identified — runtime behavior and tests are already correct; only documentation needs correction | **Likelihood**: N/A | **Mitigation**: N/A | False

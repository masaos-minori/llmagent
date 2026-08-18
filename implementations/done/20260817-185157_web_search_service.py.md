## Goal

Evaluate whether to create a shared success/failure-recording helper for `search_web`/`fetch_browser` in `web_search_service.py`, contingent on resolving the `UNK-03` design note.

## Scope

- **In-Scope**:
  - Phase 1: Investigate `UNK-03` design rationale and determine if it still blocks consolidation
  - Phase 2: Add characterization tests for metrics/health call order and arguments
  - Phase 3: Decide Option A (extract shared helper) or Option B (leave as-is) based on investigation findings
- **Out-of-Scope**:
  - Runtime behavior changes (pure refactoring if Option A)
  - Changes outside `scripts/mcp_servers/web_search/`

## Assumptions

- `search_web` and `fetch_browser` share a near-identical timing/metrics/health-recording skeleton
- Each function maintains its own independent metrics/health singleton pair (per `UNK-03` design note)
- The `UNK-03` design note may have been written before the two operations could safely be coupled

## Design decisions

- If Option A (extract), parameterize the shared helper by which metrics/health singleton pair to use
- If Option B (leave as-is), document why the `UNK-03` rationale still applies

## Alternatives considered

- Extract shared helper — preferred if `UNK-03` no longer blocks consolidation
- Leave as-is — acceptable if `UNK-03` rationale remains valid

## Compatibility considerations

- Option A: Behavioral change in metrics/health recording order — must be verified by characterization tests
- Option B: No behavioral change

## Security considerations

- N/A — no security-relevant behavior change

## Rollback considerations

- Revert the diff; no data loss or service impact

## Implementation

### Target file

`scripts/mcp_servers/web_search/web_search_service.py`

### Procedure

1. **Phase 1: Preparation / Investigation**
   - Locate and re-read the `UNK-03` design rationale: `rg "UNK-03" scripts/mcp_servers/web_search/`
   - Determine whether the `UNK-03` note still blocks consolidation
   - Read `search_web` and `fetch_browser` functions to understand the current recording patterns

2. **Phase 2: Core Logic Implementation**
   
   **If Option A (extract recommended):**
   - Add characterization tests pinning metrics/health call order and arguments per branch for both functions
   - Extract a shared trailer helper (e.g. `_record_outcome(...)`) parameterized by which metrics/health singleton pair to use
   - Call the shared helper from both `search_web` and `fetch_browser`
   - Verify all characterization tests pass unchanged
   
   **If Option B (leave as-is):**
   - Document why the `UNK-03` rationale still applies

3. **Phase 3: Deployment & Verification**
   - Run `uv run pytest tests/mcp_servers/web_search/test_web_search_service.py -v` — verify all 14+ tests pass unchanged

### Method

Refactoring — extract shared recording logic into a parameterized helper function.

### Details

```python
# In scripts/mcp_servers/web_search/web_search_service.py, Option A (extract):

# BEFORE:
def search_web(query: str, ...) -> SearchResults:
    ...
    try:
        # search logic
        result = _do_search(query, ...)
        metrics.increment("success")
        health.record_success()
        return result
    except Exception as e:
        metrics.increment("failure")
        health.record_failure(e)
        raise

def fetch_browser(url: str, ...) -> BrowserResult:
    ...
    try:
        # browser logic
        result = _do_fetch(url, ...)
        metrics.increment("success")
        health.record_success()
        return result
    except Exception as e:
        metrics.increment("failure")
        health.record_failure(e)
        raise

# AFTER:
def _record_outcome(metrics: MetricsProxy, health: HealthProxy, outcome: str, error: BaseException | None = None) -> None:
    """Record success/failure to metrics and health proxies."""
    if outcome == "success":
        metrics.increment("success")
        health.record_success()
    else:
        metrics.increment("failure")
        health.record_failure(error)

def search_web(query: str, ...) -> SearchResults:
    ...
    try:
        # search logic
        result = _do_search(query, ...)
        _record_outcome(search_metrics, search_health, "success")
        return result
    except Exception as e:
        _record_outcome(search_metrics, search_health, "failure", e)
        raise

def fetch_browser(url: str, ...) -> BrowserResult:
    ...
    try:
        # browser logic
        result = _do_fetch(url, ...)
        _record_outcome(browser_metrics, browser_health, "success")
        return result
    except Exception as e:
        _record_outcome(browser_metrics, browser_health, "failure", e)
        raise

# In scripts/mcp_servers/web_search/web_search_service.py, Option B (leave as-is):

# Add comment above each recording block:
# Note: search_web and fetch_browser maintain separate metrics/health singletons.
# This separation was established per UNK-03 design rationale and preserved here.
# Consolidation would require coupling these concerns, which is not warranted.
```

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/web_search/test_web_search_service.py` | Regression + new characterization tests | `uv run pytest tests/mcp_servers/web_search/test_web_search_service.py -v` | All pass unchanged |

## Out of scope

- Runtime behavior changes (pure refactoring if Option A)
- Changes outside `scripts/mcp_servers/web_search/`

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260817-151058_require.md
- Source plan: plans/20260817-163447_plan.md
- Source implementation procedure: N/A
- Generated at: 20260817-185157
- Related target files: scripts/mcp_servers/web_search/web_search_service.py

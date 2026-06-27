# Design: Event Bus Startup Safety Guard

## Goal

Add a startup safety guard to reduce the risk of exposing the unauthenticated Event Bus API on public or LAN interfaces by detecting and warning/failing-fast on public bind addresses.

## Scope

**In-Scope**:
- Add `host` field to EventBusConfig for config-file-based host binding control
- Add `allow_public_bind: bool = False` field to EventBusConfig
- Validate public bind addresses at startup and fail-fast by default
- Log: no authentication enabled, bind address, whether public bind is allowed
- Update deployment docs with reverse proxy + authentication guidance
- Add tests for safe bind, unsafe bind, and explicit override

**Out-of-Scope**:
- Implementing API-key auth
- Implementing mTLS
- Adding ACLs

## Assumptions

1. The Event Bus has no authentication or ACL — confirmed in `docs/06_eventbus_01_system-overview.md` line 24: "The Event Bus API has **no authentication or ACL**."
2. Host binding is controlled via uvicorn CLI arguments (not TOML config) — confirmed by start command in `docs/06_eventbus_05_configuration_deploy_and_operations.md` line 46: `uvicorn eventbus.app:app --host 127.0.0.1 --port 8010`
3. Fail-fast is preferred over warning-only for security-sensitive operations
4. An explicit override flag is needed for development/testing scenarios where public bind may be required
5. The FastAPI lifespan handler runs before the server accepts connections, so validation in lifespan is effective

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Can the Event Bus detect its own bind address at startup? | Need to check if FastAPI/uvicorn exposes bind address after startup | uvicorn logs bind address; lifespan handler runs before server accepts connections — confirmed viable | False |
| UNK-02 | Does the Event Bus have any authentication mechanism today? | Need to confirm no auth exists in current implementation | System overview doc confirms "no authentication or ACL" — confirmed | False |

## Affected Areas & Tool Evidence

- **Affected Files**:
  - `scripts/eventbus/config.py` — EventBusConfig has no `host` or `allow_public_bind` field (lines 21-33)
  - `scripts/eventbus/app.py` — FastAPI app created without host validation; needs startup guard in lifespan
  - `docs/06_eventbus_05_configuration_deploy_and_operations.md` — line 31-33: mentions binding to 127.0.0.1 but no enforcement; startup command shows uvicorn with --host 127.0.0.1 (line 46)
  - `docs/06_eventbus_01_system-overview.md` — line 24-28: confirms no authentication, access control at network boundary
  - `tests/test_eventbus*.py` — new startup guard tests needed

- **Blast Radius**: Medium — adding a fail-fast mechanism to the Event Bus startup. If fail-fast is chosen, this could break existing deployments that accidentally bind to 0.0.0.0. Mitigation: the override flag allows operators to acknowledge the risk if needed.

## Implementation Details

### Phase 1: Add `host` and `allow_public_bind` config fields

**Target**: `scripts/eventbus/config.py`

1. Add `host: str = "127.0.0.1"` to EventBusConfig dataclass
2. Add `allow_public_bind: bool = False` to EventBusConfig dataclass
3. In `__post_init__`, validate that host is not a public address unless `allow_public_bind=True`:
   - Parse the host string
   - Check if it equals `"0.0.0.0"`, `"::"`, or any other IPv4/IPv6 wildcard address
   - Raise `ValueError` if public bind detected and `allow_public_bind=False`
4. Add helper function `_is_public_host(host: str) -> bool`:
   - Returns True if host is a public/wildcard address
   - Returns False for loopback addresses (127.0.0.1, ::1) and private IPs

### Phase 2: Implement startup guard in lifespan

**Target**: `scripts/eventbus/app.py`

1. In the `lifespan` context manager, after loading config, add a startup guard call
2. The guard should:
   - Log a warning if public bind is allowed (when `allow_public_bind=True`)
   - Raise `RuntimeError` if public bind is detected and not allowed
3. Log format on public bind detection:
   - `eventbus: WARNING — No authentication enabled, bind address=0.0.0.0, allow_public_bind=true`
4. Raise RuntimeError when fail-fast is triggered:
   - `RuntimeError("Event Bus bound to public address 0.0.0.0 without allow_public_bind=true. This is a security risk because the API has no authentication.")`

### Phase 3: Update deployment docs

**Target**: `docs/06_eventbus_05_configuration_deploy_and_operations.md`

1. Add `host` and `allow_public_bind` to the config fields table
2. Add explicit guidance about reverse proxy + authentication for public-facing deployments
3. Document the `allow_public_bind` config field and its security implications
4. Add warning about binding to 0.0.0.0 in production with example error output

### Phase 4: Add startup guard tests

**Target**: `tests/test_eventbus_startup.py` (new)

1. Test: Safe bind (127.0.0.1) — startup succeeds without warning
2. Test: Unsafe bind (0.0.0.0) with allow_public_bind=False — fail-fast via ValueError
3. Test: Unsafe bind (::) with allow_public_bind=False — fail-fast via ValueError
4. Test: Unsafe bind (0.0.0.0) with allow_public_bind=True — startup proceeds with warning
5. Test: Private IP (192.168.x.x, 10.x.x.x) — allowed without override

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/config.py | Verify host and allow_public_bind fields added and validated | Check for new config field and validation logic | Config rejects public bind unless explicit override |
| scripts/eventbus/app.py | Verify startup guard implemented in lifespan | Check for bind address detection and fail-fast/warning | Public bind detected and handled at startup |
| 06_eventbus_05_configuration_deploy_and_operations.md | Verify deployment docs updated with security guidance | Check for reverse proxy + auth guidance, config table update | Docs clearly state Event Bus must not be exposed directly |
| tests/test_eventbus_startup.py (new) | Verify startup guard tests pass | `uv run pytest tests/test_eventbus_startup.py` | All startup guard tests pass |

## Risks

- **Risk**: Fail-fast on public bind may break existing deployments that accidentally bind to 0.0.0.0 | **Likelihood**: High | **Mitigation**: The override flag (`allow_public_bind=true`) allows operators to acknowledge the risk if needed. Start with warning-only behavior in lifespan, then consider fail-fast after confirming no existing deployments bind to 0.0.0.0. | True
- **Risk**: uvicorn may not expose bind address before FastAPI startup handler runs | **Likelihood**: Low | **Mitigation**: By adding `host` as a config field, the guard validates at config load time (in `__post_init__`), which runs before the lifespan handler. This is more reliable than trying to detect the bind address from uvicorn after the fact. | False

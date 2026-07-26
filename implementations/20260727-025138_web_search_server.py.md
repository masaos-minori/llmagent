## Goal

Fix pyright error in `scripts/mcp_servers/web_search/web_search_server.py` by adding `cast(_FastAPIApp, app)` before `attach_auth_middleware()` call.

## Scope

**In-Scope:**
- Import `cast` from typing module
- Wrap `app` with `cast(_FastAPIApp, app)` before `attach_auth_middleware()` call

**Out-of-Scope:**
- Changes beyond the cast addition
- Any other file modifications

## Assumptions

1. `FastAPI` instances satisfy the `_FastAPIApp` protocol — casting is safe
2. No callers rely on positional argument syntax for `.middleware()` calls

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether `cast` import conflicts with existing imports | Check existing typing imports | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/mcp_servers/web_search/web_search_server.py:55` — add cast before `attach_auth_middleware()` call

- **Blast Radius:**
  - Very low churn — two line changes (import + cast)
  - Low risk since changes are purely defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `web_search_server.py`:
```python
# Current (broken):
from typing import Any

# Line 55:
attach_auth_middleware(app, _cfg.browser_auth_token or "")

# Proposed fix:
from typing import Any, cast

# Line 55:
attach_auth_middleware(cast(_FastAPIApp, app), _cfg.browser_auth_token or "")
```

## Implementation

### Target file
`scripts/mcp_servers/web_search/web_search_server.py`

### Procedure
1. Open `scripts/mcp_servers/web_search/web_search_server.py`
2. Locate line 15: `from typing import Any`
3. Add `cast` to the import: `from typing import Any, cast`
4. Locate line 55: `attach_auth_middleware(app, _cfg.browser_auth_token or "")`
5. Change to: `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.browser_auth_token or "")`
6. Save the file

### Method
Add cast wrapper around the `app` variable before passing to `attach_auth_middleware()`.

### Details
- Line 15: `from typing import Any` → `from typing import Any, cast`
- Line 55: `attach_auth_middleware(app, ...)` → `attach_auth_middleware(cast(_FastAPIApp, app), ...)`
- Verify `_FastAPIApp` is already imported (it is — via `from mcp_servers.server import MCPServer, attach_auth_middleware, build_tools_response`)

## Compatibility considerations

N/A — cast is a no-op at runtime, only affects static analysis

## Security considerations

N/A

## Rollback considerations

- Simple revert: remove `cast` from import and remove `cast(_FastAPIApp, app)` wrapper

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/web_search/web_search_server.py` | Verify cast doesn't break FastAPI compatibility | `uv run pyright scripts/mcp_servers/web_search/web_search_server.py` | No new errors |

## Out of scope

- Changes beyond the cast addition
- Any other file modifications

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-162548_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-025138
- Related target files: scripts/mcp_servers/web_search/web_search_server.py

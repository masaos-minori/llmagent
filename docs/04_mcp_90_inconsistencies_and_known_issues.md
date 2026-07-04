# MCP Inconsistencies and Known Issues

This file catalogs bugs, unimplemented features, spec conflicts, and undefined behavior
in the MCP layer discovered during documentation restructuring.

Each entry format:
- **Type:** `Implementation bug` / `Unimplemented` / `Document inconsistency` / `Undefined` / `Needs confirmation`
- **Impact scope:** Affected modules/behavior
- **Statement A / B:** Conflicting facts (when applicable)
- **Current safe interpretation:** What to assume when uncertain
- **Recommended action:** Fix or investigation needed
- **Notes for AI reference:** Guidance for AI reasoning about this issue

---



## Active Issues

---

### MCP-08: Health semantics — HTTP status code vs body fields mismatch

**Type:** Document inconsistency
**Impact scope:** All MCP servers, `agent/repl_health.py`

**Statement A:** All MCP server `/health` endpoints return HTTP 200 even when dependency failures are detected (status=degraded, ready=false).

**Statement B:** Watchdog (`agent/repl_health.py:31`) checks only HTTP response status code (`resp.status_code == HTTPStatus.OK`), NOT body fields.

**Impact:** Dependency failures that should trigger server restart via watchdog do not — the watchdog never sees a non-200 HTTP response. This creates a gap where degraded servers are not automatically recovered.

**Current safe interpretation:** Watchdog only reacts to HTTP 5xx errors from `/health`, not to body-level degradation signals. Operators must monitor body fields separately for readiness assessment.

**Recommended action:** Define canonical semantics for `/health` response:
- `status="ok"` → HTTP 200 (fully healthy)
- `status="degraded"` → HTTP 503 (dependency failure, watchdog should restart)
- `status="unhealthy"` → HTTP 503 (critical failure)

**Notes for AI reference:** When implementing or modifying MCP server health endpoints, ensure HTTP status code matches the body `status` field. Watchdog uses HTTP status code only.

---

### MCP-09: cicd workflow_allowlist policy mismatch — RuntimeError vs warning

**Type:** Document inconsistency
**Impact scope:** `04_mcp_04`, `scripts/mcp/cicd/service_guards.py`

**Statement A:** `04_mcp_04:273` — "in production mode (`security_profile = "production"`), empty `workflow_allowlist` raises `RuntimeError` at agent startup"

**Statement B:** `scripts/mcp/cicd/service_guards.py` — no `security_profile` field exists in cicd config; empty `workflow_allowlist` only emits a warning log, never raises `RuntimeError`. The actual behavior is:
- `cicd-mcp: workflow_allowlist is empty — all workflow triggers will be denied` (warning logged)
- All workflow trigger requests are rejected (fail-closed)

**Impact:** Operators relying on RuntimeError to catch misconfiguration will not see it; the server starts successfully with a warning. AI routing systems that parse `04_mcp_04` may incorrectly assume RuntimeError prevents startup.

**Current safe interpretation:** Empty `workflow_allowlist` is fail-closed (denies all triggers) but does NOT raise RuntimeError. A startup warning is logged. Do not rely on RuntimeError to catch misconfiguration.

**Recommended action:** Either implement the RuntimeError in service_guards.py (when security_profile=="production" and workflow_allowlist is empty), or remove the RuntimeError claim from `04_mcp_04`.

**Notes for AI reference:** Do not assume RuntimeError prevents startup when workflow_allowlist is empty. Only a warning is emitted. Operators must check the warning log proactively.

---



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

## Resolved Issues

### MCP-08: Health semantics — HTTP status code vs body fields mismatch

**Type:** Document inconsistency (resolved)
**Impact scope:** All MCP servers, `agent/repl_health.py`

**Status: RESOLVED** — The health schema was redesigned to include `liveness`, `restart_recommended`, and `operator_action_required` fields. All MCP servers now return HTTP 503 when degraded (`status="degraded"`, `ready=false`). The watchdog now inspects the `restart_recommended` body field in addition to the HTTP status code. Restart is gated on `restart_recommended=true`; `operator_action_required=true` (missing credentials, missing binary) produces a WARNING log only without restarting.

**Original issue:** Watchdog checked only HTTP status code; degraded servers with missing credentials would trigger infinite restart loops. Now `operator_action_required=true` + `restart_recommended=false` prevents unwanted restarts.

---

### MCP-02: Routing authority mismatch (Priority 3 formatting)

**Type:** Document inconsistency (resolved)
**Impact scope:** `04_mcp_03`, `04_mcp_90`

**Resolved:** Routing is now 2-layer only. Priority 3 (`Config tool_names`) and Priority 4 (prefix routing) were removed. `tool_names` is drift validation metadata only, not a routing input. See `04_mcp_03` §Routing Source of Truth.

See also: MCP-10 — follow-up change that fully removed the discovery override mechanism.

### MCP-07: Health semantics ambiguity (DEGRADED state missing from diagram)

**Type:** Document inconsistency (resolved)
**Impact scope:** `04_mcp_03`

**Resolved:** Diagram in `04_mcp_03` updated to include DEGRADED state between HEALTHY and UNAVAILABLE.

---

### MCP-06: Audit log format mismatch

**Type:** Document inconsistency (resolved)
**Impact scope:** `04_mcp_02`, `04_mcp_06`, `scripts/mcp/audit.py`, `scripts/agent/tool_audit.py`

**Resolved:** Both MCP server audit records and agent-side audit events now use JSON-lines format in the shared audit log. Field names are unified: `session_id` (was `session`), `request_id` (was `request`). The `error_type` and `server_key` fields are always present in MCP server records (empty string when not applicable). The `source` field distinguishes origins: `"mcp_server"` (MCP audit) vs `"agent"` (agent-side events). Operators can filter by source using `jq 'select(.source == "mcp_server")'` or `jq 'select(.source == "agent")'`.

---

### MCP-10: Discovery-override routing removed — ToolRegistry is sole routing authority

**Type:** Document inconsistency (resolved)
**Impact scope:** `scripts/shared/route_resolver.py`, `04_mcp_03`, `04_mcp_06`

**Previously:** `ToolRouteResolver.resolve()` gave live `/v1/tools` discovery map Priority 1 — if a server's `/v1/tools` response returned a different `server_key` for a tool than the registry, the discovery map won. This was documented as "highest priority / overrides all lower layers" in `04_mcp_03`.

**Now:** The Priority 1 discovery-map lookup block has been removed from `resolve()`. `ToolRegistry` (populated from `tool_constants.py` frozensets at import time) is the sole routing authority. Live `/v1/tools` is used only for startup drift validation via `check_routing_drift_vs_live()` in `repl_health.py`.

**Resolved by:** `requires/20260703_12_require.md` — plan `plans/20260703-122947_plan.md`.

**Notes for AI reference:** Do not assume live discovery overrides registry routing. The `discovery_map` parameter is retained on `ToolRouteResolver.__init__()` for backward compatibility with integration tests only; it has no effect on `resolve()` results.

---

### MCP-04: Transport error / HealthRegistry mismatch (ambiguous parenthetical)

**Type:** Document inconsistency (resolved)
**Impact scope:** `04_mcp_03`, `04_mcp_02`

**Resolved:** `04_mcp_03` §HttpTransport bullet corrected to state that
`HttpTransport` raises `TransportError` rather than returning `is_error=True`.
`04_mcp_02` now includes an explicit cross-reference note: "`HttpTransport.call()` never
returns `is_error=True` for transport failures — it raises `TransportError`."

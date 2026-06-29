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

### MCP-01: Startup mode terminology mismatch

**Type:** Document inconsistency
**Impact scope:** `04_mcp_02`, `04_mcp_03`

**Statement A (`04_mcp_02:187`):** HTTP comparison table says "subprocess only" for process management — misleading because HTTP supports both `subprocess` and `persistent` startup modes.

**Statement B (`04_mcp_02:109`):** Production default paragraph mentions StdioTransport in an HTTP section, conflating two different transport mechanisms.

**Current safe interpretation:** HTTP mode supports both `subprocess` (agent-managed) and `persistent` (externally managed) startup modes. StdioTransport is only used for stdio transport.

**Recommended action:** Fix the HTTP comparison table to say "subprocess or persistent" and move StdioTransport reference out of the HTTP section.

**Notes for AI reference:** When determining HTTP server lifecycle, assume both `subprocess` and `persistent` modes are valid for HTTP transport.

---

### MCP-02: Routing authority mismatch (Priority 3 formatting)

**Type:** Document inconsistency
**Impact scope:** `04_mcp_03`

**Statement A (Japanese table):** Priority 3 is not bolded while Priority 1, 2, and 4 are.

**Statement B (English table):** Same issue — Priority 3 is not bolded while Priority 1, 2, and 4 are.

Both tables show the same inconsistency: Priority 3 (`Config tool_names (in mcp_servers.toml)`) lacks bold formatting despite being listed as an authority source.

**Current safe interpretation:** Priority 3 is a valid routing fallback layer but is not emphasized in the table formatting. The priority order is correct regardless of formatting.

**Recommended action:** Add bold formatting to Priority 3 in both tables for consistency with Priority 1, 2, and 4.

**Notes for AI reference:** The routing priority order is correct (1→2→3→4). Formatting inconsistency does not affect behavior.

---

### MCP-04: Transport error / HealthRegistry mismatch (ambiguous parenthetical)

**Type:** Document inconsistency
**Impact scope:** `04_mcp_03`, `04_mcp_02`

**Statement A (`04_mcp_03:380`):** Table states `record_success()` for tool errors with "(server responded)" — ambiguous wording that could be misread as "when the server responds successfully."

**Statement B (`04_mcp_02:311`):** Clarifies that transport success (even with tool-level errors) calls `record_success()` to reset failure count.

**Current safe interpretation:** Tool-level errors do NOT affect `HealthRegistry` — only server unreachable/transport failures do. Any server response triggers `record_success()`.

**Recommended action:** Rewrite the parenthetical in the table to say "tool error (server responded)" instead of "(server responded)".

**Notes for AI reference:** Tool-level errors from a server are NOT tracked by HealthRegistry. Only transport failures (unreachable servers) increment failure counts.

---

### MCP-06: Audit log format mismatch

**Type:** Document inconsistency
**Impact scope:** `04_mcp_02`, `04_mcp_06`

**Statement A (`04_mcp_02:278`):** MCP server audit log uses key=value format:
```
AUDIT session=<session_id> request=<x_request_id> action=<tool_name> target=<primary_arg> outcome=<ok|error> detail=<supplementary>
```

**Statement B (`04_mcp_06:214-216`):** The same file (`/opt/llm/logs/audit.log`) uses two different formats:
- MCP server audit log: key=value format
- Agent-side audit log: JSON-lines format

**Current safe interpretation:** Both formats write to the same file. Operators must know which source wrote each line to parse correctly.

**Recommended action:** Add a note in both documents explaining how operators can distinguish between the two formats (e.g., parsing strategy, or add a `source` field to MCP audit logs).

**Notes for AI reference:** When parsing `/opt/llm/logs/audit.log`, check if a line starts with `AUDIT` — that indicates MCP server format; otherwise it's agent-side JSON-lines format.

---

### MCP-07: Health semantics ambiguity (DEGRADED state missing from diagram)

**Type:** Document inconsistency
**Impact scope:** `04_mcp_03`

**Statement A (`04_mcp_03:233-241`):** State transition diagram shows HEALTHY going directly to UNAVAILABLE on failure threshold — omits DEGRADED state.

**Statement B (`04_mcp_03:243-248`):** State table includes DEGRADED state: "Failure count < threshold (default 3)".

The diagram should show:
```
HEALTHY ──(failure × 1)──→ DEGRADED ──(failure × 2)──→ UNAVAILABLE
```

**Current safe interpretation:** There are 3 failures before blocking (not immediate). DEGRADED is an intermediate state that the diagram omits.

**Recommended action:** Update the state transition diagram to include the DEGRADED state between HEALTHY and UNAVAILABLE.

**Notes for AI reference:** Server dispatch is NOT blocked until 3 consecutive failures. The DEGRADED state is a warning level before UNAVAILABLE.

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

## Resolved Issues

### MCP-03: rag-pipeline tool count mismatch (mdq-mcp missing declaration)

**Type:** Document inconsistency
**Impact scope:** `04_mcp_04`

**Statement A (`04_mcp_04:251`):** rag-pipeline-mcp has explicit "All 4 tools are production" statement.

**Statement B (mdq-mcp section):** mdq-mcp lacked an equivalent tool status declaration in `04_mcp_04_server_catalog.md`.

**Resolution (2026-06-29):** Added explicit tool status declaration to mdq-mcp section in `04_mcp_04_server_catalog.md`. mdq-mcp has 7 production tools (`search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`) and 2 admin tools (`fts_consistency_check`, `fts_rebuild`). No stub markers exist in the codebase. This issue is closed.

---

### MCP-05: MDQ production-ready vs stub marker mismatch

**Type:** Document inconsistency
**Impact scope:** `04_mcp_00`, `04_mcp_04`, `04_mcp_05`

**Statement A (`04_mcp_00:59,79`):** Document guide asserts mdq-mcp is production-ready (FTS5 search and indexing implemented).

**Statement B (`04_mcp_05:324`):** Same assertion: "mdq-mcp is production-ready."

**Historical context:** mdq-mcp was previously marked as `"status": "stub"` with `"stub": True` in the `/health` endpoint. Current code (`scripts/mcp/mdq/tools.py`) has all 7 non-admin tools with `"status": "production"` and no `stub` indicator in health response.

**Resolution (2026-06-18):** The `stub` marker has been verified absent from both `scripts/mcp/mdq/tools.py` (no `stub` key in any tool entry) and `scripts/mcp/mdq/server.py` (no `stub` field in `/health` endpoint). All 7 non-admin mdq-mcp tools have `"status": "production"`. Explicit tool status declaration added to `04_mcp_04_server_catalog.md`. This issue is closed.

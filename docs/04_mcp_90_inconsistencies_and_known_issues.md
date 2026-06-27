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

## Resolved

### SPEC-01: tool_definitions_strict validation behavior

**Type:** Document inconsistency — **resolved**
**Impact scope:** `04_mcp_03`, `04_mcp_06`

**Statement A (`04_mcp_03:96`):** `validate_routing_against_live()` is "Not yet wired (future)"

**Statement B (`04_mcp_06:407`):** `_check_tool_definitions` runs at agent startup and compares `tool_definitions` against live `/v1/tools`

**Resolution:** These are DIFFERENT functions with different purposes:
- `validate_routing_against_live()` (route_resolver.py): compares live `/v1/tools` against the **internal routing registry** — not yet wired at startup
- `_check_tool_definitions` (repl_health.py): compares **configured `tool_definitions`** (from `agent.toml`) against live `/v1/tools` — IS wired at startup

There is no actual contradiction. Both statements are accurate — they describe different code paths.

**Current safe interpretation:** Use `04_mcp_06 §Startup Validation Behavior` as the authoritative behavior spec for `tool_definitions_strict`. The `validate_routing_against_live()` function in `04_mcp_03` is a separate, future feature.

**Notes for AI reference:** When asked about startup validation or `tool_definitions_strict` behavior, cite `04_mcp_06 §Startup Validation Behavior`. When asked about routing drift detection, cite `04_mcp_03 §Drift validation`.

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

### MCP-03: rag-pipeline tool count mismatch (mdq-mcp missing declaration)

**Type:** Document inconsistency
**Impact scope:** `04_mcp_04`

**Statement A (`04_mcp_04:251`):** rag-pipeline-mcp has explicit "All 4 tools are production" statement.

**Statement B (mdq-mcp section):** mdq-mcp lacks an equivalent tool status declaration despite having 9 tools with mixed statuses.

**Current safe interpretation:** mdq-mcp tools have mixed statuses (production and stub). Cross-reference `scripts/mcp/mdq/tools.py` to verify individual tool status.

**Recommended action:** Add explicit tool status declaration for mdq-mcp similar to rag-pipeline-mcp's declaration.

**Notes for AI reference:** Do not assume all mdq-mcp tools are production-ready; check `scripts/mcp/mdq/tools.py` for individual tool status.

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

### MCP-05: MDQ production-ready vs stub marker mismatch

**Type:** Document inconsistency
**Impact scope:** `04_mcp_00`, `04_mcp_04`, `04_mcp_05`

**Statement A (`04_mcp_00:59,79`):** Document guide asserts mdq-mcp is production-ready (FTS5 search and indexing implemented).

**Statement B (`04_mcp_05:324`):** Same assertion: "mdq-mcp is production-ready."

**Historical context:** mdq-mcp was previously marked as `"status": "stub"` with `"stub": True` in the `/health` endpoint. Current code (`scripts/mcp/mdq/tools.py`) has all 7 non-admin tools with `"status": "production"` and no `stub` indicator in health response.

**Current safe interpretation:** mdq-mcp is production-ready for its FTS5 capabilities. The lack of hybrid search (MDQ-02) does not make it a stub — FTS5 is the primary search mechanism.

**Recommended action:** Add explicit tool status declaration to mdq-mcp section in `04_mcp_04_server_catalog.md` similar to rag-pipeline-mcp's declaration. Clarify that hybrid search (MDQ-02) is planned, not missing.

**Notes for AI reference:** mdq-mcp is production-ready for FTS5 search. Hybrid search mode (`mode=hybrid`) is planned but not yet implemented — falls back to FTS5-only results.

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

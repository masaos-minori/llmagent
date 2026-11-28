## Goal

Make MDQ's HTTP surface answer tool availability from one per-tool function used by both discovery and dispatch, emit exactly one audit record per authenticated call from a single boundary, and render domain failures as stable codes (REQ-001, REQ-004, REQ-005, REQ-007).

## Scope
**Release unit**: boundary-characterization-tests (Plan steps 3 and 4 cite this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- `tests/mcp_servers/mdq/test_mdq_exception_handlers.py` is a companion of this document (SKILL.md conditions 1-4 hold: it is named only by this row and only changes assertions to follow the boundary decided here), so it has no document of its own.
- The code vocabulary and the `tool_disabled` code are defined by `scripts/mcp_servers/mdq/mdq_error_codes.py` (seq 08); this document consumes them and defines none.
- UNK-01 (non-blocking): codes that today map to HTTP 503 stay tool-level with `is_error=true`, per the plan's documented default; no new transport behavior is introduced.
- Cross-plan overlap on `docs/22_mcp/mcp_04_04_mdq.md` (nine Frozen plans) is a sequencing dependency, not a conflict: this plan owns the availability, health, stats, error-code, and audit statements in that file.
- `grimp` reports no production importer of any `mcp_servers.mdq` module, so response-shape changes are consumed only by the tests named in the plan.

## Design decisions
- One availability function parameterized by tool name is the single source of truth for both `/v1/tools` and `call_tool`; dispatch re-evaluates it at call time instead of trusting the discovery response.
- Audit emission is one `AuditEmission` created in `call_tool()` and emitted from its single `finally`; exception handlers render transport only.
- Domain failures are rendered from the closed code vocabulary, not from `type(exc).__name__`.

## Alternatives considered
- Keep the per-handler `_audit_log()` call and add a guard so the `ExecutionContextError` branch also audits — rejected: two emission sites remain, which is the behavior the requirement removes.
- Cache the availability result per request — rejected: the requirement is re-evaluation at call time, and the allowlist can change between discovery and dispatch.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_server.py`

### Procedure
- Make `_mdq_tool_availability()` (line 112) use `tool_name`: path-dependent tools are disabled when `allowed_dirs` is empty; `grep_docs` is additionally disabled when grep is configured off.
- Pass the actual tool name at `/v1/tools` (line 391 passes `""` today) so each entry is annotated per tool.
- In `call_tool()`, evaluate availability for `req.name` before dispatch and return `is_error=true` with code `tool_disabled` when it is disabled.
- Replace the two `_audit_log()` calls in `call_tool()` (lines 426 and 444) with one `AuditEmission` emitted from a single `finally`.
- Remove the `_audit_log()` call from `_mdq_error_handler()` (line 125).
- Read the shared startup configuration result from `scripts/mcp_servers/mdq/startup_config.py` instead of `_load_auth_token()` (line 77).
- Step 3b correction: the gate is placed inside `_dispatch_mdq_tool()`, not as a separate check in `call_tool()` before the call. `call_tool()` is the HTTP entry only; `tests/mcp_servers/mdq/test_mdq_disabled_tools.py` (seq 13) asserts the programmatic entry also refuses, so evaluating in the shared dispatch entry satisfies AC-1 for both paths. `call_tool()` reads the returned `MdqDispatchResult`, whose `outcome` is `rejected` for a refusal.
- Step 3b correction (response shape, user decision 20261128): `CallToolResponse` has no code field, so a tool-level failure returns `result=code` and the transport handler returns `{"detail": code}`. This requires one assertion change in `tests/mcp_servers/mdq/test_mdq_authentication.py` line 90, a file not in the plan's Target Files table: the authorization test now asserts `body["result"] == "authorization_error"` instead of the exception text.
- Step 3b correction: `_mdq_tool_availability()` reads `allowed_dirs` and `enable_grep` from the `MdqService` instance rather than a config mapping, because the Phase 1 test files patch only `mdq_server._service`. All seven MDQ tools serve content under the authorized roots, so an empty allowlist disables every tool; `grep_docs` is additionally disabled when `enable_grep` is false.
- Step 3b correction: `call_tool()` catches `MdqServiceError` broadly and re-raises the classes that keep a transport status (400/403/404/503/503/500/500), so the single `finally` is the only emission site; the four tool-level classes are answered at HTTP 200 from inside `call_tool()` and never reach the handlers.
- Step 3b correction: `load_startup_config()` is called at import, so a missing production configuration is a pre-bind failure. The two startup assertions in `tests/mcp_servers/mdq/test_mdq_authentication.py` still pass: the field-path message `_reject_empty()` builds contains `auth_token is empty`, and the unset-variable message names `MCP_MDQ_AUTH_TOKEN`.
- Step 3b correction: `test_mdq_exception_handlers.py` is rewritten to read records from the module logger sink rather than patching `mdq_server._audit_log`, which no longer exists in the module, and its `error_type` assertions now name codes rather than exception-class names.

### Method
- The emission boundary is created before the dispatch call so the `ExecutionContextError` branch (line 412), which emits nothing today, is covered by the same `finally`.
- The refusal is returned before `_dispatch_mdq_tool()` is called, matching `scripts/mcp_servers/web_search/web_search_server.py` (line 332 emits `tool_disabled`).
- Detail and target values written to the emission come from `scripts/mcp_servers/mdq/audit_target.py` (seq 03), which already returns redacted values.

### Details
- The `finally` must emit once for every path, including the refusal path and the `ExecutionContextError` path.
- Handler responses keep the documented transport shape (HTTP 200 with `is_error=true` for tool-domain failures); only transport-level statuses stay in the handlers.
- `_enforce_posture_gate()` (line 537) runs only under `__main__` today; the gate itself is unchanged by this document, but it must read the shared configuration result.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_exception_handlers.py`
  - Procedure: replace the assertion at line 66 that the handler calls `_audit_log()` with assertions that handlers render transport only and that tool responses carry the stable code.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_exception_handlers.py`

## Compatibility considerations
- `tests/mcp_servers/mdq/test_mdq_server.py` and `tests/mcp_servers/mdq/test_mdq_disabled_tools.py` (seq 12, 13) are new files written in Phase 1 before this change, so they pin the current disagreement and then pass after it.
- No production consumer reads the response shape outside the tests; the transport status codes stay unchanged for transport-level failures.

## Security considerations
- The audit record must not carry raw query, regex, or absolute-path values; this document relies on the redacted target from seq 03.
- Exactly-one-record behavior is a security requirement (AC-3), not only a logging cleanup: the boundary must not be bypassed by an early return.

## Rollback considerations
- Revert the commit; the companion test file and the two new Phase 1 test files fail immediately after a revert, which is the expected characterization-test state.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_server.py tests/mcp_servers/mdq/test_mdq_disabled_tools.py tests/mcp_servers/mdq/test_mdq_exception_audit.py tests/mcp_servers/mdq/test_mdq_exception_handlers.py`
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports` and `uv run python tools/check_module_size.py` (the module is 20547 B against the 24576 B gate).

## Completion criteria
- Discovery and dispatch report the same availability for the same tool name.
- A disabled tool is refused before the handler with code `tool_disabled`.
- Exactly one audit record is emitted for every authenticated call, including the malformed-execution-context path.
- No handler emits an audit record.

## Out of Scope
- The error-code vocabulary itself (seq 08), the path-identifier helper (seq 10), and the audit-target redaction (seq 03).
- Health and stats response shape (seq 04, seq 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | gate moved into `_dispatch_mdq_tool()`; one `AuditEmission` in `call_tool()`'s `finally`; handlers transport-only; responses carry codes; `load_startup_config()` replaces `_load_auth_token()` |
| 2 | Add or update tests per Validation plan | Completed | 20261128 | 20261128 | `test_mdq_exception_handlers.py` rewritten on the logger sink; `test_mdq_authentication.py:90` asserts the code; `test_mdq_disabled_tools.py` programmatic test patches the module singleton; 16 passed in the four targeted files, `test_mdq_authentication.py` 13 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-093658 | 20261128-093658 | ruff / mypy / `lint-imports` / `check_module_size` Pass; the full suite runs once at the end of the release unit (`boundary-characterization-tests`) end-of-unit gate 20261128: full suite 16357 passed / 4 skipped / 6 failed; the 6 are pre-existing failures in tests/mcp_servers/git/ and tests/mcp_servers/file/ files not in this unit's diff. Batch coverage over the unit's changed files: 98% (>=90). ruff/bandit/pre-commit Pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Documentation is a separate row (seq 27) |

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
- **Requirement ID**: REQ-001 (per-tool availability), REQ-004 (closed error codes), REQ-005 (single audit boundary), REQ-007 (shared startup configuration)
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `scripts/mcp_servers/mdq/mdq_server.py`, `tests/mcp_servers/mdq/test_mdq_exception_handlers.py`
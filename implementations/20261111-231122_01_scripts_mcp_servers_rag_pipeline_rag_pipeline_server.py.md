## Goal

Close the one verified server-side audit gap: make `rag_delete_document` (and every other rag-pipeline-mcp tool) emit the shared `mcp_tool_exec` audit record from `call_tool`, for both `ok` and `error` outcomes (`REQ-001`, `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The server's existing module-level `logger` (`Logger(__name__, "/opt/llm/logs/rag-mcp.log")`) is the correct sink; the record lands there like cicd-mcp's record lands in its application log (`mcp_06_05` "Layer 2").
- `extract_request_context(request)` returns `(session_id, request_id, idempotency_key)`; the current code discards the first two (`_, _, idempotency_key = ...`) and must capture them.
- `DispatchResult.outcome` carries the `ok`/`error` taxonomy; `error_type` stays at its default because `DispatchResult` owns its own failure taxonomy.
- "Not found" is reported by `fmt_delete_document` as a normal result (outcome `ok`), so it is audited as `ok`, not `error`.
- `target` carries the document URL (truncated to 80 chars) only for `rag_delete_document`; query tools carry an empty `target` because query text may contain user content.

## Design decisions
- Reuse the shared helper `mcp_servers.audit._audit_log()` exactly as cicd-mcp and github-mcp do: one record per executed `call_tool`, `outcome` taken from `DispatchResult`, no new field and no second format.
- Place the call after `r = await _dispatch_rag_tool(...)` and before `return _to_call_tool_response(r)`, mirroring `cicd_server.py:174-186`, so a call rejected at the availability gate (before dispatch) writes no record, matching cicd-mcp and github-mcp.
- Import direction `rag_pipeline_server -> mcp_servers.audit` matches the existing `cicd_server`/`github_server` dependency direction; `audit.py` imports only `shared.logger` and `orjson`, so no new import cycle.

## Alternatives considered
- Emitting from `dispatch_tool` in `scripts/mcp_servers/dispatch.py`: would audit every server, double-record servers that already audit, and widen the blast radius. Rejected.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`

### Procedure
1. Add `from mcp_servers.audit import _audit_log` to the `mcp_servers.*` import block (after line 34, alongside the `dispatch` import).
2. In `call_tool` (line 336), change the context unpack on line 341 from `_, _, idempotency_key = extract_request_context(request)` to `session_id, request_id, idempotency_key = extract_request_context(request)`.
3. After the dispatch assignment on line 342, insert the `_audit_log(...)` call; keep the `return _to_call_tool_response(r)` on line 343.
4. Compute `target`: for `req.name == "rag_delete_document"` use `str(req.args.get("url", ""))[:80]`; otherwise `""`.

### Method
```python
    session_id, request_id, idempotency_key = extract_request_context(request)
    r = await _dispatch_rag_tool(req.name, req.args, idempotency_key=idempotency_key)
    _target = str(req.args.get("url", ""))[:80] if req.name == "rag_delete_document" else ""
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=_target,
        outcome=r.outcome,
        server_key="rag_pipeline",
    )
    return _to_call_tool_response(r)
```

### Details
- `action=req.name` records the tool name; `server_key="rag_pipeline"` identifies the emitting server.
- `error_type` is left at its default (`""`) because `DispatchResult` carries its own taxonomy; set it only if `DispatchResult` exposes one (verified at implementation).
- No argument or result fields other than the truncated URL are recorded, so the record contains no document content (`AC-1`).
- The audit call sits after `dispatch_tool`, so each request is audited once with its own `request_id`; the replayed `rag_delete_document` (retryable in `config/mcp_dedup.toml`) is audited once per request.

### Companion test files
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`
  - Procedure: add audit-emission assertions under `TestCallToolEndpoint` — capture `logger.info` for `rag_delete_document` success, for "Not found" (outcome `ok`), and for a handler error (outcome `error`); assert no record when the tool is disabled (`TestCallToolDisabledGate`); assert the record carries no document content and carries `server_key="rag_pipeline"`, `session_id`, `request_id`, `tool`, `target`.
  - Validation: `uv run pytest tests/mcp_servers/rag_pipeline -v` passes.

## Compatibility considerations
- Importers of `rag_pipeline_server` (`rag_pipeline/__init__.py`, `rag_pipeline_health_probe.py`, seven test modules) see no behavior change; the audit record format is unchanged.
- The existing `TestCallToolDisabledGate` and `TestCallToolEndpoint` tests lock the wiring layer; the new assertions extend them without altering responses.

## Security considerations
- `target` is the document URL truncated to 80 characters; nothing else from the arguments or result is recorded, so no document content or secret leaks into the audit log.
- The disabled-tool rejection path still writes no record, consistent with the security intent that a pre-dispatch rejection is not misclassified into the audit taxonomy.

## Rollback considerations
Revert the commit to `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (restores the discard-only `call_tool`).

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `rag_pipeline_server.py` audit emission | Unit (endpoint audit capture) | `uv run pytest tests/mcp_servers/rag_pipeline -v` | Pass |
| Format/lint/type/security | Static | `uv run ruff format`, `ruff check`, `uv run mypy`, `bandit -r scripts/mcp_servers/rag_pipeline -c pyproject.toml` | Clean |
| Module size | Size gate | `uv run python tools/check_module_size.py` | Pass (15792 B < 24576 B gate) |

## Completion criteria
- `call_tool` calls `_audit_log(...)` exactly once per dispatched call with `server_key="rag_pipeline"`, `session_id`/`request_id` from `extract_request_context()`, `action=req.name`, `target` = the `rag_delete_document` URL truncated to 80 chars (empty otherwise), `outcome=r.outcome`.
- A disabled tool (rejected before dispatch) writes no record.
- The captured record contains no document content.

## Out of Scope
- Adding a `principal` field or any other change to the audit record format.
- Changing the audit sink or moving the call to `dispatch.py`.
- The cross-server completeness test (`tests/mcp_servers/test_write_dangerous_audit.py`) — covered by its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_audit_log` import and the audit call in `call_tool` (REQ-001) | Pending | — | — | Follows cicd-mcp pattern |
| 2 | Add audit-emission tests to `test_rag_pipeline_server_endpoints.py` | Pending | — | — | success / not-found / error / disabled / no-content |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` — emit one shared `mcp_tool_exec` record per executed rag-pipeline-mcp call through `_audit_log()` for both `ok` and `error` outcomes.
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-231122
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`

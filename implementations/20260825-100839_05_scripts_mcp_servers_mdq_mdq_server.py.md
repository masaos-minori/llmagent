## Goal
- Compute real per-tool `enabled`/`disabled_reason` for `mdq-mcp`'s tools based on
  `allowed_dirs` (REQ-004), and thread `include_disabled`/`disabled_code` through
  `list_tools()` into `build_tools_response()` (REQ-005).

## Scope
- In scope: `list_tools()` and a new `_mdq_tool_availability()` helper in
  `scripts/mcp_servers/mdq/mdq_server.py`.
- Out of scope: `call_tool()` (see Design decisions for why no gate is added there);
  `MdqService`/`auth.py`'s `authorize_path()` enforcement (already correct and
  unchanged).

## Assumptions
- `mdq_server.py` has no module-level `MdqConfig` object; `allowed_dirs` is only
  reachable through the module-level `_service: MdqService = MdqService()`
  singleton's `.allowed_dirs` property. The new helper therefore takes
  `_service.allowed_dirs`, not a `_cfg` dataclass, unlike the other three target
  servers.
- All tools (`search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`,
  `stats`, `grep_docs`) are gated uniformly, even though `stats` does not itself call
  `authorize_path()` — chosen for consistency with the file-servers' whole-service
  gate and because `MdqService.__init__`'s own warning frames empty `allowed_dirs` as
  effectively disabling the server's usefulness.

## Design decisions
- `_mdq_tool_availability(allowed_dirs: list[str], tool_name: str) -> tuple[bool, str]`: return `(False, "allowed_dirs is empty")` when `allowed_dirs` is empty, else
  `(True, "")`. `tool_name` is accepted (unused today) to keep the signature
  consistent with the other three servers' per-tool helpers.
- Do **not** add a `call_tool()` disabled-tool gate for `mdq`, unlike the other three
  target servers: `mdq`'s existing per-operation `MdqAuthorizationError` (raised by
  `authorize_path()`, mapped by `_on_mdq_authorization_error` to an HTTP 403 with
  mdq's own structured audit log) already fails closed with richer, tool-specific
  detail than a blanket "Tool disabled" message would provide.

## Alternatives considered
- Adding a uniform `call_tool()` gate matching git/web_search/cicd/rag_pipeline —
  rejected; it would regress `mdq`'s existing, more specific
  `MdqAuthorizationError` → HTTP 403 → structured audit-log path into a generic
  200/`is_error=True` response, a behavior change beyond REQ-004/REQ-005's scope.
- Gating only the path-based tools (all but `stats`) — rejected in favor of the
  simpler whole-service gate, consistent with file-servers.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_server.py`

### Procedure
1. Add `_mdq_tool_availability(allowed_dirs, tool_name)` near `_dispatch_mdq_tool()`.
2. Add `_annotate_tool(tool, allowed_dirs)` returning `{**tool, "enabled": ..., "disabled_reason": ...}`.
3. Update `list_tools()` to accept `include_disabled: bool = False, disabled_code: str | None = None`, annotate `TOOL_LIST` using `_service.allowed_dirs`, and call
   `build_tools_response(annotated, "mdq", include_disabled=include_disabled, disabled_code=disabled_code)`.

### Method
- Structurally mirror the file-servers' `_annotate_tool(tool, enabled, disabled_reason)` pattern (a single enabled/reason pair reused across all
  tools), since `mdq`'s gate — like the file servers' — is whole-service rather than
  per-tool.

### Details
- No new imports required; `_service` is already the module-level singleton.
- FastAPI query-parameter wiring identical to the other three target files.

## Compatibility considerations
- Existing `tests/mcp_servers/mdq/test_mdq_routing.py::TestMdqV1ToolsEndpoint` cases
  continue to pass as long as the test environment's `allowed_dirs` is non-empty (or
  the tests are extended to assert `enabled` explicitly).
- No change to `call_tool()` means no behavior change for existing callers beyond
  `/v1/tools` metadata.

## Security considerations
- `/v1/tools` now accurately reflects that all tools are effectively unusable when
  `allowed_dirs` is empty, instead of always reporting them as available.

## Rollback considerations
- Fully revertible by reverting `mdq_server.py`; no config/schema changes.

## Validation plan
| Target | Test | Expected |
|---|---|---|
| `list_tools()` | `tests/mcp_servers/mdq/test_mdq_routing.py::TestMdqV1ToolsEndpoint` (extend) | `_service.allowed_dirs == []` → all tools report `enabled=False`, reason `"allowed_dirs is empty"`; non-empty `allowed_dirs` → all report `enabled=True`, reason `""` |
| `include_disabled`/`disabled_code` | same file, new case | `include_disabled=false` omits all tools when `allowed_dirs` is empty; `disabled_code="allowed_dirs is empty"` matches all of them in that state |
| Regression | `uv run pytest tests/mcp_servers/mdq/ -v` | All existing cases pass unmodified |

## Out of scope
- Any `call_tool()` behavior change (see Design decisions).
- A per-tool (path-based vs. not) gating split — deferred.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no doc update required by this item |

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
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/mcp_servers/mdq/mdq_server.py

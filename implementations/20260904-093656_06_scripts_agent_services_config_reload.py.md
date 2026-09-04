## Goal
Document that `auth_token` changes require a full process restart, by
extending the existing `needs_restart` classification's documentation to
explicitly name `auth_token`.

## Scope
- **In-Scope**: `_MCP_SERVER_FIELDS` (verified 2026-09-04, lines 96-107,
  already includes `"auth_token"` at line 103) and
  `_classify_mcp_server_changes()` (lines 508-537, whose `needs_restart`
  population already covers any changed field in `_MCP_SERVER_FIELDS`,
  including `auth_token`) — docstring/comment additions only, no logic
  change.
- **Out-of-Scope**: `_diff_mcp_server_config()` (lines 110-120),
  `ConfigReloadOutcome`'s other fields (`applied`, `skipped`, `source_files`,
  `startup_only`, lines 123-139) — confirmed by direct read to be unrelated
  or already correctly documented for their own purposes.

## Assumptions
- **Corrected 2026-09-04** (`plan-to-implementation-procedure` Step 2/3
  revalidation): this Plan's original citation
  (`scripts/agent/services/config_reload.py:470-476`) pointed to
  `_apply_tool_params()`, an unrelated method (tool-execution setting
  reload, not MCP server field classification); the actual `needs_restart`
  logic this Plan's REQ-005 describes is `_MCP_SERVER_FIELDS` (line 103) and
  `_classify_mcp_server_changes()` (lines 508-537).
- REQ-005 requires no logic change — `needs_restart` already correctly
  flags a changed `auth_token` as `mcp_servers/{key}.auth_token` (via the
  existing per-field diff at line 533); this row's work is purely
  documentation (docstrings/comments) making that existing behavior's
  intentionality explicit for `auth_token` specifically.

## Design decisions
- Add a comment next to `_MCP_SERVER_FIELDS`'s `"auth_token"` entry (line
  103) explicitly stating that this field's restart-only status is
  intentional per this Plan's REQ-005 (a security-token change must not
  take effect via a live `/reload`, which could otherwise leave a stale
  `HttpTransport` instance holding an outdated credential mid-session).
- Extend `_classify_mcp_server_changes()`'s docstring (lines 513-518) to
  name `auth_token` explicitly as an example of a security-sensitive
  restart-only field, alongside its existing general "MCP server
  definitions are restart-time snapshots" explanation.

## Alternatives considered
- Moving `auth_token` out of `_MCP_SERVER_FIELDS` into a new, separate
  "security-sensitive restart-only fields" list: rejected — REQ-005 is a
  confirm-and-document requirement, not a request to restructure the
  existing classification mechanism; `_MCP_SERVER_FIELDS`'s uniform
  treatment of all MCP-server fields as restart-only is already correct and
  sufficient for `auth_token`'s needs.

## Implementation
### Target file
`scripts/agent/services/config_reload.py`

### Procedure
1. Add an inline comment after `"auth_token",` in `_MCP_SERVER_FIELDS`
   (verified 2026-09-04, line 103) noting its restart-only status is
   intentional (security-sensitive credential, per REQ-005).
2. Extend `_classify_mcp_server_changes()`'s docstring (lines 513-518) to
   name `auth_token` as an explicit example.

### Method
Direct `Edit` at the two sites above.

### Details
Current (verified 2026-09-04, lines 96-107):
```python
_MCP_SERVER_FIELDS = (
    "transport",
    "url",
    "startup_mode",
    "call_timeout_sec",
    "startup_timeout_sec",
    "tool_names",
    "auth_token",
    "role",
    "cmd",
    "env",
)
```
After:
```python
_MCP_SERVER_FIELDS = (
    "transport",
    "url",
    "startup_mode",
    "call_timeout_sec",
    "startup_timeout_sec",
    "tool_names",
    "auth_token",  # restart-only, intentional: a live credential change must not apply mid-session
    "role",
    "cmd",
    "env",
)
```
Current (verified 2026-09-04, lines 508-519):
```python
def _classify_mcp_server_changes(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> ConfigReloadOutcome:
    """Classify MCP server definition changes as restart-required, field by field.

    MCP server definitions are restart-time snapshots: ToolExecutor and
    HttpTransport are built from them at startup, so mutating
    `ctx.cfg.mcp.mcp_servers` here would desync already-running instances
    from the reported config. This method only compares; it never writes.
    """
```
After:
```python
def _classify_mcp_server_changes(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> ConfigReloadOutcome:
    """Classify MCP server definition changes as restart-required, field by field.

    MCP server definitions are restart-time snapshots: ToolExecutor and
    HttpTransport are built from them at startup, so mutating
    `ctx.cfg.mcp.mcp_servers` here would desync already-running instances
    from the reported config. This method only compares; it never writes.

    auth_token in particular is restart-only by design: a live /reload must
    never apply a changed credential to an already-running HttpTransport
    instance mid-session.
    """
```

## Compatibility considerations
None: documentation/comment-only edit, no behavioral change.

## Security considerations
This row documents (does not change) the existing restart-only enforcement
for `auth_token`, supporting REQ-005/AC-6.

## Rollback considerations
Docstring/comment-only edit under version control; revert via `git revert`
if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload.py -v` | Existing tests pass unchanged; `auth_token` changes still classified as `needs_restart` |

## Completion criteria
`_MCP_SERVER_FIELDS` and `_classify_mcp_server_changes()`'s documentation
explicitly name `auth_token` as an intentional restart-only field.

## Out of scope
`_diff_mcp_server_config()`, `ConfigReloadOutcome`'s other fields.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Documentation-only; no logic change |
| 2 | Add or update tests per Validation plan | N/A | — | — | No new test required — existing `test_config_reload.py` coverage already exercises the unchanged logic |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Plan's Documentation Impact: Yes — restart/hot-reload guidance docs, sequenced after this Plan lands |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260902-143335_mcpauth_preserve_mandatory_mcp_authentication_under_loopback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-092407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-093656
- **Related target files**: scripts/agent/services/config_reload.py

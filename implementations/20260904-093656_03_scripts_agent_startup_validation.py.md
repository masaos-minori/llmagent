## Goal
Add a pre-discovery startup-time check that every configured HTTP MCP
server's `auth_token` is non-empty, failing startup with a clear error
identifying which server(s) lack a token.

## Scope
- **In-Scope**: `StartupValidationPipeline.check_services()` (verified
  2026-09-04, lines 32-94), specifically the insertion point between "1.
  Security audit" (line 43) and "4. MCP tool discovery" (line 68).
- **Out-of-Scope**: "2. Service readiness" (lines 56-66), "5. Routing
  drift"/"5b. Routing safety tiers" (lines 95-113), "6. RAG consistency"
  (lines 115-129) — confirmed by direct read to be unrelated to
  authentication.

## Assumptions
- **Corrected 2026-09-04** (`plan-to-implementation-procedure` Step 2/3
  revalidation): this Plan's original target file,
  `scripts/agent/startup.py:330-334`, no longer contains this logic — an
  unrelated upstream refactor (documented in
  `plans/done/20260903-091417_plan.md` Background) split `startup.py`'s
  ~370-line body into `startup_validation.py` (this row),
  `services/mcp_health.py`, `shared/retry_helper.py`, and
  `startup_mcp_starter.py`; `startup.py` itself is now 140 lines with no
  security-audit or discovery logic (confirmed: it only delegates via
  `self._validation_pipeline.check_services()`).
- Coupled to row 1 (`scripts/shared/mcp_config.py`) — this row's check reads
  `ctx.cfg.mcp.mcp_servers[*].auth_token`, values already resolved through
  row 1's environment-variable resolution and dataclass-level non-empty
  validation; this row's own check is the earlier-failing, discovery-
  specific enforcement point per the Plan's Design section (fails before
  `McpToolDiscoveryService(ctx).discover_all()` runs, at step 4, line 73).

## Design decisions
- Insert a new numbered step ("1b. MCP authentication check" or similar,
  between the existing "1. Security audit" comment at line 43 and "2.
  Service readiness" at line 56) that iterates
  `ctx.cfg.mcp.mcp_servers.items()` and collects every server key whose
  `auth_token == ""`, adding a single `pipeline.add_fatal("mcp_auth", ...)`
  entry naming all offending server keys if any are found — one aggregated
  fatal message, not one per server, so a misconfigured deployment gets one
  clear, complete error rather than a truncated first-failure message.
- Place this check before "4. MCP tool discovery" (not merely "somewhere in
  the pipeline") per REQ-001's explicit "before tool discovery begins"
  requirement — inserting it as its own early step (rather than folding it
  into the existing "1. Security audit" try/except block) keeps this
  Plan's change isolated from `security_audit.py`'s own logic, which
  `plans/done/20260903-091417_plan.md` already substantially modified for
  an unrelated requirement (REQ-005/REQ-008 there) — avoids two Plans
  editing the same function body for unrelated reasons.

## Alternatives considered
- Adding the check inside `scripts/agent/services/security_audit.py`'s
  `audit_security_defaults()` (already a per-server auth-token consumer,
  per its `production_mode`-gated `auth_token`-violation check at line 88,
  confirmed by the `localremoval` Plan's investigation): rejected — that
  function's existing violation check only downgrades to a *warning* in
  non-production mode (soon to be unconditionally fatal per
  `plans/done/20260903-091417_plan.md` REQ-005/REQ-008, but that Plan's
  scope is unrelated to this Plan's REQ-001, which requires unconditional
  rejection regardless of environment/profile); keeping this row's check
  separate avoids entangling two independently-scoped Plans' logic in one
  function body.

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
1. Add a new step between "1. Security audit" (line 43-54) and "2. Service
   readiness" (line 56-66) that iterates `ctx.cfg.mcp.mcp_servers.items()`,
   collects keys with an empty `auth_token`, and calls
   `pipeline.add_fatal("mcp_auth", ...)` with a message naming every
   offending server key, if any.
2. If no server has an empty token, call `pipeline.add_ok("mcp_auth")` for
   symmetry with the other steps' `add_ok()` calls.

### Method
Direct `Edit`, inserting a new code block.

### Details
Current (verified 2026-09-04, lines 43-56):
```python
        # 1. Security audit
        try:
            warnings = audit_security_defaults(ctx, production_mode=production_mode)
            for msg in warnings:
                pipeline.add_warning("security_audit", msg)
            pipeline.add_ok("security_audit")
        except RuntimeError as exc:
            pipeline.add_fatal(
                "security_audit",
                str(exc),
                remediation="Fix MCP server auth_token or sandbox config.",
            )

        # 2. Service readiness
```
After (illustrative; exact `ctx.cfg.mcp.mcp_servers` access pattern to be
confirmed against `AgentContext`'s actual structure at execution time):
```python
        # 1. Security audit
        try:
            warnings = audit_security_defaults(ctx, production_mode=production_mode)
            for msg in warnings:
                pipeline.add_warning("security_audit", msg)
            pipeline.add_ok("security_audit")
        except RuntimeError as exc:
            pipeline.add_fatal(
                "security_audit",
                str(exc),
                remediation="Fix MCP server auth_token or sandbox config.",
            )

        # 1b. MCP authentication check
        missing_auth = [
            key
            for key, srv in ctx.cfg.mcp.mcp_servers.items()
            if not srv.auth_token
        ]
        if missing_auth:
            pipeline.add_fatal(
                "mcp_auth",
                f"MCP server(s) missing auth_token: {', '.join(sorted(missing_auth))}",
                remediation="Set a non-empty auth_token (via environment variable) for every MCP server before startup.",
            )
        else:
            pipeline.add_ok("mcp_auth")

        # 2. Service readiness
```
Note: since row 1's `_validate_auth_token()` already rejects an empty token
at `McpServerConfig` construction time, this startup-time check may in
practice be unreachable once row 1 lands (construction would already have
failed earlier, during config loading). Re-confirm at execution time
whether `AgentContext`/`build_agent_config()`'s error path surfaces a
config-construction failure before or after this pipeline runs; if
construction-time rejection (row 1) already covers every path this check
would catch, implement this step as a defense-in-depth confirmation
(re-asserting the invariant, per REQ-001's own "identify which server(s)
lack a token" wording) rather than removing it — REQ-001 explicitly
requires this check to exist "before tool discovery begins" regardless of
whether row 1's earlier construction-time check already makes the failure
path unreachable in practice.

## Compatibility considerations
Coupled to row 1 — both rows enforce the same invariant at different
points; must land together per the Plan's Risks section.

## Security considerations
This row is the core startup-time enforcement of REQ-001/AC-2 (Agent
startup rejects MCP discovery when any configured server's `auth_token` is
missing or empty).

## Rollback considerations
Small, localized insertion under version control; revert via `git revert`
if needed, together with row 1.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_validation.py` | Unit + Integration | `uv run pytest tests/agent/test_startup.py tests/agent/shared/test_startup_validation_pipeline.py -v` | Startup fails before discovery when any server's token is empty, naming the offending server(s) |

## Completion criteria
`check_services()` fails with a FATAL pipeline outcome, before MCP tool
discovery runs, whenever any configured server's `auth_token` is empty.

## Out of scope
"2. Service readiness", "5. Routing drift", "5b. Routing safety tiers", "6.
RAG consistency".

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Coordinate with row 1; confirm reachability relative to row 1's construction-time check at execution time |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by row 12 (`tests/agent/test_startup.py`) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Plan's Documentation Impact: Yes — MCP/Agent domain mapping docs, sequenced after this Plan lands |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260902-143335_mcpauth_preserve_mandatory_mcp_authentication_under_loopback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-092407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-093656
- **Related target files**: scripts/agent/startup_validation.py

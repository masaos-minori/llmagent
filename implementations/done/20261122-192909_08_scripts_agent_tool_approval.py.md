## Goal

Source approval-grant expiry from `AgentConfig.approval_grant_ttl_seconds` instead of the module constant, keeping the constant as the identical default (REQ-002).

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- Field per seq 05; callers that construct grants from a config context pass the value, direct/test constructions keep the constant default.

## Design decisions
- `_issue_grant()` (lines 239-254) gains a lifetime parameter defaulting to `_GRANT_TTL_SECONDS` (300.0, line 51) so `expires_at=now + lifetime` is unchanged by default (AC-005 equality).
- The config-carrying call path (the approval entry point that has `AgentConfig` in scope) reads `cfg.approval_grant_ttl_seconds` at call time.

## Alternatives considered
- Reading `AgentConfig` inside `tool_approval` directly: rejected — keeps a hidden config dependency in a leaf module; the plan wires config through explicit parameters like `pending_timeout_minutes` is wired in the workflow engine.

## Implementation
### Target file
`scripts/agent/tool_approval.py`
### Procedure
1. Add a `grant_ttl_seconds: float = _GRANT_TTL_SECONDS` parameter to `_issue_grant()` and use it at line 254.
2. At the public approval entry point(s) that receive the Agent config context, pass `approval_grant_ttl_seconds` through to `_issue_grant()`.
### Method
Trace the existing call chain to `_issue_grant()` once (module-internal) and thread one existing config value along it; no new context objects.
### Details
- Keep `_GRANT_TTL_SECONDS` as the documented fallback default (row 8).

### Companion test files
- `tests/agent/test_tool_approval_paths.py`
  - Procedure: assert grant expiry equals `AgentConfig.approval_grant_ttl_seconds` when configured, and equals the 300.0 default when absent (behavior-lock equality, AC-005).
  - Validation: `uv run pytest tests/agent/test_tool_approval_paths.py -q`.

## Compatibility considerations
- Default-valued parameter keeps every existing caller and test green until the config path is exercised.

## Security considerations
- Grant lifetime remains bounded (validator range, seq 07); no path can extend grants beyond 3600 s in production.

## Rollback considerations
- N/A: revert the commit; grants in flight keep their stored expiry semantics.

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_paths.py -q`; `uv run mypy scripts/agent/tool_approval.py`.

## Completion criteria
- Grant expiry follows the config value when present, equals 300.0 otherwise; no behavior change for unconfigured deployments.

## Out of Scope
- Grant store/schema (unchanged); approval risk floors (unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the grant-lifetime threading | Completed | 2026-11-22 | 2026-11-22—run_approval_checks threads ctx.cfg value|
| 2 | Add or update companion tests per Validation plan | Completed | 2026-11-22 | 2026-11-22—run_approval_checks threads ctx.cfg value|
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22—run_approval_checks threads ctx.cfg value|

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
- **Requirement ID**: REQ-002; AC-005
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `scripts/agent/tool_approval.py`, `tests/agent/test_tool_approval_paths.py`

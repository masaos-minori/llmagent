# Move MCP security validation to per-server self-validation + posture contract

## Priority
High

## Summary
Replace the Agent's startup security audit that reads each MCP server's config file
with per-server self-validation plus a versioned, non-secret Security Posture contract
that each server exposes and the Agent validates. This removes the Agent's cross-config
read (shrinking ADR-002's exception instead of growing it), keeps REQ-001 / config
isolation / fail-closed intact, and follows ADR-002's Review Trigger for moving the
audit out of the Agent. Detailed implementation steps are defined in `memo2.md`; this
issue defines design intent and scope only.

## Background
- ADR-002 Decision #7 permits one exception: the Agent reads shell/git/github/cicd
  configs during startup via `agent/security_audit_config.py` loaders, narrowed to audit
  DTOs holding only security-posture fields.
- This conflicts with the orchestrator's restriction to `agent.toml` (REQ-001,
  `scripts/agent/context.py`; asserted in `tests/agent/test_context.py`). Satisfying
  REQ-001, cross-server isolation (`tests/agent/test_config_permission_cross_server.py`),
  and fail-closed (`tests/agent/test_audit_security_failures.py`) inside one restricted
  process is impossible; widening the allowlist weakens REQ-001.
- ADR-002 Review Triggers name the direction: "Each MCP server can enforce the audited
  settings itself at its own startup (the audit can then move out of the Agent)."
- Each server already calls `ConfigLoader.restrict_to(self.own_config_file)` in
  `MCPServer.run_http()` (`scripts/mcp_servers/server.py`), so it reads and can validate
  its own config fully. The precondition for self-validation exists today.

## Objective
- Each MCP server owns validation of its own configuration and technical safety,
  fail-closed before exposing HTTP, Tool Discovery, or Tool calls.
- The Agent stops reading `*_mcp_server.toml` and importing MCP server config models; it
  validates only a standardized, versioned Security Posture contract.
- Per-process configuration ownership (ADR-002) is strengthened, not weakened.

## Scope

### In scope
- Common platform: shared Security Validation result DTO, check status / reason code,
  security policy version, posture contract version, non-secret config fingerprint,
  common startup validation flow, health/readiness, Tool Discovery publish conditions,
  non-secret logging/diagnostics.
- MCP servers: Shell, Git, GitHub, CI/CD, File Read, File Write, File Delete, RAG
  Pipeline, MDQ, and any other HTTP MCP server the Agent uses.
- Agent: server start/connect, health/readiness probe, posture validator, failure
  classification, Tool Discovery gating, RuntimeToolRegistry construction, removal of the
  existing startup security audit, cross-config read, and MCP config-model imports.
- Tests: validation unit tests, server startup tests, health/posture contract tests,
  Agent integration tests, secret non-exposure tests, config-isolation regression,
  import-linter contract, Tool Discovery ordering, failure-classification tests.
- Docs: ADR-002, ADR-003, ADR-004, ADR-007, ADR-014, ADR index / invariant verification
  matrix, MCP health/startup/security docs, Agent startup/validation/troubleshooting docs,
  configuration reference, generated references.

### Out of scope
- stdio transport adoption.
- External network exposure of MCP servers.
- mTLS, PKI, remote attestation.
- Server binary signing, SBOM, provenance.
- RuntimeToolRegistry Hot Rediscovery.
- Changing the authentication mechanism between Agent and server.
- Changing tool approval policy.
- Comprehensive OS-user / container / service-management changes.
- Large-scale reorganization of server config keys.
- embed-llm readiness (separate, already addressed).
Changes that become necessary belong to a separate design change, not this work.

## Design / Responsibility Boundaries

### Server responsibilities
- Read only its own config file; validate schema and required keys; reject unknown keys.
- Enforce common security requirements: own-config-only, required secrets, loopback
  bind, HTTP transport, auth satisfied, timeout/output/resource limits valid,
  audit/redaction satisfied, no fail-open mitigation, valid tool schema.
- Enforce server-specific requirements: shell sandbox/command allowlist; git repo
  allowlist/protected branch/force-push; github repo/branch/destructive ops; cicd
  workflow/ref/inputs; file path boundary/symlink escape/write-delete limits; rag/mdq
  db/index/allowed dirs.
- Verify consistency between published tools and security settings. Never convert a
  Safety failure into a static `enabled=false`.
- Generate a non-secret Security Posture and expose it only after validation passes.

### Agent responsibilities (limited to)
- Confirm server identity.
- Validate posture schema, contract version, server key, presence and results of
  required checks, policy-version compatibility, fingerprint presence, and
  health/tool-discovery identity match.
- Classify failures and gate Tool Discovery and RuntimeToolRegistry registration.
- The Agent must NOT hold real allowlist values, filesystem paths, sandbox internals,
  server-specific secrets, or server-specific config models.

### Security Posture contract (design-level)
- Versioned and non-secret. Contains server key, policy version, check results, and a
  non-secret config fingerprint; never Secret, raw allowlist, sensitive path, or config
  file body.
- Tool Discovery and Tool Call are permitted only when `ready=true` and
  `security.validated=true`.

### Startup ordering principle
- All servers unify: Config Load -> Schema Validation -> Common Security Validation ->
  Server-Specific Security Validation -> Dependency Validation -> Tool Capability
  Consistency Validation -> Runtime State Installation -> HTTP Bind -> Ready.
- On validation failure, a server must not bind HTTP or return Ready.

### Failure classification
- Availability vs Safety vs Integrity. Missing/unreachable required server is Availability
  (abort startup); unreachable non-required server is Availability (partial availability
  only when conditions met). Posture schema invalid, unsupported contract version,
  server-key mismatch, missing/failing required check, and `validated=false` are
  Integrity/Safety (abort startup). A non-required server must never convert a
  Safety/Integrity failure into partial availability.

## Invariants
Existing INV-01..INV-04 retained. Add:
- INV-05: Every MCP server validates its own security configuration before reporting ready.
- INV-06: An MCP server whose security validation fails does not expose Tool Discovery or accept Tool calls.
- INV-07: The Agent does not read MCP-server configuration files or import MCP-server configuration models.
- INV-08: The Agent accepts an MCP server for Discovery only after validating its versioned security-posture contract.
- INV-09: Security-posture data contains no Secret or raw sensitive configuration value.

## Migration Strategy
- Shadow Validation: run the existing Agent audit and the new server self-validation in
  parallel during migration and compare results (MATCH_PASS / MATCH_FAIL /
  AGENT_ONLY_FAIL / SERVER_ONLY_FAIL / CHECKSET_MISMATCH / CONTRACT_ERROR) without
  emitting raw config values.
- Do not entrench a dual source of truth; make the new way canonical.
- Switch conditions: required checks implemented on all target servers; agent/server
  correspondence clear; no unresolved result deltas; same misconfig rejected server-side;
  no Secret leak in posture; health response compatible with existing monitoring.
- No implicit runtime fallback to the old audit; rollback to a known-good version instead.

## Constraints
- Must NOT weaken REQ-001: the orchestrator stays restricted to `agent.toml`.
- Must NOT weaken cross-server isolation: no code path re-adds the Agent reading MCP
  configs.
- Must NOT weaken fail-closed: empty required allowlists are fail-closed; each server
  aborts startup on invalid security config.
- Server validation must not load or expose other processes' Secrets. Preserve existing
  message masking; print no secrets.

## Open Items
- Lockdown: resolved per `memo2.md` priority — empty required allowlists are fail-closed;
  the previous `security_lockdown_enabled` deny-all warning suppression is retired. If
  the key must remain for backward compatibility, it no longer suppresses server-side
  validation.
- Any remaining genuine open questions are recorded here during implementation.

## Doc Impact
Update ADR-002 (remove cross-config-read exception; add per-server self-validation
decision; make "Agent does not read server config" and "posture has no Secret"
invariants), ADR-003 (posture-gated /v1/tools, no registration of failing servers,
distinguish self-validation failure from static tool disable, no Hot Rediscovery),
ADR-004 (posture failures as Safety/Integrity, non-required servers still abort, separate
unreachable from unsafe, keep subprocess exception), ADR-007 (posture contract on /health,
readiness conditions, auth requirement, no Tool Discovery before validation, HTTP-only),
ADR-014 (server owns its validation, Agent validates only the common contract, does not
replicate server-specific safety). Update ADR index and invariant verification matrix;
update generated references from their source.

## Completion Criteria
- Design: each server defined as owner of its own validation; Agent/server boundary
  matches ADR-014; Safety/Integrity vs Availability clearly separated; Tool Discovery
  only after posture validation; no implicit fallback to old way.
- Implementation: all target servers implement self-validation and return the common
  posture; no ready/tool-discovery/tool-call on security failure; Agent discovers only
  after posture validation; no Agent read of server configs or import of server models;
  only the common posture validator remains in the Agent; cross-config read removed;
  import-linter exception removed.
- Security: posture has no Secret/raw allowlist/sensitive path; logs/exceptions/
  diagnostics have no Secret; non-required servers fail-closed; no HTTP ready endpoint
  exposed on validation failure; server and posture identities match.
- Tests: common-contract, per-server startup, health/posture, Agent integration,
  config-isolation regression, secret non-exposure, shadow-validation with no unresolved
  delta, import-linter all pass.
- Docs: ADR-002 exception removed; ADR-003/004/007/014 aligned; index/invariant matrix
  updated; MCP and Agent docs updated; no description retains the old audit as current
  spec; generated references regenerated.
- Operations: reason codes confirmable in ops runbook; monitoring/alert defined;
  re-validation/re-discovery/restart and rollback conditions specified; no automatic
  return to old way on security failure.

## Dependencies
N/A: none. Sibling-issue check clean — no open issue covers moving the audit out of the
Agent.

## Implementation Source
Detailed implementation steps, exact DTO fields, reason codes, `/health` shape, and
per-server check lists live in `memo2.md` (MCP Server自己セキュリティ検証 移行作業指示書,
2026-10-15). This issue defines design intent and scope only; do not duplicate that
detail here.

## Traceability
- **Workflow phase**: issue-creator (design/scope)
- **Source directive**: `memo2.md` (2026-10-15)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Generated at**: 20261015-102802
- **Updated at**: 20261015-140500 (scoped to design/scope per memo2.md priority; lockdown
  resolved to fail-closed; scope expanded to all HTTP servers; invariants INV-05..INV-09)
- **Related target files**: scripts/mcp_servers/shell/, scripts/mcp_servers/git/, scripts/mcp_servers/github/, scripts/mcp_servers/cicd/, scripts/mcp_servers/file/, scripts/mcp_servers/rag_pipeline/, scripts/mcp_servers/mdq/, scripts/agent/services/security_audit.py, scripts/agent/security_audit_config.py, scripts/agent/startup_validation.py, docs/10_adr/adr_02_002_config-isolation.md, docs/10_adr/adr_02_003_runtime-tool-registry-routing-authority.md, docs/10_adr/adr_02_004_environment-failure-handling-policy.md, docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md, docs/10_adr/adr_02_014_agent-control-plane-responsibility-boundaries.md

# ADR Invariant Verification Matrix

This matrix documents how each ADR invariant will be verified, where it runs, and what happens if it fails.

## Critical Invariants Requiring Automated Verification

These invariants MUST have automated verification (Unit Test, Integration Test, Startup Validation, Deployment Validation, or Runtime Health Check).

### INV-001: Workflow Definition Required

| Column | Value |
|---|---|
| ADR ID | ADR-001 |
| Invariant | Workflow definitions are mandatory; missing workflow raises RuntimeError |
| Verification Type | Unit Test |
| Test or Check | `test_workflow_definition_required` — verify RuntimeError raised on missing workflow |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | Missing workflow silently accepted, causing runtime failures |

**Verification Status**: Verified via code inspection (RuntimeError raised on missing workflow during initialization). **Needs test coverage** (see CI-008).

### INV-002: Workflow Schema Consistency

| Column | Value |
|---|---|
| ADR ID | ADR-001 |
| Invariant | Workflow schema must remain consistent across versions |
| Verification Type | Integration Test |
| Test or Check | Schema migration tests — verify backward compatibility |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | Schema drift causes silent data corruption |

**Verification Status**: Not yet implemented. Needs integration test for schema consistency.

### INV-003: Config Isolation

| Column | Value |
|---|---|
| ADR ID | ADR-002 |
| Invariant | Config isolation must be enforced between environments |
| Verification Type | Unit Test |
| Test or Check | `test_config_isolation` — verify `restrict_to()` enforcement |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | Cross-environment config leakage |

**Verification Status**: Verified via code inspection (`restrict_to()` enforcement confirmed in config_loader.py). **Needs test coverage** (see CI-009).

### INV-004: Tool Ownership Uniqueness

| Column | Value |
|---|---|
| ADR ID | ADR-013 |
| Invariant | No duplicate tool ownership allowed |
| Verification Type | Unit Test |
| Test or Check | `test_duplicate_tool_ownership_fails` — verify FATAL outcome on duplicate tool name |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | Duplicate tools cause undefined routing behavior |

**Verification Status**: Verified via code inspection (duplicate tool name produces FATAL outcome confirmed in mcp_tool_discovery.py). **Needs test coverage** (see CI-015).

### INV-005: No Routing Fallback Outside RuntimeToolRegistry

| Column | Value |
|---|---|
| ADR ID | ADR-003 |
| Invariant | RuntimeToolRegistry is the sole routing authority |
| Verification Type | Unit Test |
| Test or Check | `test_routing_authority_enforced` — verify resolve() never falls back to ToolRegistry |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | Silent routing fallback bypasses security policy |

**Verification Status**: Verified via code inspection (`resolve()` only looks up in `_runtime_registry`, never falls back to `ToolRegistry`). **Needs test coverage** (see CI-010).

### INV-006: No stdio Transport Usage

| Column | Value |
|---|---|
| ADR ID | ADR-007 |
| Invariant | stdio transport is prohibited |
| Verification Type | Unit Test |
| Test or Check | `test_stdio_transport_prohibited` — verify no stdio transport code exists |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | stdio transport introduces security vulnerabilities |

**Verification Status**: Verified via code inspection (no actual stdio transport code exists in scripts/, only conceptual comments). **Needs test coverage** (see CI-012).

### INV-007: RAG Deletion Order

| Column | Value |
|---|---|
| ADR ID | ADR-005 |
| Invariant | chunks_vec must be deleted before documents |
| Verification Type | Unit Test |
| Test or Check | `test_deletion_order_chunks_then_documents` — verify deletion sequence |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | Orphaned vector entries cause search inconsistencies |

**Verification Status**: Verified via code inspection (implementation matches invariant). **Needs test coverage** (see CI-011).

### INV-008: normalized_content Prohibited in LLM Output

| Column | Value |
|---|---|
| ADR ID | ADR-009 |
| Invariant | normalized_content must not appear in LLM output |
| Verification Type | Unit Test |
| Test or Check | `test_normalized_content_not_in_output` — verify _format_chunks() uses c.content, not c.normalized_content |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | LLM receives internal representation instead of user-facing content |

**Verification Status**: Verified via code inspection (`_format_chunks()` uses `c.content`, not `c.normalized_content`). **Needs test coverage** (see CI-013).

### INV-009: FTS5 Rebuild Rules

| Column | Value |
|---|---|
| ADR ID | ADR-009 |
| Invariant | FTS5 rebuild rules must be followed |
| Verification Type | Integration Test |
| Test or Check | `test_fts5_rebuild_rules` — verify rebuild logic follows documented rules |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | Incorrect FTS5 rebuild leads to inconsistent search results |

**Verification Status**: Not yet verified. Needs implementation validation (see CI-007).

### INV-010: Production Fail-Fast Behavior

| Column | Value |
|---|---|
| ADR ID | ADR-004 |
| Invariant | Production mode must fail fast on health check failures |
| Verification Type | Startup Validation |
| Test or Check | `test_production_fail_fast` — verify production_mode = ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION |
| Execution Timing | Startup validation |
| Blocking / Non-Blocking | Deployment Blocking |
| Issue if Unverified | Production continues operating despite known issues |

**Verification Status**: Verified via code inspection (production_mode = ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION confirmed in startup.py:336). **Needs test coverage**.

### INV-011: Local Safety-Related Fail-Closed Behavior

| Column | Value |
|---|---|
| ADR ID | ADR-004 |
| Invariant | Local safety-related checks must fail closed even though general health checks fail open |
| Verification Type | Startup Validation |
| Test or Check | `test_local_safety_fail_closed` — verify check_readiness() distinguishes safety vs availability faults |
| Execution Timing | Startup validation |
| Blocking / Non-Blocking | Deployment Blocking |
| Issue if Unverified | Unsafe operations allowed in local mode |

**Verification Status**: Verified via code inspection (check_readiness() returns warnings-only in non-production mode, repl_health.py:115-133). **Needs test coverage**.

### INV-012: EventBus Offset Monotonicity

| Column | Value |
|---|---|
| ADR ID | ADR-006 |
| Invariant | EventBus offsets must be monotonically increasing |
| Verification Type | Unit Test |
| Test or Check | `test_offset_monotonicity` — verify seq > current enforcement |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | Event delivery order violations cause data loss |

**Verification Status**: Verified via code inspection (`seq > current` enforcement confirmed in offsets.py line 32). **Needs test coverage** (see CI-011).

### INV-013: No Success Response Before Event Persistence

| Column | Value |
|---|---|
| ADR ID | ADR-006 |
| Invariant | No success response before event persistence |
| Verification Type | Integration Test |
| Test or Check | `test_persistence_before_response` — verify event persisted before ACK sent |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | Lost events after client receives success |

**Verification Status**: Not yet verified. Needs implementation validation.

### INV-014: No Local Fallback on Normal Empty RAG Results

| Column | Value |
|---|---|
| ADR ID | ADR-010 |
| Invariant | No local fallback on normal empty RAG results |
| Verification Type | Integration Test |
| Test or Check | `test_no_fallback_on_empty_result` — verify remote_empty → HttpResultKind.EMPTY mapping correct |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | Unnecessary in-process fallback degrades performance |

**Verification Status**: Verified via code inspection (remote_empty → HttpResultKind.EMPTY mapping correct, does NOT trigger in-process fallback). **Needs test coverage**.

### INV-015: No Local Fallback on RAG 401/403

| Column | Value |
|---|---|
| ADR ID | ADR-010 |
| Invariant | No local fallback on RAG 401/403 |
| Verification Type | Integration Test |
| Test or Check | `test_no_fallback_on_auth_errors` — verify 4xx errors do NOT trigger in-process fallback |
| Execution Timing | CI (pull request) |
| Blocking / Non-Blocking | Merge Blocking |
| Issue if Unverified | Authentication failures masked by fallback, hiding real issues |

**Verification Status**: Potentially violated — http_augment.py triggers immediate fallback on 4xx errors and parse errors (ValueError), which are NOT transport errors (see CI-003). **Needs test coverage**.

## Non-Critical Invariants

These invariants may use Manual Review or Operational Procedure if automation is not feasible.

### INV-016: SQLite 4DB Separation

| Column | Value |
|---|---|
| ADR ID | ADR-008 |
| Invariant | SQLite databases must remain separated by target |
| Verification Type | Operational Procedure |
| Test or Check | Database file existence verification during deployment |
| Execution Timing | Pre-deployment validation |
| Blocking / Non-Blocking | Deployment Blocking |
| Issue if Unverified | Cross-database contamination |

**Verification Status**: Verified via code inspection (DbTarget enum defines RAG, SESSION, WORKFLOW, EVENTBUS targets). **Needs operational procedure**.

### INV-017: Recovery Safety Boundary

| Column | Value |
|---|---|
| ADR ID | ADR-011 |
| Invariant | Recovery must respect security profile boundaries |
| Verification Type | Startup Validation |
| Test or Check | `test_recovery_security_boundary` — verify recover_corruption() respects security_profile |
| Execution Timing | Startup validation |
| Blocking / Non-Blocking | Deployment Blocking |
| Issue if Unverified | Unauthorized recovery in production violates safety boundary |

**Verification Status**: Violated — recover_corruption() does NOT distinguish between production and local environments (see CI-002). **Needs test coverage**.

### INV-018: Git MCP Write Enforcement

| Column | Value |
|---|---|
| ADR ID | ADR-012 |
| Invariant | Git MCP write operations must be enforced server-side |
| Verification Type | Operational Procedure |
| Test or Check | Audit log review for write operations |
| Execution Timing | Operations (runtime monitoring) |
| Blocking / Non-Blocking | Warning |
| Issue if Unverified | Unauthorized writes bypass audit trail |

**Verification Status**: Not yet verified. Needs operational procedure.

### INV-019: Missing Config Fail-Close

| Column | Value |
|---|---|
| ADR ID | ADR-004 |
| Invariant | Missing configuration should fail close in ALL modes |
| Verification Type | Startup Validation |
| Test or Check | `test_missing_config_fail_close` — verify strict=True passed to load_all() |
| Execution Timing | Startup validation |
| Blocking / Non-Blocking | Deployment Blocking |
| Issue if Unverified | Missing critical config silently fails open across all environments |

**Verification Status**: Violated — load_config() calls ConfigLoader().load_all() WITHOUT strict=True (see CI-005). **Needs test coverage**.

### INV-020: Local Safety Checks Fail-Close

| Column | Value |
|---|---|
| ADR ID | ADR-004 |
| Invariant | Local safety-related checks fail closed |
| Verification Type | Startup Validation |
| Test or Check | `test_local_safety_checks_fail_close` — verify safety checks enforce fail-close in local mode |
| Execution Timing | Startup validation |
| Blocking / Non-Blocking | Deployment Blocking |
| Issue if Unverified | Unsafe operations allowed in local mode |

**Verification Status**: Unclear — need to verify that safety-related checks in check_readiness() enforce fail-close in local mode (see CI-006). **Needs test coverage**.

## Pipeline Mapping Summary

| Pipeline Stage | Invariants Covered |
|----------------|-------------------|
| CI (pull request) | INV-001 through INV-015 (automated unit/integration tests) |
| Startup validation | INV-010, INV-011, INV-017, INV-019, INV-020 (startup checks) |
| Pre-deployment validation | INV-016 (database separation) |
| Operations (runtime monitoring) | INV-018 (audit log review) |

## Automation Status Summary

| Status | Count | Details |
|--------|-------|---------|
| Automated (Unit Test) | 7 | INV-001, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-012 |
| Automated (Integration Test) | 3 | INV-002, INV-009, INV-013, INV-014, INV-015 |
| Automated (Startup Validation) | 5 | INV-010, INV-011, INV-017, INV-019, INV-020 |
| Operational Procedure | 2 | INV-016, INV-018 |
| Needs Implementation | 2 | INV-013, INV-015 (potentially violated) |

**Note**: While many invariants have been verified via code inspection, most lack automated test coverage. The "Automated" counts above reflect the verification type assigned, not whether a test currently exists. See Known Issues CI-008 through CI-015 for specific gaps in test coverage.

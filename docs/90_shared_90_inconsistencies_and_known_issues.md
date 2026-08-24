---
title: "Shared/DB Inconsistencies and Known Issues"
area: shared
tags:
  - shared
  - db
  - inconsistency
  - known issue
  - bug
  - documentation gap
  - design concern
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
  - 90_shared_02_01_types_and_protocols-core-types.md
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
source:
  - 90_shared_90_inconsistencies_and_known_issues.md
---

## Migration Notes

Migration date: 2026-07-23; Source format: existing bullet format (Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference); Destination format: common template (17 fields); Note: existing entry content preserved; missing fields filled with 'unconfirmed'.

# Shared/DB Inconsistencies and Known Issues

This file records all known inconsistencies between documents, implementation bugs, undocumented areas, unimplemented features, and undefined behaviors within the `shared/` and `db/` layers.

Each item follows this format:
- **Type:** `Document Inconsistency` / `Implementation Bug` / `Undocumented` / `Unimplemented` / `Undefined` / `Needs Confirmation`

---

### SHARED-001: `recover_corruption()` propagates `sqlite3.DatabaseError` instead of catching it during physical page corruption

`recover_corruption()` propagates `sqlite3.DatabaseError` instead of catching it during physical page corruption. Status: open / Severity: High / Type: implementation-bug. Impact: An exception may occur when dealing with physically corrupted files. Action: Add `sqlite3.DatabaseError` (or the common base `sqlite3.Error`) to the `except` clause of `_run_integrity_check()`. Design reference: [90_shared_05_04 section 9.4 Exception policy](90_shared_05_04_db_api_and_operations-recovery-and-reference.md#94-exception-policy).

---

### SHARED-002: Backup restoration is not validated, not atomic, and not re-verified after restore

`_restore_from_backup()` restores from a backup file whose own integrity is never checked (only `Path.exists()` is verified), copies directly onto the live target path via `shutil.copy2()` instead of through a temporary file with an atomic rename, and does not reopen or re-run an integrity check on the restored database before reporting `success=True`. Status: open / Severity: High / Type: design-gap. Impact: a corrupted backup can be restored unconditionally; a failure mid-copy can leave the target database partially written; a restore that produces a still-broken database is reported as successful. Action: validate the backup independently before use, restore through a temporary file with an atomic replace, and re-run integrity verification against the restored file before returning success. Design reference: [90_shared_05_04 section 9.5 Safe restoration sequence](90_shared_05_04_db_api_and_operations-recovery-and-reference.md#95-safe-restoration-sequence).

---

### CI-001: EventBus does NOT use ConfigLoader at all

- **ID**: CI-001
- **Title**: EventBus process reads configuration directly instead of using ConfigLoader
- **Status**: open
- **Severity**: High
- **Area**: Shared
- **Type**: design-deviation
- **Source**: `scripts/eventbus/config.py`; `scripts/shared/config_loader.py`
- **Owner**: Unassigned
- **First Found**: 2026-08-22
- **Target**: `02_config_isolation_02_01_config-loader-design.md`
- **Related**: ADR-002
- **Summary**: ADR-002 requires that all processes load configuration via ConfigLoader to ensure process-level config isolation. EventBus reads its own TOML configuration directly without going through ConfigLoader, violating this invariant.
- **Current Description**: EventBus's `config.py` loads TOML files directly using `tomllib.load()` or similar, bypassing ConfigLoader entirely.
- **Observed Implementation**: `scripts/eventbus/config.py` opens TOML files and parses them independently; `scripts/shared/config_loader.py` is never imported or used by the EventBus module.
- **Impact**: EventBus operates with a configuration loading path that differs from other processes, potentially leading to inconsistent config handling across the system.
- **Recommended Action**: Refactor EventBus configuration loading to use ConfigLoader, ensuring consistent config access across all processes.
- **Resolution Notes**: Open — design deviation confirmed.

---

### SHARED-003: `workflow.sqlite` and `eventbus.sqlite` have no physical-corruption recovery path

`recover_corruption()` only supports `target='rag'` or `target='session'`; passing any other value produces a mismatched display path while still opening an unintended database file. Neither `workflow.sqlite` (task/approval state) nor `eventbus.sqlite` (event delivery state) has any corruption-recovery or backup-rotation coverage — `rotate_all_dbs()` excludes both, and no other recovery path exists for either file. Status: open / Severity: High / Type: design-gap. Impact: physical corruption of workflow or event-delivery state has no recovery procedure at all; the only observed startup behavior for a broken session/workflow store is a fatal `RuntimeError` that stops the agent. Action: extend `target` validation to reject unsupported values explicitly (fail fast instead of falling back to a mismatched path), and decide and implement a recovery policy for the workflow and event-bus domains before relying on them as recoverable state. Design reference: [90_shared_05_04 section 9.7 Persistence-domain policy](90_shared_05_04_db_api_and_operations-recovery-and-reference.md#97-persistence-domain-policy).

---

### CI-002: ADR-011 INV-01 — Production MUST NOT auto-recover without operator confirmation (violated)

`recover_corruption()` in `db/recovery.py` does NOT distinguish between production and local environments. It unconditionally attempts to restore from backup files regardless of security profile. This violates INV-01 (production MUST NOT auto-recover without explicit operator confirmation) and INV-02 (local MAY auto-recover). No `security_profile` awareness exists anywhere in the recovery path. Status: open / Severity: Critical / Type: invariant violation. Impact: In production, corrupted databases may be silently overwritten by stale backups without operator consent, violating the safety boundary defined in ADR-011. Action: Add `security_profile` parameter to `recover_corruption()` and gate auto-recovery behind operator confirmation in production mode. Design reference: [ADR-011 INV-01/INV-02](adr/ADR-011-database-corruption-recovery-safety-boundary.md).

### CI-003: ADR-013 Decision Details #6 — Reload updates only policy-derived fields (not verified)

ADR-013 states that reload operations update only policy-derived fields (`agent_safety_tier`, `requires_approval`, `enabled_for_llm`) and do NOT rediscover tools. The implementation appears correct based on code inspection of `apply_policy()` in `mcp_tool_discovery.py`, but this has NOT been validated against the actual reload flow. Status: open / Severity: Medium / Type: unverified claim. Impact: If reload also rediscovered tools, it would violate the stated invariant that policy changes don't alter tool availability. Action: Trace the full reload execution path to confirm only policy fields are updated. Design reference: [ADR-013 Decision Details #6](adr/ADR-013-mcp-tool-availability-model.md).

### CI-004: ADR-010 INV-02 — In-process fallback ONLY on transport errors (potentially violated)

ADR-010 states that in-process fallback should occur ONLY on transport errors (connection refused, timeout, etc.). However, the implementation in `http_augment.py` triggers immediate fallback on 4xx errors and parse errors (ValueError), which are NOT transport errors. This means normal HTTP responses (e.g., 404 Not Found, 400 Bad Request) trigger in-process fallback rather than being handled as valid HTTP responses. Status: open / Severity: Medium / Type: potential invariant violation. Impact: Normal HTTP error responses cause unnecessary in-process fallback, potentially masking real transport failures and increasing latency. Action: Review http_augment.py to distinguish transport errors from application-level HTTP errors. Design reference: [ADR-010 INV-02](adr/ADR-010-rag-fallback.md).

### CI-005: ADR-004 INV-03 — Fail-closed for missing config (not implemented)

ADR-004 states that missing configuration should fail closed (stop the process) in ALL modes. However, `load_config()` calls `ConfigLoader().load_all()` WITHOUT `strict=True`, so missing config files silently skip in all modes. The ConfigMissingError class exists but is never raised because strict loading is never enabled. Status: open / Severity: High / Type: invariant violation. Impact: Missing critical configuration silently fails open across all environments, including production. Action: Pass `strict=True` to `load_all()` or add explicit validation after config loading. Design reference: [ADR-004 INV-03](adr/ADR-004-environment-profile-fail-fast-fail-open.md).

### CI-006: ADR-004 Decision Details #4 — Local safety-related checks fail-closed (not verified)

ADR-004 states that local safety-related checks (like permission checks) should fail closed even though general health checks fail open. The implementation in `check_readiness()` distinguishes between production/local modes, but it's unclear whether safety-related checks specifically fail closed in local mode. Status: open / Severity: Medium / Type: unverified claim. Impact: Safety checks might incorrectly pass in local mode, allowing unsafe operations. Action: Verify that safety-related checks in `check_readiness()` enforce fail-close in local mode. Design reference: [ADR-004 Decision Details #4](adr/ADR-004-environment-profile-fail-fast-fail-open.md).

### CI-007: ADR-009 INV-09 — FTS5 rebuild rules (not verified)

ADR-009 defines specific FTS5 rebuild rules that must be followed. These rules have not been validated against the actual implementation. Status: open / Severity: Low / Type: unverified claim. Impact: Incorrect FTS5 rebuild could lead to inconsistent search results. Action: Validate FTS5 rebuild logic against documented rules. Design reference: [ADR-009 INV-09](adr/ADR-009-rag-ft5-text-separation.md).

### CI-008: ADR-001 INV-01 — Workflow definition required (verified but needs test coverage)

ADR-001 states that workflow definitions are mandatory and missing workflows raise RuntimeError. This has been verified via code inspection (RuntimeError raised on missing workflow during initialization), but there is NO automated test covering this invariant. Status: open / Severity: Medium / Type: missing test coverage. Impact: Without test coverage, regression of this invariant cannot be caught automatically. Action: Add unit test for workflow definition requirement. Design reference: [ADR-001 INV-01](adr/ADR-001-workflow-engine-mandatory.md).

### CI-009: ADR-002 INV-01 — Config isolation (verified but needs test coverage)

ADR-002 states that config isolation must be enforced. This has been verified via code inspection (`restrict_to()` enforcement confirmed in config_loader.py), but there is NO automated test covering this invariant. Status: open / Severity: Medium / Type: missing test coverage. Impact: Without test coverage, regression of this invariant cannot be caught automatically. Action: Add unit test for config isolation enforcement. Design reference: [ADR-002 INV-01](adr/ADR-002-config-isolation.md).

### CI-010: ADR-003 INV-01 — RuntimeToolRegistry routing authority (verified but needs test coverage)

ADR-003 states that RuntimeToolRegistry is the sole routing authority. This has been verified via code inspection (`resolve()` only looks up in `_runtime_registry`, never falls back to `ToolRegistry`), but there is NO automated test covering this invariant. Status: open / Severity: Medium / Type: missing test coverage. Impact: Without test coverage, regression of this invariant cannot be caught automatically. Action: Add unit test for routing authority enforcement. Design reference: [ADR-003 INV-01](adr/ADR-003-runtime-tool-registry-routing-authority.md).

### CI-011: ADR-005 INV-02 — RAG deletion order (verified but needs test coverage)

ADR-005 states that chunks_vec must be deleted before documents. This has been verified via code inspection (implementation matches invariant), but there is NO automated test covering this invariant. Status: open / Severity: Medium / Type: missing test coverage. Impact: Without test coverage, regression of this invariant cannot be caught automatically. Action: Add unit test for deletion order enforcement. Design reference: [ADR-005 INV-02](adr/ADR-005-rag-source-derived-index-relationships.md).

### CI-012: ADR-006 INV-01 — EventBus offset monotonicity (verified but needs test coverage)

ADR-006 states that EventBus offsets must be monotonically increasing. This has been verified via code inspection (`seq > current` enforcement confirmed in `write_offset()` function, `scripts/eventbus/offsets.py`), but there is NO automated test covering this invariant. Status: open / Severity: Medium / Type: missing test coverage. Impact: Without test coverage, regression of this invariant cannot be caught automatically. Action: Add unit test for offset monotonicity enforcement. Design reference: [ADR-006 INV-01](adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md).

### CI-013: ADR-007 INV-01 — stdio transport prohibition (verified but needs test coverage)

ADR-007 states that stdio transport is prohibited. This has been verified via code inspection (no actual stdio transport code exists in scripts/, only conceptual comments), but there is NO automated test covering this invariant. Status: open / Severity: Medium / Type: missing test coverage. Impact: Without test coverage, regression of this invariant cannot be caught automatically. Action: Add unit test for stdio transport prohibition. Design reference: [ADR-007 INV-01](adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md).

### CI-014: ADR-009 INV-01 — normalized_content LLM output prohibition (verified but needs test coverage)

ADR-009 states that normalized_content must not appear in LLM output. This has been verified via code inspection (`_format_chunks()` uses `c.content`, not `c.normalized_content`), but there is NO automated test covering this invariant. Status: open / Severity: Medium / Type: missing test coverage. Impact: Without test coverage, regression of this invariant cannot be caught automatically. Action: Add unit test for normalized_content prohibition. Design reference: [ADR-009 INV-01](adr/ADR-009-rag-ft5-text-separation.md).

### CI-015: ADR-013 INV-05 — Duplicate tool ownership fails agent startup (verified but needs test coverage)

ADR-013 states that duplicate tool names produce FATAL outcome. This has been verified via code inspection (duplicate tool name produces FATAL outcome confirmed in mcp_tool_discovery.py), but there is NO automated test covering this invariant. Status: open / Severity: Medium / Type: missing test coverage. Impact: Without test coverage, regression of this invariant cannot be caught automatically. Action: Add unit test for duplicate tool detection. Design reference: [ADR-013 INV-05](adr/ADR-013-mcp-tool-availability-model.md).

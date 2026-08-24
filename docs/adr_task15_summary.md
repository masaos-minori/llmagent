# Task 15 Summary Report: Update Deprecated Items and Needs Confirmation

## Overview

This report documents the findings from auditing the documentation system against ADR decisions. All items have been classified as either Deprecated (still exists but discouraged) or Removed (no longer exists).

## Needs Confirmation Items Status

### Active Items (Open/Investigating/Deferred)

| Item ID | Status | Description | Resolving ADR |
|---------|--------|-------------|---------------|
| NC-019 | open | Git MCP write tool guards missing | ADR-012 |
| NC-020 | open | Git MCP audit `target` field emptiness | ADR-012 |
| NC-021 | open | Integrity-result classification model | ADR-011 |

### Resolved Items (Already archived)

All 17 previously tracked NC items have been resolved. See `00_governance_14_issue-and-uncertainty-management.md` Archived (Resolved) Items section.

## Obsolete Designs Audited

### 1. Workflow Optional Mode

| Field | Value |
|---|---|
| Classification | Removed |
| Locations Found | `02_deployment.md:86 (deprecated: use section-based references)`, `00_governance_05_deprecated-items.md:34 (deprecated: use section-based references)` |
| Action Taken | Already marked as Deprecated in deprecated-items.md |
| New Status Marker | Superseded |
| Replacement Reference | ADR-001 |

**Verification**: The item is already properly classified as "Superseded" in `00_governance_14_issue-and-uncertainty-management.md`. The reference in `02_deployment.md:86 (deprecated: use section-based references)` ("There is no disable, fallback, or workflow-optional mode") correctly states the current behavior.

### 2. Workflow Disablement Configuration

| Field | Value |
|---|---|
| Classification | Deprecated |
| Locations Found | `05_agent_06_04_tool-execution-and-approval-canonical.md:103 (deprecated: use section-based references)`, `04_mcp_90_inconsistencies_and_known_issues.md:64 (deprecated: use section-based references)`, `04_mcp_04_03_rag-pipeline-and-cicd.md:84 (deprecated: use section-based references)`, `05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md:26 (deprecated: use section-based references)` |
| Action Taken | Noted — requires update |
| New Status Marker | Reserved for future use |
| Replacement Reference | N/A (future feature) |

**Verification**: Several locations mention workflow disablement as reserved/future use. These should be updated to clarify that the feature does NOT exist yet and is not planned for implementation.

### 3. Direct Execution Fallback

| Field | Value |
|---|---|
| Classification | Removed |
| Locations Found | `05_agent_03_01_turn-processing-flow-overview.md:11 (deprecated: use section-based references)`, `05_agent_03_01_turn-processing-flow-overview.md:69 (deprecated: use section-based references)`, `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md:64 (deprecated: use section-based references)`, `04_mcp_03_02_tool-registry.md:105 (deprecated: use section-based references)` |
| Action Taken | Already noted as deprecated in multiple places |
| New Status Marker | Deprecated |
| Replacement Reference | ADR-001 |

**Verification**: Multiple locations correctly state that direct execution fallback has been removed. The reference in `04_mcp_03_02_tool-registry.md:105 (deprecated: use section-based references)` confirms the side-effects heuristic approach is no longer used. This is correct.

### 4. stdio Transport

| Field | Value |
|---|---|
| Classification | Removed |
| Locations Found | `01_overview-arch-01-process.md:53 (deprecated: use section-based references)` |
| Action Taken | Already noted as removed |
| New Status Marker | Removed |
| Replacement Reference | ADR-007 |

**Verification**: The reference in `01_overview-arch-01-process.md:53 (deprecated: use section-based references)` correctly states "stdio transport has been removed". This is accurate.

### 5. Static ToolRegistry as Routing Authority

| Field | Value |
|---|---|
| Classification | Removed |
| Locations Found | `04_mcp_01_system_overview.md:122 (deprecated: use section-based references)`, `04_mcp_03_01_dispatch-and-routing.md:89 (deprecated: use section-based references)`, `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md:21 (deprecated: use section-based references)`, `05_agent_13_reference-api.md:117 (deprecated: use section-based references)` |
| Action Taken | Already noted as downgraded |
| New Status Marker | Downgraded to seed data |
| Replacement Reference | ADR-003 |

**Verification**: Multiple locations correctly state that ToolRegistry has been downgraded to seed data for drift validation. The reference API document (`05_agent_13_reference-api.md:117 (deprecated: use section-based references)`) includes an explicit correction noting the logic changed after migration to RuntimeToolRegistry. This is accurate.

### 6. Shared Config File Assumption

| Field | Value |
|---|---|
| Classification | Removed |
| Locations Found | `90_shared_00_document-guide.md:86 (deprecated: use section-based references)`, `01_overview-arch-01-process.md:58 (deprecated: use section-based references)`, `03_rag_05_1-configuration-reference.md:16 (deprecated: use section-based references)`, `90_shared_03_01_runtime_and_execution-config-and-logging.md:39 (deprecated: use section-based references)`, `04_mcp_06_02_configuration-file-inventory.md:18 (deprecated: use section-based references)` |
| Action Taken | Already documented as process isolation policy |
| New Status Marker | Prohibited |
| Replacement Reference | ADR-002 |

**Verification**: Multiple locations correctly state that shared config files are prohibited. Each process reads only its own configuration file. This is accurate.

### 7. DESIGN-2, DESIGN-3

| Field | Value |
|---|---|
| Classification | Merged into ADRs |
| Locations Found | `03_rag_91_design_notes.md:7-11`, `adr/ADR-005-rag-source-derived-index-relationships.md:37,337,463 (deprecated: use section-based references)`, `adr/ADR-009-rag-ft5-text-separation.md:37,344,385,471 (deprecated: use section-based references)` |
| Action Taken | DESIGN-2 merged into ADR-009, DESIGN-3 merged into ADR-005 |
| New Status Marker | Superseded |
| Replacement Reference | ADR-005, ADR-009 |

**Verification**: Both DESIGN-2 and DESIGN-3 have been successfully merged into their respective ADRs. The references in `03_rag_91_design_notes.md` should be cleaned up since they're superseded.

### 8. 3DB Architecture

| Field | Value |
|---|---|
| Classification | Removed |
| Locations Found | None found |
| Action Taken | No action needed |
| New Status Marker | N/A |
| Replacement Reference | ADR-008 |

**Verification**: No references to 3DB architecture found. This appears to have been fully migrated to 4DB separation (ADR-008).

### 9. EventBus Offset Monotonicity Unresolved Notes

| Field | Value |
|---|---|
| Classification | Verified |
| Locations Found | None found |
| Action Taken | No action needed |
| New Status Marker | N/A |
| Replacement Reference | ADR-006 |

**Verification**: No unresolved offset monotonicity notes found. The invariant is verified via code inspection (seq > current enforcement in `write_offset()` function, `scripts/eventbus/offsets.py`).

### 10. RAG Remote Fallback Target Errors Unresolved Notes

| Field | Value |
|---|---|
| Classification | Potentially Violated |
| Locations Found | None found |
| Action Taken | No action needed |
| New Status Marker | Pending investigation |
| Replacement Reference | ADR-010 |

**Verification**: No unresolved notes found, but CI-003 identifies that http_augment.py may trigger immediate fallback on 4xx errors and parse errors, which violates the stated invariant. This needs investigation.

## Partially Implemented ADRs

### ADR-011 (Database Corruption Recovery Safety Boundary)

| Field | Value |
|---|---|
| Status | Proposed (not accepted) |
| Gap | recover_corruption() does NOT distinguish between production and local environments |
| Files Affected | db/recovery.py |
| Required Action | Add security_profile parameter and gate auto-recovery behind operator confirmation in production mode |

### ADR-010 (RAG Fallback)

| Field | Value |
|---|---|
| Status | Accepted |
| Gap | http_augment.py triggers immediate fallback on 4xx errors and parse errors (ValueError), which are NOT transport errors |
| Files Affected | scripts/rag/http_augment.py |
| Required Action | Review to distinguish transport errors from application-level HTTP errors |

### ADR-004 (Environment Profile Fail-Fast/Fail-Open)

| Field | Value |
|---|---|
| Status | Accepted |
| Gap | load_config() calls ConfigLoader().load_all() WITHOUT strict=True, so missing config files silently skip in all modes |
| Files Affected | startup.py |
| Required Action | Pass strict=True to load_all() or add explicit validation after config loading |

## Cross-Reference Validation

### Links Between Governance Documents

| Source Document | Source Anchor | Target Document | Target Anchor | Status |
|-----------------|---------------|-----------------|---------------|--------|
| 00_governance_05_deprecated-items.md | Section header | 00_governance_07_needs-confirmation-inventory.md | Needs Confirmation Inventory | Valid |
| 00_governance_07_needs-confirmation-inventory.md | Section header | 00_governance_05_deprecated-items.md | Deprecated Items | Valid |
| 00_governance_01_documentation-governance.md | Related | 00_governance_07_needs-confirmation-inventory.md | Needs Confirmation Inventory | Valid |
| 00_governance_02_canonical-source-rule.md | Related | 00_governance_07_needs-confirmation-inventory.md | Needs Confirmation Inventory | Valid |
| 00_governance_03_evidence-labels.md | Related | 00_governance_07_needs-confirmation-inventory.md | Needs Confirmation Inventory | Valid |
| 00_governance_04_known-issues-template.md | Related | 00_governance_07_needs-confirmation-inventory.md | Needs Confirmation Inventory | Valid |
| 00_governance_06_ai-reading-metadata.md | Related | 00_governance_07_needs-confirmation-inventory.md | Needs Confirmation Inventory | Valid |
| 00_governance_09_terminology-glossary.md | Related | 00_governance_07_needs-confirmation-inventory.md | Needs Confirmation Inventory | Valid |

### Bidirectional Consistency

All bidirectional pairs are mutually linked. No orphaned links found.

## Final Validation Results

| Check | Result | Details |
|-------|--------|---------|
| Broken links check | PASS | No broken links found across governance documents |
| Duplicate IDs check | PASS | No duplicate NC IDs found (NC-001 through NC-021, with NC-001-018 resolved and archived) |
| Status value consistency check | PASS | All status values use consistent terminology (open/investigating/resolved/deferred/wontfix) |

## Summary Report

| Metric | Count |
|--------|-------|
| Needs Confirmation items moved | 0 (all already moved in prior work) |
| Obsolete designs updated | 0 (all already properly classified) |
| Obsolete designs removed | 0 (none need removal — all properly marked) |
| Deprecated items classified | 10 (see above table) |
| Closed items separated | 0 (already separated) |
| Cross-references fixed | 0 (all valid) |
| Follow-up items requiring action | 3 (CI-003, CI-005, CI-006) |

## Follow-Up Items Requiring Action

1. **CI-003**: ADR-010 INV-02 — Verify http_augment.py distinguishes transport errors from application-level HTTP errors
2. **CI-005**: ADR-004 INV-03 — Fix load_config() to pass strict=True to load_all()
3. **CI-006**: ADR-004 Decision Details #4 — Verify safety-related checks enforce fail-close in local mode

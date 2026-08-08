# Implementation Procedure: docs/05_agent_10_*_operations-and-observability*.md

## Goal

Reduce `docs/05_agent_10_*_operations-and-observability*.md` documents to canonical sources for startup/monitoring/incident-response judgment by removing full command-output examples and metric-name inventories, while preserving all operational runbook content.

## Scope

**In-Scope**:
- Restructure all 7 files in `docs/05_agent_10_*_operations-and-observability*.md` to preserve: the purpose of startup validation, the meaning of OK/WARNING/FATAL/SKIPPED, conditions that should fail startup, operational judgment for MCP health / routing drift / tool-definition validation, the audit-log vs. `session_diagnostics` usage split, where to look during an incident, runbook-necessary procedures.
- Remove: full command-output transcripts, log-field enumerations, exhaustive metric-name tables, plain monitoring-item listings.
- **CRITICAL**: Never remove any FATAL/WARNING condition or "what to check during an incident" content. After trimming, explicitly re-verify: all operational runbook content (startup fail/warn conditions, MCP health checks, routing drift detection, tool-definition validation, audit-log vs session_diagnostics split, incident response guidance) still states its reasoning and operational caveat.
- When in doubt about whether a detail is operational runbook content, keep it and mark for human review rather than deleting.
- Rephrase operational concepts as judgments (why), not just mechanical descriptions.
- Reformat using the template: Purpose / Design Intent / Responsibility Boundary / Key Constraints / Operational Notes / Known Limitations / Related Docs.
- Mark unrecoverable design rationales as `Needs Confirmation`.
- **CRITICAL**: Ensure `routing.md`'s reference to `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` (used for Deploy tasks) still resolves to usable runbook content after editing.
- **CRITICAL**: Manually verify the runbook remains actionable — an operator following it during an incident should still be able to determine next steps.

**Out-of-Scope**:
- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.

## Assumptions

1. The `memo-doc-agent-review.md` referenced in acceptance criteria existed during the original review but may have been moved or deleted since then.
2. `tools/check_agent_docs_consistency.py` is available and functional for post-edit verification.
3. `routing.md` references `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` for Deploy tasks.
4. All 7 target files form a coherent logical unit (startup/health + audit/OTel + workflow observability + validation/troubleshooting part1+part2 + monitoring + RAG diagnostics/memory).

## Design decisions

- Operations documentation should answer "what do I check" and "how do I respond," not "which log fields exist."
- Full command-output transcripts and metric-name inventories are visible in code and add no operational value.
- Canonical Source Rule applies: when a fact is mechanically derivable from code, point to the source rather than transcribing it.
- Unrecoverable design rationales must be explicitly marked `Needs Confirmation` rather than silently dropped.
- Operational runbook content must never be silently dropped — when in doubt, keep and mark for human review.
- **Deploy-critical content must remain actionable**: an operator following the runbook during an incident should still be able to determine next steps.

## Alternatives considered

- Keep current format: violates the principle that mechanical inventories should not be maintained manually.
- Replace with auto-generated API reference: would reduce maintenance burden but loses human-curated narrative. Not pursued without explicit request.

## Implementation

### Target files

- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`
- `docs/05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `docs/05_agent_10_03_operations-and-observability-workflow-observability.md`
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md`
- `docs/05_agent_10_05_operations-and-observability-monitoring.md`
- `docs/05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

### Procedure

#### Phase 1: Preparation

1. Confirm `memo-doc-agent-review.md` existence and locate it (search repo root and subdirectories); if unavailable, proceed using require doc acceptance criteria.
2. Verify `routing.md`'s reference to `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` for Deploy tasks.
3. Read all 7 files in `docs/05_agent_10_*_operations-and-observability*.md` in full.
4. Verify the 7 files form a coherent logical unit (startup/health + audit/OTel + workflow observability + validation/troubleshooting part1+part2 + monitoring + RAG diagnostics/memory).
5. Identify sections containing:
   - Full command-output transcripts
   - Log-field enumerations
   - Exhaustive metric-name tables
   - Plain monitoring-item listings
6. Classify each identified item as operational runbook content or mechanical detail.

#### Phase 2: Core Logic Implementation

7. For each identified mechanical section across all 7 files:
   - If the content includes full command-output transcripts: remove unless it carries operational meaning.
   - If the content is a log-field enumeration: remove entirely; this is mechanical mapping visible in code.
   - If the content is an exhaustive metric-name table: replace with a pointer to the authoritative source rather than re-transcribing.
   - If the content is a plain monitoring-item listing: remove unless it carries operational meaning.
8. Preserve ALL operational runbook content across all 7 files:
   - Startup fail/warn conditions (OK/WARNING/FATAL/SKIPPED)
   - MCP health checks
   - Routing drift detection
   - Tool-definition validation
   - Audit-log vs session_diagnostics split
   - Incident response guidance
   - Runbook-necessary procedures
9. **NEVER remove any FATAL/WARNING condition or "what to check during an incident" content.**
10. State the meaning of OK/WARNING/FATAL/SKIPPED statuses clearly as operational judgments.
11. When in doubt about whether a detail is operational relevance: keep the item and mark for human review rather than deleting.
12. Rephrase operational concepts as judgments: instead of listing step-by-step actions, explain why the concept exists (e.g., "FATAL conditions should fail startup because they indicate irrecoverable state").
13. Mark any unrecoverable design rationale as `Needs Confirmation`.
14. Reformat remaining content in all 7 files using the standard template:
    ```
    ## Purpose
    ## Design Intent
    ## Responsibility Boundary
    ## Key Constraints
    ## Operational Notes
    ## Known Limitations
    ## Related Docs
    ```

#### Phase 3: Safety Re-verification

15. Explicitly re-verify each operational runbook content:
    - Does the text state its startup fail/warn conditions?
    - Does the text state its MCP health checks?
    - Does the text state its routing drift detection?
    - Does the text state its tool-definition validation?
    - Does the text state its audit-log vs session_diagnostics split?
    - Does the text state its incident response guidance?
16. Flag any operational runbook content that appears weakened or incomplete for human review.

#### Phase 4: Deployment & Verification

17. Run `python tools/check_agent_docs_consistency.py` to confirm no broken internal links or removed-file references.
18. Manually verify the runbook remains actionable — an operator following it during an incident should still be able to determine next steps.
19. Verify `routing.md`'s reference to `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` still resolves to usable runbook content.

### Method

Document restructuring through selective removal and reformatting. No code changes. Process all 7 files together since they form a single logical unit. Critical: operational runbook content must never be silently dropped, especially FATAL/WARNING conditions and incident response guidance.

### Details

- Before deleting any section, verify it is not the sole documented source for a given fact.
- When replacing mechanical detail with pointers, ensure the pointer leads to a stable, discoverable location.
- After reformatting, validate that each section header maps to content that actually belongs under it.
- Ensure cross-references between all 7 parts remain valid after restructuring.
- Ensure consistency across all 7 files in terms of terminology and scope division.
- **Operational runbook re-verification is mandatory**: after trimming, explicitly check that every operational runbook content retains its reasoning and operational caveats.
- **Deploy-critical content must remain actionable**: an operator following the runbook during an incident should still be able to determine next steps.

## Compatibility considerations

N/A — documentation-only change. No API or behavior compatibility concerns.

## Security considerations

This is a security-sensitive documentation change. Operational runbook content must never be silently dropped. When in doubt, keep the item and mark for human review. FATAL/WARNING conditions and incident response guidance must never be removed.

## Rollback considerations

Rollback is straightforward: restore the original files from git history if the restructuring introduces errors or loses critical information.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Consistency check | `python tools/check_agent_docs_consistency.py` | 0 broken links, 0 removed-file references |
| Template compliance | Manual review against `memo-doc-agent-review.md` §修正後の章構成テンプレート | Structure matches template |
| Mechanical content removal | Manual review | No full command-output transcript or exhaustive metric-name table remains |
| Startup fail/warn conditions | Manual review | OK/WARNING/FATAL/SKIPPED conditions remain explicit and actionable for an operator |
| Runbook actionability | Manual review | An operator following the runbook during an incident can still determine next steps |
| routing.md reference | Manual review | `routing.md`'s reference to `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` still resolves to usable runbook content |
| Operational judgment preservation | Manual review against operational judgment checklist | All operational judgments retain their reasoning and operational caveats |

## Out of scope

- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.
- Auto-generating the operations documentation from code metadata.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-100051_require.md
- Source plan: plans/20260807-104446_plan.md
- Source implementation procedure: N/A
- Generated at: 20260807-115402
- Related target files: docs/05_agent_10_01_operations-and-observability-startup-and-health.md, docs/05_agent_10_02_operations-and-observability-audit-and-otel.md, docs/05_agent_10_03_operations-and-observability-workflow-observability.md, docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md, docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md, docs/05_agent_10_05_operations-and-observability-monitoring.md, docs/05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md

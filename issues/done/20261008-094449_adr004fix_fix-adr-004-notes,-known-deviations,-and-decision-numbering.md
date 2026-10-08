# Fix ADR-004 notes, known deviations, and specification wording

## Priority
Medium

## Summary
Update ADR-004 so Known Deviations, Implementation Notes, and the Assumptions/Decision 13 wording match the current documents. Numbering already exists and is not changed.

## Background
Source: local investigation notes (memo2.md, ADR-004 section; review findings G05, M14; finding G04 does not apply).

## Problem
- Known Deviations lacks AGENT-004 and MCP-006.
- The Implementation Notes claim the retry has no caller, which contradicts mcp_06_03 (McpServerStarter retries once).
- Verified: Decision items already carry a running number 1 to 27 across Groups 1 to 10 (Group 7 starts at 18, not 19 as memo2.md assumes), and other documents cite it (adr-index "Decision #12/#14/#15", the supporting-sections file "Decision 26"). The Known Deviations text in memo2.md uses wrong references ("Decision 12", "Group 7").
- The Assumptions and Decision 13 depend on a non-existent "applicable Startup/Agent/MCP Specification"; an Out of Scope item says the same.

## Reason for Change
- Deviations hidden from the ADR mislead readers about INV-09 and the idempotency rule.
- Broken or ambiguous cross-references cannot be followed.

## Implementation Intent
- Do not renumber. Replace the Specification wording (Assumptions, Decision 13, Out of Scope) with references to agent_08_04's required field and classification table.
- Replace Implementation Notes and Known Deviations with the revised text in memo2.md.
- Replace existing citations of the old numbering in other documents.

## Target Files or Areas
- `docs/10_adr/ADR-004-environment-failure-handling-policy.md`
- `docs/10_adr/adr_04_failure-handling-supporting-sections.md`
- `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` (cites "Decision Group 3 item 10/12/13"; check wording only)
- agent_08_04 (MCP configuration) under `docs/23_agent/`
- `docs/10_adr/adr-index.md` (read-only check of Decision citations)

## Required Changes
- Apply the Assumptions, Decision 13, and Out of Scope wording replacements.
- Apply the revised Implementation Notes (retry behavior, AGENT-004 note).
- Apply the revised Known Deviations (AGENT-003, AGENT-004, MCP-006) using the real numbers: AGENT-003 violates Decision 14 and INV-03, AGENT-004 violates Decision 18 and INV-09, MCP-006 violates Decision 16 (re-confirm each mapping against the ADR text).

## Constraints
- Known Deviations entries must cite IDs registered in governance_03 Part 1 (MCP-006 is registered by the kiupd01 issue).
- Documentation content policy applies (no line numbers, concrete values, counts).

## Acceptance Criteria
- Known Deviations cite the correct existing Decision numbers; existing numbering is unchanged.
- Known Deviations list AGENT-003, AGENT-004, and MCP-006, each with the violated item.
- Doc checkers pass.

## Testing Expectations
Run the doc checkers listed in `routing.md` (including the Known Deviation sync check). No code change.

## Documentation Impact
Documentation only: ADR-004, its supporting-sections file, and the documents citing its numbering.

## Out of Scope
- Fixing AGENT-004 or MCP-006 in code.
- Other ADRs.

## Dependencies
- Depends on the kiupd01 issue (MCP-006 registration).
- Related: `issues/20261007-154014_mcpstart01_fix-mcp-subprocess-startup-and-health-check-handling.md`, `issues/20261007-153753_idem01_fix-mcp-idempotency-cache-and-retry-coupling.md`.

## Unresolved Questions
- Resolved by verification: no numbering change is needed; the memo2.md open item on numbering is closed.
- Whether the Implementation Notes retry claim in memo2.md (startup retry via McpServerStarter; HealthChecker.startup_poll has no callers) holds; verify in code before writing.

## AI Implementation Instruction
Do not renumber or alter Decision wording except the specification references. Run the doc checkers before finishing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094449
- **Related target files**: `docs/10_adr/ADR-004-environment-failure-handling-policy.md`, `docs/10_adr/adr_04_failure-handling-supporting-sections.md`, `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr-index.md`

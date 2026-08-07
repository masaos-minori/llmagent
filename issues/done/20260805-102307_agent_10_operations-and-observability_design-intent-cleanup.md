# Reduce implementation-derived detail in docs/05_agent_10_*_operations-and-observability*.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to the operations-and-observability chapter (startup-and-health, audit-and-otel, workflow-observability, validation-and-troubleshooting parts 1-2, monitoring, rag-diagnostics-and-memory): keep runbook-relevant judgment; remove full command-output examples and metric-name inventories.

## Reason for Change
This chapter functions as the operational runbook (startup validation, MCP health, routing drift, where to look during an incident), which is safety/reliability-relevant and referenced directly by `routing.md`'s Deploy task mapping. It currently also carries full command-output transcripts and exhaustive metric-name tables that add maintenance burden without runbook value.

## Implementation Intent
Keep this chapter as the canonical source for startup/monitoring/incident-response judgment (per `memo-doc-agent-review.md` §「章間の正本ルール」: 起動・監視・障害対応 = `05_agent_10_operations-and-observability`). This chapter is directly used during Deploy tasks per `routing.md`, so runbook usability must not regress.

## Target Files or Areas
- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`
- `docs/05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `docs/05_agent_10_03_operations-and-observability-workflow-observability.md`
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md`
- `docs/05_agent_10_05_operations-and-observability-monitoring.md`
- `docs/05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

## Required Changes
- Keep: the purpose of startup validation, the meaning of OK/WARNING/FATAL/SKIPPED, conditions that should fail startup, operational judgment for MCP health / routing drift / tool-definition validation, the audit-log vs. `session_diagnostics` usage split, where to look during an incident, runbook-necessary procedures.
- Remove or compress: full command-output transcripts, log-field enumerations, exhaustive metric-name tables, plain monitoring-item listings.

## Acceptance Criteria
- All seven files follow the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」.
- No full command-output transcript or exhaustive metric-name table remains.
- Startup fail/warn conditions (OK/WARNING/FATAL/SKIPPED) remain explicit and actionable for an operator.
- `routing.md`'s reference to `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` (used for Deploy tasks) still resolves to usable runbook content after editing.

## Testing Expectations
Not required for behavior (documentation-only), but manually verify the runbook remains actionable — an operator following it during an incident should still be able to determine next steps. Run `python tools/check_agent_docs_consistency.py` after editing.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but is operationally sensitive (startup/incident runbook) — treat removal decisions conservatively.

## Out of Scope
- Other `docs/05_agent_*.md` chapters.
- Actual startup-validation code changes.
- `docs/05_agent_90_inconsistencies_and_known_issues.md` (separate issue).

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_10_operations-and-observability」. Because this chapter is a live runbook referenced from `routing.md`, do not remove any FATAL/WARNING condition or "what to check during an incident" content — only trim command-output examples and metric-name tables. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_10_operations-and-observability」
- Generated at: 2026-08-05

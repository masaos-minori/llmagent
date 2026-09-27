## Goal

Replace ADR-004's NC-037 cross-reference with the completed trace's findings and the owner's ruling on whether MCP-unreachable retry was intended (REQ-001, REQ-002).

## Scope

In scope: the Implementation Notes paragraph currently cross-referencing NC-037. Out of scope: any code change (deferred to a follow-up issue per REQ-002 if the owner rules retry was intended).

## Assumptions

N/A: none — the trace (Plan's Problem section) is confirmed evidence, re-verified this cycle.

## Design decisions

Replace the cross-reference paragraph with the trace's findings stated directly in the ADR, rather than pointing to governance_03 (which will no longer carry this entry after row 2 removes it).

## Alternatives considered

Leaving the cross-reference in place and only updating governance_03: rejected — the cross-reference would become dangling once NC-037 is removed (row 2), violating this repository's own "Removal-placeholder-reference policy" spirit for cross-document references.

## Implementation

### Target file

`docs/10_adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

1. Re-confirm the current Japanese-language paragraph at lines 461-463 (confirmed present, unchanged, as of this cycle) immediately before editing.
2. Present the owner with the completed trace's findings: no retry logic exists anywhere in the currently-exercised MCP-unreachable-handling paths (`scripts/agent/services/mcp_health.py`, `scripts/agent/services/mcp_tool_discovery.py::fetch_tools()`, and three additional adjacent files); the only retry logic anywhere in this area is `scripts/agent/http_lifecycle_health_checker.py::HealthChecker.startup_poll()`, which has zero callers.
3. Replace the paragraph with the trace's findings and the owner's ruling (either: "no-retry is the intentional, confirmed policy for these paths" or "retry was intended; tracked as a new follow-up issue: {path}").

### Method

Single-paragraph replacement, written in the same language (Japanese) as the surrounding Implementation Notes section, per this repository's existing mixed-language convention for this document.

### Details

- Confirmed current paragraph (re-verified this cycle, lines 461-463): "MCPサーバー到達不能時の再試行方針（固定単発再試行が意図的な簡素化か、設定可能な汎用Retry Policyが未実装なだけかの区別）については`docs/governance_03_issue-and-uncertainty-management.md`のNC-037を参照。"
- If the owner rules "intentional": replace with a statement that the current no-retry behavior across all traced paths is confirmed intentional, citing the trace's evidence (file list above).
- If the owner rules "retry was intended": replace with a statement of that ruling plus a reference to the new follow-up issue's path (created per REQ-002, not part of this row).

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually restore the prior cross-reference paragraph.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/10_adr/ADR-004-environment-failure-handling-policy.md` | Automated | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_adr_structure.py` | Pass, no new findings |

## Completion criteria

- The Implementation Notes state the completed trace's findings and the owner's ruling, with no dangling reference to NC-037 (AC-1).

## Out of scope

- Any code change to add retry logic (a separate follow-up issue if ruled).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-161727 | 20260927-161727 | Owner ruling obtained (via AskUserQuestion): current no-retry behavior across all traced paths confirmed as intentional policy; no follow-up issue needed |
| 2 | Add or update tests per Validation plan | Completed | 20260927-161727 | 20260927-161727 | N/A: documentation-only, automated checks per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-161727 | 20260927-161727 | N/A: documentation-only; docs checkers run instead |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-161727 | 20260927-161727 | N/A: this document's own target file IS the documentation being updated |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20260927-115931_nc037_confirm-whether-a-configurable-mcp-health-check-retry-policy-was-intended.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121645_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-124733
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md

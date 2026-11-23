# Perform the per-server mandatoriness assessment and record the registry authority

## Priority
Medium

## Summary
All 10 MCP servers carry the status-quo default in the component-mandatoriness registry, and the registry's authority and placement approval has no ledger entry. Record the maintainer's per-server assessment and the owner-list approval.

## Background
Source: governance Known Issues MCP-003 (Medium) and MCP-004 (Low). Evidence (`Explicit in code`, by reading): `registry/component_mandatoriness.yaml` has 10 entries, each with the rationale "Not assessed as satisfying Decision Group 3 item 10" and `startup_consequence: abort_startup`. ADR-004 Decision Group 3 item 13 requires an approved per-server classification, which the inventory says was never performed; `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` restates the criteria with no approval record. `config/documentation_canonical_sources.toml` registers the registry as the source for `mcp.component-mandatoriness`; the `governance_01` Resolution Matrix owner list for that row is a prepared proposal pending maintainer approval, with no ledger entry. The open question of whether `failure_category` stays uniformly `safety-integrity` or follows ADR-004 Group 2 item 7 (availability failure) overlaps Needs Confirmation NC-002.

## Problem
The approved-classification precondition of ADR-004 item 13 is unmet for all 10 servers, and the pending authority approval is not tracked.

## Reason for Change
Startup-abort behavior rests on classifications that nobody has assessed.

## Implementation Intent
A maintainer assessment is recorded per server through an approved change to the registry, and the registry owner list is approved or amended.

## Target Files or Areas
- `registry/component_mandatoriness.yaml`
- `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
- `docs/00_governance/governance_01_documentation-policy.md` (Resolution Matrix row `mcp.component-mandatoriness`)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (MCP-003, MCP-004)

## Required Changes
- Prepare the per-server Group 3 item 10 assessment for the maintainer, including the `failure_category` question as a proposal only.
- Record the approved result in the registry and the approval in the ADR record; approve or amend the Resolution Matrix owner list.
- Remove MCP-003 and MCP-004 from the inventory with evidence.

## Constraints
- No registry value changes before the maintainer's assessment; the registry is a contract file checked by the manifest and mandatoriness checkers.
- The maintainer states every approval; an implementer writes none.

## Acceptance Criteria
- [ ] Each of the 10 entries has an approved item-10 assessment or an explicit approved status-quo decision.
- [ ] The Resolution Matrix owner list for `mcp.component-mandatoriness` is approved or amended.
- [ ] MCP-003 and MCP-004 are removed from the inventory.

## Testing Expectations
Registry and manifest checkers pass (`generate_reference_table.py --check`, `check_canonical_sources.py`), and the mandatoriness registry tests pass.

## Documentation Impact
Yes: `agent_08_04`, `governance_01`, and the governance inventory.

## Out of Scope
- Changing which servers abort startup unless the recorded assessment decides so.
- The ADR-004 Group 2 item 7 justification itself (NC-002, carried in `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`).

## Dependencies
- Needs the maintainer's ADR-004 Group 2 item 7 decision (NC-002) for the `failure_category` question; there is no open issue to sequence against.

## Unresolved Questions
- `不明`: the assessment outcome per server and the `failure_category` rule.

## AI Implementation Instruction
Prepare the assessment as a proposal and stop for the maintainer before changing the registry. Do not write approval text.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261123-104602
- **Related target files**: `registry/component_mandatoriness.yaml`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, `docs/00_governance/governance_01_documentation-policy.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

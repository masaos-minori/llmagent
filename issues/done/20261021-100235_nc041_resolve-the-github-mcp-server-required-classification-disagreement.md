# Resolve the github MCP server required classification disagreement

## Priority
Medium

## Summary
Record an owner decision on whether `config/agent.toml` `[mcp_servers.github]` with `required = false` and `startup_mode = "none"` is an approved reclassification or a deviation, and make the classification table and the deployed configuration agree.

## Background
NC-041 is registered as an active item in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`. The classification table in `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` records `github` as `required` ("status quo default", not assessed against ADR-004 Decision Group 3 item 10). `config/agent.toml` currently sets `required = false` and `startup_mode = "none"` for `github`, introduced by commit `4e2442a75` ("disable the github MCP server until GITHUB_TOKEN is provisioned"). ADR-004 Decision Group 3 item 13 requires the `required` field to match the table and states that configuration alone cannot weaken a mandatory component.

## Problem
The classification table and the deployed configuration disagree for `github`. It is unknown whether the Fail-Closed handling of a disabled `github-mcp` has been assessed against Decision Group 3 item 10. No owner decision accompanies the configuration change.

## Reason for Change
An unresolved disagreement between an Accepted ADR contract and effective configuration is a canonical source conflict that startup validation may treat inconsistently. The active NC item has no assigned owner.

## Implementation Intent
Obtain an owner decision first; do not infer it. Then apply exactly one of two outcomes:

- Reclassify: update the `github` row of the classification table with an item 10 assessment, keeping `config/agent.toml` as is.
- Restore: set `required = true` and an appropriate `startup_mode` once `GITHUB_TOKEN` is provisioned.

The ADR Decision is not changed by either outcome.

## Target Files or Areas
- `config/agent.toml` (`[mcp_servers.github]`)
- `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` (classification table, `github` row)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (NC-041 entry)

## Required Changes
- Obtain and record the owner decision (reclassify or restore) and assign the NC item an owner.
- If reclassify: update the `github` row with the item 10 assessment (criteria met or not, observability of the disabled state, Fail-Closed rejection of calls).
- If restore: set `required = true` in `config/agent.toml` after `GITHUB_TOKEN` is provisioned; leave the table unchanged.
- Mark NC-041 resolved in the inventory and remove the inline marker from the source doc per the inventory checker rules.

## Constraints
- ADR-004 Decision Group 3 item 13: configuration alone cannot weaken a mandatory component; an approved architecture or specification change is required for reclassification.
- No secret value (`GITHUB_TOKEN`) may appear in any file or issue.

## Acceptance Criteria
- The classification table `github` row and `config/agent.toml` `required` agree.
- If reclassified, the table row states the item 10 assessment; if restored, startup validation passes with `github` as required.
- NC-041 is closed in the inventory with the decision recorded, and no inline marker remains in `agent_08_04`.
- The ADR-004 Decision text is unchanged.

## Testing Expectations
- `uv run python tools/check_needs_confirmation_inventory.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/generate_reference_table.py --check` (config/agent.toml is a generated-reference domain)
- `uv run python tools/check_adr_preservation.py`
- Manual verification: startup validation behavior for the chosen classification.

## Documentation Impact
Yes. Classification table row (intent and item 10 assessment, if reclassified) and the NC inventory entry. No change to ADR Decision text.

## Out of Scope
- Reclassifying any other MCP server.
- Changing ADR-004 text.
- Provisioning `GITHUB_TOKEN` itself.

## Dependencies
N/A: none (sibling-issue check: open issues `compat001` and `compat002` do not touch these files).

## Unresolved Questions
- Which outcome (reclassify or restore) does the owner choose?
- Who is the assigned owner for NC-041?
- When will `GITHUB_TOKEN` be provisioned, if restoring?

## AI Implementation Instruction
Do not choose the outcome; stop and report if no owner decision is recorded. Change only the files listed. Do not modify the ADR Decision. Do not print or store token values.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-100235
- **Related target files**: `config/agent.toml`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

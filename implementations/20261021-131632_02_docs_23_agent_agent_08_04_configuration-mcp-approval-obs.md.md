## Goal

Add the Decision Group 3 item 10 assessment to the `github` classification row in
`docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`. This is the reclassify
branch of REQ-001 / REQ-002.

## Scope

Only the `github` row of the Component Criticality Classification table in
`agent_08_04`. No other file is modified by this document.

## Assumptions

- The owner chose the reclassify outcome.
- The item 10 assessment genuinely satisfies every Decision Group 3 item 10 condition.
- ADR-004 Decision text stays unchanged.

## Design decisions

- The row's Reason cell must state each item 10 condition (met or not met): disabled-state
  observability, other required components stay safe, fallback assumed non-required.
- This document captures only the reclassify branch. The restore branch lives in the
  `config/agent.toml` row.

## Alternatives considered

Restore `required = true` in `config/agent.toml` instead (leave the table unchanged).
That is the `config/agent.toml` row's branch; this row covers only reclassify.

## Implementation

### Target file

`docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`

### Procedure

Replace the `github` row's Reason text with a Decision Group 3 item 10 assessment.

### Method

Edit the classification-table row at line 61.

### Details

- Current state (evidence: `agent_08_04` line 61):
  `| github | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |`.
- Replace the Reason cell with an item 10 assessment that states, per condition, met or
  not met:
  - Disabled-state observability — whether the disabled `github` state is observable.
  - Other required components stay safe under the disabled `github` state.
  - Fallback assumed non-required.
- Keep the classification column consistent with the assessment result. If the
  assessment shows any item 10 condition unmet, the row must not read `required = false`
  and the restore branch applies instead.
- Run `uv run python tools/check_docs_consistency.py --domain agent` and confirm no issues.

## Compatibility considerations

The classification table is the ADR-004 canonical record. `required` in
`config/agent.toml` must match it (ADR-004 Decision #13), so any reclassify here requires
the corresponding config change (or vice versa) to keep the two aligned.

## Security considerations

A reclassify to non-required is defensible only if Fail-Closed handling of the disabled
`github` state is verified. An unmet item 10 condition forces the restore branch rather
than weakening a mandatory component.

## Rollback considerations

Restore the original `Not assessed as satisfying Decision Group 3 item 10; status quo
default` text, or take the restore branch instead.

## Validation plan

- `check_docs_consistency.py --domain agent` — no issues found.
- `check_needs_confirmation_inventory.py` — NC-041 closed, no unregistered inline marker.

## Completion criteria

The `github` row states the item 10 assessment; `check_docs_consistency.py --domain agent`
passes; the classification agrees with `config/agent.toml`.

## Out of Scope

Changing `config/agent.toml`; reclassifying other MCP servers; ADR-004 Decision text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `github` row Reason with the item 10 assessment | Blocked | 20261021-205928 | — | Assumption false: owner chose restore (see Blocker Log); reclassify branch conflicts with procedure 01. No change applied. |
| 2 | Run validation sequence (`check_docs_consistency.py --domain agent`, `check_needs_confirmation_inventory.py`) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner decision (reclassify vs restore) not available to the planning agent | N/A: pending external governance decision | — |
| 2 | Re-verified 2026-10-21: owner chose restore, so the reclassify branch does not apply. No action taken. | N/A: branch not selected | 2026-10-21 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261021-100235_nc041_resolve-the-github-mcp-server-required-classification-disagreement.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-121020_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-131632
- **Related target files**: `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
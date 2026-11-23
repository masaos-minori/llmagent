## Goal

Remove the `EventBus Client Modules` section that presents the retired modules.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the section (heading at about line 155 and its paragraph). Neighbouring sections and the rest of the file stay.

## Assumptions

- Verified: the section describes `EventBusSubscriber` and `EventBusTopicAdminClient` and says no runtime component imports them; after retirement it describes nothing that exists.
- Verified: no other part of the file or an anchor link points at the section (checked with `rg` before the edit).

## Design decisions

- Delete the section whole; do not add a replacement note (history and the Plan record the retirement).

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`docs/23_agent/agent_02_runtime-architecture.md`

### Procedure
1. Delete the heading and its paragraph; confirm no dangling link to the removed anchor.

### Method
One Edit.

### Details
- Run the documentation checkers (broken links, function references).

## Compatibility considerations

N/A: no behavior change.

## Security considerations

N/A: documentation only; no approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The section is gone and the checkers pass.

## Out of Scope

Other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (retire the two modules and match the documents)
- **Source issue**: issues/20261123-104603_gov004_eventbus-client-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-111218_gov004_eventbus-client-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-153647
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`

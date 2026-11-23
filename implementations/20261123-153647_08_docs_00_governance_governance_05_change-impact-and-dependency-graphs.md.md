## Goal

Drop the sentence that names the retired client modules from the `Not represented as an edge` list, keeping the statement that no runtime component calls the Event Bus.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the Agent, RAG or MCP to EventBus bullet (about lines 140-144).

## Assumptions

- Verified: the bullet says no runtime component calls the Event Bus, then names the subscriber and topic-admin modules as imported only by their unit tests; the second sentence is stale after retirement while the first stays true.

## Design decisions

- Keep the first statement and the sentence about `eventbus.sqlite` ownership; remove only the client-module sentence.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`

### Procedure
1. Edit the bullet as described.

### Method
One Edit.

### Details
- Run the documentation checkers.

## Compatibility considerations

N/A: no behavior change.

## Security considerations

N/A: documentation only; no approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The bullet no longer names the modules and still says no runtime component calls the Event Bus.

## Out of Scope

Other dependency-graph text.

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
- **Related target files**: `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`

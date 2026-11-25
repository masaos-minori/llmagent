## Goal

Add the outcome states `STOPPING` (new), `EXIT_UNCONFIRMED` (new), `SIGNAL_NOT_DELIVERED` (new) to `LifecycleState` and extend `_VALID_TRANSITIONS` so shutdown outcomes can be represented per server (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 2 is not listed in R3-ownership's Phases)

## Assumptions
- No test pins the `LifecycleState` member count (verified in the Plan's Step 5 predictable-fallout check), so adding members is additive.
- The invalid pairs pinned by `tests/agent/test_lifecycle.py:685-696` (`FAILED -> RUNNING`, `STOPPED -> RUNNING`) stay invalid.

## Design decisions
- The new members are transport-layer outcome states mirroring the existing `TerminationOutcome` vocabulary (`scripts/agent/http_lifecycle_errors.py:46`); the enum itself does not import the errors module.
- Transitions added: `RUNNING` -> `STOPPING` (new); `STOPPING` (new) -> {STOPPED, `EXIT_UNCONFIRMED` (new), `SIGNAL_NOT_DELIVERED` (new)}; the unconfirmed states -> `STARTING` (re-termination) or `STOPPED` (confirmed on a later pass).

## Alternatives considered
- Reusing `FAILED` for unconfirmed outcomes — rejected: `FAILED` means startup failure, and conflating it loses the restart-recommendation distinction in `/mcp status` (REQ-009).

## Implementation
### Target file
`scripts/agent/lifecycle.py`

### Procedure
Add three members to `LifecycleState` (values `stopping`, `exit_unconfirmed`, `signal_not_delivered`) at `:26-30`; extend `_VALID_TRANSITIONS` (`:33-46`) with the transition sets listed in Design decisions.

### Method
Literal enum extension plus dict-literal entries; no behavior change in `assert_valid_transition` itself — the table is the contract.

### Details
- Keep the existing entries unchanged; add `RUNNING` -> `STOPPING` (new) to the `RUNNING` entry, add a `STOPPING` (new) entry, and add entries for the three unconfirmed states.
- Do not add self-transitions for the unconfirmed states beyond the re-termination path (`EXIT_UNCONFIRMED -> STARTING`), which the coordinator's repeated shutdown uses.

## Compatibility considerations
- Additive enum members: consumers that switch on state values (`scripts/agent/services/mcp_status.py:146`) get new branches in Phase 5; no existing value changes.

## Security considerations
- N/A: no security-sensitive behavior in a state enum.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit tests for the new transitions and for the still-invalid pinned pairs: `uv run pytest tests/agent/test_lifecycle.py` (tests written in Phase 1, see REQ-011).

## Completion criteria
- The three states exist, the extended transitions validate, the pinned invalid pairs still raise `ValueError`, and the test file passes.

## Out of Scope
- Enforcement of rejection-without-mutation in the router (REQ-007, its own row).
- Mapping the new states into `/mcp status` (REQ-009, Phase 5 rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests written first in Phase 1 (REQ-011) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs rows cover the state-machine description |

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
- **Requirement ID**: REQ-006 (new outcome states, no global `STOPPED`)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `scripts/agent/lifecycle.py`

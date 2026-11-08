## Goal
Rename the retry-policy key and clarify the constant-wait semantics in the Retry Mechanism and Loader Validation Rules sections of `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` (`REQ-003`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 13 only: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`.

## Assumptions
- Landing order: wfaudit004 procedure `implementations/20261108-151141_03_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md` lands first (its new bullet is inserted after the numeric `retry_policy` bullet this row rewrites, and its verbatim quote of that bullet matches HEAD); `implementations/20261108-175155_09_...md` edits the Startup Recovery sentence at L165, disjoint. Re-anchor the numeric bullet by quoted text at execution time (plan Related Documents row).
- HEAD citations: Retry Mechanism bullets L131 `- Backoff strategy is currently implemented as "fixed" only`, L132 `- \`backoff_sec\`: Delay between retries`, the `retry_on` bullet ending `no backoff wait and no further attempt` (L133-135), and the numeric validation bullet at L153 (`retry_policy.max_attempts` and `retry_policy.backoff_sec` must both be integers ... `backoff_sec` at least 0).

## Design decisions
- Rename the key wherever it appears and state the constant-wait semantics that procedure 02 pins in the engine: the `fixed` strategy bullet gains an explicit "same delay on every retry" clause instead of being left as a bare label.
- The `retry_on` bullet's phrase "no backoff wait" becomes "no retry wait" so the doc uses one vocabulary for the delay after the rename.

## Alternatives considered
- Rename only the key tokens and leave the "fixed" bullet untouched: rejected — the plan row freezes this file's edits as naming "the key and the fixed-wait semantics", and the engine change (procedure 02) makes the constant behavior an explicit contract worth stating.

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure
Four bullet-level text edits, quoted-text anchored.

### Method
1. L131: `- Backoff strategy is currently implemented as "fixed" only` -> `- Backoff strategy is currently implemented as "fixed" only: the retry wait is the same delay on every attempt` (renders the `REQ-004` contract).
2. L132: `- \`backoff_sec\`: Delay between retries` -> `- \`retry_wait_sec\`: Delay between retries`.
3. `retry_on` bullet (HEAD L133-135): `is terminal at once — no backoff wait and no further attempt` -> `is terminal at once — no retry wait and no further attempt`.
4. Numeric validation bullet (HEAD L153): both occurrences -> `` `retry_policy.max_attempts` and `retry_policy.retry_wait_sec` must both be integers, not booleans, floats, or strings, with `max_attempts` at least 1 and `retry_wait_sec` at least 0``.

### Details
- After the edit, `grep -n backoff_sec docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` returns nothing.
- No section headings, list order, or other bullets change.

## Compatibility considerations
- wfaudit004 `151141_03` quotes the old L153 text verbatim; landing this row first would break its anchor (plan freezes the opposite order).

## Security considerations
- No change: documentation-only edit.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- Docs checkers per `routing.md` "When to run which tool" (docs staleness/structure checks) on this file after all landing-order rows are applied.

## Completion criteria
- `REQ-003`: no `backoff_sec` token in the file; the Retry Mechanism and validation bullets describe the renamed key with constant-wait semantics.

## Out of Scope
- The `retry_on`, `require_approval`, and stage-deadline bullets beyond the phrase in Method step 3.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-211937
- **Related target files**: docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md

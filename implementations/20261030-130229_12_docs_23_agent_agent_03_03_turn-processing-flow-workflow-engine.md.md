## Goal

Update the "Task Status Transitions" table, the "Retry Mechanism" section, and the Operational Notes of `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` to describe the implemented retry policy and the terminal-failure contract (`REQ-010`, documentation of the policy and outcomes).

## Scope

- Modify only `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`.
- Intent and failure behavior only; no code restatement (`skills/DESIGN.md` "Avoid implementation-reference duplication", "Docs content policy — remove").

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): Plan Phase 5, after the code rows. The wfrecovery001 and wflease001 Plans edit other sections of the same document (state semantics, resume, startup recovery); the transitions table is edited by both the wfrecovery001 Plan and this one, so the later change reconciles the rows. Execution order follows the Plan's phases, not `seq`.
- Owner decisions (2026-10-30): timeouts and LLM-level failure results are not retried by default; UNK-01 and UNK-02 are settled, so no Needs Confirmation marker is required for them.
- Current text (checked in this cycle): the transitions table has a row "A retryable stage exhausts `max_attempts`, or a stage times out" written `halted` by the engine, and a row "The engine completes but the turn reported a soft error" written `failed` by the turn adapter; the Retry Mechanism section says retry is determined by `retryable`, `max_attempts`, and `backoff_sec`; Operational Notes bullet one describes `halted`.
- ADR-001 decision 6 stays true under the shipped configuration and is not edited here (it is not a row of this Plan).

## Design decisions

- State the outcome mapping once: terminal halt and timeout produce a failed turn with the stable kinds workflow_halted and workflow_timeout in the turn result and the turn-end audit, regardless of callbacks; the callback is a notification.
- Replace the "soft error" row: an LLM-level failure now fails the stage inside the engine, so the engine is the single writer of `failed` for it and no downgrade by the adapter remains.

## Alternatives considered

- N/A: documentation row; wording follows the Plan.

## Implementation

### Target file

`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure

1. Update the "Task Status Transitions" table (`:74-95`): the timeout and exhaustion row reflects policy-based eligibility; the soft-error row is replaced by the engine-written `failed` for LLM-level failures; add the turn-level kinds workflow_halted and workflow_timeout and the rule that the returned result and the turn-end audit carry them with or without `on_error`.
2. Update "Retry Mechanism" (`:119-130`): describe the optional `retry_policy.retry_on` kinds (`exception`, `timeout`, llm_failure), the shipped default (exception only), that each failed attempt consumes `max_attempts`, the deadline-versus-inner-timeout distinction, and that no retry follows a completed non-READ tool call in the same attempt.
3. Update the Operational Notes bullet on `halted` (`:149`) so it no longer says a timeout always halts without retry; refer to the policy.

### Method

- Keep the prose at the level of intent and boundaries; do not restate class or function names beyond the configuration key.

### Details

- Do not touch the sections owned by the other Plans (state semantics, resuming tasks, startup recovery).
- Run the docs checkers named in the Validation plan after the edit.

## Compatibility considerations

- Documentation only; the description follows the shipped defaults, so it stays accurate if the owner later changes `retry_on`.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/check_docs_japanese.py`

## Completion criteria

- The three passages describe the implemented policy and contract; all docs checkers pass.

## Out of Scope

- ADR-001 and the other sections of this document (other Plans).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the transitions table, retry mechanism, and operational notes | Pending | — | — | Plan Phase 5 |
| 2 | Run the documentation checkers (`routing.md` Tools "When to run which tool") | Pending | — | — | |

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
- **Requirement ID**: REQ-010 (retry policy and failure-contract documentation)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md

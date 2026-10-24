## Goal

Update the workflow-engine chapter to reflect that turn-end work and workflow teardown moved out of
the engine adapter into the Orchestrator's bracket (`REQ-005`, `REQ-012`).

## Scope

- **In-Scope**: the passages describing the `verify` stage's role, `execute_turn`'s `finally`, and
  `_handle_workflow_halt`'s state clearing.
- **Out-of-Scope**: the task-status state machine (turn003's `### Task Status Transitions`), the
  stage table at `:79`, the retry mechanism at `:82-88` (turn002's passages), and any other
  chapter.

## Assumptions

- The production changes land first; this doc mirrors them.
- The `verify` stage still exists in the engine signature (`workflow_loader.py:49`) but is now a
  no-op for turn-end work.

## Design decisions

- State the three moved responsibilities (turn-end emit, workflow deactivation, halt-state clear)
  as owned by the caller's bracket, without restating turn002's/turn003's passages.

## Alternatives considered

`N/A: restating the stage table or task-status machine was rejected as turn002's/turn003's frozen
passages; only the turn-end/teardown claims are in scope.`

## Implementation

### Target file

`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure

1. State that the `verify` stage no longer performs turn-end work; `turn_end` is emitted by the
   Orchestrator's `_execute_turn` bracket instead.
2. State that `execute_turn`'s `finally` no longer deactivates the workflow; the caller's bracket
   does.
3. State that `_handle_workflow_halt` no longer clears `ctx.workflow.*`; the caller's bracket does.
4. Do not restate the task-status state machine, the stage table at `:79`, or the retry mechanism
   at `:82-88`.

### Method

Prose edits only; keep the chapter's structure and its cross-references to turn002/turn003 intact.

### Details

- The `verify` stage remains in the engine signature; explain why it is now empty rather than
  removing it (follow-up candidate in the Plan's out-of-scope table).
- Keep consistency with `agent_03_01` (its lifecycle-bracket wording) and `agent_02` (ownership).

## Compatibility considerations

Documentation-only; no code or API change. Read against the post-implementation code state.

## Security considerations

`N/A: documentation-only; no auth, secret, or input-handling change.`

## Rollback considerations

`N/A: revert the commit to this doc.`

## Validation plan

- `tools/check_docs_structure.py` passes.
- `tools/check_docs_consistency.py --domain agent` passes.
- `tools/check_docs_content_policy.py` passes.
- See `routing.md` Tools "When to run which tool" for the authoritative list.

## Completion criteria

The chapter states the `verify` stage no longer does turn-end work, `execute_turn`'s `finally` no
longer deactivates the workflow, and `_handle_workflow_halt` no longer clears `ctx.workflow.*`,
each attributed to the caller's bracket; the three doc checkers pass; turn002's/turn003's
passages are unchanged.

## Out of Scope

The other three doc passages (`agent_10_02`, `agent_03_01`, `agent_02`), the code changes, and the
test changes are handled by sibling documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the three moved-responsibility passages (`Implementation > Procedure`) | Pending | — | — | run after the code change it describes |
| 2 | Add or update tests per Validation plan | N/A: documentation-only | | | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | the three doc checkers above |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this document |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Phase 3 | turn002 (`plans/20261023-102728_plan.md`) and turn003 (`plans/20261023-125756_plan.md`) own the stage table and task-status machine | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005` (adapter turn-end ownership removed), `REQ-012` (documentation)
- **Source issue**: `issues/20261021-093421_turn004_turn-end-events-duplicated-or-missing.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-140855_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-092307
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

## Goal

Extend the Orchestrator bullet in the runtime-architecture chapter to name the turn bracket and
the `AuditEventEmitter` as the single `turn_end` emitter (`REQ-012`).

## Scope

- **In-Scope**: the Orchestrator bullet at `:102` ("Issues audit log events (`turn_start`,
  `turn_end`)").
- **Out-of-Scope**: the `AgentContext` paragraph at `:105` (stays accurate), the Shutdown
  constraint at `:160-165` (another Plan's frozen passage), and any other chapter.

## Assumptions

- The production change lands first; this doc mirrors it.
- `:102` is an anchor against the current file; read the surrounding bullet to place the edit.

## Design decisions

- Extend the existing bullet minimally to name the owner (`_execute_turn` bracket) and the single
  emitter (`AuditEventEmitter`), keeping the chapter's terse bullet style.

## Alternatives considered

`N/A: restructuring the architecture chapter was rejected — this is a one-bullet correctness
correction, and the Shutdown constraint belongs to another Plan.`

## Implementation

### Target file

`docs/23_agent/agent_02_runtime-architecture.md`

### Procedure

1. At `:102`, extend the Orchestrator bullet so it states the `_execute_turn` bracket issues the
   audit log events and that `AuditEventEmitter` is the single emitter of `turn_end` on every exit
   path.
2. Leave the `AgentContext` paragraph at `:105` unchanged (still accurate: turn id is `None`
   between turns because the bracket guarantees it).
3. Do not edit `:160-165` (the Shutdown constraint owned by another Plan).

### Method

Prose edit to a single bullet; keep the chapter's structure and cross-references intact.

### Details

- This chapter is reached from `docs/00_index.md:39`/`:146` ("AgentREPL class structure" and
  "AgentContext / DI hub"); keep those mappings valid.
- The extended bullet must not contradict `agent_10_02` (which names the same owner/emitter).

## Compatibility considerations

Documentation-only; no code or API change. Read against the post-implementation code state.

## Security considerations

`N/A: documentation-only; no auth, secret, or input-handling change.`

## Rollback considerations

`N/A: revert the commit to this doc.`

## Validation plan

- `tools/check_docs_structure.py` passes.
- `tools/check_docs_consistency.py --domain agent` passes.
- See `routing.md` Tools "When to run which tool" for the authoritative list.

## Completion criteria

`:102` names the `_execute_turn` bracket and `AuditEventEmitter` as the single `turn_end` emitter;
`:105` remains accurate; `:160-165` is unchanged; the two doc checkers pass.

## Out of Scope

The other three doc passages (`agent_10_02`, `agent_03_01`, `agent_03_03`), the code changes, and
the test changes are handled by sibling documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the Orchestrator bullet (`Implementation > Procedure`) | Pending | — | — | run after the code change it describes |
| 2 | Add or update tests per Validation plan | N/A: documentation-only | | | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | the two doc checkers above |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this document |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Phase 3 | `:160-165` is another Plan's frozen Shutdown constraint | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-012` (documentation: ownership/single-emitter wording)
- **Source issue**: `issues/20261021-093421_turn004_turn-end-events-duplicated-or-missing.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-140855_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-092307
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`

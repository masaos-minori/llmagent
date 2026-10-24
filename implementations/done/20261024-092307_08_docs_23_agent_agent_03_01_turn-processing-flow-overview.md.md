## Goal

Update the turn-processing-flow overview so it presents `turn_start` … `turn_end` as one bracket
owned by `Orchestrator._execute_turn` that runs on every exit path (`REQ-012`).

## Scope

- **In-Scope**: the turn-lifecycle bracket statements at `:43` and `:77`.
- **Out-of-Scope**: the stage/retry sequence text at `:82-89` and `:104-113` (turn002's frozen
  passage), and any other chapter.

## Assumptions

- The production bracket lands first; this doc mirrors it.
- `:43` and `:77` are anchors against the current file; read the surrounding prose to locate them.

## Design decisions

- Make the minimal wording change to the two bracket statements so the overview names the owner and
  the every-exit-path property, without restating the stage machine (turn002's territory).

## Alternatives considered

`N/A: re-writing the stage/retry sequence was rejected as turn002's frozen passage; only the
lifecycle-bracket claims are in scope.`

## Implementation

### Target file

`docs/23_agent/agent_03_01_turn-processing-flow-overview.md`

### Procedure

1. At `:43`, update the turn-lifecycle statement to say the Orchestrator's `_execute_turn` wraps
   the turn in a single `turn_start` … `turn_end` bracket that runs on every exit path.
2. At `:77`, update the companion statement consistently with `:43`.
3. Do not touch `:82-89` or `:104-113` (turn002's stage/retry passage).

### Method

Prose edits only; keep the chapter's existing structure and cross-references intact.

### Details

- This chapter is reached from `docs/00_index.md:148` ("Agent REPL flow / tool execution"); keep
  that mapping valid.
- The change must not contradict the `verify`-stage text that turn002 owns.

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

`:43` and `:77` describe the single turn bracket owned by `_execute_turn` running on every exit
path; the two doc checkers pass; `:82-89` / `:104-113` are unchanged.

## Out of Scope

The other three doc passages (`agent_10_02`, `agent_03_03`, `agent_02`), the code changes, and the
test changes are handled by sibling documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two bracket statements (`Implementation > Procedure`) | Pending | — | — | run after the code change it describes |
| 2 | Add or update tests per Validation plan | N/A: documentation-only | | | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | the two doc checkers above |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this document |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Phase 3 | turn002 (`plans/20261023-102728_plan.md`) also edits `:82-89`; respect its passage | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-012` (documentation: turn lifecycle bracket ownership)
- **Source issue**: `issues/20261021-093421_turn004_turn-end-events-duplicated-or-missing.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-140855_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-092307
- **Related target files**: `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`

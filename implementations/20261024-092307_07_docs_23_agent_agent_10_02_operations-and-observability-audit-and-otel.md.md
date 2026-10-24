## Goal

Correct the audit/observability doc so it states that exactly one `turn_end` event is emitted per
user turn on every exit path (success, soft LLM error, workflow halt, escaping exception,
cancellation) and names the Orchestrator as the bracket owner (`REQ-012`).

## Scope

- **In-Scope**: the lifecycle-event passage at `:32`, the `turn_end` field table at `:56`, and a
  Known Limitations entry at `:73`.
- **Out-of-Scope**: `## Keywords` (not edited) and any non-audit passage.

## Assumptions

- The production change (one `turn_end` owned by `_execute_turn`) lands first; this doc mirrors it.
- Line numbers `:32`, `:56`, `:73` are anchors against the current file; read the surrounding
  prose/table to locate them precisely before editing.

## Design decisions

- Keep the doc's existing structure and tone; make the minimal wording change so the claim matches
  the code, and extend the field table rather than restructuring it.

## Alternatives considered

`N/A: rewriting the whole chapter was rejected — the change is a narrow correctness correction to
three spots, and the rest of the chapter is already accurate.`

## Implementation

### Target file

`docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`

### Procedure

1. At `:32`, rewrite the lifecycle-event passage (currently states "two events … for each turn")
   to state that the Orchestrator's `_execute_turn` bracket emits exactly one `turn_end` on every
   exit path, including failure and cancellation, and that `AuditEventEmitter` is the single
   emitter.
2. At `:56`, extend the `turn_end` field table with the `error_kind` values a failure path produces
   (e.g. `'PREMATURE_EOF'`, `'RuntimeError'`, `'CancelledError'`) and a note that `elapsed_ms` is
   measured from turn entry (`time.perf_counter()` before `emit_turn_start`), not process uptime.
3. At `:73`, add a Known Limitations entry explaining that historical `audit.log` records keep the
   old doubled turn count and the wrong (uptime-based) `elapsed_ms`, and name the cutoff date after
   this change lands.
4. Do not edit `## Keywords`.

### Method

Prose and table edits only; no new sections. Keep comments/log guidance consistent with the
chapter's existing style.

### Details

- The Known Limitations entry feeds `UNK-05` (operator asked for the log range); keep it factual
  and non-prescriptive.
- The field-table extension must not alter the existing column layout that `check_docs_structure.py`
  validates.

## Compatibility considerations

Documentation-only; no code or API change. Read against the post-implementation code state.

## Security considerations

`N/A: documentation-only; no auth, secret, or input-handling change.`

## Rollback considerations

`N/A: revert the commit to this doc.`

## Validation plan

- `tools/check_docs_structure.py` passes.
- `tools/check_docs_content_policy.py` passes.
- `tools/check_docs_quality.py` passes.
- See `routing.md` Tools "When to run which tool" for the authoritative list.

## Completion criteria

`:32` states one `turn_end` per exit path owned by the Orchestrator bracket, `:56`'s field table
includes `error_kind` values and the turn-relative meaning of `elapsed_ms`, and `:73` carries the
historical-log Known Limitations entry; all three doc checkers pass.

## Out of Scope

The other three doc passages (`agent_03_01`, `agent_03_03`, `agent_02`), the code changes, and the
test changes are handled by sibling documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the three passages (`Implementation > Procedure`) | Pending | — | — | run after the code change it describes |
| 2 | Add or update tests per Validation plan | N/A: documentation-only | | | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | the three doc checkers above |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this document |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-012` (documentation: one `turn_end` per exit path, owner, fields)
- **Source issue**: `issues/20261021-093421_turn004_turn-end-events-duplicated-or-missing.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-140855_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-092307
- **Related target files**: `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`

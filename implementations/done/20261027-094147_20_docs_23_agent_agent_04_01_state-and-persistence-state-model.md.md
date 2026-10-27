## Goal

Update the existing architectural contract `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` to document the atomic turn-persistence boundary (`REQ-001`, `REQ-003`, `REQ-004`). The doc currently describes `AgentSession` save rules, the conversation-history/DB relationship, and `/undo` semantics; this row adds the turn-level all-or-nothing write contract, the dedicated persistence error type, the compensation/delete semantics, and the memory-rollback rule so the state/persistence model reflects the single-writer-per-turn boundary introduced by this Plan.

## Scope

- **In-Scope** (`docs/23_agent/agent_04_01_state-and-persistence-state-model.md` only):
  - Add a "Turn Persistence Boundary" subsection under the Session Persistence area describing the all-or-nothing turn write unit (`REQ-001`).
  - Document the dedicated persistence error type and its propagation (`REQ-003`).
  - Document compensation semantics: delete only the turn's rows (`message_id >= marker`) and restore memory to the turn-start snapshot (`REQ-004`).
  - Cross-reference the existing `/undo` and compression sections without altering their meaning.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The boundary body (`scripts/agent/turn_persistence.py`, seq 01).
  - The facade factory (`scripts/agent/session.py`, seq 03).
  - Memory snapshot/restore API (`scripts/agent/context.py`, seq 04).
  - Write-routing callers (orchestrator.py seq 05; conversation_state_manager.py seq 06; llm_turn_runner.py seq 07; tool_round_completion.py seq 08; workflow_engine_adapter.py seq 09).

## Assumptions

- The doc is an existing canonical source under `docs/23_agent/`; edits must preserve its front matter, headings, and cross-references (`docs/23_agent/agent_00_document-guide.md`).
- The turn-persistence boundary is the sole writer of `messages` rows during a turn (`AC-001`), so the doc's "single writer" statement can be tightened to "one boundary per turn".
- Content policy forbids implementation-detail warnings that should point to a canonical source; the doc stays at the architectural-contract level.

## Design decisions

- **Add a focused subsection, do not rewrite.** Insert a "Turn Persistence Boundary" subsection into the existing Session Persistence area so the current session/DB model remains intact and the new all-or-nothing contract layers on top. This matches how the doc already isolates concerns (Message Saving Rules, DiagnosticStore Separation, etc.).
- **Contract-level language, not code.** The doc states the boundary contract (one writer per turn, compensation deletes only the turn's rows, memory rolls back to the turn-start snapshot) without embedding method bodies or line numbers, keeping it a canonical architectural reference rather than a per-implementation note.
- **Preserve `/undo` semantics.** The existing `undo_last_turn()` description is left unchanged; the new boundary compensation is a distinct, failure-triggered path, not the manual `/undo` command.

## Alternatives considered

- **New standalone doc.** Rejected: `docs/23_agent/agent_00_document-guide.md` already maps "persistence vs memory state" to this file; the turn-persistence contract belongs with the existing session/persistence state model, not as a sibling doc.
- **Put the contract in the history-compression doc.** Rejected: that doc (agent_04_02) covers compression; the turn-write atomicity and compensation are a state/persistence concern owned here.

## Implementation

### Target file

`docs/23_agent/agent_04_01_state-and-persistence-state-model.md` (existing; extended)

### Procedure

1. Under the Session Persistence area, add a "Turn Persistence Boundary" subsection after the existing Message Saving Rules section.
2. State the all-or-nothing turn write contract: one boundary materialized per turn owns every `messages` write; a failure anywhere in the turn rolls the whole turn back (`REQ-001`, `AC-001`).
3. Document the dedicated persistence error type (`REQ-003`) and that it propagates from the boundary to the orchestrator and then to the REPL for distinct surfacing.
4. Document compensation semantics: only the turn's rows (`message_id >= marker`) are deleted, earlier rows are retained, and `ctx.conv.history` is restored element-wise to the turn-start snapshot (`REQ-004`, `AC-002`, `AC-004`).
5. Cross-reference the existing `/undo` and compression sections without changing them.
6. Run the doc validation sequence (`routing.md`).

### Method

The doc's Session Persistence area currently covers `AgentSession` ownership of the `sessions` and `messages` tables, the save rules (`save`, `save_many`, `replace_messages`), and the in-memory `ctx.conv.history` ↔ DB synchronization. The turn-persistence boundary (seq 01) sits between the turn-path writers and the repository: it captures the turn-start `message_id` marker and a memory snapshot at turn entry (via the turn_boundary factory, seq 03), routes every turn write through it, and on a persistence failure compensates by deleting only the turn's rows and restoring memory. The dedicated error type (turn_persistence.py, seq 01) is raised instead of a raw DB error and re-raised by the orchestrator (orchestrator.py, seq 05) so the REPL (repl_input_loop.py, seq 10) can surface it distinctly (`REQ-007`).

```text
Turn-path writers (manager, runner, round, adapter)
        ↕ all writes routed through one boundary per turn
TurnPersistence boundary (turn-start marker + memory snapshot)
        ↕ on success: commit per phase; on failure: delete turn rows + restore memory
session_message_repo (session.sqlite: messages)
```

### Details

- **`REQ-001` / `AC-001` (one writer per turn):** the boundary (seq 01) is materialized once per turn via the factory (seq 03); every turn-path write routes through it, so the turn commits atomically or not at all.
- **`REQ-003` / `AC-003` (dedicated error type):** a DB failure inside the turn is surfaced as the dedicated persistence error type, never a raw DB error; it propagates to the orchestrator (seq 05) and the REPL (seq 10).
- **`REQ-004` / `AC-002` / `AC-004` (compensation + rollback):** compensation deletes only `message_id >= marker` rows (retaining earlier rows) and restores `ctx.conv.history` element-wise to the turn-start snapshot.
- **Backward compatibility:** the existing `/undo`, save-rules, and session/memory responsibility sections are unchanged; the new subsection is purely additive.

## Compatibility considerations

- Additive subsection; front matter, headings, and existing cross-references preserved. No change to sibling docs.

## Security considerations

- Documentation-only; no new input surface or secret handling.

## Rollback considerations

- Revert the doc edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| structural integrity | Format/headings/fences/front matter | `uv run python tools/check_docs_quality.py` | Clean |
| structure | File size, H1 count, front matter, Related Docs, link reachability | `uv run python tools/check_docs_structure.py docs/23_agent/agent_04_01_state-and-persistence-state-model.md` | Clean |
| content policy | No implementation-detail warnings pointing away from canonical source | `uv run python tools/check_docs_content_policy.py --strict` | Clean |
| domain consistency | Doc claims (symbols, save rules) match `scripts/` and `config/agent.toml` | `uv run python tools/check_docs_consistency.py --domain agent` | Clean |

## Completion criteria

- The doc has an additive "Turn Persistence Boundary" subsection covering the all-or-nothing turn write, the dedicated persistence error type, compensation (`message_id >= marker` delete + memory rollback), and cross-references to `/undo`/compression.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, and `check_docs_consistency.py --domain agent` all pass clean.

## Out of Scope

- Boundary body (`scripts/agent/turn_persistence.py`, seq 01).
- Facade factory (`scripts/agent/session.py`, seq 03).
- Memory snapshot/restore (`scripts/agent/context.py`, seq 04).
- Write-routing callers (orchestrator.py seq 05; conversation_state_manager.py seq 06; llm_turn_runner.py seq 07; tool_round_completion.py seq 08; workflow_engine_adapter.py seq 09).
- REPL surfacing (`scripts/agent/repl_input_loop.py`, seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the state/persistence doc with the turn-persistence boundary contract | Pending | — | — | Additive subsection |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Doc checkers |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This doc |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`

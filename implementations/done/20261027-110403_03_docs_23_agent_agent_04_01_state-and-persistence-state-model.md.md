## Goal

Update the existing architectural contract `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` to document the load-time orphan-tool-call repair this Plan introduces. The doc currently describes `AgentSession` save rules, the conversation-history/DB relationship, and `/undo` semantics; this row adds a "Load-Time Orphan Repair" subsection under the Session Persistence area so resumed sessions make clear that an interrupted tool round (assistant `tool_calls` with no matching tool rows) is repaired in memory at load, that synthesized rows carry an identifiable marker, and that the repair is memory-only and idempotent.

## Scope

- **In-Scope** (`docs/23_agent/agent_04_01_state-and-persistence-state-model.md` only):
  - Add a "Load-Time Orphan Repair" subsection under the Session Persistence area describing the interrupted-tool-round repair (memory-only synthesis, marker content, idempotency).
  - State that synthesized rows are not persisted until the next compression `replace_messages`, and that the DB row count is unchanged after load.
  - Cross-reference the existing `/undo` and compression sections without altering their meaning.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The repair body (`scripts/agent/services/session_restore.py`, row 01).
  - The regression tests (`tests/agent/test_session_restore.py`, row 02).

## Assumptions

- The doc is an existing canonical source under `docs/23_agent/`; edits must preserve its front matter, headings, and cross-references (`docs/23_agent/agent_00_document-guide.md`).
- The repair is confined to the load boundary `restore_session`; it does not change the turn write path (the frozen turn001 Plan prevents new orphans).
- Content policy forbids implementation-detail warnings that should point to a canonical source; the doc stays at the architectural-contract level.

## Design decisions

- **Add a focused subsection, do not rewrite.** Insert the new subsection into the existing Session Persistence area so the current session/DB model remains intact and the repair behavior layers on top. This matches how the doc already isolates concerns (Message Saving Rules, DiagnosticStore Separation, etc.).
- **Contract-level language, not code.** The doc states the repair contract (interrupted round → paired after load, memory-only synthesis with a marker, idempotent, floor preserved) without embedding method bodies or line numbers, keeping it a canonical architectural reference.
- **Preserve `/undo` semantics.** The existing `undo_last_turn()` description is left unchanged; the load-time repair is a distinct, failure-triggered path, not the manual `/undo` command.

## Alternatives considered

- **New standalone doc.** Rejected: `docs/23_agent/agent_00_document-guide.md` already maps "persistence vs memory state" to this file; the repair behavior belongs with the existing session/persistence state model, not as a sibling doc.
- **Put the repair in the history-compression doc.** Rejected: that doc (agent_04_02) covers compression; the load-time orphan repair is a restore/persistence concern owned here.

## Implementation

### Target file

`docs/23_agent/agent_04_01_state-and-persistence-state-model.md` (existing; extended)

### Procedure

1. Under the Session Persistence area, add a "Load-Time Orphan Repair" subsection after the existing "Session Persistence" subsection (Responsibility Boundary area), before the "Relationship Between Conversation History and Database" subsection.
2. State what an interrupted tool round looks like after resume: an assistant `tool_calls` row with no following `role="tool"` rows is repaired in memory at load so the restored history is always paired.
3. Document the synthesis: missing tool-result rows are synthesized in `tool_calls` order with an identifiable interrupted-marker content, conforming to the message whitelist so `replace_history` validation keeps them.
4. Document that the repair is memory-only and idempotent — no DB rows are written at load, so the `messages` table row count is unchanged and loading twice yields identical history; synthesized rows are persisted only by the next compression `replace_messages`.
5. Note that the `undo_floor` boundary index accounts for synthesized rows inserted before the compression boundary, so `/undo` still lands on the correct turn.
6. Cross-reference the existing `/undo` and compression sections without changing them.
7. Run the doc validation sequence (`routing.md`).

### Method

The doc's Session Persistence area currently covers `AgentSession` ownership of the `sessions` and `messages` tables, the save rules (`save`, `save_many`, `replace_messages`), and the in-memory `ctx.conv.history` ↔ DB synchronization. The load-time repair sits between `fetch_messages` and `replace_history` in `restore_session`: it detects assistant rows whose `tool_calls` ids are unanswered by a following tool-row run, synthesizes the missing tool rows in memory with a marker, logs a warning, and shifts the `undo_floor` index accordingly. The subsection below records this as an architectural contract.

```text
fetch_messages (session.sqlite: messages)
        v
assistant row with tool_calls, no matching tool rows?
        v  yes
synthesize missing tool rows (marker content, whitelist-conformant)
        v
replace_history(paired)   # memory-only; DB row count unchanged
        v
undo_floor shifted by synthesized rows before the boundary
```

### Details

- **Interrupted round (paired after load):** an assistant `tool_calls` row with no following `role="tool"` row (the hard-kill crash case) is repaired at load; the restored history ends with the assistant row followed by synthesized tool rows whose `tool_call_id`s match.
- **Synthesis + marker:** synthesized rows use `role="tool"`, the original `tool_call_id`, and an identifiable interrupted-marker content; they are whitelist-conformant so `replace_history` validation retains them.
- **Memory-only + idempotent:** no DB rows are written at load; the `messages` table row count is unchanged, and a second load reproduces identical history. Synthesized rows persist only via the next compression `replace_messages`.
- **Floor preservation:** the `undo_floor` boundary index accounts for synthesized rows inserted before the compression boundary, so `/undo` still lands on the correct turn.
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

- The doc has an additive "Load-Time Orphan Repair" subsection covering the interrupted-tool-round repair, synthesis with marker, memory-only/idempotent behavior, and `undo_floor` preservation, plus cross-references to `/undo`/compression.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, and `check_docs_consistency.py --domain agent` all pass clean.

## Out of Scope

- Repair body (`scripts/agent/services/session_restore.py`, row 01).
- Regression tests (`tests/agent/test_session_restore.py`, row 02).
- Turn write-path changes (frozen turn001 Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the state/persistence doc with the load-time repair contract | Completed | — | 20261027-183919 | Additive subsection Additive Load-Time Orphan Repair subsection; 4 doc checkers clean; tests/docs 20 passed |
| 2 | Add or update tests per Validation plan | Completed | — | 20261027-183919 | N/A: documentation only Additive Load-Time Orphan Repair subsection; 4 doc checkers clean; tests/docs 20 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261027-183919 | Doc checkers Additive Load-Time Orphan Repair subsection; 4 doc checkers clean; tests/docs 20 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261027-183919 | This doc Additive Load-Time Orphan Repair subsection; 4 doc checkers clean; tests/docs 20 passed |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-007`
- **Source issue**: `issues/20261026-224729_turn002_repair-orphan-tool-call-rows.md`
- **Source plan**: `plans/20261027-071546_turn002_repair-orphan-tool-call-rows.md`
- **Generated at**: 20261027-110403
- **Related target files**: `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`
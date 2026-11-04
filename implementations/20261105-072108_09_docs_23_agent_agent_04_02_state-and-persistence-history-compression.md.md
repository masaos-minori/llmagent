## Goal

State in `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md` that ephemeral system rows are not persisted by compression and that the canonical summary row is persisted and restored on load, updating the "Compression Persistence Model" section which currently says only that the summary row is persisted with `role=system` (REQ-006; AC-7).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 5 documentation; the release unit `summary-persist-restore` covers Phases 3–4 only).

## Assumptions

- The document has a "### Compression Persistence Model" subsection describing how the compressed set is written through `replace_messages`; it currently notes the summary row is persisted with `role=system` and says nothing about ephemeral rows or restore.
- The change lives in `scripts/agent/session_message_repo.py` (Row 03): `replace_messages` skips messages carrying `_ephemeral` or `_memory_injected`, and the persisted boundary stays the maximum persisted `message_id`.
- The companion load document [agent_04_01](agent_04_01_state-and-persistence-state-model.md) states what `/session load` restores; this document cross-references it rather than restating the restore rule.

## Design decisions

- Extend the "### Compression Persistence Model" subsection with two sentences: the compressed set no longer persists ephemeral system rows (only `role`, `content`, `tool_calls`, `tool_call_id` are stored), and the single canonical summary row is persisted and later restored by `/session load`.
- Cross-reference [agent_04_01](agent_04_01_state-and-persistence-state-model.md) for the restore side so the persist/restore contract spans both documents without duplication.

## Alternatives considered

- Add a new subsection: rejected; the non-persistence rule is part of the compression persistence model, so it belongs inside the existing subsection.
- Describe the ephemeral filter implementation here: rejected; the model document states the rule, not the code path (which is documented in the repository/implementation procedures).

## Implementation
### Target file
`docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`

### Procedure
1. Locate the "### Compression Persistence Model" subsection.
2. Insert the ephemeral-row non-persistence sentence and the restore cross-reference into that subsection, after the existing statement that the summary row is persisted with `role=system`.

### Method
Insert after the existing summary-row sentence:
> A compression no longer persists ephemeral system rows: `replace_messages` stores only `role`, `content`, `tool_calls`, and `tool_call_id`, so `_ephemeral` / `_memory_injected` rows are dropped from the stored set. The single canonical summary row (`role=system`, content starting with the shared `CONVERSATION_SUMMARY_PREFIX`) is persisted and is restored by `/session load` after the current system prompt; every other persisted system row is still dropped. See [agent_04_01](agent_04_01_state-and-persistence-state-model.md).

### Details
- `CONVERSATION_SUMMARY_PREFIX` and `is_conversation_summary` are declared in Row 01; `/session load` is prose, not a source symbol.
- Stale-reference marks: no source symbol is created here; the rule is documented.

## Compatibility considerations

- Additive prose within one existing subsection; the compression schema description is extended, not rewritten.
- Overlap with the compression-compensation Plan (shared `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` via cross-reference and `session_message_repo.py` in a different method): this edit is prose in the compression model section.

## Security considerations

- Restating that ephemeral rows are not persisted confirms the stored session cannot accumulate an ephemeral memory block across sessions.

## Rollback considerations

- Remove the two inserted sentences.

## Validation plan

- `uv run python tools/check_docs_quality.py docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent` — no findings; the referenced [agent_04_01] link resolves.

## Completion criteria

- The "Compression Persistence Model" subsection states that ephemeral system rows are not persisted and that the canonical summary row is persisted and restored on load; the docs checkers report no findings.

## Out of Scope

- The shared constant/predicate (Row 01), restore (Row 02), persistence code (Row 03), the tests (Rows 04–07), and the generated reference regeneration (Row 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | docs checkers |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this row |

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
- **Requirement ID**: `REQ-006` (document persistence model), `AC-7`
- **Source issue**: issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115505_restoresummary001_session-load-drops-summary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-072108
- **Related target files**: docs/23_agent/agent_04_02_state-and-persistence-history-compression.md

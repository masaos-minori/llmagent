## Goal

State in `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` what `/session load` restores — the current system prompt plus exactly one canonical conversation-summary row — and which system rows are not restored and why (untrusted restore), so the load behavior matches the change in `issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md` (REQ-006; AC-7).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 5 documentation; the release unit `summary-persist-restore` covers Phases 3–4 only).

## Assumptions

- The document already has a "## Responsibility Boundary" section containing "### Load-Time Orphan Repair" and "### Relationship Between Conversation History and Database"; the load section currently describes orphan repair and the undo floor only, not system or summary rows.
- The canonical summary row is the one restored after the current system prompt, recognized by the shared constant `CONVERSATION_SUMMARY_PREFIX` and rebuilt canonically (declared in `scripts/agent/history.py`, Row 01); the value is `"[Conversation summary]"`.
- The companion compression document [agent_04_02](agent_04_02_state-and-persistence-history-compression.md) states the non-persistence of ephemeral rows, so this document cross-references it rather than restating the persistence rule.

## Design decisions

- Add one new subsection, "### Restored Rows on Load" (new), directly after "### Load-Time Orphan Repair" and before "### Relationship Between Conversation History and Database", so the load contract sits next to the existing load path without disturbing the orphan-repair description.
- Describe the restored history as `[current system prompt, canonical summary row?, ...non-system rows]` in prose and a small diagram, list the drop rule for every other persisted system row with the untrusted-restore reason, and cross-reference [agent_04_02](agent_04_02_state-and-persistence-history-compression.md) for the ephemeral-row non-persistence.

## Alternatives considered

- Extend the existing "### Load-Time Orphan Repair" bullets: rejected; that section is scoped to interrupted-tool-call repair, and a dedicated subsection keeps the summary-restoration rule discoverable and reviewable on its own.
- Put the persistence rule here too: rejected; the non-persistence of ephemeral rows belongs with the compression model in [agent_04_02](agent_04_02_state-and-persistence-history-compression.md).

## Implementation
### Target file
`docs/23_agent/agent_04_01_state-and-persistence-state-model.md`

### Procedure
1. Insert the "### Restored Rows on Load" (new) subsection after the "### Load-Time Orphan Repair" subsection and before "### Relationship Between Conversation History and Database".
2. In the subsection, state the restored order, the single-summary rule, the drop rule for other system rows with the untrusted-restore reason, and the cross-reference to the non-persistence rule.
3. Add one sentence to the "### Session Persistence Design Intent" paragraph that `/session load` now keeps the compressed session's summary.

### Method
```text
### Restored Rows on Load

`/session load` rebuilds `ctx.conv.history` from stored messages as
[current system prompt, canonical summary row?, ...non-system rows]:

- **Current system prompt.** The live prompt replaces any persisted prompt row.
- **Canonical summary row.** Exactly one persisted system row whose content starts
  with the shared `CONVERSATION_SUMMARY_PREFIX` (`"[Conversation summary]"`) is
  restored immediately after the current prompt, rebuilt with only `role` and
  `content`. When several summary-shaped rows are persisted, only the most recent
  is kept and a warning names the dropped count.
- **Non-system rows.** Every user, assistant, and tool row is restored.
- **Other persisted system rows are dropped.** Only the owner-assigned current
  prompt is trusted; any other persisted system row cannot become an instruction
  (untrusted restore). This is the behavior the Plan preserves.

Ephemeral system rows (`_ephemeral` / `_memory_injected`) are not persisted, so they
are never restored; see [agent_04_02](agent_04_02_state-and-persistence-history-compression.md).
```
The added sentence for the design-intent paragraph: "`/session load` keeps the conversation summary of a compressed session: one canonical summary row, recognized by a shared constant, is restored after the current prompt, while every other persisted system row is still dropped."

### Details
- The new subsection references `CONVERSATION_SUMMARY_PREFIX` and `is_conversation_summary`, which are declared in Row 01; the command names `/session load` and `/undo` are prose, not source symbols.
- Stale-reference marks: "### Restored Rows on Load" (new) is a new doc subsection; no source symbol is created here.

## Compatibility considerations

- Additive prose; no existing section is rewritten except one added sentence in the design-intent paragraph. The orphan-repair description is untouched.
- Overlap with the compression-compensation Plan (shared `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`): this edit adds a new subsection in the Load boundary; the documents are edited in different sections.

## Security considerations

- The drop rule restates the untrusted-restore policy: only the current prompt is trusted, and the accepted residual risk is bounded to one canonical summary row.

## Rollback considerations

- Remove the new subsection and the added design-intent sentence.

## Validation plan

- `uv run python tools/check_docs_quality.py docs/23_agent/agent_04_01_state-and-persistence-state-model.md`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent` — no findings; the document still parses and the front-matter `related` links resolve.

## Completion criteria

- The document states that `/session load` restores the current prompt plus exactly one canonical summary row, that other persisted system rows are dropped with the untrusted-restore reason, and that ephemeral system rows are not persisted; the docs checkers report no findings.

## Out of Scope

- The shared constant/predicate (Row 01), restore (Row 02), persistence code (Row 03), the tests (Rows 04–07), and the generated reference regeneration (Row 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261105-143257 | added '### Restored Rows on Load' after '### Load-Time Orphan Repair'; added design-intent sentence |
| 2 | Add or update tests per Validation plan | Completed | — | 20261105-143257 | N/A: documentation N/A: documentation row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-143257 | docs checkers quality/content_policy/consistency clean; structure checker has 1 pre-existing agent_13 size finding at HEAD (26421>26145), not introduced here |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-143257 | this row this row |

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
- **Requirement ID**: `REQ-006` (document load behavior), `AC-7`
- **Source issue**: issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115505_restoresummary001_session-load-drops-summary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-072108
- **Related target files**: docs/23_agent/agent_04_01_state-and-persistence-state-model.md
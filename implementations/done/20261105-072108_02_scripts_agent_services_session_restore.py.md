## Goal

In `restore_session`, restore exactly one canonical conversation-summary row right after the current system prompt, rebuild it canonically, drop any extra summary-shaped rows with a warning, and still drop every other persisted system row; update `_boundary_to_index` so the restored summary counts as a restored row (REQ-002, REQ-003; AC-2, AC-3, AC-4). The no-current-prompt branch stays unchanged.

## Scope
**Release unit**: summary-persist-restore (Phase 4; released with the persistence change in Row 03 so the boundary arithmetic agrees with what is restored).

## Assumptions

- `restore_session` (`scripts/agent/services/session_restore.py`, line ~157) builds the history as `system_msgs + [m for m in repaired if m["role"] != "system"]` when `ctx.conv.system_prompt_content` is set; the else branch (line ~165) is left untouched (UNK-01).
- `is_conversation_summary` (new) is imported from `agent.history`; a persisted summary row read by `fetch_messages` carries only `role`/`content`, so the canonical rebuild is `{"role": "system", "content": <content>}`.
- `_boundary_to_index` (line ~110) receives the original snapshot `messages` and slices `messages[:n_snapshot]`; the summary row is unchanged by orphan repair, so it is visible there.

## Design decisions

- Select summary rows with `is_conversation_summary`, keep the last (`summary_rows[-1]`, the most recent compression per the Plan), rebuild it with only `role`/`content`, and insert it between the current prompt and the non-system rows. Extra summary rows are dropped with one warning naming the count and session id (Risk: multi-summary data loss).
- In `_boundary_to_index`, count snapshot system rows that are NOT the restored canonical summary (`not is_conversation_summary(m)`), so the restored summary is treated as present in the rebuilt history rather than subtracted as a dropped row. When no canonical summary exists the count is unchanged, so the forged-row and no-summary cases keep their existing indices.

## Alternatives considered

- Restore every summary-shaped row: rejected; the Plan requires exactly one (the single-summary rule), and keeping several would widen context and risk a second summary after the next compression.
- Recompute the whole index formula: rejected; only the `system_count` term changes, so the post-snapshot rows are unaffected and the existing clamp path is preserved.

## Implementation
### Target file
`scripts/agent/services/session_restore.py`

### Procedure
1. Import the predicate: add `from agent.history import is_conversation_summary` (new symbol declared in Row 01).
2. In `restore_session`, inside the `if ctx.conv.system_prompt_content:` branch, before building `non_system`, select the canonical summary rows from `repaired`, keep the last, warn on extras, and rebuild it canonically.
3. In `_boundary_to_index`, exclude the restored canonical summary from `system_count`.

### Method
```python
from agent.history import is_conversation_summary
```
```python
# module-level helper (keeps restore_session at radon grade B, Plan mitigation):
def _restored_summary_msgs(
    repaired: list[LLMMessage], session_id: int
) -> list[LLMMessage]:
    summary_rows = [m for m in repaired if is_conversation_summary(m)]
    if len(summary_rows) > 1:
        logger.warning(
            "Session %s dropped %d extra summary row(s); kept the most recent",
            session_id,
            len(summary_rows) - 1,
        )
    return (
        [{"role": "system", "content": summary_rows[-1]["content"]}]
        if summary_rows
        else []
    )
```
```python
# inside restore_session, system_prompt set branch:
non_system = [m for m in repaired if m["role"] != "system"]
await ctx.conv.replace_history(
    system_msgs + _restored_summary_msgs(repaired, session_id) + non_system
)
```
```python
# _boundary_to_index:
system_count = sum(
    1
    for m in snapshot_msgs
    if m.get("role") == "system" and not is_conversation_summary(m)
)
```

### Details
- The rebuild keeps only `role`/`content`, so the restored row passes `replace_history`'s untrusted validation with no ephemeral or extra keys (Plan Assumptions).
- A forged system row whose content does not start with `CONVERSATION_SUMMARY_PREFIX` (e.g. `"[summary]"`) is not recognized, stays dropped, and is still counted in `system_count` — the existing `test_system_message_appears_exactly_once_when_db_also_has_system` and `test_undo_floor_converts_boundary_to_index` keep passing.
- Stale-reference marks: `is_conversation_summary` is resolved from Row 01's `(new)` declaration; no local `(new)` mark is needed.

## Compatibility considerations

- The no-current-prompt branch is unchanged; the prompt-set branch adds one optional row and one warning path only when a canonical summary exists.
- The new public predicate is listed by the regenerated reference doc (Row 10).

## Security considerations

- Recognition is by the shared prefix via `is_conversation_summary`, so an attacker-added system row without the prefix still cannot become an instruction (untrusted-restore). The accepted residual risk is bounded to one canonical row, rebuilt with only `role`/`content`.

## Rollback considerations

- Revert the import, the summary-selection block, and the `system_count` change.

## Validation plan

- `uv run pytest tests/agent/test_session_restore.py -v` — new summary-restored, forged-row, multi-summary, undo-boundary, and idempotency tests (Row 04) fail before and pass after; existing restore tests pass unchanged.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`.
- Baseline grade: `restore_session` must stay at grade B (`radon cc`); the summary selection lives in the module-level helper `_restored_summary_msgs()` (Plan mitigation line: "selection goes into a helper and the grade stays B") — an inline block with the canonical-rebuild ternary pushed `restore_session` to C (11) in the cycle measurement, so the helper form is the one applied.

## Completion criteria

- After a restore with a current prompt, the rebuilt history is `[current prompt, canonical summary?, ...non-system rows]` with exactly one summary row, canonical shape, no extra keys; extra summary rows are dropped with a warning; other persisted system rows are still dropped; the no-prompt branch is unchanged; `_boundary_to_index` counts the restored summary as present.

## Out of Scope

- The shared constant/predicate definition (Row 01), the persistence ephemeral filter (Row 03), the restore tests (Row 04), and the docs (Rows 08–10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261105-132959 | 20261105-133108 | release unit summary-persist-restore helper _restored_summary_msgs; changed session_restore.py |
| 2 | Add or update tests per Validation plan | Completed | — | 20261105-133108 | covered by Row 04 N/A: no test change needed; covered by Row 04; existing tests/agent/test_session_restore.py 23 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261105-133108 | 20261105-140654 | unit end full-suite run pending (release unit) unit-end diff-cover 82%: missing lines 146 (session_restore) / 174,182 (session_message_repo) are new branches first tested by Row 04-06; gate re-evaluated at those cycles' full-suite runs before archival unit gate passed at Row 05 full-suite run (diff-cover 100%) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-133108 | load behavior in Row 08 N/A: load-behavior docs are Row 08 target |

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
- **Requirement ID**: `REQ-002` (restore one canonical summary after the prompt), `REQ-003` (boundary counts the restored row), `AC-2`, `AC-3`, `AC-4`
- **Source issue**: issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115505_restoresummary001_session-load-drops-summary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-072108
- **Related target files**: scripts/agent/services/session_restore.py
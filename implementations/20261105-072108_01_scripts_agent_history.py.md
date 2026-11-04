## Goal

Promote the private `_SUMMARY_PREFIX` constant to a public `CONVERSATION_SUMMARY_PREFIX` (new) and add a public `is_conversation_summary` (new) predicate that recognizes a canonical summary row, then use both in `_split_system_msgs` and `_build_summary_msg` (REQ-001; AC-1). No copy of the prefix string remains anywhere in `scripts/`.

## Scope
**Release unit**: N/A: not part of a release unit (Phase 2; the `summary-persist-restore` unit covers Phases 3–4 only).

## Assumptions

- `_SUMMARY_PREFIX = "[Conversation summary]"` (line 31) is used only by `_split_system_msgs` (line 247) and `_build_summary_msg` (line 262) in `scripts/`; a consumer scan (`tools/scan_change_consumers.py --seed _SUMMARY_PREFIX`) lists only `history.py` and the two prose docs, none of which import the name.
- The predicate takes a message dict and reproduces the existing `content.startswith(_SUMMARY_PREFIX)` test plus the role `system` guard, so restore can recognize the same shape without re-deriving it.
- `is_conversation_summary` (new) is module-level (not a `HistoryManager` method) so `session_restore.py` (Row 02) can import it directly without instantiating compression.

## Design decisions

- Promote the constant to `CONVERSATION_SUMMARY_PREFIX` (new) (module-level, all-caps, unchanged value), matching the `INTERRUPTED_TOOL_CALL_MARKER` style in `session_restore.py`, so it reads as a shared contract rather than an internal detail.
- Add `is_conversation_summary(message: dict) -> bool` returning `message.get("role") == "system" and str(message.get("content") or "").startswith(CONVERSATION_SUMMARY_PREFIX)`. The single constant is the one home of the shape rule, so compression and restore cannot drift from each other (Risk: shape-rule drift).

## Alternatives considered

- Keep `_SUMMARY_PREFIX` private and pass the literal into restore: rejected; the plan forbids a copied prefix string, and restore would need a second import path to a private name.
- Make the predicate a `HistoryManager` method: rejected; restore holds no `HistoryManager`, and a module-level function is importable without constructing the manager.

## Implementation
### Target file
`scripts/agent/history.py`

### Procedure
1. Rename the module constant on line 31 from `_SUMMARY_PREFIX` to `CONVERSATION_SUMMARY_PREFIX` (new), keeping the value `"[Conversation summary]"`.
2. Update the two call sites to the new name: `_split_system_msgs` (line 247) and `_build_summary_msg` (line 262).
3. Add the public predicate `is_conversation_summary` (new) at module level, immediately after the constant and before `HistoryCompressionError`.

### Method
```python
CONVERSATION_SUMMARY_PREFIX = "[Conversation summary]"


def is_conversation_summary(message: dict) -> bool:
    """Return True when *message* is a canonical conversation-summary row.

    A summary row has role ``system`` and content that starts with the shared
    `CONVERSATION_SUMMARY_PREFIX` (new); this is the single shape rule shared by
    compression and restore.
    """
    return (
        message.get("role") == "system"
        and str(message.get("content") or "").startswith(CONVERSATION_SUMMARY_PREFIX)
    )
```

### Details
- `_split_system_msgs` replaces `content.startswith(_SUMMARY_PREFIX)` with `content.startswith(CONVERSATION_SUMMARY_PREFIX)`; `_build_summary_msg` builds `f"{CONVERSATION_SUMMARY_PREFIX}\n{summary_text}"`.
- The predicate short-circuits on a non-`system` role, so a forged user/assistant row never counts as a summary (Security: untrusted-restore).
- Stale-reference marks: `CONVERSATION_SUMMARY_PREFIX` (new) and `is_conversation_summary` (new) are created here; `_SUMMARY_PREFIX` is the pre-existing name being renamed.

## Compatibility considerations

- Additive: the constant keeps its value and `_split_system_msgs`/`_build_summary_msg` behavior is unchanged; only the internal identifier changes.
- The new public predicate is listed by `generate_reference_table.py --type agent` once the source is regenerated (Row 10).

## Security considerations

- The predicate narrows recognition to the shared prefix, so a local actor cannot gain system authority except through the owner-accepted residual risk already bounded to one canonical row (Plan Risks).

## Rollback considerations

- Revert the rename and remove the predicate.

## Validation plan

- `uv run pytest tests/agent/test_history_manager.py tests/agent/test_history_selection_policy.py -v` — predicate tests (Row 07) and the existing compression tests pass.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`.
- Confirm `CONVERSATION_SUMMARY_PREFIX` (new) appears once across `scripts/` (AC-1) and `rg _SUMMARY_PREFIX scripts/` returns nothing.

## Completion criteria

- `CONVERSATION_SUMMARY_PREFIX` (new) holds the literal once in `scripts/`; `is_conversation_summary` (new) recognizes only a `system` row whose content starts with it; `_split_system_msgs` and `_build_summary_msg` use both; no `_SUMMARY_PREFIX` reference remains in `scripts/`.

## Out of Scope

- Compression turn selection and summary building.
- Restore (Row 02), persistence (Row 03), the round-trip/persistence tests (Rows 04–06), the predicate tests themselves (Row 07), and the prose/generated docs (Rows 08–10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | predicate tests live in Row 07 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | predicate listed in Row 10 |

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
- **Requirement ID**: `REQ-001` (public constant + predicate for the summary shape), `AC-1`
- **Source issue**: issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115505_restoresummary001_session-load-drops-summary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-072108
- **Related target files**: scripts/agent/history.py

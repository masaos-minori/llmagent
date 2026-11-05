## Goal

Add tests to `tests/agent/test_history_manager.py` that fail on the pre-change code and pass after it (REQ-001; AC-1): the public predicate `is_conversation_summary` recognizes only a `system` row whose content starts with the shared prefix, and compression still produces exactly one canonical summary row through the promoted constant.

## Scope
**Release unit**: N/A: not part of a release unit (Phase 2; the release unit `summary-persist-restore` covers Phases 3–4 only).

## Assumptions

- The file already provides `_make_manager`, `_history`, and the `TestCompressWithLLM` class, which asserts summary rows by the literal prefix text in several compression tests; those stay valid.
- `is_conversation_summary` (new) is importable as `from agent.history import is_conversation_summary`; the existing import line is `from agent.history import HistoryManager`.
- Compression routes the summary through `_build_summary_msg`, so the produced summary row content starts with the promoted constant value `"[Conversation summary]"`.

## Design decisions

- `TestIsConversationSummaryPredicate` (new) pins the four recognition cases: accept a `system` row whose content starts with the prefix; reject a `system` row without the prefix, a non-`system` role, and a `user`/`assistant` row that merely contains the prefix text.
- One compression test re-uses `_make_manager` with a mocked LLM and asserts the produced summary row is a `system` row whose content starts with the canonical prefix, confirming `_build_summary_msg` still emits the canonical shape through the promoted constant.

## Alternatives considered

- Import the constant value vs. the literal text: rejected; the Plan keeps tests on the literal prefix text, and the value is stable under the rename, so the predicate test reads the literal directly.
- Test the predicate as a `HistoryManager` method: rejected; the predicate is module-level, so the test imports it directly.

## Implementation
### Target file
`tests/agent/test_history_manager.py`

### Procedure
1. Add the import of the new predicate next to the existing `from agent.history import HistoryManager`.
2. Add the `TestIsConversationSummaryPredicate` (new) class with the four recognition tests.
3. Add one compression test asserting the canonical summary row is produced through the promoted constant.

### Method
```python
from agent.history import HistoryManager, is_conversation_summary
```
```python
class TestIsConversationSummaryPredicate:
    def test_accepts_system_row_with_prefix(self) -> None:
        assert is_conversation_summary(
            {"role": "system", "content": "[Conversation summary]\nprior turns"}
        )

    def test_rejects_system_row_without_prefix(self) -> None:
        assert not is_conversation_summary(
            {"role": "system", "content": "[summary] forged"}
        )

    def test_rejects_non_system_role(self) -> None:
        assert not is_conversation_summary(
            {"role": "user", "content": "[Conversation summary]\nprior turns"}
        )

    def test_rejects_user_row_containing_prefix_text(self) -> None:
        assert not is_conversation_summary(
            {"role": "assistant", "content": "say [Conversation summary]"}
        )
```
The compression assertion reuses `TestCompressWithLLM`'s mocked-LLM path and checks the produced summary row:
```python
async def test_compress_produces_canonical_summary_row(self) -> None:
    mgr = _make_manager(char_limit=1, compress_turns=2)
    result, history = await mgr.compress(_history(...))
    summary_rows = [m for m in history if is_conversation_summary(m)]
    assert len(summary_rows) == 1
    assert summary_rows[0]["content"].startswith("[Conversation summary]")
```

### Details
- The predicate tests are additive; the existing compression tests keep passing, confirming only the canonical shape is newly pinned.
- Stale-reference marks: `is_conversation_summary` (new) is declared in Row 01 and imported here; the new test class and functions are marked (new).

## Compatibility considerations

- Purely additive tests; no existing test is modified, so the regression set (`test_history_manager.py`, `test_history_selection_policy.py`) keeps its pinned behaviors.

## Security considerations

- The `test_rejects_non_system_role` (new) and `test_rejects_user_row_containing_prefix_text` (new) cases pin that authority is granted only to a `system` row, matching the untrusted-restore design.

## Rollback considerations

- Remove the new import binding addition, the predicate test class, and the compression assertion.

## Validation plan

- `uv run pytest tests/agent/test_history_manager.py tests/agent/test_history_selection_policy.py -v` — the predicate and canonical-summary tests fail on the pre-change code (the name does not exist) and pass after; existing tests pass unchanged.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria

- `is_conversation_summary` (new) accepts only a `system` row whose content starts with the shared prefix and rejects every other case; compression produces exactly one canonical summary row through the promoted constant; the new tests fail before and pass after the change.

## Out of Scope

- The shared constant definition (Row 01), restore (Row 02), persistence (Row 03), the round-trip and repository tests (Rows 05–06), and the docs (Rows 08–10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261105-143130 | added TestIsConversationSummaryPredicate (4 cases) + canonical-shape compression test |
| 2 | Add or update tests per Validation plan | Completed | — | 20261105-143130 | this row this row; 80 targeted passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-143130 | red demo (import error on HEAD worktree); full suite 11555 passed; diff-cover 100%; ruff clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-143130 | N/A: no test-file docs in scope |

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
- **Requirement ID**: `REQ-001` (predicate + canonical-summary tests), `AC-1`
- **Source issue**: issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115505_restoresummary001_session-load-drops-summary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-072108
- **Related target files**: tests/agent/test_history_manager.py
## Goal

Make `AgentSession.set_title` report whether the title was actually persisted: return
`True` after a successful UPDATE/commit and `False` when no active session row exists
(`session_id is None`), replacing today's silent no-op (REQ-1). DB failures keep raising
`sqlite3.Error` unchanged.

## Scope

- Only `AgentSession.set_title` in `scripts/agent/session.py` (current def at L190-200;
  the Plan's "L170-180" line numbers are stale — behavior claims verified against
  current source).
- Return annotation `None` → `bool`; the `_title_pending = False` bookkeeping stays at
  the top of the method, including on the no-op path (behavior preserved).
- No change to truncation (`title[:SESSION_TITLE_MAX_CHARS]`), the `SQLiteHelper`
  usage, or the `Raises sqlite3.Error` semantics.

## Assumptions

- Bool return over raising an error (Plan Assumptions): the four current call sites
  (`cmd_session.py` L209, `commands/session_title.py` L41, `services/conversation_service.py`
  L33, `services/session_title.py` L59) all call `set_title` as a statement and discard
  the return; `conversation_service.py` L33 is deliberately best-effort.
- Cross-batch overlap: `scripts/agent/session.py` is also a target of
  `plans/20261027-070403_turn001...` and `plans/20261027-074657_undo002...` (not members
  of this `memo2.md` batch). The Plan already adjudicates these Compatible — members
  disjoint (this row touches only `set_title`); that adjudication is reused, not
  re-litigated.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this Plan; no sequencing dependency against sibling plans in the batch.
- The consumer (`cmd_session.py` rename branch) is updated in the sibling document
  `implementations/20261028-001446_02_scripts_agent_commands_cmd_session.py.md`; until
  that document is implemented, its branch discards the new return value exactly like
  today, so this change alone is behavior-neutral.

## Design decisions

- `return False` only for the no-active-session early exit; DB errors keep propagating
  as `sqlite3.Error` (contract: False means "nothing to update", not "update failed").
- Keep clearing `_title_pending` before the branch check — preserves the current
  bookkeeping on both paths (Plan Design section).

## Alternatives considered

- Raise a new "no active session" exception: rejected — would force error handling at
  the three best-effort call sites that do not want it (Plan Assumptions).
- Auto-creating a session row on rename: rejected — Plan OUT-1.

## Implementation

### Target file

`scripts/agent/session.py`

### Procedure

Change `set_title`'s return contract from `None` to `bool` and state it in the
docstring.

### Method

Edit only `AgentSession.set_title`; no other member of the class is touched.

### Details

```python
def set_title(self, title: str) -> bool:
    """Set the session title (truncated to SESSION_TITLE_MAX_CHARS).

    Returns True when the title was persisted, False when there is no active
    session (session_id is None). Raises sqlite3.Error on DB failure.
    """
    self._title_pending = False
    if self.session_id is None:
        return False
    with SQLiteHelper("session").open(write_mode=True) as db:
        db.execute(
            "UPDATE sessions SET title = ? WHERE session_id = ?",
            (title[:SESSION_TITLE_MAX_CHARS], self.session_id),
        )
        db.commit()
    return True
```

## Compatibility considerations

- All four existing call sites discard the return value; `None` → `bool` is
  source- and type-compatible for them (mypy: discarding a return value is allowed).
- Tests that mock `set_title` (`tests/agent/commands/test_agent_cmd_session.py`) stay
  valid: a `MagicMock` return is truthy, so existing rename-success assertions are
  unaffected.
- Implement this document before
  `implementations/20261028-001446_02_scripts_agent_commands_cmd_session.py.md`: the
  consumer branch checks the return value and needs the bool contract in place.

## Security considerations

- No change to SQL text or parameterization; `?` placeholder binding preserved.

## Rollback considerations

- Single-method revert (`git checkout -- scripts/agent/session.py`); safe only if the
  sibling consumer document is not yet implemented or is reverted first, because its
  branch depends on the bool return.

## Validation plan

| Check | Command | Expected |
|-------|---------|----------|
| type gate | `uv run mypy scripts/` | clean — new annotation flows to all call sites |
| lint | `uv run ruff check . && uv run ruff format --check .` | clean |
| contract tests | `uv run pytest tests/agent/commands/test_agent_cmd_session.py -k rename` | green (cases added by `implementations/20261028-001446_03_tests_agent_commands_test_agent_cmd_session.py.md`) |
| regression | `uv run pytest tests/agent/test_agent_session.py` | green unchanged |
| full suite | `uv run pytest` | green |

## Completion criteria

- `set_title` returns `False` for `session_id is None` with no DB write, `True` after
  UPDATE/commit; docstring states the contract (Plan AC REQ-1).
- `sqlite3.Error` propagation unchanged.
- mypy/ruff clean; existing session/command test suites green.

## Out of Scope

- Session-row auto-creation (Plan OUT-1).
- Title parsing/truncation changes (Plan OUT-2 / Constraints).
- Behavior changes at the other call sites (Plan Out of scope — they ignore the return).
- `tests/agent/test_agent_session.py` (not a target row; run read-only as regression).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Test authoring is owned by document _03 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: Plan has no docs row |

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
- **Requirement ID**: REQ-1
- **Source issue**: `issues/20261026-225105_sess007_validate-session-rename-result.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-085735_sess007_validate-session-rename-result.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-001446
- **Related target files**: `scripts/agent/session.py`

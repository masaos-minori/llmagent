## Goal

Make the `/session rename` branch in `_SessionMixin._cmd_session` consume `set_title`'s
new bool return: `False` → print the existing-style validation error and suppress the
success line; `True` → print the unchanged success line (REQ-2, REQ-4).

## Scope

- Only the `rename` sub-branch of `_cmd_session` (`scripts/agent/commands/cmd_session.py`,
  current branch at L202-213).
- The empty-title validation path (L204-206), the `SESSION_TITLE_MAX_CHARS` import, and
  the success line format `f"Session renamed: {title[:SESSION_TITLE_MAX_CHARS]!r}"`
  stay byte-identical.
- Other `/session` sub-branches (`load`, `delete`, `list`, usage) are not touched.

## Assumptions

- Reuses the branch's own `write_validation_error("/session rename <title>")` pattern
  (Plan Reference Files L204-206); `write_validation_error` prints
  `  [usage] <text>` (`scripts/agent/commands/output_port.py` L133-135), so the failure
  line is visually consistent with the empty-title case.
- `sqlite3.Error` from `set_title` keeps propagating out of the branch exactly as
  today — no new try/except is added (Plan REQ-1 keeps DB failures as exceptions).
- Depends on `implementations/20261028-001446_01_scripts_agent_session.py.md` being
  implemented first: with the old `None` return, `not persisted` would be `True` and
  every real rename would print the failure line.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this Plan's `cmd_session.py` row; no sibling sequencing constraint.

## Design decisions

- Capture the return into a local (`persisted`) and early-return on falsy — the branch
  already owns the validation-error + `return` shape, so the failure path mirrors the
  empty-title path one-for-one (Plan Design section).

## Alternatives considered

- A distinct "no active session" error message: rejected — Plan REQ-2 and Risk
  mitigation require reusing the existing usage-hint string exactly.
- Silently skipping the success line without any error output: rejected — the user
  would get no signal at all (Plan Problem: false success must become a visible
  failure).

## Implementation

### Target file

`scripts/agent/commands/cmd_session.py`

### Procedure

In the `rename` branch, capture `set_title`'s return and map falsy to the validation
error line.

### Method

Edit only the statements after the `from agent.commands.session_title import
SESSION_TITLE_MAX_CHARS` import inside the `if sub == "rename":` branch.

### Details

```python
persisted = self._ctx.session.set_title(title)
if not persisted:
    self._out.write_validation_error("/session rename <title>")
    return
self._out.write_success(
    f"Session renamed: {title[:SESSION_TITLE_MAX_CHARS]!r}"
)
return
```

## Compatibility considerations

- Existing test `test_rename_updates_title` (`tests/agent/commands/test_agent_cmd_session.py`
  L249-253) stays green before any test edit: the mocked `set_title` returns a truthy
  `MagicMock`, so the success line still prints.
- `mypy`: requires the document _01 annotation change to type `persisted` as `bool`;
  running this change alone against the old `None` signature is a behavior error, not a
  type error — hence the stated implementation order.

## Security considerations

- No new I/O or SQL; output goes through the existing output port (`write_validation_error` in `scripts/agent/commands/output_port.py`).

## Rollback considerations

- Single-branch revert; independent of the `load`/`delete` branches. Revert after (or
  together with) document _01 if both are backed out, to avoid the `not None` false-
  failure described in Assumptions.

## Validation plan

| Check | Command | Expected |
|-------|---------|----------|
| targeted tests | `uv run pytest tests/agent/commands/test_agent_cmd_session.py -k rename` | green (with document _03 cases) |
| lint/type | `uv run ruff check . && uv run mypy scripts/` | clean |
| full suite | `uv run pytest` | green |

## Completion criteria

- `/session rename <title>` with a persisted title prints exactly
  `Session renamed: {title[:32]!r}` (Plan AC REQ-4).
- `/session rename <title>` when `set_title` returns `False` prints the `[usage]`
  validation line and no "renamed" text (Plan AC REQ-2).
- Empty-title behavior unchanged.

## Out of Scope

- Auto-creating a session on rename (Plan OUT-1).
- Title parsing/truncation changes (Plan OUT-2).
- Catching `sqlite3.Error` in the branch (unchanged propagation per REQ-1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-075014 | 20261028-080550 | After document _01 rename branch captures persisted; per Details snippet |
| 2 | Add or update tests per Validation plan | Completed | — | 20261028-080550 | Test authoring is owned by document _03 Regression-only; new cases owned by document _03 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261028-080550 | Shared _02/_03 validation pass: full suite 10255 passed, diff-cover 100% (7 changed lines); no new mypy/ruff findings |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261028-080550 | N/A: Plan has no docs row N/A: Plan has no docs row |

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
- **Requirement ID**: REQ-2, REQ-4
- **Source issue**: `issues/20261026-225105_sess007_validate-session-rename-result.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-085735_sess007_validate-session-rename-result.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-001446
- **Related target files**: `scripts/agent/commands/cmd_session.py`
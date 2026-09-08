## Goal

Remove the redundant `if self._cmds is None:` guard clause from the `_dispatch_line` method of `ReplInputLoop`, restoring the single-authoritative-check design that was intended but never applied.

## Scope

Modify exactly one file: `scripts/agent/repl_input_loop.py`. Remove the `_cmds is None` check from `_dispatch_line` method.

## Assumptions

- `_dispatch_line` is only ever called from within `_repl_loop`'s loop, which already checks the `_cmds is None` precondition first. This is confirmed by repository evidence: `rg` search found `_dispatch_line` called only at line 224 inside `_repl_loop`.
- The class docstring's "single authoritative precondition" claim is correct and should be preserved rather than softened.

## Design decisions

- Remove the `_cmds is None` check from `_dispatch_line` because `_dispatch_line` is only ever called from within `_repl_loop`'s loop, which already checks this precondition first.
- Keep the existing docstring's claim accurate by making the code match it, not by softening the docstring's wording.
- Preserve `_repl_loop`'s existing check and its `RuntimeError` message text unchanged.

## Alternatives considered

- Softening the class docstring's "single authoritative precondition" claim: rejected because the original design decision (REQ-RIL002-1) was clear that `_repl_loop` should be the single authoritative precondition; the code should match the docstring, not vice versa.
- Adding a new assertion or warning in `_dispatch_line`: rejected because this would add complexity without addressing the root issue of having two independent checks.

## Implementation
### Target file
`scripts/agent/repl_input_loop.py`

### Procedure
Remove the `if self._cmds is None:` guard clause from `_dispatch_line` method.

### Method
1. Open `scripts/agent/repl_input_loop.py`.
2. Locate the `_dispatch_line` method (starting at line 178).
3. Remove the following block (lines 183-185):
```python
        if self._cmds is None:
            self._view.write_fatal("Command registry not initialized")
            return
```
4. Verify that `_repl_loop`'s existing check (line 202) remains intact.

### Details
1. Read the current file to confirm line numbers (may have shifted from the archived procedure's cited 170-171 due to intervening docstring insertion).
2. Confirm `_dispatch_line` is only called from `_repl_loop` at line 224.
3. After removing the block, verify that `_repl_loop`'s check at line 202 is still present and unchanged.
4. Run the test suite: `uv run pytest tests/agent/test_repl.py -v`.
5. Run static verification: `rg -n "_cmds is None" scripts/agent/repl_input_loop.py` should show exactly one match at `_repl_loop`.

## Compatibility considerations

- This removes a runtime check; callers that bypass `_repl_loop`'s precondition will no longer receive a `RuntimeError` from `_dispatch_line` directly. However, since `_dispatch_line` is only ever called from within `_repl_loop`'s loop (confirmed by `rg`), this change has no practical compatibility impact.

## Security considerations

This change does not introduce security risks. The removal of the `_cmds is None` check in `_dispatch_line` is safe because `_repl_loop` already enforces this precondition before calling `_dispatch_line`.

## Rollback considerations

Reverting this change means re-adding the removed block. No operational impact since this is a simple removal of a guard clause.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/repl_input_loop.py` | Unit: verify `_dispatch_line` behavior unchanged when `_cmds` is initialized | `uv run pytest tests/agent/test_repl.py -v` | All existing tests pass |
| `scripts/agent/repl_input_loop.py` | Static: verify no duplicate `_cmds is None` check remains | `rg -n "_cmds is None" scripts/agent/repl_input_loop.py` | Exactly one match at `_repl_loop` |
| `scripts/agent/repl_input_loop.py` | Static: verify `_dispatch_line` has no non-`_repl_loop` callers | `rg -n "_dispatch_line" scripts/ tests/` | Only `_repl_loop` calls `_dispatch_line` |
| `scripts/agent/repl_input_loop.py` | Lint/format: verify code style compliance | `uv run ruff format scripts/ && uv run ruff check scripts/ --fix && uv run ruff check scripts/` | Clean (no errors) |
| `scripts/agent/repl_input_loop.py` | Type checking: verify mypy passes | `uv run mypy scripts/` | No new regressions vs pre-existing errors |
| `scripts/agent/repl_input_loop.py` | Security: verify bandit passes | `uv run bandit -r scripts/ -c pyproject.toml` | No high/medium unaddressed findings |
| `scripts/agent/repl_input_loop.py` | Architecture: verify import integrity | `PYTHONPATH=scripts uv run lint-imports` | No boundary violations |

## Completion criteria

- [ ] `_dispatch_line` no longer contains an independent `_cmds is None` check
- [ ] Exactly one `_cmds is None` check remains in the file (`_repl_loop`)
- [ ] The class docstring's "single authoritative precondition" claim is accurate against the resulting code
- [ ] No regression in existing REPL command-dispatch tests

## Out of scope

- Modifying any other file.
- Changing `_repl_loop`'s existing `_cmds` check or its `RuntimeError` message text.
- Adding new tests for `_dispatch_line` being called before `_cmds` initialization (the plan assumes none currently exists).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260907-131805_ril002b_dispatch_line_cmds_check_not_removed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-215927_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-08T00:03:23Z
- **Related target files**: scripts/agent/repl_input_loop.py

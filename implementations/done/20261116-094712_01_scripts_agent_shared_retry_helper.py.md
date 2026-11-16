## Goal

Give `retry_once_with_delay` a keyword-only `skip_first_attempt` (new) option so a caller that has already made, and lost, the first attempt can run only the delayed second attempt (`REQ-003`: caller-made first attempt supported, default behavior unchanged; `REQ-004`: tests for the option).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `scripts/agent/shared/retry_helper.py` (`retry_once_with_delay` and its docstring) and its companion test file `tests/agent/test_retry_helper.py`.
- Out of scope: the two call sites in `scripts/agent/startup_mcp_starter.py` (document `02`), the delay value, and the helper's exception rebuilding.

## Assumptions

- The only production callers of `retry_once_with_delay` are the two sites in `scripts/agent/startup_mcp_starter.py` (re-checked with `rg`: all other hits are tests, the ADR text, the MCP startup doc and `tools/compat_exceptions.toml`).
- `tools/compat_exceptions.toml` lists the name `retry_once_with_delay` as an exempt symbol name; a new keyword-only parameter does not change that entry, so the file is not a target.
- Plan overlap judgment (Step 2 `tools/check_plan_target_overlaps.py`): no Frozen Plan other than this one targets `scripts/agent/shared/retry_helper.py` or `tests/agent/test_retry_helper.py`.
- Test file `tests/agent/test_retry_helper.py` is a companion: it is a Plan row under `tests/`, only the `retry_helper.py` row names it in `Related Tests` (besides itself), and the test cases are fully specified by the Plan.

## Design decisions

- Add `skip_first_attempt: bool = False` after the existing `*` marker. With the default, the first `await fn()` and everything after it stay byte-for-byte as before (`REQ-003`).
- With the option set, skip only the leading `try: return await fn() except Exception: pass` block. Keep the shutdown pre-check, the interruptible delay, the second `await fn()` and the masked fatal rebuild untouched.

## Alternatives considered

- A second helper that only retries: rejected, because the ADR and the MCP startup doc cite `retry_once_with_delay()` by name and the tests patch `agent.startup_mcp_starter.retry_once_with_delay`.
- Removing the inline first attempt at the call sites: rejected in the Plan (exception filter and tolerated `None` result would be lost).

## Implementation
### Target file
`scripts/agent/shared/retry_helper.py`

### Procedure
1. Add the keyword-only parameter `skip_first_attempt: bool = False` to `retry_once_with_delay`.
2. Guard the leading first-attempt `try` block with `if not skip_first_attempt:` so it is not executed when the option is set.
3. Update the docstring: describe the option, state that with it the helper makes exactly one attempt after the delay, and that `StartupInterrupted` is raised without calling `fn` when shutdown is already set or fires during the delay.

### Method
- Keep the `Logger` construction and every import where they are; no new import is added.
- The guarded block keeps its existing `# noqa: BLE001 — ...` justification comment.
- The shutdown check, `_interruptible_sleep` and the second-attempt `try/except` run in both modes, so the fatal-prefixed, secret-masked rebuilt exception is identical.

### Details
- Complexity: `retry_once_with_delay` is radon B (6) today; one added branch must keep it at B or better.
- Do not change `_rebuild_after_retry`, `_interruptible_sleep` or `_mask_secrets`.

### Companion test files
- `tests/agent/test_retry_helper.py`
  - Procedure: write these tests first and confirm the option tests fail before the change: (a) `skip_first_attempt=True` (new) calls `fn` exactly once, after the delay; (b) its failure raises the original exception type with the `fatal_prefix` and a masked message, with `__cause__` set; (c) a pre-set shutdown event raises `StartupInterrupted` with `fn` never called; (d) a shutdown event set during the delay raises `StartupInterrupted` with `fn` never called; (e) the default mode still calls `fn` first (call count 2 on persistent failure, 1 on first-attempt success). Use the file's existing `call_count` closure style, `delay=0.01`, and a lower-bound-only timing assertion.
  - Validation: `uv run pytest tests/agent/test_retry_helper.py -q`.

## Compatibility considerations

- Default call signature and behavior are unchanged; existing positional and keyword callers and the exception-type-preservation tests keep passing.
- The only production behavior change is at the two call sites (document `02`), which stop making an immediate second attempt.

## Security considerations

- The masked fatal message path (`_mask_secrets` applied to the retry error text) is unchanged and is asserted for the new mode by test (b); no secret can reach the log or the raised message through the new mode.

## Rollback considerations

- Revert the commit; the call sites in document `02` must be reverted with it, because they pass the new option.

## Validation plan

- `uv run pytest tests/agent/test_retry_helper.py -q` passes, and the option tests fail on the pre-change code.
- `uv run ruff format` and `uv run ruff check` on the changed files; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check`.

## Completion criteria

- `retry_once_with_delay(..., skip_first_attempt=True)` calls `fn` exactly once after the delay, raises the masked fatal-prefixed exception on failure, and raises `StartupInterrupted` without calling `fn` when shutdown is set before or during the delay (`REQ-003`, AC-3).
- The default mode behaves exactly as before and a regression test proves it (`REQ-003`).
- The new tests are present and fail against the pre-change code (`REQ-004`, AC-4).

## Out of Scope

- Call-site changes, delay value changes, documentation edits, removal of the default mode (`UNK-01` of the Plan keeps it).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the helper tests first and confirm the option tests fail on the current code (companion `tests/agent/test_retry_helper.py`) | Completed | 20261116-131551 | 20261116-131551 | STEP:1: skip_first_attempt added to retry_once_with_delay plus docstring update; guarded leading attempt; files scripts/agent/shared/retry_helper.py and tests/agent/test_retry_helper.py |
| 2 | Add `skip_first_attempt` (new) to `retry_once_with_delay` and update its docstring | Completed | 20261116-131551 | 20261116-131551 | STEP:2: five option tests added (call once after delay, masked fatal preserve, shutdown before/during delay, default regression); failed on pre-change code, pass after change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-131551 | 20261116-131730 | STEP:3: ruff clean; mypy 444 files ok; lint-imports 6 kept 0 broken; bandit no high/medium; ast-grep no bare except; check_module_size OK; generate_reference_table no drift; helper test 10 passed; full suite 12325 passed 7 skipped; diff-cover 100% |

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
- **Requirement ID**: `REQ-003` (helper option), `REQ-004` (tests for the option)
- **Source issue**: issues/20261115-214902_startrev002_mcp-start-retry-attempts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-215900_startrev002_mcp-start-retry-attempts.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-094712
- **Related target files**: `scripts/agent/shared/retry_helper.py`, `tests/agent/test_retry_helper.py`
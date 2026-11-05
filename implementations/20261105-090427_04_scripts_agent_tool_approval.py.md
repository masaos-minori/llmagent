# Implementation Procedure: scripts/agent/tool_approval.py — share the module reader

## Goal

Route approval answers through the process-shared `StdinReader` (declared by sibling seq 01) so
the approval prompt participates in the same hand-off path as the REPL and multiline prompts
(REQ-002: one shared reader instance).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the module-level lazy reader global and its initialization inside the approval read
  helper, plus the import from `agent.stdin_reader`.
- Out of scope: the accessor itself (seq 01), the other consumers (seq 02, seq 03), the approval
  decision logic and prompt strings.

## Assumptions

- The approval helper already passes its prompt per call (`_approval_read` forwards
  `read(prompt=prompt)` with `  Execute? [yes/no]: ` / `  Execute? [y/N]: ` strings) — confirmed
  — so no prompt move is needed here.
- Existing approval tests replace the read helper at function level with an async mock (confirmed
  across `tests/agent/test_tool_approval_preflight.py` and `tests/agent/test_tool_approval_paths.py`
  patch targets), so rewiring the helper body does not require test edits.

## Design decisions

- Delete the module lazy global rather than redirect it to the accessor (chosen): keeping a second
  module-level reader variable would preserve the duplicate-instance bug shape and add a name with
  no owner; the accessor already provides lazy creation with a reset hook for tests.

## Alternatives considered

- Assigning the shared accessor result into the existing global once — rejected: a stale module
  global would outlive `reset_stdin_reader()` in test fixtures and shadow the accessor contract.

## Implementation
### Target file
`scripts/agent/tool_approval.py`

### Procedure
Remove the module-level reader global and its lazy initialization; call the shared accessor
directly in the read helper:

```python
# After:
async def _approval_read(prompt: str) -> str:
    """Read one approval answer on the shared daemon reader thread."""
    return await get_stdin_reader().read(prompt=prompt)
```

- Delete the module-level `_approval_reader` global declaration and the `global` statement plus
  lazy-construction branch inside the helper.
- Import: `from agent.stdin_reader import get_stdin_reader` (new) replaces the previous import
  name from the same module.

### Method
`_approval_read` keeps its signature (`prompt: str`) and return behavior unchanged; only the body
loses the lazy global. No other function changes.

### Details
- Prompt strings (`  Execute? [yes/no]: `, `  Execute? [y/N]: `) stay at their call sites in
  `_prompt_user_approval` (REQ-003: unchanged).
- The helper docstring's wording about "the module's daemon reader thread" becomes the shared
  thread, matching the new body.
- Follow `rules/coding.md`; no new annotations needed.

### Companion test files
N/A: no companion test files for this target (the Plan names none; existing approval suites mock
the helper at function level and verify unchanged behavior in the Validation plan).

### Implementation Checklist
| # | Target File(s) | Action Summary | Acceptance Criteria | Status |
|---|----------------|----------------|---------------------|--------|
| 1 | scripts/agent/tool_approval.py | Drop the lazy reader global; helper calls the shared accessor; import updated. | Approval reads use the shared instance; prompts unchanged. | Pending |

## Compatibility considerations

- Approval answer semantics (HIGH requires `yes`, otherwise `y`) are unchanged (REQ-003).
- Tests patching the helper (function-level `AsyncMock`) keep working because the helper name and
  signature survive the rewiring.
- Removing the global removes the module's private second reader instance, which is the point of
  the change.

## Security considerations

N/A: no new trust boundary; approval gating logic untouched.

## Rollback considerations

Revert the commit; the module restores its private lazy reader, regaining isolation but losing the
shared hand-off.

## Validation plan

- `uv run pytest tests/agent/test_tool_approval_preflight.py tests/agent/test_tool_approval_paths.py
  tests/agent/test_tool_approval_risk.py tests/agent/test_tool_approval_concurrency.py -v` —
  approval suites pass unchanged.
- Static gates per `rules/toolchain.md`: `uv run ruff format scripts/`, `uv run ruff check
  scripts/ tests/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`,
  `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria

- No `StdinReader` instance is constructed anywhere in the module after the change.
- All approval test suites pass without modification.

## Out of Scope

- The accessor implementation (seq 01), the `CLIView` and REPL consumers (seq 02, seq 03).
- Approval risk gating, preflight checks, preview rendering, and prompt strings.
- Approval test edits (existing suites verify unchanged behavior).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Drop the lazy global and rewire the helper per Implementation > Procedure | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docs carried by sibling procedure seq 07 |

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
- **Requirement ID**: REQ-002 (shared reader wiring), REQ-003 (unchanged approval prompts)
- **Source issue**: issues/20261104-112115_cliview002_stdin-line-lost-after-multiline-timeout.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-223334_cliview002_stdin-line-lost-after-multiline-timeout.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-090427
- **Related target files**: `scripts/agent/tool_approval.py`

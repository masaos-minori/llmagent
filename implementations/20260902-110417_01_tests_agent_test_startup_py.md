## Goal
Fix `REQ-001`/`REQ-002` (six `tests/agent/test_startup.py` fixtures currently failing with
`TypeError: object MagicMock can't be used in 'await' expression`) by giving each fixture's
`ctx.conv` a genuinely awaitable `replace_history()`.

## Scope
Modify exactly `tests/agent/test_startup.py`: insert `ctx.conv = ConversationState()`
immediately after `ctx = MagicMock()` in six test bodies. No other file changes.

## Assumptions
- Each of the six tests builds `ctx = MagicMock()` inline with no shared fixture function
  (re-confirmed by reading the current file — see Implementation below); the edit is scoped
  to exactly those six test bodies and does not ripple into other tests.
- No test among the six asserts on `replace_history` as a mock call (e.g.
  `assert_called_once_with`) — all assertions check resulting state
  (`ctx.conv.history`, `ctx.conv.system_prompt_content`, `ctx.conv.memory_disabled`), which a
  real `ConversationState` instance satisfies.

## Design decisions
Reuse the real `ConversationState()` dataclass (already imported at module level,
`from agent.context import ConversationState`, confirmed at line 18) rather than a partial
async mock (e.g. `AsyncMock(spec=ConversationState)` or patching only `replace_history`).
Per `skills/python-design/SKILL.md` Core Design Rules ("keep proposed design separate from
implemented behavior"; "validate only at system boundaries"): this is the existing,
already-precedented in-file pattern (`test_no_pinned_notes_block_injected`,
`test_history_set_to_system_message`, confirmed at lines 530 and 582), so no new
test-double strategy is introduced.

## Alternatives considered
- `AsyncMock(spec=ConversationState)` patching only `replace_history`: rejected — would
  require a new import and a second mock-construction pattern in the same file for no
  behavioral benefit, since the six tests' assertions check real dataclass state, not mock
  call arguments.
- A shared `pytest` fixture constructing `ctx.conv` once for all six tests: rejected — each
  test currently builds `ctx = MagicMock()` inline with no shared fixture; introducing one
  now would be an unrelated structural change beyond this row's scope.

## Implementation
### Target file
`tests/agent/test_startup.py`

### Procedure
For each of the six failing tests, insert `ctx.conv = ConversationState()` immediately after
`ctx = MagicMock()`, before any subsequent `ctx.conv.<attr> = ...` assignment line.

### Method
1. In `TestStartupOrchestratorSetupPrompt` (class starts line 526): edit
   `test_memory_snippets_are_injected_when_enabled` (line 546),
   `test_no_memory_injection_when_disabled` (line 567), and
   `test_memory_snippets_truncated_when_exceeds_limit` (line 598) — insert
   `ctx.conv = ConversationState()` right after `ctx = MagicMock()`, before the existing
   `ctx.conv.system_prompt_name = "default"` line (REQ-001).
2. In `TestStartupMemoryFailures::test_memory_injection_categorized_logging` (class starts
   line 1504, method at line 1516; parametrized ×3) — insert
   `ctx.conv = ConversationState()` right after `ctx = MagicMock()`, before the existing
   `ctx.conv.system_prompt_name = "default"` line, keeping the subsequent
   `ctx.conv.memory_disabled = False` assignment (now a real dataclass field write)
   (REQ-002).

### Details
Re-confirmed against current source (adversarial verification, this cycle):
- `uv run pytest tests/agent/test_startup.py -k "TestStartupMemoryFailures or TestStartupOrchestratorSetupPrompt" -q` reproduces exactly the Plan's claimed failures: `6 failed, 3 passed, 63 deselected`, with the identical `TypeError: object MagicMock can't be used in 'await' expression` traceback through `scripts/agent/startup.py`'s `await ctx.conv.replace_history(...)`.
- `scripts/agent/context.py::ConversationState` (class at line 85) is a dataclass with
  `history: list[LLMMessage]` (line 94), `system_prompt_content: str` (line 101),
  `memory_disabled: bool = False` (line 104), and `async def replace_history(...)` (line
  168) — all fields the six tests' assertions depend on are present as described in the
  Plan.
- Class/method line numbers for all six target tests and the two sibling
  already-passing tests were re-confirmed via `grep -n` against the current file and match
  the Plan's Background/Implementation intent (`test_no_pinned_notes_block_injected` at 530,
  `test_history_set_to_system_message` at 582).
- No discrepancy found; the Plan's claims hold against current source. No Plan correction
  was needed.

## Compatibility considerations
N/A: test-only change to `tests/agent/test_startup.py`; no public interface, schema, or
runtime behavior changes. `scripts/agent/startup.py::_setup_prompt()` and
`scripts/agent/context.py::ConversationState` are read-only references, not modified.

## Security considerations
N/A: no security-relevant code path is touched; this is a unit-test fixture correction.

## Rollback considerations
Trivially revertable: `git checkout -- tests/agent/test_startup.py` restores the six
original (failing) fixture bodies. No migration, no persisted state, no other file depends
on this change.

## Validation plan
- `uv run pytest tests/agent/test_startup.py -k "TestStartupMemoryFailures or TestStartupOrchestratorSetupPrompt" -q` — expect all 9 selected tests passing (0 failed), up from `6 failed, 3 passed`.
- `uv run pytest tests/agent/test_startup.py -q` — expect `72 passed`, 0 failed (pre-fix baseline: `6 failed, 66 passed`).
- `uv run ruff format tests/agent/test_startup.py && uv run ruff check tests/agent/test_startup.py` — no formatting diff beyond the fixture edit; no lint errors.
- `uv run mypy tests/agent/test_startup.py` — no new type errors vs. pre-existing baseline.

## Completion criteria
(Corrected 2026-09-02, Step 4: `TestStartupWorkflowPreflight::test_aborts_on_missing_workflow_schema`
fails identically with this row's changes reverted — a pre-existing, unrelated failure, not
introduced by this row. "All 72 tests pass" below should be read as "all 6 tests this row
targets pass, with no new regression" — 71 passed / 1 failed (pre-existing) is the actual,
correct outcome.)

All 72 tests in `tests/agent/test_startup.py` pass; the six previously-failing tests
(`test_memory_snippets_are_injected_when_enabled`, `test_no_memory_injection_when_disabled`,
`test_memory_snippets_truncated_when_exceeds_limit`, and the three
`test_memory_injection_categorized_logging` parametrizations) now pass via a real
`ConversationState()` instance; no previously-passing test in the file regresses; `ruff`/
`mypy` report no new issues.

## Out of scope
`scripts/agent/startup.py::_setup_prompt()` (read-only reference; its `await
ctx.conv.replace_history(...)` is correct as-is). Any other test in
`tests/agent/test_startup.py` not named above. `ctx.conv`'s production implementation
(`scripts/agent/context.py::ConversationState`) — read-only reference, not modified.
`TestStartupWorkflowPreflight::test_aborts_on_missing_workflow_schema` — confirmed
pre-existing, unrelated failure (see Execution Status Step 3), not fixed by this row.

## Documentation
`tests/agent/test_startup.py` has no matching row in `docs/00_index.md`'s "Document
References by Task" table — no `docs/*.md` update applies (Step 5: `N/A: no docs/00_index.md
task-scope mapping for tests/agent/test_startup.py`). Step 6 content checks skipped
accordingly.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert `ctx.conv = ConversationState()` in the six affected test bodies | Completed | 2026-09-02 | 2026-09-02 | |
| 2 | Run targeted test selection (9 tests) | Completed | 2026-09-02 | 2026-09-02 | All 9 pass |
| 3 | Run full-file regression (`uv run pytest tests/agent/test_startup.py -q`) | Completed | 2026-09-02 | 2026-09-02 | 71 passed, 1 failed — `TestStartupWorkflowPreflight::test_aborts_on_missing_workflow_schema` fails identically with this Plan's changes reverted (`git stash`), with and without `pytest-randomly` — confirmed pre-existing, unrelated to this row's scope; not fixed here |
| 4 | Run `ruff format`/`ruff check`/`mypy` | Completed | 2026-09-02 | 2026-09-02 | `ruff` clean; `mypy` shows 42 pre-existing errors, identical count before/after this change (confirmed via `git stash`) — none introduced by this row |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (`tests/agent/test_startup.py` fixture fix; no other test regresses)
- **Source issue**: `issues/20260831-191101_startup01_setup_prompt_async_mock_test_failures.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-101413_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-110417
- **Related target files**: `tests/agent/test_startup.py`

# Procedure: extend TestSingleLlmTurnExecutorOwnership with factory-count guard

**Doc ID:** 20261030-122302_05
**Target File:** `tests/agent/test_orchestrator.py`
**Change Type:** test | **Priority:** P1 | **Plan Phase:** 3

## Goal
REQ-004/AC-3: make the existing guard fail on a second construction or a retained-unused
`LlmTurnExecutor` instance, counting constructions via a patched factory so future renames
cannot blind it (issue testing expectation).

## Scope
- Extend `TestSingleLlmTurnExecutorOwnership` (`tests/agent/test_orchestrator.py:2933`)
  with one new method `test_orchestrator_constructs_llm_executor_exactly_once` (new).
- Existing method `test_orchestrator_creates_single_shared_llm_turn_executor` stays
  unchanged (regression row in the plan Tests section).
- ADR-014 verification-row text coordination: row 01 Step 2.

## Assumptions
- The Orchestrator constructs `LlmTurnExecutor` through the name imported into its own
  module namespace (`scripts/agent/orchestrator.py:36` `from agent.llm_turn_executor
  import LlmTurnExecutor`), so `monkeypatch.setattr("agent.orchestrator.LlmTurnExecutor",
  counting_factory)` intercepts every production construction.
- `_make_orchestrator(ctx)` (module helper already used by the existing guard test)
  exercises the real construction path.
- Headline fact verified at HEAD: exactly one construction site
  (`orchestrator.py:120`); adapter only stores the injected instance
  (`workflow_engine_adapter.py:98`).

## Design decisions
- Factory-count shape: wrap the class in a counting factory (records each constructed
  instance in a list), patch `agent.orchestrator.LlmTurnExecutor`, build the orchestrator
  via `_make_orchestrator`, then assert: (a) `len(constructions) == 1`; (b) the recorded
  instance `is orch._llm_executor`; (c) `orch._workflow_adapter._llm_executor is` that
  same instance — so a second construction, used or unused, fails the test.
- Patch the class (Risk mitigation "Count via patched class, not call-site strings"): a
  rename of `LlmTurnExecutor` still breaks the import line loudly; the assertion logic
  never greps source text.
- Fail-before proof (AC-3): temporarily add a second unused construction inside
  `Orchestrator.__init__` (e.g. `_ = LlmTurnExecutor(...)`), show the new test fails,
  then `git checkout scripts/agent/orchestrator.py` (single-path revert, allowed by the
  Execution policy). Record the failing assertion output as fail-before evidence.

## Alternatives considered
- `rg`-based source scanning for construction sites in the test: rejected — brittle to
  renames/formatting and already covered by the mcpgate001-style static checkers, not a
  unit guard.
- Counting constructions across a full turn run: rejected — runner-side per-turn objects
  are out of INV-02 scope; construction happens once at Orchestrator init.

## Implementation
1. Add the new method inside the existing class with a one-line docstring citing INV-02.
2. Implement the counting factory as a local helper inside the test (no shared fixture
   changes); restore via `monkeypatch` teardown (implicit).
3. Run the fail-before proof above; capture output; revert the fixture.
4. Coordinate with row 01: ADR-014 verification-row text lands in the same commit group.

## Compatibility considerations
- `_make_orchestrator` must keep working with the patched class: the factory must return
  a real `LlmTurnExecutor` instance (subclass or pass-through wrapper), never a stub, or
  downstream adapter type expectations break.

## Security considerations
None.

## Rollback considerations
Remove the new method; revert the temporary fixture per Step 3.

## Validation plan
- `uv run pytest tests/agent/test_orchestrator.py tests/agent/test_llm_turn_runner.py`
  (issue-specified).
- `uv run ruff check tests`.
- Fail-before evidence retained in the implementation record (AC-3).

## Completion criteria
New method green on current HEAD; fails on the fabricated second-executor fixture;
existing guard test unchanged and green.

## Out of Scope
Runner-side assertions (row 06); `scripts/` production changes (the fixture is reverted).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_orchestrator_constructs_llm_executor_exactly_once` (new) per Procedure | Pending | — | — | |
| 2 | Fail-before proof + revert | Pending | — | — | AC-3 evidence |
| 3 | pytest + ruff gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Row 01 verification-row text must land in the same commit group | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

#### Marker edit record
- `test_orchestrator_constructs_llm_executor_exactly_once` (new) は生成時にインラインで
  マーカー付与（事後編集なし）。新規コンストラクトはこの 1 件。

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004; AC-3
- **Source issue**: `issues/20261029-104510_turnadr001_align-adr014-loop-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_turnadr001_align-adr014-loop-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-122302
- **Related target files**: `tests/agent/test_orchestrator.py`

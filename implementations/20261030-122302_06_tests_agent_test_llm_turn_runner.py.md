# Procedure: test_llm_turn_runner.py per-turn lifecycle check (conditional)

**Doc ID:** 20261030-122302_06
**Target File:** `tests/agent/test_llm_turn_runner.py`
**Change Type:** test | **Priority:** P2 | **Plan Phase:** 3

## Goal
Target-row condition "per-turn lifecycle assertion only if the trace requires it":
verify the runner-side lifecycle fact and add the smallest characterization guard only
when a gap is found.

## Scope
- Trace re-verification (read-only): `llm_turn_executor.py:84` creates a local
  `LLMTurnRunner` per `execute_turn()`; no `self._runner` attribute exists (verified at
  procedure-generation time by grep); the runner is not stored on the executor.
- Conditional addition: one test method
  `test_executor_does_not_retain_llm_turn_runner` (new) in this file only if the trace
  shows a retention or authority gap.

## Assumptions
- Current trace shows no gap (runner is local; guard is created by the executor at
  `llm_turn_executor.py:83` and passed in), so the default outcome is a recorded
  no-change verification, not a new test.
- Row 05's factory-count guard already covers executor-side single-instance ownership;
  adding a runner-side test without a gap would duplicate guard value.

## Design decisions
- Decision gate at implementation time: run `grep -n "self._runner"
  scripts/agent/llm_turn_executor.py` (must be empty) and inspect `execute_turn` for any
  new retention. If both hold: record "no change required — trace verified" in Execution
  Status with the grep output. If a gap exists: add
  `test_executor_does_not_retain_llm_turn_runner` (new) constructing a real
  `LlmTurnExecutor` (existing fixtures in `tests/agent/` for executor construction),
  running one turn, and asserting the executor holds no runner attribute afterwards.
- No test asserting the runner "holds no authority" beyond retention: authority is an
  INV-01 manual-review concern (plan: verification-only).

## Alternatives considered
- Adding a lifecycle test unconditionally: rejected — the frozen row itself is
  conditional; an unconditional test mutates against a behavior that does not exist.

## Implementation
1. Run the grep/inspect gate; capture output.
2. Branch: no-change record, or add the conditional method per Design decisions.

## Compatibility considerations
None if no change; a new method must not re-import private helpers (existing fixtures).

## Security considerations
None.

## Rollback considerations
Remove the added method (only exists in the gap branch).

## Validation plan
- `uv run pytest tests/agent/test_llm_turn_runner.py` (issue-specified; also run with
  row 05 per the combined command).

## Completion criteria
Execution Status records the trace verdict with evidence; if the gap branch fired, the
new method fails before the fix-equivalent scenario and passes on HEAD.

## Out of Scope
Executor-side counting (row 05); ADR wording (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Trace gate (grep + inspect) | Pending | — | — | Default: no change |
| 2 | Gap branch: add `test_executor_does_not_retain_llm_turn_runner` (new) | Pending | — | — | Only if gate fails |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

#### Marker edit record
- `test_executor_does_not_retain_llm_turn_runner` (new) は gap 分岐発動時のみ作成。
  発動したら本 doc のマーカーが有効マーカーとして記録される。

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 (supporting), REQ-005 (verification-only)
- **Source issue**: `issues/20261029-104510_turnadr001_align-adr014-loop-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_turnadr001_align-adr014-loop-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-122302
- **Related target files**: `tests/agent/test_llm_turn_runner.py`

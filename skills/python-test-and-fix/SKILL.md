---
name: python-test-and-fix
description: |
  Use this skill PROACTIVELY when adding, fixing, or investigating Python tests.
  Covers: flaky detection, mutation testing, deterministic runtime, boundary virtualization,
  contract validation, observability validation, resource leak detection,
  impact-based test execution, regression quality analysis, and repository test policy compression.
  Use when reproducing bugs, repairing failing tests, adding regression coverage,
  or validating implementation fixes.
---

# Python Test And Fix Skill

## Purpose

Add, repair, and improve Python tests; reproduce the problem clearly; fix the smallest correct implementation surface without altering core behavior unless specified.

## Core Testing Rules (Strictly Enforced for AI)

- **Do Not Fix Tests by Blindly Changing Expectations**: If a test fails, MUST NOT modify the assertions to match the current broken output. You MUST verify whether the implementation or the test violates the system contract.
- **Strictly Forbid Flaky Fix Anti-Patterns**: Never use arbitrary `time.sleep()` to fix timing or race conditions in async or multi-threaded tests. Use synchronization primitives, event-loop waits, or `pytest-asyncio` lifecycles.
- **Ensure Mock Cleanliness**: Always patch/mock dependencies using context managers or pytest fixtures that guarantee automatic cleanup. MUST NOT leave leakage or side-effects that affect later tests.
- **Wiring-Guard and Mock-State Prohibition**: A component constructed in `__init__` and shared with other objects (e.g. `AgentREPL`'s shutdown event, held by `ReplInputLoop` and `SignalHandler`) MUST have a wiring-level guard test that runs the real constructor and asserts the production handoff; and a test MUST NOT assert on state the test itself assigned to a `MagicMock` — asserting self-assigned mock state hides the very defect (wrong or missing wiring) this rule exists to catch.
- **No Tool Hallucination**: applies to `mutmut`, `freezegun`, `respx`, `hypothesis`, `pytest-testmon` — see `skills/DESIGN.md` Tool availability guard (fallback: standard `pytest`/`unittest.mock`).

## Task Routing (Step 1 Classification & Phase Guide)

Classify the task in **Step 1** and strictly follow the assigned path. MUST NOT skip mandatory steps.

### [Path A] Bug Fix Verification
- **Criteria**: Reproducing and fixing an implementation bug.
- **Path**: 1 -> 2 -> 3 -> 5 -> 6 -> 9 -> 10 -> 11 -> 12 -> 13
- *Skip*: 4 (mutmut), 7 (hypothesis), 8 (observability)

### [Path B] New Feature Test
- **Criteria**: Adding test coverage for a newly implemented feature.
- **Path**: 1 -> 2 -> 4 -> 5 -> 6 -> 7 -> 9 -> 10 -> 11 -> 12 -> 13
- *Skip*: 3 (flaky detection), 8 (observability)

### [Path C] Fix Broken Test
- **Criteria**: Repairing a test that is broken due to recent code changes or regressions.
- **Path**: 1 -> 2 -> 3 -> 5 -> 6 -> 7 -> 9 -> 10 -> 11 -> 12 -> 13
- *Skip*: 4 (mutmut), 8 (observability)

### [Path D] Flaky Test Investigation
- **Criteria**: Debugging non-deterministic or intermittent test failures.
- **Path**: 1 -> 2 -> 3 (Mandatory multiple runs) -> 5 -> 6 -> 9 -> 10 -> 11 -> 12 -> 13
- *Skip*: 4 (mutmut), 7 (hypothesis), 8 (observability)

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 1 | Classify the testing task | Classify task into Bug / New Test / Fix Broken / Regression / Flaky. Select Path A, B, C, or D. |
| 2 | Inspect before changing | Scan usages via `rg`, analyze `conftest.py`, and inspect existing fixtures to match repository testing patterns. |
| 3 | Flaky detection | Use `pytest-randomly` for seed randomization and run with `--reruns` or loops to confirm failure determinism. |
| 4 | Mutation testing | Run `mutmut` on the modified paths to validate that tests actually catch logical mutations. |
| 5 | Deterministic runtime | Enforce time determinism using `freezegun` for time-dependent assertions and use fixed random seeds. |
| 6 | Boundary virtualization | Use `pytest-subprocess`, `respx`, or `mocker`. Isolate the test environment and mock *only* at true external boundaries. |
| 7 | Contract validation | Use `hypothesis` for invariant-based property testing (restrict to pure functions like parsers or serializers). |
| 8 | Observability validation | Capture logging output using pytest's `caplog` fixture. Skip OTel unless project-wide patterns exist. |
| 9 | Resource leak detection | Audit `pytest-asyncio` lifecycles and use `pytest-timeout` to catch unclosed resources or hanging loops. |
| 10 | Impact-based execution | Leverage `pytest-testmon` if available for rapid, incremental test execution during local feedback loops. |
| 11 | Regression quality analysis | Apply `rules/toolchain.md` §7 (Diff-scoped coverage) and check that the specific bug-fix or new path achieves complete logical coverage. |
| 12 | Fix strategy | **Audit step**: Formulate the smallest possible fix. If implementation behavior is correct, fix the test; otherwise, fix the implementation. |
| 13 | Repository test policy compression | Update shared test utilities in `conftest.py`; record new patterns in `routing.md` or the skill's `workflow.md`. |

## Mandatory Record Template for Step 12 (Fix Strategy)

Before committing any fix for a broken or failing test, the AI MUST document its strategy in the thought process or final response using this format:

### [Test Fix Strategy Record]
- **Failure Symptom**: (Paste the exact error message or stack trace here)
- **Root Cause Analysis**: (Is the failure due to a broken implementation, a stale test expectation, or environmental factors?)
- **Scope of Change**: (List specific files and lines modified. Confirm each listed file is
  required to make the failing test pass — if a file could be removed from the list without
  the fix breaking, remove it; see `AGENTS.md` Global Rule 5 for the broader unrelated-change
  prohibition)
- **Contract Verification**: (Explain how the fix aligns with the application's structural contract, not just the test passing)

## See Also
See `workflow.md` for detailed phase content, plugin flags, and CLI commands.
Run tests via `uv run pytest` (see `AGENTS.md` Development); MUST NOT use `~/.local/bin/pytest`.

## Composes with
- `python-implementation` — if Step 12 determines that the fix requires modifying application logic beyond the test suite.
- `python-refactoring` — if resolving the failure or adding the test exposes architectural debt requiring a structural rewrite.

## Improvement feedback
After running this skill, if a skip criterion was wrong or a step was missing for a specific task type, update the Task Routing section in this file.

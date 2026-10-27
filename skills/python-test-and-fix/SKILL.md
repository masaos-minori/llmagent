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
- **Never Turn a Failure Green by Removing the Check**: MUST NOT add `pytest.mark.skip`/`skipif`/`xfail`, delete a test, loosen a test to vacuity, or widen a `--deselect`/`-k` filter to make a failing test pass. A skip or xfail is allowed only when the user asks for it or the cause is a documented, tracked environment limitation (cite the Issue); record it in the final response.
- **Verify Production Isolation Before Running Tests**: running the suite has real side effects on this host. Before the first test run, record what the isolation mechanism in `tests/conftest.py` (and `tests/test_production_isolation.py`) covers and what it does not, per `skills/test-audit/safety.md` "Verify the test suite's own isolation before classifying `Safe`". Do not run tests only when no mechanism exists for a production path the tests you will run reach. Default to `-m "not integration and not production_paths_allowed"`: `integration` tests start real subprocesses, and the `production_paths_allowed` marker exempts a test from the guard so it can write production state. Run either group only on request.
- **Wiring-Guard and Mock-State Prohibition**: A component constructed in `__init__` and shared with other objects MUST have a wiring-level guard test that runs the real constructor and asserts the production handoff; and a test MUST NOT assert on state the test itself assigned to a `MagicMock` — asserting self-assigned mock state hides the very defect (wrong or missing wiring) this rule exists to catch. A project example is in `workflow.md` Test structure.
- **Build Timeout / Branch Tests off the Production Body**: A test that asserts a branch fired (e.g. a timeout, a fallback) MUST exercise the real production step body, not a stub whose `await` behaviour the production method lacks. A stub whose await differs from production is the same defect class as an assertion that cannot fail.
- **No Tool Hallucination**: applies to every plugin and tool the Steps use — `mutmut`, `freezegun`, `respx`, `hypothesis`, `pytest-testmon`, `pytest-randomly`, `pytest-rerunfailures`, `pytest-timeout`, `pytest-subprocess`, `pytest-xdist`, `diff-cover` — see `skills/DESIGN.md` Tool availability guard. Confirm a plugin is installed before relying on it (`uv run pytest --help` lists its options; `uv pip list`). Fallbacks: standard `pytest`/`unittest.mock`, a shell loop for `--reruns`, `-p no:randomly` omitted when the plugin is absent. Record a skipped check as `Needs confirmation`.

## Task Routing (Step 1 Classification & Phase Guide)

Classify the task in **Step 1** and strictly follow the assigned path. MUST NOT skip mandatory steps.

Step 1 classification maps to a Path as follows (every classification has exactly one Path):

| Step 1 class | Path |
|---|---|
| bug | A |
| regression (behavior changed; find the breaking commit first, then reproduce and fix) | A |
| new test | B |
| fix broken (test exists but fails) | C |
| flaky | D |

### [Path A] Bug Fix Verification (classes: bug, regression)
- **Criteria**: Reproducing and fixing an implementation bug or regression.
- **Path**: 1 -> 2 -> 3 -> 5 -> 6 -> write the reproducing test -> 12 (record the strategy) -> apply the fix -> 4 (scoped to the fix, after it) -> 9 -> 10 -> 11 -> 13
- *Skip*: 7 (hypothesis)
- Step 4 is scoped to the changed lines; if `mutmut` is unavailable or cannot be scoped, record `Not run` with the reason (the 0-surviving-mutants target is then unverified, not met).

### [Path B] New Feature Test (class: new test)
- **Criteria**: Adding test coverage for a newly implemented feature.
- **Path**: 1 -> 2 -> 4 -> 5 -> 6 -> 7 -> 9 -> 10 -> 11 -> 13 (Step 12 only if a new test fails and needs a fix; its record comes before that fix)
- *Skip*: 3 (flaky detection) — instead run the new test file once in the default randomized order and once with `-p no:randomly`

### [Path C] Fix Broken Test (class: fix broken)
- **Criteria**: Repairing a test that is broken due to recent code changes or regressions.
- **Path**: 1 -> 2 -> 3 -> 12 (record the strategy) -> repair the test -> 5 -> 6 -> 7 (only when the repaired test targets a pure function that meets Step 7's conditions; otherwise not applicable) -> 9 -> 10 -> 11 -> 13
- *Skip*: 4 (mutmut)
- A repair never adds property tests or other new tests beyond what the fix needs (`AGENTS.md` Global Rule 5).

### [Path D] Flaky Test Investigation (class: flaky)
- **Criteria**: Debugging non-deterministic or intermittent test failures.
- **Path**: 1 -> 2 -> 3 (Mandatory multiple runs) -> 12 (record the strategy) -> apply the fix -> 5 -> 6 -> 9 -> 10 -> 11 -> 13
- *Skip*: 4 (mutmut), 7 (hypothesis)

Step 12's record is written before the first edit that changes a failing test or its implementation (the Mandatory Record below), so each Path list places it there, not at the end.

### Conditional step (any Path)
- **Step 8 (observability)** runs only when the behavior under test is a log or audit record that the task asserts; otherwise it is not applicable and is not reported as skipped.

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 1 | Classify the testing task | Classify task into bug / new test / fix broken / regression / flaky; map it to Path A, B, C, or D (table above). |
| 2 | Inspect before changing | Scan usages via `rg`, analyze `conftest.py`, and inspect existing fixtures to match repository testing patterns. |
| 3 | Flaky detection | Use `pytest-randomly` for seed randomization and run with `--reruns` or loops to confirm failure determinism. |
| 4 | Mutation testing | Run `mutmut` on the modified paths to validate that tests actually catch logical mutations. |
| 5 | Deterministic runtime | Enforce time determinism using `freezegun` for time-dependent assertions and use fixed random seeds. |
| 6 | Boundary virtualization | Use `pytest-subprocess`, `respx`, or `mocker`. Isolate the test environment and mock *only* at true external boundaries. |
| 7 | Contract validation | Use `hypothesis` for invariant-based property testing (restrict to pure functions like parsers or serializers). |
| 8 | Observability validation | Conditional: when the task asserts log/audit output, capture it with pytest's `caplog` fixture. Skip OTel unless project-wide patterns exist. |
| 9 | Resource leak detection | Audit `pytest-asyncio` lifecycles and use `pytest-timeout` to catch unclosed resources or hanging loops. |
| 10 | Impact-based execution | While iterating, run `pytest --testmon-forceselect` together with `-m` (plain `--testmon` is deactivated by `-m`) when `pytest-testmon` is installed and no other session uses `.testmondata`; the single full run in Step 11 is unchanged. |
| 11 | Regression quality analysis | Apply `rules/toolchain.md` §7 (Diff-scoped coverage) and check that the specific bug-fix or new path achieves complete logical coverage. |
| 12 | Fix strategy | **Audit step**, done before the fix (see the Path lists): Formulate the smallest possible fix. If implementation behavior is correct, fix the test; otherwise, fix the implementation. |
| 13 | Repository test policy compression | Place a fixture you added that 2+ test files need in `conftest.py` (never reorganize existing fixtures, never touch the production-isolation guard); propose (do not apply unprompted) any `routing.md`/skill/`rules/` documentation updates for new patterns. |

## Mandatory Record Template for Step 12 (Fix Strategy)

Before changing any file to fix a broken or failing test (and before any commit of it), the AI MUST document its strategy in the thought process or final response using this format:

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
Run every Python tool through `uv run` (`uv run pytest`, `uv run mutmut`; see `AGENTS.md` Development); MUST NOT use `~/.local/bin/pytest`. The commands in `workflow.md` already carry the prefix.

This skill does not stage, commit, or push. When the user asks for that, use `git-commit-and-sync`. A reproducing test and its fix may be delivered in one change set; any other test-plus-implementation mix needs the Step 12 plan.

## Called by
- `code-implementation` — Step 4 testing guidance.
- `git-commit-and-sync` — when tests fail in pre-commit or post-sync validation.
- `python-lint-typecheck`, `python-debug-root-cause`, `test-audit`, `python-refactoring` — when they route a test failure or new test here.

## Final response
Report: the Test Fix Strategy Record (for any fix to a failing test); the tests run with their pass/fail counts and the marker filter used; every check recorded `Not run` or `Needs confirmation` with its reason; the diff-cover result and how it was measured (`workflow.md` Step 11); and that the changes are uncommitted, so `git-commit-and-sync` commits them on request.

## Composes with
- `python-implementation` — if Step 12 determines that the fix requires modifying application logic beyond the test suite.
- `python-refactoring` — if resolving the failure or adding the test exposes architectural debt requiring a structural rewrite.
- `python-debug-root-cause` — if the failure's cause is unclear after Step 2-3 (the Root Cause Analysis in the Step 12 record cannot be filled).
- `test-audit` — for a whole-suite review rather than a single failing test or new test.
- `git-commit-and-sync` — to commit and push the result on request.

## Improvement feedback
After running this skill: a wrong skip criterion or missing step for a task type is fixed in Task Routing here; a wrong Step instruction/command/example, or a checklist that missed (or wrongly listed) a check, is fixed in `workflow.md`.

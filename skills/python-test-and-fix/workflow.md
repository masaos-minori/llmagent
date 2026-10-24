# Python Test And Fix — Detailed Workflow

## Toolchain

| Tool | Goal | Role |
|---|---|---|
| `pytest` | — | Test runner |
| `pytest-xdist` | — | Parallel execution (`-n auto`) |
| `pytest-cov` / `coverage` | regression quality analysis | Coverage measurement |
| `pytest-mock` | boundary virtualization | `mocker` fixture for patching |
| `pytest-randomly` | flaky detection | Randomize test order |
| `pytest-asyncio` | resource leak detection | Async test runner with lifecycle control |
| `pytest-subprocess` | boundary virtualization | Intercept and fake subprocess calls |
| `pytest-testmon` | impact-based test execution | Run only tests affected by changed files |
| `pytest-timeout` | resource leak detection | Catch hung tests |
| `pytest-rerunfailures` | flaky detection | Confirm or rule out intermittency |
| `mutmut` | mutation testing | Mutate source; count surviving mutants |
| `freezegun` | deterministic runtime | Freeze `datetime.now()` |
| `hypothesis` | contract validation | Property-based testing |
| `respx` | boundary virtualization | Mock `httpx` HTTP calls |
| `factory_boy` | — | Readable, repeatable test data factories |
| `diff-cover` | regression quality analysis | Coverage gate scoped to changed lines |

## Test structure

`tests/` mirrors the `scripts/` package layout: each `scripts/<package>/<module>.py` has its
test at `tests/<package>/test_<module>.py`.

```
tests/
  conftest.py                       # sys.path setup; shared fixtures
  agent/
    commands/test_<module>.py       # mirrors scripts/agent/commands/<module>.py
    memory/test_<module>.py         # mirrors scripts/agent/memory/<module>.py
    services/test_<module>.py       # mirrors scripts/agent/services/<module>.py
    shared/test_<module>.py         # mirrors scripts/agent/shared/<module>.py
    workflow/test_<module>.py       # mirrors scripts/agent/workflow/<module>.py
    test_<module>.py                # mirrors scripts/agent/<module>.py directly
  shared/test_<module>.py           # mirrors scripts/shared/<module>.py
  mcp_servers/
    <server>/test_<module>.py       # mirrors scripts/mcp_servers/<server>/<module>.py
    test_<module>.py                # mirrors scripts/mcp_servers/<module>.py directly
  rag/
    ingestion/test_<module>.py      # mirrors scripts/rag/ingestion/<module>.py
    test_<module>.py                # mirrors scripts/rag/<module>.py directly
  db/test_<module>.py               # mirrors scripts/db/<module>.py
  eventbus/test_<module>.py         # mirrors scripts/eventbus/<module>.py
  tools/test_<module>.py            # mirrors tools/<module>.py
  integration/                      # cross-module tests with no single scripts/ mirror
  docs/                             # doc-consistency checks with no single scripts/ mirror
  deploy/test_<module>.py           # checks for deploy/ scripts (no scripts/ mirror)
  test_<topic>.py                   # top-level cross-cutting tests (e.g. test_production_isolation.py)
```

A new test for a `scripts/` module goes at the mirrored path. Only a cross-cutting test with
no single module (isolation, lint-style invariants) goes at the top level of `tests/`.
Check the real tree with `ls tests/<package>` before adding a file; the list above is a map, not
an exhaustive inventory.

When finding or adding a test, mirror the target module's path under `scripts/`
(or `tools/`), not a flat `tests/test_<module>.py` layout.

A fixture that repairs production wiring must be paired with a wiring-level test. `_make_bare_repl` (`tests/agent/test_repl.py`) bypasses `AgentREPL.__init__` (`AgentREPL.__new__` plus a hand-supplied shutdown event) so its doubles stand in for config, terminal, LLM and MCP services; because it supplies what `__init__` does not, it must be paired with `TestWiringGuard`, which runs the real constructor and asserts one `asyncio.Event` is held across the objects that own it. Every wiring-repairing fixture in the suite carries such a paired guard and names it in its docstring — see the wiring-guard and mock-state rule in `SKILL.md`.

## Step 1: Classify the Testing Task

Before reading any test file, classify:

- **bug**: known failure; need a reproducing test + fix
- **new test**: coverage gap; add tests for existing behavior
- **fix broken**: test exists but fails; determine if test or impl is wrong
- **regression**: behavior changed; find the breaking commit (`git log -S`/`git bisect` is
  read-only research only — do not commit from it), then follow Path A
- **flaky**: intermittent failure; confirm before diagnosing

Classification determines which steps to run (class → Path table in `SKILL.md` Task Routing).
MUST NOT run the full sequence for every task.

**Completed when**: the task is classified as bug / new test / fix broken / regression /
flaky, and the matching Path (A/B/C/D, see `SKILL.md` Task Routing) is selected.
**Stop and ask the user before Step 2 when**: the task fits none of the five
classifications above (e.g. no failing test, no code change, and no coverage gap can be
identified) — there is nothing for this skill to act on.

Apply `rules/ai-execution.md` Step-Level Failure Triage (Base) to every later Step —
when an unavailable tool has a documented fallback in that Step, use it (or skip the
Step if none applies) instead of stopping the whole task.

## Step 2: Inspect Before Changing

```bash
rg "<symbol_under_test>" scripts/         # find usages
rg "<symbol_under_test>" tests/           # find existing tests
fd --glob "test_*" tests/<package>/       # list the target package's test files
```

Read `tests/conftest.py` (shared fixtures and the production-isolation guard) and the existing
tests for the target with the Read tool before writing new ones.

Before the first test run, apply `SKILL.md` Core rule "Verify Production Isolation Before
Running Tests": confirm the guard in `tests/conftest.py` covers the production paths in
`rules/env.md` (cite the file), and check the `integration` marker in `pyproject.toml`
(`-m "not integration"` by default). If a production path is unguarded, stop and record the
affected commands as `Needs confirmation`; MUST NOT run them.

Understand:

- available fixtures
- established mock boundaries
- the module's interface from the test perspective

## Step 3: Flaky Detection

If the failure is intermittent, run these in order (each with `uv run` and the mirrored test
path, e.g. `tests/<package>/test_<module>.py`, never a flat `tests/test_<module>.py`; add
`-m "not integration"` unless the test is an integration test); stop as soon as one gives a
clear answer:

```bash
pytest <test path> --randomly-seed=1234 -v
pytest <test path> --randomly-seed=0 -v
pytest <test path> --randomly-seed=4321 -v
pytest <test path> -p no:randomly -v      # fixed (collection) order
```

Run these four to separate an ordering dependency from non-determinism: each seed fixes one
order, so a failure that appears for some seeds and not others is an ordering dependency; a
failure that varies across repeated runs of the same seed is true non-determinism (timing,
external state). Use `--randomly-seed=last` to replay the last failing order.

`--reruns` is a confirmation aid only, not evidence of stability: a test that fails and then
passes on rerun is still flaky, and `--reruns` reports such a run as passed. To measure the
rate, run the same command in a loop without `--reruns`
(`for i in $(seq 1 10); do uv run pytest <test path> --randomly-seed=1234 -q || break; done`).

Identify the ordering dependency:

```bash
pytest tests/ --randomly-seed=last -v     # replay last failing order
pytest tests/ -p no:randomly              # disable to see if it disappears
```

**Completed when**: the failure is confirmed either as seed-order-dependent (fails
only on certain seeds, reproducibly) or as true non-determinism (varies across repeated runs
of the same seed), with the dependency (if any) identified via the replay commands above.

## Step 4: Mutation Testing

Before trusting an existing test suite for regression protection:

This repository uses mutmut 3.x (`mutmut --version`). Its mutation scope comes from
`[tool.mutmut] source_paths` in `pyproject.toml` (currently `scripts`); there is no
`--paths-to-mutate` or `--use-coverage` option. Mutant names are the dotted module path
under `source_paths` plus the function (for `scripts/shared/tool_executor.py`, names start
with `shared.tool_executor.`); `mutants/` holds the generated output and is git-ignored.

```bash
uv run mutmut run "shared.tool_executor.*"   # limit the run to one module's mutants (name pattern)
uv run mutmut results                        # list survived/killed mutants
uv run mutmut show <MUTANT_NAME>             # inspect one surviving mutant
uv run mutmut tests-for-mutant <MUTANT_NAME> # which tests exercise it
```

Check `uv run mutmut run --help` first (only `--max-children` and the mutant-name arguments
exist). If the run cannot be limited to the target in reasonable time (an unbounded
whole-`scripts/` run), record `Not run` with the reason instead of running it unbounded.

If `mutmut run` itself exits non-zero (distinct from completing and reporting
results): treat as a tool failure per `rules/ai-execution.md` Step-Level Failure
Triage — MUST NOT report mutation testing as passed.

A surviving mutant means the suite does not catch a one-line code change. Before
treating "0 surviving mutants" as evidence of reliability, confirm `mutmut results`
reports a non-zero total mutant count for the target — per `rules/ai-execution.md`
Repository Tool Usage #8, 0 surviving out of 0 total means the target was not mutated,
not that the suite is strong.
Add targeted tests to kill surviving mutants before declaring the suite reliable.

For a bug fix path (Path A): run the same name-scoped `mutmut run` for the function(s) the fix
changed, after the fix, then check `mutmut results` for those functions only.

## Step 5: Deterministic Runtime

#### freezegun — freeze time

```python
from freezegun import freeze_time

def test_cache_expiry():
    with freeze_time("2024-01-01 00:00:00") as frozen:
        cache = SemanticCache(ttl=3600)
        cache.put("q", "result")
        assert cache.get("q") == "result"
        frozen.tick(delta=3601)
        assert cache.get("q") is None
```

Use `freezegun` whenever the function under test reads the clock (`datetime.now()`,
`time.time()`). It does not skip `time.sleep()`: a code path that really sleeps must have the
sleep removed from the path under test (inject the delay or patch the sleeping call at the
boundary) rather than being "frozen". For async code, wait on events or futures; do not
combine a frozen monotonic clock with `asyncio` waits without checking, because a loop whose
clock is frozen can wait forever (freezegun's `real_asyncio` option exists for this; verify
the behavior in the target test before relying on it).

#### fixed random seed

```python
import random
import pytest

@pytest.fixture(autouse=True)
def fixed_seed():
    random.seed(42)
```

## Step 6: Boundary Virtualization

Mock only at true I/O boundaries. MUST NOT mock internal helpers.

#### respx — mock httpx at the transport level (preferred for httpx calls)

```python
import respx
import httpx

@respx.mock
def test_web_search_returns_empty_on_404():
    respx.get("https://api.search.brave.com/res/v1/web/search").mock(
        return_value=httpx.Response(404)
    )
    result = search("query")
    assert result == []
```

#### pytest-subprocess — intercept subprocess calls

```python
def test_subprocess_start(fake_process):
    fake_process.register(["agent.py", "--start"], returncode=0)
    result = start_service("file-mcp")
    assert result is True
```

Prefer `fake_process` over `mocker.patch("subprocess.run")` for subprocess calls.

## Step 7: Contract Validation

Use hypothesis **only** when ALL of the following are true:
- the function is pure (no I/O, no side effects, no DB access)
- an invariant holds for all inputs (idempotency, roundtrip, monotonicity)

Apply to: string normalizers, serializers, deserializers, chunk splitters, URL validators.
Skip for: REPL commands, DB operations, MCP handlers, LLM calls.

#### hypothesis — property-based invariants

```python
from hypothesis import given, settings
from hypothesis import strategies as st

@given(st.text())
@settings(max_examples=500)
def test_normalize_unicode_is_idempotent(text):
    from rag.utils import normalize_unicode  # real module path: scripts/rag/utils.py
    once = normalize_unicode(text)
    twice = normalize_unicode(once)
    assert once == twice

@given(st.floats(width=32, allow_nan=False, allow_infinity=False))
def test_floats_to_blob_roundtrip(f):
    # width=32 generates only float32-representable values, so packing is lossless
    # and exact equality holds; unbounded float64 would overflow or lose precision.
    import struct
    from rag.utils import floats_to_blob
    blob = floats_to_blob([f])
    recovered = struct.unpack("<f", blob)[0]
    assert recovered == f
```

**Completed when**: a property-based test has been written for each function
meeting both listed conditions, or the Step is confirmed not applicable (no function
in scope meets both conditions).

## Step 8: Observability Validation

This step is conditional (any Path): run it only when the task asserts log or audit output.

This project uses `logging.getLogger(__name__)`, so the logger name is the module's import
path under `PYTHONPATH=scripts` (for `scripts/shared/tool_executor.py`, `shared.tool_executor`),
not the bare file name. Take the name from the module itself instead of typing it. Skip OTel
span validation — not adopted project-wide.

To validate log output in tests, use pytest's `caplog` fixture:

```python
import logging

from shared import tool_executor

def test_tool_executor_logs_cache_hit(caplog):
    with caplog.at_level(logging.INFO, logger=tool_executor.logger.name):
        executor = ToolExecutor(...)
        executor.call("search_web", {"query": "test"})
        executor.call("search_web", {"query": "test"})
    assert any("cache_hit" in r.message for r in caplog.records)
```

## Step 9: Resource Leak Detection

#### pytest-asyncio — lifecycle control

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_no_pending_tasks_after_completion():
    # replace with a real async function under test (e.g. Orchestrator.handle_turn)
    await some_async_function_under_test()
    # all_tasks() includes the running test task itself; exclude it or the list is never empty
    current = asyncio.current_task()
    pending = [t for t in asyncio.all_tasks() if t is not current and not t.done()]
    assert len(pending) == 0, f"Leaked tasks: {pending}"
```

#### pytest-timeout — catch hung tests

```bash
pytest --timeout=10 tests/
pytest --timeout=10 tests/test_agent_repl.py
```

Add `@pytest.mark.timeout(5)` to individual tests that involve LLM calls or network I/O.

## Step 10: Impact-Based Execution

Use `pytest --testmon` while iterating on a fix within this same session; run the
repository's full, non-testmon `pytest` suite once before considering the task complete
(Step 11) regardless of testmon results — testmon narrows re-runs during iteration, it
does not replace the final full run.
Per `rules/ai-execution.md` Tool Usage's idempotent-command rule, MUST NOT re-run `pytest
--testmon` with no source change since the last run — its result is unchanged.
MUST NOT commit `.testmondata` (`.gitignore` already lists `.testmondata` and
`.testmondata-*`; confirm with `git check-ignore .testmondata` and do not re-add it):

```bash
pytest --testmon tests/                   # only tests affected by changed files
pytest --testmon-noselect tests/          # run everything, prioritising likely failures, update DB
pytest --testmon-forceselect tests/       # select only tests affected by changes, on top of -k/-m filters
```

`--testmon-noselect` is the testmon option that deselects nothing; `--testmon-forceselect`
narrows the selection, so it is not a full run.

## Step 11: Regression Quality Analysis

See `rules/toolchain.md` section 7 for the diff-cover sequence, and Step 4 above for the mutmut
commands. Target: 0 surviving mutants on the bug-fix code path (Path A) or on the new code
(Path B), counting only functions mutmut actually mutated. Paths C and D do not run Step 4;
Path A/B record `Not run` when Step 4 could not run, and the target is then reported as
unverified rather than met.

## Step 12: Fix Strategy

Applies `SKILL.md` Core Testing Rules ("Do Not Fix Tests by Blindly Changing Expectations").
Document the outcome using `SKILL.md` Mandatory Record Template.

When a test fails:

1. determine if the test reflects the correct contract
2. if the test is correct: fix the implementation (smallest change), then re-run only
   this test to confirm — MUST NOT re-derive the contract judgment from list item 1 again
3. if the test is wrong: fix the test to match the intended contract, then verify the
   impl is correct by re-running the corrected test — MUST NOT re-open the contract
   judgment unless the re-run surfaces new evidence

MUST NOT change both the test and the implementation in the same change set, except the
Path A case: a reproducing test written for a bug plus the fix that makes it pass (the test
first fails without the fix, then passes with it). Any other combination needs an explicit
plan in the Step 12 record. This skill never commits; use `git-commit-and-sync` on request.

If the re-run after a fix still fails, return to list item 1 and re-derive the contract
judgment from that new failure (list item 1's original judgment may have been wrong) — MUST NOT
simply try the other branch of list item 2/3 on the same judgment. Per
`AGENTS.md` Attempt Limit, at most 3 iterations of this list item 1→2/3→re-run cycle for the
same failing test; if it still fails after 3 attempts, stop and apply Rollback (see
`AGENTS.md` Loop Prevention > Rollback Directive) and report `Blocked: {test} still
failing after 3 fix attempts — {summary of each attempt}` — MUST NOT start a fourth
attempt as if it were a fresh judgment.

Smallest effective change rules:

- see `AGENTS.md` Global Rule 5 for the broader unrelated-refactoring prohibition
- add or adjust exactly one test per bug
- if the fix requires a larger structural change, use the python-refactoring skill

## Step 13: Repository Test Policy Compression

After adding tests, update project knowledge if patterns changed:

- **`tests/conftest.py`**: add fixtures used by 2+ test files (this is test code, within the
  task's scope)
- **Documentation** (`routing.md`, `rules/coding.md`, a skill's `workflow.md`, `CLAUDE.md`):
  do not edit unprompted (`AGENTS.md` Global Rule 5). Record a new test library or pattern as
  a proposal in the final response (what to document and where), and apply it only when the
  user asks. `CLAUDE.md` currently has no test library table; the library list is the
  Toolchain table above and `pyproject.toml`.
- **`.gitignore`**: `.testmondata` and `mutants/` are already ignored; add an entry only for
  a new generated artifact the task introduces.

Fixture naming conventions:

```python
# prefer descriptive fixture names
@pytest.fixture
def llm_client_with_timeout():
    return LLMClient(timeout=0.1)

# not generic names
@pytest.fixture
def client():  # ambiguous — which client?
    ...
```

## Completion checklist

**This task is complete when, and only when**: every item below is confirmed true, or the
task ended in a `Blocked` state per Step 12's own stop condition.

Confirm against each Step's stated criteria above; MUST NOT re-derive them:

- Step 1: failure classified before any code change; reproducing test written for bug-class failures
- Step 2: production isolation confirmed before the first test run; no test was skipped, xfailed, or deleted to get a green run
- Step 3 (Paths A, C, D): no flakiness introduced — the target passes under the seeds used and under `-p no:randomly`, and a 10-run loop of the same seed (without `--reruns`) shows no failure. Path B: the new test file passes in randomized order and with `-p no:randomly`
- Step 6: mock only at true I/O boundaries, no `mocker.patch` on internal helpers
- Step 10 / 13: `.testmondata` not committed
- Step 11 target (Paths A and B): 0 surviving mutants on the fix/new code, or `Not run` recorded with the reason (then reported as unverified); Paths C and D: not applicable
- Step 11 diff-scoped coverage: per `rules/toolchain.md` §7 (Diff-scoped coverage)

## Required behavior

- Mock only at true I/O boundaries, per Step 6 (network, subprocess, filesystem — call
  internal helpers directly).
- Write each test so it passes under any execution order — verify with
  `pytest -p no:randomly` vs. the default randomized order (Step 3).
- MUST NOT commit `.testmondata`, per Step 10.
- Use `freezegun` for clock-dependent tests and events/futures (with `asyncio.timeout()` only
  as a failure bound, not as the timing source) for async waits, per Step 5 — never
  `time.sleep()` as a fix.
- Assert on the function's public contract (return value, raised exception, observable
  side effect) — never on an internal variable name, private attribute, or call count to
  a helper that isn't the boundary under test.
- Change test and implementation in the same change set only for a Path A reproducing
  test plus its fix, or when Step 12 explicitly plans both (e.g. the test itself had a
  bug) — otherwise change one, verify, then the other.

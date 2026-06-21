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

```
tests/
  conftest.py              # sys.path setup; shared fixtures
  test_<module>.py         # one file per scripts/**/<module>.py
```

---

## Step 1: Classify the Testing Task

Before reading any test file, classify:

- **bug**: known failure; need a reproducing test + fix
- **new test**: coverage gap; add tests for existing behavior
- **fix broken**: test exists but fails; determine if test or impl is wrong
- **regression**: behavior changed; find the breaking commit
- **flaky**: intermittent failure; confirm before diagnosing

Classification determines which steps to run. Do not run the full sequence for every task.

---

## Step 2: Inspect Before Changing

```bash
rg "<symbol_under_test>" scripts/         # find usages
rg "<symbol_under_test>" tests/           # find existing tests
cat tests/conftest.py                     # read shared fixtures
fd --glob "test_*" tests/                 # list all test files
```

Read the existing tests before writing any new ones. Understand:

- what fixtures are already available
- what mock boundaries are established
- what the module's interface looks like from the test perspective

---

## Step 3: Flaky Detection

If the failure is intermittent:

```bash
pytest tests/test_<module>.py --randomly-seed=1234 -v
pytest tests/test_<module>.py --randomly-seed=0 -v
pytest tests/test_<module>.py --reruns 10 --reruns-delay 0.2
```

Confirm flakiness by reproducing with at least 3 different seeds.
If the test fails only on certain seeds: the test has an ordering dependency.

Identify the dependency:

```bash
pytest tests/ --randomly-seed=last -v     # replay last failing order
pytest tests/ -p no:randomly              # disable to see if it disappears
```

---

## Step 4: Mutation Testing

Before trusting an existing test suite for regression protection:

```bash
mutmut run --paths-to-mutate scripts/<module>.py
mutmut results
mutmut show <id>                           # inspect surviving mutant
```

A surviving mutant means the test suite does not catch a one-line code change.
Add targeted tests to kill surviving mutants before declaring the suite reliable.

For a bug fix path: run mutmut specifically on the changed lines after the fix.

```bash
mutmut run --paths-to-mutate scripts/<module>.py --use-coverage
```

---

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

Use `freezegun` whenever the function under test calls `datetime.now()`, `time.time()`, or `time.sleep()`.

#### fixed random seed

```python
import random
import pytest

@pytest.fixture(autouse=True)
def fixed_seed():
    random.seed(42)
```

---

## Step 6: Boundary Virtualization

Mock only at true I/O boundaries. Do not mock internal helpers.

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

---

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
    from rag_utils import normalize_unicode
    once = normalize_unicode(text)
    twice = normalize_unicode(once)
    assert once == twice

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_floats_to_blob_roundtrip(f):
    import struct
    from rag_utils import floats_to_blob
    blob = floats_to_blob([f])
    recovered = struct.unpack("<f", blob)[0]
    assert abs(recovered - f) < 1e-5
```

---

## Step 8: Observability Validation

This project uses `logging.getLogger(__name__)`. Skip OTel span validation — not adopted project-wide.

To validate log output in tests, use pytest's `caplog` fixture:

```python
import logging

def test_tool_executor_logs_cache_hit(caplog):
    with caplog.at_level(logging.INFO, logger="tool_executor"):
        executor = ToolExecutor(...)
        executor.call("search_web", {"query": "test"})
        executor.call("search_web", {"query": "test"})
    assert any("cache_hit" in r.message for r in caplog.records)
```

---

## Step 9: Resource Leak Detection

#### pytest-asyncio — lifecycle control

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_no_pending_tasks_after_completion():
    # replace with a real async function under test (e.g. Orchestrator.handle_turn)
    await some_async_function_under_test()
    pending = [t for t in asyncio.all_tasks() if not t.done()]
    assert len(pending) == 0, f"Leaked tasks: {pending}"
```

#### pytest-timeout — catch hung tests

```bash
pytest --timeout=10 tests/
pytest --timeout=10 tests/test_agent_repl.py
```

Add `@pytest.mark.timeout(5)` to individual tests that involve LLM calls or network I/O.

---

## Step 10: Impact-Based Execution

For fast dev feedback — do not commit `.testmondata`:

```bash
pytest --testmon tests/                   # only tests affected by changed files
pytest --testmon --testmon-forceselect    # force full run, update DB
```

Add `.testmondata` to `.gitignore`.

---

## Step 11: Regression Quality Analysis

```bash
coverage run -m pytest tests/
coverage xml
diff-cover coverage.xml --compare-branch=master
diff-cover coverage.xml --compare-branch=master --fail-under=90
```

For bug fixes: run mutmut on the exact lines that changed:

```bash
mutmut run --paths-to-mutate scripts/<module>.py
mutmut results
```

Target: 0 surviving mutants on the bug-fix code path.

---

## Step 12: Fix Strategy

When a test fails:

1. determine if the test reflects the correct contract
2. if the test is correct: fix the implementation (smallest change)
3. if the test is wrong: fix the test to match the intended contract, then verify the impl is correct

Do not change both the test and the implementation in the same commit.

Smallest effective change rules:

- change only the lines that are incorrect
- do not refactor the surrounding code in the same commit
- add or adjust exactly one test per bug
- if the fix requires a larger structural change, use the python-refactoring skill

---

## Step 13: Repository Test Policy Compression

After adding tests, update project knowledge if patterns changed:

- **`tests/conftest.py`**: add fixtures used by 2+ test files
- **`CLAUDE.md` test library table**: document any new test library with its use case
- **`.gitignore`**: add `.testmondata` if not present

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

---

## Completion checklist

- failure classified before any code change
- reproducing test written before fixing implementation
- mock only at true I/O boundaries (http, subprocess, filesystem, DB)
- no `mocker.patch` on internal helpers
- `diff-cover coverage.xml --compare-branch=master --fail-under=90` passes
- `pytest --reruns 5` passes — no flakiness introduced
- `mutmut` 0 surviving mutants on bug-fix path
- `.testmondata` not committed

---

## Prohibited behavior

- do not mock internal helpers — mock only at true boundaries
- do not write tests that pass only with a specific execution order
- do not commit `.testmondata`
- do not add `time.sleep()` in tests — use `freezegun` or `asyncio.timeout()`
- do not write overspecified tests that assert on implementation details
- do not change test and implementation in the same commit when diagnosing a failure

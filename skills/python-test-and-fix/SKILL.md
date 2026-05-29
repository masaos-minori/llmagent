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

Add, repair, and improve Python tests with minimal, correct, and maintainable changes,
using the full toolchain to detect flakiness, validate contracts, and measure regression quality.

## Primary goals

- reproduce the problem clearly
- protect behavior with meaningful tests
- fix the smallest correct implementation surface
- avoid brittle or overspecified tests
- preserve or improve regression detection

---

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
  conftest.py          # sys.path setup; shared fixtures
  test_<module>.py     # one file per scripts/<module>.py
```

---

## Phase overview

| Step | Name | Goal |
|---|---|---|
| 1 | Classify the testing task | bug / new test / fix broken / regression / flaky |
| 2 | Inspect before changing | rg usages; read conftest; existing fixtures |
| 3 | Flaky detection | pytest-randomly seeds; --reruns to confirm |
| 4 | Mutation testing | mutmut to validate test suite strength |
| 5 | Deterministic runtime | freezegun for time; fixed seed in CI |
| 6 | Boundary virtualization | pytest-subprocess, respx, mocker — mock only at true boundaries |
| 7 | Contract validation | hypothesis for invariants — pure functions only (parsers, serializers) |
| 8 | Observability validation | logging capture — skip OTel; not adopted project-wide |
| 9 | Resource leak detection | pytest-asyncio lifecycle; pytest-timeout |
| 10 | Impact-based execution | pytest-testmon for fast dev feedback |
| 11 | Regression quality analysis | diff-cover ≥ 90%; mutmut score on bug-fix path |
| 12 | Fix strategy | smallest change; fix impl if test reflects contract |
| 13 | Repository test policy compression | conftest patterns; CLAUDE.md test library table |

## Phase skip table (based on Step 1 classification)

| Task type | Skip steps |
|---|---|
| bug | 4 (mutmut), 7 (hypothesis), 8 (OTel) |
| new test | 3 (flaky detection), 8 |
| fix broken | 4 (mutmut), 8 |
| regression | 8 |
| flaky | 4 (mutmut), 7 (hypothesis), 8 |

**Execution policy** — run non-destructive commands (file reads, grep, lint, type checks, tests) directly without asking for user confirmation. These are always safe to execute; user approval before each run is explicitly not required.

---

See `workflow.md` for detailed phase content.
See `rules/coding.md` for prohibited behavior and conventions.
See `rules/toolchain.md` for the standard validation sequence.

## Composes with

- `python-implementation` — if the fix requires changing implementation beyond the test fix
- `python-refactoring` — if a larger structural change is needed (use Step 12 decision)

## Improvement feedback

After running this skill, if a skip criterion was wrong or a step was missing for a task type:
update the phase skip table above.

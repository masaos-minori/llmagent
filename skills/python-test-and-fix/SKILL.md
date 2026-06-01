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

Add, repair, and improve Python tests; reproduce the problem clearly; fix the smallest correct implementation surface.

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

---

See `workflow.md` for detailed phase content.

## Composes with

- `python-implementation` — if the fix requires changing implementation beyond the test fix
- `python-refactoring` — if a larger structural change is needed (use Step 12 decision)

## Improvement feedback

After running this skill, if a skip criterion was wrong or a step was missing for a task type:
update the phase skip table above.

---
name: python-debug-root-cause
description: |
  Use this skill PROACTIVELY when debugging Python failures, exceptions,
  incorrect behavior, regressions, or intermittent bugs in this project.
  Covers: observability, tracing, runtime inspection, env reproduction,
  forensic tooling, and causal validation tooling.
  Use when the task involves root cause analysis, reproduction steps,
  log inspection, stack traces, failure isolation, or narrowing hypotheses
  before changing code.
---

# Debug Root Cause Skill

## Purpose

Investigate Python failures systematically; reproduce with evidence; separate observations from hypotheses; find root cause before touching code.

---

## Core Debugging Rules (Strictly Enforced for AI)

- **Do Not Touch Production Code Early**: Never modify application logic during the investigation phases (Phases 1-7). Code changes are strictly forbidden until a reproducible test case is established in Phase 8.
- **No Tool Hallucination**: If an advanced tool (e.g., `viztracer`, `py-spy`, `mitmproxy`) is required but not installed in the environment, **do not invent its output**. Immediately fallback to native Python capabilities (`pdb`, `traceback`, `logging`, `print` inspecting) and document the fallback.
- **Evidence-Driven**: Every bug report must be backed by an actual log snippet, stack trace, or test failure output. Do not assume the cause without copying the exact error message.

---

## Phase overview

| Phase | Name | Goal / AI Action |
|---|---|---|
| 1 | Problem Framing | State the exact symptom, expected behavior, environment info, and whether it is deterministic or intermittent. |
| 2 | Initial Observability | Filter and analyze logs using tools like `jq`, `lnav`, `multitail`, or Sentry. |
| 3 | Failure Classification | Classify the bug into the matrix: (Deterministic/Intermittent) $\times$ (Sync/Async) $\times$ (Logic/IO/Network/Perf). |
| 4 | Focused Reproduction | Create a minimal isolation environment using `tox`, `httpie`, `/mcp`, `sqlite3`, etc. |
| 5 | Runtime / Trace Inspection | Run profiling/tracing tools (`viztracer`, `py-spy`, `strace`, `tracemalloc`, `aiomonitor`, `ipdb`) to capture state. |
| 6 | Hypothesis Validation | Create a Hypothesis Table. Validate or invalidate each using `respx`, `freezegun`, or reruns. |
| 7 | Regression Localization | Pinpoint the introducing commit using `git bisect` or analyzing `lnav` time windows. |
| 8 | Minimal Fix | Write a strictly failing test case that captures the bug *before* changing code. Delegate fix to `python-test-and-fix`. |
| 9 | Validation + Cleanup | Run `pytest` + `ruff`. Restart affected services. Ensure all temporary debug logs/artifacts are removed. |

---

## Phase routing (Based on Phase 3 Classification)

AI Must dynamically adjust its execution path based on Phase 3 classification:

- **Deterministic $\times$ Logic**: 1 $\rightarrow$ 2 $\rightarrow$ 3 $\rightarrow$ 4 $\rightarrow$ 6 (hypothesis/ipdb) $\rightarrow$ 8 $\rightarrow$ 9
  - *Skip*: 5 (viztracer/strace), 7 (bisect)
- **Deterministic $\times$ I/O**: 1 $\rightarrow$ 2 $\rightarrow$ 3 $\rightarrow$ 4 (sqlite3/httpie) $\rightarrow$ 5 (strace) $\rightarrow$ 8 $\rightarrow$ 9
  - *Skip*: 7 (bisect)
- **Deterministic $\times$ Network**: 1 $\rightarrow$ 2 $\rightarrow$ 3 $\rightarrow$ 4 (mitmproxy/httpie//mcp) $\rightarrow$ 6 $\rightarrow$ 8 $\rightarrow$ 9
  - *Skip*: 5 (strace), 7 (bisect)
- **Intermittent**: 1 $\rightarrow$ 2 $\rightarrow$ 3 $\rightarrow$ 4 $\rightarrow$ 6 (reruns/freezegun) $\rightarrow$ 7 (bisect) $\rightarrow$ 8 $\rightarrow$ 9
  - *Skip*: 5 (strace/tracemalloc)
- **Performance**: 1 $\rightarrow$ 2 $\rightarrow$ 3 $\rightarrow$ 5 (py-spy/viztracer) $\rightarrow$ 8 $\rightarrow$ 9
  - *Skip*: 6 (hypothesis/freezegun)

---

## Mandatory Output Template for Phase 6 (Hypothesis Validation)

When executing Phase 6, the AI must format its findings using the following structured table to prevent logical leaps:

### Hypothesis Analysis Matrix
| ID | Hypothesis Description | Verification Method / Command | Results Observed | Status (Validated / Invalidated) |
|---|---|---|---|---|
| H-01 | [e.g., Race condition in async loop] | [e.g., Run with 100 iterations via pytest-rerunfailures] | [e.g., Failed 3/100 times with same traceback] | **Validated** |
| H-02 | [e.g., Network timeout from external API] | [e.g., Mock timeout using respx] | [e.g., Raised different exception type] | **Invalidated** |

---

## See Also
See `workflow.md` for detailed phase content.
See `rules/env.md` for service ports and status commands.

## Composes with

- `python-test-and-fix` — Phase 8 (Minimal Fix) delegates test writing and fix validation.
- `python-implementation` — If the root cause requires a feature-level code change.

## Improvement feedback

After running this skill, if a hypothesis in Phase 6 was missing for a common failure mode:
add it to the hypothesis table in `workflow.md` Phase 6.

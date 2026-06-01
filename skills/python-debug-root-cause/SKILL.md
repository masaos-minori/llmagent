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

## Phase overview

| Phase | Name | Goal |
|---|---|---|
| 1 | Problem Framing | state symptom, expected, env, deterministic/intermittent |
| 2 | Initial Observability | jq/lnav log filtering; multitail; sentry (if DSN configured) |
| 3 | Failure Classification | Deterministic/Intermittent × Sync/Async × Logic/IO/Network/Perf |
| 4 | Focused Reproduction | tox, mitmproxy, httpie, /mcp, sqlite3, service status |
| 5 | Runtime / Trace Inspection | viztracer, py-spy, strace, tracemalloc, aiomonitor, ipdb |
| 6 | Hypothesis Validation | common hypothesis table; hypothesis, respx, freezegun, reruns |
| 7 | Regression Localization | git bisect, lnav time window, rg call sites |
| 8 | Minimal Fix | write failing test before changing code; delegate to python-test-and-fix |
| 9 | Validation + Cleanup | pytest, ruff, service restart, remove debug artifacts |

## Phase routing (based on Phase 3 classification)

| Classification | Required phases | Skip |
|---|---|---|
| Deterministic × Logic | 1→2→3→4→6 (hypothesis/ipdb)→8→9 | 5 (viztracer/strace), 7 (bisect) |
| Deterministic × I/O | 1→2→3→4 (sqlite3/httpie)→5 (strace)→8→9 | 7 (bisect) |
| Deterministic × Network | 1→2→3→4 (mitmproxy/httpie//mcp)→6→8→9 | 5 (strace), 7 (bisect) |
| Intermittent | 1→2→3→4→6 (reruns/freezegun)→7 (bisect)→8→9 | 5 (strace/tracemalloc) |
| Performance | 1→2→3→5 (py-spy/viztracer)→8→9 | 6 (hypothesis/freezegun) |

---

See `workflow.md` for detailed phase content.
See `rules/env.md` for service ports and status commands.

## Composes with

- `python-test-and-fix` — Phase 8 (Minimal Fix) delegates test writing and fix validation
- `python-implementation` — if the root cause requires a feature-level code change

## Improvement feedback

After running this skill, if a hypothesis in Phase 6 was missing for a common failure mode:
add it to the hypothesis table in workflow.md Phase 6.

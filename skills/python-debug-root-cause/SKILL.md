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

Investigate Python failures systematically; reproduce with evidence; separate observations from hypotheses; find root cause before touching code. No code changes during Phases 1-7 — see `skills/DESIGN.md` Analysis-only phase constraint. The write phase is Phase 8 (Minimal Fix).

---

## Core Debugging Rules (Strictly Enforced for AI)

- **No Tool Hallucination**: applies to every optional tool in `workflow.md` Toolchain (`lnav`, `multitail`, `strace`, `py-spy`, `viztracer`, `mitmproxy`, `httpie`, `tox`, `aiomonitor`, ...), several of which are not installed on every host (check with `command -v <tool>`) — see `skills/DESIGN.md` Tool availability guard. Use the fallback in `workflow.md` Toolchain and record the check as `Needs confirmation` when no fallback gives equal evidence.
- **Evidence-Driven**: Every bug report MUST be backed by an actual log snippet, stack trace, or test failure output. MUST NOT assume the cause without copying the exact error message.
- **Production Safety (read-only by default)**: the observation tools run against a host whose configuration points at `/opt/llm`. Reading logs and files is allowed. The following need the user's explicit confirmation before they run, and an isolated alternative is preferred: attaching to a running process (`strace -p`, `py-spy --pid`, `aiomonitor`), routing the agent through a proxy (`mitmproxy`), any request that can execute a tool or write state (`POST /v1/call_tool`), `git bisect` in the working tree, restarting a service, and running the test suite before the production-isolation check (`python-test-and-fix` Core rules). A confirmation covers the one action named, not later ones.

---

## Phase overview

| Phase | Name | Goal / AI Action |
|---|---|---|
| 1 | Problem Framing | State the exact symptom, expected behavior, environment info, and whether it is deterministic or intermittent. |
| 2 | Initial Observability | Check the `agent.log` format first (text by default, JSON-lines only when `structured_log` is on), then filter with `rg`/`jq` accordingly; `lnav` / `multitail` only as `workflow.md` Phase 2 directs. Logs are under `/opt/llm/logs/`; see `rules/env.md`. |
| 3 | Failure Classification | Classify the bug into the matrix: (Deterministic/Intermittent) × (Sync/Async) × (Logic/IO/Network/Perf). |
| 4 | Focused Reproduction | Create a minimal isolation environment using `uv run pytest`, `tox` (if installed), `httpie`, `/mcp`, `sqlite3`, etc., under the Production Safety rule. |
| 5 | Runtime / Trace Inspection | Run profiling/tracing tools (`viztracer`, `py-spy`, `strace`, `tracemalloc`, `aiomonitor`, `ipdb`) to capture state; attaching to a live process needs confirmation. |
| 6 | Hypothesis Validation | Create a Hypothesis Table from the observations. Validate or invalidate each using `respx`, `freezegun`, or repeated runs. |
| 7 | Regression Localization | Pinpoint the introducing commit using `git bisect` (clean tree or separate worktree) or analyzing log time windows. |
| 8 | Minimal Fix | Report the root cause, confidence, and proposed fix first (the fix gate); then write a failing test that captures the bug *before* changing code. Delegate fix to `python-test-and-fix`. |
| 9 | Validation + Cleanup | Run the tests (after the isolation check), `ruff`, and the project gates. Restart affected services only with confirmation. Ensure all temporary debug logs/artifacts are removed. |

---

## Phase routing (Based on Phase 3 Classification)

AI MUST dynamically adjust its execution path based on Phase 3 classification. Select the
route by this precedence (first match wins): **Performance** > **Intermittent** (any domain,
sync or async) > **Deterministic** by failure domain (Logic, I/O, Network). The Sync/Async
axis does not change the route; it selects the tools within a phase (`workflow.md` Phase 3).

- **Performance**: 1 → 2 → 3 → 5 (py-spy/viztracer, or the fallback) → 6 (a short table of the profiled hot spots) → 8 → 9
  - *Skip*: 4 (focused reproduction), 7 (bisect)
  - Phase 6 is not skipped: Phase 8's failing test needs a stated hypothesis (for a performance bug, a bound such as a time or allocation budget).
- **Intermittent**: 1 → 2 → 3 → 4 → 6 (repeated runs/freezegun) → 7 (bisect) → 8 → 9
  - *Skip*: 5 unless the hypotheses need a trace (then run only the one tool the hypothesis names)
- **Deterministic × Logic**: 1 → 2 → 3 → 4 → 6 (hypothesis/ipdb) → 8 → 9
  - *Skip*: 5 (viztracer/strace); 7 (bisect) unless Phase 2 or Phase 4 points to a recent change — then run it
- **Deterministic × I/O**: 1 → 2 → 3 → 4 (sqlite3/httpie) → 5 (strace or the fallback) → 6 (a short table of the I/O hypotheses) → 8 → 9
  - *Skip*: 7 (bisect) unless a recent change is suspected
- **Deterministic × Network**: 1 → 2 → 3 → 4 (mitmproxy/httpie//mcp) → 6 → 7 (when the failure began after a known change) → 8 → 9
  - *Skip*: 5 (strace)

Phase 6 is mandatory on every route: no fix is written before at least one hypothesis is
Validated, and a skipped phase is replaced by the Phase 6 table, not by guessing.

---

## Mandatory Output Template for Phase 6 (Hypothesis Validation)

When executing Phase 6, the AI MUST format its findings using this table:

### Hypothesis Analysis Matrix
| ID | Hypothesis Description | Suggested by (observation) | Verification Method / Command | Results Observed | Status (Validated / Invalidated / Inconclusive) |
|---|---|---|---|---|---|
| H-01 | [e.g., Race condition in async loop] | [e.g., Phase 2 log: same session errors only under load] | [e.g., Run 100 iterations of the target test, no `--reruns`] | [e.g., Failed 3/100 times with same traceback] | **Validated** |
| H-02 | [e.g., Network timeout from external API] | [e.g., Phase 2 log: retry events before the failure] | [e.g., Mock timeout using respx] | [e.g., Raised different exception type] | **Invalidated** |

`Inconclusive` means the check could not be run (tool unavailable, no safe way to run it) or
gave ambiguous output. It is not counted as Invalidated or Validated; state what is needed to
resolve it, and carry it into the report's residual uncertainty.

---

## See Also
See `workflow.md` for phase details; `rules/env.md` for service ports and status commands.

## Composes with

- `python-test-and-fix` — Phase 8 (Minimal Fix) delegates test writing and fix validation.
- `python-implementation` — If the root cause requires a feature-level code change.
- `python-refactoring` — If the root cause is a structural issue (Phase 8).
- `python-lint-typecheck` — If Phase 9's `ruff`/`mypy` gates fail for reasons the fix caused.
- `deploy` — Phase 9b: restarting or redeploying services after a production code change.
- `issue-creator` — If the root cause is found but the fix is out of scope or declined: record the finding as an Issue instead of fixing.

## Improvement feedback

If a common failure mode lacked a Phase 6 hypothesis, add it to the hypothesis table in `workflow.md` Phase 6.

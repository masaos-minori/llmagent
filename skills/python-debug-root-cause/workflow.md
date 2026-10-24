# Debug Root Cause — Detailed Workflow

## Toolchain

| Tool | Phase | Role |
|---|---|---|
| `rg` / `grep` + `jq` | Initial Observability | Filter `agent.log` (text by default; `jq` only for the JSON-lines format) |
| `lnav` | Initial Observability | Interactive log navigator |
| `multitail` | Initial Observability | Follow multiple log files simultaneously |
| `sentry-sdk` | Initial Observability | Exception capture with context (only if the project already configures a DSN) |
| `tox` | Focused Reproduction | Reproduce failures in isolated env |
| `mitmproxy` | Focused Reproduction | Intercept live HTTP traffic |
| `httpie` | Focused Reproduction | Ad-hoc endpoint testing |
| `sqlite3` (CLI) | Focused Reproduction | Inspect DB state |
| `viztracer` | Runtime / Trace Inspection | Wall-clock execution timeline |
| `py-spy` | Runtime / Trace Inspection | Sampling profiler; attaches to live process |
| `opentelemetry-sdk` | Runtime / Trace Inspection | Distributed traces |
| `strace` | Runtime / Trace Inspection | Syscall-level tracing |
| `tracemalloc` | Runtime / Trace Inspection | Memory allocation tracing |
| `aiomonitor` | Runtime / Trace Inspection | Live asyncio task inspector |
| `ipdb` | Runtime / Trace Inspection | Interactive breakpoint debugger |
| `rich` | Runtime / Trace Inspection | Pretty-print objects and tracebacks |
| `stackprinter` | Runtime / Trace Inspection | Multi-frame stack traces |
| `hypothesis` | Hypothesis Validation | Find minimal failing input |
| `pytest-asyncio` | Hypothesis Validation | Reproduce async bugs |
| `freezegun` | Hypothesis Validation | Freeze time for TTL/cache bugs |
| `respx` | Hypothesis Validation | Mock httpx calls |
| `pytest-rerunfailures` | Hypothesis Validation | Confirm intermittency |
| `pytest-timeout` | Hypothesis Validation | Detect hangs |
| `git bisect run` | Regression Localization | Automated regression commit search |
| `rg` | — | Fast text search |

Apply `rules/ai-execution.md` Tool Usage's idempotent-command rule throughout: MUST NOT
re-run a log/trace command against the same file at the same offset without new evidence
(e.g. the same `tail`/`jq` filter twice).

Run every Python tool through `uv run` (`uv run pytest`, not a bare `pytest`); the commands
below omit the prefix for brevity. Use mirrored test paths (`tests/<package>/test_<module>.py`).

### Tool availability and fallbacks

Tools come in two kinds, and the availability check differs (checking the wrong way gives a
false "missing"):

- **Python-package tools** (`viztracer`, `py-spy`, `mitmproxy`, `http` from httpie, `tox`,
  `pyright`, `ipdb`, `aiomonitor`, ...) are installed in the project environment, not on PATH.
  Run them as `uv run <tool> ...` and check with `uv run <tool> --version`. Libraries without a
  command (`aiomonitor`, `ipdb`, `rich`, `stackprinter`) are checked by importing them:
  `uv run python -c "import aiomonitor"`. On this host, `viztracer`, `py-spy`, `mitmproxy`, `http`,
  and `tox` run under `uv run` although `command -v` finds none of them.
- **System tools** (`strace`, `lnav`, `multitail`, `jq`, `sqlite3`, `rg`) are checked with
  `command -v <tool>`; they may be absent.

Re-check on each host rather than trusting this list. If the correct check fails, apply
`skills/DESIGN.md` Tool availability guard and use the fallback, recording the check as
`Needs confirmation` when the fallback gives weaker evidence:

| Missing tool | Fallback |
|---|---|
| `lnav`, `multitail` | `rg`/`grep` with a time-window filter on the log; `tail -f` for one file |
| `strace` | `python -X faulthandler`, `lsof -p <PID>` / `/proc/<PID>/fd` for open files, application logs |
| `py-spy` | `faulthandler.dump_traceback_later`, `cProfile`, `tracemalloc` for memory |
| `viztracer` | `cProfile` / `python -X importtime` |
| `mitmproxy` | an `httpx` event hook or `respx` in a test to capture the request/response |
| `httpie` (`http`) | `curl` (or `uv run python -c` with `httpx`) |
| `tox` | `uv run pytest` directly |
| `aiomonitor` | `PYTHONASYNCIODEBUG=1`, `asyncio.all_tasks()` dump from a test, `faulthandler` |

`py-spy --pid` and `strace -p` additionally need ptrace permission on the target process; a
permission error is an observation to record, not a reason to escalate privileges.

---

## Phase 1: Problem Framing

Before any tool use, identify:

- observed behavior (exact error message or symptom)
- expected behavior
- affected input or environment
- whether the issue is deterministic, intermittent, or unknown
- where it happens: this working tree / an isolated test, or the running production services
  under `/opt/llm` (this decides which `SKILL.md` Production Safety confirmations apply)

State unknowns explicitly. Record `git status --short` as the working-tree baseline before any
edit: changes already present (another session's edits, earlier work) are not this task's, and
Phase 7's bisect rule and Phase 9c rely on it.

**Completed when**: observed behavior, expected behavior, affected input/environment, and
reproducibility are all recorded — each either as a confirmed value or an explicit unknown.
**Stop and ask the user before Phase 2 when**: neither an exact error message/symptom nor
a way to reproduce or observe it (a log, a failing test, a user-reported trace) is
available — there is no evidence to investigate from. Any other unknown is recorded and
Phase 2 proceeds to gather evidence for it.

---

## Phase 2: Initial Observability

Read the logs (read-only). First check the format, because it decides the filter:

```bash
tail -3 /opt/llm/logs/agent.log
```

`agent.log` is text by default: `YYYY-MM-DD HH:MM:SS,mmm LEVEL [function] message`
(`scripts/shared/logger.py`). It is JSON-lines (keys `ts`, `level`, `func`, `msg`, plus
`session_id`, `turn_id`, ... when set) only when the agent's `structured_log` setting is on.
`structlog` is not used for these logs. Pick the matching block below. Besides `agent.log`,
`/opt/llm/logs/` holds other logs the failure may have left traces in (list them with
`ls /opt/llm/logs/`): `audit.log` (turn-level events, JSON-lines), the per-service MCP logs
(`<server>-mcp.log`), and the ingestion logs (`ingest.log`, `chunk.log`, `crawl.log`). Pick the
log of the component that failed, not only `agent.log`.

Rules for reading and quoting logs:

- Tracebacks span several lines, and a one-line `rg " ERROR "` returns only the first. Add
  context: `rg -A 15 " ERROR "` (or `-B 2 -A 15` around the match).
- Rotation is not documented here. Prefer a time window (`rg "^<date> <hour>:"`) over a fixed
  `tail -N`, and confirm the log covers the failure time (the first line's date).
- Logs can contain secrets (tokens, authorization headers, production values). Before quoting a
  snippet in the report, replace each secret with `<redacted>` (`skills/DESIGN.md` No secrets in
  output); keep the rest of the text exact.

Use `lnav` only when plain filtering cannot narrow the window (e.g. correlating across log files by time). Use
`multitail` only when several services must be watched live as the failure reproduces (not for
a historical failure). Use `sentry-sdk` only if the project already configures a DSN — it
captures future occurrences; it does not analyze a failure that already produced a log.

#### Text format (default): rg / grep

```bash
tail -2000 /opt/llm/logs/agent.log | rg -A 15 " (ERROR|WARNING) "       # -A 15: keep multi-line tracebacks
tail -2000 /opt/llm/logs/agent.log | rg "tool_called"
tail -2000 /opt/llm/logs/agent.log | rg "<session id>"
tail -2000 /opt/llm/logs/agent.log | awk '{print $3, $4}' | sort | uniq -c | sort -rn | head   # level + function
```

#### JSON-lines format (`structured_log` on): jq

```bash
tail -200 /opt/llm/logs/agent.log | jq 'select(.level == "ERROR")'
tail -500 /opt/llm/logs/agent.log | jq 'select(.msg | contains("tool_called"))'
tail -1000 /opt/llm/logs/agent.log | jq 'select(.session_id == "abc123")'
tail -1000 /opt/llm/logs/agent.log | jq -r '.func' | sort | uniq -c | sort -rn
```

#### lnav

```bash
lnav /opt/llm/logs/agent.log /opt/llm/logs/file-mcp.log
# :filter-in error   :filter-out debug   q
```

#### multitail

```bash
multitail /opt/llm/logs/agent.log /opt/llm/logs/file-mcp.log /opt/llm/logs/web-search-mcp.log
```

#### sentry-sdk (optional — requires DSN in environment)

Only use if the project's service environment already defines `SENTRY_DSN` (no such setting is
recorded in this repository; confirm with the user first — otherwise skip this block); read the
DSN from `os.environ["SENTRY_DSN"]` only — never hardcode it into a script.

```python
import os, sentry_sdk
sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], traces_sample_rate=1.0)
with sentry_sdk.push_scope() as scope:
    scope.set_extra("session_id", session_id)
    sentry_sdk.capture_exception(exc)
```

See `rules/coding.md`, section "Prohibited behavior (all tasks)" — remove before committing.

**Completed when**: at least one observability source above has surfaced enough
signal to inform Phase 3's classification, or all applicable sources were checked
and none did.

---

## Phase 3: Failure Classification

| Axis | Classification | Implication |
|---|---|---|
| Reproducibility | **Deterministic** | Reproduce with fixed pytest case; use `ipdb` / `viztracer` |
| Reproducibility | **Intermittent** | Measure the failure rate by looping the command without `--reruns` (Phase 6b; `--reruns` can hide it); check races, asyncio scheduling, TTL edge cases |
| Execution model | **Sync** | `ipdb`, `stackprinter`, `py-spy` (or the fallback) |
| Execution model | **Async** | `PYTHONASYNCIODEBUG=1`, `aiomonitor` (or the fallback), `asyncio.timeout()` |
| Failure domain | **Logic** | Wrong output; `hypothesis` to minimize, `ipdb` to trace |
| Failure domain | **I/O** | File/DB/socket errors; `strace`, `sqlite3` CLI, `httpie` |
| Failure domain | **Network** | MCP/LLM failures; `mitmproxy`, `respx`, service health check |
| Failure domain | **Performance** | Latency/memory; `py-spy`, `viztracer`, `tracemalloc` |

The route is chosen from the Reproducibility and Failure domain axes (`SKILL.md` Phase
routing); the Execution model axis only selects tools inside a phase.

---

## Phase 4: Focused Reproduction

Before the first test run, apply `python-test-and-fix` Core rule "Verify Production Isolation
Before Running Tests": record what the guard in `tests/conftest.py` covers and does not (it
fails a test that opens a SQLite database or a `FileHandler` under `/opt/llm`; it does not guard
ports or other kinds of write), and stop only when no mechanism exists for a production path the
tests you run reach (record `Needs confirmation`). Default to
`-m "not integration and not production_paths_allowed"`: `integration` tests start real
subprocesses and `production_paths_allowed` tests are exempt from the guard. Run either group only
when the failure is in it and the user agrees.

#### pytest (direct — preferred)

```bash
PYTHONPATH=scripts uv run pytest tests/<package>/test_<module>.py -x -q
PYTHONPATH=scripts uv run pytest tests/<package>/test_<module>.py -v
```

Run the one failing test first; run a wider set only to confirm scope.

#### tox (only if available — `uv run tox --version`)

```bash
uv run tox -e tests
uv run tox --recreate -e tests
```

If `tox` does not run under `uv run`, use `uv run pytest` directly (see Tool availability and fallbacks).

#### Running the agent itself (needs confirmation)

Starting `python -m agent` — alone, behind `mitmproxy`, or under `viztracer`/`strace` — is not an
isolated reproduction even when launched from the working tree: the repository configuration
points at `/opt/llm`, so the process would use the production session database, write the
production logs, and start MCP servers on the configured ports (which may already be in use). The
test suite avoids this with a temporary root that holds a copy of `config/` and `schemas/` with
the state paths rewritten, and the environment variables `LLMAGENT_CONFIG_DIR`,
`EVENTBUS_CONFIG_PATH`, `EVENTBUS_SCHEMA_PATH`, and `LLMAGENT_LOG_DIR` (see the header of
`tests/conftest.py`). The repository does not document that setup as a supported way to launch the
agent, so an isolated launch is unverified. Therefore:

1. Prefer reproducing in a test that builds the real component under the test-suite isolation.
2. Launch the agent only when the user confirms, states which of the production side effects above
   are acceptable, and (if they want isolation) provides or approves the redirected configuration;
   record the launch as `Needs confirmation` about isolation.

#### mitmproxy (needs confirmation — it changes how the agent connects)

Only after the user confirms (and only with a confirmed agent launch, above):

```bash
uv run mitmproxy --listen-port 8080
HTTP_PROXY=http://localhost:8080 HTTPS_PROXY=http://localhost:8080 \
  PYTHONPATH=scripts uv run python -m agent
```

Prefer a `respx`-based capture in a test (no proxy, no live traffic) when the hypothesis allows.

#### httpie / curl

Use read-only requests against a live server:

```bash
uv run http GET http://127.0.0.1:<PORT>/health Accept:application/json     # or: curl -s http://127.0.0.1:<PORT>/health
uv run http GET http://127.0.0.1:<PORT>/v1/tools                          # tool list, read-only
```

The agent expects MCP authentication tokens (`MCP_*_AUTH_TOKEN`, see `deploy/start_agent.sh`), so a
server may answer `401`/`403` to these requests. Record such a response as an observation (it can
be the failure itself); never read the token from the environment into the report or add it to a
command line you quote.

`POST /v1/call_tool` (body `{"name": "<tool>", "args": {...}}`; the field is `name`, not
`tool_name`) can execute a tool and change state. MUST NOT send it to a running service without
the user's confirmation; reproduce tool behavior in a test with the real server class under the
test-suite isolation instead. Get `<PORT>` from the server's `http_port` class variable or
`config/agent.toml` `[mcp_servers.*]` `url` (`rules/env.md`), never from memory.

#### sqlite3 CLI (read-only)

Open production databases read-only so an inspection cannot write or checkpoint:

```bash
sqlite3 "file:<path/to/rag|session|workflow|eventbus>.sqlite?mode=ro" -cmd ".tables"   # see rules/env.md SQLite schema
# .schema <table>   PRAGMA integrity_check;   (PRAGMA wal_checkpoint writes: only on a copy)
```

#### Service status

```bash
# For all service names and ports, see rules/env.md; substitute <PORT> for the affected service
curl -s http://127.0.0.1:<PORT>/health
```

#### MCP server health check (from agent REPL)

If the agent REPL is running, use the built-in probes: `/mcp status` checks each configured
server's health, and `/mcp tools` lists the tools they report (`/mcp` alone is the same as
`/mcp status`):

```
/mcp status
/mcp tools
```

---

## Phase 5: Runtime / Trace Inspection

Select the tool(s) using Phase 3's classification table (Execution model / Failure
domain columns) — MUST NOT try tools in the order listed below without that basis. Check each
tool first with the check that matches its kind (Tool availability and fallbacks: `uv run <tool>
--version` for Python-package tools, `command -v` for system tools) and use the fallback table
when the right check fails.

Attaching to a running process (`py-spy --pid`, `strace -p`, `aiomonitor`) needs the user's
confirmation (`SKILL.md` Production Safety). Starting a fresh agent process under a tool is not a
safe alternative: it needs the confirmation and caveats in Phase 4 "Running the agent itself". The
agent entry point is `PYTHONPATH=scripts uv run python -m agent` (`scripts/agent/__main__.py`);
there is no `scripts/agent.py`. Prefer profiling or tracing the suspect component inside a test
under the test-suite isolation (for example `uv run viztracer -m pytest <test path>`, or
`cProfile` around the call).

#### viztracer

```bash
uv run viztracer -m pytest tests/<package>/test_<module>.py -x -q              # preferred: inside a test
# only with a confirmed agent launch (Phase 4):
PYTHONPATH=scripts uv run viztracer --ignore_frozen --include_files scripts/ -m agent
uv run vizviewer result.json
```

#### py-spy

```bash
uv run py-spy top --pid <PID>
uv run py-spy record -o profile.svg --pid <PID> --duration 30
uv run py-spy dump --pid <PID>
```

(Attaching to `<PID>` needs confirmation and ptrace permission; for a test process you started
yourself, `uv run py-spy record -- uv run pytest <test path>` needs no attach.)

#### OpenTelemetry

Tracing in this project is built by `scripts/shared/otel_tracer.py` (`build_tracer`, wired in
`scripts/agent/factory.py`; the SDK is optional and a no-op tracer is used when disabled).
MUST NOT call `trace.set_tracer_provider()` for debugging (the module deliberately avoids the
global provider to prevent cross-test pollution). To see spans, enable the existing tracer
setting in a local run, or in a test construct a tracer with `build_tracer` and a
`ConsoleSpanExporter` on its own provider.

#### strace

```bash
strace -p <PID> -e trace=openat,read,write,connect 2>&1 | head -100
strace -f -e trace=network uv run pytest tests/<package>/test_<module>.py -x -q 2>&1 | grep -v ENOENT
strace -f -e trace=openat uv run pytest tests/<package>/test_<module>.py -x -q 2>&1 | grep '/opt/llm'
```

(`strace` may be absent; use the fallback table. The last command is also a check that a test does
not open production paths. Tracing `python -m agent` itself needs the Phase 4 confirmation.)

#### tracemalloc

```python
import tracemalloc
tracemalloc.start()
snapshot1 = tracemalloc.take_snapshot()
for _ in range(100):
    suspect_function()
snapshot2 = tracemalloc.take_snapshot()
for stat in snapshot2.compare_to(snapshot1, "lineno")[:10]:
    print(stat)
```

#### aiomonitor

```python
import aiomonitor
async def main():
    with aiomonitor.start_monitor(asyncio.get_event_loop()):
        await real_main()
```

```bash
# connect to the monitor's terminal port: use the port aiomonitor prints at startup or the one
# passed to start_monitor (the default differs between aiomonitor versions; do not assume it)
telnet localhost <MONITOR_PORT>   # tasks / task <id> / cancel <id> / exit
```

`aiomonitor` is not used by `scripts/` today; this block instruments a local debugging run only
(removed in Phase 9c). Attaching it to a production process is out of scope.

#### ipdb

```python
import ipdb; ipdb.set_trace()
```
```bash
PYTHONBREAKPOINT=ipdb.set_trace uv run pytest tests/<package>/test_<module>.py -s
```

#### rich + stackprinter

```python
from rich.pretty import pprint; pprint(config_dict)
import stackprinter; stackprinter.set_excepthook(style="plaintext")
```

**Completed when**: the tool(s) selected via Phase 3's table have been run and
produced either a concrete lead for Phase 6's hypothesis table or a confirmed
absence of signal from that tool.

---

## Phase 6: Hypothesis Validation

Build the hypothesis table (6a), then falsify each entry (6b).

### Phase 6a: Build the hypothesis table

Start from the observations of Phases 2-5: each hypothesis names the observation that
suggests it (the "Suggested by" column of the matrix). The list below is a prompt for common
causes, not a fixed checklist; add only rows an observation supports, and drop rows no
observation points to.

| Hypothesis | How to falsify |
|---|---|
| Config path or key mismatch | Print the loaded value via `shared/config_loader.py`'s loader in a test or REPL |
| MCP server down / port mismatch | `curl -s http://127.0.0.1:<PORT>/health` (port from `http_port` / `config/agent.toml`) |
| LLM endpoint unavailable | Look for retry events in `agent.log`; mock with `respx` |
| SQLite extension load failure | `sqlite3 :memory: ".load /opt/llm/sqlite-vec/vec0.so"` |
| Embedding dimension mismatch | `len(blob) == dim * 4` for `floats_to_blob` (`scripts/rag/utils.py`) |
| Memory leak in embedding loop | `tracemalloc` growth test over 100 iterations |
| Asyncio task hang | `asyncio.all_tasks()` dump in a test; `PYTHONASYNCIODEBUG=1`; `aiomonitor` if installed |
| TTL cache stale result | `freezegun`; inspect the cache's own hit/miss counters in the module under test |
| `None` propagation | `assert x is not None` at the boundary + pytest |
| Wire format mismatch | `respx` capture in a test; `mitmproxy` only with confirmation |
| Performance regression | `py-spy record` + `viztracer`, or `cProfile` as the fallback |

**Completed when**: every plausible hypothesis for the classified failure domain (Phase 3)
has a row in the matrix, each with the observation that suggested it, using `SKILL.md`'s
Hypothesis Analysis Matrix format.

### Phase 6b: Falsify each hypothesis with its matching tool

#### hypothesis

See `python-test-and-fix/workflow.md` Step 7 for the property-based invariant
pattern — apply it here to falsify a "does not raise for any input" hypothesis on a
pure function.

#### pytest-asyncio

```python
@pytest.mark.asyncio
async def test_reproduce_deadlock():
    async with asyncio.timeout(5):
        result = await suspect_async_function()
    assert result is not None
```

```bash
PYTHONASYNCIODEBUG=1 uv run pytest tests/<package>/test_<module>.py -v -s
```

#### freezegun

See `python-test-and-fix/workflow.md` Step 5 for the time-freezing pattern — apply it
here to falsify a TTL/cache-staleness hypothesis.

#### respx

See `python-test-and-fix/workflow.md` Step 6 for the httpx-mocking pattern — apply it
here to falsify a wire-format or status-code hypothesis.

#### pytest-rerunfailures + pytest-timeout

```bash
uv run pytest --reruns 10 --reruns-delay 0.2 tests/<package>/test_<module>.py
uv run pytest --timeout=10 tests/<package>/test_<module>.py
```

`--reruns` re-runs a failing test and reports a later pass as a pass, so it can hide
intermittency. To measure a failure rate, loop the same command without `--reruns`
(`for i in $(seq 1 100); do uv run pytest <test path> -x -q || echo "fail $i"; done`).

**Completed when**: every row in 6a's table is marked Validated, Invalidated, or Inconclusive
with an observed result (per `SKILL.md`'s Mandatory Output Template) — not left blank. At least
one Validated row is required before Phase 8; if none is, follow the all-Invalidated rule below
(an `Inconclusive` row does not count as Validated).
**If no row is Validated** (every row Invalidated or Inconclusive): return to Phase 6a and add new hypotheses informed by
what was ruled out — MUST NOT re-test an already-Invalidated row. Per `AGENTS.md` Attempt
Limit, at most 3 Phase 6a/6b round-trips; if no hypothesis validates within that bound,
stop and report `Blocked: no hypothesis validated after 3 rounds — {all ruled-out
hypotheses}` rather than continuing to add rows indefinitely.

---

## Phase 7: Regression Localization

#### git bisect run

`git bisect` checks out other commits, which rewrites the working tree. MUST NOT run it in the
user's working tree when `git status --short` shows any change (parallel sessions leave
unstaged edits), and it needs the user's confirmation otherwise. Run it in a separate worktree
outside the repository instead, and remove only that worktree afterwards:

```bash
git worktree add --detach <scratchpad dir>/bisect-<sha> <bad-sha>
cd <scratchpad dir>/bisect-<sha>
git bisect start
git bisect bad
git bisect good <last-known-good-sha>
git bisect run env PYTHONPATH=scripts uv run pytest tests/<package>/test_<module>.py -x -q -m "not integration and not production_paths_allowed"
git bisect reset
cd - && git worktree remove <scratchpad dir>/bisect-<sha>
```

The test command must exit non-zero only on the target failure (a test that fails for another
reason at an older commit misdirects the search); test isolation (Phase 4) applies inside the
worktree too.

The worktree has no `.venv` (it is git-ignored), so run `uv sync --dev` inside it once before
`git bisect run`. `uv run` re-syncs the environment when `uv.lock` differs between the commits
being tested; that is slow and can fail for reasons unrelated to the bug. If the bisect range
crosses a dependency change, either test with a fixed environment (reuse one `uv sync`ed
environment and skip re-sync with `uv run --frozen`/`--no-sync`) or treat a failure at those
commits as inconclusive rather than "bad" (these `uv` behaviors are not verified here; confirm with
`uv run --help` first).

#### Log time window

```bash
rg -n "^<YYYY-MM-DD> <HH>:" /opt/llm/logs/agent.log | rg " (ERROR|WARNING) "     # text format: fill in the date/hour
lnav /opt/llm/logs/agent.log                                       # only if installed
# :goto <timestamp>  /pattern  n/N  :filter-in error  :zoom-to 1h
```

#### rg — call sites

```bash
rg "<symbol or log string>" scripts/
rg "cache_key|<other symbol>" scripts/        # plain `|`: ripgrep treats `\|` as a literal pipe
```

---

## Phase 8: Minimal Fix

**Fix gate (before any file is changed)**: report to the user the root cause with its
confidence (`skills/DESIGN.md` Confidence levels), the evidence (Validated hypothesis and the
observation behind it), residual uncertainty, and the proposed fix with its scope. Proceed to the
steps below when the user asked for a fix in the original request or approves the proposal; if the
request was investigation only, stop here and deliver the Output format report. A root cause
found but not fixed is recorded as an Issue via `issue-creator`.

- write or adjust a failing test that captures the defect **before** changing code (the
  hypothesis Validated in Phase 6 states what it must assert; for a performance bug, a time or
  allocation bound)
- before the first edit that changes the failing test or its implementation, write
  `python-test-and-fix`'s Test Fix Strategy Record (`python-test-and-fix` Step 12); the fix gate
  above does not replace it
- apply the smallest effective code change (see `AGENTS.md` Global Rule 5 for the
  broader unrelated-refactoring/scope-expansion prohibition)
- explain why the fix addresses the root cause (not just the symptom)

Delegate to composed skills when appropriate:
- test writing and fix validation → `python-test-and-fix` skill (Steps 6, 12)
- if the fix requires a new feature or interface change → `python-implementation` skill
- if the root cause is a structural issue → `python-refactoring` skill

---

## Phase 9: Validation + Cleanup

Apply 9a, 9b, 9c in order.

### Phase 9a: Run tests

After the Phase 4 isolation check still holds (use `-m "not integration and not production_paths_allowed"` unless needed):

```bash
uv run pytest tests/<package>/test_<module>.py -v
uv run pytest -m "not integration and not production_paths_allowed" -q                 # wider suite (see below)
uv run ruff check <changed files>
uv run mypy --no-namespace-packages <changed files>
uv run python tools/run_validation_gates.py           # project gates for the changed files
```

For the wider suite, follow `python-test-and-fix` Step 10: run it in the background with output
in a temporary directory outside the repository, check `pgrep -af "pytest|mutmut"` first so
another session's run is not using the same checkout, and compare `git rev-parse HEAD` and
`git status --short` before and after.

**Completed when**: both pytest runs collected at least one test and passed (a 0-collected,
exit-0 run is not a pass — per `rules/ai-execution.md` Repository Tool Usage #8), and
`ruff check`, `mypy`, and the project gates pass (a gate failure unrelated to this change is
recorded, not fixed here). Lint or type failures the fix caused go to `python-lint-typecheck`.
**On a failure**: return to Phase 8 and revise the fix — MUST NOT re-run this Phase 9a
against an unchanged fix hoping for a different result. Per `AGENTS.md` Attempt Limit,
at most 3 Phase 8/9a cycles for the same failure; if a clean pass is not reached within
that bound, stop and report `Blocked: fix requires more than 3 attempts — {summary}`.

### Phase 9b: Restart services

Run only if production code changed, and only with the user's confirmation: a restart
interrupts the running services and can drop in-flight state. The changed code reaches
`/opt/llm` only through the `deploy` skill, so hand the restart to it:

```bash
# Use the `deploy` skill (skills/deploy/workflow.md Phase 3 Step 3a decision criteria for which
# service(s) restart, Step 3b for the restart commands); do not restart by hand from here.
```

**Completed when**: the user confirmed and every service selected by the decision criteria above
is restarted and healthy, or this sub-step was skipped because no production code changed (or the
user declined; record that as residual uncertainty).

### Phase 9c: Remove debug artifacts

Before committing, remove every debug artifact listed in `rules/coding.md` Prohibited
behavior (`import ipdb`/`ipdb.set_trace()` calls, temporary debug logging or `print` calls,
`viztracer`/`tracemalloc`/`aiomonitor` instrumentation, Sentry DSN). Also delete generated trace
output you wrote (`result.json`, `profile.svg`) if it is inside the repository.

**Completed when**: `git diff <the files this task touched>` shows none of those artifacts remain (a hunk that was already in the Phase 1 baseline is not this task's).

---

## Completion checklist

**This investigation is complete when, and only when**: every item below is true, or the
cycle ended in a `Blocked` state per Phase 6b or Phase 9a's own stop condition.

- observations stated separately from hypotheses
- failure classified (reproducibility / execution model / domain)
- most likely root cause stated with confidence level (see `skills/DESIGN.md` Confidence levels)
- no confirmation-gated action (attach, proxy, state-changing request, bisect in the working tree, restart) ran without the user's confirmation
- every `Inconclusive` hypothesis and every unavailable-tool check is stated as residual uncertainty
- fix applied or proposed with justification
- failing test added or adjusted to cover the defect
- the wider suite (`uv run pytest -m "not integration and not production_paths_allowed"`) and the targeted test pass, and the project gates pass or each unrelated failure is recorded
- services restarted if production code changed and the user confirmed; if the user declined or no production code changed, say so (not an unmet item)
- debug artifacts removed
- every quoted log, request, or output snippet has its secrets redacted
- residual uncertainty stated explicitly

---

## Output format

Populate every item from what earlier Phases recorded — MUST NOT re-derive or re-run a check merely to produce this report.

1. symptom (exact error or behavior)
2. failure classification (reproducibility / sync-async / domain)
3. observations (logs, service status, git diff, rg results, trace output)
4. hypotheses considered and how each was tested
5. most likely root cause (with confidence)
6. fix applied or proposed
7. validation (pytest output, service status after restart)
8. residual uncertainty
9. next steps: any changes are uncommitted, so `git-commit-and-sync` commits them on request; findings recorded instead of fixed (and the Issue filed via `issue-creator`, when the user asked)

---

## Prohibited behavior

The rules stated in `SKILL.md` Core Debugging Rules (evidence, observations vs assumptions,
production safety, secrets) apply throughout. Additionally:

- MUST NOT skip reproduction analysis when feasible
- MUST NOT apply multiple speculative fixes at once
- MUST NOT hide uncertainty

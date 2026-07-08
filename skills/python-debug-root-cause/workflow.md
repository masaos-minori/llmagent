# Debug Root Cause — Detailed Workflow

## Toolchain

| Tool | Phase | Role |
|---|---|---|
| `structlog` + `jq` | Initial Observability | Structured log emission and filtering |
| `lnav` | Initial Observability | Interactive log navigator |
| `multitail` | Initial Observability | Follow multiple log files simultaneously |
| `sentry-sdk` | Initial Observability | Exception capture with context |
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

---

## Phase 1: Problem Framing

Before any tool use, identify:

- observed behavior (exact error message or symptom)
- expected behavior
- affected input or environment
- whether the issue is deterministic, intermittent, or unknown

State unknowns explicitly. Do not proceed to tools until the failure is framed.

---

## Phase 2: Initial Observability

#### structlog + jq

```bash
tail -200 /opt/llm/logs/agent.log | jq 'select(.level == "error")'
tail -500 /opt/llm/logs/agent.log | jq 'select(.event | contains("tool_called"))'
tail -1000 /opt/llm/logs/agent.log | jq 'select(.session_id == "abc123")'
tail -1000 /opt/llm/logs/agent.log | jq -r '.event' | sort | uniq -c | sort -rn
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

Only use if `SENTRY_DSN` is configured in `/etc/conf.d/llama-agent`.
Do not add a hardcoded DSN to any script.

```python
import os, sentry_sdk
sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], traces_sample_rate=1.0)
with sentry_sdk.push_scope() as scope:
    scope.set_extra("session_id", session_id)
    sentry_sdk.capture_exception(exc)
```

Remove before committing. DSN must come from environment only.

---

## Phase 3: Failure Classification

| Axis | Classification | Implication |
|---|---|---|
| Reproducibility | **Deterministic** | Reproduce with fixed pytest case; use `ipdb` / `viztracer` |
| Reproducibility | **Intermittent** | Run with `--reruns 10`; check races, asyncio scheduling, TTL edge cases |
| Execution model | **Sync** | `ipdb`, `stackprinter`, `py-spy` |
| Execution model | **Async** | `PYTHONASYNCIODEBUG=1`, `aiomonitor`, `asyncio.timeout()` |
| Failure domain | **Logic** | Wrong output; `hypothesis` to minimize, `ipdb` to trace |
| Failure domain | **I/O** | File/DB/socket errors; `strace`, `sqlite3` CLI, `httpie` |
| Failure domain | **Network** | MCP/LLM failures; `mitmproxy`, `respx`, service health check |
| Failure domain | **Performance** | Latency/memory; `py-spy`, `viztracer`, `tracemalloc` |

---

## Phase 4: Focused Reproduction

#### pytest (direct — preferred)

```bash
PYTHONPATH=scripts pytest tests/ -x -q
PYTHONPATH=scripts pytest tests/test_<module>.py -v
```

#### tox (if installed and tox.ini is configured)

```bash
tox -e tests
tox --recreate -e tests
```

#### mitmproxy

```bash
mitmproxy --listen-port 8080
HTTP_PROXY=http://localhost:8080 HTTPS_PROXY=http://localhost:8080 \
  python3 /opt/llm/scripts/agent.py
```

#### httpie

```bash
http POST http://localhost:8005/v1/call_tool \
  tool_name=read_file args:='{"path": "/opt/llm/config/agent.toml"}'
http GET http://localhost:8004/health Accept:application/json
```

#### sqlite3 CLI

```bash
sqlite3 /opt/llm/db/llm.db
# .tables  .schema chunks  PRAGMA integrity_check;  PRAGMA wal_checkpoint;
```

#### Service status

```bash
# For all service names and ports, see rules/env.md
curl -s http://127.0.0.1:8004/health   # web-search-mcp
curl -s http://127.0.0.1:8005/health   # file-read-mcp
curl -s http://127.0.0.1:8006/health   # github-mcp
curl -s http://127.0.0.1:8007/health   # file-write-mcp
curl -s http://127.0.0.1:8008/health   # file-delete-mcp
curl -s http://127.0.0.1:8009/health   # shell-mcp
curl -s http://127.0.0.1:8010/health   # rag-pipeline-mcp
curl -s http://127.0.0.1:8012/health   # cicd-mcp
curl -s http://127.0.0.1:8013/health   # mdq-mcp
curl -s http://127.0.0.1:8014/health   # git-mcp
curl -s http://127.0.0.1:8003/health   # embed-llm
curl -s http://127.0.0.1:8001/health   # agent-llm
```

#### MCP server health check (from agent REPL)

If the agent REPL is running, use the built-in probe command:

```
/mcp
```

This probes `/health` and `/v1/tools` for all configured HTTP-transport servers
and displays connectivity status, tool count, and any error responses.

---

## Phase 5: Runtime / Trace Inspection

#### viztracer

```bash
viztracer python3 scripts/agent.py
viztracer --ignore_frozen --include_files scripts/ python3 scripts/agent.py
vizviewer result.json
```

#### py-spy

```bash
py-spy top --pid <PID>
py-spy record -o profile.svg --pid <PID> --duration 30
py-spy dump --pid <PID>
```

#### OpenTelemetry

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
```

#### strace

```bash
strace -p <PID> -e trace=openat,read,write,connect 2>&1 | head -100
strace -e trace=network python3 scripts/agent.py 2>&1 | grep -v ENOENT
strace -e trace=openat python3 scripts/agent.py 2>&1 | grep '/opt/llm'
```

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
telnet localhost 20101   # tasks / task <id> / cancel <id> / exit
```

#### ipdb

```python
import ipdb; ipdb.set_trace()
```
```bash
PYTHONBREAKPOINT=ipdb.set_trace pytest tests/test_<module>.py -s
```

#### rich + stackprinter

```python
from rich.pretty import pprint; pprint(config_dict)
import stackprinter; stackprinter.set_excepthook(style="plaintext")
```

---

## Phase 6: Hypothesis Validation

| Hypothesis | How to falsify |
|---|---|
| ConfigLoader path mismatch | Print `ConfigLoader().load(...)` output |
| MCP server down / port mismatch | `curl -s http://127.0.0.1:<PORT>/health` |
| LLM endpoint unavailable | Check `agent.log` for retry events; mock with `respx` |
| SQLite extension load failure | `sqlite3 :memory: ".load /opt/llm/sqlite-vec/vec0.so"` |
| Embedding dimension mismatch | `len(blob) == dim * 4` in `rag_utils.py` |
| Memory leak in embedding loop | `tracemalloc` growth test over 100 iterations |
| Asyncio task hang | `aiomonitor` task list; `PYTHONASYNCIODEBUG=1` |
| TTL cache stale result | `freezegun`; check `stat_cache_hits` |
| `None` propagation | `assert x is not None` at boundary + pytest |
| Wire format mismatch | `mitmproxy` to capture actual request/response |
| Performance regression | `py-spy record` + `viztracer` |

#### hypothesis

```python
from hypothesis import given, settings
from hypothesis import strategies as st

@given(st.text())
@settings(max_examples=500)
def test_normalize_does_not_raise(text):
    from rag_utils import normalize_unicode
    normalize_unicode(text)
```

#### pytest-asyncio

```python
@pytest.mark.asyncio
async def test_reproduce_deadlock():
    async with asyncio.timeout(5):
        result = await suspect_async_function()
    assert result is not None
```

```bash
PYTHONASYNCIODEBUG=1 pytest tests/test_agent_repl.py -v -s
```

#### freezegun

```python
from freezegun import freeze_time

def test_cache_expiry():
    with freeze_time("2024-01-01 00:00:00") as frozen:
        cache = SemanticCache(ttl=3600)
        cache.put("q", "result")
        frozen.tick(delta=3601)
        assert cache.get("q") is None
```

#### respx

```python
@respx.mock
def test_reproduce_500():
    respx.post("http://localhost:8002/v1/chat/completions").mock(
        return_value=httpx.Response(500, json={"error": "internal"})
    )
```

#### pytest-rerunfailures + pytest-timeout

```bash
pytest --reruns 10 --reruns-delay 0.2 tests/test_<module>.py
pytest --timeout=10 tests/
```

---

## Phase 7: Regression Localization

#### git bisect run

```bash
git bisect start
git bisect bad
git bisect good <last-known-good-sha>
git bisect run pytest tests/test_<module>.py -x -q
git bisect reset
```

#### lnav — time window

```bash
lnav /opt/llm/logs/agent.log
# :goto <timestamp>  /pattern  n/N  :filter-in error  :zoom-to 1h
```

#### rg — call sites

```bash
rg "<symbol or log string>" scripts/
rg "cache_key\|stat_cache_hits"
```

---

## Phase 8: Minimal Fix

- write or adjust a failing test that captures the defect **before** changing code
- apply the smallest effective code change
- explain why the fix addresses the root cause (not just the symptom)
- do not refactor, clean up, or expand scope in the same change

Delegate to composed skills when appropriate:
- test writing and fix validation → `python-test-and-fix` skill (Steps 6, 12)
- if the fix requires a new feature or interface change → `python-implementation` skill
- if the root cause is a structural issue → `python-refactoring` skill

---

## Phase 9: Validation + Cleanup

```bash
pytest tests/test_<module>.py -v
pytest -v
ruff check scripts/
# Restart MCP server via agent REPL or direct process management if production code changed
```

Before committing:
- remove `import ipdb` and all `ipdb.set_trace()` calls
- remove temporary `structlog` debug calls
- remove `viztracer` / `tracemalloc` instrumentation
- confirm Sentry DSN is not in any committed file

---

## Completion checklist

- observations stated separately from hypotheses
- failure classified (reproducibility / execution model / domain)
- most likely root cause stated with confidence level
- fix applied or proposed with justification
- failing test added or adjusted to cover the defect
- full pytest suite passes
- services restarted if production code changed
- debug artifacts removed
- residual uncertainty stated explicitly

---

## Output format

1. symptom (exact error or behavior)
2. failure classification (reproducibility / sync-async / domain)
3. observations (logs, service status, git diff, rg results, trace output)
4. hypotheses considered and how each was tested
5. most likely root cause (with confidence)
6. fix applied or proposed
7. validation (pytest output, service status after restart)
8. residual uncertainty

---

## Prohibited behavior

- do not claim certainty without evidence
- do not skip reproduction analysis when feasible
- do not apply multiple speculative fixes at once
- do not mix observations and assumptions without labeling them
- do not hide uncertainty

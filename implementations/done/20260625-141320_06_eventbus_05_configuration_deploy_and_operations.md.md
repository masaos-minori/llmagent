# Implementation: Add tuning guide to configuration and operations doc

Source plan: `plans/20260625-140621_plan.md` (req #20)

## Goal

Add a `## Tuning Guide` section to `docs/06_eventbus_05_configuration_deploy_and_operations.md` that explains how `poll_interval_ms`, `offset_checkpoint_interval`, and the asyncio threadpool interact under the new offload-based runtime model, with recommended values for three workload profiles.

## Scope

- Append a new `## Tuning Guide` section to the existing document
- Cover three parameters: `poll_interval_ms`, `offset_checkpoint_interval`, threadpool sizing
- Provide a three-row recommendation table (low / medium / high fan-out)
- No changes to `config.py` or application code
- Prerequisite: req #14, #15, #16 implemented (offload model must be real before documenting it)

## Assumptions

1. `asyncio.to_thread` uses Python's default `ThreadPoolExecutor` with `max_workers=None` (≈ CPU cores × 5, minimum 5)
2. Each DB poll in `/subscribe` occupies one thread for the duration of the query
3. Offset file writes are short (< 1 ms) and do not materially affect threadpool saturation
4. The existing Config fields table remains unchanged; the tuning guide is additive

## Implementation

### Target file

`docs/06_eventbus_05_configuration_deploy_and_operations.md`

### Procedure

1. Append `## Tuning Guide` section after the existing `## Validation status` section
2. Add `### poll_interval_ms` sub-section with trade-off explanation
3. Add `### offset_checkpoint_interval` sub-section with trade-off explanation
4. Add `### Threadpool sizing` sub-section with default and override instructions
5. Add `### Recommended starting values` table

### Method

Additive edit — insert new section at end of file. Do not modify any existing content.

### Details

Content to append:

```markdown
## Tuning Guide

### poll_interval_ms

Controls how often `/subscribe` polls the database for new events.

- **Lower values** (100–300 ms): lower SSE delivery latency; higher DB read pressure (proportional to active subscriber count)
- **Higher values** (500–2000 ms): lower DB pressure; higher delivery latency
- Default (500 ms) is suitable for up to ~10 concurrent subscribers

### offset_checkpoint_interval

Controls how often `/subscribe` writes the consumer offset to disk (every N delivered events).

- **Lower values** (1–10): fewer events re-delivered after restart; higher file I/O pressure
- **Higher values** (50–100): lower file I/O; more re-delivery on unexpected disconnect
- Default (10) is suitable for most workloads

### Threadpool sizing

`asyncio.to_thread()` uses Python's default `ThreadPoolExecutor` (`max_workers=None`, approximately `min(32, cpu_count + 4)` on Python 3.13).

Each concurrent DB poll (one per active subscriber) occupies one thread slot during query execution. If active subscribers exceed the default pool size, polls queue behind each other — increasing effective latency.

To override the default pool size:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
loop = asyncio.get_event_loop()
loop.set_default_executor(ThreadPoolExecutor(max_workers=64))
```

This is recommended when running more than 20 concurrent subscribers.

### Recommended starting values

| Workload | `poll_interval_ms` | `offset_checkpoint_interval` | Notes |
|---|---|---|---|
| Low fan-out (< 5 consumers) | 500 (default) | 10 (default) | No tuning required |
| Medium fan-out (5–20 consumers) | 300 | 50 | Reduces DB polling pressure |
| High fan-out (> 20 consumers) | 200 | 100 | Consider increasing threadpool max_workers |

> **Note**: These are starting values. Tune based on observed DB query latency (see `db_latency_ms` in `/health`) and SSE delivery lag in your environment.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Section present | `grep "## Tuning Guide" docs/06_eventbus_05_configuration_deploy_and_operations.md` | 1 match |
| Table present | `grep "Low fan-out" docs/06_eventbus_05_configuration_deploy_and_operations.md` | 1 match |
| No existing content broken | `diff` with original | Only new lines appended |
| Markdown lint | `markdownlint docs/06_eventbus_05_configuration_deploy_and_operations.md` | 0 errors (if installed) |

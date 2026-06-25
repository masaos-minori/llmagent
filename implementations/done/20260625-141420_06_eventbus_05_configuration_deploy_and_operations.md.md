# Implementation: Add runtime metrics and alerting guidance

Source plan: `plans/20260625-140651_plan.md` (req #23)

## Goal

Append a `## Runtime Metrics` section to `docs/06_eventbus_05_configuration_deploy_and_operations.md` that defines recommended metrics, alert thresholds, and guidance for distinguishing load saturation from DB unavailability.

## Scope

- Append `## Runtime Metrics` section after the existing content (after the Tuning Guide added by req #20)
- Cover four metric categories: publish latency, SSE delivery lag, DLQ loop duration, threadpool saturation proxy
- Include saturation-vs-unavailability disambiguation table
- Include alerting guidance (critical / warning / info tiers)
- No code changes; documentation only

## Assumptions

1. req #19 (/health extension) is implemented; `dlq_last_run_age_s` field is available from `/health`
2. req #20 (tuning guide) has already been appended; this section follows it
3. No specific metrics platform (Prometheus, Datadog, etc.) is mandated; guidance is platform-agnostic
4. The implementation is assumed to run at a single host; distributed metrics aggregation is out of scope

## Implementation

### Target file

`docs/06_eventbus_05_configuration_deploy_and_operations.md`

### Procedure

1. Append `## Runtime Metrics` section at the end of the file (after the Tuning Guide section)

### Method

Additive edit — append new section. No existing content is modified.

### Details

Content to append:

```markdown
## Runtime Metrics

### Recommended metrics

Collect the following metrics to detect performance degradation before it becomes a visible outage.

| Metric | How to collect | Recommended alert threshold |
|---|---|---|
| Publish P95 latency | Measure POST `/publish` round-trip time at the client | > 200 ms (warning) |
| Publish P99 latency | Same | > 500 ms (critical) |
| SSE delivery lag | `published_at` of last received event vs. current time | > 2 s sustained for > 2 min (warning) |
| DLQ loop delay | `dlq_last_run_age_s` from GET `/health` | > 120 s (info) |
| Threadpool saturation (proxy) | High publish latency AND high CPU (> 80%) simultaneously | P95 > 500 ms with CPU > 80% (warning) |
| Event backlog rate | Rate of increase of `event_count` from GET `/health` | Sustained increase with no active subscribers (warning) |

> `dlq_last_run_age_s` is `null` for the first 60 seconds after startup (DLQ loop has not yet completed one cycle). Do not alert during this window.

### Distinguishing load saturation from DB unavailability

| Symptom | Load saturation | DB unavailable |
|---|---|---|
| `/health` → `db` | `ok` | `unavailable` |
| `/health` → `status` | `degraded` (latency-based) | `unavailable` |
| `/health` → `db_latency_ms` | Elevated (> 100 ms) | N/A (error) |
| POST `/publish` response | Slow (> 200 ms) but 200 | Timeout or 500 |
| GET `/subscribe` SSE | Delayed delivery, stream continues | Stream stops |

### Alerting guidance

| Severity | Condition | Action |
|---|---|---|
| Critical | `/health` → `status = "unavailable"` | Page on-call immediately |
| Warning | Publish P95 > 200 ms sustained for > 5 min | Investigate threadpool saturation or DB disk I/O |
| Warning | SSE delivery lag > 2 s sustained for > 2 min | Check poll_interval_ms and subscriber count |
| Info | `dlq_last_run_age_s` > 120 s | Review DLQ loop logs for exceptions |

### Collecting metrics without a dedicated metrics system

If no dedicated metrics collector is available, use the following approaches:

- **`/health` polling**: poll `GET /health` every 30 s and log `db_latency_ms` and `dlq_last_run_age_s`
- **Access log parsing**: extract publish latency from uvicorn access logs (response time column)
- **Consumer-side lag**: compute `published_at` delta in the subscribing application
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Section present | `grep "## Runtime Metrics" docs/06_eventbus_05_configuration_deploy_and_operations.md` | 1 match |
| Alert table present | `grep "Publish P95" docs/06_eventbus_05_configuration_deploy_and_operations.md` | 1 match |
| Disambiguation table present | `grep "Load saturation" docs/06_eventbus_05_configuration_deploy_and_operations.md` | 1 match |
| No existing content broken | `diff` with previous state | Only new lines appended |
| Markdown lint | `markdownlint docs/06_eventbus_05_configuration_deploy_and_operations.md` | 0 errors (if installed) |

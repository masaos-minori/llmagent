## Goal
- Pin the health-side dedup metrics block: `dedup_health_details()` (new) returns an empty mapping when no store is wired and a `dedup` block when one is, while `make_health_response` keeps the payload it publishes today (`REQ-004` health payload reports dedup metrics and status).

## Scope
**Release unit**: health exposure
- One new test class for the `details` metrics block and its degradation path; rows 05, 08, 09 own the module changes.

## Assumptions
- `collect_dedup_metrics()` (new) defines the metric field names, including `legal_hold_states` (new) and `held_past_retention` (new); a per-metric status block appears only when that metric's threshold key is set.
- The threshold keys are `max_dedup_rows` (new), `max_dedup_growth_per_hour` (new), `max_dedup_wal_mb` (new), all optional and unset by default (row 08).
- `dedup_health_details()` (new) reads the `mcp_servers.dispatch` globals and never raises; the metrics module itself is tested by `tests/shared/test_mcp_dedup_metrics.py` (new).

## Design decisions
- `TestDedupHealthDetails` (new) follows the file's style: a `DEDUP_METRIC_KEYS` (new) constant mirroring `POSTURE_KEYS`, and the existing `_body()` helper for decoding the payload.
- Prefer `monkeypatch.setattr` on the `dispatch` store and config globals over `configure_dedup()`, so process-wide bootstrap state is restored automatically.

## Alternatives considered
- Asserting the whole `details` dict by equality: rejected, it pins values the row 05 module may extend; the key-set form mirrors how the security block is pinned.

## Implementation
### Target file
`tests/mcp_servers/test_health_response.py`
### Procedure
- Keep every existing assertion unchanged: `set(body) == BASE_KEYS`, the `details == {}` default, the two-argument call form, and all of `TestPosturePublication`.
- Add `TestDedupHealthDetails` (new): the degradation case, the metrics-block case, the payload case.
### Method
- Degradation: with the `dispatch` store and config globals at `None` (their default), `dedup_health_details()` (new) returns `{}` and raises nothing, and a response built with no details keeps `details == {}`.
- Metrics: open a tmp_path store the way `tests/shared/test_mcp_dedup.py` does, seed one row per state, build the matching `DedupStoreConfig` with every threshold unset, patch it into `dispatch`, then read the block.
### Details
- Assert `set(body["details"]["dedup"]) == DEDUP_METRIC_KEYS` (new) with no status block while thresholds are unset, and the matching status block when one threshold key is set to a value the seeded store breaches.
- Payload: `make_health_response(deps, {"service": "web-search-mcp", **block})` keeps `BASE_KEYS` and the `service` key, carries the block under `body["details"]["dedup"]`, and leaks no config path or token, following `test_the_published_block_carries_no_config_path_or_token`.

## Compatibility considerations
- `BASE_KEYS` stays unchanged and the new content sits only inside `details`, so this file's and the per-server key-set assertions keep passing; no store state or schema change is involved.

## Security considerations
- N/A: tests-only; the only security-relevant assertion is that the block carries no path or token.

## Rollback considerations
- N/A: revert the commit (tests-only row, single commit).

## Validation plan
- `uv run pytest tests/mcp_servers/test_health_response.py` — pass, with the pre-existing classes unchanged.
- The class lands with or before the row 09 change; then the full sequence in `rules/toolchain.md`.

## Completion criteria
- An un-wired dispatcher yields an empty mapping and an unchanged `details` default.
- A wired store yields a `dedup` block whose keys match the documented metric fields, with status blocks only for a set and breached threshold, and `BASE_KEYS` plus every pre-existing assertion still passes.

## Out of Scope
- Changing `make_health_response`, the metrics module, the `[dedup]` keys, or the 10 handlers (rows 05, 08, 09, 10 to 17).
- Threshold values (`U-1`) and the endpoint tests that assert `details` by equality (rows 22 to 24).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the degradation-path and metrics-block tests | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` (health payload reports dedup metrics and status); AC-4
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `tests/mcp_servers/test_health_response.py`

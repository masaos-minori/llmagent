## Goal
Document the new `details.dedup` block in the GET /health payload of the 10 servers wired to a `[dedup]` table: its fields, read-only semantics, and status-only behaviour (REQ-004 read-only metrics published through the existing health `details` block).

## Scope
**Release unit**: health exposure
Additions to the two health sections of one page; the startup-mode, authentication, and truncation content stays as it is.

## Assumptions
- Owner decision `D-6`: the per-metric `status` (`ok`/`warning`/`fail`) is computed and published only — it never changes store or dispatcher behaviour, and only for configured thresholds.
- Threshold and hold keys are optional and operator-supplied (`U-1`); no numeric value is written into the page.
- The exposure reuses the existing `details` mechanism; no new endpoint or status service is documented (Plan out-of-scope rule).

## Design decisions
- Document `dedup_health_details()` (new) as the single source of the `details.dedup` block, so the page describes one helper, not 10 per-server variants.
- State the payload-key contract as unchanged: the existing top-level keys (`status`, `ready`, `liveness`, `restart_recommended`, `operator_action_required`, `dependencies`, `details`, optional `security`) are not replaced.

## Alternatives considered
N/A: docs-only change.

## Implementation
### Target file
- `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
### Procedure
- Extend the `**details**` paragraph in `### Standard /health Response Semantics`: the 10 servers with a `[dedup]` table may carry the single key `dedup`, computed read-only (SELECT/PRAGMA reads only) via `dedup_health_details()` (new).
- Add a `details.dedup` field table: per-status row counts, `pending_overdue`, `growth_rows_per_hour`, `wal_size_bytes`, `lock_wait_ms`, `legal_hold_states`, `held_past_retention`, per-threshold blocks `rows`/`growth`/`wal` with `status` `ok`/`warning`/`fail`.
- Status rule: a per-metric status is reported only when its threshold key (`max_dedup_rows`, `max_dedup_growth_per_hour`, `max_dedup_wal_mb`) is configured; absent keys report no status; `legal_hold_states` and `held_past_retention` report held rows as held, not as retained-at-large.
- Degradation rule: when the dedup store is unavailable or the open is refused, `details` gains no `dedup` key and the existing degradation path is unchanged.
- In `## Server-Specific Health Response Fields`, add one row applying to all 10 wired servers pointing at `details.dedup`, cross-linking the retention matrix in [db_03_07](../41_db/db_03_07_mcp-dedup-and-execution-snapshot.md) and the key inventory in [mcp_06_01](mcp_06_01_configuration-file-inventory.md); existing per-server entries (for example mdq's row counts, web-search's `metrics`) stay.
### Method
- Paragraph and table additions in the existing section style; no new section; `dependencies`, HTTP status codes, and the `security` block text are untouched.
### Details
- The block never alters `status`, `ready`, or `operator_action_required`: a `fail` metric status is information reported in `details` only.

## Compatibility considerations
N/A: docs-only change.

## Security considerations
N/A: docs-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain mcp` (the Plan row names `tools/check_docs_consistency.py`); per `rules/tool-gates.md`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` run for any `docs/*.md` edit.

## Completion criteria
The page describes the `details.dedup` field set exactly as implemented, states the status-only and store-unavailable rules, keeps every existing payload contract claim intact, and its cross-links resolve.

## Out of Scope
Per-server handler wiring and the metrics module itself (other Plan rows); threshold values (`U-1`); any new endpoint or automatic action.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-212420 | 20261123-212449 | adversarial verification: anchors exist in current doc; procedure-length finding (78 lines) kept as full form because this row carries the details.dedup field table changed: docs/22_mcp/mcp_02_02_startup-modes-and-health.md (details.dedup paragraph + field table + status/degradation rules + Server-Specific row) |
| 2 | Run the documentation checkers named in the Validation plan | Completed | — | 20261123-212449 | quality/structure/content_policy pass; consistency --domain mcp: 1 warning for dedup_health_details() (new), allowed red state attributed to sibling seq 09; documentation-only case replaced test runs |

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
- **Requirement ID**: `REQ-004` (read-only metrics published through the existing health `details` block)
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
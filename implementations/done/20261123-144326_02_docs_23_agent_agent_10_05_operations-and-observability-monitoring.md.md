## Goal
Document the operator monitoring criteria for the dedup store's capacity state: a new criteria row describing the `details.dedup` metrics block and its per-metric status (REQ-004 health payload reports metrics and status), and record that the numeric thresholds extend the existing criteria rows at the warning level (REQ-005, no automatic action).

## Scope
**Release unit**: health exposure
Criteria-table additions in one page; the startup/troubleshooting sections and the existing `Dedup Protection Degraded (MCP dedup store)` log-conditions row stay as they are.

## Assumptions
- Owner decision `U-3`: the sweep stays terminal-row-only, so the criteria row describes unresolved states as growth to observe, not growth the sweep removes.
- Owner decision `D-6`: threshold status is reported only — `ok`/`warning`/`fail` never gates store or dispatcher behaviour; values are operator-supplied (`U-1`).
- Classification states (`reconciliation_required`, `outcome_unknown`, `replay_unavailable`) belong to mcpdl006 and are deferred (`U-6`); no alert-delivery claim is added (`U-7`).

## Design decisions
- The new row is a status-monitoring row, kept distinct from the `Dedup Protection Degraded` log-conditions row: that row stays untouched and gains numeric criteria only when the Plan's monitoring phase wires the thresholds.
- The row mirrors the implemented payload exactly: fields and key names as published through `collect_dedup_metrics()` (new) via `dedup_health_details()` (new), never a paraphrase.

## Alternatives considered
N/A: docs-only change.

## Implementation
### Target file
- `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`
### Procedure
- In the `## Monitoring Partial Completions and Truncation` table, add a new row `Dedup Store Capacity Status (MCP dedup store)` directly after the `Dedup Protection Degraded (MCP dedup store)` row.
- Detection Method cell: each wired server's `GET /health` `details.dedup` block reports per-metric `status` (`ok`/`warning`/`fail`) for row count, row growth, and WAL size against the optional `[dedup]` threshold keys `max_dedup_rows`, `max_dedup_growth_per_hour`, `max_dedup_wal_mb`; absent keys report no status and an unavailable store reports no `dedup` key; `legal_hold_states` and `held_past_retention` report held-state rows past the retention as held rows.
- Action cell: check the configured thresholds and `retention_days`; terminal rows past the retention are swept at most once per process on first use, unresolved states are not swept — their lifecycle belongs to `reconcile_execution()` and the matrix in [db_03_07](../41_db/db_03_07_mcp-dedup-and-execution-snapshot.md).
- Add a short paragraph under the table: the existing `Dedup Protection Degraded` row stays as a list of log conditions, and its numeric criteria are the thresholds this Plan's monitoring phase wires; no automatic action or alert is introduced.
### Method
- Table-row and paragraph additions only; match the table's existing cell and relative-link style; no new section and no `## Needs Confirmation` subsection (open decisions live in the Plan's Unknowns).
### Details
- No numeric value is written into the page; the row names the keys and the status vocabulary, per `U-1`.

## Compatibility considerations
N/A: docs-only change.

## Security considerations
N/A: docs-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain agent` (the Plan row names `tools/check_docs_consistency.py`); per `rules/tool-gates.md`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` run for any `docs/*.md` edit.

## Completion criteria
The criteria table carries exactly one new capacity row whose field and key names match the implemented `details.dedup` payload, the degraded row is unchanged, no numeric threshold value appears, and the db_03_07 cross-link resolves.

## Out of Scope
Threshold values (`U-1`); alert delivery (`U-7`); automatic restart/escalation/purge action; the classification-state criteria rows (mcpdl006, `U-6`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-212240 | 20261123-212329 | 3b correction applied: sweep trigger corrected to once-per-process on first use; procedure-length finding (77 lines) kept as full form because this row carries criteria-table cell text; no test step applies (documentation-only case, replaced by tool-gates checkers) changed: docs/23_agent/agent_10_05_operations-and-observability-monitoring.md (capacity criteria row + status-only paragraph) |
| 2 | Run the documentation checkers named in the Validation plan | Completed | — | 20261123-212329 | checkers pass; consistency warning in agent_14 is pre-existing, unrelated to this cycle; documentation-only case replaced tool-gates checkers for tests |

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
- **Requirement ID**: `REQ-004` (health payload reports metrics and status), `REQ-005` (warning-level monitoring criteria, no automatic action)
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`
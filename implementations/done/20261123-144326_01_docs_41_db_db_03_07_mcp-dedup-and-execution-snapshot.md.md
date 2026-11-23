## Goal
Add a Retention and Capacity Monitoring section to the dedup-store page: the sweep eligibility matrix per stored state with the configuration-based legal-hold boundary (REQ-001 matrix per state; REQ-002 sweep stays terminal-only; REQ-003 hold as a `[dedup]` config entry), plus the read-only capacity-metrics fields with status-only semantics (REQ-008).

## Scope
**Release unit**: matrix and its test
One new section in an existing page; the existing state table, attempt-history note, and Replay Decision Table stay as they are.

## Assumptions
- Owner decision `U-3`: retention stays terminal-row-only; `U-2`/`D-2`: legal hold is configuration-based (`legal_hold_states`), no schema or fingerprint change.
- Owner decision `D-2`/`U-5`: the age-based `call_attempt_history` delete is intentional and recorded as such.
- Classification states (`reconciliation_required`, `outcome_unknown`, `replay_unavailable`) belong to mcpdl006; their matrix rows are state-conditional and deferred (`U-6`); threshold values are operator-supplied (`U-1`).

## Design decisions
- State the sweep from verified behaviour — `purge_expired` (`scripts/shared/mcp_dedup_ledger.py`, line 551) and `reconcile_execution` (line 395) — not from invented SQL.
- Document the capacity fields as the payload contract of `collect_dedup_metrics()` (new) with status-only semantics (owner decision `D-6`): a computed `status` never changes store or dispatcher behaviour.

## Alternatives considered
N/A: docs-only change.

## Implementation
### Target file
- `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
### Procedure
- Add a `## Retention and Capacity Monitoring` section after the Replay Decision Table side notes, before `## Adoption Path`.
- Eligibility matrix per stored state: `completed`, `failed`, `interrupted` swept at most once per process on first use (`_purge_once` in `scripts/mcp_servers/dispatch.py`) when `updated_epoch` is past `retention_days`; `pending` never swept — its lifecycle is `reconcile_execution`, which moves a stale-lease, attempts-remaining row to `interrupted` (attempts exhausted -> refusal, outcome unknown).
- `call_attempt_history` row: deleted by `recorded_epoch` past the same cutoff regardless of the parent state; recorded as intentional (`U-5`).
- Legal-hold column: hold is configuration-based — `legal_hold_states` (new) lists stored state names excluded from the sweep; `purge_expired` gains the `AND status NOT IN (...)` exclusion reading the store's own config; held rows are counted as held, not as retained-at-large; no DDL, no fingerprint change (`U-2`).
- Deferred rows: the three classification states appear as state-conditional rows resolved by mcpdl006 (`U-6`), not present-tense rules.
- Capacity-fields block: per-status row counts, `pending_overdue`, `growth_rows_per_hour`, `wal_size_bytes`, `lock_wait_ms`, `legal_hold_states`, `held_past_retention`, per-threshold blocks `rows`/`growth`/`wal` with `status` `ok`/`warning`/`fail`; cross-link [agent_10_05](../23_agent/agent_10_05_operations-and-observability-monitoring.md), [mcp_02_02](../22_mcp/mcp_02_02_startup-modes-and-health.md), [mcp_06_01](../22_mcp/mcp_06_01_configuration-file-inventory.md) in the file's existing relative-link style.
### Method
- Plain Markdown edit; matrix as a pipe table in the page's existing shape; cite existing `purge_expired`/`reconcile_execution` behaviour, no invented SQL or new state names.
### Details
- The section elaborates the existing "Retention sweep" bullet and stays consistent with the lease-based state machine above it.

## Compatibility considerations
N/A: docs-only change.

## Security considerations
N/A: docs-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` (the Plan row names `tools/check_docs_consistency.py`); per `rules/tool-gates.md`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` run for any `docs/*.md` edit.

## Completion criteria
The matrix names only states the schema `status` CHECK allows, matches `purge_expired` behaviour, records the history rule and the configuration-based hold as designed, defers the classification rows, and its fields match the payload `collect_dedup_metrics()` (new) publishes.

## Out of Scope
Classification-state matrix behaviour (mcpdl006, `U-6`); threshold values (`U-1`); the state-machine definition itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-211956 | 20261123-212147 | 3b correction applied: line citations re-verified (purge_expired 551, reconcile_execution 395); sweep trigger corrected to once-per-process on first use; procedure-length finding (79 lines) kept as full form because this row carries the eligibility matrix changed: docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md (matrix section + corrected attempt-history and retention-sweep bullets) |
| 2 | Run the documentation checkers named in the Validation plan | Completed | — | 20261123-212147 | check_docs_quality/structure/content_policy pass; check_docs_consistency --domain db: 1 warning for collect_dedup_metrics() (new) - allowed red state attributed to sibling seq 05, re-run after it lands |

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
- **Requirement ID**: `REQ-001` (retention matrix per state), `REQ-002` (sweep stays terminal-only; unresolved states stay outside), `REQ-003` (legal hold as a configuration entry), `REQ-008` (capacity read is read-only)
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
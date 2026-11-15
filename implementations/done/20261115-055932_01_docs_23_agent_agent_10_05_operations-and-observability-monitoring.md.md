## Goal

Document the existing dedup-store degradation signal (dispatcher `logger.warning()` calls plus the `dedup_state=store_error` marker) as an operational detection method in the monitoring document, so operators can recognize degraded dedup protection without re-documenting behavior already frozen by `adrrev008`/`adrrev011`.

## Scope
**Release unit**: N/A: no release unit

- Covers `REQ-001`: one new row in the monitoring document's Status/Detection/Action table listing the three WARNING triggers and the `dedup_state=store_error` marker, with pointers to `db_03_07` (behavior) and ADR-008 (classification).

## Assumptions
- The existing `logger.warning()` signals are the adequate operational signal; no structured metric/exporter is added (UNK-01 resolved in the Plan: no metrics framework exists; OTel is trace-only and optional).
- The degradation behavior lives in `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` and the health wording in `docs/22_mcp/mcp_03_03_transport-and-health.md`; this document only adds the detection method and cross-references. (Verified against source: `scripts/mcp_servers/dispatch.py` L190 store-init unavailable, L215 write failure, L334 lookup failure; marker `dedup_state="store_error"` / `error_type="dedup_store_error"` returned on the store lost-or-recreated refusal (L323-325) and retryable fallback (L326), the lookup-failure retryable marker (L337) and refusal (L342-343), the pre-open `record_pending` write-failure refusal (L449-450), and the store-init-unavailable/disabled refusal (L465-466) and retryable overlay-only fallback (L468). A retryable post-open write failure is warning-only with no marker, per the ADR-004 registered exception. A fourth WARNING path exists — the store lost-or-recreated sentinel (L312) — whose behavior is owned by `db_03_07`/ADR-008 and is not added to the row: REQ-001 freezes the three named triggers.)
- The monitoring document currently has no dedup row (verified: no `dedup` match in `agent_10_05`).

## Design decisions
- Add exactly one row to the existing `Status | Detection Method | Action` table (L25-29); do not add a separate section and do not duplicate the Troubleshooting table.
- Describe each signal by level and trigger (WARNING-level log from the dispatcher at store-init unavailability, lookup failure, or post-open write failure), NOT by quoting concrete log strings or config values, per the Plan's content-policy mitigation.
- State only the observable marker (`dedup_state=store_error` recorded in the tool-audit payload when non-empty, `scripts/agent/tool_audit.py` L251-252) and defer the retry-class-dependent fail-open/fail-closed behavior to `db_03_07` and the disposable-cache classification to ADR-008, rather than restating them.

## Alternatives considered
- Adding a structured counter/metric: rejected (UNK-01) — no metrics framework exists; existing log warnings suffice.
- Adding a Troubleshooting-table row instead: rejected — the signal is a detectable status, not a symptom with a local fix action; the Status table is its home.

## Implementation
### Target file
- `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`

### Procedure
1. Confirm the three degradation branches and the marker in `scripts/mcp_servers/dispatch.py` (reference only, not modified): store-init unavailability warning (L190), store write-failure warning via `_store_op` (L215), lookup-failure warning (L334). The `dedup_state=store_error` marker is returned on the lost-or-recreated (L324, L326), lookup-failure (L337; refusal L342-343), pre-open `record_pending` write-failure refusal (L449-450), and store-init-unavailable/disabled (refusal L465-466; retryable fallback L468) paths; a retryable post-open write failure is warning-only with no marker (ADR-004).
2. Add one row to the `Status | Detection Method | Action` table: status "Dedup Protection Degraded (MCP dedup store)"; detection method = dispatcher WARNING-level log on any of the three triggers (store unavailable at init, dedup lookup failure, dedup store write failure) plus the `dedup_state=store_error` marker recorded in the tool-audit payload; action = pointer to `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (Replay Decision Table) for the degradation behavior and to `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (Recovery Policy Matrix) for the `mcp_dedup.sqlite` disposable-cache classification.

### Method
- Single table-row insertion matching the existing row format of the Status table; English only; no concrete log strings or config values quoted.

### Details
- Align marker wording with `docs/22_mcp/mcp_03_03_transport-and-health.md` L57-62: retryable tools proceed with an audited `dedup_state="store_error"` marker; `non_retryable` tools fail closed with `error_type="dedup_store_error"`. Name both markers only as detection identifiers; do not explain the retry-class policy (owned by `db_03_07` and ADR-004).
- The registered `record_pending` write-failure exceptions (`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` L247-248) are context for why the warning-only path is expected; they are not restated in the new row.

## Compatibility considerations
- Documentation-only; no runtime interface change. Existing overlay-only fallback behavior is already asserted by `tests/mcp_servers/test_mcp_dispatch.py` (reference only, not modified).

## Security considerations
- N/A for code. The edit closes an operational blind spot: degraded dedup protection was previously invisible in the monitoring reference.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/check_docs_japanese.py` — pass; English only; no implementation-detail content (no quoted log strings/config values); no Japanese.

## Completion criteria
- The Status table contains one dedup-degradation row listing the three WARNING triggers and the `dedup_state=store_error` marker, with pointers to `db_03_07` and ADR-008; all five documentation checkers pass.

## Out of Scope
- Adding a metric/exporter or metrics framework (UNK-01 resolved: document the existing log signal). Re-documenting degradation behavior, the `record_pending` post-open-write-failure policy, or the disposable-cache claim (`adrrev008`). Any edit to `scripts/mcp_servers/dispatch.py`, `scripts/agent/tool_audit.py`, the `db_03_07`, `mcp_03_03`, ADR-004, ADR-008 documents, or `tests/mcp_servers/test_mcp_dispatch.py` (reference files).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the three WARNING branches and `store_error` marker in `scripts/mcp_servers/dispatch.py` (reference read) | Completed | 20261115-203005 | 20261115-203005 | REQ-001 REQ-001: reference reads verified against dispatch.py/tool_audit.py/mcp_03_03; Step 3b corrected store_error marker line attribution (L326 belongs to lost-or-recreated; init/write-failure markers at L449-450/L465-468) |
| 2 | Add the dedup-degradation row to the Status table in `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Completed | 20261115-203005 | 20261115-203005 | REQ-001 Changed: docs/23_agent/agent_10_05_operations-and-observability-monitoring.md (one Status-table row added) |
| 3 | Run the five documentation checkers | Completed | 20261115-203054 | 20261115-203054 | Validation plan N/A: documentation-only change; replaced by the five docs checkers (all Pass); docs/00_index.md task-scope: target doc is the procedure's own target, no code file changed |

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
- **Requirement ID**: `REQ-001` (dedup-degradation signal documented as a detection method)
- **Source issue**: `issues/20261111-163849_mcpsec002_dedup-degradation-security-docs.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-055932_mcpsec002_dedup-degradation-security-docs.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-055932
- **Related target files**: `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`
## Goal
- Define the retention eligibility of the dedup store per stored state — retention applies to terminal
  rows past the retention window only, while unresolved states and `call_attempt_history` stay outside
  the sweep under the rules the repository owner recorded as intentional (`U-3`) — define the legal-hold
  boundary, and give operators a read-only view of the store's state counts, growth, WAL size, lock wait,
  lease health, and threshold status, exposed through the existing health `details` block of the 10
  servers that have a `[dedup]` table.

## Priority
Medium

## Scope
- **In-Scope**:
  - The retention matrix, mapping each state and result classification to its retention behaviour,
    including the classifications that have no stored status today. Retention eligibility applies to
    terminal rows past the retention window only; the matrix records the non-swept unresolved states and
    the state-independent history rule as intentional (owner decision recorded in `U-3`).
  - The legal-hold boundary: which rows the sweep excludes, and how held rows appear in counts.
  - `scripts/shared/mcp_dedup_metrics.py` (new, read-only): per-status counts, growth, WAL size, lock
    wait, lease health, threshold status.
  - The threshold mechanism: per-metric warning and fail-closed keys in the `[dedup]` table. Values are
    operator-supplied and are not defined by this Plan (`U-1`).
  - Health exposure through `scripts/mcp_servers/health_response.py` and the 10 server handlers that have
    a `[dedup]` table.
  - Monitoring criteria rows for the store, including the `Dedup Protection Degraded` row's thresholds.
  - The repository owner's resolution of the ADR-008 conflict this change had introduced: the sweep stays
    inside ADR-008's terminal-row retention behavior, so no ADR change is introduced and no approval
    record is required (`U-3`; `issues/20261123-120131_unknowns.md`, `issues/20261123-120131_02_unknowns.md`).
- **Out-of-Scope**:
  - Automatic restart, automatic escalation, automatic purge action. The threshold decision stays a
    documented operator action.
  - A new status service or endpoint.
  - Alert delivery, which has no source in the repository.
  - Threshold values.
  - A `legal_hold` column, which would change the persisted schema.
  - The state-machine definition itself (beyond the retention matrix), and the generated reference documents
    (the AUTO-GENERATED guard blocks such as `docs/23_agent/agent_13_reference-api-generated.md` and
    `docs/23_agent/agent_14_reference-api-subpackages-generated.md`), which are generated from code and must
    not be edited by hand.
- **Dependencies**: N/A: none. No ordering is asserted here. `check_plan_target_overlaps.py` reports shared
  target rows with the plan for mcpdl004, the plan for mcpai001, and the plan for mcpdl006, and the plan for
  mcpdl006 needs this Plan's matrix; all three overlaps are judged compatible in `Assumptions`, and the
  owner decides the order.

## Background
The issue exists because "delete after 14 days" is wrong for a durable ledger, and because no operator can
tell whether an unresolved state is expected, stuck, or growing. `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
`## Context` classifies the dedup store as a disposable cache with a retention window, while the same
document's Decision Details and Consequences describe it as a durable execution ledger with lease
ownership. That contradiction is what makes a single retention period ambiguous.

## Problem
`scripts/shared/mcp_dedup_ledger.py::purge_expired` (line 457) deletes only rows whose `status` is
`completed`, `failed`, or `interrupted` and whose `updated_epoch` is past the cutoff; `pending` rows are
never deleted there — the module states "Pending rows are never purged here; their expiry path is
classification." `reconcile_execution()` (line 367) moves a stale `pending` row to `interrupted` and
appends a `reconciled` history entry, after which the sweep can purge it, so what persists past the
window is a row that cannot be reconciled — an attempts-exhausted `outcome_unknown` or a row with no
external fact to reconcile against. `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`
already carries a `Dedup Protection Degraded` criteria row for this store, but it is a list of log
conditions, not numeric criteria, and no read path reports counts, growth, WAL size, lock wait, or lease
health.

`call_attempt_history` keeps no state; the sweep deletes its rows by `recorded_epoch < cutoff` regardless
of the parent row's state (line 478), so its retention cannot be decided by state (`U-5`). Whether an
unresolved state is an in-flight record, a retained exception, or an item requiring operator action is not
decided anywhere.

## Reason for Change
Unresolved states cannot be deleted by the same rule as terminal ones, and an operator needs a definition
of normal, degraded, and action-required for the store. The metrics read is what makes the retention and
legal-hold decisions observable, so both halves of this Plan are one change.

## Implementation Intent
- Write the retention matrix test first, then change the purge, so the expected behaviour is fixed before
  the code that produces it.
- Map each result classification to a stored status before writing matrix rows, because the stored
  vocabulary is four states and the classifications are not states.
- Keep the metrics read read-only, as the issue states.
- Use the existing health `details` mechanism for exposure, so there is no second status service.
- Record the ADR-008 resolution the repository owner decided (terminal-row-only scope, `U-3`); no ADR
  change is introduced and no approval statement is written.

## Requirements
- `REQ-001`: Define the retention matrix per state and result classification, mapping each classification
  to the stored status it corresponds to, and state for each whether retention applies.
- `REQ-002`: Keep the sweep inside the terminal-row rule `purge_expired` already implements and the
  ADR-008 Recovery Policy Matrix states, and add the legal-hold exclusion to its condition; the matrix
  records unresolved states and `call_attempt_history` as outside the sweep, and the lifecycle of
  unresolved rows belongs to `reconcile_execution()` and mcpdl006, not to the sweep.
- `REQ-003`: Define the legal-hold boundary as a configuration entry, and state how held rows appear in
  counts.
- `REQ-004`: Add a read-only metrics module reporting per-status counts, growth, WAL size, lock wait,
  lease health, and threshold status, and publish it through the existing health `details` block for the 10
  servers that have a `[dedup]` table.
- `REQ-005`: Define the warning-level monitoring criteria for those metrics as reported per-metric status
  (a read path that computes and publishes the status; no store or dispatcher behaviour changes), keep
  automatic action out of scope, and treat the retained unresolved rows as growth the criteria must surface
  rather than growth the sweep removes.
- `REQ-006`: Record the repository owner's resolution of the ADR-008 conflict (`U-3`: the sweep stays inside
  the terminal-row rule, so no ADR change is introduced); do not amend the ADR and do not write an approval
  statement.
- `REQ-007`: Define the threshold mechanism (config keys and their validation range) without defining
  numeric values.
- `REQ-008`: Keep the metrics path read-only: no writes, no migration, no new service.

## Implementation Target Files
**Freeze status**: Frozen — `tools/audit_plan_target_paths.py` reported 0 findings for this Plan and
`tools/check_plan_target_overlaps.py` reported no overlap with the other Frozen plans; every row below is
`Verified`.

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this table.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | The retention matrix and the per-state retention eligibility rule, written first: terminal rows swept past the retention window, the unresolved states and `call_attempt_history` recorded as outside the sweep. The file already documents the retention sweep, so the matrix belongs in it rather than in a new file. | REQ-001, REQ-003; AC-1, AC-3 | `docs/41_db/db_00_document-guide.md` lists it; the retention-sweep paragraph was read, and the file has 10 changes in 30 days, the highest of the targets. (checked in Step 3) | `tests/shared/test_mcp_dedup.py` | Verified |
| `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Modify | The monitoring criteria rows for the store, and the numeric thresholds for the existing `Dedup Protection Degraded` row. | REQ-005; AC-5 | Read in full in Step 3: the criteria table already carries a `Dedup Protection Degraded` row for this store as a list of log conditions with no numeric criteria, so the change adds the numeric criteria rows, not the first mention of the store. | `tools/check_docs_consistency.py` | Verified |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Modify | The `details` content for the 10 wired servers. | REQ-004; AC-4 | Read in Step 3; it defines the health payload and the per-server `details` table, and `docs/22_mcp/mcp_00_document-guide.md` lists it. | `tests/mcp_servers/test_health_response.py` | Verified |
| `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` | Modify | The `[dedup]` key inventory for the new threshold and legal-hold keys. | REQ-007; AC-7 | Read in Step 3; `docs/22_mcp/mcp_00_document-guide.md` requires the inventory, and the file already lists the `[dedup]` keys. | `tools/check_docs_consistency.py` | Verified |
| `scripts/shared/mcp_dedup_metrics.py` | Create | New read-only metrics module: counts, growth, WAL size, lock wait, lease health, threshold status. | REQ-004, REQ-008; AC-4, AC-8 | New module. `scripts/mcp_servers/web_search/metrics.py` is the existing metrics-module placement pattern (there is no existing shared dedup health or metrics module). The import contract keeps `scripts/shared/` a leaf, so it cannot import `mcp_servers`. (checked in Step 3) | `tests/shared/test_mcp_dedup_metrics.py` | Verified |
| `scripts/shared/mcp_dedup.py` | Modify | Re-export the new module's public names through the facade. | REQ-004; AC-4 | `scripts/shared/mcp_dedup.py` imports `shared.mcp_dedup_config` and `shared.mcp_dedup_ledger` and re-exports their names; the WAL pragma is at line 169, not 271 as the issue states, and `purge_expired` is not in this file. (checked in Step 2) | `tests/shared/test_mcp_dedup.py` | Verified |
| `scripts/shared/mcp_dedup_ledger.py` | Modify | `purge_expired` keeps its terminal-only eligibility and gains the legal-hold exclusion to its `WHERE` condition; the eligibility rule is made explicit. | REQ-002; AC-2 | Read in full in Step 2: the terminal-only `DELETE` and the "pending rows are never purged here" line were confirmed. | `tests/shared/test_mcp_dedup.py` | Verified |
| `scripts/shared/mcp_dedup_config.py` | Modify | The threshold keys and the `legal_hold_states` list key, each with its own validation; no default value is added. | REQ-003, REQ-007; AC-3, AC-7 | Read in Step 3: the `_DEDUP_INT_KEYS` table validates `retention_days` and the other keys with `(default, low, high)` tuples, so the thresholds extend the same contract; unknown keys already fail closed, and `_config_fingerprint()` stays untouched (the threshold keys are not part of store identity). | `tests/mcp_servers/test_config_isolation_fail_closed.py` | Verified |
| `scripts/mcp_servers/health_response.py` | Modify | Publish the metrics block through `make_health_response(...)`, additively. | REQ-004; AC-4 | Read in full in Step 3; `details` is an argument, and `tests/mcp_servers/test_health_response.py` pins `BASE_KEYS`, so the change must be additive. | `tests/mcp_servers/test_health_response.py` | Verified |
| `scripts/mcp_servers/file/common.py` | Modify | The shared health path for the three file servers. | REQ-004; AC-4 | `scripts/mcp_servers/file/read_server.py`, `write_server.py`, `delete_server.py` call `_health()` from this module, so one row covers three servers. (checked in Step 3) | `tests/mcp_servers/file/test_file_health_posture.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_server.py` | Modify | Its `/health` handler passes the metrics block. | REQ-004; AC-4 | `grep` found `@app.get("/health")` at line 189; `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` asserts the current `details` content, so it is extended in the same step. (checked in Step 3) | `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Verified |
| `scripts/mcp_servers/git/git_server.py` | Modify | The same. | REQ-004; AC-4 | `grep` found the handler at line 373; `tests/mcp_servers/git/test_git_security_compliance.py` asserts `details`. (checked in Step 3) | `tests/mcp_servers/git/test_git_security_compliance.py` | Verified |
| `scripts/mcp_servers/github/github_server.py` | Modify | The same. | REQ-004; AC-4 | `grep` found the handler at line 173; `tests/mcp_servers/github/test_github_server_endpoints.py` asserts `details`. (checked in Step 3) | `tests/mcp_servers/github/test_github_server_endpoints.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | The same, keeping the row counts it already publishes. | REQ-004; AC-4 | The handler at line 445 and its existing `details` content were read in Step 3. | `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Verified |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Modify | The same. | REQ-004; AC-4 | `grep` found the handler at line 202; `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py` asserts the payload keys. (checked in Step 3) | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py` | Verified |
| `scripts/mcp_servers/shell/shell_server.py` | Modify | The same. | REQ-004; AC-4 | `grep` found the handler at line 140; `tests/mcp_servers/shell/test_shell_mcp_service.py` asserts `details`. (checked in Step 3) | `tests/mcp_servers/shell/test_shell_mcp_service.py` | Verified |
| `scripts/mcp_servers/web_search/web_search_server.py` | Modify | The same, alongside the existing metrics module. | REQ-004; AC-4 | `grep` found the handler at line 139; `scripts/mcp_servers/web_search/metrics.py` was read in Step 3. | `tests/mcp_servers/web_search/test_web_search_health.py` | Verified |
| `tests/shared/test_mcp_dedup.py` | Modify | The matrix-shaped tests, written before the code. `TestTtlPurge` pins the current behaviour, so the new expectation is added there. | REQ-001, REQ-002, REQ-003; AC-1, AC-2, AC-3 | `class TestTtlPurge` was read in Step 3. | itself | Verified |
| `tests/shared/test_mcp_dedup_metrics.py` | Create | Tests for the new module, including that the read is read-only. | REQ-004, REQ-008; AC-4, AC-8 | New file. `tests/shared/test_mcp_dedup.py` and `tests/shared/test_mcp_dedup_identity.py` are the existing pattern; there is no metrics test in the repository. (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/test_health_response.py` | Modify | The `details` block with metrics; `BASE_KEYS` must stay intact. | REQ-004; AC-4 | Read in Step 3; it asserts `set(body) == BASE_KEYS` and `details == {}`. | itself | Verified |
| `tests/mcp_servers/test_config_isolation_fail_closed.py` | Modify | A threshold value outside the validation range must fail closed, as the other `[dedup]` keys do. | REQ-003, REQ-007; AC-3, AC-7 | Read in Step 3. | itself | Verified |
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Modify | It asserts `body["details"] == {"service": "cicd-mcp"}`, an exact-equality assertion that the new `details` content breaks, so the expectation is extended here. | REQ-004; AC-4 | Read in Step 3, line 255. | itself | Verified |
| `tests/mcp_servers/github/test_github_server_endpoints.py` | Modify | The same exact-equality assertion, at lines 188 and 200. | REQ-004; AC-4 | Read in Step 3. | itself | Verified |
| `tests/mcp_servers/file/test_file_health_posture.py` | Modify | It asserts `body["details"] == {}` for the file servers, so the expectation is extended here. | REQ-004; AC-4 | Read in Step 3, line 149. | itself | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | The ADR whose Decision Detail #23 and INV-09 the scope question touched. It is not modified by this Plan: the owner resolved `U-3` with terminal-row-only scope, which stays inside Decision Detail #23, so Decision Details and INV-09 stay as they are and no approval record is introduced. | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`; REQ-006, `U-3` |
| `scripts/shared/mcp_dedup_schema.py` | The `status` `CHECK` and `START_STATES`/`TERMINAL_STATES` the matrix must map to; the matrix cannot name a state the schema does not allow. | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`; REQ-001 |
| `scripts/shared/mcp_health.py` | Server availability health for dispatch gating; a distinct concern from dedup store metrics. The new metrics module must not be conflated with it, and no pending-row-degraded check exists in it today: the criteria row in `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` is a list of WARNING log conditions, and the new numeric criteria extend it, not replace it. | `scripts/shared/mcp_dedup_metrics.py`; REQ-004, REQ-005 |
| `scripts/mcp_servers/server.py` | Calls `load_dedup_section()` at startup (line 364), the fail-closed validation gate every config change must keep passing. | `scripts/shared/mcp_dedup_config.py`; REQ-003, REQ-007 |
| `scripts/shared/config_loader.py` | `ConfigLoader.restrict_to()` is how the `[dedup]` table is loaded, so the new keys are validated through it unchanged. | `scripts/shared/mcp_dedup_config.py`; REQ-003 |
| `scripts/db/maintenance.py` | A separate `retention_days` rule that must not be confused with the dedup sweep; confirmed not affected. | `scripts/shared/mcp_dedup_config.py`; REQ-002 |
| `scripts/mcp_servers/dispatch.py` | The only caller of `purge_expired`, and the module is 3 bytes under the size gate, so the Plan adds no code there. | `scripts/shared/mcp_dedup_ledger.py`; REQ-002 |
| `scripts/mcp_servers/web_search/metrics.py` | The existing metrics-module placement pattern the new module follows. | `scripts/shared/mcp_dedup_metrics.py`; REQ-004 |
| `tests/mcp_servers/_route_inventory.py` | The invariant that an MCP app registers exactly one execution route, which is why no new endpoint is added. | REQ-004 (Out-of-Scope) |
| `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | The existing pattern for asserting health `details` content, including the `service` key the new block must not replace. Its assertions read specific keys by subscript, so they stay passing unchanged. | `scripts/mcp_servers/mdq/mdq_server.py`; REQ-004 |
| `tests/mcp_servers/git/test_git_security_compliance.py` | Asserts `details` values by key, not by whole-dict equality, so the new `details` content does not break it. Recorded to show the per-server tests that are unaffected. | `scripts/mcp_servers/git/git_server.py`; REQ-004 |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py` | Asserts the health payload key set for rag-pipeline-mcp; the added `details` content must not break it. Not modified. | `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`; REQ-004 |
| `tests/mcp_servers/shell/test_shell_mcp_service.py` | Asserts `details` membership for shell-mcp rather than equality, so it stays passing unchanged. | `scripts/mcp_servers/shell/shell_server.py`; REQ-004 |
| `tests/mcp_servers/web_search/test_web_search_health.py` | Asserts `details` membership for web-search-mcp, including the existing `metrics` key, so the new block must not replace it. Not modified. | `scripts/mcp_servers/web_search/web_search_server.py`; REQ-004 |
| `tests/mcp_servers/test_mcp_dispatch.py` | Asserts the caller contract for the changed rule: the once-per-process sweep flag and the degradation behaviour must stay unchanged. | `scripts/mcp_servers/dispatch.py`; REQ-002 |
| `tests/deploy/test_init_db_schema_gate.py` | The persisted-schema and config-file-count assertions. No DDL is added, so it must stay passing unchanged. | `scripts/shared/mcp_dedup_config.py`; REQ-003, REQ-008 |
| `docs/00_governance/governance_01_documentation-policy.md` | The ADR Status values, the ADR Acceptance Evidence Standard that makes an approval record required, and the generated-reference rule that forbids hand-editing `docs/13_ref/*`. | REQ-006, REQ-007 |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | The RACI Model that names the accountable party for an ADR decision. | REQ-006 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | The requirement that an open decision be recorded as uncertainty (`## Needs Confirmation` in a document, or the Plan's Unknowns table), not as a present-tense decision. | REQ-006 |
| `docs/41_db/db_08_active_databases.md` | The metrics list the new read must stay consistent with. | `scripts/shared/mcp_dedup_metrics.py`; REQ-004 |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (state-machine sections) | The existing state table (`pending -> completed/failed/interrupted`) the retention matrix must not contradict; the state-machine definition itself is out of scope for change. | REQ-001 |
| `docs/22_mcp/mcp_00_document-guide.md` | The guide that requires the config-file inventory and the health payload to be documented in these files. | `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`; REQ-004 |
| `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` | The operator runbook the criteria table describes action for; the criteria row must name the same action it already defines. | `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`; REQ-005 |

## Acceptance Criteria
- AC-1 (REQ-001): the matrix maps every state and result classification to a stored status and states
  whether retention applies, for every row including `call_attempt_history`.
- AC-2 (REQ-002): `purge_expired` purges terminal rows past the retention and does not purge held rows or
  unresolved states.
- AC-3 (REQ-003): a legal-hold exception exists as a `[dedup]` configuration entry, and held rows are
  reported as held, not as retained-at-large.
- AC-4 (REQ-004): the metrics module reports per-status counts, growth, WAL size, lock wait, lease health,
  and threshold status, and the 10 servers with a `[dedup]` table publish them through `/health`.
- AC-5 (REQ-005): the criteria table defines normal, degraded, and action-required at the warning level,
  and no automatic action is introduced.
- AC-6 (REQ-006): the ADR-008 resolution (`U-3`: terminal-row-only scope, no ADR change) is recorded in this
  Plan and in the unknowns issues; the ADR is not amended and no approval statement is written.
- AC-7 (REQ-007): the threshold keys and their validation range are defined, and no numeric value is
  introduced by this Plan.
- AC-8 (REQ-008): the metrics path performs no write, no migration, and no new service.

## Tests
- REQ-001, REQ-002, REQ-003 — `tests/shared/test_mcp_dedup.py` (unit): matrix-shaped tests written
  before the code. Terminal rows past the retention are purged; a retained unresolved state is not; a held
  row is not. `TestTtlPurge` is extended, not replaced.
- REQ-003, REQ-007 — `tests/mcp_servers/test_config_isolation_fail_closed.py` (unit): a new threshold key
  outside its declared range fails startup closed, and configs without the optional keys keep passing. There
  is no `tests/shared/test_mcp_dedup_config.py` in the repository, so this is where the contract is tested.
- REQ-004, REQ-008 — `tests/shared/test_mcp_dedup_metrics.py` (unit): the read returns the documented
  fields for a store with rows in each state, and issues no write.
- REQ-004 — `tests/mcp_servers/test_health_response.py` (unit): `details` carries the metrics block when a
  store is given and stays empty otherwise; `BASE_KEYS` is unchanged.
- REQ-004 — `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`,
  `tests/mcp_servers/github/test_github_server_endpoints.py`,
  `tests/mcp_servers/file/test_file_health_posture.py` (unit): these assert the whole `details` dict by
  equality, so their expectation is extended to include the metrics block while the `service` key stays as
  it is. The other per-server tests assert `details` by key membership and are reference rows, so they must
  keep passing unchanged.
- REQ-002 — `tests/mcp_servers/test_mcp_dispatch.py` (unit): the degradation path and the once-per-process
  sweep behaviour are unchanged.
- REQ-005 — `tests/deploy/test_init_db_schema_gate.py` (integration, marked `integration`): the config-file
  count expectation and the schema fingerprint stay unchanged.

## Documentation Impact
- `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` — REQ-001, REQ-003: the retention matrix and
  the per-state eligibility rule; the existing retention-sweep paragraph must say the same as the code.
- `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` — REQ-005: the criteria rows. No
  `## Needs Confirmation` subsection is required there, because the threshold values are recorded as an open
  decision in the Plan's Unknowns table, not as an unresolved claim in the document.
- `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` — REQ-004: the health `details` content for the
  wired servers.
- `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` — REQ-007: the `[dedup]` key inventory, which
  `docs/22_mcp/mcp_00_document-guide.md` requires.
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` — REQ-006: unchanged by this Plan. `U-3` is
  resolved with terminal-row-only scope, which stays inside Decision Detail #23 and INV-09, so the ADR's
  wording is not touched and no approval record is created.

## Assumptions
- The metrics module is read-only; no write and no migration.
- The metrics read is not a separate status service; it is exposed through the health `details` block.
- The 10 `config/*_mcp_server.toml` files are committed and carry a `[dedup]` table, but they are not target
  rows: the Plan adds no default values and its new keys are optional, so the existing configs stay valid
  unchanged, and the operator-supplied values (`U-1`) are an operational decision, not a repository edit. The
  `[dedup]` key inventory is documented through `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`.
- Threshold values are operator-supplied; the Plan defines the mechanism only.
- Threshold status is reported only: the read path computes and publishes per-metric status; thresholds do
  not gate store or dispatcher behaviour (owner decision `D-6` in
  `issues/20261123-120131_02_unknowns.md`).
- The new threshold and hold keys are excluded from `_config_fingerprint()`: store identity is unchanged,
  and the 10 committed configs do not need value agreement for keys they do not yet carry (owner decision
  `D-5` in `issues/20261123-120131_02_unknowns.md`).
- `call_attempt_history` retention stays the current state-independent rule and is recorded as intentional
  (owner decision `D-2` in `issues/20261123-120131_02_unknowns.md`); the unresolved states are not swept, and
  moving them to a resolvable state belongs to `reconcile_execution()` and the mcpdl006 plan, not to this
  Plan's sweep.
- Legal hold is configuration-based, per the decision recorded in this cycle, not a schema change.
- The 10 servers with a `[dedup]` table are the whole scope of the health wiring; `scripts/mcp_servers/dispatch.py`
  runs the sweep inside the servers and is not a health endpoint, so it is not wired.
- Overlap with the plan for mcpdl004: `tools/check_plan_target_overlaps.py` reports three shared target
  rows — `scripts/shared/mcp_dedup.py`, `scripts/shared/mcp_dedup_ledger.py`,
  `tests/shared/test_mcp_dedup.py`. The designs do not contradict each other: that plan adds result metadata
  and a read-only `call_state_view`, this plan changes the purge rule and adds a read-only metrics read, and
  neither modifies what the other adds. Both add test cases to the same test file, so they are additive. That
  plan is the one that defines the observable result vocabulary this plan maps; no order is asserted here, and
  `check_plan_target_overlaps.py` treats shared targets as notes, not as ordering edges. If this plan is
  implemented before that one, the matrix rows for the three classifications can only state the mapping
  direction, because the vocabulary does not exist yet.
- That plan's DDL change moves the persisted-schema fingerprint and raises `_USER_VERSION` 1→2. This plan adds
  no DDL, so `tools/check_init_db_schema_gate.py`'s assertion is unaffected by this plan alone; the overlap is
  noted here because the same test file is targeted by both. `scripts/shared/mcp_dedup_ledger.py` growth is a
  shared risk for the 24,576 B module-size gate, which is why this plan puts the read in a new module rather
  than in the ledger.
- Overlap with the plan for mcpai001 (`plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md`):
  `tools/check_plan_target_overlaps.py` reports shared rows including `scripts/shared/mcp_dedup_ledger.py` and
  `tests/shared/test_mcp_dedup.py`. The designs do not contradict each other: that plan changes
  `try_acquire_execution()` and the `interrupted`-reopen cases, this plan touches `purge_expired` and
  `TestTtlPurge`; the shared files are edited at different functions and test classes. That plan's Assumptions
  record the same judgement from its side. No order is asserted here.

## Unknowns

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? |
|----|---------------------|----------------|-----------------|-----------|
| U-1 | Threshold values for capacity, lock wait, heartbeat delay, and unresolved-state backlog. | No defined thresholds exist in the repository; the `Dedup Protection Degraded` criteria row in `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` lists log conditions but no numeric criteria. | Operator-supplied config values through the mechanism REQ-007 defines. Ask the repository owner for the values, or record them when the criteria table is filled. | False |
| U-2 | Whether legal hold is legal or operational. | No legal-hold mechanism exists in the repository; the nearest precedent is `/memory prune` excluding `pinned`. | Resolved as configuration-based, which keeps the persisted schema unchanged. If it is later decided to be a stored column, the persisted-schema gate and the config fingerprint apply, and it needs an ADR decision because it changes the disposable-cache classification. Re-check then. | False |
| U-3 | A state-dependent rule would change ADR-008 Decision Detail #23, which defines retention as terminal rows past the retention, and conflicts with the unbounded-growth acceptance in INV-09 for a store classified as a disposable cache. | No approval record or decision existed that permitted retaining non-terminal states in a disposable-cache store; `docs/00_governance/governance_01_documentation-policy.md` requires a named approval record for a decision that changes an ADR, which this phase cannot create. | Resolved by the repository owner in this cycle, option (a): scope retention to terminal rows only (see `Scope`, `REQ-002`). The sweep stays inside the rule ADR-008 Decision Detail #23 already states, so no ADR change is introduced and no approval record is needed; the retained-unresolved growth stays inside ADR-008's unbounded-growth acceptance and is made observable by the criteria rows. Recorded in `issues/20261123-120131_unknowns.md` and `issues/20261123-120131_02_unknowns.md`. | False |
| U-4 | Whether the metrics read is exposed through `/health`, a new endpoint, or a runbook command. | None: resolved by evidence. The health `details` mechanism is defined and mdq-mcp already publishes counts, so no new status service is needed. | Confirmed by repository evidence; recorded as the design decision in `Design`. | False |
| U-5 | `call_attempt_history` has no state, so its retention cannot be decided by the matrix. | None: the issue itself states this. | Resolved by the repository owner in this cycle (`D-2` in `issues/20261123-120131_02_unknowns.md`): the sweep's current state-independent rule — history rows older than the cutoff are deleted alongside terminal rows — is recorded as intentional. The matrix states the history rule separately from the state rows and names it as such; a state-dependent history exception would need a separate owner approval outside this Plan. | False |
| U-6 | The three result classifications have no observable state, so the matrix cannot assign them retention behaviour as states. | The stored-state set in `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` and `scripts/shared/mcp_dedup_schema.py` does not include them (there is no `docs/11_req/*` in the repository). | mcpdl006 defines those states; this Plan's matrix keeps its unresolved-state rows as state-conditional definitions applied when those states exist, which is why it is not blocked here. Recorded in `Assumptions` as a shared-target overlap, not as an ordering. | False |
| U-7 | No alert delivery exists for the warning level. | `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` states no alert, escalation, or metric-emitter source exists. | Out of scope per the issue. A delivery channel needs a source, not a judgment call. | False |

## Affected areas
Every row below is a row of `Implementation Target Files` above, so this table analyses the same scope.
Churn is from `git log --name-only --since=30.days` (Step 3); Bus Factor is `N/A` because `git-fame` is not
installed. `deploy.sh Impact` is stated per row.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | High | 10 | N/A: `git-fame` is not installed | docs-only |
| `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Modify | Medium | 5 | N/A: `git-fame` is not installed | docs-only |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Modify | Medium | 4 | N/A: `git-fame` is not installed | docs-only |
| `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` | Modify | Medium | 1 | N/A: `git-fame` is not installed | docs-only |
| `scripts/shared/mcp_dedup_metrics.py` | Create | Medium | N/A: new file | N/A: new file | MCP servers |
| `scripts/shared/mcp_dedup.py` | Modify | High | 10 | N/A: `git-fame` is not installed | MCP servers |
| `scripts/shared/mcp_dedup_ledger.py` | Modify | Medium | 1 | N/A: `git-fame` is not installed | MCP servers |
| `scripts/shared/mcp_dedup_config.py` | Modify | High | 3 | N/A: `git-fame` is not installed | MCP servers |
| `scripts/mcp_servers/health_response.py` | Modify | High | 0 | N/A: `git-fame` is not installed | MCP servers |
| `scripts/mcp_servers/file/common.py` | Modify | Medium | 0 | N/A: `git-fame` is not installed | MCP servers |
| `scripts/mcp_servers/cicd/cicd_server.py` | Modify | Medium | 1 | N/A: `git-fame` is not installed | MCP servers |
| `scripts/mcp_servers/git/git_server.py` | Modify | Medium | 2 | N/A: `git-fame` is not installed | MCP servers |
| `scripts/mcp_servers/github/github_server.py` | Modify | Medium | 2 | N/A: `git-fame` is not installed | MCP servers |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | Medium | 5 | N/A: `git-fame` is not installed | MCP servers |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Modify | Medium | 7 | N/A: `git-fame` is not installed | MCP servers |
| `scripts/mcp_servers/shell/shell_server.py` | Modify | Medium | 3 | N/A: `git-fame` is not installed | MCP servers |
| `scripts/mcp_servers/web_search/web_search_server.py` | Modify | Medium | 3 | N/A: `git-fame` is not installed | MCP servers |
| `tests/shared/test_mcp_dedup.py` | Modify | Medium | 9 | N/A: `git-fame` is not installed | tests-only |
| `tests/shared/test_mcp_dedup_metrics.py` | Create | Low | N/A: new file | N/A: new file | tests-only |
| `tests/mcp_servers/test_health_response.py` | Modify | Medium | 0 | N/A: `git-fame` is not installed | tests-only |
| `tests/mcp_servers/test_config_isolation_fail_closed.py` | Modify | Low | 1 | N/A: `git-fame` is not installed | tests-only |
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Modify | Low | 3 | N/A: `git-fame` is not installed | tests-only |
| `tests/mcp_servers/github/test_github_server_endpoints.py` | Modify | Low | 1 | N/A: `git-fame` is not installed | tests-only |
| `tests/mcp_servers/file/test_file_health_posture.py` | Modify | Low | 0 | N/A: `git-fame` is not installed | tests-only |

## Design

### Path classification
Path B: more than 3 target files, new monitoring modules, a configuration change, and an ADR conflict.

### State vocabulary
The stored vocabulary is `pending` (unresolved) and `completed`, `failed`, `interrupted` (terminal),
defined by the `status` `CHECK` in `scripts/shared/mcp_dedup_schema.py` and re-exported as `START_STATES`
and `TERMINAL_STATES` through `scripts/shared/mcp_dedup.py`. `reconciliation_required`,
`outcome_unknown`, and `replay_unavailable` are acquisition result classifications, and `reconciled` is a
`call_attempt_history` outcome value, not a `dedup_call_state` status. The matrix must map each
classification to its stored status (`pending`, or `interrupted` for an interrupted execution); `reconciled`
has no stored status row, so its retention follows the history rule. Because the three classifications have
no observable state, the matrix cannot assign retention behaviour to them as states; this Plan states the
mapping direction, and its test asserts behaviour only for what is observable. That gap belongs to mcpdl006;
no implementation order is asserted, so the matrix rows for the three classifications state the mapping
direction only, and their behaviour test is written after that vocabulary exists.

### Module placement
The metrics module is a new leaf module in `scripts/shared/`, following `scripts/mcp_servers/web_search/metrics.py`'s
pattern, because `scripts/shared/mcp_dedup_schema.py` defines the schema and `scripts/shared/mcp_dedup_ledger.py`
owns row access. `scripts/shared/` is the leaf of the import contract (6 contracts kept, run in Step 3), so
it cannot import `mcp_servers`; the read goes from `shared` toward the handler, not the other way. The read
uses the store's existing connection, which already carries `busy_timeout` (`scripts/shared/mcp_dedup.py::open_store()`),
so lock-wait reporting reuses it instead of opening a second connection.

The health change is a new optional argument to `make_health_response(...)`, which must stay additive
because `tests/mcp_servers/test_health_response.py` pins `BASE_KEYS`. `scripts/mcp_servers/file/common.py`
is shared by the three file servers, so one row covers three handlers; the other seven handlers are
separate rows.

### Module size
`scripts/mcp_servers/dispatch.py` is 24573 bytes against the 24576 B gate, so it gains no code. The read is
placed in the new shared module and called from each handler, which keeps `_purge_once()` unchanged.

### Thresholds
The mechanism is config-supplied warning and fail-closed thresholds per metric, validated in
`scripts/shared/mcp_dedup_config.py` and reported as a per-metric status (`ok`, `warning`, `fail`) that the
read path computes and publishes; no store or dispatcher behaviour changes (owner decision `D-6` in
`issues/20261123-120131_02_unknowns.md`). The values are not defined here (`U-1`); nothing in this Plan
hard-codes a number. Design
constraint verified against the code: `scripts/shared/mcp_dedup_config.py::_DEDUP_INT_KEYS` gives every key
a `(default, low, high)` tuple and unknown keys already fail closed, so the threshold keys cannot join that
table without inventing numeric defaults. They are added as explicitly allowed optional keys: absent means
unset (no status computed for that metric), present means validated against an explicit `(low, high)`
range, and none of them enter `_config_fingerprint()`, so store identity is unchanged (owner decision).

### Retention matrix
Rows: the four stored states, the three classifications that have no stored state, and
`call_attempt_history`. Each row states whether retention applies, the rule, whether legal hold applies, and
what the test asserts. Terminal rows are purged past the retention; `pending` rows are already never
purged, so the change is the exception path for the observable classifications, and the matrix is the
source the test is written from.

### Legal hold
Configuration-based: a `[dedup]` entry listing states or keys excluded from the sweep. No DDL change, so the
persisted-schema gate and the config fingerprint are unaffected. Held rows are counted as held, not as
retained-at-large; the matrix states this in its legal-hold column. The nearest repository precedent for a
hold list is `/memory prune` excluding `pinned`.

### Consumer scan
`uv run python tools/scan_change_consumers.py --seed purge_expired --seed retention_days` (testmon state:
not applicable, no `.testmondata`) returned these candidates, each resolved here:

- `scripts/shared/mcp_dedup.py` — facade re-export; row, no rename.
- `scripts/mcp_servers/dispatch.py::_purge_once` — the only caller; reference row, no change.
- `scripts/mcp_servers/server.py` — `load_dedup_section()` is called at startup (line 364); the validation gate
  must keep passing after the threshold keys are added. There is no `scripts/shared/mcp_dedup_cli.py` or
  `scripts/shared/mcp_dedup_health.py` in the repository, and no `cmd_purge` or `check_store` symbol exists;
  `dispatch.py::_purge_once` is the only caller of `purge_expired`.
- `scripts/db/maintenance.py` — `not affected: its own `retention_days` rule is not the dedup sweep`.
- `scripts/shared/config_loader.py` — `not affected: the loader does not validate keys`; the validation row is
  `scripts/shared/mcp_dedup_config.py`.
- `tests/shared/test_mcp_dedup.py`, `tests/mcp_servers/test_mcp_dispatch.py`,
  `tests/mcp_servers/test_health_response.py`, `tests/mcp_servers/test_config_isolation_fail_closed.py` — rows.

### Predictable fallout
- Module size: `scripts/mcp_servers/dispatch.py` is 3 bytes under the gate, so no code is added there and no
  split row is created; the new module is the split.
- Pinned counts and pinned payload content: `tests/deploy/test_init_db_schema_gate.py` asserts the
  config-file count, `tests/shared/test_mcp_dedup.py::TestDedupSectionValidation` pins the current key
  validation behaviour, and three endpoint tests assert the whole `details` dict by equality
  (`tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, `tests/mcp_servers/github/test_github_server_endpoints.py`,
  `tests/mcp_servers/file/test_file_health_posture.py`); `tests/shared/test_mcp_dedup.py` and the last three
  are target rows, `tests/deploy/test_init_db_schema_gate.py` is a reference row that must keep passing
  unchanged, and the config-file count is unchanged because no config file is added.
- Tool inventory: no `tools/*.py` is added or removed.
- Generated blocks: no target row is under a generated-reference domain, so
  `tools/generate_reference_table.py --check` is not applicable to this Plan's rows.

### Historical analysis
30-day churn from `git log --name-only --since=30.days` (Step 3), used for the `Affected areas` table.
Bus factor: `N/A`, `git-fame` is not installed.

### Operational dependency inspection
`fuser` is available; the dedup store path was confirmed to exist and no process holds it, and no MCP
service port is listening, so no runtime consumer is affected at the time of this analysis. `universal-ctags`
is not installed, so the consumer scan relied on `tools/scan_change_consumers.py` and `grep` instead. `grimp`
and `networkx` are not installed, so the dependency graph is the import-linter contract plus the consumer
scan, not a computed graph.

## Implementation steps

1. **Phase 1: Write the retention matrix first**
   - [ ] Add the matrix rows for the four stored states and for the three classifications that have no
     stored state, each mapped to its stored status — terminal rows swept past the retention window,
     unresolved states and classifications recorded as outside the sweep — plus the `call_attempt_history`
     row, which states the current state-independent history rule as intentional (owner-resolved `U-5`;
     `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`).
   - [ ] Add the legal-hold column and define what is excluded (REQ-003; `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`).
   - [ ] Write each row from the behaviour the test will assert, so the document is the source of the test
     expectation and not a description of the code after the change (REQ-001; `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`).
2. **Phase 2: Tests from the matrix**
   - [ ] Extend `TestTtlPurge`: terminal rows past the retention are purged, a retained unresolved state is
     not, a held row is not (REQ-001, REQ-002, REQ-003; `tests/shared/test_mcp_dedup.py`).
   - [ ] Add `tests/shared/test_mcp_dedup_metrics.py`: the read returns the documented fields for a store
     with rows in each state and issues no write (REQ-004, REQ-008; `tests/shared/test_mcp_dedup_metrics.py`).
3. **Phase 3: Change the purge**
   - [ ] Add the legal-hold exclusion to `purge_expired`'s terminal-only `DELETE`: terminal rows past the
     retention are purged, held rows are excluded, and the eligibility set stays terminal-only so unresolved
     states stay outside the sweep (REQ-002; `scripts/shared/mcp_dedup_ledger.py`).
   - [ ] Keep the caller contract in `scripts/mcp_servers/dispatch.py` unchanged, including the
     once-per-process flag and the degradation behaviour (REQ-002; `scripts/mcp_servers/dispatch.py` is not a
     target row, so this item changes nothing and is guarded by `tests/mcp_servers/test_mcp_dispatch.py`).
   - [ ] Make the document say the same as the code (REQ-002; `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`).
4. **Phase 4: Threshold mechanism and metrics module**
   - [ ] Add the threshold keys (warning and fail-closed per metric) to the `[dedup]` validation as explicitly
     allowed optional keys with an explicit `(low, high)` range and no numeric default — absent means unset —
     and keep them out of `_config_fingerprint()` (REQ-007; `scripts/shared/mcp_dedup_config.py`).
   - [ ] Create `scripts/shared/mcp_dedup_metrics.py` with the read-only counts, growth, WAL size, lock wait,
     lease health, and threshold status (REQ-004; `scripts/shared/mcp_dedup_metrics.py`).
   - [ ] Re-export the new names through the facade (REQ-004; `scripts/shared/mcp_dedup.py`).
   - [ ] Publish the metrics block through `make_health_response(...)`, extending its test with the
     metrics-block and degradation-path cases (REQ-004; `scripts/mcp_servers/health_response.py`,
     `tests/mcp_servers/test_health_response.py`).
   - [ ] Wire the read into the 10 handlers, with `scripts/mcp_servers/file/common.py` covering the three
     file servers (REQ-004; the 8 handler rows in `Implementation Target Files`).
   - [ ] Extend the three endpoint tests that assert the whole `details` dict by equality, keeping the
     `service` key unchanged (REQ-004; `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`,
     `tests/mcp_servers/github/test_github_server_endpoints.py`,
     `tests/mcp_servers/file/test_file_health_posture.py`).
   - [ ] Update the `[dedup]` key inventory and the health fields table (REQ-004, REQ-007;
     `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`).
   - [ ] Add the criteria rows, including the thresholds for the existing `Dedup Protection Degraded` row
     (REQ-005; `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`).
5. **Phase 5: Record the ADR resolution**
   - [ ] The conflict with ADR-008 was reported as `U-3` in `issues/20261123-120131_unknowns.md` and resolved
     by the repository owner (terminal-row-only scope) in `issues/20261123-120131_02_unknowns.md`; this Plan
     records that resolution and amends no ADR and writes no approval statement (REQ-006; no target row
     changes in this phase, so it is a recording step only).
6. **Phase 6: Deploy**
   - [ ] Commit and push first, then hand off to `skills/deploy/SKILL.md`; deploying is the user's decision
     and has an approval gate. `scripts/` and `config/` change, so this step is required (REQ-004, REQ-007;
     the `scripts/` rows above).

### Release units
**Unit**: matrix and its test | **Phases**: 1, 2, 3 | **Reason**: Phase 1 writes expectations that nothing executes yet, and Phase 3 is what makes them pass, so Phase 2 asserts behaviour Phase 3 defines and cannot be validated alone.
**Unit**: health exposure | **Phases**: 4 | **Reason**: the health-builder change and the 10 handler wirings cannot be validated alone, because the tests that assert the new `details` content cover both together; Phase 5 is a reporting step and Phase 6 is deployment, and neither is a unit member because neither can break a test.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Unit, driven from the matrix | `uv run python tools/check_docs_consistency.py` | Pass |
| `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Unit, criteria consistency | `uv run python tools/check_docs_consistency.py` | Pass |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Unit, payload contract | `uv run python tools/check_docs_consistency.py` | Pass |
| `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` | Generated reference | `uv run python tools/generate_reference_table.py --check` | Pass |
| `scripts/shared/mcp_dedup_metrics.py` | Unit | `uv run pytest tests/shared/test_mcp_dedup_metrics.py` | Pass, read-only |
| `scripts/shared/mcp_dedup_ledger.py` | Unit | `uv run pytest tests/shared/test_mcp_dedup.py` | Pass |
| `scripts/shared/mcp_dedup_config.py` | Unit | `uv run pytest tests/mcp_servers/test_config_isolation_fail_closed.py tests/shared/test_mcp_dedup.py` | Pass |
| `scripts/mcp_servers/health_response.py` and the 10 handlers | Unit, endpoint | `uv run pytest tests/mcp_servers/` | Pass |
| Import-layer contract | Static check | `uv run lint-imports --config .importlinter` | Pass, 6 contracts kept |
| Module size | Static check | `uv run python tools/check_module_size.py` | Pass |
| Full sequence | `rules/toolchain.md` (7 steps, in order) | as defined | All pass |

### Validation quality baseline

| Check | Command | Applicability | Current result | Result |
|---|---|---|---|---|
| Complexity | `radon cc <file> -s` | 3 Python targets run in Step 3 | `mcp_dedup.py` 12, `mcp_dedup_ledger.py` 7, `mcp_dedup_config.py` 5 | Pass |
| Dead code | `vulture scripts/ --min-confidence 80` | Any `scripts/` change | 13 findings, none in the target files | Pass |
| Security | `bandit -r scripts/ -c pyproject.toml` | Any `scripts/` change | 26 findings, none in the target files | Pass |
| Diff-scoped coverage | `rules/toolchain.md` section 7 | Any `scripts/` change | N/A: the baseline command ran, but the diff contains no lines with coverage information, so no current number exists. The Plan must raise it to `90`, the threshold in `rules/toolchain.md`'s Completion checklist, and a measurable value appears once the change is on disk. | Pass |

No row of this Plan changes the persisted schema, so `rules/persisted-schema-change.md` does not apply here,
and `tools/check_init_db_schema_gate.py`'s assertion stays as it is.

## Risks
- **Risk**: A state-dependent rule could contradict ADR-008 Decision Detail #23 and INV-09 → **Resolved**: the
  repository owner scoped retention to terminal rows only (`U-3`), which stays inside Decision Detail #23; no
  approval statement is written, and no target row changes the ADR in this Plan.
- **Risk**: Retaining unresolved states grows the store without bound, which ADR-008's disposable-cache
  classification already accepts → **Mitigation**: the criteria table makes it observable at the warning level;
  automatic action stays out of scope, and moving unresolved rows to a resolvable state belongs to
  `reconcile_execution()` and the mcpdl006 plan, not to this Plan.
- **Risk**: The issue's instruction to exclude unresolved states could be read as a change to the current
  implementation, which already never purges `pending` → **Mitigation**: the matrix states current behaviour as
  the baseline, so the only code change in the sweep is the legal-hold exclusion; the test written first asserts
  both.
- **Risk**: `tests/shared/test_mcp_dedup.py` pins the current purge and validation behaviour → **Mitigation**:
  it is a target row; the new expectation is added there in the same step as the validation change, and the
  existing assertions stay passing.
- **Risk**: 10 health handlers change while several tests assert the exact payload key set → **Mitigation**:
  new keys are added only through `make_health_response`, and the existing `details` assertions are for
  `service`, which is not replaced; key-set equality tests use `BASE_KEYS`, which stays unchanged.
- **Risk**: The metrics read can add latency to `/health` → **Mitigation**: it uses the store's existing
  connection and its `busy_timeout`, issues no write, and reports lock wait as an observation rather than
  issuing a statement that can block a writer.
- **Risk**: `scripts/mcp_servers/dispatch.py` has no room for new code under the size gate → **Mitigation**: no
  code is added there; the read lives in the new module and is called from the handlers.
- **Risk**: `scripts/shared/mcp_dedup_ledger.py` is also a target of the plan for mcpdl004, so the two changes
  together can approach the 24,576 B module-size gate → **Mitigation**: this plan adds no code to the ledger
  beyond the legal-hold condition in `purge_expired`; the read is placed in a new module, and the size gate is run as
  part of the validation sequence.
- **Risk**: `tests/deploy/test_init_db_schema_gate.py` counts config files and asserts the schema
  fingerprint → **Mitigation**: no new config file and no DDL change, so the counts and the fingerprint are
  unchanged; the reference row records it.

## Execution Status

Table structure and vocabulary: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the retention matrix first (REQ-001, REQ-003). | In Progress | — | — | Implementation procedures generated 20261123-144326; implementation owned by skills/code-implementation. |
| 2 | Tests written from the matrix, before the code (REQ-001, REQ-002, REQ-003, REQ-008). | In Progress | — | — | Implementation procedures generated 20261123-144326; implementation owned by skills/code-implementation. |
| 3 | Add the legal-hold exclusion to the terminal-only purge (REQ-002). | In Progress | — | — | Implementation procedures generated 20261123-144326; implementation owned by skills/code-implementation. |
| 4 | Threshold mechanism, metrics module, health wiring, criteria rows (REQ-004, REQ-005, REQ-007). | In Progress | — | — | Implementation procedures generated 20261123-144326; implementation owned by skills/code-implementation. |
| 5 | Record the ADR-008 resolution (REQ-006). | Completed | 2026-11-23 | 2026-11-23 | Reported in `issues/20261123-120131_unknowns.md`; resolved by the repository owner with terminal-row-only scope in `issues/20261123-120131_02_unknowns.md`; recorded in `U-3`, `REQ-002`, and `Assumptions`. |
| 6 | Deploy after commit and push (all). | Pending | — | — | User's decision; approval gate. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 5 | A state-dependent rule would change ADR-008 Decision Detail #23, and `docs/00_governance/governance_01_documentation-policy.md` requires a named approval record for a decision that changes an ADR, which this phase cannot create. | Yes | 2026-11-23 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| U-3 | 5 | Issue | Resolved | repository owner (`@lead`, RACI Model of `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`) | — |
| implementations/20261123-144326_01_docs_41_db_db_03_07_mcp-dedup-and-execution-snapshot.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261123-144326_02_docs_23_agent_agent_10_05_operations-and-observability-monitoring.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_03_docs_22_mcp_mcp_02_02_startup-modes-and-health.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_04_docs_22_mcp_mcp_06_01_configuration-file-inventory.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_05_scripts_shared_mcp_dedup_metrics.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_06_scripts_shared_mcp_dedup.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_07_scripts_shared_mcp_dedup_ledger.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-144326_08_scripts_shared_mcp_dedup_config.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_09_scripts_mcp_servers_health_response.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_10_scripts_mcp_servers_file_common.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_11_scripts_mcp_servers_cicd_cicd_server.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_12_scripts_mcp_servers_git_git_server.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_13_scripts_mcp_servers_github_github_server.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_14_scripts_mcp_servers_mdq_mdq_server.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_15_scripts_mcp_servers_rag_pipeline_rag_pipeline_server.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_16_scripts_mcp_servers_shell_shell_server.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_17_scripts_mcp_servers_web_search_web_search_server.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-144326_18_tests_shared_test_mcp_dedup.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261123-144326_20_tests_mcp_servers_test_health_response.py.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-120131
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`, `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`, `scripts/shared/mcp_dedup_metrics.py`, `scripts/shared/mcp_dedup.py`, `scripts/shared/mcp_dedup_ledger.py`, `scripts/shared/mcp_dedup_config.py`, `scripts/mcp_servers/health_response.py`, `scripts/mcp_servers/file/common.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/github/github_server.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/web_search/web_search_server.py`, `tests/shared/test_mcp_dedup.py`, `tests/shared/test_mcp_dedup_metrics.py`, `tests/mcp_servers/test_health_response.py`, `tests/mcp_servers/test_config_isolation_fail_closed.py`, `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, `tests/mcp_servers/github/test_github_server_endpoints.py`, `tests/mcp_servers/file/test_file_health_posture.py` — the full `File Path` list of `Implementation Target Files` above, now `Frozen`.

### Requirement Traceability

| Requirement ID | Source Issue Section or Evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Acceptance Criteria; the state table in `scripts/shared/mcp_dedup_schema.py` | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Phase 1 | AC-1 | `tests/shared/test_mcp_dedup.py` | Confirmed by repository evidence |
| REQ-001 | Implementation Intent, write the matrix first | `tests/shared/test_mcp_dedup.py` | Phase 2 | AC-1 | itself | Confirmed by repository evidence |
| REQ-001 | Classifications have no stored state (mcpdl006) | `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Phase 4 | AC-1, AC-5 | `uv run python tools/check_docs_consistency.py` | Needs confirmation |
| REQ-002 | Problem; Required Changes; the terminal-only condition in `purge_expired` | `scripts/shared/mcp_dedup_ledger.py` | Phase 3 | AC-2 | `tests/shared/test_mcp_dedup.py` | Confirmed by repository evidence |
| REQ-002 | Consumer scan, caller contract | `scripts/mcp_servers/dispatch.py` (reference row) | Phase 3 | AC-2 | `tests/mcp_servers/test_mcp_dispatch.py` | Confirmed by repository evidence |
| REQ-003 | Acceptance Criteria; no legal-hold mechanism exists; resolved as configuration-based in `U-2` | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Phase 1 | AC-3 | `tests/shared/test_mcp_dedup.py` | Derived from confirmed evidence |
| REQ-003 | Configuration-based hold, decided in this cycle | `scripts/shared/mcp_dedup_config.py` | Phase 4 | AC-3 | `tests/mcp_servers/test_config_isolation_fail_closed.py` | Derived from confirmed evidence |
| REQ-004 | Problem; Required Changes; the metrics list in `docs/41_db/db_08_active_databases.md` | `scripts/shared/mcp_dedup_metrics.py` | Phase 4 | AC-4 | `tests/shared/test_mcp_dedup_metrics.py` | Derived from confirmed evidence |
| REQ-004 | Facade re-export | `scripts/shared/mcp_dedup.py` | Phase 4 | AC-4 | `tests/shared/test_mcp_dedup_metrics.py` | Derived from confirmed evidence |
| REQ-004 | Health `details` mechanism | `scripts/mcp_servers/health_response.py` | Phase 4 | AC-4 | `tests/mcp_servers/test_health_response.py` | Confirmed by repository evidence |
| REQ-004 | 10 handlers with a `[dedup]` table, found by `grep` | `scripts/mcp_servers/cicd/cicd_server.py` | Phase 4 | AC-4 | `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Confirmed by repository evidence |
| REQ-004 | Shared health path for three servers | `scripts/mcp_servers/file/common.py` | Phase 4 | AC-4 | `tests/mcp_servers/file/test_file_health_posture.py` | Confirmed by repository evidence |
| REQ-004 | 10 handlers | `scripts/mcp_servers/git/git_server.py` | Phase 4 | AC-4 | `tests/mcp_servers/git/test_git_security_compliance.py` | Confirmed by repository evidence |
| REQ-004 | 10 handlers | `scripts/mcp_servers/github/github_server.py` | Phase 4 | AC-4 | `tests/mcp_servers/github/test_github_server_endpoints.py` | Confirmed by repository evidence |
| REQ-004 | 10 handlers | `scripts/mcp_servers/mdq/mdq_server.py` | Phase 4 | AC-4 | `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Confirmed by repository evidence |
| REQ-004 | 10 handlers | `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Phase 4 | AC-4 | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py` | Confirmed by repository evidence |
| REQ-004 | 10 handlers | `scripts/mcp_servers/shell/shell_server.py` | Phase 4 | AC-4 | `tests/mcp_servers/shell/test_shell_mcp_service.py` | Confirmed by repository evidence |
| REQ-004 | 10 handlers | `scripts/mcp_servers/web_search/web_search_server.py` | Phase 4 | AC-4 | `tests/mcp_servers/web_search/test_web_search_health.py` | Confirmed by repository evidence |
| REQ-004 | Exact-equality `details` assertion that the new content breaks | `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Phase 4 | AC-4 | itself | Confirmed by repository evidence |
| REQ-004 | Exact-equality `details` assertion that the new content breaks | `tests/mcp_servers/github/test_github_server_endpoints.py` | Phase 4 | AC-4 | itself | Confirmed by repository evidence |
| REQ-004 | Exact-equality `details` assertion that the new content breaks | `tests/mcp_servers/file/test_file_health_posture.py` | Phase 4 | AC-4 | itself | Confirmed by repository evidence |
| REQ-004 | Health payload documentation | `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Phase 4 | AC-4 | `uv run python tools/check_docs_consistency.py` | Confirmed by repository evidence |
| REQ-004 | Config-file inventory, required by `docs/22_mcp/mcp_00_document-guide.md` | `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` | Phase 4 | AC-4, AC-7 | `uv run python tools/generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-005 | Acceptance Criteria, unbounded growth | `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Phase 4 | AC-5 | `uv run python tools/check_docs_consistency.py` | Confirmed by repository evidence |
| REQ-006 | AI Implementation Instruction, report the conflict; ADR Decision Details #23; owner resolution recorded in `issues/20261123-120131_02_unknowns.md` | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (reference row) | Phase 5 | AC-6 | `uv run python tools/check_docs_consistency.py` | Derived from confirmed evidence |
| REQ-007 | Threshold values not defined; mechanism only | `scripts/shared/mcp_dedup_config.py` | Phase 4 | AC-7 | `tests/mcp_servers/test_config_isolation_fail_closed.py` | Derived from confirmed evidence |
| REQ-008 | Read-only metrics path, no schema change | `tests/shared/test_mcp_dedup_metrics.py` | Phase 2 | AC-8 | itself | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261123-144326 -->
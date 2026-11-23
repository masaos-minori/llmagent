## Goal
- Make the dedup retention rule state-dependent, define the legal-hold boundary, and give operators a
  read-only view of the store's state counts, growth, WAL size, lock wait, lease health, and threshold
  status, exposed through the existing health `details` block of the 10 servers that have a `[dedup]`
  table.

## Priority
Medium

## Scope
- **In-Scope**:
  - The retention matrix, mapping each state and result classification to its retention behaviour,
    including the classifications that have no stored status today.
  - The legal-hold boundary: which rows the sweep excludes, and how held rows appear in counts.
  - `scripts/shared/mcp_dedup_metrics.py` (new, read-only): per-status counts, growth, WAL size, lock
    wait, lease health, threshold status.
  - The threshold mechanism: per-metric warning and fail-closed keys in the `[dedup]` table. Values are
    operator-supplied and are not defined by this Plan (`U-1`).
  - Health exposure through `scripts/mcp_servers/health_response.py` and the 10 server handlers that have
    a `[dedup]` table.
  - Monitoring criteria rows for the store, including the `Dedup Protection Degraded` row's thresholds.
  - The conflict this change introduces with ADR-008, reported as an open decision.
- **Out-of-Scope**:
  - Automatic restart, automatic escalation, automatic purge action. The threshold decision stays a
    documented operator action.
  - A new status service or endpoint.
  - Alert delivery, which has no source in the repository.
  - Threshold values.
  - A `legal_hold` column, which would change the persisted schema.
  - `docs/11_req/*`, and `docs/13_ref/*`, which is generated from code and must not be edited by hand.
- **Dependencies**: N/A: none. No ordering is asserted here. `check_plan_target_overlaps.py` reports three
  shared target rows with the plan for mcpdl004, and the plan for mcpdl006 needs this Plan's matrix; both are
  recorded in `Assumptions`, and the owner decides the order.

## Background
The issue exists because "delete after 14 days" is wrong for a durable ledger, and because no operator can
tell whether an unresolved state is expected, stuck, or growing. `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
`## Context` classifies the dedup store as a disposable cache with a retention window, while the same
document's Decision Details and Consequences describe it as a durable execution ledger with lease
ownership. That contradiction is what makes a single retention period ambiguous.

## Problem
`scripts/shared/mcp_dedup_ledger.py::purge_expired` deletes only rows whose `status` is `completed`,
`failed`, or `interrupted` and whose `updated_epoch` is past the cutoff; `pending` rows are never deleted
there. So a row left `pending` by a crash is retained forever, and
`docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` has no criteria saying what is
normal, degraded, or action-required for that store. No read path reports counts, growth, WAL size, lock
wait, or lease health.

`call_attempt_history` keeps no state; it records results, so its retention cannot be decided by state
(`U-5`). Whether an unresolved state is an in-flight record, a retained exception, or an item requiring
operator action is not decided anywhere.

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
- Report the ADR conflict; do not write an approval statement for it.

## Requirements
- `REQ-001`: Define the retention matrix per state and result classification, mapping each classification
  to the stored status it corresponds to, and state for each whether retention applies.
- `REQ-002`: Make the purge rule state-dependent: terminal states are purged past the retention window,
  unresolved states are not.
- `REQ-003`: Define the legal-hold boundary as a configuration entry, and state how held rows appear in
  counts.
- `REQ-004`: Add a read-only metrics module reporting per-status counts, growth, WAL size, lock wait,
  lease health, and threshold status, and publish it through the existing health `details` block for the 10
  servers that have a `[dedup]` table.
- `REQ-005`: Define the warning-level monitoring criteria for those metrics, including the unbounded growth
  a state-dependent rule permits, and keep automatic action out of scope.
- `REQ-006`: Report the conflict with ADR-008's Decision Details as an open decision; do not write an
  approval statement.
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
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | The retention matrix and the state-dependent rule, written first. The file already documents the retention sweep, so the matrix belongs in it rather than in a new file. | REQ-001, REQ-003; AC-1, AC-3 | `docs/41_db/db_00_document-guide.md` lists it; the retention-sweep paragraph was read, and the file has 10 changes in 30 days, the highest of the targets. (checked in Step 3) | `tests/shared/test_mcp_dedup.py` | Verified |
| `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Modify | The monitoring criteria rows for the store, and the thresholds for the existing `Dedup Protection Degraded` row. | REQ-005; AC-5 | Read in full in Step 3: the table has no criteria rows for this store, and the `Dedup Protection Degraded` row is already there. | `tests/mcp_servers/test_config_isolation_import.py` | Verified |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Modify | The `details` content for the 10 wired servers. | REQ-004; AC-4 | Read in Step 3; it defines the health payload and the per-server `details` table, and `docs/22_mcp/mcp_00_document-guide.md` lists it. | `tests/mcp_servers/test_health_response.py` | Verified |
| `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` | Modify | The `[dedup]` key inventory for the new threshold keys. | REQ-007; AC-7 | Read in Step 3; `docs/22_mcp/mcp_00_document-guide.md` requires the inventory, and the file already lists the `[dedup]` keys. | `tests/mcp_servers/test_config_isolation_import.py` | Verified |
| `scripts/shared/mcp_dedup_metrics.py` | Create | New read-only metrics module: counts, growth, WAL size, lock wait, lease health, threshold status. | REQ-004, REQ-008; AC-4, AC-8 | New module. `scripts/shared/mcp_dedup_health.py`'s read-only guard and `scripts/mcp_servers/web_search/metrics.py`'s placement are the existing patterns; the import contract keeps `scripts/shared/` a leaf, so it cannot import `mcp_servers`. (checked in Step 3) | `tests/shared/test_mcp_dedup_metrics.py` | Verified |
| `scripts/shared/mcp_dedup.py` | Modify | Re-export the new module's public names through the facade. | REQ-004; AC-4 | `scripts/shared/mcp_dedup.py` imports `shared.mcp_dedup_config` and `shared.mcp_dedup_ledger` and re-exports their names; the WAL pragma is at line 169, not 271 as the issue states, and `purge_expired` is not in this file. (checked in Step 2) | `tests/shared/test_mcp_dedup.py` | Verified |
| `scripts/shared/mcp_dedup_ledger.py` | Modify | `purge_expired` becomes state-dependent. | REQ-002; AC-2 | Read in full in Step 2: the terminal-only `DELETE` and the "pending rows are never purged here" line were confirmed. | `tests/shared/test_mcp_dedup.py` | Verified |
| `scripts/shared/mcp_dedup_config.py` | Modify | The threshold keys and their validation range; no default value is added. | REQ-003, REQ-007; AC-3, AC-7 | Read in Step 3: `_RANGES` validates `retention_days` and the other keys, so the thresholds extend the same contract. | `tests/mcp_servers/test_config_isolation_fail_closed.py` | Verified |
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
| `tests/mcp_servers/test_config_isolation_import.py` | Modify | The `[dedup]` key set it asserts per config file. | REQ-003, REQ-007; AC-3, AC-7 | Read in Step 3; it asserts key sets per file. | itself | Verified |
| `tests/mcp_servers/test_config_isolation_fail_closed.py` | Modify | A threshold value outside the validation range must fail closed, as the other `[dedup]` keys do. | REQ-007; AC-7 | Read in Step 3. | itself | Verified |
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Modify | It asserts `body["details"] == {"service": "cicd-mcp"}`, an exact-equality assertion that the new `details` content breaks, so the expectation is extended here. | REQ-004; AC-4 | Read in Step 3, line 255. | itself | Verified |
| `tests/mcp_servers/github/test_github_server_endpoints.py` | Modify | The same exact-equality assertion, at lines 188 and 200. | REQ-004; AC-4 | Read in Step 3. | itself | Verified |
| `tests/mcp_servers/file/test_file_health_posture.py` | Modify | It asserts `body["details"] == {}` for the file servers, so the expectation is extended here. | REQ-004; AC-4 | Read in Step 3, line 149. | itself | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | The source of the conflict this Plan reports. It is not modified by this Plan: `docs/00_governance/governance_01_documentation-policy.md` requires a named approval record for a decision that changes an ADR, and this phase cannot create one, so its Decision Details and INV-09 stay as they are until the repository owner decides. | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`; REQ-006, `U-3` |
| `scripts/shared/mcp_dedup_schema.py` | The `status` `CHECK` and `START_STATES`/`TERMINAL_STATES` the matrix must map to; the matrix cannot name a state the schema does not allow. | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`; REQ-001 |
| `scripts/shared/mcp_dedup_health.py` | The read-only guard the new module follows, and the existing `pending`-is-degraded check the criteria table must stay consistent with. | `scripts/shared/mcp_dedup_metrics.py`; REQ-004, REQ-005 |
| `scripts/shared/mcp_dedup_cli.py` | `cmd_purge` is a consumer of the changed rule; the scan found it and it is confirmed not affected. | `scripts/shared/mcp_dedup_ledger.py`; REQ-002 |
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
| `docs/10_adr/adr_02_05_011_adr-authoring-and-status.md` | The requirement that an open decision be recorded as a `## Needs Confirmation` section, not as a present-tense decision. | REQ-006 |
| `docs/41_db/db_08_active_databases.md` | The metrics list the new read must stay consistent with. | `scripts/shared/mcp_dedup_metrics.py`; REQ-004 |
| `docs/11_req/req_01_11_mcp-dedup-state-machine.md` | The existing state table the classification mapping must not contradict; out of scope for change. | REQ-001 |
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
- AC-6 (REQ-006): the conflict with ADR-008 is reported as an open decision; no approval statement is
  written.
- AC-7 (REQ-007): the threshold keys and their validation range are defined, and no numeric value is
  introduced by this Plan.
- AC-8 (REQ-008): the metrics path performs no write, no migration, and no new service.

## Tests
- REQ-001, REQ-002, REQ-003 — `tests/shared/test_mcp_dedup.py` (unit): matrix-shaped tests written
  before the code. Terminal rows past the retention are purged; a retained unresolved state is not; a held
  row is not. `TestTtlPurge` is extended, not replaced.
- REQ-003, REQ-007 — `tests/mcp_servers/test_config_isolation_fail_closed.py` (unit): the new `[dedup]`
  keys are validated against the existing range contract, and a value outside it fails closed. There is no
  `tests/shared/test_mcp_dedup_config.py` in the repository, so this is where the contract is tested.
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
- REQ-003 — `tests/mcp_servers/test_config_isolation_import.py` (unit): the per-file `[dedup]` key sets
  include the new keys.
- REQ-005 — `tests/deploy/test_init_db_schema_gate.py` (integration, marked `integration`): the config-file
  count expectation and the schema fingerprint stay unchanged.

## Documentation Impact
- `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` — REQ-001, REQ-003: the retention matrix and
  the state-dependent rule; the existing retention-sweep paragraph must say the same as the code.
- `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` — REQ-005: the criteria rows. No
  `## Needs Confirmation` subsection is required there, because the threshold values are recorded as an open
  decision in the Plan's Unknowns table, not as an unresolved claim in the document.
- `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` — REQ-004: the health `details` content for the
  wired servers.
- `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` — REQ-007: the `[dedup]` key inventory, which
  `docs/22_mcp/mcp_00_document-guide.md` requires.
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` — REQ-006: the conflict is reported as an open
  decision. `docs/10_adr/adr_02_05_011_adr-authoring-and-status.md` requires a `## Needs Confirmation`
  section for an open decision, and the ADR already has one; the wording is not changed here.

## Assumptions
- The metrics module is read-only; no write and no migration.
- The metrics read is not a separate status service; it is exposed through the health `details` block.
- `config/*.toml` files are not committed, so their per-server `[dedup]` content cannot be a row; the
  config-file inventory is documented through `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`.
- Threshold values are operator-supplied; the Plan defines the mechanism only.
- Legal hold is configuration-based, per the decision recorded in this cycle, not a schema change.
- The 10 servers with a `[dedup]` table are the whole scope of the health wiring; `scripts/shared/mcp_dedup_cli.py`
  is not a server and is not wired.
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

## Unknowns

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? |
|----|---------------------|----------------|-----------------|-----------|
| U-1 | Threshold values for capacity, lock wait, heartbeat delay, and unresolved-state backlog. | No defined thresholds exist in the repository; `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` has no criteria rows for this store. | Operator-supplied config values through the mechanism REQ-007 defines. Ask the repository owner for the values, or record them when the criteria table is filled. | False |
| U-2 | Whether legal hold is legal or operational. | No legal-hold mechanism exists in the repository; the nearest precedent is `/memory prune` excluding `pinned`. | Resolved as configuration-based, which keeps the persisted schema unchanged. If it is later decided to be a stored column, the persisted-schema gate and the config fingerprint apply, and it needs an ADR decision because it changes the disposable-cache classification. Re-check then. | False |
| U-3 | A state-dependent rule changes ADR-008 Decision Detail #23, which defines retention as terminal rows past the retention, and conflicts with the unbounded-growth acceptance in INV-09 for a store classified as a disposable cache. | No approval record or decision exists that permits retaining non-terminal states in a disposable-cache store. `docs/00_governance/governance_01_documentation-policy.md` requires a named approval record for a decision that changes an ADR, and this phase cannot create one. | Reported, not resolved, per this issue's instruction, in `issues/20261123-120131_unknowns.md`. The repository owner decides: amend the ADR, or bound unresolved-state growth another way. | True |
| U-4 | Whether the metrics read is exposed through `/health`, a new endpoint, or a runbook command. | None: resolved by evidence. The health `details` mechanism is defined and mdq-mcp already publishes counts, so no new status service is needed. | Confirmed by repository evidence; recorded as the design decision in `Design`. | False |
| U-5 | `call_attempt_history` has no state, so its retention cannot be decided by the matrix. | None: the issue itself states this. | The matrix states the history rule separately from the state rows. | False |
| U-6 | The three result classifications have no observable state, so the matrix cannot assign them retention behaviour as states. | `docs/11_req/req_01_11_mcp-dedup-state-machine.md`'s state table does not include them. | mcpdl006 defines those states; this Plan's mapping is applied to that set. Recorded in `Assumptions` as a shared-target overlap, not as an ordering. | False |
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
| `tests/mcp_servers/test_config_isolation_import.py` | Modify | Low | 0 | N/A: `git-fame` is not installed | tests-only |
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
The mechanism is config-supplied warning and fail-closed thresholds per metric, validated with the same
range contract as `scripts/shared/mcp_dedup_config.py::_RANGES` and reported as a status per metric. The
values are not defined here (`U-1`); nothing in this Plan hard-codes a number.

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
- `scripts/shared/mcp_dedup_cli.py` (`cmd_purge`), `scripts/shared/mcp_dedup_health.py` (`check_store`) —
  reference rows, `not affected: both read the store and do not call purge_expired`; `check_store` already
  reports `pending` as degraded, which the criteria table must stay consistent with.
- `scripts/db/maintenance.py` — `not affected: its own `retention_days` rule is not the dedup sweep`.
- `scripts/shared/config_loader.py` — `not affected: the loader does not validate keys`; the validation row is
  `scripts/shared/mcp_dedup_config.py`.
- `tests/shared/test_mcp_dedup.py`, `tests/mcp_servers/test_mcp_dispatch.py`,
  `tests/mcp_servers/test_health_response.py`, `tests/mcp_servers/test_config_isolation_fail_closed.py` — rows.

### Predictable fallout
- Module size: `scripts/mcp_servers/dispatch.py` is 3 bytes under the gate, so no code is added there and no
  split row is created; the new module is the split.
- Pinned counts and pinned payload content: `tests/mcp_servers/test_config_isolation_import.py` asserts the
  `[dedup]` key set per config file, `tests/deploy/test_init_db_schema_gate.py` asserts the config-file
  count, and three endpoint tests assert the whole `details` dict by equality
  (`tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, `tests/mcp_servers/github/test_github_server_endpoints.py`,
  `tests/mcp_servers/file/test_file_health_posture.py`); the first and the last three are target rows, and the
  config-file count is unchanged because no config file is added.
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
     stored state, each mapped to its stored status, plus the `call_attempt_history` row that states the
     history rule cannot be decided by state (REQ-001; `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`).
   - [ ] Add the legal-hold column and define what is excluded (REQ-003; `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`).
   - [ ] Write each row from the behaviour the test will assert, so the document is the source of the test
     expectation and not a description of the code after the change (REQ-001; `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`).
2. **Phase 2: Tests from the matrix**
   - [ ] Extend `TestTtlPurge`: terminal rows past the retention are purged, a retained unresolved state is
     not, a held row is not (REQ-001, REQ-002, REQ-003; `tests/shared/test_mcp_dedup.py`).
   - [ ] Add `tests/shared/test_mcp_dedup_metrics.py`: the read returns the documented fields for a store
     with rows in each state and issues no write (REQ-004, REQ-008; `tests/shared/test_mcp_dedup_metrics.py`).
3. **Phase 3: Change the purge**
   - [ ] Make `purge_expired` state-dependent: terminal rows past the retention, unresolved rows retained,
     held rows excluded (REQ-002; `scripts/shared/mcp_dedup_ledger.py`).
   - [ ] Keep the caller contract in `scripts/mcp_servers/dispatch.py` unchanged, including the
     once-per-process flag and the degradation behaviour (REQ-002; `scripts/mcp_servers/dispatch.py` is not a
     target row, so this item changes nothing and is guarded by `tests/mcp_servers/test_mcp_dispatch.py`).
   - [ ] Make the document say the same as the code (REQ-002; `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`).
4. **Phase 4: Threshold mechanism and metrics module**
   - [ ] Add the warning and fail-closed keys to the `[dedup]` validation with the existing range contract;
     no default value is added (REQ-007; `scripts/shared/mcp_dedup_config.py`).
   - [ ] Create `scripts/shared/mcp_dedup_metrics.py` with the read-only counts, growth, WAL size, lock wait,
     lease health, and threshold status (REQ-004; `scripts/shared/mcp_dedup_metrics.py`).
   - [ ] Re-export the new names through the facade (REQ-004; `scripts/shared/mcp_dedup.py`).
   - [ ] Publish the metrics block through `make_health_response(...)` (REQ-004; `scripts/mcp_servers/health_response.py`).
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
5. **Phase 5: Report the ADR conflict**
   - [ ] Report the conflict with ADR-008 as `U-3` in `issues/20261123-120131_unknowns.md`, written from the
     plan, and do not write an approval statement (REQ-006; no target row changes this phase, so it is a
     reporting step only).
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
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Unit, driven from the matrix | `uv run python tools/check_document_consistency.py` | Pass |
| `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Unit, criteria consistency | `uv run python tools/check_document_consistency.py` | Pass |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Unit, payload contract | `uv run python tools/check_document_consistency.py` | Pass |
| `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` | Generated reference | `uv run python tools/generate_reference_table.py --check` | Pass |
| `scripts/shared/mcp_dedup_metrics.py` | Unit | `uv run pytest tests/shared/test_mcp_dedup_metrics.py` | Pass, read-only |
| `scripts/shared/mcp_dedup_ledger.py` | Unit | `uv run pytest tests/shared/test_mcp_dedup.py` | Pass |
| `scripts/shared/mcp_dedup_config.py` | Unit | `uv run pytest tests/mcp_servers/test_config_isolation_fail_closed.py tests/mcp_servers/test_config_isolation_import.py` | Pass |
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
- **Risk**: A state-dependent rule contradicts ADR-008 Decision Detail #23 and INV-09 → **Mitigation**: report
  the conflict as `U-3` and ask the repository owner; no approval statement is written, and no target row
  changes the ADR in this Plan.
- **Risk**: Retaining unresolved states grows the store without bound, which is the same decision that makes
  retention state-dependent → **Mitigation**: the criteria table makes it observable at the warning level;
  automatic action stays out of scope, and the growth risk remains a reported consequence.
- **Risk**: The issue's instruction not to purge unresolved states conflicts with the current implementation,
  which never purges `pending` at all → **Mitigation**: the matrix states current behaviour as the baseline, so
  the change is the exception path, not a rewrite of the terminal rule; the test written first asserts both.
- **Risk**: `tests/shared/test_mcp_dedup.py` and `tests/mcp_servers/test_config_isolation_import.py` pin the
  current behaviour and key set → **Mitigation**: both are target rows; the new expectation is added there in
  the same step as the validation change.
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
  beyond the state condition in `purge_expired`; the read is placed in a new module, and the size gate is run as
  part of the validation sequence.
- **Risk**: `tests/deploy/test_init_db_schema_gate.py` counts config files and asserts the schema
  fingerprint → **Mitigation**: no new config file and no DDL change, so the counts and the fingerprint are
  unchanged; the reference row records it.

## Execution Status

Table structure and vocabulary: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the retention matrix first (REQ-001, REQ-003). | Pending | — | — | |
| 2 | Tests written from the matrix, before the code (REQ-001, REQ-002, REQ-003, REQ-008). | Pending | — | — | |
| 3 | Make the purge state-dependent (REQ-002). | Pending | — | — | |
| 4 | Threshold mechanism, metrics module, health wiring, criteria rows (REQ-004, REQ-005, REQ-007). | Pending | — | — | |
| 5 | Report the ADR conflict (REQ-006). | Blocked | — | — | Blocked by `U-3`; reported, not resolved. |
| 6 | Deploy after commit and push (all). | Pending | — | — | User's decision; approval gate. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 5 | A state-dependent rule changes ADR-008 Decision Detail #23, and `docs/00_governance/governance_01_documentation-policy.md` requires a named approval record for a decision that changes an ADR, which this phase cannot create. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| U-3 | 5 | Issue | Open | repository owner (`@lead`, RACI Model of `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`) | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-120131
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`, `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`, `scripts/shared/mcp_dedup_metrics.py`, `scripts/shared/mcp_dedup.py`, `scripts/shared/mcp_dedup_ledger.py`, `scripts/shared/mcp_dedup_config.py`, `scripts/mcp_servers/health_response.py`, `scripts/mcp_servers/file/common.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/github/github_server.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/web_search/web_search_server.py`, `tests/shared/test_mcp_dedup.py`, `tests/shared/test_mcp_dedup_metrics.py`, `tests/mcp_servers/test_health_response.py`, `tests/mcp_servers/test_config_isolation_import.py`, `tests/mcp_servers/test_config_isolation_fail_closed.py`, `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, `tests/mcp_servers/github/test_github_server_endpoints.py`, `tests/mcp_servers/file/test_file_health_posture.py` — the full `File Path` list of `Implementation Target Files` above, now `Frozen`.

### Requirement Traceability

| Requirement ID | Source Issue Section or Evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Acceptance Criteria; the state table in `scripts/shared/mcp_dedup_schema.py` | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Phase 1 | AC-1 | `tests/shared/test_mcp_dedup.py` | Confirmed by repository evidence |
| REQ-001 | Implementation Intent, write the matrix first | `tests/shared/test_mcp_dedup.py` | Phase 2 | AC-1 | itself | Confirmed by repository evidence |
| REQ-001 | Classifications have no stored state (mcpdl006) | `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Phase 4 | AC-1, AC-5 | `tests/mcp_servers/test_config_isolation_import.py` | Needs confirmation |
| REQ-002 | Problem; Required Changes; the terminal-only condition in `purge_expired` | `scripts/shared/mcp_dedup_ledger.py` | Phase 3 | AC-2 | `tests/shared/test_mcp_dedup.py` | Confirmed by repository evidence |
| REQ-002 | Consumer scan, caller contract | `scripts/mcp_servers/dispatch.py` (reference row) | Phase 3 | AC-2 | `tests/mcp_servers/test_mcp_dispatch.py` | Confirmed by repository evidence |
| REQ-003 | Acceptance Criteria; no legal-hold mechanism exists | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Phase 1 | AC-3 | `tests/shared/test_mcp_dedup.py` | Needs confirmation |
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
| REQ-004 | Health payload documentation | `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Phase 4 | AC-4 | `uv run python tools/check_document_consistency.py` | Confirmed by repository evidence |
| REQ-004 | Config-file inventory, required by `docs/22_mcp/mcp_00_document-guide.md` | `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` | Phase 4 | AC-4, AC-7 | `uv run python tools/generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-005 | Acceptance Criteria, unbounded growth | `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Phase 4 | AC-5 | `tests/mcp_servers/test_config_isolation_import.py` | Confirmed by repository evidence |
| REQ-006 | AI Implementation Instruction, report the conflict; ADR Decision Details | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (reference row) | Phase 5 | AC-6 | `uv run python tools/check_document_consistency.py` | Needs confirmation |
| REQ-007 | Threshold values not defined; mechanism only | `scripts/shared/mcp_dedup_config.py` | Phase 4 | AC-7 | `tests/mcp_servers/test_config_isolation_fail_closed.py` | Derived from confirmed evidence |
| REQ-008 | Read-only metrics path, no schema change | `tests/shared/test_mcp_dedup_metrics.py` | Phase 2 | AC-8 | itself | Confirmed by repository evidence |

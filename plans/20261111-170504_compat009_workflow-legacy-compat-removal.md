## Goal
- Remove the single-valued `FailurePolicy` indirection from the MCP server configuration and the startup readiness report, and remove the retained-database compatibility tests and the `legacy_recovered` test fallout that the already-planned lease-less recovery removal does not cover, so that no workflow or MCP compatibility leftover remains outside that other plan's scope. The lease-less recovery removal in `scripts/agent/workflow/state_store.py` itself is owned by the archived adrrev005 plan and is not repeated here.

## Priority
Medium

## Scope
- **In-Scope**:
  - `REQ-001`: remove `FailurePolicy`, `McpServerConfig.failure_policy`, its parsing, its use in the readiness warning, the test name that refers to it, and its documentation bullet.
  - `REQ-002`: remove the lease-less age dependence and the `legacy_recovered` assertions from `tests/agent/workflow/test_state_store.py` (a fallout of the adrrev005 lease-less removal that none of its procedures names).
  - `REQ-003`: remove the two retained-database compatibility tests (legacy composite task key, legacy snapshot column) from `tests/agent/workflow/test_workflow_state_store.py`.
  - `REQ-004`: completion checks (`tools/check_compat_shims.py`, zero-caller `rg`, documentation and toolchain gates).
- **Out-of-Scope**:
  - The lease-less legacy recovery branch, `_LEGACY_STALE_AGE_SEC`, the `legacy_recovered` field, the legacy-age cases of `tests/agent/workflow/test_workflow_state_store.py` and `tests/agent/workflow/test_stale_recovery_lease.py`, and the ADR and DB document wording about lease-less recovery. These belong to the archived adrrev005 plan (`REQ-004`, `REQ-006`), whose procedures for `state_store.py`, both test files, and the documents are still `Pending`.
  - Changing the optional `lease_duration_sec` parameter of `begin_stage_if_new` (see UNK-01).
  - RAG, EventBus, history-comment, and checker items owned by `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md` through `issues/20261110-171157_rmcompat008_compat-checker-patterns.md`.
  - `ToolConfig.tool_definitions` consumers and `scripts/shared/tool_constants.py` comments (owned by `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md` and `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`).
  - WAL, mode, and Memory compatibility cleanup (see UNK-04).
- **Dependencies**: Fix order for this Plan: `REQ-001` is independent of every other item. `REQ-002` and `REQ-003` edit test files that the adrrev005 procedures also edit or whose behavior they change, so they follow adrrev005 phase 4. `plans/20261111-110144_adrrev017_docs-history-wording.md` edits ADR-001 wording and no file of this Plan, so no ordering applies to it. `issues/20261110-171040_rmcompat007_history-comment-sweep.md` runs after this Plan. `issues/20261111-163819_wfrecov001_adr001-recovery-reconciliation.md` describes the recovery rule that adrrev005 and this Plan finish.
  - **Depends on**: plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md | phase 4 | its lease-less removal (procedures 11, 29, 30 in `implementations/`) must land before `REQ-003` edits the same test file and before the `legacy_recovered` field disappears

## Background
The Issue (`issues/20261111-163923_compat009_workflow-legacy-compat-removal.md`) asks to remove workflow-recovery compatibility code and the single-valued `FailurePolicy`. Step 2 verification against current source changed its scope:

- The lease-less legacy recovery branch (`_LEGACY_STALE_AGE_SEC`, `legacy_recovered`) is confirmed in `scripts/agent/workflow/state_store.py`, but the Issue's claim that no open plan covers it is wrong. The archived adrrev005 plan lists it as `REQ-004`, and its implementation procedures for `state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`, and `tests/agent/workflow/test_stale_recovery_lease.py` are `Pending` in `implementations/`. adrrev005's Execution Status shows phase 4 `In Progress`. This Plan therefore does not plan that removal again.
- `tests/agent/workflow/test_state_store.py` also asserts the legacy rule (a lease-less row older than the legacy age is recovered and reports `legacy_recovered`) and is not a target of any adrrev005 procedure, so it would fail once the field is removed.
- `FailurePolicy` is confirmed single-valued: the enum has one member, the `McpServerConfig.failure_policy` field is documented as reserved, and `docs/22_mcp` states nothing branches on it.
- Two retained-database compatibility tests exist in `tests/agent/workflow/test_workflow_state_store.py` and are not named by adrrev005's procedure for that file.
- The Issue's memo path `tests/test_workflow_state_store.py` does not exist; the real path is `tests/agent/workflow/test_workflow_state_store.py`. The WAL module path in the memo (`scripts/db/wal_checkpoint_manager.py`) does not exist either.

## Problem
- `FailurePolicy` adds an enum, a config field, a parse step, and a log suffix for a policy that has exactly one value and that no code branches on.
- Retained-database tests pin behavior for pre-current-schema data (a composite-style task key and an unused snapshot column), which contradicts the current-schema-only policy.
- `tests/agent/workflow/test_state_store.py` depends on the lease-less age rule that adrrev005 removes, so adrrev005's `state_store.py` change would break it with no procedure assigned to fix it.

## Reason for Change
The recovery transaction is being documented and simplified (adrrev005, the ADR-001 issue). Removing the remaining test dependencies and the unused `FailurePolicy` indirection at the same time avoids a broken test file after adrrev005 lands and avoids leaving a second dead abstraction. No deadline exists; priority is Medium maintainability work.

## Implementation Intent
- Delete `FailurePolicy` outright (no alias, no shim), and let the readiness warning list unavailable servers by key only.
- Rewrite the `test_state_store.py` recovery cases to use lease-bearing rows so they test the lease-based rule only, and delete the two retained-database compatibility tests.
- Leave `state_store.py`, `idempotency_ops.py`, and `tests/agent/workflow/test_stale_recovery_lease.py` untouched; adrrev005 owns them.
- Use `tools/check_compat_shims.py` and zero-caller `rg` searches as the completion check.

## Requirements
- `REQ-001`: Remove the `FailurePolicy` enum, `McpServerConfig.failure_policy`, its parsing in `_build_single_server`, the `getattr(..., "failure_policy", None)` suffix in the readiness warning, the test name that refers to it, and the `failure_policy` bullet in the MCP server configuration reference. A stale `failure_policy` key in an existing `agent.toml` MUST still load (ignored).
- `REQ-002`: In `tests/agent/workflow/test_state_store.py`, replace lease-less seeded rows with lease-bearing rows and remove every `legacy_recovered` assertion and the `legacy` error-message assertion, keeping the lease-expiry, live-lease, compare-and-swap, and reconciliation cases.
- `REQ-003`: Remove `test_retained_db_compatibility` and `test_lifecycle_works_on_legacy_shape_with_unused_snapshot_column` from `tests/agent/workflow/test_workflow_state_store.py`.
- `REQ-004`: `uv run python tools/check_compat_shims.py` passes, `rg` finds no `FailurePolicy` or `failure_policy` outside work items, no `legacy_recovered` remains in `tests/agent/workflow/test_state_store.py`, and no file owned by adrrev005 is modified by this Plan.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/mcp_config.py` | MCP server configuration model and parser | Delete the `FailurePolicy` enum, the `McpServerConfig.failure_policy` field, and the `FailurePolicy(...)` call in `_build_single_server`; keep `StrEnum` for `TransportType` | `REQ-001`, AC-1, AC-2 | `class FailurePolicy(StrEnum)` has only `FAIL_FAST`; the field comment says "currently single-valued (FAIL_FAST) with no branching"; consumer scan lists no other script reader (checked in Step 3) | `tests/shared/test_mcp_config.py`, `tests/shared/test_mcp_config_validation.py` | Verified |
| `scripts/agent/startup_reporter.py` | Readiness warning text | Remove the `getattr(cfg_entry, "failure_policy", None)` lookup so `ReadinessReporter` lists unavailable servers by key only | `REQ-001`, AC-1, AC-2 | `ReadinessReporter` builds `f"{key} ({policy})"` from that lookup; the consumer scan lists it as the only other script reader (checked in Step 3) | `tests/agent/test_startup_reporter.py`, `tests/agent/test_startup.py` | Verified |
| `tests/agent/test_startup.py` | Startup readiness test | Rename `test_excluded_tools_log_includes_failure_policy` to describe what it asserts (excluded server keys are listed); its assertions never check the policy text | `REQ-001`, AC-2 | The test asserts "Excluded tools (unavailable)", "srv1", and "srv2" only (checked in Step 3) | itself | Verified |
| `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` | MCP server configuration field reference | Remove the `failure_policy` bullet (a documented field that no longer exists) | `REQ-001`, AC-1 | The bullet states the field is reserved and that only `fail-fast` exists; it is the only `docs/` mention of `failure_policy` (checked in Step 3) | `tools/check_docs_consistency.py --domain mcp` | Verified |
| `tests/agent/workflow/test_state_store.py` | Real-DB recovery tests | Seed lease-bearing rows in `test_recover_single_stale_attempt` and `test_recover_non_stale_attempt_not_changed`, drop the `legacy` message assertion and every `legacy_recovered` assertion | `REQ-002`, AC-3 | `test_recover_single_stale_attempt` asserts `"legacy"` in `error_msg` and `(report.recovered, report.legacy_recovered) == (1, 1)`; the expired-lease test asserts `(1, 0)`; no adrrev005 procedure targets this file (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_state_store.py` | State-store unit tests | Delete `test_retained_db_compatibility` (pre-existing composite-key row) and `test_lifecycle_works_on_legacy_shape_with_unused_snapshot_column` (legacy table and column shape) | `REQ-003`, AC-4 | The first test is in `TestCreateTask` and the second in `TestToolCallStateOps`; both build legacy data by hand; `snapshot_id` is absent from `scripts/db/schema_sql.py` and the workflow schema service; the adrrev005 procedure for this file names the legacy-age cases only (checked in Step 3) | itself | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/state_store.py` | Shows `RecoveryReport` and the lease-less branch that adrrev005 removes; confirms what `last_recovery_report` still carries when `REQ-002` lands | `REQ-002`, `tests/agent/workflow/test_state_store.py` |
| `scripts/agent/workflow/idempotency_ops.py` | `begin_stage_if_new` keeps an optional `lease_duration_sec`; read to judge UNK-01 | `REQ-002` |
| `tests/agent/workflow/test_stale_recovery_lease.py` | Adrrev005 procedure 30 edits it; read to avoid duplicating or conflicting with that removal | `REQ-002`, `REQ-003` |
| `implementations/20261110-164906_11_scripts_agent_workflow_state_store_py.md` | The pending procedure that removes the lease-less rule; confirms its ordering and what remains undefined | `REQ-002`, UNK-01 |
| `implementations/20261110-164906_29_tests_agent_workflow_test_workflow_state_store_py.md` | The pending procedure that edits `tests/agent/workflow/test_workflow_state_store.py`; `REQ-003` follows it | `REQ-003` |
| `tests/shared/test_mcp_config_validation.py` | Exercises `_build_single_server`; must keep passing after the field removal | `REQ-001`, `scripts/shared/mcp_config.py` |
| `tests/agent/test_startup_reporter.py` | `ReadinessReporter` tests; must keep passing after the log suffix removal | `REQ-001`, `scripts/agent/startup_reporter.py` |

## Acceptance Criteria
- AC-1 (`REQ-001`): `rg -n "FailurePolicy|failure_policy" scripts tests docs config registry` returns no hit, and the readiness warning lists unavailable servers by key only.
- AC-2 (`REQ-001`): `tests/shared/test_mcp_config.py`, `tests/shared/test_mcp_config_validation.py`, `tests/agent/test_startup.py`, and `tests/agent/test_startup_reporter.py` pass, and a server entry that still carries a `failure_policy` key loads without error.
- AC-3 (`REQ-002`): `rg -n "legacy_recovered|_LEGACY_STALE_AGE_SEC|legacy" tests/agent/workflow/test_state_store.py` returns no hit, and the lease-expiry, live-lease, compare-and-swap, and reconciliation cases in that file pass.
- AC-4 (`REQ-003`): the two named tests no longer exist and `rg -n "composite|legacy shape|retained" tests/agent/workflow/test_workflow_state_store.py` returns no hit.
- AC-5 (`REQ-004`): `uv run python tools/check_compat_shims.py`, `uv run python tools/check_docs_consistency.py --domain mcp`, ruff, mypy, import-linter, and the targeted pytest runs pass, and `git diff --name-only` lists only files from the frozen table.

## Tests
- `REQ-001`: run `uv run pytest tests/shared/test_mcp_config.py tests/shared/test_mcp_config_validation.py tests/agent/test_startup.py tests/agent/test_startup_reporter.py -v`; add a one-off load check that an entry with a leftover `failure_policy` key is accepted (manual verification, no new test file).
- `REQ-002`: run `uv run pytest tests/agent/workflow/test_state_store.py -v`.
- `REQ-003`: run `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` after adrrev005 procedure 29 has landed.
- `REQ-004`: run `uv run pytest tests/agent/workflow/ tests/shared/ tests/agent/ -q` and the checks in the Validation plan.

## Documentation Impact
Yes, for `REQ-001` only: the MCP server configuration field reference loses the `failure_policy` bullet (located through the MCP entries of `docs/00_index.md` "Document References by Task"). The ADR and DB wording about lease-less recovery is owned by adrrev005 `REQ-006` and the ADR-001 issue, so no document for `REQ-002` or `REQ-003` is changed here. Run `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, and `check_docs_consistency.py --domain mcp`.

## Assumptions
- A-1: removing the field does not reject an existing `failure_policy` key, because `_build_single_server` reads keys by name and `rg` finds no unknown-key or allowed-key check in `scripts/shared/mcp_config.py`; it is checked once by a load check in Phase 1 (falsifiable).
- A-2: the readiness warning change from `srv (fail-fast)` to `srv` affects no parser or document: tests assert only the prefix and the server names, and `docs/` never quotes the suffix (checked in Step 3).
- A-3: `tests/agent/workflow/test_state_store.py` is not an adrrev005 target (its implementation procedure list names `test_workflow_state_store.py` and `test_stale_recovery_lease.py` only), so `REQ-002` does not conflict with it; sequencing risk applies to `tests/agent/workflow/test_workflow_state_store.py` only.
- A-4: the removal of the two retained-database tests loses no current-schema coverage, because neighboring tests (`test_state_store_create_task_issues_unique_keys` and the tool-call-state lifecycle tests) exercise the same current-schema paths.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | What recovery does with a running attempt that has no lease after adrrev005 removes the legacy age rule. Its procedure says such a row "falls through to normal classification", but `_classify_running_attempts` has no other branch for a missing lease, and `begin_stage_if_new` still accepts `lease_duration_sec=None` (documented "for legacy callers"; the production caller passes a lease, several tests do not). This is the Issue's Decision 1 (can a lease-less row still exist) in a new form. | A recorded decision on lease-less rows and on whether the `None` default stays | Owner of adrrev005 procedure `implementations/20261110-164906_11_scripts_agent_workflow_state_store_py.md` decides; if the `None` default should go, file a follow-up Issue (it touches `idempotency_ops.py`, `state_store.py`, and three test files) | False |
| UNK-02 | Whether adrrev005 procedures 29 and 30 enumerate every `legacy_recovered` assertion (`test_stale_recovery_lease.py` has two outside the removed cases, `test_workflow_state_store.py` has two more); any missed one fails after the field is removed | Line-level coverage of those two procedures | Owner of adrrev005 phase 4 confirms before procedure 11 executes; not a target of this Plan | False |
| UNK-03 | Whether any deployed `agent.toml` sets `failure_policy` | Production configuration was not inspected (`rules/ai-execution.md` Repository Tool Usage item 7) | A-1 shows it is ignored; confirm during the deploy hand-off | False |
| UNK-04 | Whether any WAL, mode, or Memory compatibility remains (the Issue's own open fact; the WAL path in the memo does not exist) | A confirmed target list | File a separate Issue after a repository search; outside this Plan | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/mcp_config.py` | Modify | Medium: imported by 19 script modules and 38 test modules, but only the removed field and enum change | 5 | High: one author (name variants) holds all commits | not applicable (rsynced) |
| `scripts/agent/startup_reporter.py` | Modify | Low: imported by `scripts/agent/startup.py` and one test module | 4 | High: one author | not applicable (rsynced) |
| `tests/agent/test_startup.py` | Modify | Low: a rename in one test | 7 | High: one author | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` | Modify | Low: one bullet, no other document quotes it | 6 | High: one author | not applicable (rsynced) |
| `tests/agent/workflow/test_state_store.py` | Modify | Low: recovery test cases only | 6 | High: one author | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify | Low: two tests removed; shares the file with adrrev005 procedure 29 | 12 | High: one author | not applicable (rsynced) |

## Design
- **Scope decision (Step 2 verification)**: the Issue's main item (remove the lease-less recovery branch) duplicates adrrev005 `REQ-004`, whose procedures are still `Pending` and in active execution. This Plan keeps only what that plan does not cover, so no two plans edit `state_store.py`. The alternative (a second plan for the same branch) was rejected because it would create two procedures for one file.
- **`FailurePolicy` removal**: delete the enum, field, and parse step; no alias or deprecation shim (`rules/coding.md` Deprecation policy; zero-caller `rg` check first). Alternative rejected: keep the enum for future policies, because nothing branches on it and a future policy can add it back with its behavior. Alternative rejected: reject a leftover `failure_policy` key, because that adds new strict validation outside the Issue.
- **Operator-visible change**: the readiness warning line changes from `srv (fail-fast)` to `srv`.
- **Consumer scan record** (`tools/scan_change_consumers.py --seed FailurePolicy --seed failure_policy`; the testmon state was stale, so results are candidates only):
  - direct scripts: `scripts/shared/mcp_config.py`, `scripts/agent/startup_reporter.py` — target rows.
  - direct docs: `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` — target row.
  - ADR test-citation candidates in `docs/10_adr/`: not affected: they cite tests that import `shared.mcp_config`, and `rg` finds no ADR text naming the symbol.
  - `tools/check_component_mandatoriness.py`: not affected: it mentions only the `required` default.
  - 69 import candidates under `tests/`: not affected: none constructs `McpServerConfig` with `failure_policy=` (`rg`), and the field has a default.
- **Path B analysis** (Path B: more than 3 target files and a config interface): architecture: `PYTHONPATH=scripts uv run lint-imports` reports 6 kept, 0 broken; dependency graph: `shared.mcp_config` has 19 script and 38 test importers, `agent.startup_reporter` has one script importer; history: see Affected areas; operational: no process, port, or database lock is involved and no dependency changes (`pip-audit` not needed); persisted schema check: not applicable, no DDL changes.
- **Validation quality baseline**: `radon cc` on the two Python targets reports no grade C or worse; `vulture scripts/ --min-confidence 80` reports 16 existing findings, none in the target files (exit 3 is the pre-existing result); `bandit -r scripts/ -c pyproject.toml -ll` exits 0. The diff-cover baseline number is `N/A: no code diff exists at planning time`; the Plan requires at least the threshold in `rules/toolchain.md` Completion checklist on the changed lines.
- **Impact radius** (`rules/toolchain.md`): `McpServerConfig` is imported by 19 script modules and 38 test modules, which exceeds the rule-of-thumb size, but only the removed field is touched and no caller passes it.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Remove `FailurePolicy` (independent of adrrev005)**
   - [ ] Re-run `rg -n "FailurePolicy|failure_policy" scripts tests docs config registry` and confirm only the frozen rows hit (`REQ-001`, `REQ-004`)
   - [ ] Delete the enum, the field, and its parse call (`REQ-001`; `scripts/shared/mcp_config.py`)
   - [ ] Drop the policy lookup so unavailable servers are listed by key only (`REQ-001`; `scripts/agent/startup_reporter.py`)
   - [ ] Rename the readiness test to describe what it asserts (`REQ-001`; `tests/agent/test_startup.py`)
   - [ ] Remove the `failure_policy` bullet (`REQ-001`; `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`)
   - [ ] Check that a server entry with a leftover `failure_policy` key still loads (A-1)
2. **Phase 2: Align the workflow tests (after adrrev005 phase 4)**
   - [ ] Seed lease-bearing rows and remove `legacy`/`legacy_recovered` assertions (`REQ-002`; `tests/agent/workflow/test_state_store.py`)
   - [ ] Delete `test_retained_db_compatibility` and `test_lifecycle_works_on_legacy_shape_with_unused_snapshot_column`, after adrrev005 procedure 29 has landed (`REQ-003`; `tests/agent/workflow/test_workflow_state_store.py`)
3. **Phase 3: Deployment & Verification**
   - [ ] Run the validation sequence in `rules/toolchain.md`, `uv run python tools/check_compat_shims.py`, and the documentation checks (`REQ-004`)
   - [ ] Deployment hand-off: `scripts/shared/mcp_config.py` and `scripts/agent/startup_reporter.py` are production code, so deploying follows `skills/deploy/SKILL.md`; its prerequisite is that the change is committed and pushed first, and deploying is the user's decision (it has an approval gate); confirm UNK-03 during that hand-off (`REQ-001`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/mcp_config.py` | Unit: config parse and validation | `uv run pytest tests/shared/test_mcp_config.py tests/shared/test_mcp_config_validation.py -v` | Pass; no `failure_policy` reference remains |
| `scripts/agent/startup_reporter.py`, `tests/agent/test_startup.py` | Unit: readiness warning | `uv run pytest tests/agent/test_startup_reporter.py tests/agent/test_startup.py -v` | Pass; unavailable servers listed by key |
| `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` | Documentation consistency | `uv run python tools/check_docs_consistency.py --domain mcp`; `check_docs_quality.py`; `check_docs_structure.py`; `check_docs_content_policy.py` | No findings |
| `tests/agent/workflow/test_state_store.py` | Unit: real-DB recovery | `uv run pytest tests/agent/workflow/test_state_store.py -v` | Pass; no legacy reference |
| `tests/agent/workflow/test_workflow_state_store.py` | Unit | `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` | Pass; two compatibility tests gone |
| Whole change | Static and architecture | `uv run ruff check scripts/`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `uv run vulture scripts/ --min-confidence 80` | No new findings beyond the existing baseline |
| Whole change | Compatibility and coverage | `uv run python tools/check_compat_shims.py`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | Pass |

## Risks
- **Risk**: adrrev005 is in active execution and edits `tests/agent/workflow/test_workflow_state_store.py` (procedure 29), so `REQ-003` can conflict with it → **Mitigation**: run Phase 2 after procedure 29 is archived, and rerun `tools/check_plan_target_overlaps.py` when this Plan is frozen.
- **Risk**: adrrev005 removes `legacy_recovered` while other `legacy_recovered` assertions remain in files outside this Plan (UNK-02) → **Mitigation**: report UNK-02 to the adrrev005 owner before procedure 11 runs; this Plan changes only `tests/agent/workflow/test_state_store.py`.
- **Risk**: after adrrev005, a running attempt without a lease has no defined recovery outcome (UNK-01) → **Mitigation**: not changed here; flag to the adrrev005 owner and file a follow-up Issue if the optional lease parameter should be removed.
- **Risk**: the readiness warning text changes for operators → **Mitigation**: no test or document parses the suffix (A-2); state the change in the commit message.
- **Risk**: blast radius of `McpServerConfig` (19 script and 38 test importers) → **Mitigation**: only a defaulted field is removed and no caller passes it; run `tests/shared/`, `tests/agent/`, and `tests/integration/` suites in Phase 3.
- **Risk**: a deployed `agent.toml` still carries `failure_policy` → **Mitigation**: the key is ignored (A-1, verified in Phase 1); confirm during deployment (UNK-03).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `FailurePolicy` from `scripts/shared/mcp_config.py`, `scripts/agent/startup_reporter.py`, `tests/agent/test_startup.py`, and the MCP configuration reference | Pending | — | — | |
| 2 | Align `tests/agent/workflow/test_state_store.py` and `tests/agent/workflow/test_workflow_state_store.py` with lease-only recovery and the current schema | Pending | — | — | Starts after adrrev005 phase 4 |
| 3 | Run the validation sequence and the compatibility checks, then hand off deployment | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261111-163923_compat009_workflow-legacy-compat-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-170504
- **Related target files**: `scripts/shared/mcp_config.py`, `scripts/agent/startup_reporter.py`, `tests/agent/test_startup.py`, `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (FailurePolicy search) and Implementation Intent; `FailurePolicy` enum and field in `scripts/shared/mcp_config.py` | `scripts/shared/mcp_config.py` | Step 1 | AC-1, AC-2 | `tests/shared/test_mcp_config.py`, `tests/shared/test_mcp_config_validation.py` | Confirmed by repository evidence |
| REQ-001 | `ReadinessReporter` policy lookup in `scripts/agent/startup_reporter.py` | `scripts/agent/startup_reporter.py` | Step 1 | AC-1, AC-2 | `tests/agent/test_startup_reporter.py` | Confirmed by repository evidence |
| REQ-001 | Test named after the removed field in `tests/agent/test_startup.py` | `tests/agent/test_startup.py` | Step 1 | AC-2 | `tests/agent/test_startup.py` | Confirmed by repository evidence |
| REQ-001 | Documented field bullet in the MCP configuration reference | `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` | Step 1 | AC-1 | `tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (legacy-only tests) and Acceptance Criteria; legacy assertions in `tests/agent/workflow/test_state_store.py` | `tests/agent/workflow/test_state_store.py` | Step 2 | AC-3 | `tests/agent/workflow/test_state_store.py` | Derived from confirmed evidence |
| REQ-003 | Issue Required Changes (retained-database compatibility tests); the two named tests in `tests/agent/workflow/test_workflow_state_store.py` | `tests/agent/workflow/test_workflow_state_store.py` | Step 2 | AC-4 | `tests/agent/workflow/test_workflow_state_store.py` | Confirmed by repository evidence |
| REQ-004 | Issue Acceptance Criteria (`check_compat_shims.py` passes) and Testing Expectations | N/A: verification only, no file change | Step 3 | AC-5 | `tools/check_compat_shims.py`, toolchain gates | Explicit in issue |

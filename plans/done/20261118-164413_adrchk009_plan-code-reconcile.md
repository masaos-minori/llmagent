## Goal
- Make the Execution Status, Work Items Created, deployment-phase preconditions, and acceptance-criteria text of the archived plans adrrev005 and adrrev002 match the repository, and make one rule decide EventBus DDL exposure: `scripts/db/` MUST NOT expose EventBus DDL, so the `build_eventbus_schema_sql` accessor and `_EVENTBUS_SCHEMA_PATH` are removed from `scripts/db/schema_sql.py`.

## Priority
High

## Scope
- **In-Scope**: Re-run the issue's searches and attach their output; remove `build_eventbus_schema_sql`, `_EVENTBUS_SCHEMA_PATH`, the module-docstring entry, and the then-unused `Path` import from `scripts/db/schema_sql.py`; remove the matching import and the one test from `tests/db/test_create_schema.py`; reconcile the adrrev005 `Work Items Created` rows with the archived procedures; record the adrrev005 AC-04 residual hits as a deviation note; add the deployment-phase preconditions to adrrev005 Phase 7 and adrrev002 Phase 6; reference or mark pending the approval records of the adrrev005 Phase 6 ADR edits; correct the adrrev005 text that describes an EventBus accessor in `scripts/db/`.
- **Out-of-Scope**: Running the deployment (`skills/deploy/SKILL.md` hand-off only); any DDL change; any production database inspection or change; changing `scripts/eventbus/db_tools.py`, `tests/eventbus/test_eventbus_db_tools.py`, `scripts/agent/services/workflow_schema.py`, `deploy/init_db.sh`, or `deploy/setup_services.sh` (UNK-02); editing ADR-001, ADR-006, ADR-008, or `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, and writing any approval statement or ledger entry for a past approval (UNK-03).
- **Dependencies**: Closed. The data lifecycle decision (issue id adrchk008) and the ADR approval governance (issue id adrchk011) are archived with their plans; the rows those plans still list as `Pending` are validation and deploy hand-off steps, which this Plan does not need. Fix order against sibling Plans: no ordering dependency; overlap judgments are in `Assumptions`.

## Background
- Source: the review task list `memo-issue.md` (package `ADRCHK2-H09`, merged from ADRCHK-H10 and ADRCHK-H18). Every claim below was re-verified against the repository on 2026-11-18 (see Requirement Traceability `Status`).
- `Confirmed by repository evidence`: `rg -n "build_eventbus_schema_sql|_EVENTBUS_SCHEMA_PATH" scripts tools tests` returns the definitions and docstring entry in `scripts/db/schema_sql.py` (`_EVENTBUS_SCHEMA_PATH`, `build_eventbus_schema_sql`) and, in `tests/db/test_create_schema.py`, the import and `TestEventbusSchemaFingerprint::test_db_accessor_returns_eventbus_canonical_ddl`. No `scripts/`, `tools/`, `docs/`, `registry/`, or `deploy/` file uses either symbol.
- `Confirmed by repository evidence` (history): commit `add36ad68` removed the accessor under adrrev002; commit `0c456183a` ("adrrev005 row 05") added it back with the same shape, following the adrrev005 row text "one accessor family". adrrev002 `REQ-004` and `AC-04` therefore fail on the current tree, while adrrev005's `Design` already says the EventBus DDL is read from `schema.sql` by callers.
- `Confirmed by repository evidence` (narrowing): adrrev002 `AC-04` names `build_eventbus_schema_sql` but not `_EVENTBUS_SCHEMA_PATH`; the adrrev002 target row names the constant `EVENTBUS_SCHEMA_SQL_PATH`, a name that never existed in the file. The EventBus-owned accessor is `schema_sql()` in `scripts/eventbus/db_tools.py`; `tests/db/test_create_schema.py` already builds its canonical DDL from it (`_CANONICAL_EVENTBUS_DDL`). `docs/41_db/db_08_active_databases.md` states that `scripts/eventbus/schema.sql` is the only DDL definition and that the EventBus service and its tool read it.
- `Confirmed by repository evidence`: adrrev005 `Execution Status` marks Phases 1-6 `Completed` while 35 `Work Items Created` rows are `Pending`. All 50 procedures are in `implementations/done/`, and `uv run python tools/sync_plan_workitem_status.py <plan> --dry-run` reports it would set those 35 rows to `Completed` from the archived procedures' own Execution Status. The same plan's Phase 1 note already says procedures 01 and 19 are archived while their rows read `Pending`. adrrev002 has no `Pending` row under a `Completed` Phase; its Phase 6 is the only `Pending` Phase.
- `Confirmed by repository evidence` (wider than the issue): adrrev005 `AC-04` (`rg -n "user_version|schema_migrations|workflow_schema_version|_LEGACY_STALE_AGE_SEC" scripts/ deploy/`) is documented to return only the `execution_snapshot.py` header read. It also returns `scripts/eventbus/db_tools.py` (`schema_version()` reads `PRAGMA user_version`, now always the SQLite default; used by the `version` entry point and its tests) and comments in `scripts/agent/services/workflow_schema.py`, `deploy/init_db.sh`, and `deploy/setup_services.sh` that name the retired marker tables.
- `Confirmed by repository evidence`: the Phase 6 ADR edits of adrrev005 are commits `5e8e89203` (ADR-001, row 35), `c3573341e` (ADR-008, row 36), and `8f5c5825c` (ADR-006, row 47). None of the commit messages cites an approval record. The ADR approval ledger (`governance_03` Part 5) holds `AAL-025` (ADR-008 schema-mismatch rule, approver `Not recorded`) and `AAL-029` (ADR-006 no-loss statements, a different statement); no ledger row covers the ADR-001 lease-less clause removal or the ADR-006 version-stamp clause removal.
- `Confirmed by repository evidence`: the two open unknowns behind adrrev005 Phase 7 are its `UNK-02` (whether a legacy workflow database carrying `execution_snapshots` must fail startup) and `UNK-03` (the operator's archive-and-recreate plan for the deployed `/opt/llm/db` files). Both are listed `Blocking? False` and unresolved in the plan. ADR-008 Decision Details 22 and 23 now record the schema-mismatch and retention rules, with approval pending in `AAL-025` and `AAL-026`.
- `Confirmed by repository evidence`: `tools/check_db_separation.py` passes on the current tree ("No violations found"); `PYTHONPATH=scripts uv run lint-imports` keeps all 6 contracts.

## Problem
- adrrev005 reports completed Phases next to `Pending` Work Items, and its Phase 7 lists no preconditions although the deployed databases do not match the current schema and the data lifecycle approval is pending; running it as written would stop the workflow and EventBus services at the fingerprint gates.
- adrrev002 `AC-04` and adrrev005's accessor-family row contradict each other on `scripts/db/` exposing EventBus DDL; the code follows adrrev005, so adrrev002's completed Phase 3 does not match the tree.
- The Phase 6 ADR edits carry no approval reference and, for ADR-001 and ADR-006, no ledger row.

## Reason for Change
- A plan whose status disagrees with the tree misleads the next reader and the deploy hand-off. The EventBus DDL ownership split reappeared once and will keep reappearing until one rule is written down and the code follows it. No external deadline.

## Implementation Intent
- Rule (user confirmation in session 2026-11-18, consistent with the adrrev002 owner decision of 2026-11-10 that `scripts/db/` loses all EventBus handling): `scripts/db/` MUST NOT expose EventBus DDL; the EventBus service and `eventbus.db_tools` own it. Remove the accessor and constant; adrrev002 `AC-04` then holds unchanged; correct adrrev005's description to three databases.
- Correction method (user confirmation in session 2026-11-18): correct the archived plans in place, using `tools/sync_plan_workitem_status.py` for `Work Items Created` and Edit for text, as earlier commits did.
- Change only what the evidence supports: status rows follow the archived procedures, preconditions cite ledger IDs and plan Unknown IDs, and no approval text is written.

## Requirements
- `REQ-001`: Before any edit, re-run the issue's searches (the accessor symbols, adrrev002 `AC-04`, adrrev005 `AC-04`, the Work Items dry-run) and attach their output to every status or text change made in the two archived plans.
- `REQ-002`: In adrrev005, set each `Pending` Work Items row to `Completed` from the archived procedure evidence, so no Phase marked `Completed` has a `Pending` Work Item in either plan; record the adrrev005 `AC-04` residual hits (Background) as an explicit deviation note in the plan's `Execution Status` notes.
- `REQ-003`: Add the deployment-phase preconditions to adrrev005 Phase 7 and adrrev002 Phase 6: the data lifecycle decision text recorded in ADR-008 (approval pending in `AAL-025` and `AAL-026`), adrrev005 `UNK-02` and `UNK-03` resolved by the maintainer, each deployed database that fails the fingerprint archived and recreated by the operator, and the deployment itself not run by any document edit.
- `REQ-004`: In adrrev005 Phase 6, cite for each of the three ADR edits its commit and either its ledger row (`AAL-025` for ADR-008, pending) or "no ledger row; pending" (ADR-001, ADR-006); write no approval statement.
- `REQ-005`: Remove `build_eventbus_schema_sql`, `_EVENTBUS_SCHEMA_PATH`, their module-docstring entry, and the `Path` import that only they use from `scripts/db/schema_sql.py`, and remove the import and `test_db_accessor_returns_eventbus_canonical_ddl` from `tests/db/test_create_schema.py`; add no alias, shim, or history comment.
- `REQ-006`: Make both plans follow the rule: the adrrev005 `Implementation Target Files` row for `scripts/db/schema_sql.py` describes canonical DDL accessors for workflow, session, and rag only, with the EventBus DDL owned by `eventbus.db_tools` (its `Implementation steps` text names no EventBus accessor and stays unchanged); adrrev002 `AC-04` returns no match on the tree and its text stays unchanged.
- `REQ-007`: Verify with `uv run python tools/check_db_separation.py`, `uv run pytest tests/db -v`, the archived-plan checkers, and the full validation sequence of `rules/toolchain.md`.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/db/schema_sql.py` | Remove the EventBus DDL accessor | Delete `build_eventbus_schema_sql`, `_EVENTBUS_SCHEMA_PATH`, the docstring entry, and the `Path` import that only they use | REQ-001, REQ-005 / AC-01, AC-05 | `rg -n "build_eventbus_schema_sql\|_EVENTBUS_SCHEMA_PATH" scripts tools tests` hits the definitions and docstring; `Path` appears only in `_EVENTBUS_SCHEMA_PATH` (checked in Step 3) | `tests/db/test_create_schema.py` | Verified |
| `tests/db/test_create_schema.py` | Remove the only consumer | Delete the `build_eventbus_schema_sql` import and `TestEventbusSchemaFingerprint::test_db_accessor_returns_eventbus_canonical_ddl`; the class keeps building its DDL through `eventbus_schema_sql()` | REQ-005 / AC-05 | `tests/db/test_create_schema.py` import line and the test body; no `docs/` or `tools/` citation of the test (checked in Step 3) | `uv run pytest tests/db/test_create_schema.py -v` | Verified |
| `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` | Reconcile status, preconditions, approval references, and accessor text | Set 35 `Pending` Work Items rows `Completed` through the sync tool; add the `AC-04` deviation note, the Phase 7 preconditions, the Phase 6 approval references, and the three-database accessor wording | REQ-001, REQ-002, REQ-003, REQ-004, REQ-006 / AC-01, AC-02, AC-03, AC-04, AC-06 | Execution Status marks Phases 1-6 `Completed`; `uv run python tools/sync_plan_workitem_status.py <plan> --dry-run` reports 35 rows; commits `5e8e89203`, `c3573341e`, `8f5c5825c` (checked in Step 2) | `uv run python tools/sync_plan_workitem_status.py <plan> --dry-run`; `uv run python tools/check_workitem_structure.py --archived-status` | Verified |
| `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | Add the Phase 6 preconditions and the `AC-04` evidence | Add the deployment preconditions to Phase 6 and record that `AC-04` returns no match after the accessor removal; `AC-04` text stays unchanged | REQ-001, REQ-003, REQ-006 / AC-01, AC-03, AC-06 | `AC-04` pattern hits `scripts/db/schema_sql.py` today; Phase 6 is the only `Pending` Phase (checked in Step 2) | `rg -n "DbTarget\.EVENTBUS\|build_eventbus_schema_sql\|create_eventbus_schema\|rotate_eventbus_db\|eventbus_db_path" scripts/db/ scripts/shared/ scripts/agent/`; `uv run python tools/check_workitem_structure.py --archived-status` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/db_tools.py` | The EventBus-owned accessor `schema_sql()` that replaces the removed one; `schema_version()` is the `AC-04` residual (UNK-02) | REQ-005, REQ-006 |
| `scripts/eventbus/schema.sql` | The only EventBus DDL definition | REQ-005 |
| `tools/check_db_separation.py` | ADR-008 check that must keep passing | REQ-007 |
| `tools/sync_plan_workitem_status.py` | Reconciles `Work Items Created` rows from archived procedures | REQ-002 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Part 5 ADR Approval Ledger: `AAL-025`, `AAL-026`, `AAL-029` and the rule that an implementer writes no approval text | REQ-003, REQ-004 |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Decision Details 22 and 23 and the pending approval bullets | REQ-003, REQ-004 |
| `docs/41_db/db_08_active_databases.md` | States that `schema.sql` is the only EventBus DDL definition | REQ-005, REQ-006 |

## Acceptance Criteria
- `AC-01` (REQ-001): each status or text change in the two archived plans cites the output of a search or tool run made on the day of the change; the searches were re-run before the first edit.
- `AC-02` (REQ-002): `uv run python tools/sync_plan_workitem_status.py plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md --dry-run` reports no row to change; no Phase marked `Completed` in either plan has a `Pending` Work Item; the adrrev005 `Execution Status` notes name the `AC-04` residual hits.
- `AC-03` (REQ-003): adrrev005 Phase 7 and adrrev002 Phase 6 each list the four preconditions of `REQ-003`, name `AAL-025`, `AAL-026`, `UNK-02`, and `UNK-03`, and state that deployment is the user's decision after commit and push.
- `AC-04` (REQ-004): adrrev005 Phase 6 names commits `5e8e89203`, `c3573341e`, `8f5c5825c` with `AAL-025` (ADR-008) and "no ledger row; pending" (ADR-001, ADR-006); no approval statement appears in either plan.
- `AC-05` (REQ-005): `rg -n "build_eventbus_schema_sql|_EVENTBUS_SCHEMA_PATH" scripts tools tests docs` returns no match; `uv run pytest tests/db -v` passes.
- `AC-06` (REQ-006): adrrev002 `AC-04` search returns no match; the adrrev005 `scripts/db/schema_sql.py` target row names accessors for workflow, session, and rag only and names `eventbus.db_tools` as the EventBus DDL owner; the adrrev005 `Implementation steps` text is unchanged because it names no EventBus accessor.
- `AC-07` (REQ-007): `uv run python tools/check_db_separation.py` passes, `uv run python tools/check_workitem_structure.py --archived-status` reports no new finding, and the full validation sequence of `rules/toolchain.md` passes.

## Tests
- `REQ-005`: `uv run pytest tests/db/test_create_schema.py -v` and `uv run pytest tests/db -v` after the removal; `tests/eventbus/test_eventbus_db_tools.py` keeps covering the EventBus-owned accessor.
- `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-006`: the searches and the sync tool dry-run named in `AC-01` to `AC-06`; no new test is written for plan text.
- `REQ-007`: `tools/check_db_separation.py`, the archived-plan checkers, and the full validation sequence.

## Documentation Impact
N/A: no `docs/*.md` file changes. The two plans are workflow documents, not `docs/`. `governance_03` is not modified because this Plan registers no Needs Confirmation marker under `docs/`; its Unknowns are plan-level. Ledger rows or ADR text for the ADR-001 and ADR-006 edits would change `docs/` and are routed to UNK-03.

## Assumptions
- Removing the accessor does not change production behavior: no `scripts/` file calls it. Falsifiable by `rg` (`AC-05`) and `uv run pytest tests/db`.
- `tools/sync_plan_workitem_status.py` sets a row `Completed` only when the archived procedure's own Execution Status is complete, as the dry-run output at Step 2 showed. Falsifiable by the dry-run repeated before the edit.
- The `Pending` Phase 7 of adrrev005 and Phase 6 of adrrev002 stay `Pending`: they are deployment phases that this Plan does not run. Falsifiable by the Execution Status tables after the edit.
- Overlap with other Frozen Plans (`tools/check_plan_target_overlaps.py`, Step 8b): none reported for these rows (checked in Step 8b after the freeze). Falsifiable by re-running the tool before Phase 1.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How archived plans are corrected | Resolved 2026-11-18: the user confirmed in-place correction with `tools/sync_plan_workitem_status.py` and Edit; earlier commits `1d905842f` and `6bce337b5` did the same | None; `tools/amend_plan.py` is not used because it refuses an archived Plan | False |
| UNK-02 | Whether the adrrev005 `AC-04` residual hits are amended in the `AC-04` text or removed from code | A maintainer decision; removal touches `scripts/eventbus/db_tools.py`, `tests/eventbus/test_eventbus_db_tools.py`, `scripts/agent/services/workflow_schema.py`, `deploy/init_db.sh`, `deploy/setup_services.sh`, none of which is a target here | Maintainer decides; if removal, file a follow-up Issue (scope amendment). This Plan only records the deviation (`REQ-002`) | False |
| UNK-03 | Whether the ADR-001 lease-less clause removal and the ADR-006 version-stamp clause removal are decision-text changes that need `AAL` ledger rows and pending bullets | A maintainer classification; the rows and bullets would change ADR-001, ADR-006, and `governance_03` (outside the Target Files) | Maintainer decides; if yes, file a follow-up Issue (scope amendment). This Plan marks the edits pending in the adrrev005 text only and writes no approval statement | False |
| UNK-04 | Whether adrrev005 `UNK-02` and `UNK-03` have been resolved since 2026-11-11, and the present state of the deployed databases | No resolution is recorded in the plan or in `governance_03`; production was not inspected here | Maintainer resolves both in the adrrev005 plan before any deployment; the preconditions of `REQ-003` gate the deploy hand-off, not this Plan | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/db/schema_sql.py` | Modify | Low: no `scripts/` caller of the removed symbols; the other builders stay | 18 commits | N/A | not applicable (rsynced) |
| `tests/db/test_create_schema.py` | Modify | Low: one import and one test | 25 commits | N/A | not applicable (rsynced) |
| `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` | Modify | Low: archived workflow document read by plan tools only | 4 commits | N/A | not applicable (rsynced) |
| `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | Modify | Low: archived workflow document read by plan tools only | 2 commits | N/A | not applicable (rsynced) |

## Design
- **Rule and alternatives**: `scripts/db/` exposes no EventBus DDL. Alternative rejected: keep the accessor and amend adrrev002 `AC-04` and `REQ-004`; it keeps a second reader of `scripts/eventbus/schema.sql` that has no production caller, contradicts `db_08` and the adrrev002 owner decision, and leaves the EventBus DDL owned in two places. The user chose removal on 2026-11-18.
- **Compatibility impact**: none for runtime. The only consumer is one test that compares the accessor with the EventBus-owned accessor; that comparison disappears with the accessor.
- **Plan correction**: `Work Items Created` rows change only through `tools/sync_plan_workitem_status.py` (dry-run first); text changes use Edit. Preconditions cite ledger IDs (`AAL-025`, `AAL-026`) and plan Unknown IDs, and say "pending" where the ledger has no approver; no approval wording is composed.
- **Consumer scan** (`tools/scan_change_consumers.py --seed build_eventbus_schema_sql --seed _EVENTBUS_SCHEMA_PATH`): the candidates are `adr-test-citation` matches on unrelated tests, so they are `not affected`; `rg` over `scripts`, `tools`, `tests`, `docs`, `registry`, `config`, `deploy`, `rules`, `skills`, `prompts`, and `templates` found only the two target files. The scan lists candidates only (text search); indirect users are not detected.
- **Path B analysis** (Step 5): architecture: `PYTHONPATH=scripts uv run lint-imports` reports 6 contracts kept, 0 broken; the removal deletes the only `db` reference to the `eventbus` directory (a path, not an import). Dependency graph: the two target code files only. Historical: churn is in `Affected areas`; bus factor is `N/A` (`git shortlog` returned nothing). Operational: no port, process, or database is touched; `ss`, `fuser`, and `pip-audit` were not run (no dependency or runtime change). Persisted schema check (`rules/persisted-schema-change.md`): not applicable, the DDL and `schema.sql` are unchanged.
- **Validation quality baseline**: `radon cc scripts/db/schema_sql.py -s` grades every function `A`; `vulture scripts/ --min-confidence 80` reports only unused-variable findings outside the targets; `bandit -r scripts/ -c pyproject.toml` reports Low 45, Medium 0, High 0; diff-cover baseline `N/A: no code diff yet`, and implementation raises diff coverage to the `rules/toolchain.md` threshold (a deletion adds no uncovered lines).
- **Path classification**: Path B (more than 3 target files).

## Implementation steps
1. **Phase 1: Remove the EventBus DDL accessor (code)**
   - [ ] Re-run `rg -n "build_eventbus_schema_sql|_EVENTBUS_SCHEMA_PATH" scripts tools tests`, adrrev002 `AC-04`, and adrrev005 `AC-04`; keep the output as evidence (REQ-001; `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`).
   - [ ] Delete the accessor, constant, docstring entry, and unused `Path` import; delete the test import and `test_db_accessor_returns_eventbus_canonical_ddl`; run `uv run pytest tests/db -v` (REQ-005; `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`).
2. **Phase 2: Reconcile adrrev005**
   - [ ] Run the sync tool with `--dry-run`, then without it, and read back that no row is left to change (REQ-002; `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md`).
   - [ ] Add the `AC-04` deviation note to the `Execution Status` notes, the Phase 6 approval references, the Phase 7 preconditions, and the three-database accessor wording; attach the Phase 1 evidence (REQ-001, REQ-002, REQ-003, REQ-004, REQ-006; `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md`).
3. **Phase 3: Reconcile adrrev002**
   - [ ] Add the Phase 6 preconditions and record the `AC-04` result with its evidence; leave the `AC-04` text unchanged (REQ-001, REQ-003, REQ-006; `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`).
4. **Phase 4: Verification and deploy hand-off**
   - [ ] Run `uv run python tools/check_db_separation.py`, `uv run python tools/check_workitem_structure.py --archived-status`, `uv run python tools/check_workitem_traceability.py --active-only`, and the full validation sequence in `rules/toolchain.md` (REQ-007; `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`, `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md`, `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`).
   - [ ] `scripts/` changed, so hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision and is gated by the preconditions of `REQ-003`; this Plan does not run it (REQ-007; `scripts/db/schema_sql.py`).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py` | Unit | `uv run pytest tests/db -v` | Passes |
| Removed symbols | Search | `rg -n "build_eventbus_schema_sql\|_EVENTBUS_SCHEMA_PATH" scripts tools tests docs` | No match |
| adrrev002 `AC-04` | Search | `rg -n "DbTarget\.EVENTBUS\|build_eventbus_schema_sql\|create_eventbus_schema\|rotate_eventbus_db\|eventbus_db_path" scripts/db/ scripts/shared/ scripts/agent/` | No match |
| ADR-008 separation | Repository check | `uv run python tools/check_db_separation.py` | Passes |
| adrrev005 Work Items | Tool dry-run | `uv run python tools/sync_plan_workitem_status.py plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md --dry-run` | No row to change |
| Archived plans | Structure check | `uv run python tools/check_workitem_structure.py --archived-status` | No new finding |
| Whole repository | Full validation sequence | `rules/toolchain.md`: ruff format/check, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, bandit, full `uv run pytest`, `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | No new findings; all pass |
| Diff coverage | Coverage | `rules/toolchain.md` section 7 sequence | At or above the Completion checklist threshold |

## Risks
- **Risk**: Editing archived plans alters records that plan tools read (status vocabulary, archived-status check) → **Mitigation**: change rows only through the sync tool, run `check_workitem_structure.py --archived-status` after the edit, and keep the six-value Status vocabulary.
- **Risk**: A parallel change edits `scripts/db/schema_sql.py` or `tests/db/test_create_schema.py` (30-day churn is 18 and 25 commits) → **Mitigation**: re-run the searches before editing (Phase 1), use `tools/check_plan_target_overlaps.py` at Step 8b, and skip any task whose defect is already gone, recording the evidence.
- **Risk**: Removing the test lowers coverage of the canonical-DDL accessor → **Mitigation**: the EventBus-owned accessor stays covered by `tests/eventbus/test_eventbus_db_tools.py` and by `TestEventbusSchemaFingerprint`, which builds its DDL from it.
- **Risk**: "No ledger row; pending" is read as an approval → **Mitigation**: the text states that the approver and date are not recorded and cites `governance_03` Part 5; no approval wording is written.
- **Risk**: The Phase 7 and Phase 6 deploy hand-offs are run before the preconditions hold, and the services refuse the mismatched databases → **Mitigation**: the preconditions name `UNK-02`, `UNK-03`, `AAL-025`, and `AAL-026`; deploying stays the user's decision after commit and push.
- **Risk**: Blast radius of the removal is larger than the search shows (`rules/toolchain.md` impact-radius check) → **Mitigation**: `rg` over all repository directories found two files; the `tests/db` run and the full suite confirm.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the EventBus DDL accessor (code) | In Progress | — | — |  |
| 2 | Reconcile adrrev005 | In Progress | — | — |  |
| 3 | Reconcile adrrev002 | In Progress | — | — |  |
| 4 | Verification and deploy hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261118-165056_01_scripts_db_schema_sql.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261118-165056_03_plans_done_20261110-095137_adrrev005_schema-fingerprint-unify.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261118-165056_04_plans_done_20261110-091327_adrrev002_agent-eventbus-coupling.md.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123009_adrchk009_plan-code-reconcile.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-164413
- **Related target files**: `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`, `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md`, `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes: run the `rg` search and attach the result; Constraints: re-run the searches before editing | `scripts/db/schema_sql.py` | 1 | AC-01 | `rg -n "build_eventbus_schema_sql\|_EVENTBUS_SCHEMA_PATH" scripts tools tests` | Explicit in issue |
| REQ-001 | Required Changes: attach `rg` evidence for every status change | `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` | 2 | AC-01 | Sync tool dry-run output and the `AC-04` searches | Explicit in issue |
| REQ-001 | AI Implementation Instruction: attach `rg` evidence for every status change | `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | 3 | AC-01 | adrrev002 `AC-04` search output | Explicit in issue |
| REQ-002 | Required Changes: mark each Pending Work Item Completed with evidence; Step 2 evidence: 35 rows and the `AC-04` residual hits | `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` | 2 | AC-02 | `uv run python tools/sync_plan_workitem_status.py <plan> --dry-run` | Confirmed by repository evidence |
| REQ-003 | Required Changes: add the deployment-phase preconditions; adrrev005 Phase 7 and `UNK-02`, `UNK-03` | `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` | 2 | AC-03 | Read-back of the Phase 7 text | Confirmed by repository evidence |
| REQ-003 | Derived: adrrev002 Phase 6 runs `init_db.sh` on the existing databases, which the adrrev005 gate now checks | `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | 3 | AC-03 | Read-back of the Phase 6 text | Derived from confirmed evidence |
| REQ-004 | Required Changes: reference the Phase 6 approval records or mark them pending; commits and ledger rows in Step 2 | `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` | 2 | AC-04 | Read-back of the Phase 6 text; ledger rows in `governance_03` Part 5 | Confirmed by repository evidence |
| REQ-005 | Required Changes (decision): remove `build_eventbus_schema_sql` and `_EVENTBUS_SCHEMA_PATH`; the user chose removal | `scripts/db/schema_sql.py` | 1 | AC-05 | `uv run pytest tests/db -v`; the removed-symbols search | Confirmed by repository evidence |
| REQ-005 | Required Changes (decision): update the callers | `tests/db/test_create_schema.py` | 1 | AC-05 | `uv run pytest tests/db/test_create_schema.py -v` | Confirmed by repository evidence |
| REQ-006 | Implementation Intent: both plans follow one rule; adrrev005 `scripts/db/schema_sql.py` target row | `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` | 2 | AC-06 | Read-back of the `scripts/db/schema_sql.py` target row | Derived from confirmed evidence |
| REQ-006 | Acceptance Criteria: the `AC-04` search result matches the plan text | `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | 3 | AC-06 | adrrev002 `AC-04` search | Derived from confirmed evidence |
| REQ-007 | Testing Expectations: `check_db_separation.py`, `tests/db/`, the full validation sequence | `scripts/db/schema_sql.py` | 4 | AC-07 | `uv run python tools/check_db_separation.py`; full validation sequence | Explicit in issue |
| REQ-007 | Testing Expectations | `tests/db/test_create_schema.py` | 4 | AC-07 | `uv run pytest tests/db -v` | Explicit in issue |
| REQ-007 | Testing Expectations: archived-plan checkers | `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` | 4 | AC-07 | `uv run python tools/check_workitem_structure.py --archived-status` | Explicit in issue |
| REQ-007 | Testing Expectations: archived-plan checkers | `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | 4 | AC-07 | `uv run python tools/check_workitem_structure.py --archived-status` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-165056 -->
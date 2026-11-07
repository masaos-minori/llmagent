## Goal
Resolve the never-written `execution_snapshots` schema: retire the table, the `tool_call_state.snapshot_id` FK column, and the pass-through `snapshot_id` plumbing in the tool-call request path, and correct the docs that describe the table as written. This is the decision plan that gates the `tool_call_state` gate list (`wfaudit003`) and its key redesign (`wfaudit002`).

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/db/schema_sql.py` — remove the `execution_snapshots` table and the `snapshot_id` column/FK from `tool_call_state` in the workflow schema DDL.
  - `scripts/agent/workflow/tool_call_state_ops.py` — drop `snapshot_id` from `ToolCallState`, `_to_row`, and `record_tool_call`.
  - `scripts/agent/workflow/state_store.py` — drop the `snapshot_id` parameter from `record_tool_call`.
  - `scripts/agent/context.py` — drop the `snapshot_id` field/parameter on the tool-call request path (L297).
  - Docs: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` (L72, L79 stale claims), `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/41_db/db_02_architecture_and_schema-schema-reference.md`.
  - Tests: retire/adjust snapshot assertions in `tests/agent/workflow/`.
- **Out-of-Scope**:
  - Dropping the column from an existing production `workflow.sqlite` (no migration path exists; see Design "existing databases").
  - Re-introducing a snapshot feature; the origin concept (idempotency/snapshot plan) is archived history.
- **Dependencies**: Blocks `wfaudit003` (whether `execution_snapshots` enters the required-shape gate) and `wfaudit002` (`snapshot_id` FK must be resolved before any `tool_call_state` re-keying decision). Land this plan first.

## Background
`execution_snapshots` is defined in the workflow schema (`scripts/db/schema_sql.py:227-228`) and referenced by `tool_call_state.snapshot_id` (L239), but no code ever inserts a snapshot row and every `snapshot_id` write is the default null: pass-through parameters default to `None` (`state_store.py:112,116`, `tool_call_state_ops.py:55,67-69`, `context.py:297`) and no production caller passes a value (the single production call site `scripts/agent/tool_runner.py:174` omits it). Grep across `scripts/` finds no `INSERT INTO execution_snapshots`. The docs nonetheless describe the table as written: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md:72` ("written through `tool_call_state_ops.py`") and L79 ("recorded at call time"). All claims verified in the issue's `## Adversarial Validation` section.

## Problem
A schema surface and a request-path field exist that nothing writes: the FK points into a permanently empty table, the dataclass carries a dead field, and two docs carry stale claims about a written table. Keeping it costs schema-gate surface (wfaudit003), DDL coupling (wfaudit002), and misleading documentation.

## Reason for Change
Dead schema is a liability the repository has already been pruning (archived wfreview006 dead-method removal, compatrm004 removed-name set). The decision itself is required before two other open issues can touch the same tables; making it explicitly here prevents two downstream plans each re-deciding it.

## Implementation Intent
Retire the snapshot schema surface completely rather than keep it dormant: remove the table and column from the DDL, delete the dead plumbing, and update the docs to state the retirement. Do not add a migration for existing databases — the workflow domain has no migration path, and the code must simply stop reading or writing the column so both old and new databases work.

## Requirements
- `REQ-001`: The workflow schema DDL no longer creates `execution_snapshots`, and `tool_call_state` no longer declares `snapshot_id` or its FK.
- `REQ-002`: `ToolCallState`, `record_tool_call` (ops and facade), and the tool-call request path no longer carry a `snapshot_id` field/parameter.
- `REQ-003`: Code paths still function against a pre-retirement database that has the column: no SQL names `snapshot_id` in INSERT column lists or row reads (column defaults to NULL; absent reads are not attempted).
- `REQ-004`: Docs state that `execution_snapshots` is retired (not written, not created by new databases) and remove the "written through tool_call_state_ops.py" claim.
- `REQ-005`: Tests that referenced snapshots are removed or retargeted; full workflow test suite green.

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/db/schema_sql.py` | Modify | Remove `execution_snapshots` DDL (L227-232) and `snapshot_id TEXT REFERENCES ...` from `tool_call_state` (L239) | `REQ-001` | Table/column defined, never written (grep) | `tests/db/` schema tests | `Verified` |
| `scripts/agent/workflow/tool_call_state_ops.py` | Modify | Drop `snapshot_id` from dataclass (L30), `_to_row` (L43), `record_tool_call` signature and INSERT column list (L55,67-69) | `REQ-002`/`REQ-003` | Verified in Step 2 validation | `tests/agent/workflow/test_workflow_state_store.py` | `Verified` |
| `scripts/agent/workflow/state_store.py` | Modify | Drop `snapshot_id` parameter from facade `record_tool_call` (L112-116) | `REQ-002` | Pass-through default None | `tests/agent/workflow/` | `Verified` |
| `scripts/agent/context.py` | Modify | Drop `snapshot_id` from the tool-call request dataclass/parameters (L297) | `REQ-002` | No caller sets it (grep) | `tests/agent/` request-path tests | `Verified` |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Modify | Remove/replace stale claims at L72 and table-map row L79 | `REQ-004` | Stale claim verified verbatim | docs checkers | `Verified` |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | Update the execution-snapshot section to "retired" status | `REQ-004` | Doc documents the two lifecycle tables | docs checkers | `Verified` |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Modify | Remove the `execution_snapshots` row from the workflow table reference | `REQ-004` | Table map lists it | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/tool_runner.py` | Sole production `record_tool_call` caller (L174) — confirms no value is passed | `REQ-002` |
| `scripts/shared/execution_snapshot.py` | A separate, live execution-snapshot feature (config fingerprinting) exists in the shared domain; do not confuse it with the retired `execution_snapshots` table — verify the plan does not touch it | Out-of-scope guard |
| `tests/agent/workflow/test_workflow_state_store.py` | Tests that construct/read `ToolCallState` rows; must compile after the field removal | `REQ-005` |
| `docs/90_deployment/deployment_01_deployment.md` | Deployment docs may list the table in database shape descriptions — check and update if present | `REQ-004` |

## Acceptance Criteria
- `REQ-001`: `create_workflow_schema()` on a fresh database produces no `execution_snapshots` table and no `snapshot_id` column in `tool_call_state`.
- `REQ-002`: `grep -rn "snapshot_id" scripts/agent/` returns nothing outside the retirement note; dataclass has 7 fields, none named `snapshot_id`.
- `REQ-003`: Workflow tool-call tests against a freshly created (post-retirement) database pass; a test fixture simulating a pre-retirement database (column present) also passes record/finalize/classify.
- `REQ-004`: The three docs no longer describe `execution_snapshots` as written; docs checkers pass.
- `REQ-005`: `uv run pytest tests/agent/workflow/ tests/db/ -q` green.

## Tests
- Schema test: fresh workflow database table list excludes `execution_snapshots` and `tool_call_state` columns exclude `snapshot_id`.
- Legacy-shape test: insert into a fixture database created with the old DDL using the new code (INSERT must not name the column) — proves REQ-003 compatibility.
- Remove snapshot-specific assertions from `tests/agent/workflow/`; keep the remaining tool-call lifecycle tests unchanged.

## Documentation Impact
- `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` — replace the L72 lifecycle claim; drop or mark-retired the L79 table-map row.
- `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` — retitle the snapshot section to retirement status with a pointer to this decision.
- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` — remove the table row.
- Run docs checkers for domains agent and db per `routing.md` Tools.

## Assumptions
- Retire (not keep) is the correct decision: nothing in the open issue set or archived plans schedules a snapshot-writing feature. Recorded as `UNK-01` for owner veto.
- Existing production databases keep the leftover column harmlessly; no ALTER is attempted (the workflow domain has no migration path — `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | owner veto on retire-vs-keep if a future replay-equality feature is planned | roadmap intent not recorded | owner review of this plan's Design; keep path would instead just fix docs and gate | `False` |
| `UNK-02` | whether the production `workflow.sqlite` currently has rows in `execution_snapshots` (grep says no writer, but a historical writer may have existed) | production DB not queried | one SELECT probe on `/opt/llm/db/workflow.sqlite` before deploy; rows would be orphaned data, removed only on archive-and-recreate | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/db/schema_sql.py` | Modify | workflow schema creation (fresh DBs only) | 17 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/tool_call_state_ops.py` | Modify | tool-call lifecycle reads/writes | 2 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/state_store.py` | Modify | facade signature | 6 | N/A | not applicable (rsynced) |
| `scripts/agent/context.py` | Modify | tool-call request dataclass | N/A | N/A | not applicable (rsynced) |
| docs (3 files) | Modify | docs only | N/A | N/A | not applicable |

## Design
**Decision: retire.** The table has had zero writers since introduction; `tool_call_state` rows always carry null `snapshot_id`; the FK target is permanently empty. Keeping it forces `wfaudit003` to gate an empty table and `wfaudit002` to design around a dead FK.

**Existing databases.** No migration: new code never names `snapshot_id` in INSERT column lists and never reads the column, so a legacy database with the column behaves identically (column stays NULL). New databases never create it. The schema gate (`wfaudit003`) will therefore require neither the table nor the column, and legacy databases pass it (extra tables/columns are not gate failures — gate checks required-shape presence only).

**Plumbing removal.** Delete the parameter at every layer in one change (ops → facade → request dataclass → tool_runner nothing changes because it never passed the argument) so no half-removed API remains.

## Implementation steps
1. **Phase 1: Code retirement (`REQ-001`, `REQ-002`).** Remove DDL table/column and the `snapshot_id` plumbing across the four source files.
2. **Phase 2: Tests (`REQ-003`, `REQ-005`).** Retarget workflow/schema tests; add the legacy-shape compatibility test.
3. **Phase 3: Documentation (`REQ-004`).** Update the three docs; run docs checkers.

### Release units
**Unit**: wfaudit010-full | **Phases**: 1, 2, 3 | **Reason**: single decision applied atomically across DDL, code, tests, docs; existing databases are untouched by design.

## Validation plan
- `uv run pytest tests/agent/workflow/ tests/db/ -q` after Phases 1-2; full `uv run pytest tests/ -q` before completion.
- `grep -rn "execution_snapshots\|snapshot_id" scripts/` returns only intentional retirement comments.
- Lint/type gates per `rules/toolchain.md`; docs checkers (`check_docs_structure.py` on edited docs, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent --domain db`) after Phase 3.
- Confirm `scripts/shared/execution_snapshot.py` (live shared-domain feature) is byte-identical after the change.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A future feature needs deployment-fingerprint replay equality | Low | Medium (schema must be re-added) | Decision recorded in docs and this plan; re-adding is a fresh-schema change since no migration path exists |
| Legacy-shape database breaks on code paths that assume the column is gone (or vice versa) | Low | Medium | Explicit compatibility test (Phase 2) for both shapes |
| docs checkers flag removals as missing-symbol findings | Medium | Low | Update every doc row in the same change; run checkers before completion |

## Execution Status
### Execution Status
| Work Item | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|
| Phase 1: code retirement | Planned | engineer | | | |
| Phase 2: tests | Planned | engineer | | | |
| Phase 3: documentation | Planned | engineer | | | |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203223_wfaudit010_snapshots-never-written.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084001
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem + validation | `scripts/db/schema_sql.py` | Fresh DB has no table/column | schema test |
| `REQ-002` | Issue Required Changes | ops/state_store/context | No `snapshot_id` in API | grep + compile |
| `REQ-003` | Plan Design (legacy compatibility) | ops layer | Legacy-shape DB works | compatibility fixture test |
| `REQ-004` | Issue Problem (stale doc claims) | 3 docs | Retirement stated | docs checkers |
| `REQ-005` | Issue Testing Expectations | workflow/db tests | Suite green | pytest |

## Notes
- Validation evidence lives in the issue's `## Adversarial Validation` section (live checker/grep runs at HEAD `926dbc109`).
- This plan is the gate for `wfaudit003` (gate table list) and `wfaudit002` (tool_call_state key design must not resurrect the FK).

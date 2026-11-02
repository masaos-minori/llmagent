## Goal
- Write a repository-specific checklist for changes to persisted SQLite schema (DDL, versions, migrations) as `rules/persisted-schema-change.md`, and make the planning and design skills load it, so known pitfalls are checked when the Plan is written instead of being found during implementation.

## Priority
High

## Scope
- **In-Scope**:
  - A new rule file stating each pitfall, why it matters here, and a verification (a command, a test, or a scratch-database recipe), covering at least the seven pitfalls named in the Issue.
  - References from `skills/issue-to-plan/workflow-path-b.md` and `skills/python-design/workflow.md` (Step 8d), a pointer in `skills/python-implementation/SKILL.md`, and a conditional-load entry in `routing.md`.
  - A recorded decision between a scratch-database probe tool and a documented recipe.
  - A retroactive review of the archived `wfrecovery001` Plan, recorded as a mapping from each historical finding to a checklist item.
- **Out-of-Scope**:
  - Changing how migrations are executed (`scripts/shared/db_migrations.py`), the DDL, or any existing Plan.
  - Rewriting open Plans to follow the checklist.
  - Non-SQLite persistence.
- **Dependencies**: Sequencing, non-blocking: `plans/done/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md` (procedures generated and Plan archived 2026-11-02, code not yet implemented) adds the runner's opt-in foreign-key switch and pre-commit foreign-key check that the cascade item should cite. If it has not landed when this Plan is implemented, the cascade item states its verification through the scratch-database recipe and cites that Plan by path; the item text is updated when the runner contract exists. This Plan changes no file that Plan targets (`tools/check_plan_target_overlaps.py` reports no overlap for this Plan). Related, no ordering: the Plan filed from `issues/20261030-191006_flowimp001_consumer-impact-scan.md` (finds consumers; this Plan checks the design of the change itself).

## Background
- `Operationally observed` (2026-10-30, from the Issue): during `dbmig001`, `wftaskapi001`, and `wfrecovery001`, seven pitfalls were each caught during procedure generation or implementation, depending on what the author happened to check: the workflow database version lives in a table, not `PRAGMA user_version`; a new ledger table changes the schema fingerprint and forces a version stamp and baseline step; `DROP TABLE` with foreign keys on cascades and removes child rows, and `PRAGMA foreign_keys=OFF` does nothing inside a transaction; a `NOT NULL` column without a default breaks every existing `INSERT`; a migration must be frozen text while the result must equal the canonical DDL; a test that pinned the registry as empty fails at the first registration; rows with an old meaning need an explicit decision and owner confirmation.
- `Explicit in code` (checked in Step 3): `skills/python-design/workflow.md` Step 8d asks only for "the migration path for existing data/callers"; `skills/issue-to-plan/workflow-path-b.md` has no storage-specific section. A search of `skills/`, `templates/`, and `rules/` for foreign key, foreign_keys, cascade, and table rebuild finds nothing.
- `Explicit in code` (checked in Step 3): the workflow database stores its version in the `workflow_schema_version` table (`scripts/db/schema_sql.py`, `scripts/db/create_schema.py`); the event bus database uses `PRAGMA user_version` (`scripts/eventbus/migrate.py`). The migration framework is `scripts/shared/db_migrations.py` and `scripts/db/migrations_workflow.py`; `scripts/shared/eventbus_schema_fingerprint.py` holds the event bus fingerprint.
- Verified in Step 2 (2026-11-02): the Issue's list of queued Plans (`toolexec001`, `wflease001`, `dlqbox001`, `ragcorpus001`) is stale; all four are archived in `plans/done/`. The pending schema work is `dbmigrunner001` (Plan archived with procedures in `implementations/`, runner code not yet changed), which concerns the same runner gap as the foreign-key pitfall (`scripts/shared/db_migrations.py` has no foreign-key handling today).

## Problem
Whether a persisted-schema Plan covers the cascade, versioning, fingerprint, default, and data-meaning questions depends on the author's memory. The cost of a miss is a wrong design in a Frozen Plan or, in the cascade case, silent loss of child rows.

## Reason for Change
Every persisted-state Plan changes a `*.sqlite` schema, and the repository now has a migration framework whose preconditions are specific enough to list. The checklist makes those preconditions a planning-time check.

## Implementation Intent
Write the checklist once as a short rule file and load it where schema changes are planned and designed. Each item states the pitfall, why it matters here, and how to verify it. The checklist is guidance, not a gate. Decide separately whether a scratch-database probe tool earns its upkeep, and record the decision with its reason.

## Requirements
- `REQ-001`: `rules/persisted-schema-change.md` MUST exist and state, for each of at least the seven pitfalls, the rule and a stated verification; it MUST cite the framework contract by path and MUST NOT copy implementation detail forbidden by `skills/DESIGN.md`.
- `REQ-002`: `skills/issue-to-plan/workflow-path-b.md` and `skills/python-design/workflow.md` (Step 8d) MUST load and apply the rule for schema changes, `skills/python-implementation/SKILL.md` MUST point to it when the change touches DDL, and `routing.md` MUST have a conditional-load entry for schema, DDL, version, and migration work.
- `REQ-003`: The tool-or-recipe decision MUST be recorded with its reason in the rule file.
- `REQ-004`: The checklist MUST be applied retroactively to the archived `wfrecovery001` Plan, and the result MUST be recorded as a mapping from each historical finding to a checklist item, or a statement of why one is not covered.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `rules/persisted-schema-change.md` | New file: the checklist, the decision record, and the retroactive mapping | New file; no storage-specific checklist exists (`rules/` directory exists) | REQ-001, REQ-003, REQ-004 / AC-1, AC-3, AC-4 | `rg` for foreign key, cascade, table rebuild in `skills/`, `templates/`, `rules/` returns nothing (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/issue-to-plan/workflow-path-b.md` | Load and apply the rule for schema changes | The file has Architecture, Dependency, Historical, and Operational sections and no storage check | REQ-002 / AC-2 | section list of the file (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/python-design/workflow.md` | Step 8d loads and applies the rule | Step 8d asks only for a migration path for existing data | REQ-002 / AC-2 | "Step 8d: Note migration path and documentation update points" (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/python-implementation/SKILL.md` | A pointer when the change touches DDL | The Composition rules list the skills it composes with and have no schema pointer | REQ-002 / AC-2 | "Composition rules" section (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `routing.md` | Conditional-load entry | The "Conditional load" list covers `skills/DESIGN.md` and `rules/env.md` only | REQ-002 / AC-2 | "Conditional load" section (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/db_migrations.py` | Framework contract the checklist cites by path | REQ-001 |
| `scripts/db/migrations_workflow.py` | Registered steps, frozen migration text, and fingerprint postcondition | REQ-001 |
| `scripts/shared/eventbus_schema_fingerprint.py` | Fingerprint behavior behind the version-stamp pitfall | REQ-001 |
| `scripts/db/schema_sql.py` | Canonical workflow DDL and `workflow_schema_version` table | REQ-001 |
| `scripts/db/create_schema.py` | Version recording path | REQ-001 |
| `scripts/eventbus/migrate.py` | `PRAGMA user_version` usage for the event bus database | REQ-001 |
| `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` | Archived Plan reviewed retroactively | REQ-004 |
| `plans/done/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md` | Archived Plan (procedures generated, code not implemented) that adds the runner's foreign-key switch the cascade item cites | REQ-001 |
| `skills/DESIGN.md` | Docs content policy limits on copying implementation detail | REQ-001 |
| `rules/env.md` | Conditional-load companion entry and DB architecture | REQ-002 |

## Acceptance Criteria
- AC-1 (`REQ-001`): `rules/persisted-schema-change.md` exists, every item has a stated verification, and it cites the framework contract by path without code excerpts.
- AC-2 (`REQ-002`): The two skills load the rule for schema changes, `skills/python-implementation/SKILL.md` points to it, `routing.md` has the entry, and `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- AC-3 (`REQ-003`): The tool-or-recipe decision and its reason are recorded in the rule file.
- AC-4 (`REQ-004`): The retroactive review is recorded and maps each historical finding to a checklist item, or states why one is not covered.

## Tests
- `REQ-001` to `REQ-003`: the skill and rules checkers named in `routing.md` for changed `skills/*.md` and `rules/*.md` files.
- `REQ-004`: a read-through of the archived Plan against the checklist, with the mapping recorded (no code test).
- Not applicable: no probe tool is built (decision in Design), so no tool tests are planned.

## Documentation Impact
- N/A: this Plan changes workflow rules and skills, which are not `docs/*.md`. The rule file is the documentation of record for the checklist (REQ-001 to REQ-004).

## Assumptions
- A1: SQLite-specific items are enough for the first version because every persisted store in scope is SQLite (from the Issue).
- A2: The checklist belongs under `rules/` and is loaded conditionally through `routing.md`, rather than inside a skill reference, because three skills need it and `skills/DESIGN.md` asks shared rules to live in one file. Falsifiable by the owner preferring a skill reference.
- A3: Decision (REQ-003): a documented scratch-database recipe inside the rule file is sufficient and no probe tool is built now. Reasons: the existing framework already runs a fingerprint postcondition and per-step tests; a probe needs a seeded copy shaped per change, so reuse across Plans is unproven; `AGENTS.md` Global Rule 7 asks for a tool after three repetitions of the same operation. The decision is revisited when three Plans have used the recipe. Falsifiable by a Plan author reporting the recipe is too costly to repeat.
- A4: The seven pitfalls in the Issue's Background are the origin findings, so the retroactive mapping can be written as an origin table in the rule file, with the list of findings the checklist would have raised at planning time carried in the implementing change's report.
- A5: `git-fame` is not used; Bus Factor is `N/A` (single-owner repository).
- A7: Step 3a correction (plan-to-implementation-procedure, 2026-11-02): `dbmigrunner001` Plan moved to `plans/done/` after its procedures were generated; its path references were updated, and the runner code (`scripts/shared/db_migrations.py`) still has no foreign-key handling (rg verified), so UNK-02 wording is unchanged.
- A6: Overlap judgment (Step 8b, `check_plan_target_overlaps.py`): `routing.md` is also a target of `plans/20261102-075445_flowimp005_gates-hook-parity.md`. Judged compatible: that Plan adds rows to the "When to run which tool" table, this Plan adds an entry to the "Conditional load" list, so the two edits touch different sections.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the rule belongs under `rules/` or inside a skill reference | Owner preference not stated | Proceed with `rules/` (A2); revisit on owner feedback | False |
| UNK-02 | Whether `dbmigrunner001` will land before this Plan is implemented, which fixes the wording of the cascade item | Implementation order not decided (owner decides) | Check the Plan status at implementation start; use the recipe wording if it has not landed | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `rules/persisted-schema-change.md` | Create | Low (new; loaded only for schema work) | 0 | N/A | not applicable (rsynced) |
| `skills/issue-to-plan/workflow-path-b.md` | Modify | Low (Path B plans only) | 3 | N/A | not applicable (rsynced) |
| `skills/python-design/workflow.md` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `skills/python-implementation/SKILL.md` | Modify | Medium (entry skill for code changes) | 4 | N/A | not applicable (rsynced) |
| `routing.md` | Modify | Medium (loaded by every task) | 28 | N/A | not applicable (rsynced) |

## Design
- Placement: a rule file with one section per pitfall, each stating the rule, why it matters in this repository, and the verification. Items are verifiable checks, not general warnings; an item without a verification is not written (the Issue's stop condition).
- Items (the seven pitfalls): version storage per database (table versus `PRAGMA user_version`); fingerprint-driven version stamp and baseline step; foreign-key cascade on table rebuild and the connection-level setting; `NOT NULL` without default and the release-unit coupling of schema and write path; migration text frozen versus canonical DDL equality; registry-pinning tests; old-meaning rows and owner confirmation.
- Verification forms: a command (for example `uv run python tools/check_db_separation.py`), a test, or a scratch-database recipe (apply the candidate change to a seeded copy; compare row counts, run the foreign-key check, compare the fingerprint).
- Loading: `skills/issue-to-plan/workflow-path-b.md` and `skills/python-design/workflow.md` load the rule when the change touches DDL, schema versions, or migrations; `routing.md` adds a conditional-load entry. The rule file does not link back to those skill sections, to keep `check_skills_heading_cycles.py` clean.
- Decision record: Assumption A3 is written into the rule file under a short "Decision" heading.
- Retroactive review: the archived `wfrecovery001` Plan is read and each historical finding is mapped to an item in an origin table; unmapped findings are named with a reason.
- Compatibility: no migration code, DDL, or Plan is edited.

## Implementation steps
1. **Phase 1: Write the checklist**
   - [ ] Write `rules/persisted-schema-change.md` with the seven items, the decision record, and the origin table (`REQ-001`, `REQ-003`; `rules/persisted-schema-change.md`)
   - [ ] Read the archived `wfrecovery001` Plan against the checklist and record the mapping in the origin table (`REQ-004`; `rules/persisted-schema-change.md`)
2. **Phase 2: Load the rule**
   - [ ] Add the load and apply instruction to `skills/issue-to-plan/workflow-path-b.md` and Step 8d of `skills/python-design/workflow.md` (`REQ-002`; `skills/issue-to-plan/workflow-path-b.md`, `skills/python-design/workflow.md`)
   - [ ] Add the DDL pointer to `skills/python-implementation/SKILL.md` and the conditional-load entry to `routing.md` (`REQ-002`; `skills/python-implementation/SKILL.md`, `routing.md`)
3. **Phase 3: Verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Run `check_skills_references.py` and `check_skills_heading_cycles.py` as named in the Validation plan (`REQ-001` to `REQ-004`; all rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `rules/persisted-schema-change.md`, the two skills, `skills/python-implementation/SKILL.md`, `routing.md` | Reference and heading checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | no findings |
| `rules/persisted-schema-change.md` | Manual read-through of each item's verification | read each item; confirm a command, test, or recipe is named | every item has a verification |
| `rules/persisted-schema-change.md` | Retroactive review | read `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` against the checklist | mapping recorded for each historical finding |

## Risks
- **Risk**: The checklist duplicates or contradicts the framework's own docstrings and goes stale. → **Mitigation**: items cite the framework by path and state rules and checks, not code; `skills/DESIGN.md` forbids copying implementation detail.
- **Risk**: The cascade item describes a runner capability that does not exist yet (`dbmigrunner001` procedures generated, runner code not yet changed). → **Mitigation**: UNK-02; the item uses the scratch-database recipe wording until the runner contract exists, and cites the Plan by path.
- **Risk**: A new rule file in `rules/` creates a heading-level reference cycle with the skills. → **Mitigation**: the rule file does not reference skill sections; `check_skills_heading_cycles.py` runs in Phase 3.
- **Risk**: A checklist read as a gate blocks Plans unnecessarily. → **Mitigation**: the rule states it is guidance, not a gate (Issue Implementation Intent).
- **Risk**: The retroactive review reads an archived Plan, which the workflow normally does not read. → **Mitigation**: the read is a one-time, read-only evidence step named by the Issue and limited to that file.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the checklist and the retroactive mapping: `rules/persisted-schema-change.md` | Completed | — | 20261102-094925 | Procedures archived; full suite deferred to plan end (docs-only) |
| 2 | Load the rule: `skills/issue-to-plan/workflow-path-b.md`, `skills/python-design/workflow.md`, `skills/python-implementation/SKILL.md`, `routing.md` | Completed | — | 20261102-094925 | Procedures archived; full suite deferred to plan end (docs-only) |
| 3 | Verification of all changed files | Completed | — | 20261102-095901 | checkers and full suite passed (1 known pre-existing failure) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-084616_01_rules_persisted-schema-change.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-084616_02_skills_issue-to-plan_workflow-path-b.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-084616_03_skills_python-design_workflow.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-084616_04_skills_python-implementation_SKILL.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-084616_05_routing.md.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-191222_flowimp004_schema-change-checklist.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-075753
- **Related target files**: `rules/persisted-schema-change.md`, `skills/issue-to-plan/workflow-path-b.md`, `skills/python-design/workflow.md`, `skills/python-implementation/SKILL.md`, `routing.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (checklist, seven pitfalls); Background | `rules/persisted-schema-change.md` | Phase 1 | AC-1 | manual read-through; reference checkers | Explicit in issue |
| REQ-002 | Required Changes (reference from skills, routing row) | `skills/issue-to-plan/workflow-path-b.md` | Phase 2 | AC-2 | reference and heading checkers | Explicit in issue |
| REQ-002 | Target Files (`skills/python-design/workflow.md` Step 8d) | `skills/python-design/workflow.md` | Phase 2 | AC-2 | reference and heading checkers | Confirmed by repository evidence |
| REQ-002 | Target Files (`skills/python-implementation/SKILL.md` pointer) | `skills/python-implementation/SKILL.md` | Phase 2 | AC-2 | reference and heading checkers | Explicit in issue |
| REQ-002 | Required Changes (routing row) | `routing.md` | Phase 2 | AC-2 | reference and heading checkers | Explicit in issue |
| REQ-003 | Required Changes (record the tool-or-recipe decision) | `rules/persisted-schema-change.md` | Phase 1 | AC-3 | manual read-through | Explicit in issue |
| REQ-004 | Required Changes (retroactive application to `wfrecovery001`) | `rules/persisted-schema-change.md` | Phase 1 | AC-4 | retroactive read-through | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-084616 -->
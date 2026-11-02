## Goal
- Create `rules/persisted-schema-change.md`, the planning-time checklist for persisted SQLite schema changes, with the decision record and the retroactive `wfrecovery001` mapping (`REQ-001`: checklist with verifications; `REQ-003`: tool-or-recipe decision; `REQ-004`: retroactive mapping).

## Scope
- Create one new Markdown rule file. No change to migration code, DDL, or any Plan.
- Docs-only change that is not `docs/*.md`; the rule file is the documentation of record.

## Assumptions
- A1: The rule is guidance, not a gate (Plan Risks). Each item must name a verification (command, test, or scratch-database recipe); an item without one is not written.
- A2: Plan A3 holds: a documented scratch-database recipe is enough and no probe tool is built; the rule states this under a short "Decision" heading with the reasons and the revisit condition (three Plans have used the recipe).
- A3: Plan UNK-02: `dbmigrunner001` code has not landed (Step 3a: `rg -i foreign scripts/shared/db_migrations.py` returns nothing; its Plan is archived at `plans/done/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md` and its procedures exist). The cascade item therefore states its verification through the scratch-database recipe and cites that Plan by path. If the runner contract exists when this is implemented, cite the contract instead.
- A4: The rule file must not link back to skill sections (avoids `check_skills_heading_cycles.py` findings). It cites framework files by path only, with no code excerpts (`skills/DESIGN.md` content policy).
- A5: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): `routing.md` is targeted by six Frozen Plans (flowimp001, 003, 004, 005, 010, 011). Judged compatible: the others add rows to "When to run which tool" or a different section; this Plan only adds one entry to the "Conditional load" list. No conflict or sequencing dependency. Other Plans' judgments (A5-A7 in their Assumptions) agree.
- A6: The seven pitfalls come from the Issue Background; line-level facts about the framework are re-read from the Reference Files at implementation time, not copied from this document.

## Design decisions
- One section per pitfall, each with three parts: rule, why it matters in this repository, verification. Seven items: (1) version storage per database (`workflow_schema_version` table in `scripts/db/schema_sql.py` and `scripts/db/create_schema.py` versus `PRAGMA user_version` in `scripts/eventbus/migrate.py`); (2) fingerprint-driven version stamp and baseline step (`scripts/shared/eventbus_schema_fingerprint.py`, `scripts/db/migrations_workflow.py`); (3) foreign-key cascade on `DROP TABLE` and the fact that `PRAGMA foreign_keys=OFF` is a no-op inside a transaction; (4) `NOT NULL` column without a default and the release-unit coupling of schema and write path; (5) frozen migration text versus equality with the canonical DDL; (6) tests that pin the migration registry as empty; (7) old-meaning rows need an explicit decision and owner confirmation.
- Short "Decision" section (Plan A3), a short "Origin" table mapping each historical finding to an item, and a one-line statement that the checklist is guidance.

## Alternatives considered
- A probe tool (scratch-database seeding and comparison): rejected for now; needs a seed shaped per change, reuse unproven, `AGENTS.md` Global Rule 7 triggers after three repetitions.
- Placing the checklist in a skill reference: rejected (Plan A2); three skills need it and `skills/DESIGN.md` asks shared rules to live in one file.

## Implementation
### Target file
`rules/persisted-schema-change.md` (new)

### Procedure
1. Read the Reference Files named for REQ-001 in the Plan (framework, DDL, version recording, event bus migrate, `skills/DESIGN.md`) to confirm each item's current facts.
2. Write the file: title and one-paragraph purpose (guidance, not a gate; applies to persisted SQLite schema, DDL, versions, migrations), the seven item sections, the "Decision" section, and the "Origin" table.
3. Read `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` once, read-only, against the seven items and record each historical finding in the Origin table with its item, or name the finding as uncovered with a reason (`REQ-004`).

### Method
- Each item states its verification concretely: for example `uv run python tools/check_db_separation.py`, the named existing test, or the scratch-database recipe (apply the candidate change to a seeded copy; compare row counts; run `PRAGMA foreign_key_check`; compare the fingerprint).
- Describe the recipe once, in its own short section, and have items 3, 4, 5 refer to it.
- Cite framework files by repository path; do not paste code or line numbers.

### Details
- Item 3 wording follows A3 above. Item 7 names the owner as the confirming party.
- The Origin table lists findings from the archived Plan; per Plan A4, the list of findings the checklist would have raised at planning time goes in the implementing change's report, not in the rule file.
- English text, no emojis; keep the file short (one screen per item at most).

## Compatibility considerations
- N/A: new file, loaded only for schema work through the `routing.md` entry (separate document).

## Security considerations
- N/A: documentation only; no secrets, paths, or credentials are written.

## Rollback considerations
- N/A: revert the commit. The other four documents of this Plan reference this file, so revert together.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`: no findings.
- Read-through: each item names a command, test, or recipe; the Origin table has a row for every finding in the archived Plan.
- `uv run python tools/check_workitem_structure.py` is not applicable to a rule file.

## Completion criteria
- File exists with seven items, each with a stated verification (AC-1).
- "Decision" section records the tool-or-recipe decision and reason (AC-3).
- Origin table maps each historical finding or states why it is not covered (AC-4).
- Both checkers report no findings.

## Out of Scope
- Skill and routing edits (documents 02 to 05), migration code, DDL, existing Plans, non-SQLite persistence.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the seven items, the recipe, and the Decision section in `rules/persisted-schema-change.md` | Pending | — | — | |
| 2 | Read the archived `wfrecovery001` Plan and record the Origin table | Pending | — | — | |
| 3 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004`
- **Source issue**: issues/20261030-191222_flowimp004_schema-change-checklist.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-075753_flowimp004_schema-change-checklist.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-084616
- **Related target files**: rules/persisted-schema-change.md

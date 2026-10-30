# Add a persisted-schema change checklist to planning and design

## Priority
High

## Summary
Add a repository-specific checklist for changes to persisted SQLite schema (DDL, versions, migrations) and make the planning and design skills load it, so that known pitfalls are checked when the Plan is written instead of being found by reading code or by hitting a failure during implementation. Decide whether a small scratch-database probe is worth a tool.

## Background
- `Operationally observed` (2026-10-30, plans `dbmig001`, `wftaskapi001`, `wfrecovery001`): the pitfalls below were each caught during procedure generation or implementation, depending on what the author happened to check:
  - the workflow database stores its version in the `workflow_schema_version` table, not in `PRAGMA user_version`, which the Plan's design assumed;
  - adding a ledger table to `scripts/eventbus/schema.sql` changes the schema fingerprint and therefore forces a version stamp bump and a registered baseline step, otherwise every existing database is refused;
  - with `foreign_keys=ON`, `DROP TABLE tasks` runs an implicit delete that cascades and removes every `attempts` row, and `PRAGMA foreign_keys=OFF` does nothing inside a transaction, so the migration connection must be opened with foreign keys off;
  - a `NOT NULL` column without a default breaks every existing `INSERT` site, which makes the schema phase and the write-path phase one release unit;
  - a migration must be a frozen text, not derived from the current canonical DDL, while the post-migration shape must still equal that DDL;
  - a test that pinned the registry as empty would have failed at the first registration;
  - rows that carried an old meaning (started markers in `processed_events`) need an explicit decision and an owner confirmation.
- `Explicit in code`: `skills/python-design/workflow.md` Step 8d only asks for "a migration path for existing data"; `skills/issue-to-plan/workflow-path-b.md` has no storage-specific check (a search for foreign key, table rebuild, and cascade in `skills/`, `templates/`, and `rules/` finds nothing).
- `Explicit in code`: `scripts/shared/db_migrations.py` and `scripts/db/migrations_workflow.py` (added 2026-10-30) now define the framework contract the checklist should point to.

## Problem
Whether a persisted-schema Plan covers the cascade, versioning, fingerprint, default, and data-meaning questions depends on the author's memory. The cost of a miss is a wrong design in a Frozen Plan or, in the cascade case, silent loss of child rows.

## Reason for Change
Several persisted-state Plans are open (`toolexec001`, `wflease001`, `dlqbox001`, `ragcorpus001`), each will change a `*.sqlite` schema, and the repository now has a migration framework whose preconditions are specific enough to list.

## Implementation Intent
Write the checklist once, as a short rule file, and load it from the places where schema changes are planned and designed. Each item states the pitfall, why it matters here, and how to verify it (a command, a test, or a probe). The checklist is guidance, not a gate. Evaluate separately whether a scratch-database probe (apply a candidate change to a seeded copy, report row counts, foreign-key check, and fingerprint difference) is reusable enough to deserve a tool, or whether a short documented recipe is sufficient.

## Target Files or Areas
- `rules/persisted-schema-change.md` (new)
- `skills/issue-to-plan/workflow-path-b.md` and `skills/python-design/workflow.md` (Step 8d) — load and apply it
- `skills/python-implementation/SKILL.md` — a pointer when the change touches DDL
- `routing.md` — a conditional-load row for schema, DDL, version, and migration work
- Optional, only if the evaluation says so: `tools/probe_schema_change.py` (new), its tests, and `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Write the checklist covering at least the seven pitfalls in Background, each with a verification step.
- Reference it from the planning and design skills and add the routing row.
- Record the tool-or-recipe decision with the reason.
- Apply the checklist retroactively to the archived `wfrecovery001` Plan and list which findings it would have raised at planning time.

## Constraints
- Docs and rules must not copy implementation detail that `skills/DESIGN.md` forbids; the checklist states the rule and the check, and cites the framework contract by path.
- No change to the migration framework or to any existing Plan.
- Rules are written in English.

## Acceptance Criteria
- `rules/persisted-schema-change.md` exists and every item has a stated verification.
- `skills/issue-to-plan/workflow-path-b.md` and `skills/python-design/workflow.md` load it for schema changes, and `routing.md` has the row.
- The retroactive review is recorded and maps each historical finding to a checklist item (or states why one is not covered).
- `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- The tool-or-recipe decision is recorded; if a tool is built, it follows `routing.md` "Adding a new tool" and is registered.

## Testing Expectations
- Skill and rules checkers named in `routing.md` for the changed files.
- If a probe tool is built: unit tests over temporary databases covering the cascade-loss case, a clean case, and a fingerprint mismatch; plus lint, type, and security checks on the tool.

## Documentation Impact
Yes. The new rule and the skill references state intent, boundaries, and failure behavior of schema changes. No code excerpts.

## Out of Scope
- Changing how migrations are executed (`scripts/shared/db_migrations.py`).
- Rewriting open Plans to follow the checklist.
- Non-SQLite persistence.

## Dependencies
N/A: none. No open issue or Plan targets these files (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30). Related: `issues/20261030-191006_flowimp001_consumer-impact-scan.md` (finds consumers; this issue checks the design of the change itself).

## Unresolved Questions
- `不明`: whether the checklist belongs under `rules/` (loaded conditionally by `routing.md`) or inside a skill reference.
- `不明`: whether a probe tool is worth its upkeep; the decision is part of the work.
- Assumption: SQLite-specific items are enough for the first version because every persisted store in scope is SQLite.

## AI Implementation Instruction
Write the checklist and the references only, plus the optional tool if the evaluation justifies it. Do not edit any Plan, the migration framework, or the DDL. State each item as a verifiable check, not a general warning. Stop and report if an item cannot be given a verification.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191222
- **Related target files**: `rules/persisted-schema-change.md`, `skills/issue-to-plan/workflow-path-b.md`, `skills/python-design/workflow.md`, `skills/python-implementation/SKILL.md`, `routing.md`, `tools/probe_schema_change.py`

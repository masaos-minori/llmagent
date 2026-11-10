## Goal
- Rewrite the `create_eventbus_schema()` sentence and the `rotate_eventbus_db()` table cell (REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this one file, Phase 5 of the Plan.
- Not in scope: any other file; a second file needed here is an additional-target discovery.
- Execution order follows the Plan's phases, not `seq`: Phase 1 (documents 03, 04), Phase 2 (05, 18), Phase 3 (the `scripts/db`, `scripts/shared`, validator, config, and test documents, one release unit), Phase 4 (01, 38, 39), Phase 5 (the document rows), Phase 6 verification.

## Assumptions
- Overlap with plans 003, 004, 005, 006 (judged in the Plan's Assumptions): sequencing or different keys; no contradiction on this file.
- The Plan's Step 3a corrections apply (EventBus tool reads `db_path` with its own reader; `eventbus_schema_version` and the DDL text accessor move to `scripts/eventbus/db_tools.py`).

## Design decisions
- Remove only what the Plan names for this file; keep every other behavior unchanged.

## Alternatives considered
N/A: the ownership decision (EventBus-side tooling, maintainer 2026-11-10) is fixed in the Plan's Design section.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. At line 49 state that the EventBus service (and its tool) creates the schema from `schema.sql`; at line 83 replace the rotate cell with the EventBus-side rotate entry.

### Method
- Documentation edit in place; English only; follow the docs content policy (intent, boundaries, failure behavior; no symbol inventories).

### Details
- Plan 005 edits other statements in this file.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `uv run python tools/check_docs_consistency.py --domain db`.

## Completion criteria
- The statement matches the post-change code and the checkers pass.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` as described in Procedure | Completed | 20261110-122422 | 20261110-122422 |  |
| 2 | Run the checkers listed in Validation plan | Completed | 20261110-122422 | 20261110-122422 |  |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261109-112538_adrrev002_agent-eventbus-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-091327_adrrev002_agent-eventbus-coupling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-102050
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
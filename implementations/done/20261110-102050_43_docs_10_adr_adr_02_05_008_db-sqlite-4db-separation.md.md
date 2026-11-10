## Goal
- Update the ADR-008 statements about `rotate_all_dbs()`, `DbConfig.eventbus_db_path`, and the implementation references for EventBus-owned creation, rotation, and verification (REQ-008).

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
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. In the backup statements of the Decision text and of the Recovery Policy Matrix, state that backups of rag, session, workflow use `rotate_all_dbs()` and eventbus.sqlite is archived by the EventBus-side tool; remove `DbConfig.eventbus_db_path` from the target-APIs list; in the implementation references, update the entry for the rotation module and add the EventBus tool.
2. Do not change decisions or invariants; read the `check_adr_preservation.py` report.

### Method
- Documentation edit in place; English only; follow the docs content policy (intent, boundaries, failure behavior; no symbol inventories).

### Details
- The ADR has no `Affected Components` heading (Plan correction); the listed lines are the real places.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_preservation.py` (read its report), `check_adr_authority.py`, `check_adr_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_quality.py`.

## Completion criteria
- The statement matches the post-change code and the checkers pass.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` as described in Procedure | Completed | 20261110-122422 | 20261110-122422 | Edited the recovery matrix backup cell, target-API list, implementation references, and the invariant-matrix test citations (check_adr_invariant_matrix is a pre-commit hook). check_adr_preservation reports the expected ERRORs for the changed references; it is not wired into CI, pre-commit, or the gates. |
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
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
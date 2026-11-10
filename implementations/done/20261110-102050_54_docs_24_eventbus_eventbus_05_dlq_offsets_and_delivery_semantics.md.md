## Goal
- Reword the archive sentence that names `rotate_eventbus_db()` (REQ-008; fallout row added in Step 3a).

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
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. In the retention sentence of the dead-letter section, replace the removed Agent-side rotate function name with the EventBus-side rotate entry and fix the parenthesis that says no retention logic exists in the Agent-side rotation module.

### Method
- Documentation edit in place; English only; follow the docs content policy (intent, boundaries, failure behavior; no symbol inventories).

### Details
- Lightweight row.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `uv run python tools/check_docs_consistency.py --domain eventbus`.

## Completion criteria
- The statement matches the post-change code and the checkers pass.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` as described in Procedure | Completed | 20261110-122422 | 20261110-122422 |  |
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
- **Related target files**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
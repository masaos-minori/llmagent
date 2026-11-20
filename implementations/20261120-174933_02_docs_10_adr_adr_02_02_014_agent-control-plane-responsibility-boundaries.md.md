## Goal
Extend the ADR-014 Workflow Engine responsibility bullet with the task-status vocabulary the code persists, per plan REQ-002 (name both state vocabularies exactly as defined in the schema).

## Scope
**Release unit**: N/A: not part of a release unit
- Edit only the `**Workflow Engine**` bullet in the Decision section (file L59). No other section changes.

## Assumptions
- The addition is descriptive of already-implemented behavior (like the existing stage list), so it needs no pending-amendment record (Plan Assumption).
- Gated Plan: `tools/plan_dependency_order.py` reports this plan gated (prose) by `issues/20261117-123022_adrchk022_history-comment-removal.md` phase all; the owner chose to proceed with this Plan first (2026-11-20). The overlap is section-disjoint (adrchk022 targets history text).

## Design decisions
- Vocabulary is copied verbatim from the authoritative DDL (`tasks.status` CHECK constraint in `scripts/db/schema_sql.py` L171), not paraphrased.
- Task status is stated as a second vocabulary distinct from the stage vocabulary; the existing `plan -> execute -> verify -> complete/failed` stage text stays unchanged.

## Alternatives considered
- N/A: docs-only vocabulary sentence; no design surface beyond which authoritative source to copy (decided above).

## Implementation
### Target file
- `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`

### Procedure
1. In the `**Workflow Engine**` bullet (L59), after the existing stage-transitions text `(`plan -> execute -> verify -> complete/failed`) and retries`, insert the task-status sentence (Details).

### Method
State the task-status vocabulary as part of the same Workflow Engine responsibility sentence, with its source and the `halted` trigger. No history wording; do not rename or re-explain the existing stage list.

### Details
Insert after `and retries`:

task status (`pending`/`running`/`completed`/`failed`/`halted`, the `tasks.status` CHECK constraint values in `scripts/db/schema_sql.py`; `halted` is persisted when a task exceeds its `max_attempts`), distinct from the stage vocabulary above

## Compatibility considerations
- N/A: docs-only; the vocabulary matches `scripts/agent/workflow/models.py` `TASK_STATUSES` (L16) and the DDL, both unchanged.

## Security considerations
- N/A: no security surface (vocabulary statement only).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py` — 0 errors, no new warning.
- Vocabulary re-checked against `scripts/db/schema_sql.py` L171 (`pending`, `running`, `completed`, `failed`, `halted`) and `scripts/agent/workflow/workflow_engine.py` L233 (`halted` on max attempts).
- `uv run pytest tests/db/test_create_schema.py -q` — DDL pins unchanged (no code edit expected).

## Completion criteria
- The bullet names both vocabularies; the five status strings match the CHECK constraint exactly; `complete/failed` remains only in the stage list; the validation commands pass.

## Out of Scope
- Any `complete` vs `completed` "cleanup" (Plan: claim invalid — only the stage term `complete` exists in the file); code or schema changes; other ADRs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) |
| 2 | Run the documentation checkers named in `routing.md` Tools (Validation plan) | Pending | — | — | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) |

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
- **Requirement ID**: REQ-002 (add the task-status vocabulary to the ADR-014 Workflow Engine bullet)
- **Source issue**: issues/20261117-123021_adrchk021_adr-editorial-defects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-172527_adrchk021_adr-editorial-defects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-174933
- **Related target files**: docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md

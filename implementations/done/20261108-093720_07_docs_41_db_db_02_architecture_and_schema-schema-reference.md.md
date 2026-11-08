# Implementation procedure: `docs/41_db/db_02_architecture_and_schema-schema-reference.md` — state the allowed status vocabularies

## Goal
Record the enforced status vocabulary per workflow status column in the schema reference (`REQ-003`/`REQ-004` doc propagation).

## Scope
**Release unit**: wfaudit005-full

- One prose addition in the workflow database section (around L46, `Initialized by create_workflow_schema()...`).

## Assumptions
- The doc edit lands after Phases 1-2 (the doc must describe implemented behavior).
- Revalidation confirmed the doc carries no `status` text today and no table map row for `tasks`/`attempts` status columns; this is an addition, not a correction (target row added to the Plan at revalidation).

## Design decisions
- Add one sentence naming both vocabularies and the enforcement mechanism (code-side helpers for all databases, DDL CHECK for fresh databases); no constant names or file paths beyond the mechanism sentence (DESIGN Docs content policy).

## Alternatives considered
- N/A: docs-only addition.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md`

### Procedure
- After the sentence describing the workflow task tables (L46), state: `tasks.status` accepts only `pending`, `running`, `completed`, `failed`, `halted`; `attempts.status` accepts only `running`, `completed`, `failed`; writes are validated by the workflow ops helpers, and fresh databases additionally carry matching CHECK constraints (`tool_call_state.state` already had this pattern).

### Method
- One paragraph appended in place.

### Details
- `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` needs no edit: confirmed at revalidation it carries no status-column text (Plan Documentation Impact).

## Compatibility considerations
- N/A: docs-only.

## Security considerations
- N/A: docs-only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| edited doc | structure/quality gates | `uv run python tools/check_docs_structure.py docs/41_db/db_02_architecture_and_schema-schema-reference.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain db --domain agent` | No findings |

## Completion criteria
- The schema reference states both allowed status sets and their enforcement accurately against the implemented code (`REQ-003`, `REQ-004`); docs checkers pass.

## Out of Scope
- Column-by-column listings for other tables (out of the row's responsibility).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the prose addition described in Implementation > Procedure/Method/Details | Completed | 20261108-130652 | 20261108-130652 | Land after Plan Phases 1-2 memo3 adversarial verification pass at HEAD 11c20696a: stale check clean; doc has no status/tool_call_state text and L46 anchor confirmed; agent_04_03 confirmed no-edit-needed; no document correction required vocabulary + enforcement sentence added after the task-tables sentence in section 7 |
| 2 | Run the docs checkers named in the Validation plan | Completed | 20261108-130652 | 20261108-130652 | check_docs_structure, check_docs_content_policy, check_docs_consistency --domain db --domain agent all clean |

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
- **Requirement ID**: `REQ-003` (CHECK vocabularies documented), `REQ-004` (declared vocabularies documented)
- **Source issue**: `issues/20261107-203218_wfaudit005_unvalidated-status-writes.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084002_wfaudit005_unvalidated-status-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-093720
- **Related target files**: `docs/41_db/db_02_architecture_and_schema-schema-reference.md`
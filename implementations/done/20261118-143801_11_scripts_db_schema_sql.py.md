## Goal
Rewrite the `session.sqlite` recreate comment so it states the ADR-008 rule instead of a deferred decision (`REQ-005`); comment only.

## Scope
**Release unit**: ['Rewrite the comment and record the fingerprints (Implementation > Procedure)', 'Add or update tests per Validation plan: no test change needed; run the existing tests', 'Run the validation sequence (`rules/toolchain.md`)']
- In scope: the comment block before `_SESSION_SCHEMA_TEMPLATE`; no DDL, no code.

## Assumptions
- Comments are stripped by `_COMMENT_RE` in `scripts/shared/schema_fingerprint.py` before the fingerprint is computed (checked in Step 3a), so the fingerprint does not change.
- Procedure 02 has landed: ADR-008 Decision Detail #22 exists.

## Design decisions
- The comment follows the Current-Specification-Only policy: no history wording, no reference to an archived issue.

## Alternatives considered
N/A: the maintainer's decisions are recorded in the Plan's Design section.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Replace the six-line comment (`session.sqlite uses recreate-only DDL ...`) with a comment stating: the DDL is create-only; session data (history, semantic and episodic memory) is not re-derivable from an external source, so ADR-008 Decision Detail #22 requires the operator to export conversations with `/session export` before archiving and recreating; memory is recovered from the JSONL archive with `/memory rebuild`.
2. Before editing, compute the fingerprints of `build_session_schema_sql(dims)`, `build_workflow_schema_sql()`, and `build_eventbus_schema_sql()` with `shared.schema_fingerprint.expected_fingerprint` and record them in the Notes; compute them again after procedure 12 and require equality.

### Method
- Keep the comment to about five lines of at most 88 characters.

### Details
- Run `uv run python tools/check_db_separation.py` after the edit.

## Compatibility considerations
N/A: documentation or comment text only.

## Security considerations
N/A: no approval statement is written or simulated; pending bullets only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `scripts/` change: committed and pushed first; deploying is the user's decision (`skills/deploy/SKILL.md`).

## Completion criteria
- `uv run ruff format --check scripts/db/schema_sql.py`, `uv run ruff check scripts/db/schema_sql.py`, `uv run mypy scripts/db/schema_sql.py`, `uv run python tools/check_db_separation.py`, `uv run pytest tests/db/test_create_schema.py`, `uv run python tools/check_docstrings.py`.

## Out of Scope
- The comment states the rule without history wording; fingerprints are unchanged; the checks pass.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | - | Completed | 20261118-150735 | 20261118-150735 | Changed: scripts/db/schema_sql.py (comment only). Fingerprints before and after: session 72101732ce18feb5, workflow ad4d236562148f8b, eventbus 559f024815cbeeb1 (unchanged). |
| 2 | — | Completed | 20261118-150735 | 20261118-150735 | — |
| 3 | A | Completed | 20261118-150735 | 20261118-150735 | — |
| 4 | n | Completed | 20261118-150735 | 20261118-150735 | — |
| 5 | y | Completed | 20261118-150735 | 20261118-150735 | — |
| 6 | — | Completed | 20261118-150735 | 20261118-150735 | — |
| 7 | D | Completed | 20261118-150735 | 20261118-150735 | — |
| 8 | D | Completed | 20261118-150735 | 20261118-150735 | — |
| 9 | L | Completed | 20261118-150735 | 20261118-150735 | — |
| 10 | , | Completed | 20261118-150735 | 20261118-150735 | — |
| 11 | — | Completed | 20261118-150735 | 20261118-150735 | — |
| 12 | a | Completed | 20261118-150735 | 20261118-150735 | — |
| 13 | n | Completed | 20261118-150735 | 20261118-150735 | — |
| 14 | y | Completed | 20261118-150735 | 20261118-150735 | — |
| 15 | — | Completed | 20261118-150735 | 20261118-150735 | — |
| 16 | c | Completed | 20261118-150735 | 20261118-150735 | — |
| 17 | o | Completed | 20261118-150735 | 20261118-150735 | — |
| 18 | d | Completed | 20261118-150735 | 20261118-150735 | — |
| 19 | e | Completed | 20261118-150735 | 20261118-150735 | — |
| 20 | . | Completed | 20261118-150735 | 20261118-150735 | — |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142957_adrchk008_db-data-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-143801
- **Related target files**: `scripts/db/schema_sql.py`

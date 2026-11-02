# Replace the assertion-error claim in the workflow-observability doc

## Goal

Replace the Key Constraints sentence in
`docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md` so it states the
skip-and-warn behavior instead of an assertion error (Plan REQ-004 / AC-4).

## Scope

- One bullet at line 47: "Calling writing functions for `tool_approval` / `tool_exec` outside of a
  workflow context results in an assertion error." Nothing else in the file.

## Assumptions

- Verified 20261102: line 47 is the only "assertion error" occurrence in this file; the file's
  surrounding Key Constraints list is otherwise about workflow lifecycle and stays untouched.
- Wording must match row 03's replacement so the two docs agree.

## Design decisions

- N/A: docs-only, single bullet.

## Alternatives considered

- N/A.

## Implementation
### Target file
`docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md`

### Procedure
Replace the bullet with: calling the `tool_approval` / `approval_decision` / `tool_exec` audit
writers outside a workflow context (empty `workflow_id`) writes no event and logs one warning
naming the writer and the tool; existing silent-return guards keep their precedence.

### Details
- Keep the bullet's position in the list; match row 03's phrasing.

## Compatibility considerations

- N/A: documentation only.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py`,
  `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent`
  per `routing.md` Tools "When to run which tool".

## Completion criteria

- Neither this file nor agent_10_02 mentions an assertion error for these writers; both describe
  skip-and-warn; docs checkers pass (AC-4).

## Out of Scope

- The audit-and-otel doc (row 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the Key Constraints bullet | Pending | — | — | Land with row 01, same commit as row 03 |
| 2 | Run the docs checkers (`routing.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (workflow-observability doc states skip-and-warn)
- **Source issue**: issues/20261003-180336_assertaudit001_audit-assert-risks-post-execution-crash.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-141314_assertaudit001_audit-assert-risks-post-execution-crash.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132615
- **Related target files**: docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md

# Replace the assertion-error claim in the audit doc

## Goal

Replace the Key Constraints sentence in
`docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md` so it states
the skip-and-warn behavior instead of an assertion error (Plan REQ-004 / AC-4).

## Scope

- One bullet at line 52: "Calling writing functions for `tool_approval` / `tool_exec` outside of a
  workflow context will result in an assertion error." Nothing else in the file.

## Assumptions

- Verified 20261102: line 52 is the only "assertion error" occurrence in this file; it must land
  with row 01 so the claim matches code.

## Design decisions

- N/A: docs-only, single bullet.

## Alternatives considered

- N/A.

## Implementation
### Target file
`docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`

### Procedure
Replace the bullet with: calling the `tool_approval` / `approval_decision` / `tool_exec` writing
functions outside a workflow context (empty `workflow_id`) writes no event and logs one warning
naming the writer and the tool; the missing-`audit_logger` silent return and `audit_tool_exec`'s
empty-`mcp_request_id`/`source` early return keep their precedence ahead of this check.

### Details
- Name all three writers the Plan covers (`approval_decision` is currently unlisted — REQ-004).

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

- The file contains no "assertion error" claim for these writers; the bullet describes skip-and-warn
  with guard precedence; docs checkers pass.

## Out of Scope

- The workflow-observability doc (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the Key Constraints bullet | Completed | 20261102-180240 | 20261102-180004 | Land with row 01 landed in batch 20261102-132615; red-first verified, all targets green |
| 2 | Run the docs checkers (`routing.md`) | Completed | — | 20261102-180004 | full suite 11348 passed/8 skipped; diff-cover 100%; ruff/mypy/bandit/lint-imports/check_module_size green; docs checkers green |

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
- **Requirement ID**: REQ-004 (audit doc states skip-and-warn)
- **Source issue**: issues/20261003-180336_assertaudit001_audit-assert-risks-post-execution-crash.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-141314_assertaudit001_audit-assert-risks-post-execution-crash.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132615
- **Related target files**: docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md
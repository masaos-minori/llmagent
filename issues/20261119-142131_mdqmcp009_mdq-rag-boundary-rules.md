# Replace MDQ/RAG boundary string scanning with enforceable import and AST rules

## Priority
Medium

## Summary
Enforce MDQ, RAG, and Agent dependency directions and direct-database-access restrictions with import rules and AST checks instead of filename and string scanning.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 9). `.importlinter` exists with contracts including `rag-no-agent-or-mcp_servers` and `mcp_servers-no-agent`, and none named for MDQ (`Explicit in code`, by `rg`); `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` exists. The statement that the tests acknowledge string scans are not runtime guarantees is a backlog claim and `Needs confirmation`.

## Problem
Filename allowlists can grow into broad exceptions and miss alias imports, wrappers, or indirect SQLite connection creation.

## Reason for Change
Architecture-boundary enforcement is weak; it should land before production-readiness reclassification (`issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`). No other time pressure is known.

## Implementation Intent
Boundaries are enforced by package-level import-linter rules and targeted AST checks; exceptions are narrow, owned, justified, and expiring.

## Target Files or Areas
- `.importlinter`
- `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`
- New architecture-test helpers; the design document that states the boundary guarantee (`Unknown`)

## Required Changes
- Add import-linter rules for MDQ, RAG, and Agent directions.
- Add AST checks for prohibited imports and direct SQLite connection creation; detect common alias-import patterns where practical.
- Replace filename allowlists with interface-level exceptions requiring owner, reason, and expiry; update the design document to state the actual guarantee.

## Constraints
- Do not break existing contracts (`shared-is-leaf`, `db-only-uses-shared`); `lint-imports` must stay green.

## Acceptance Criteria
- [ ] Prohibited direct database access fails CI.
- [ ] Alias imports are detected where supported.
- [ ] Exceptions are narrow and expiring.
- [ ] Boundary documentation matches test capability.

## Testing Expectations
- Positive and negative AST fixtures for alias imports and wrapper connection creation; run `lint-imports`, ruff, mypy, and the full test suite.

## Documentation Impact
Yes. State the actual enforcement guarantee and the exception policy.

## Out of Scope
- MDQ runtime behavior.

## Dependencies
- None blocking; independent of the other MDQ issues. Should land before `issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`.

## Unresolved Questions
- `不明`: how the expiry of exceptions is enforced (date in test versus CI check).
- `不明`: the design document to update.

## AI Implementation Instruction
Add failing fixtures for alias imports first. Keep changes in `.importlinter`, the boundary test, and helpers. Stop and report if a new import-linter rule fails on existing code that needs a policy decision.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-142131
- **Related target files**: `.importlinter`, `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`

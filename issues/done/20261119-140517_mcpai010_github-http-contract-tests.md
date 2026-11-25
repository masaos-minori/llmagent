# Build real GitHub HTTP security and contract integration tests

## Priority
Medium

## Summary
Add HTTP-level tests that use the real GitHub service boundary with a mocked GitHub API client, so authorization, Pydantic validation, schema publication, and deduplication are verified at `/v1/tools` and `/v1/call_tool`.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 10). Existing tests under `tests/mcp_servers/github/` are `test_formatter.py`, `test_github_exception_handlers.py`, `test_github_health_posture.py`, `test_github_mapper.py`, and `test_github_mcp_service.py` (`Explicit in code`, by listing); the claim that endpoint tests use a fake handler is from the review and `Needs confirmation`. The review's `test_github_tool_schema.py` and `test_github_security_compliance.py` do not exist and are created here.

## Problem
Characterization tests with a fake service can pass while runtime authorization and validation are absent, so they do not prove the security contract.

## Reason for Change
It is the integration gate for the GitHub and MCP changes and prevents future refactoring from bypassing guards.

## Implementation Intent
Keep characterization tests and security-contract tests clearly separated; run the latter through the deployed HTTP contract against the real service with mocked external API calls.

## Target Files or Areas
- `tests/mcp_servers/github/` (new `test_github_tool_schema.py`, `test_github_security_compliance.py`)
- GitHub MCP FastAPI application; mocked GitHub API client fixtures

## Required Changes
- Test out-of-allowlist reads, constrained global search, denied, oversized, and binary file reads, `/v1/tools` schemas including `dry_run`, unknown-argument rejection, `dedup_state` in responses, and same-key concurrent write executing once.
- Cover authenticated and unauthenticated endpoint access; separate characterization from security-contract tests.
- Provide the reusable HTTP-level MCP test fixture (real server boundary, mocked upstream client, authentication headers, `/v1/tools` schema assertions) and define the characterization-versus-authoritative-contract convention (marker or directory) for MCP tests; the CI/CD, Web Search, and MDQ issues reuse both instead of building their own.

## Constraints
- Run after the unit tests of the dependent issues pass; do not weaken existing characterization tests.

## Acceptance Criteria
- [ ] HTTP tests reject out-of-allowlist reads and constrain global search.
- [ ] HTTP tests reject denied, oversized, and binary file reads and unknown arguments.
- [ ] `/v1/tools` exposes the generated strict schemas, including `dry_run`.
- [ ] `dedup_state` is preserved in responses; a same-key concurrent write executes once.
- [ ] Characterization and security-contract tests are clearly separated.

## Testing Expectations
- The tests above are the deliverable; run ruff, mypy, and the full suite, and check the diff-cover threshold.

## Documentation Impact
Not required beyond the test layout note in the testing documentation if the repository keeps one (`Needs confirmation`).

## Out of Scope
- Implementing the behavior under test.

## Dependencies
- Depends on `issues/20261119-140509_mcpai002_github-read-security-boundary.md`, `issues/20261119-140510_mcpai003_github-pydantic-schema-source.md`, `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, `issues/20261119-140512_mcpai005_structured-execution-context.md`, and `issues/20261119-140513_mcpai006_github-write-retry-policy.md`. Blocks `issues/20261119-140520_mcpai013_github-resource-scope-refine.md` and `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`.

## Unresolved Questions
- `不明`: how the same-key concurrent test reaches the real dedup store in the HTTP test fixture.

## AI Implementation Instruction
Add tests only; if a test exposes a missing behavior, report it against the owning issue rather than fixing it here.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140517
- **Related target files**: `tests/mcp_servers/github/`

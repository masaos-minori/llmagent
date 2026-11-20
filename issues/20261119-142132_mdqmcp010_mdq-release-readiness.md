# Finalize MDQ product semantics, production readiness, test migration, and model cleanup

## Priority
Low

## Summary
Finalize supported Markdown semantics, benchmark-based production status, authoritative contract tests, and response-model cleanup after the higher-priority behavior is stable.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 10). The claims (fenced code excluded from search, all tools marked production without measured criteria, characterization tests locking legacy behavior, unused response models, empty `IndexMetadata`) are backlog claims and `Needs confirmation` against current `parser.py`, `mdq_models.py`, and the tests.

## Problem
Tool descriptions may not match parser behavior, production status lacks measured criteria, characterization tests can obstruct corrections, and unused models act as a false contract.

## Reason for Change
These four activities depend on the final parser, result, error, schema, and consistency contracts; doing them earlier would cause drift. No urgency otherwise.

## Implementation Intent
One release-readiness pass: tool descriptions match the parser, production status is evidence-based, CI distinguishes characterization from contract tests, and every retained response model has a production use.

## Target Files or Areas
- `scripts/mcp_servers/mdq/parser.py`, `mdq_models.py`, `mdq_tools.py`
- MDQ test directories and markers under `tests/mcp_servers/mdq/`
- MDQ benchmark and operations documentation (locations `Unknown`)

## Required Changes
- Decide whether fenced code content is searchable, keep suppressing heading parsing inside fences, add golden tests for Python, JSON, shell, and Mermaid blocks, and document ATX and Setext headings, tables, HTML, code fences, and MDX support.
- Define production criteria for integrity, recovery, security, observability, and performance; consider beta status for write tools until met; benchmark search, grep, index, refresh, rebuild, and recovery p50, p95, p99 by chunk count, database size, chunk length, and concurrency; publish verified scale and limits.
- Apply the characterization-versus-authoritative convention defined by `issues/20261119-140517_mcpai010_github-http-contract-tests.md` to the MDQ tests; mark MDQ security and reliability contract tests as authoritative; reverse or remove unsafe legacy expectations as fixes land.
- Identify internal DTOs and public result contracts; remove unused response models; use retained models consistently from service to audit and formatter; remove or define empty placeholders such as `IndexMetadata`.

## Constraints
- Start only after the other MDQ issues are stable.
- A change of tool status needs the project's documented status process (`不明`).

## Acceptance Criteria
- [ ] Parser behavior and tool descriptions agree.
- [ ] Production status is backed by published criteria and measurements.
- [ ] CI separates characterization and contract tests.
- [ ] Every retained response model is used by production code.
- [ ] No obsolete or contradictory documentation remains.

## Testing Expectations
- Markdown golden tests; a reproducible benchmark harness and report; a release-readiness checklist; a characterization-to-contract migration inventory; dead-model checks (vulture, ruff).
- Run mypy and the full test suite.

## Documentation Impact
Yes. Markdown semantics, production criteria and measured scale, test classification, and model contracts.

## Out of Scope
- Behavior changes owned by `issues/20261119-142123_mdqmcp001_mdq-server-boundary.md` through `issues/20261119-142131_mdqmcp009_mdq-rag-boundary-rules.md`.

## Dependencies
- Depends on `issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`, `issues/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`, `issues/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`, `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`, `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`, `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`, `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`, `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`, and `issues/20261119-142131_mdqmcp009_mdq-rag-boundary-rules.md`; also on `issues/20261119-140517_mcpai010_github-http-contract-tests.md` (test convention).

## Unresolved Questions
- `不明`: whether fenced code should be searchable.
- `不明`: the benchmark environment and acceptance thresholds.

## AI Implementation Instruction
Verify each claim against current source before acting. Do not change behavior contracts here. Stop and report if thresholds for production status are not agreed.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-142132
- **Related target files**: `scripts/mcp_servers/mdq/parser.py`, `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_tools.py`

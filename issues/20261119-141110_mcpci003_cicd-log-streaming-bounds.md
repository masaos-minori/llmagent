# Stream, bound, and structure CI/CD workflow log retrieval

## Priority
High

## Summary
Replace full in-memory job-log downloads and string-embedded failures with bounded streaming and a structured partial-success result.

## Background
Source: consolidated Web Search and CI/CD MCP backlog (`memo-issue.md`, Issue 7).

Evidence (`Explicit in code`, by reading `cicd_service_github_actions_job.py`): the log request uses `follow_redirects=True` (line 85), reads `log_resp.text` in full (line 89), and records a failure as the string `(log fetch failed: HTTP {status})` inside the output (line 91). Test expectations that allow overrun are from the backlog and `Needs confirmation`.

## Problem
The output limit applies only after full download and assembly, so it does not bound network, decompressed size, or memory; redirects are unrestricted; per-job failures are embedded as text while the overall result stays successful.

## Reason for Change
Resource control and result-contract correctness for a High-priority CI/CD feature; follows the credential and client lifecycle work.

## Implementation Intent
Stream with raw-download and decompressed limits, restrict redirects to documented GitHub-controlled hosts, enforce one exact final byte budget including headers and markers, keep UTF-8 boundaries, and return job-level status with an explicit `partial_success`.

## Target Files or Areas
- `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py`
- CI/CD log response models and formatter; `config/cicd_mcp_server.toml`
- `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` and log tests
- `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` (see the document map of `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`)

## Required Changes
- Use the shared bounded streaming helper of `issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md` for log retrieval, with a trusted-GitHub-host redirect policy and a maximum redirect count; the CI/CD-specific part is the per-job log byte budget.
- One exact final-output budget including headers and truncation markers; stop adding jobs when the next header does not fit; preserve complete UTF-8 characters.
- Return per-job status, included bytes, error code, truncation state; add `partial_success`; return a tool error when every job fails; never include raw transport exception text.
- Return totals: jobs, included jobs, failed jobs, downloaded bytes, visible bytes, truncation reason.

## Constraints
- Final output never exceeds `max_log_size_kb` in bytes.
- Tokens and raw upstream text never appear in results.

## Acceptance Criteria
- [ ] Network and decompressed data are bounded before full buffering.
- [ ] Final output never exceeds the byte limit; UTF-8 truncation introduces no replacement characters.
- [ ] Redirects outside trusted GitHub hosts are rejected.
- [ ] Complete, partial, and total failure are machine-distinguishable; raw exception strings are absent.

## Testing Expectations
- Huge single-job log, many jobs, header-only budget exhaustion, trusted and untrusted redirects, compressed and chunked responses, mixed and all-failed cases; replace tests that allow overrun or string-embedded exceptions.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Download, decompressed, selected-job, and returned-output limits; redirect policy and trusted hosts; the complete, partial, and error result contract.

## Out of Scope
- Dispatch reconciliation (`issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md`); error mapping (`issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md`).

## Dependencies
- Depends on `issues/20261119-141106_mcpci001_cicd-credential-config-contract.md` and on `issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md` (shared bounded streaming helper). Can run in parallel with `issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md`.

## Unresolved Questions
- `不明`: the list of trusted GitHub log hosts and the redirect maximum.
- `不明`: limit values for raw and decompressed bytes.

## AI Implementation Instruction
Write the byte-budget and untrusted-redirect tests first. Keep changes inside the job backend, its models, and tests. Stop and report if the trusted-host list cannot be determined from GitHub documentation or observed behavior.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-141110
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py`, `config/cicd_mcp_server.toml`

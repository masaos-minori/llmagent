# Define safe retry, timeout, audit, and reconciliation behavior for GitHub writes

## Priority
High

## Summary
Classify GitHub writes by actual reconciliation capability, fail closed when durable protection is unavailable, distinguish applied-but-audit-failed outcomes, and represent timeout ambiguity explicitly.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 6).

Evidence (`Explicit in code`, by reading `config/mcp_dedup.toml`): the `[retry_class]` map currently marks `github_add_issue_comment`, `github_create_branch`, and `github_create_issue` as `retryable` (lines 34-36; the rest of the GitHub entries were not read here). Source constants (`scripts/shared/tool_constants.py` `RETRYABLE_TOOLS`) are the owner and the TOML is a mirror. Related archived work: `issues/done/20261117-123018_adrchk018_mcp-retry-classes.md` (single-source of retry classes). Audit and timeout claims are from the review and `Needs confirmation`.

## Problem
Retrying issue creation, comments, pull request creation, merge, deletion, branch creation, or multi-file push after a lost response can duplicate or corrupt remote state. An audit failure after a successful API write can be reported as a generic failure, encouraging a duplicate retry, and a worker or transport timeout does not prove non-application.

## Reason for Change
External side effects with incomplete protection; the behavior is stricter than the current classification, so it is a deliberate behavior change.

## Implementation Intent
Only operations with a documented, tested reconciliation algorithm may be retried automatically; classify conservatively (reachability over HTTP does not imply retryability). Unknown outcomes block automatic retry. High-risk writes record intent before execution and distinguish completion-audit failure from API failure.

## Target Files or Areas
- `config/mcp_dedup.toml`, `scripts/shared/tool_constants.py`
- GitHub client initialization and timeout configuration (`scripts/mcp_servers/github/github_service_init.py`)
- `scripts/mcp_servers/github/github_service_security.py`, GitHub write operations (`github_service_*`, `github_service_dispatch_writes.py`)
- GitHub audit and recovery tests under `tests/mcp_servers/github/`

## Required Changes
- Classify `github_create_issue`, `github_add_issue_comment`, `github_create_pull_request`, `github_merge_pull_request`, `github_delete_file`, `github_push_files`, and `github_create_branch` as non-retryable until reconciliation exists; define operation-specific reconciliation before making file update, branch creation, pull request update, or merge retryable.
- Classify the GitHub writes under the shared fail-closed rule of `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (a non-retryable write fails closed when the durable dedup store is unavailable); this issue adds only the GitHub-specific classification and tests.
- Add strict connect and read timeouts; return `outcome_unknown` when a write may have succeeded; never retry it automatically.
- Write intent audit before a high-risk operation (fail closed if it cannot be recorded) and completion audit after; return `applied_audit_failed` when the API write succeeded but completion audit failed.
- Expose audit failures in health or metrics; keep the TOML and the constants synchronized through CI.
- Implement each operation's reconciliation on the shared reconciler contract of `issues/20261120-115843_mcpdl004_call-state-control-api.md`: reuse completed evidence, never rerun an active, unknown, or ambiguous call, and record the evidence without raw payloads.
- Define the shared write-outcome vocabulary (`outcome_unknown`, `applied_audit_failed`, and the rule that neither is retried automatically) and the shared write-audit contract (an intent audit before a high-risk or destructive write that fails closed, a completion audit after, and session, request, and logical call identifiers in every audit record); the Git, File, and CI/CD issues reuse both.

## Constraints
- Do not infer non-application from a timeout.
- ADR-004 and ADR-008 govern retry and fail-closed behavior; a change to an ADR decision or invariant needs a maintainer approval record in the same change (governance_01, governance_05). Do not write or simulate that approval.

## Acceptance Criteria
- [ ] The listed operations are non-retryable in every classification source.
- [ ] A dedup-store failure prevents non-retryable GitHub writes; intent-audit failure prevents API execution.
- [ ] Timeout does not imply non-application; `outcome_unknown` and `applied_audit_failed` prohibit automatic retry.
- [ ] Completion-audit failure does not erase the fact that the write was applied.
- [ ] Every retryable GitHub write has a documented, tested reconciliation algorithm.

## Testing Expectations
- Retry classification consistency tests; dedup-store failure tests for every non-retryable write.
- API-success-plus-audit-failure tests for issue, comment, merge, and file update.
- Read and write timeout tests; outcome-unknown no-retry tests; reconciliation tests for any operation kept retryable.
- Run ruff, mypy, the retry-class consistency check, and the full test suite.

## Documentation Impact
Yes. Retry policy, timeout outcomes, and audit outcomes as failure behavior (ADR-004/ADR-008 mention, final sweep in `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`).

## Out of Scope
- Dedup storage (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`); key propagation (`issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`); read authorization (`issues/20261119-140509_mcpai002_github-read-security-boundary.md`); Git and File MCP outcomes (`issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md`, `issues/20261119-140516_mcpai009_file-mcp-hardening.md`).

## Dependencies
- Depends on `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (recovery-state semantics) and `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md` (stable call identity); `issues/20261119-140509_mcpai002_github-read-security-boundary.md` should be completed first for a consistent security boundary; `issues/20261119-140514_mcpai007_dedup-audit-observability.md` is recommended but not blocking.
- Blocks `issues/20261119-140517_mcpai010_github-http-contract-tests.md`. Must land before automatic replay of GitHub writes is enabled.
- Related: `issues/20261120-115842_mcpdl003_dedup-config-isolation.md` removes `config/mcp_dedup.toml`, which this issue lists as a target, and `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md` makes RuntimeTool the retry-policy authority; the retry-class mirror in the TOML is retired with them, so the classification here must land in the metadata that remains.

## Unresolved Questions
- `不明`: which operations can get a reconciliation algorithm (versus staying non-retryable).
- `不明`: current classification of the remaining GitHub tools in `config/mcp_dedup.toml` and `RETRYABLE_TOOLS` (only three entries were read).
- `不明`: timeout values.

## AI Implementation Instruction
Prefer conservative classification. Change the constants and the TOML together with the consistency test. Do not enable automatic replay for any GitHub write without a tested reconciliation. Stop and report ADR conflicts.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140513
- **Related target files**: `config/mcp_dedup.toml`, `scripts/shared/tool_constants.py`, `scripts/mcp_servers/github/github_service_init.py`, `scripts/mcp_servers/github/github_service_security.py`, `tests/mcp_servers/github/`

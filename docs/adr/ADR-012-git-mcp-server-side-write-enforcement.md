---
title: "ADR-012: Git MCP Server-Side Write Enforcement"
area: adr
tags:
  - mcp
  - git
  - write-enforcement
decision_scope:
  - mcp/git
related: []
---

# ADR-012: Git MCP Server-Side Write Enforcement

## Status

Accepted

使用可能なStatusは次のとおりとする。

- `Proposed`: 提案中、レビューまたは承認前
- `Accepted`: 採用済みであり、現行設計として有効

Accepted後に現在の判断を変更する場合は、本ADR本文を直接更新する。同じ変更の中で、影響を受けるSpecification、Reference、Operations文書および検証要件を更新する。

## Summary

Agent-side approval confirms user intent; it does not verify that a Git write operation is technically safe. Git MCP enforces protected-branch, Force-Push, Dirty-Worktree, and ref/remote validation independently of Agent-side approval, using constrained argument validation rather than passing caller-supplied strings through to the underlying `git` CLI unchecked.

## Context

### Problem

Approval and technical safety are different concerns: Agent-side approval confirms user intent before a call is made, but it does not itself validate that the call is safe to execute against the target repository. Git MCP's write tools (`git_checkout`/`git_pull`/`git_push`) must therefore enforce their own technical constraints — protected-branch policy, ref/remote shape, worktree/HEAD state, and postcondition verification — independently of whatever approval state exists on the Agent side, and without assuming a call it receives was already approved.

### Constraints

- Git MCP wraps local `git` operations via GitPython; it does not shell out through a shell interpreter (no shell-injection vector), but GitPython still passes argument strings to `git`'s own CLI option parser.
- Approval is enforced client-side in the Agent process (`agent/tool_policy.py`, `tool_approval.py`); the Git MCP HTTP endpoint itself has no dependency on Agent-side approval state and accepts calls authenticated only by an optional Bearer token.

### Assumptions

- Target environment: single Agent process talking to a locally-run Git MCP server over HTTP.
- Re-evaluate if: Git MCP is exposed to callers other than the single trusted Agent process, or if GitPython is replaced by a different git-invocation mechanism.

## Decision

### Decision Details

1. Approval and technical safety are separate layers. Agent-side approval MUST NOT be treated as a substitute for Git MCP's own validation, and Git MCP MUST NOT assume a call it receives was already approved.
2. `branch` and `remote` arguments MUST be validated against a safe-ref pattern before being passed to `git`; values that would be interpreted as command-line options (e.g., leading `-`) MUST be rejected.
3. Force Push MUST be rejected by the normal `git_push` operation. If Force Push is ever required operationally, it MUST be implemented as a separate, more strongly authorized administrative capability with its own approval and audit requirements — not as a mode of the normal tool.
4. A protected-branch policy MUST be enforced by Git MCP itself for `git_checkout`/`git_push`/`git_pull` against configured protected branches, independent of any Agent-side branch-name checks (which apply only to `github_*` tools, not local git).
5. `git_checkout`/`git_pull` MUST reject execution against a Dirty Worktree unless a documented safe exception applies; Detached HEAD MUST be rejected unless explicitly permitted by policy.
6. Postcondition verification MUST confirm the resulting branch/HEAD and detect unresolved conflicts before reporting success; a `git` command that exits non-zero already fails today, but a low-level "did we actually end up where we intended" check is not the same guarantee.
7. Audit records for Git MCP write operations include the correct repository identity; the key-name mismatch (`"repo"` vs. `repo_path`) was fixed as part of closing this gap.
8. `RepositoryState` frozen dataclass MUST capture full repository state from a single `git.Repo` query and provide immutable access to all fields.
9. Write-protection pipeline MUST enforce stage ordering: Stage 4 (state snapshot) → Stage 5 (preconditions) → Stage 6 (execution) → Stage 7 (postcondition verification).
10. Audit records for Git MCP write operations MUST include both pre-condition and post-condition snapshots captured by `RepositoryState`.

### Scope

- **Components**: `scripts/mcp_servers/git/git_service.py`, `git_security.py`, `format_output.py`, `git_server.py`, `git_models.py`, `repository_state.py`.
- **Tools**: `git_checkout`, `git_pull`, `git_push` specifically; `git_add`/`git_commit` are lower-risk and out of scope for command-specific guards beyond the existing common guard.

### Out of Scope

- GitHub MCP's existing `protected_branches`/force-push handling (already implemented separately; not part of this decision).
- Redesign of the Agent-side approval risk-tier mapping (tracked separately; resolved).
- Any capability to allow Force Push, even as an administrative feature — this ADR only requires that if such a capability is later added, it MUST NOT be the default `git_push` path.

## Rationale

### 1. Correctness / Security

An MCP server that accepts unvalidated ref-shaped strings and forwards them to an external CLI process is exposed to option-injection regardless of what its own JSON schema appears to allow. Omitting a `force` field from the schema is not a control if the same effect is reachable through `branch`.

### 2. Defense in Depth

Relying solely on Agent-side approval collapses two independent layers (user-intent confirmation and technical safety) into one, so a bypass of the approval UI (or a call made directly against the MCP HTTP endpoint) removes all protection. Server-side enforcement keeps a technical floor regardless of how the call arrived.

### 3. Auditability

A write surface with this risk profile (repository state mutation, potential history rewrite) requires an audit trail that identifies which repository was affected and what state it was in before and after the call.

## Alternatives Considered

### Alternative A: Rely entirely on Agent-side approval and leave Git MCP as a thin wrapper

#### Advantages
Less code in the MCP server; simpler tool implementation.

#### Disadvantages
No protection if the approval step is bypassed or the MCP endpoint is reached directly; unvalidated `branch`/`remote` values reaching the underlying `git` CLI remain exploitable regardless of approval-layer changes.

#### Reason for Rejection
Violates the layered-protection principle already adopted for other high-risk MCP tools (`00_security_02_high-risk-tool-common-policy.md`); approval is a UX/intent layer, not a technical control.

### Alternative B: Block `git_checkout`/`git_pull`/`git_push` entirely until guards are implemented

#### Advantages
Removes the exploitable surface immediately.

#### Disadvantages
Removes legitimate, currently-relied-upon functionality; disproportionate to the risk for a single-operator local-git use case.

#### Reason for Rejection
A low-cost mitigation (reject option-shaped `branch`/`remote` values, plus the remaining guards) addresses the risk without removing the tools.

## Consequences

### Positive Consequences
- Git MCP's safety posture is independent of, and does not rely on, Agent-side approval state.
- Makes Git MCP's safety posture consistent with the common high-risk-tool policy it is supposed to follow.

### Negative Consequences
- Validation code and protected-branch configuration surface exist in what was previously a minimal server.
- A safe-ref pattern that is too strict can reject legitimate ref names that happen to resemble options; the pattern requires clear documentation to avoid false rejections.

### Ongoing Risks

- `RepositoryState` frozen-dataclass immutability must continue to hold under all code paths as the module evolves.
- `RepositoryState`'s internal repository reference must not prevent garbage collection.
- Pipeline early-exit paths must not skip required audit entries.
- Option-injection prevention via the safe-ref check must continue to run before any `git.Repo` query is made.

### Operational Consequences
- Operators configuring Git MCP define a protected-branch list, analogous to GitHub MCP's existing configuration.

### Security Consequences
- Closes the option-injection vector for `branch`/`remote` arguments.
- Audit records identify the affected repository and capture pre/post-condition state.
- Audit `target` field fix completed; this tool category's audit trail now includes canonical repository identity.

## Traceability

### Implementation Procedures
- `implementations/20260829-134950_01_scripts_mcp_servers_git_repository_state.py.md`: Create RepositoryState module
- `implementations/20260829-134950_02_scripts_mcp_servers_git_git_service.py.md`: Modify git_service.py
- `implementations/20260829-134950_03_scripts_mcp_servers_git_git_security.py.md`: Modify git_security.py
- `implementations/20260829-134950_04_scripts_mcp_servers_git_format_output.py.md`: Modify format_output.py
- `implementations/20260829-134950_05_scripts_mcp_servers_git_git_models.py.md`: Modify git_models.py
- `implementations/20260829-134950_06_scripts_mcp_servers_git_git_server.py.md`: Modify git_server.py
- `implementations/20260829-134950_07_scripts_mcp_servers_dispatch.py.md`: Skipped — procedure did not match actual architecture (generic async dispatcher vs git-specific sync dispatcher); git_server.py already handles RepositoryState via call_tool endpoint
- `implementations/20260829-134950_08_scripts_mcp_servers_audit.py.md`: Modify audit.py
- `implementations/20260829-134950_09_tests_mcp_servers_git_test_repository_state.py.md`: Create tests

### Source Documents
- Source issue: issues/20260828-162303_mcp003_git_write_protection_pipeline.md
- Source plan: plans/20260829-134950_plan.md

## Invariants

- INV-01: `branch`/`remote` values MUST be rejected if they do not match a safe ref/remote-name pattern.
- INV-02: `git_push` MUST NOT perform a forced update through the normal tool path.
- INV-03: `git_checkout`/`git_push`/`git_pull` against a configured protected branch MUST be rejected unless a separately approved policy explicitly allows it.
- INV-04: Agent-side approval state MUST NOT be assumed or required by Git MCP's own validation logic — the two checks are independent.

## Exceptions

None.

## Failure Policy

### Fail-Fast Conditions
- `branch`/`remote` value matches an option-injection pattern.
- Target branch is on the protected-branch list.

### Fail-Open or Degraded Conditions
- None for the write-guard checks themselves; read-only tools (`git_status`, `git_log`, etc.) are unaffected by this decision.

### Retry Policy
Not applicable.

### Fallback Policy
Not applicable — a rejected write MUST be reported as rejected, not silently downgraded to a no-op.

## Data Ownership and Persistence

Not applicable in the DB sense — this ADR governs a control-flow/validation boundary, not persisted state. The audit record (JSON lines, per-call) is the relevant persisted artifact and is covered by INV-04's requirement for correct repository identity.

## Verification

### Automated Tests
- **Test**: `git_checkout`/`git_pull`/`git_push` reject a `branch`/`remote` value shaped like a CLI option (`test_is_safe_ref`, `test_git_pull_unsafe_remote`, `test_git_show_unsafe_ref`) — **Verifies**: INV-01 — **Type**: Regression — **Blocking**: Yes
- **Test**: `git_push` exposes no `force` parameter, so a forced update is unreachable through the normal path — **Verifies**: INV-02 — **Type**: Unit — **Blocking**: Yes
- **Test**: push/checkout/pull against a configured protected branch is rejected (`test_check_protected_branch`, `test_git_checkout_protected_branch`, `test_git_push_protected_branch`, `test_git_pull_protected_branch`, `test_write_tools_reject_shipped_protected_branches`) — **Verifies**: INV-03 — **Type**: Integration — **Blocking**: Yes
- **Test**: Dirty Worktree / Detached HEAD are rejected (or explicitly allowed) per policy (`test_git_checkout_dirty_worktree_denied`, `test_git_pull_dirty_worktree_denied`, `test_git_checkout_detached_head_denied`, `test_git_pull_detached_head_denied`, `test_git_checkout_detached_head_allowed`, `test_git_pull_detached_head_allowed`) — **Verifies**: Decision Details #5 — **Type**: Integration — **Blocking**: Yes
- **Test**: Postcondition verification detects a wrong resulting branch, a detached HEAD, unresolved merge conflicts, and a push-rejection marker (`test_checkout_postcondition_failure_wrong_branch`, `test_checkout_postcondition_failure_detached_head`, `test_pull_postcondition_failure_unresolved_conflicts`, `test_push_postcondition_failure_rejection_marker_in_output`) — **Verifies**: Decision Details #6 — **Type**: Unit — **Blocking**: Yes
- **Test**: `RepositoryState` is a frozen dataclass and snapshots capture the required fields (`test_snapshot_frozen_dataclass`, plus the `TestRepositoryStateSnapshot` suite) — **Verifies**: Decision Details #8 — **Type**: Unit — **Blocking**: Yes
- **Test**: audit records include the correct repository identity and pre/post-condition state (`test_audit_record_includes_repo_identity`, `test_audit_record_has_pre_condition`, `test_audit_record_has_post_condition`) — **Verifies**: Decision Details #7, #10 — **Type**: Unit — **Blocking**: Yes

### Resolved Items

- **Resolved**: Protected-branch empty-branch short-circuit — resolved by commit `800aea33e` (fix `_validate_protected()` to reject empty `branch` argument).
- **Resolved**: Audit `target` field key-name mismatch fixed (see Resolution Notes).

## Implementation Notes

- Implementation files: `scripts/mcp_servers/git/repository_state.py` (`RepositoryState`, `WriteProtectionPipeline`, `_is_safe_ref`, `_validate_ref`, `_check_protected_branch`), `scripts/mcp_servers/git/git_security.py` (`GitSecurityGuards`), `scripts/mcp_servers/git/git_service.py` (`GitService`, dispatch table), `scripts/mcp_servers/git/format_output.py` (`format_checkout()`, `format_pull()`, `format_push()`), `scripts/mcp_servers/git/git_server.py` (`call_tool()` endpoint, audit logging), `scripts/mcp_servers/git/git_models.py` (`GitConfig`, request models)
- Key symbols: `GitSecurityGuards`, `RepositoryState.snapshot()`, `WriteProtectionPipeline.run()`, `GitService.get_dispatch_table()`, `format_checkout()`, `format_pull()`, `format_push()`
- Corresponding tests: `tests/mcp_servers/git/test_git_security_compliance.py`, `tests/mcp_servers/git/test_format_output.py`, `tests/mcp_servers/git/test_repository_state.py`, `tests/mcp_servers/git/test_git_service_dispatch.py`, `tests/mcp_servers/git/test_mcp_git.py`, `tests/mcp_servers/git/test_git_models.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

現時点で記載すべき差異はない(protected-branch/Force-Pushガード追加、承認リスク階層の是正、audit `target`フィールド修正はいずれも解決済み)。

ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する。

## Review Triggers

- Git MCP is exposed to any caller other than the single trusted Agent process.
- A legitimate operational need for Force Push is identified (triggers designing the separate administrative capability referenced in Decision Details #3).

## Approval

### Required Reviewers
- Architecture Owner
- Security Reviewer

### Approval Record

- **Approved By**: タスクレベル承認判断(リポジトリ管理者。個別レビュアー名は記録しない)
- **Approval Date**: 記録なし(タスクレベル承認判断のため個別の承認日は記録しない)
- **Approval Reference**: `docs/00_governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

本ADRの`Accepted`ステータスは、上記ガバナンス文書が定めるタスクレベル承認判断を受理証跡とする。個別レビュアー名・承認日による正式なApproval Recordは作成していない。

## Related Documents

### Specifications
- [MCP Server Catalog: git-mcp](../04_mcp_04_05_git.md)
- [High-Risk MCP Tool Common Policy](../00_security_02_high-risk-tool-common-policy.md)
- [Fail-Open/Fail-Closed and Risk Tiers](../04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md)

### Known Issues
- [Issue and Uncertainty Management](../00_governance_03_issue-and-uncertainty-management.md) — no active entries related to this ADR; the protected-branch/Force-Push guard, approval risk-tier mapping, and audit repository-identity gaps this ADR addressed are all resolved.

### Implementation References
- `scripts/mcp_servers/git/repository_state.py` — `RepositoryState`, `WriteProtectionPipeline`
- `scripts/mcp_servers/git/git_security.py` — `GitSecurityGuards`, dispatch table
- `scripts/mcp_servers/git/format_output.py` — `format_checkout()`, `format_pull()`, `format_push()`

## Completion Checklist

ADRをAcceptedへ変更する前に確認する。

- [x] 解決する問題が明確である
- [x] Decisionが1つの主要な設計判断に絞られている
- [x] Decisionが必須、禁止、正本、Fallback条件などの明確な表現で記載されている
- [x] 採用理由が現在の実装以外の観点で説明されている
- [x] 実質的な代替案と不採用理由が記載されている
- [x] Positive Consequencesが記載されている
- [x] Negative Consequencesが記載されている
- [x] Securityへの影響が評価されている
- [x] Operations、Monitoring、Recoveryへの影響が評価されている
- [x] 検証可能なInvariantsが定義されている
- [x] Exceptionsまたは適用対象外が明確である
- [x] 各InvariantにVerificationが対応している
- [x] 自動化可能な検証がManual Reviewだけになっていない
- [x] 現行実装との差異がKnown Issueへ登録されている
- [x] Ownerと必要なReviewerが定義されている（`docs/00_governance_01_documentation-policy.md` ADR Acceptance Evidence Standardが定めるタスクレベル承認判断を受理証跡とする。個別のApproval Record［承認者・承認日・承認参照］は作成していない）
- [x] Review Triggersが記載されている
- [ ] ADR索引と関係領域のDocument Guideへ登録されている（別途確認が必要）

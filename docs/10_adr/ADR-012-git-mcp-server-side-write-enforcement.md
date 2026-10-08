---
title: "ADR-012: Git MCP Server-Side Write Enforcement"
area: governance
tags:
  - mcp
  - git
  - write-enforcement
related:
  - mcp_04_05_git.md
  - security_02_high-risk-tool-common-policy.md
  - mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - governance_03_issue-and-uncertainty-management.md
---

# ADR-012: Git MCP Server-Side Write Enforcement

## Keywords

- git mcp
- write protection
- server-side enforcement
- protected branch

## Status

Accepted

## Summary

Agent-side approval confirms user intent; it does not verify that a Git write operation is technically safe. Git MCP enforces protected-branch, Force-Push, Dirty-Worktree, and ref/remote validation independently of Agent-side approval, using constrained argument validation rather than passing caller-supplied strings through to the underlying `git` CLI unchecked.

## Context

### Problem

Approval and technical safety are different concerns: Agent-side approval confirms user intent before a call is made, but it does not itself validate that the call is safe to execute against the target repository. Git MCP's write tools (`git_checkout`/`git_pull`/`git_push`) must therefore enforce their own technical constraints — protected-branch policy, ref/remote shape, worktree/HEAD state, and postcondition verification — independently of whatever approval state exists on the Agent side, and without assuming a call it receives was already approved.

### Constraints

- Git MCP wraps local `git` operations via GitPython; it does not shell out through a shell interpreter (no shell-injection vector), but GitPython still passes argument strings to `git`'s own CLI option parser.
- Approval is enforced client-side in the Agent process (`agent/tool_policy.py`, `tool_approval.py`); the Git MCP HTTP endpoint itself has no dependency on Agent-side approval state and accepts calls authenticated only by an optional Bearer token.

## Assumptions

- Target environment: single Agent process talking to a locally-run Git MCP server over HTTP.
- Re-evaluate if: Git MCP is exposed to callers other than the single trusted Agent process, or if GitPython is replaced by a different git-invocation mechanism.

## Decision

### Decision Details

1. Approval and technical safety are separate layers. Agent-side approval MUST NOT be treated as a substitute for Git MCP's own validation, and Git MCP MUST NOT assume a call it receives was already approved.
2. `branch` and `remote` arguments MUST be validated against a safe-ref pattern before being passed to `git`; values that would be interpreted as command-line options (e.g., leading `-`) MUST be rejected.
3. Force Push MUST be rejected by the normal `git_push` operation. If Force Push is ever required operationally, it MUST be implemented as a separate, more strongly authorized administrative capability with its own approval and audit requirements — not as a mode of the normal tool.
4. A protected-branch policy MUST be enforced by Git MCP itself for `git_checkout`/`git_push`/`git_pull` against configured protected branches, independent of any Agent-side branch-name checks (which apply only to `github_*` tools, not local git).
5. `git_checkout`/`git_pull` MUST reject execution against a Dirty Worktree unless a documented safe exception applies; Detached HEAD MUST be rejected unless explicitly permitted by policy.
6. Postcondition verification MUST confirm the resulting branch/HEAD and detect unresolved conflicts before reporting success; a non-zero `git` exit status alone does not guarantee the repository ended up in the intended state.
7. Audit records for Git MCP write operations MUST include the correct repository identity (the `repo_path` key).
8. `RepositoryState` frozen dataclass MUST capture full repository state from a single `git.Repo` query and provide immutable access to all fields.
9. Write-protection pipeline MUST enforce stage ordering: Stage 4 (state snapshot) → Stage 5 (preconditions) → Stage 5b (HEAD-identity re-check immediately before the mutating Git call) → Stage 6 (execution) → Stage 7 (postcondition verification).
10. Audit records for Git MCP write operations MUST include both pre-condition and post-condition snapshots captured by `RepositoryState`.

### Scope

- **Components**: `scripts/mcp_servers/git/git_service.py`, `git_security.py`, `format_output.py`, `git_server.py`, `git_models.py`, `repository_state.py`.
- **Tools**: `git_checkout`, `git_pull`, `git_push` specifically; `git_add`/`git_commit` are lower-risk and out of scope for command-specific guards beyond the existing common guard.

### Out of Scope

- GitHub MCP's existing `protected_branches`/force-push handling (already implemented separately; not part of this decision).
- Redesign of the Agent-side approval risk-tier mapping (out of scope for this ADR).
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
Violates the layered-protection principle already adopted for other high-risk MCP tools (`security_02_high-risk-tool-common-policy.md`); approval is a UX/intent layer, not a technical control.

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
- Validation code and protected-branch configuration surface add maintenance burden to the server.
- A safe-ref pattern that is too strict can reject legitimate ref names that happen to resemble options; the pattern requires clear documentation to avoid false rejections.

### Ongoing Risks

- `RepositoryState` frozen-dataclass immutability must continue to hold under all code paths as the module evolves.
- `RepositoryState`'s internal repository reference must not prevent garbage collection.
- Pipeline early-exit paths must not skip required audit entries.
- Option-injection prevention via the safe-ref check must continue to run before any `git.Repo` query is made.

### Operational Consequences
- Operators configuring Git MCP define a protected-branch list, analogous to GitHub MCP's existing configuration.

### Security Consequences
- Closes the option-injection vector for ref-shaped arguments (`branch`, `remote`, `commit`, `ref`) on the tools that accept them, by rejecting values that start with `-`.
- Intended: audit records identify the affected repository and capture pre/post-condition state, with canonical repository identity in the `target` field. Currently git-mcp audit records for dispatched calls are not written (the `_audit_log()` call raises `TypeError`, which is swallowed); see MCP-001 in `governance_03_issue-and-uncertainty-management.md`. (Explicit in code — `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/audit.py`)

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

Not applicable in the DB sense — this ADR governs a control-flow/validation boundary, not persisted state. The audit record (JSON lines, per-call) is the relevant persisted artifact and is governed by Decision Details #7 and #10.

## Verification

### Automated Tests
- **Test**: `git_checkout`/`git_pull`/`git_push` reject a `branch`/`remote` value shaped like a CLI option (`test_is_safe_ref`, `test_git_pull_unsafe_remote`, `test_git_show_unsafe_ref`) — **Verifies**: INV-01 — **Type**: Regression — **Blocking**: Yes
- **Test**: write tools reject malformed `branch`/`remote` through the `git check-ref-format --branch`-equivalent allow-list (`TestWriteRefAllowlist::test_rejected_branch_forms`, `test_rejected_remote_forms`; `TestGitPushRefRejectionBeforeGit::test_rejected_before_snapshot`); read-tool ref tests (`test_is_safe_ref`, `test_git_show_unsafe_ref`) remain for the option-injection-only check — **Verifies**: INV-01 — **Type**: Regression — **Blocking**: Yes
- **Test**: `git_push` exposes no `force` parameter, so a forced update is unreachable through the normal path — **Verifies**: INV-02 — **Type**: Unit — **Blocking**: Yes
- **Test**: push/checkout/pull against a configured protected branch is rejected (`test_check_protected_branch`, `test_git_checkout_protected_branch`, `test_git_push_protected_branch`, `test_git_pull_protected_branch`, `test_write_tools_reject_shipped_protected_branches`; `TestLiveCallToolAuthorization`: `test_checkout_protected_branch_denied`, `test_pull_protected_branch_denied`, `test_push_protected_branch_denied`, `test_checkout_non_protected_branch_allowed`, `test_pull_non_protected_branch_allowed`, `test_push_non_protected_branch_allowed`, `test_checkout_implicit_target_denied`, `test_pull_implicit_target_denied`, `test_push_implicit_target_denied`); a protected destination is also rejected when reached directly through the pipeline (`test_repository_state.py::TestStage3DestinationProtection`; `test_git_service_dispatch.py::TestDestinationBasedProtection`), and checkout away from a protected branch is allowed — **Verifies**: INV-03 — **Type**: Integration — **Blocking**: Yes
- **Test**: Dirty Worktree / Detached HEAD are rejected (or explicitly allowed) per policy (`test_git_checkout_dirty_worktree_denied`, `test_git_pull_dirty_worktree_denied`, `test_git_checkout_detached_head_denied`, `test_git_pull_detached_head_denied`, `test_git_checkout_detached_head_allowed`, `test_git_pull_detached_head_allowed`; `TestDryRunAndDetachedHeadLivePath`: `test_dry_run_checkout_skips_dirty_and_detached_precondition`, `test_dry_run_checkout_protected_branch_still_denied`, `test_non_dry_run_detached_head_denied_then_allowed`, `test_dry_run_pull_and_push_skip_dirty_precondition`) — **Verifies**: Decision Details #5 — **Type**: Integration — **Blocking**: Yes
- **Test**: Postcondition verification runs on the live path and cannot be bypassed (`TestPostConditionBypassPrevention`: `test_checkout_postcondition_cannot_be_bypassed`, `test_pull_postcondition_cannot_be_bypassed`, `test_push_postcondition_cannot_be_bypassed`) — **Verifies**: Decision Details #6 — **Type**: Integration — **Blocking**: Yes
- **Test**: `RepositoryState` is a frozen dataclass and snapshots capture the required fields (`test_snapshot_frozen_dataclass`, plus the `TestRepositoryStateSnapshot` suite) — **Verifies**: Decision Details #8 — **Type**: Unit — **Blocking**: Yes
- **Test**: audit records include the correct repository identity and pre/post-condition state (`test_audit_record_includes_repo_identity`, `test_audit_record_has_pre_condition`, `test_audit_record_has_post_condition`) — **Verifies**: Decision Details #7, #10 — **Type**: Unit — **Blocking**: Yes
- **Test**: the pipeline stages execute in the documented order for `git_checkout`/`git_pull`/`git_push` (`TestCompletePipelineCoverage`: `test_all_stages_execute_in_order_for_checkout`, `test_all_stages_execute_in_order_for_pull`, `test_all_stages_execute_in_order_for_push`) — **Verifies**: Decision Details #9 — **Type**: Integration — **Blocking**: Yes

## Implementation Notes

See Implementation References for the current file/symbol list.

## Known Deviations

- MCP-001 — git-mcp audit records are now emitted for every write-tool call.
- **MCP-002 — resolved.** The `git_pull`/`git_push` schema contradiction (an empty `branch` default that always failed `_validate_protected("")`) is closed: `branch` is now required in both request schemas, so the empty-branch default no longer reaches validation. Resolution target met.
- **MCP-004 — residual known deviation.** The force-push-via-`branch` vector is now closed server-side: the write-tool allow-list rejects `+main` and other refspec forms before any GitPython call, and Stage 3 rejects a push onto a protected destination. Retained as a known deviation for the residual "no generic technical Force-Push block" point — no `force` field exists, so there is nothing to guard for ordinary pushes.

## Review Triggers

- Git MCP is exposed to any caller other than the single trusted Agent process.
- A legitimate operational need for Force Push is identified (triggers designing the separate administrative capability referenced in Decision Details #3).

## Approval

### Required Reviewers
- Architecture Owner
- Security Reviewer

### Approval Record

- **Approved By**: Task-level approval decision (repository administrator; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

Not applicable.

## Implementation References

- `scripts/mcp_servers/git/repository_state.py` — `RepositoryState`, `RepositoryState.snapshot()`, `WriteProtectionPipeline`, `WriteProtectionPipeline.run()`
- `scripts/mcp_servers/git/git_security.py` — `GitSecurityGuards`, dispatch table
- `scripts/mcp_servers/git/git_service.py` — `GitService`, `GitService.get_dispatch_table()`
- `scripts/mcp_servers/git/format_output.py` — `format_checkout()`, `format_pull()`, `format_push()`
- `scripts/mcp_servers/git/git_server.py` — `call_tool()` endpoint, audit logging
- `scripts/mcp_servers/git/git_models.py` — `GitConfig`, request models
- Tests — `tests/mcp_servers/git/test_git_security_compliance.py`, `tests/mcp_servers/git/test_format_output.py`, `tests/mcp_servers/git/test_repository_state.py`, `tests/mcp_servers/git/test_git_service_dispatch.py`, `tests/mcp_servers/git/test_mcp_git.py`, `tests/mcp_servers/git/test_git_models.py`

## Completion Checklist

Confirm the following before changing the ADR to Accepted.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] The impact on Security has been evaluated
- [x] The impact on Operations, Monitoring, and Recovery has been evaluated
- [x] Verifiable Invariants are defined
- [x] Exceptions or out-of-scope cases are clear
- [x] Each Invariant has a corresponding Verification
- [x] Automatable verification does not rely only on Manual Review
- [x] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
- [x] Review Triggers are recorded
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas (separate confirmation required)

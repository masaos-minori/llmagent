---
title: "ADR-003: Git MCP Server-Side Write Enforcement"
category: adr
status: proposed
date: "2026-08-21"
last_updated: "2026-08-21"
owners:
  - agent-team
reviewers:
  - architecture-reviewer
  - security-reviewer
decision_scope:
  - mcp/git
related: []
supersedes: []
superseded_by: null
---

# ADR-003: Git MCP Server-Side Write Enforcement

## Status

Proposed

Allowed values: `Proposed`, `Accepted`, `Rejected`, `Deprecated`, `Superseded`. Changing an Accepted decision requires a new ADR that supersedes this one, not an edit to this body.

## Summary

Agent-side approval confirms user intent; it does not verify that a Git write operation is technically safe. Git MCP MUST enforce protected-branch, Force-Push, Dirty-Worktree, and ref/remote validation independently of Agent-side approval, using constrained argument validation rather than passing caller-supplied strings through to the underlying `git` CLI unchecked. This ADR records that requirement and the specific gap between it and the current implementation, which was confirmed exploitable during investigation.

## Context

### Problem

Git MCP's `git_checkout`/`git_pull`/`git_push` currently enforce only two checks: repository-path allowlisting and a global `read_only` flag. No check distinguishes these three operations from each other or from safer write tools (`git_add`, `git_commit`). Critically, the `branch`/`remote` arguments are forwarded to GitPython without validation, and a value such as `"--force"` is interpreted by the underlying `git` CLI as an option rather than a ref name — confirmed in a sandboxed reproduction to cause an unwarned forced checkout (discarding uncommitted changes) and a forced push (overwriting a diverged remote branch). Separately, project documentation (`00_security_02_high-risk-tool-common-policy.md`) previously claimed Git MCP already implements `protected_branches` and `force_push_blocked`, which was factually incorrect and has been corrected as part of this documentation update.

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
4. A protected-branch policy MUST be enforced by Git MCP itself for `git_checkout`/`git_push` against configured protected branches, independent of any Agent-side branch-name checks (which today apply only to `github_*` tools, not local git).
5. `git_checkout`/`git_pull` MUST reject execution against a Dirty Worktree unless a documented safe exception applies; Detached HEAD MUST be rejected unless explicitly permitted by policy.
6. Postcondition verification MUST confirm the resulting branch/HEAD and detect unresolved conflicts before reporting success; a `git` command that exits non-zero already fails today, but a low-level "did we actually end up where we intended" check is not the same guarantee.
7. Audit records for Git MCP write operations MUST include the correct repository identity; the current `target` field is suspected to always be empty due to a key-name mismatch (`"repo"` vs. the schema's `repo_path`) and MUST be fixed as part of closing this gap.

### Scope

- **Components**: `scripts/mcp_servers/git/git_service.py`, `git_security.py`, `format_output.py`, `tool_validators.py`, `git_server.py`.
- **Tools**: `git_checkout`, `git_pull`, `git_push` specifically; `git_add`/`git_commit` are lower-risk and out of scope for command-specific guards beyond the existing common guard.

### Out of Scope

- GitHub MCP's existing `protected_branches`/force-push handling (already implemented separately; not part of this decision).
- Redesign of the Agent-side approval risk-tier mapping (tracked separately as Known Issue MCP-004).
- Any capability to allow Force Push, even as an administrative feature — this ADR only requires that if such a capability is later added, it MUST NOT be the default `git_push` path.

## Rationale

### 1. Correctness / Security

An MCP server that accepts unvalidated ref-shaped strings and forwards them to an external CLI process is exposed to option-injection regardless of what its own JSON schema appears to allow. Omitting a `force` field from the schema is not a control if the same effect is reachable through `branch`.

### 2. Defense in Depth

Relying solely on Agent-side approval collapses two independent layers (user-intent confirmation and technical safety) into one, so a bypass of the approval UI (or a call made directly against the MCP HTTP endpoint) removes all protection. Server-side enforcement keeps a technical floor regardless of how the call arrived.

### 3. Auditability

A write surface with this risk profile (repository state mutation, potential history rewrite) requires an audit trail that actually identifies which repository was affected; an audit record with an empty `target` field defeats the purpose of auditing this tool category.

## Alternatives Considered

### Alternative A: Rely entirely on Agent-side approval and leave Git MCP as a thin wrapper

#### Advantages
Less code in the MCP server; simpler tool implementation.

#### Disadvantages
No protection if the approval step is bypassed or the MCP endpoint is reached directly; the confirmed option-injection exploit remains open regardless of approval-layer changes.

#### Reason for Rejection
Violates the layered-protection principle already adopted for other high-risk MCP tools (`00_security_02_high-risk-tool-common-policy.md`); approval is a UX/intent layer, not a technical control.

### Alternative B: Block `git_checkout`/`git_pull`/`git_push` entirely until guards are implemented

#### Advantages
Removes the exploitable surface immediately.

#### Disadvantages
Removes legitimate, currently-relied-upon functionality; disproportionate to the risk for a single-operator local-git use case.

#### Reason for Rejection
The immediate, low-cost mitigation (reject option-shaped `branch`/`remote` values) addresses the confirmed exploit without removing the tools; full guard implementation can follow as a normal implementation task.

## Consequences

### Positive Consequences
- Closes a confirmed exploitable gap (forced checkout/push via argument injection).
- Makes Git MCP's safety posture consistent with the common high-risk-tool policy it is supposed to follow.

### Negative Consequences
- Adds validation code and (for protected branches) configuration surface to a previously minimal server.
- May reject legitimate ref names that happen to resemble options; needs a clear, documented safe-ref pattern to avoid false rejections.

### Operational Consequences
- Operators configuring Git MCP will need to define a protected-branch list, analogous to GitHub MCP's existing configuration.

### Security Consequences
- Closes the option-injection vector confirmed during investigation (MCP-003).
- Requires fixing the audit `target` field (MCP-005) so this tool category's audit trail is actually usable.

## Invariants

- INV-01: `branch`/`remote` values MUST be rejected if they do not match a safe ref/remote-name pattern.
- INV-02: `git_push` MUST NOT perform a forced update through the normal tool path.
- INV-03: `git_checkout`/`git_push` against a configured protected branch MUST be rejected unless a separately approved policy explicitly allows it.
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
- **Test**: `git_checkout`/`git_push` reject a `branch`/`remote` value shaped like a CLI option — **Verifies**: INV-01 — **Type**: Regression — **Blocking**: Yes
- **Test**: `git_push` cannot force-update a diverged remote branch through the normal path — **Verifies**: INV-02 — **Type**: Integration — **Blocking**: Yes
- **Test**: push/checkout against a configured protected branch is rejected — **Verifies**: INV-03 — **Type**: Integration — **Blocking**: Yes

### Manual Review
- Confirm the audit `target` field fix (MCP-005) via an actual captured log line before closing this ADR's implementation gap.

## Migration and Rollout

No existing callers rely on Force Push or protected-branch bypass being possible (no such capability is currently exposed as an intentional feature), so closing this gap is not expected to break existing legitimate usage.

### Compatibility
Ref values that were never valid git refs to begin with (i.e., only option-injection strings) lose the ability to reach `git` as an argument; this is the intended effect, not a compatibility break.

### Rollback
Revert the validation change if it is found to reject legitimate ref names not anticipated by the safe-ref pattern; track any such false rejection as a bug in the pattern, not a reason to remove the check.

### Completion Criteria
This ADR moves to Accepted once INV-01 through INV-04 are implemented and covered by the tests above, and MCP-003/MCP-005 are closed.

## Implementation Notes

- Implementation files: `scripts/mcp_servers/git/git_service.py`, `git_security.py`, `format_output.py`, `tool_validators.py`
- Key symbols: `GitSecurityGuards`, `GitService.get_dispatch_table()`, `format_checkout()`, `format_pull()`, `format_push()`
- Corresponding tests: `tests/mcp_servers/git/test_mcp_git.py`, `test_git_service_dispatch.py`

## Known Deviations

- **Known Issue**: MCP-003 — no protected-branch/Force-Push guard; confirmed option-injection exploit via `branch`/`remote`.
- **Known Issue**: MCP-004 — approval tier for these tools falls back to `MEDIUM` (`y/N`) rather than the documented `HIGH` (full-word `yes`).
- **Known Issue**: MCP-005 — audit `target` field likely always empty due to a key-name mismatch.

## Review Triggers

- Git MCP is exposed to any caller other than the single trusted Agent process.
- A legitimate operational need for Force Push is identified (triggers designing the separate administrative capability referenced in Decision Details #3).

## Approval

### Required Reviewers
- Architecture Owner
- Security Reviewer

### Approval Record
- **Approved By**: pending
- **Approval Date**: pending

## Related Documents

### Specifications
- [MCP Server Catalog: git-mcp](../04_mcp_04_05_git.md)
- [High-Risk MCP Tool Common Policy](../00_security_02_high-risk-tool-common-policy.md)
- [Fail-Open/Fail-Closed and Risk Tiers](../04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md)

### Known Issues
- MCP-003, MCP-004, MCP-005 in [MCP Known Issues](../04_mcp_90_inconsistencies_and_known_issues.md)

### Implementation References
- `scripts/mcp_servers/git/git_service.py` — `GitSecurityGuards`, dispatch table
- `scripts/mcp_servers/git/format_output.py` — `format_checkout()`, `format_pull()`, `format_push()`

## Change History

- 2026-08-21: Created as Proposed.

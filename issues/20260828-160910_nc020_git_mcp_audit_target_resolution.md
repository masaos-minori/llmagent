# NC-020: Git MCP audit-log target resolution — confirm in production, then implement canonical, common resolution (closes MCP-005)

## Priority
Medium

## Summary
`NC-020` asks whether the Git MCP audit log's `target` field is actually always empty in
production. Code inspection shows the specific key-mismatch originally suspected
(`req.args.get("repo", "")` vs. the schema's `repo_path`) was already fixed in
`scripts/mcp_servers/git/git_server.py` on 2026-08-21 (commit `a53e9c62d`) — but this fix has
never been confirmed against a live audit log line, and `NC-020`/`MCP-005`'s tracking-doc text
still describes the old, now-incorrect `"repo"` key. Beyond that narrow point, this issue's
acceptance criteria describe a materially more robust audit-target design (canonical identity,
common resolution, pre-/post-validation distinction, credential scrubbing, correlation ID) that
is confirmed to still be missing regardless of the key-name fix. Resolve in three phases: (1)
capture real logs to establish current, accurate ground truth, (2) implement common canonical
target resolution, (3) add regression coverage.

## Background
`NC-020` is tracked in `docs/00_governance_03_issue-and-uncertainty-management.md` (Active
Items); `MCP-005` is tracked in `docs/04_mcp_90_inconsistencies_and_known_issues.md`.
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` Decision Details #7 requires that
"Audit records for Git MCP write operations MUST include the correct repository identity,"
explicitly naming the same `"repo"`/`repo_path` key mismatch as something that "MUST be fixed as
part of closing this gap." `scripts/mcp_servers/audit.py` defines the `AuditRecord`
TypedDict/`_audit_log()` helper shared by all MCP servers (git, github, cicd, mdq, web_search,
shell); Git MCP has exactly one call site for it, in `scripts/mcp_servers/git/git_server.py::call_tool()`.

## Problem
Confirmed by reading current code (not yet confirmed by a live captured log line):

- **Key-mismatch status is stale in the tracking docs.** `git_server.py` line 137 currently reads
  `target=cast(str, req.args.get("repo_path", ""))` — the correct key — as of commit `a53e9c62d`
  (2026-08-21, "docs: update ADRs, document guides, and fix code drift"). `NC-020`'s Evidence and
  `MCP-005`'s Summary/Current Description still describe the call site as reading `"repo"`. This
  specific claim needs correcting in both tracking entries regardless of what live-log capture
  finds.
- **Target is the raw, unvalidated caller string, not a canonical identity.**
  `GitSecurityGuards._check_repo_path()` (`scripts/mcp_servers/git/git_security.py`) already
  computes `target = Path(repo_path).resolve()` to validate the path against
  `allowed_repo_paths`, but only returns `(bool, str)` — the resolved path is discarded rather
  than reused for the audit record. The audit `target` is therefore whatever string the caller
  supplied, before validation.
- **Pre-dispatch rejections are never audited at all.** In `call_tool()`, the "Tool disabled"
  early return (`_git_tool_availability()` check) and the `validate_args()` `ValueError` early
  return both `return CallToolResponse(...)` before `_audit_log()` is ever called. No audit
  record — not even an empty one — is emitted for either case, so there is currently no way to
  distinguish "rejected before execution" from "failed during/after execution" in the audit log;
  the former simply produces no entry.
- **`remote` is unvalidated free text that could carry credentials.** The `git_pull`/`git_push`
  schemas describe `remote` as a plain "Remote name" (default `"origin"`), but the only
  validation applied (`_is_safe_ref()`) rejects option-injection shapes, not URL shapes. A
  credential-bearing URL (e.g. `https://user:token@host/repo.git`, which `git` itself accepts in
  place of a remote name for a one-off push/pull) passed as `remote` is not rejected, and nothing
  currently scrubs credentials before any such value could reach a log line.
- **A correlation mechanism may already exist but is unconfirmed for Git MCP.** The MCP-server
  `AuditRecord` already carries `request_id` (a per-call ID minted by each server's own
  middleware and returned via the `X-Request-Id` response header), and the Agent-side
  `scripts/agent/tool_audit.py::audit_tool_exec()` already records the same value as
  `mcp_request_id`. This may already satisfy "correlate an Agent-side identifier with the MCP
  execution record" for Git MCP specifically — this needs to be verified (is `request_id`
  reliably non-empty for git calls, and is it actually joinable to the approval decision record
  `audit_approval_requested()` writes under `approval_id`?) before concluding new plumbing is
  required.
- **No existing test asserts on the audit `target` field's content.** `tests/mcp_servers/git/test_mcp_git.py`
  and `test_git_service_dispatch.py` do not currently parse or assert on emitted audit JSON lines.

## Reason for Change
Git MCP's write tools (`git_checkout`, `git_pull`, `git_push`, plus `git_add`/`git_commit`)
mutate repository state and are documented as a High-Severity write surface (`MCP-003`). An
audit trail for that surface that cannot reliably identify which repository was affected, cannot
distinguish a rejected call from a failed one, and has no confirmed protection against logging
credentials embedded in a remote URL is a real gap in the security/operability posture ADR-012
is meant to establish — independent of whether the originally-suspected key-mismatch bug is
already fixed. Priority is set to Medium rather than Low (the priority both tracking entries
currently carry) because the expanded scope here includes a credential-exposure-shaped risk
(security-sensitive per this skill's High-priority criteria) that the original narrow bug report
did not cover; it is not raised to High because no live evidence of an actual credential leak or
an active audit blind spot has been captured yet — that confirmation is exactly what Phase 1
below is for.

## Implementation Intent
Three phases, in order — do not skip Phase 1 based on the code-reading evidence above; it is
necessary to establish current ground truth before designing the fix, and to correct the stale
tracking-doc claims either way.

1. **Capture real logs to confirm current behavior.** Run representative Git MCP calls (success,
   rejection via disabled tool, `validate_args()` failure, dispatch failure) against a live
   instance and capture the actual emitted `AuditRecord` JSON lines. Confirm whether `target` is
   now non-empty for the already-fixed `repo_path` key, and confirm the pre-dispatch-rejection
   gap (no audit line emitted at all) reproduces as read from the code. Update `NC-020` and
   `MCP-005`'s Evidence/Current-Description text to reflect what was actually observed, including
   correcting the stale `"repo"`-key claim.
2. **Implement common, canonical target resolution.** At the single `call_tool()` chokepoint in
   `git_server.py`, introduce one target-resolution step used by every Git tool that: (a) uses
   the validated/canonical repository identity (reusing or exposing the
   `Path(repo_path).resolve()` value already computed in `GitSecurityGuards._check_repo_path()`
   instead of the raw caller string), (b) is invoked on the pre-dispatch-rejection paths too, with
   an `outcome`/`error_type` that distinguishes "rejected before validation" from "failed after
   validation," (c) never includes remote-URL credential material — scrub or reject
   credential-shaped `remote` values before they can reach the target or any log line, (d)
   confirms and, if needed, threads through whatever identifier already correlates this record
   with the Agent-side approval/tool-exec audit trail (`request_id`/`mcp_request_id`/`approval_id`
   per the Background section — extend only if Phase 1/code-reading shows the existing mechanism
   does not already cover Git MCP).
3. **Add regression coverage.** Unit test(s) for the new target-resolution function in isolation;
   integration test(s) extending `test_mcp_git.py`/`test_git_service_dispatch.py` covering
   success, pre-validation rejection, and post-validation failure paths; a log-verification test
   that parses actual emitted JSON audit lines (not just return values) and asserts on the fields
   listed in Acceptance Criteria.

## Target Files or Areas
- `scripts/mcp_servers/git/git_server.py` (`call_tool()` — audit call site and the two
  pre-dispatch early-return paths)
- `scripts/mcp_servers/git/git_security.py` (`GitSecurityGuards._check_repo_path()` — canonical
  path currently computed and discarded)
- `scripts/mcp_servers/audit.py` (shared `AuditRecord`/`_audit_log()` — confirm whether an
  `error_type` vocabulary for "rejected" vs. "failed" should be defined here for reuse, since it
  is shared across all MCP servers, or kept Git-local; `Unknown` until Phase 1/2 investigation)
- `scripts/agent/tool_audit.py` (`audit_tool_exec()`'s `mcp_request_id`, `audit_approval_requested()`'s
  `approval_id` — reference for the existing correlation mechanism to verify/reuse)
- `tests/mcp_servers/git/test_mcp_git.py`, `tests/mcp_servers/git/test_git_service_dispatch.py`
- `docs/00_governance_03_issue-and-uncertainty-management.md` (`NC-020`)
- `docs/04_mcp_90_inconsistencies_and_known_issues.md` (`MCP-005`)
- `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` (Decision Details #7 / Known
  Deviations — confirm the fix satisfies this requirement once implemented)

## Required Changes
- Capture and record real audit-log evidence per Phase 1, correcting the stale `"repo"`-key claim
  in `NC-020` and `MCP-005` regardless of what else is found.
- Implement one canonical, common target-resolution path in `git_server.py::call_tool()` used by
  every Git tool, covering: validated/canonical identity, pre-validation-rejection recording,
  credential scrubbing for `remote`, and confirmed correlation with the Agent-side audit trail.
- Add unit tests, integration tests, and a real-JSON-log-verification test per Phase 3.
- Update `NC-020`, `MCP-005`, and ADR-012 (Known Deviations / audit requirement reference) to
  reflect the resolved state once all Acceptance Criteria below are met.

## Constraints
- Do not change the audit record schema (`AuditRecord` in `scripts/mcp_servers/audit.py`) in a
  way that breaks the other MCP servers already using it (github, cicd, mdq, web_search, shell) —
  additive fields only, and only if genuinely needed after Phase 1/2 investigation.
- Do not weaken `allowed_repo_paths`/`read_only` enforcement while refactoring the target
  resolution — this issue is about what gets logged, not the access-control decision itself.

## Acceptance Criteria
`NC-020` and `MCP-005` may be marked resolved once all of the following hold:
- Git MCP audit events derive `target` from validated input/context, not the raw `repo` (or any
  other unvalidated) argument.
- The recorded target is the canonical, post-validation repository identity.
- All Git MCP tools use the same target-resolution logic.
- `target` is never empty on a successful call.
- A validated target is recorded even when the underlying git command fails.
- Pre-validation rejection and post-validation failure are distinguishable in the audit record.
- The Agent approval ID or an equivalent correlation ID can be associated with the corresponding
  MCP execution record.
- No remote-URL credential material is ever recorded.
- A unit test exists for the target-resolution logic.
- An MCP integration test exists covering success/rejection/failure paths.
- A test exists that verifies actual emitted JSON audit-log content, not just return values.
- `NC-020` and `MCP-005`'s Status and Resolution Notes are updated to reflect the outcome.
- The result does not contradict ADR-012's audit requirement (Decision Details #7).

## Testing Expectations
Unit tests for the new target-resolution function; integration tests extending
`tests/mcp_servers/git/test_mcp_git.py` and `test_git_service_dispatch.py` for
success/rejection/failure paths; a dedicated test asserting on real, emitted JSON audit-log
records (parsed, not just the function's return value).

## Documentation Impact
Yes. `docs/00_governance_03_issue-and-uncertainty-management.md` (`NC-020`) and
`docs/04_mcp_90_inconsistencies_and_known_issues.md` (`MCP-005`) must have their Evidence,
Current Description, Status, and Resolution Notes updated to reflect what Phase 1's live-log
capture actually found and what Phase 2 implemented — including correcting the stale `"repo"`-key
claim regardless of the rest of the outcome. Cross-check `docs/adr/ADR-012-...md`'s audit
requirement (Decision Details #7) and Known Deviations (`MCP-005` entry) for consistency once
resolved.

## Out of Scope
- Extending this canonical-target-resolution work to the other 7 MCP servers (github, cicd, mdq,
  web_search, shell, file_read/write/delete) — this issue is scoped to Git MCP only, per
  `NC-020`/`MCP-005`'s existing scope.
- Implementing the Dirty-Worktree/Detached-HEAD/postcondition-verification guards tracked
  separately as `GIT-001`/`GIT-002`/`NC-019` — related but independent of audit-target
  correctness.
- Redesigning the Agent-side approval/audit architecture (`tool_audit.py`) beyond confirming or
  minimally extending its existing correlation fields.

## Dependencies
- Related: `MCP-005` (this issue resolves it), `ADR-012` (Decision Details #7 governs the target
  requirement), `NC-019`/`GIT-001`/`GIT-002` (related Git MCP write-surface gaps, tracked
  separately and not blocking this issue).

## Unresolved Questions
- Whether the existing `request_id`/`mcp_request_id` correlation already satisfies the
  Agent-approval-correlation acceptance criterion for Git MCP specifically, or whether
  `approval_id` itself needs to be threaded through as a new field — needs confirmation during
  Phase 1/2 investigation rather than assumed either way here.
- Whether `error_type`/outcome vocabulary for "rejected before validation" vs. "failed after
  validation" should live in the shared `scripts/mcp_servers/audit.py` (for reuse by other
  servers later) or remain Git-local for now, given this issue's scope is Git-only — left to the
  implementer once Phase 2 design is underway.

## AI Implementation Instruction
Follow the three phases in order — do not implement Phase 2 without first completing Phase 1's
live-log capture, since it may change what Phase 2 actually needs to fix (e.g., the key-mismatch
itself is likely already resolved; confirm rather than re-fixing something already fixed). Before
editing, re-read `scripts/mcp_servers/git/git_server.py::call_tool()`,
`git_security.py::GitSecurityGuards._check_repo_path()`, and `scripts/mcp_servers/audit.py` in
full, and confirm the current state of the `"repo"`-vs-`"repo_path"` key (`git log -p -S'req.args.get("repo"' -- scripts/mcp_servers/git/git_server.py`)
so the fix targets only what is genuinely still broken. Do not modify `AuditRecord`'s schema in a
way that affects the other 7 MCP servers without checking their call sites first. Update
`NC-020`, `MCP-005`, and ADR-012's relevant sections as part of the same change once the
Acceptance Criteria are met — do not leave them stale.

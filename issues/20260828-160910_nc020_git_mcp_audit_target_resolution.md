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
common resolution, pre-/post-validation distinction, credential scrubbing, correlation ID).
Adversarial verification found a close, directly reusable precedent for most of this design
already implemented for `mdq` MCP, and also found that the credential-exposure risk this issue
worries about on the Git-MCP-server side is currently only prospective — while a materially real,
currently-live version of that same risk already exists on the Agent side, outside this issue's
original scope. Resolve in three phases: (1) capture real logs to establish current, accurate
ground truth, (2) implement common canonical target resolution (using `mdq`'s pattern as a
reference), (3) add regression coverage.

## Background
`NC-020` is tracked in `docs/00_governance_03_issue-and-uncertainty-management.md` (Active
Items); `MCP-005` is tracked in `docs/04_mcp_90_inconsistencies_and_known_issues.md`.
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` Decision Details #7 requires that
"Audit records for Git MCP write operations MUST include the correct repository identity,"
explicitly naming the same `"repo"`/`repo_path` key mismatch as something that "MUST be fixed as
part of closing this gap" — this requirement is repeated in at least 4 locations in the ADR
(Decision Details #7, Rationale §3, Verification's Manual Review note, and the Known Deviations
`MCP-005` entry), all still describing the bug as open. `scripts/mcp_servers/audit.py` defines
the `AuditRecord` TypedDict/`_audit_log()` helper shared by all MCP servers (git, github, cicd,
mdq, web_search, shell); Git MCP has exactly one call site for it, in
`scripts/mcp_servers/git/git_server.py::call_tool()`.

**Directly relevant prior art this issue should build on, not design from scratch:**
`scripts/mcp_servers/mdq/audit_target.py::extract_audit_target()` already implements almost
exactly the "common, canonical target-resolution function used by every tool" pattern this
issue's Phase 2 needs, with its own dedicated test file
(`tests/mcp_servers/mdq/test_audit_target.py`). `mdq_server.py`'s exception-handler-based flow
(`_mdq_error_handler`) already audits rejection/failure paths with `error_type` populated, and
`tests/mcp_servers/mdq/test_mdq_exception_handlers.py::test_logs_audit_entry_with_error_type`
asserts on the audit call's `error_type`/`outcome`/`server_key` kwargs. Reviewing this pattern
before designing Git MCP's version should substantially de-risk and speed up Phase 2.

## Problem
Confirmed by reading current code (not yet confirmed by a live captured log line except where
noted):

- **Key-mismatch status is stale in the tracking docs.** `git_server.py` line 137 currently reads
  `target=cast(str, req.args.get("repo_path", ""))` — the correct key — as of commit `a53e9c62d`
  (2026-08-21, "docs: update ADRs, document guides, and fix code drift"). `NC-020`'s Evidence and
  `MCP-005`'s Summary/Current Description still describe the call site as reading `"repo"`. This
  specific claim needs correcting in both tracking entries regardless of what live-log capture
  finds. (Confirmed distinct from a similar-looking case: `cicd_server.py` also reads
  `req.args.get("repo", "")`, but `cicd`'s own schema field really is named `"repo"` — that is not
  a parallel unfixed bug, just a different, correctly-named field.)
- **Target is the raw, unvalidated caller string, not a canonical identity.**
  `GitSecurityGuards._check_repo_path()` (`scripts/mcp_servers/git/git_security.py`) already
  computes `target = Path(repo_path).resolve()` to validate the path against
  `allowed_repo_paths`, but only returns `(bool, str)` — the resolved path is discarded rather
  than reused for the audit record. The audit `target` is therefore whatever string the caller
  supplied, before validation.
- **Pre-dispatch rejections are never audited at all — and this is a systemic pattern across MCP
  servers, not Git-specific, with at least one server defending it as intentional.** In
  `call_tool()`, the "Tool disabled" early return and the `validate_args()` `ValueError` early
  return both `return CallToolResponse(...)` before `_audit_log()` is ever called — no audit
  record is emitted for either case. The same gate-before-audit placement exists in
  `shell_server.py` and `cicd_server.py`. `web_search_server.py` has the identical placement, but
  with an explicit code comment defending it: "Disabled-tool gate — must come BEFORE the try
  block so a disabled-tool rejection is not misclassified into the audit log's error-type
  taxonomy." Fixing this for Git MCP alone (this issue's stated scope) will make Git MCP diverge
  from what looks like a deliberate cross-server convention — this needs a decision, not just an
  implementation, before Phase 2 proceeds (see Unresolved Questions).
- **`remote` is unvalidated free text that could carry credentials — but this risk is currently
  prospective on the Git-MCP-server side specifically, while a materially real version of the
  same risk already exists today on the Agent side, outside this issue's original scope.** The
  `git_pull`/`git_push` schemas describe `remote` as a plain "Remote name" (default `"origin"`),
  validated only by `_is_safe_ref()` (rejects CLI-option-injection shapes, not URL shapes). On the
  Git-MCP-server side, `remote` is never actually logged today — `git_server.py`'s `_audit_log()`
  call only ever passes `repo_path` as `target`, so there is no live MCP-server-side leak yet;
  the risk is design-time, tied to how Phase 2's "canonical target" gets built. **However**,
  `scripts/agent/tool_audit.py::audit_approval()`/`audit_tool_exec()` both call
  `mask_args(args, ctx.cfg.tool.masked_fields)` and write the resulting `args_preview` —
  effectively the full args dict, only fields named in `masked_fields` are redacted — verbatim
  into the Agent-side `tool_approval`/`tool_exec` audit log. `config/agent.toml`'s
  `masked_fields = ["file_content"]` does not include `remote`. So a credential-bearing URL
  passed as `remote` to `git_push`/`git_pull` is written in plaintext into the Agent-side audit
  JSON **today**, independent of anything this issue's Git-MCP-server-scoped fix would touch.
  This is a real, currently-existing gap that sits in `scripts/agent/tool_audit.py` — which this
  issue's Out of Scope section explicitly excludes from redesign.
- **A correlation mechanism may already exist but does not currently join the way one might
  assume.** The MCP-server `AuditRecord` carries `request_id` (a per-call ID minted by each
  server's own middleware, `uuid.uuid4()` in `attach_auth_middleware`, returned via the
  `X-Request-Id` response header), and `scripts/agent/tool_audit.py::audit_tool_exec()` records
  the same value as `mcp_request_id`. Confirmed: `approval_id` (from `audit_approval_requested()`)
  and `mcp_request_id`/`request_id` are **not** the same key — they are minted at different points
  by different mechanisms, and the only fields the two event types share are
  `task_id`/`workflow_id`/`session_id`, not a direct join key. So `request_id`/`mcp_request_id`
  already correlates an MCP execution record back to the Agent's own tool-exec log entry, but does
  **not** currently provide a path from an approval decision (`approval_id`) to the MCP execution
  record — if the acceptance criterion "Agent approval ID... can be associated with the
  corresponding MCP execution record" is meant literally (approval_id specifically), this is a
  confirmed gap, not an already-satisfied requirement.
- **`error_type` is not a new field to add — it already exists in the shared `AuditRecord` schema,
  with two already-inconsistent vocabularies in use.** `scripts/mcp_servers/audit.py`'s
  `AuditRecord.error_type: str` and `_audit_log()`'s `error_type: str = ""` parameter already
  exist today. `mdq_server.py` and `web_search_server.py` already populate it — but with different
  styles (`web_search` uses lowercase-snake strings like `"validation_error"`; `mdq` uses Python
  exception-class names via `type(exc).__name__`). The real design question for Phase 2 is which
  vocabulary style Git MCP should adopt, not whether the field needs to be introduced.
- **No existing test anywhere in the MCP test suite parses real emitted JSON audit-log lines —
  not even `mdq`'s.** `tests/mcp_servers/mdq/test_mdq_exception_handlers.py` only mocks
  `_audit_log` and asserts on the call's kwargs; it does not parse actual log output. This means
  the Acceptance Criteria item "a test exists that verifies actual emitted JSON audit-log
  content" has zero precedent anywhere in this codebase to copy — it is a genuinely novel test
  shape, not a routine addition.

## Reason for Change
Git MCP's write tools (`git_checkout`, `git_pull`, `git_push`, plus `git_add`/`git_commit`)
mutate repository state and are documented as a High-Severity write surface (`MCP-003`). An
audit trail for that surface that cannot reliably identify which repository was affected and
cannot distinguish a rejected call from a failed one is a real gap in the operability posture
ADR-012 is meant to establish, independent of whether the originally-suspected key-mismatch bug
is already fixed. Priority is Medium rather than Low (what both tracking entries currently carry)
primarily for that operability reason; it is **not** primarily because of an active,
already-observed credential leak on the component this issue actually touches — on the
Git-MCP-server side specifically, the credential-exposure risk is prospective, tied to how Phase
2's target-resolution design turns out, not something currently happening. The materially real,
currently-live version of that risk lives on the Agent side (`scripts/agent/tool_audit.py`'s
unmasked `args_preview`) and is explicitly out of scope here (see Out of Scope) — it is flagged as
a separate, likely higher-urgency follow-up rather than folded into this issue's priority
reasoning, since fixing it properly would benefit every tool with a credential-shaped argument,
not just Git's `remote`.

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
2. **Implement common, canonical target resolution — modeled on `mdq`'s existing pattern.**
   Read `scripts/mcp_servers/mdq/audit_target.py::extract_audit_target()` and
   `mdq_server.py`'s exception-handler flow first; do not design from a blank slate. At the
   single `call_tool()` chokepoint in `git_server.py`, introduce one target-resolution step used
   by every Git tool that: (a) uses the validated/canonical repository identity (reusing or
   exposing the `Path(repo_path).resolve()` value already computed in
   `GitSecurityGuards._check_repo_path()` instead of the raw caller string), (b) is invoked on
   the pre-dispatch-rejection paths too — **only after resolving the cross-server
   convention question in Unresolved Questions below**, since `web_search_server.py` defends the
   current placement as intentional and changing only Git MCP's behavior would create a new
   inconsistency, (c) never includes remote-URL credential material in the Git-MCP-server-side
   audit record specifically — scrub or reject credential-shaped `remote` values before they can
   reach the target or any log line on this side, while treating the Agent-side `tool_audit.py`
   exposure as a separate, out-of-scope finding to be filed independently, (d) adopts a
   deliberate `error_type` vocabulary choice (matching one of `mdq`'s or `web_search`'s existing
   styles, or documenting a reason to introduce a third) rather than treating the field as new,
   and (e) confirms that `request_id`/`mcp_request_id` already correlates MCP execution records
   with the Agent's tool-exec log — and, separately, decides whether `approval_id` specifically
   also needs a new plumbing path, since it does not currently share a key with `request_id`.
3. **Add regression coverage.** Unit test(s) for the new target-resolution function in isolation
   (`mdq`'s `test_audit_target.py` as a structural template); integration test(s) extending
   `test_mcp_git.py`/`test_git_service_dispatch.py` covering success, pre-validation rejection,
   and post-validation failure paths; a log-verification test that parses actual emitted JSON
   audit lines and asserts on the fields listed in Acceptance Criteria — note this has no
   existing precedent anywhere in this codebase (see Problem), so budget time for designing the
   test harness itself, not just the assertions.

## Target Files or Areas
- `scripts/mcp_servers/git/git_server.py` (`call_tool()` — audit call site and the two
  pre-dispatch early-return paths)
- `scripts/mcp_servers/git/git_security.py` (`GitSecurityGuards._check_repo_path()` — canonical
  path currently computed and discarded)
- `scripts/mcp_servers/audit.py` (shared `AuditRecord`/`_audit_log()` — `error_type` already
  exists; the question is vocabulary choice, not field addition)
- `scripts/mcp_servers/mdq/audit_target.py`, `mdq_server.py` (reference implementation to model
  Phase 2 on — read before designing anything new)
- `scripts/mcp_servers/web_search/web_search_server.py` (reference for the explicit
  gate-before-audit design comment relevant to Unresolved Questions)
- `scripts/agent/tool_audit.py` (`audit_tool_exec()`'s `mcp_request_id`,
  `audit_approval_requested()`'s `approval_id`, and `mask_args()`/`masked_fields` — reference for
  the existing correlation mechanism and the out-of-scope credential-masking gap; do not redesign
  here, see Out of Scope)
- `tests/mcp_servers/git/test_mcp_git.py`, `tests/mcp_servers/git/test_git_service_dispatch.py`
- `tests/mcp_servers/mdq/test_audit_target.py`, `test_mdq_exception_handlers.py` (structural
  templates for Phase 3)
- `docs/00_governance_03_issue-and-uncertainty-management.md` (`NC-020`)
- `docs/04_mcp_90_inconsistencies_and_known_issues.md` (`MCP-005`)
- `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` (Decision Details #7, Rationale §3,
  Verification, and Known Deviations — all four locations reference this bug and need correcting
  together)

## Required Changes
- Capture and record real audit-log evidence per Phase 1, correcting the stale `"repo"`-key claim
  in `NC-020` and `MCP-005` regardless of what else is found.
- Resolve the cross-server "pre-dispatch rejection skips audit" question (see Unresolved
  Questions) before implementing Git MCP's version of that change.
- Implement one canonical, common target-resolution path in `git_server.py::call_tool()` used by
  every Git tool, modeled on `mdq`'s `extract_audit_target()` pattern, covering: validated/
  canonical identity, pre-validation-rejection recording (once the cross-server question above is
  resolved), a deliberate `error_type` vocabulary choice, and Git-MCP-server-side credential
  scrubbing for `remote`.
- Add unit tests, integration tests, and a real-JSON-log-verification test per Phase 3.
- Update `NC-020`, `MCP-005`, and all four ADR-012 locations that reference this bug to reflect
  the resolved state once all Acceptance Criteria below are met.
- File a separate follow-up issue for the Agent-side `tool_audit.py`/`mask_args()`/`masked_fields`
  credential-exposure gap (see Out of Scope) — do not fold it into this issue's implementation.

## Constraints
- Do not change the audit record schema (`AuditRecord` in `scripts/mcp_servers/audit.py`) in a
  way that breaks the other MCP servers already using it (github, cicd, mdq, web_search, shell) —
  additive fields only, and only if genuinely needed after Phase 1/2 investigation. `error_type`
  already exists and needs no schema change.
- Do not weaken `allowed_repo_paths`/`read_only` enforcement while refactoring the target
  resolution — this issue is about what gets logged, not the access-control decision itself.
- Do not redesign `scripts/agent/tool_audit.py`'s masking (`mask_args()`/`masked_fields`) as part
  of this issue — file it separately (see Required Changes and Out of Scope).

## Acceptance Criteria
`NC-020` and `MCP-005` may be marked resolved once all of the following hold:
- Git MCP audit events derive `target` from validated input/context, not the raw `repo` (or any
  other unvalidated) argument.
- The recorded target is the canonical, post-validation repository identity.
- All Git MCP tools use the same target-resolution logic.
- `target` is never empty on a successful call.
- A validated target is recorded even when the underlying git command fails.
- Pre-validation rejection and post-validation failure are distinguishable in the audit record,
  in a way that is consistent with (or that deliberately and explicitly revises) the same
  decision already made for `shell`/`cicd`/`web_search` MCP servers.
- `request_id`/`mcp_request_id` correlation is confirmed to already associate an MCP execution
  record with the Agent's tool-exec log; if `approval_id` specifically must also be associated,
  that plumbing is added — this criterion is satisfied by either confirming the existing
  mechanism suffices or by adding the missing link, not assumed to already be complete.
- No remote-URL credential material is ever recorded in the **Git-MCP-server-side** audit
  record produced by this issue's work. (The separate, currently-real Agent-side exposure via
  `tool_audit.py`'s unmasked `args_preview` is out of scope for this criterion — tracked as a
  follow-up issue instead.)
- A unit test exists for the target-resolution logic.
- An MCP integration test exists covering success/rejection/failure paths.
- A test exists that verifies actual emitted JSON audit-log content, not just return values.
- `NC-020` and `MCP-005`'s Status and Resolution Notes are updated to reflect the outcome.
- The result does not contradict ADR-012's audit requirement (Decision Details #7; also update
  Rationale §3, the Verification Manual Review note, and the Known Deviations entry — all four
  currently reference this bug).

## Testing Expectations
Unit tests for the new target-resolution function, structured like
`tests/mcp_servers/mdq/test_audit_target.py`; integration tests extending
`tests/mcp_servers/git/test_mcp_git.py` and `test_git_service_dispatch.py` for
success/rejection/failure paths; a dedicated test asserting on real, emitted JSON audit-log
records (parsed, not just the function's return value or mocked call kwargs) — note this test
shape has no existing precedent in this codebase, budget accordingly.

## Documentation Impact
Yes. `docs/00_governance_03_issue-and-uncertainty-management.md` (`NC-020`) and
`docs/04_mcp_90_inconsistencies_and_known_issues.md` (`MCP-005`) must have their Evidence,
Current Description, Status, and Resolution Notes updated to reflect what Phase 1's live-log
capture actually found and what Phase 2 implemented — including correcting the stale `"repo"`-key
claim regardless of the rest of the outcome. `docs/adr/ADR-012-...md` references this bug in four
places (Decision Details #7, Rationale §3, Verification, Known Deviations) — update all four
together, not just one, once resolved.

## Out of Scope
- Extending this canonical-target-resolution work to the other 7 MCP servers (github, cicd, mdq,
  web_search, shell, file_read/write/delete) — this issue is scoped to Git MCP only, per
  `NC-020`/`MCP-005`'s existing scope. (`mdq` already has its own equivalent; the others do not.)
- Implementing the Dirty-Worktree/Detached-HEAD/postcondition-verification guards tracked
  separately as `GIT-001`/`GIT-002`/`NC-019` — related but independent of audit-target
  correctness.
- Redesigning the Agent-side approval/audit architecture (`tool_audit.py`) beyond confirming or
  minimally extending its existing correlation fields. **In particular, fixing
  `mask_args()`/`masked_fields`'s failure to redact credential-shaped values (e.g. a
  credential-bearing `remote` URL) from the Agent-side `args_preview` is explicitly out of
  scope here** — this is a real, currently-live gap (see Problem), but it affects every tool with
  a credential-shaped argument, not just Git's `remote`, and deserves its own issue rather than a
  narrow fix folded into this one.
- Changing the cross-server "pre-dispatch rejection skips audit" convention for any server other
  than Git MCP, and even for Git MCP, only after the Unresolved Question below is resolved.

## Dependencies
- Related: `MCP-005` (this issue resolves it), `ADR-012` (governs the target requirement across
  4 locations), `NC-019`/`GIT-001`/`GIT-002` (related Git MCP write-surface gaps, tracked
  separately and not blocking this issue).
- A new, not-yet-filed issue is warranted for the Agent-side `tool_audit.py`/`mask_args()`
  credential-exposure gap found during this issue's verification (see Problem/Out of Scope) —
  out of scope here, flagged for separate filing.

## Unresolved Questions
- **Cross-server pre-dispatch-audit convention.** `web_search_server.py` has an explicit code
  comment defending "disabled-tool gate before audit" as intentional (to avoid misclassifying a
  disabled-tool rejection into the audit error-type taxonomy). Before implementing "audit
  pre-dispatch rejections too" for Git MCP, decide: (a) is that web_search comment's reasoning
  still considered correct project-wide, in which case Git MCP's current behavior is actually
  consistent with intended design and this Acceptance Criterion should be dropped or reframed, or
  (b) was that a narrower, web_search-specific judgment that doesn't apply to Git MCP's
  higher-severity write surface, in which case Git MCP can diverge deliberately. This needs an
  answer before Phase 2's audit-integration work, not left to the implementer to guess.
- Whether `approval_id` specifically (not just `request_id`/`mcp_request_id`) needs a new
  plumbing path to satisfy the Agent-approval-correlation acceptance criterion, or whether the
  existing `request_id`/`mcp_request_id` correlation is what that criterion actually intended —
  confirm the criterion's original intent (this session's own drafting) against what's
  technically feasible before deciding whether new plumbing is required.

## AI Implementation Instruction
Follow the three phases in order — do not implement Phase 2 without first completing Phase 1's
live-log capture, since it may change what Phase 2 actually needs to fix (e.g., the key-mismatch
itself is likely already resolved; confirm rather than re-fixing something already fixed). Before
editing, re-read `scripts/mcp_servers/git/git_server.py::call_tool()`,
`git_security.py::GitSecurityGuards._check_repo_path()`, `scripts/mcp_servers/audit.py`, and —
critically — `scripts/mcp_servers/mdq/audit_target.py`/`mdq_server.py` and
`web_search_server.py`'s disabled-tool-gate comment, so the design is informed by existing
precedent and known cross-server tensions rather than invented from scratch. Resolve the two
Unresolved Questions above before finalizing Phase 2's design. Do not modify `AuditRecord`'s
schema in a way that affects the other 7 MCP servers without checking their call sites first, and
do not attempt to fix the Agent-side `tool_audit.py`/`mask_args()` credential-masking gap as part
of this issue — file it separately instead. Update `NC-020`, `MCP-005`, and all four `ADR-012`
locations that reference this bug as part of the same change once resolved — do not leave them
stale.

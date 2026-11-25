## Goal
- Make every GitHub write fail safe: no GitHub write is classified retryable until a tested reconciliation exists, the GitHub client itself never re-sends a write, an ambiguous timeout is reported as `outcome_unknown` and never retried, an intent audit that fails prevents the API call, and a completion-audit failure after an applied write is reported as `applied_audit_failed` instead of a generic failure.

## Priority
High

## Scope
- **In-Scope**:
  - Classify all nine GitHub writes as non-retryable by declaring `retry_policy = "never"` in the four tool tables (the classification owner) and removing them from the `RETRYABLE_TOOLS` reference set, checked by the existing drift test.
  - A GitHub client with explicit connect and read timeouts from configuration and with PyGithub's built-in retry disabled.
  - Translation of an ambiguous transport failure of a write (timeout, connection loss after send) into a typed `outcome_unknown` outcome that is never retried automatically.
  - An intent audit record written before every write API call (fail closed), and a completion audit that reports `applied_audit_failed` when it cannot be written after an applied write; session, request, and logical call identifiers in every audit record.
  - A shared write-outcome vocabulary and write-audit field contract in a new `shared` module, reusable by the Git, File, and CI/CD work items.
  - An audit-failure counter exposed in the GitHub health details.
  - Tests for classification consistency, dedup-store failure per write, API-success-plus-audit-failure, timeouts, and no-retry of `outcome_unknown`; documentation updates.
- **Out-of-Scope**:
  - Implementing any per-operation reconciler: no GitHub write stays retryable, so the reconciler registration seam of the call-state control API is left unused (see `Assumptions`).
  - Dedup storage state machine, key propagation, read authorization, Git and File MCP outcomes, the MCP design-document final sweep.
  - Any change to an ADR decision or invariant: none is required (see `Design`); no approval record is written or simulated.
  - Removing the issue-title text from the completion audit record (observed, see `Issue Verification`; a separate concern).
- **Dependencies**:
  - Every prerequisite (dedup state machine, logical key replay, GitHub read security boundary, dedup config isolation, call-state control API, runtime tool metadata) is delivered by a closed Plan. The structured execution context Plan (mcpai005) edits `github_server.py` and has procedures generated but not executed; this Plan's `github_server.py` edit is written against that Plan's context signature; see UNK-01. This Plan blocks the GitHub HTTP contract test work item and must land before automatic replay of GitHub writes is enabled.
  - **Depends on**: plans/done/20261125-121807_mcpai005_structured-execution-context.md | phase all | both edit `github_server.py` (`_dispatch_github_tool` signature and `call_tool`); land the context change first (procedures still pending; UNK-01)

## Background
- Source: consolidated review backlog (`memo-issue.md`, Issue 6), filed as `issues/20261119-140513_mcpai006_github-write-retry-policy.md`.
- Path B: more than 3 files, new module, public configuration key additions, and a deliberate behavior change (stricter classification, new failure outcomes).
- The Issue's classification evidence is stale: `config/mcp_dedup.toml` no longer exists and the classification owner is each tool's declared `retry_policy`, with `RETRYABLE_TOOLS` as drift-checked reference data (see `Issue Verification`).

## Problem
- Eight of the nine GitHub writes (issue create, comment, branch create, file update, file push, file delete, PR update, merge) declare `same_logical_call_only`, a retryable policy; only `github_create_pull_request` declares `never`. A retryable classification lets a dedup-store failure proceed unprotected (fail-open for retryable tools) and makes an interrupted call eligible for re-dispatch and Agent replay.
- The PyGithub client is built with library defaults: a single 15 second timeout and `GithubRetry(total=10)`, which retries POST, PUT, and DELETE on any 5xx status and on 403. A write can therefore be re-sent up to ten times inside one tool call, creating duplicate issues, comments, or commits before the Agent or the dedup layer sees anything.
- An ambiguous write failure (timeout, dropped connection) is not translated: it surfaces as a generic exception, which the dispatcher records as a terminal `failed` row and the HTTP layer reports as an unspecific 500.
- The audit is completion-only: it is written after the API call, a failure raises `GitHubAuditError` after the write was applied, and the response (HTTP 500) hides that the write happened, encouraging a duplicate manual retry. No intent audit exists, and audit records carry no session, request, or call identifier.

## Reason for Change
- External side effects with incomplete protection; the new behavior is stricter than the current classification, so it is a deliberate change.

## Implementation Intent
- Move classification to the conservative side in the owner (tool tables) and the reference set; build the client so it never re-sends; give ambiguous failures and audit failures their own typed outcomes mapped to explicit responses; write an intent audit before the API call; and define the vocabulary once in `shared` so the other MCP servers can adopt it.

## Requirements
- `REQ-001`: Declare `retry_policy = "never"` for `github_create_issue`, `github_add_issue_comment`, `github_create_pull_request`, `github_merge_pull_request`, `github_delete_file`, `github_push_files`, `github_create_branch`, `github_create_or_update_file`, and `github_update_pull_request`; remove the same names from `RETRYABLE_TOOLS`; the drift test passes and asserts no GitHub write is retryable.
- `REQ-002`: Build the GitHub client with explicit connect and read timeouts read from `github_mcp_server.toml` (strictly parsed, positive numbers, with documented defaults) and with the library retry disabled, so a write is sent at most once per call.
- `REQ-003`: Translate an ambiguous transport failure of a write (timeout, connection error, or an upstream 5xx) into `GitHubOutcomeUnknownError`; map it to HTTP 504 with the outcome named in the body; never retry it; the dispatcher's terminal `failed` row records the class name as evidence. A timeout never implies non-application.
- `REQ-004`: Write an intent audit record before the API call of every write; if it cannot be written, raise before any API call (fail closed, nothing applied).
- `REQ-005`: Write the completion audit after an applied write; if it fails, raise `GitHubAppliedAuditError`, which the GitHub dispatch wrapper converts to an error result `applied_audit_failed` stating that the write was applied and must not be retried; the failure is counted.
- `REQ-006`: Every GitHub audit record (intent and completion) carries the session id, request id, and logical call id (the idempotency key), alongside the existing identifiers, and never a payload.
- `REQ-007`: Define the shared write-outcome vocabulary (`outcome_unknown`, `applied_audit_failed`, the rule that neither is retried automatically) and the write-audit field contract in `scripts/shared/write_outcome.py`; the GitHub code uses it.
- `REQ-008`: Expose the audit-failure count in the GitHub `/health` details.
- `REQ-009`: Tests: classification consistency, dedup-store failure for every GitHub write, API-success-plus-audit-failure for issue, comment, merge, and file update, read and write timeouts, `outcome_unknown` no-retry, client built without retry.
- `REQ-010`: Document the retry policy, timeout outcomes, and audit outcomes; document the two new configuration keys.

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-25 (fallout): added tests/mcp_servers/github/test_service_init.py — The test pins the import-time Github() singleton (lines 31-63); the client moves to build_service(cfg) with explicit timeouts and retry=None

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/write_outcome.py | Create (new file): outcome vocabulary and audit field contract | One definition reused by Git, File, CI/CD work | REQ-007; AC-3 | No such module: `rg outcome_unknown scripts/shared` finds only the dedup acquisition states (checked in Step 3) | `tests/shared/test_write_outcome.py` | Verified |
| scripts/shared/tool_constants.py | Modify: remove the eight GitHub writes it lists from `RETRYABLE_TOOLS` | Reference set must match the declarations | REQ-001; AC-1 | `RETRYABLE_TOOLS` lists eight GitHub writes at lines 184-217 (checked in Step 3) | `tests/shared/test_tool_constants.py` | Verified |
| scripts/mcp_servers/github/tools_file.py | Modify: `retry_policy` of `github_create_or_update_file`, `github_push_files`, `github_delete_file` to `never` | Classification owner | REQ-001; AC-1 | `same_logical_call_only` at lines 90, 107, 123 (checked in Step 3) | `tests/mcp_servers/github/test_github_tool_registry.py` | Verified |
| scripts/mcp_servers/github/tools_issues.py | Modify: `github_create_issue`, `github_add_issue_comment` to `never` | Classification owner | REQ-001; AC-1 | `same_logical_call_only` at lines 118, 152 (checked in Step 3) | `tests/mcp_servers/github/test_github_tool_registry.py` | Verified |
| scripts/mcp_servers/github/tools_pull_requests.py | Modify: `github_update_pull_request`, `github_merge_pull_request` to `never` | Classification owner | REQ-001; AC-1 | `same_logical_call_only` at lines 153, 169; `github_create_pull_request` already `never` at line 120 (checked in Step 3) | `tests/mcp_servers/github/test_github_tool_registry.py` | Verified |
| scripts/mcp_servers/github/tools_repository.py | Modify: `github_create_branch` to `never` | Classification owner | REQ-001; AC-1 | `same_logical_call_only` at line 123 (checked in Step 3) | `tests/mcp_servers/github/test_github_tool_registry.py` | Verified |
| scripts/mcp_servers/github/github_models_config.py | Modify: `connect_timeout_sec`, `read_timeout_sec` config fields; `GitHubOutcomeUnknownError`, `GitHubAppliedAuditError` | Timeouts and typed outcomes | REQ-002, REQ-003, REQ-005; AC-2, AC-3 | `GitHubConfig` has no timeout field; `GitHubAuditError(RuntimeError)` at line 173 (checked in Step 3) | `tests/mcp_servers/github/test_github_config_strict_parsing.py` | Verified |
| scripts/mcp_servers/github/github_service_init.py | Modify: build the client from config with timeouts and `retry=None` | Never re-send a write | REQ-002; AC-2 | `Github()` and `Github(auth=...)` built at import with defaults at lines 22-24; library default `GithubRetry(total=10)` retries POST/PUT/DELETE on 5xx and 403 (runtime check, Step 3) | `tests/mcp_servers/github/test_github_write_outcomes.py` | Verified |
| scripts/mcp_servers/github/github_service_security.py | Modify: intent and completion audit helpers with call identity, ambiguous-failure translation in `_run_github`, audit failure counter | Shared write plumbing | REQ-003, REQ-004, REQ-005, REQ-006, REQ-008; AC-2, AC-3, AC-4 | `_write_github_audit_log` at line 146 writes after the call and raises `GitHubAuditError`; `_run_github` at line 297 only maps `GithubException` (checked in Step 3) | `tests/mcp_servers/github/test_github_mcp_service.py` | Verified |
| scripts/mcp_servers/github/github_service_dispatch_writes.py | Modify: intent audit before the execute callback on the non-dry-run path | Single place before every write | REQ-004; AC-2 | `_execute_with_dry_run` at line 103: authorization, then dry-run branch, then execute (checked in Step 3) | `tests/mcp_servers/github/test_service_dispatch.py` | Verified |
| scripts/mcp_servers/github/github_service_file.py | Modify: completion audit through the applied-audit helper (3 writes) | `applied_audit_failed` | REQ-005, REQ-006; AC-3 | `_write_github_audit_log` at lines 111, 156, 185 (checked in Step 3) | `tests/mcp_servers/github/test_github_mcp_service.py` | Verified |
| scripts/mcp_servers/github/github_service_issues.py | Modify: same (2 writes) | `applied_audit_failed` | REQ-005, REQ-006; AC-3 | audit calls at lines 80, 120 (checked in Step 3) | `tests/mcp_servers/github/test_github_mcp_service.py` | Verified |
| scripts/mcp_servers/github/github_service_pull_requests.py | Modify: same (3 writes) | `applied_audit_failed` | REQ-005, REQ-006; AC-3 | audit calls at lines 93, 146, 189 (checked in Step 3) | `tests/mcp_servers/github/test_github_mcp_service.py` | Verified |
| scripts/mcp_servers/github/github_service_repository.py | Modify: same (1 write) | `applied_audit_failed` | REQ-005, REQ-006; AC-3 | audit call at line 108 (checked in Step 3) | `tests/mcp_servers/github/test_github_mcp_service.py` | Verified |
| scripts/mcp_servers/github/github_server.py | Modify: convert `GitHubAppliedAuditError` to the `applied_audit_failed` result, set the call identity, expose the audit-failure count in `/health` | Response contract and health | REQ-005, REQ-006, REQ-008; AC-3, AC-5 | `_dispatch_github_tool` at line 193; `/health` at line 177 (checked in Step 3) | `tests/mcp_servers/github/test_github_write_outcomes.py` | Verified |
| scripts/mcp_servers/github/exception_handlers.py | Modify: 504 handler for `GitHubOutcomeUnknownError`; audit handlers name the outcome | Explicit ambiguous-outcome response | REQ-003; AC-3 | `_handle_audit` returns a bare 500 (checked in Step 3) | `tests/mcp_servers/github/test_github_exception_handlers.py` | Verified |
| config/github_mcp_server.toml | Modify: add `connect_timeout_sec` and `read_timeout_sec` | Configured timeouts | REQ-002; AC-2 | Config has no timeout key (checked in Step 3) | `tests/mcp_servers/github/test_github_config_strict_parsing.py` | Verified |
| tests/shared/test_write_outcome.py | Create (new file): vocabulary and field contract | Cover REQ-007 | REQ-007, REQ-009; AC-3 | New module has no test (checked in Step 3) | itself | Verified |
| tests/shared/test_tool_constants.py | Modify: assert no GitHub write is retryable; keep the drift check | Cover REQ-001 | REQ-001, REQ-009; AC-1 | Drift test at lines 102-148 (checked in Step 3) | itself | Verified |
| tests/mcp_servers/github/test_github_tool_registry.py | Modify: declared `retry_policy` of every GitHub write is `never` | Cover REQ-001 | REQ-001, REQ-009; AC-1 | Registry tests exist (checked in Step 3) | itself | Verified |
| tests/mcp_servers/github/test_github_write_outcomes.py | Create (new file): store failure per write, API-success-plus-audit-failure, timeouts, outcome-unknown no-retry, client built without retry | Cover REQ-002 to REQ-006, REQ-008 | REQ-009; AC-2, AC-3, AC-4, AC-5 | No test covers these outcomes (checked in Step 3) | itself | Verified |
| tests/mcp_servers/github/test_github_config_strict_parsing.py | Modify: timeout key cases | Cover REQ-002 | REQ-002, REQ-009; AC-2 | Strict-parsing suite exists (checked in Step 3) | itself | Verified |
| tests/mcp_servers/github/test_github_exception_handlers.py | Modify: 504 outcome-unknown and named audit outcomes | Cover REQ-003 | REQ-003, REQ-009; AC-3 | Handler tests at line 53 (checked in Step 3) | itself | Verified |
| tests/mcp_servers/github/test_github_mcp_service.py | Modify: existing audit-failure tests (lines 202, 860) now expect the intent audit to fail first or the applied-audit outcome | Behavior change | REQ-004, REQ-005, REQ-009; AC-2, AC-3 | Tests expect `GitHubAuditError` from a write at lines 202-205 and 860 (checked in Step 3) | itself | Verified |
| tests/mcp_servers/github/test_service_dispatch.py | Modify: intent audit runs before execute and not on a dry run | Cover REQ-004 | REQ-004, REQ-009; AC-2 | Dispatch tests exist (checked in Step 3) | itself | Verified |
| docs/22_mcp/mcp_04_01_web-search-file-read-github.md | Modify: GitHub write outcomes, timeouts, audit layers | Documentation Impact | REQ-010; AC-6 | Audit and config text at lines 93-114 (checked in Step 3) | docs gates | Verified |
| docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md | Modify: GitHub writes are fail-closed on store failure and non-retryable | Documentation Impact | REQ-010; AC-6 | Mentions GitHub writes and audit (checked in Step 3) | docs gates | Verified |
| docs/22_mcp/mcp_06_01_configuration-file-inventory.md | Modify: the two new GitHub config keys | Documentation Impact | REQ-010; AC-6 | Lists GitHub config keys such as `max_file_read_size_kb` (checked in Step 3) | docs gates | Verified |
| `tests/mcp_servers/github/test_service_init.py` | Modify: characterization of the client built at import now covers the config-built client with timeouts and no retry | The test pins the import-time Github() singleton (lines 31-63); the client moves to build_service(cfg) with explicit timeouts and retry=None | REQ-002 / AC-2 | test_service_init.py asserts reloaded._gh is Github() with auth None or Auth.Token at lines 31-63 (checked in Step 3a) | itself | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/shared/tool_metadata.py | `RetryPolicy` vocabulary and `retry_policy_is_retryable` | REQ-001 |
| scripts/mcp_servers/dispatch.py | Terminal `failed` recording and the retryable fail-open path | REQ-001, REQ-003 |
| scripts/shared/mcp_dedup_claim.py | `failed` rows are terminal; only `interrupted` rows recover for retryable tools | REQ-001 |
| scripts/mcp_servers/control_api.py | Reconciler registration seam, left unused here | REQ-001 |
| scripts/shared/http_transport.py | Ambiguous 502, 503, 504 write statuses become Agent-side `outcome_unknown` | REQ-003 |
| scripts/mcp_servers/github/github_service_dispatch.py | Builds the dispatch table the intent audit wraps | REQ-004 |
| scripts/mcp_servers/github/github_models.py | Re-exports the config error classes | REQ-003, REQ-005 |
| config/agent.toml | Agent-side server table; no change needed | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): All nine GitHub writes declare `retry_policy = "never"` and are absent from `RETRYABLE_TOOLS`; no classification source marks a GitHub write retryable.
- AC-2 (REQ-002, REQ-004): The client is built with the configured timeouts and no library retry; a dedup-store failure refuses every GitHub write (fail closed); an intent-audit failure raises before the API call and applies nothing.
- AC-3 (REQ-003, REQ-005, REQ-006, REQ-007): A timeout of a write yields `outcome_unknown` (HTTP 504) and is never retried; a completion-audit failure after an applied write yields `applied_audit_failed` stating the write was applied; neither triggers an automatic retry; every audit record carries session, request, and call ids.
- AC-4 (REQ-005): The completion-audit failure does not erase the fact that the write was applied: the result says so and the dedup row stays terminal.
- AC-5 (REQ-008): `/health` reports the audit-failure count.
- AC-6 (REQ-010): The three documents describe the final behavior.

## Tests
- REQ-001: each write's declared policy is `never`; `RETRYABLE_TOOLS` contains no GitHub name; the drift check passes.
- REQ-002: patch the PyGithub constructor and assert it receives the configured timeout tuple and `retry=None`; strict-parsing cases for zero, negative, boolean, and string values.
- REQ-003: a write whose underlying call raises a read timeout, a connection error, and an upstream 5xx each yields `GitHubOutcomeUnknownError`; the HTTP layer returns 504; a second call with the same key is not re-executed (terminal row).
- REQ-004: with the store unavailable, every write refuses (non-retryable fail-closed); with an unwritable audit path the intent audit raises and the API stub is never called.
- REQ-005, REQ-006: API stub succeeds and the completion audit fails for issue, comment, merge, and file update: the result is `applied_audit_failed`; audit records contain the three identifiers and no payload text.
- REQ-007, REQ-008: vocabulary table; counter increments and appears in `/health`.

## Documentation Impact
- Yes. REQ-010 drives updates to the GitHub section of the MCP server document, the fail-open and fail-closed document, and the configuration inventory, located via `docs/00_index.md` "Document References by Task". ADR-004 and ADR-008 text is not changed because no decision or invariant changes; the final sweep of the MCP design documents stays with the separate documentation work item.

## Assumptions
- All nine writes become non-retryable, including `github_create_or_update_file` and `github_update_pull_request`, which the Issue lists only as candidates for a future reconciler: with no reconciler and no tested algorithm, the Issue's own rule ("only operations with a tested reconciliation may be retried") leaves none retryable (falsifiable at procedure review; UNK-02).
- No per-operation reconciler is implemented: every write is non-retryable, so the "every retryable write has a tested reconciliation" criterion holds vacuously and the `register_reconciler` seam stays unused.
- `outcome_unknown` is carried as the terminal dispatcher row's recorded error class and as the HTTP body, not as a new ledger status, which would need a persisted-schema change; the Agent already treats a 502, 503, or 504 response for a write as `outcome_unknown` without retry.
- The classification owner is the tools tables (`retry_policy`), exactly as the closed config-isolation and runtime-metadata Plans established; `config/mcp_dedup.toml` no longer exists, so no TOML mirror is edited.
- A single PyGithub client with `retry=None` serves reads and writes. Reads lose the library's automatic rate-limit wait; a 403 already maps to an authorization error, and safe read retry lives in the Agent transport. PyGithub passes `timeout` straight to `requests`, which accepts a `(connect, read)` tuple although the annotation says `int`; a test pins this.
- Plan Amendment: the context Plan (mcpai005) changes the `_dispatch_github_tool` signature; this Plan's wrapper edit follows that signature, so that Plan's procedures execute first.
- Overlap judgment (`tools/check_plan_target_overlaps.py`, run after the freeze): no other Frozen Plan in `plans/` lists any of these files; no overlap to judge.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The context Plan's procedures (`implementations/20261125-122426_*`) are generated but unexecuted and rewrite `github_server.py`; the dependency tool reads that Plan as closed | Implementation status when this Plan's procedures execute | Execute that Plan's `github_server.py` procedure first; re-read `_dispatch_github_tool` at procedure generation | False |
| UNK-02 | Whether the owner wants `github_create_or_update_file` and `github_update_pull_request` non-retryable now (the Issue lists them only as future-reconciler candidates) | Owner decision | Default is conservative (`never`); revert two declarations if a reconciler is planned | False |
| UNK-03 | Concrete timeout values | Operational latency data for GitHub API calls from the host | Defaults `connect_timeout_sec = 5` and `read_timeout_sec = 30`, documented as tunable; revisit with observed latency | False |
| UNK-04 | Existing tests that build `GitHubService` with fake clients and assert audit-after-write ordering | Per-test classification (about 40 test files under `tests/mcp_servers/github/`) | Run the GitHub test directory after Phase 3; fallout files are added as Fallout-class amendments | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/write_outcome.py | Create | Low | N/A | N/A | Yes: `scripts/` change needs a deploy |
| scripts/shared/tool_constants.py | Modify | Medium (18 importers of reference sets) | N/A | N/A | Yes |
| scripts/mcp_servers/github/tools_file.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/github/tools_issues.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/github/tools_pull_requests.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/github/tools_repository.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/github/github_models_config.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/github/github_service_init.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/github/github_service_security.py | Modify | High (mixin of the service) | N/A | N/A | Yes |
| scripts/mcp_servers/github/github_service_dispatch_writes.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/github/github_service_file.py | Modify | Low | N/A | N/A | Yes |
| scripts/mcp_servers/github/github_service_issues.py | Modify | Low | N/A | N/A | Yes |
| scripts/mcp_servers/github/github_service_pull_requests.py | Modify | Low | N/A | N/A | Yes |
| scripts/mcp_servers/github/github_service_repository.py | Modify | Low | N/A | N/A | Yes |
| scripts/mcp_servers/github/github_server.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/github/exception_handlers.py | Modify | Low | N/A | N/A | Yes |
| config/github_mcp_server.toml | Modify | Medium | N/A | N/A | Yes: config change needs a deploy |
| tests/shared/test_write_outcome.py | Create | Low | N/A | N/A | None |
| tests/shared/test_tool_constants.py | Modify | Low | N/A | N/A | None |
| tests/mcp_servers/github/test_github_tool_registry.py | Modify | Low | N/A | N/A | None |
| tests/mcp_servers/github/test_github_write_outcomes.py | Create | Low | N/A | N/A | None |
| tests/mcp_servers/github/test_github_config_strict_parsing.py | Modify | Low | N/A | N/A | None |
| tests/mcp_servers/github/test_github_exception_handlers.py | Modify | Low | N/A | N/A | None |
| tests/mcp_servers/github/test_github_mcp_service.py | Modify | Low | N/A | N/A | None |
| tests/mcp_servers/github/test_service_dispatch.py | Modify | Low | N/A | N/A | None |
| docs/22_mcp/mcp_04_01_web-search-file-read-github.md | Modify | Low | N/A | N/A | None |
| docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md | Modify | Low | N/A | N/A | None |
| docs/22_mcp/mcp_06_01_configuration-file-inventory.md | Modify | Low | N/A | N/A | None |
| `tests/mcp_servers/github/test_service_init.py` | Modify | Not assessed (amendment 2026-11-25) | N/A | N/A | Not assessed (amendment 2026-11-25) |

## Design
- **Issue Verification** (re-checked against current source and the installed library; Step 2):

| Issue claim | Verdict | Evidence |
|---|---|---|
| `config/mcp_dedup.toml` `[retry_class]` marks three GitHub writes retryable and is mirrored by `RETRYABLE_TOOLS` | Stale, corrected | The file no longer exists (`ls config`); the dedup config Plan removed it. The owner is each tool's `retry_policy`; `RETRYABLE_TOOLS` is reference data checked by `tests/shared/test_tool_constants.py` |
| Only three GitHub entries were read; the rest unknown | Resolved | Eight GitHub names are in `RETRYABLE_TOOLS`; eight writes declare `same_logical_call_only` and `github_create_pull_request` declares `never`; `github_delete_file` and `github_merge_pull_request` are the dangerous tier |
| `github_create_pull_request` is listed for reclassification | Already non-retryable | `tools_pull_requests.py` declares `never`; it is absent from `RETRYABLE_TOOLS`; only a test guard is needed |
| Retrying after a lost response can duplicate remote state | Confirmed, with a larger source | Beyond dedup replay, the client itself retries: `Github()` defaults to `GithubRetry(total=10)` whose `allowed_methods` include POST, PUT, DELETE and whose `status_forcelist` covers every 5xx and 403 (runtime values, PyGithub 2.9.1). A write can be re-sent up to ten times inside one call |
| Audit and timeout claims (needs confirmation) | Confirmed | The audit is completion-only (`_write_github_audit_log` after `_run_github` in nine writes) and raises `GitHubAuditError` after the write; `_run_github` only maps `GithubException`, so a timeout or connection error propagates raw and the dispatcher records a terminal `failed` row; the timeout is the library default (15 seconds) |
| A completion-audit failure is reported as a generic failure | Confirmed | `exception_handlers.py` returns a bare 500 for `GitHubAuditError` with no mention that the write was applied |
| Audit records carry session, request, and call identifiers | Contradicted | `_write_github_audit_log` records only `repo`, `number`, `title`-style fields, `before/after`, and `approved=true`; no identifier |
| (Found) The audit record logs the issue title | Observed, out of scope | `create_issue` passes `title=req.title` although the helper's comment says contents are never logged |
| Timeout values are unknown | Resolved as a default | Library default 15 seconds today; this Plan sets configured connect and read values (UNK-03) |

- **ADR check**: ADR-004 (failure handling) already describes retryable versus non-retryable fail-open and fail-closed behavior; this Plan changes which tools are non-retryable, not the rule. ADR-008 owns the disposable dedup store and is untouched. No decision or invariant changes, so no approval record is needed.
- **Dispatcher interaction**: a non-retryable write fails closed when the durable store is unavailable (the existing `_degraded_decision` and `_acquire_dedup` branches), and an interrupted row is not re-opened for it (`allow_interrupted_recovery` follows retryability). An ambiguous failure becomes a terminal `failed` row (`replay_unavailable`), so a repeat of the same key never re-executes.
- **Audit flow**: the intent audit sits in `_execute_with_dry_run` after authorization and the dry-run branch (a preview writes nothing), before `execute_callback`. The completion audit stays in each service method after the API call and raises `GitHubAppliedAuditError` on failure; `_dispatch_github_tool` converts it to `error_type="applied_audit_failed"`.
- **Consumer scan** (`tools/scan_change_consumers.py`, seed `shared/tool_constants.py`): 18 direct script importers read the side-effect and tier sets, not `RETRYABLE_TOOLS`; `rg RETRYABLE_TOOLS scripts` finds only the definition, so the reference-set edit is `not affected` elsewhere. `GitHubConfig` consumers: `github_server.py` and the service mixins (targets).
- **Predictable fallout**: the GitHub test directory (UNK-04); generated reference artifacts are unaffected because no public API symbol of the Agent changes; tool inventory unchanged.

## Implementation steps
1. **Phase 1: Tests first (REQ-009)**
   - [ ] Write the classification, store-failure, audit-failure, timeout, no-retry, and client-construction tests, expecting failure (REQ-009; tests/mcp_servers/github/test_github_write_outcomes.py, tests/shared/test_write_outcome.py, tests/shared/test_tool_constants.py, tests/mcp_servers/github/test_github_tool_registry.py, tests/mcp_servers/github/test_github_config_strict_parsing.py, tests/mcp_servers/github/test_github_exception_handlers.py, tests/mcp_servers/github/test_github_mcp_service.py, tests/mcp_servers/github/test_service_dispatch.py)
   - [ ] Modify: characterization of the client built at import now covers the config-built client with timeouts and no retry (REQ-002; `tests/mcp_servers/github/test_service_init.py`) — amendment 2026-11-25
2. **Phase 2: Classification (REQ-001)**
   - [ ] Declare `never` for the nine writes and shrink the reference set (REQ-001; scripts/mcp_servers/github/tools_file.py, scripts/mcp_servers/github/tools_issues.py, scripts/mcp_servers/github/tools_pull_requests.py, scripts/mcp_servers/github/tools_repository.py, scripts/shared/tool_constants.py)
3. **Phase 3: Client, outcomes, and audit (REQ-002 to REQ-008)**
   - [ ] Shared vocabulary (REQ-007; scripts/shared/write_outcome.py)
   - [ ] Timeouts, no-retry client, typed errors, config (REQ-002, REQ-003; scripts/mcp_servers/github/github_models_config.py, scripts/mcp_servers/github/github_service_init.py, config/github_mcp_server.toml)
   - [ ] Intent and completion audit, ambiguous-failure translation, counter (REQ-003 to REQ-006; scripts/mcp_servers/github/github_service_security.py, scripts/mcp_servers/github/github_service_dispatch_writes.py, scripts/mcp_servers/github/github_service_file.py, scripts/mcp_servers/github/github_service_issues.py, scripts/mcp_servers/github/github_service_pull_requests.py, scripts/mcp_servers/github/github_service_repository.py)
   - [ ] Response mapping and health (REQ-003, REQ-005, REQ-008; scripts/mcp_servers/github/github_server.py, scripts/mcp_servers/github/exception_handlers.py)
4. **Phase 4: Documentation (REQ-010)**
   - [ ] docs/22_mcp/mcp_04_01_web-search-file-read-github.md, docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md, docs/22_mcp/mcp_06_01_configuration-file-inventory.md
5. **Phase 5: Deployment & Verification**
   - [ ] Run `uv run ruff format`, `uv run ruff check`, `uv run mypy`, and the full `uv run pytest`; hand off to `skills/deploy/SKILL.md` after commit and push (deploying is the user's decision); restart the GitHub server so the new config keys and client take effect (REQ-002; config/github_mcp_server.toml, scripts/mcp_servers/github/github_service_init.py)

### Release units
**Unit**: R1-github-write-safety | **Phases**: 2, 3 | **Reason**: removing the writes from `RETRYABLE_TOOLS` and declaring `never` must land with the audit and client changes, because the drift test, the registry tests, and the service tests assert the final combined behavior; Phase 1 tests are expected to fail until then.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/tool_constants.py and the tool tables | Unit | `uv run pytest tests/shared/test_tool_constants.py tests/mcp_servers/github/test_github_tool_registry.py` | No GitHub write retryable; drift check passes |
| scripts/shared/write_outcome.py | Unit | `uv run pytest tests/shared/test_write_outcome.py` | Vocabulary and field contract pass |
| GitHub client, audit, outcomes | Unit and contract | `uv run pytest tests/mcp_servers/github` | Store failure, audit failure, timeout, no-retry cases pass |
| config/github_mcp_server.toml | Unit | `uv run pytest tests/mcp_servers/github/test_github_config_strict_parsing.py` | Strict timeout parsing passes |
| All changed Python | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml` | Clean |
| Whole suite and coverage | Regression | `uv run pytest` and the diff-cover sequence in `rules/toolchain.md` | Green; changed lines at the Completion-checklist threshold |
| docs | Gates | the checkers in `rules/tool-gates.md` "When to run which tool" | No findings |

Validation quality baseline (Step 5): `radon cc` average complexity is A for every Python target (`github_service_security.py` 4.0, `github_service_dispatch_writes.py` 2.2, `github_models_config.py` 2.6, `github_server.py` 2.0, the four service files 1.1-2.0, `github_service_init.py` 1.0); the vulture and bandit baselines recorded earlier in this cycle on the same tree are unchanged for these modules; the diff-cover baseline is N/A in this document-only phase and is recorded at implementation.

## Risks
- **Risk**: Declaring the writes non-retryable removes the Agent replay of an interrupted GitHub write and the retryable fail-open behavior on a dedup-store failure, so a store outage now refuses GitHub writes → **Mitigation**: this is the intended fail-closed behavior (AC-2); the store outage is visible in the dedup health block; the Agent reports the refusal to the user.
- **Risk**: Disabling library retry makes reads fail fast on a transient 5xx or a rate-limit 403 → **Mitigation**: reads keep the Agent transport's safe read retry for 429, 502, 503, 504; a 403 already maps to a clear authorization error; the timeout defaults are configurable (UNK-03).
- **Risk**: Strict timeouts abort a slow but successful large `github_push_files` call and report `outcome_unknown` → **Mitigation**: `outcome_unknown` tells the user to verify on GitHub and never retries; the read timeout is configurable.
- **Risk**: An intent audit that fails blocks all writes when the audit path is unwritable → **Mitigation**: this is the required fail-closed behavior; the health check already reports `audit_log_writable`, and an empty `audit_log_path` keeps the documented skip.
- **Risk**: `github_server.py` conflicts with the context Plan → **Mitigation**: UNK-01 and the `Depends on` bullet.
- **Risk**: About 40 existing GitHub tests assume completion-only audit ordering → **Mitigation**: UNK-04 triage after Phase 3; fallout files added by amendment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | In Progress | — | — | Expected to fail until Phases 2-3 land |
| 2 | Phase 2: classification | In Progress | — | — | Release unit R1-github-write-safety |
| 3 | Phase 3: client, outcomes, and audit | In Progress | — | — | Release unit R1-github-write-safety |
| 4 | Phase 4: documentation | In Progress | — | — |  |
| 5 | Phase 5: deployment and verification | Pending | — | — | Deploy is the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261125-125134_01_scripts_shared_write_outcome.py.md | 1, 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_02_scripts_shared_tool_constants.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261125-125134_03_scripts_mcp_servers_github_tools_file.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-125134_04_scripts_mcp_servers_github_tools_issues.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-125134_05_scripts_mcp_servers_github_tools_pull_requests.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-125134_06_scripts_mcp_servers_github_tools_repository.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-125134_07_scripts_mcp_servers_github_github_models_config.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_08_scripts_mcp_servers_github_github_service_init.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_09_scripts_mcp_servers_github_github_service_security.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_10_scripts_mcp_servers_github_github_service_dispatch_writes.py.md | 1, 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_11_scripts_mcp_servers_github_github_service_file.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_12_scripts_mcp_servers_github_github_service_issues.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_13_scripts_mcp_servers_github_github_service_pull_requests.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_14_scripts_mcp_servers_github_github_service_repository.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_15_scripts_mcp_servers_github_github_server.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_16_scripts_mcp_servers_github_exception_handlers.py.md | 1, 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_17_config_github_mcp_server.toml.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-125134_20_tests_mcp_servers_github_test_github_tool_registry.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-125134_21_tests_mcp_servers_github_test_github_write_outcomes.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-125134_22_tests_mcp_servers_github_test_github_config_strict_parsing.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-125134_24_tests_mcp_servers_github_test_github_mcp_service.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-125134_26_docs_22_mcp_mcp_04_01_web-search-file-read-github.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261125-125134_27_docs_22_mcp_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261125-125134_28_docs_22_mcp_mcp_06_01_configuration-file-inventory.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261125-125134_29_tests_mcp_servers_github_test_service_init.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261125-124502
- **Related target files**: scripts/shared/write_outcome.py, scripts/shared/tool_constants.py, scripts/mcp_servers/github/tools_file.py, scripts/mcp_servers/github/tools_issues.py, scripts/mcp_servers/github/tools_pull_requests.py, scripts/mcp_servers/github/tools_repository.py, scripts/mcp_servers/github/github_models_config.py, scripts/mcp_servers/github/github_service_init.py, scripts/mcp_servers/github/github_service_security.py, scripts/mcp_servers/github/github_service_dispatch_writes.py, scripts/mcp_servers/github/github_service_file.py, scripts/mcp_servers/github/github_service_issues.py, scripts/mcp_servers/github/github_service_pull_requests.py, scripts/mcp_servers/github/github_service_repository.py, scripts/mcp_servers/github/github_server.py, scripts/mcp_servers/github/exception_handlers.py, config/github_mcp_server.toml, tests/shared/test_write_outcome.py, tests/shared/test_tool_constants.py, tests/mcp_servers/github/test_github_tool_registry.py, tests/mcp_servers/github/test_github_write_outcomes.py, tests/mcp_servers/github/test_github_config_strict_parsing.py, tests/mcp_servers/github/test_github_exception_handlers.py, tests/mcp_servers/github/test_github_mcp_service.py, tests/mcp_servers/github/test_service_dispatch.py, docs/22_mcp/mcp_04_01_web-search-file-read-github.md, docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md, docs/22_mcp/mcp_06_01_configuration-file-inventory.md, tests/mcp_servers/github/test_service_init.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (classify non-retryable); `tools_file.py` lines 90, 107, 123 | scripts/mcp_servers/github/tools_file.py | 2 | AC-1 | tests/mcp_servers/github/test_github_tool_registry.py | Confirmed by repository evidence |
| REQ-001 | Required Changes; `tools_issues.py` lines 118, 152 | scripts/mcp_servers/github/tools_issues.py | 2 | AC-1 | tests/mcp_servers/github/test_github_tool_registry.py | Confirmed by repository evidence |
| REQ-001 | Required Changes; `tools_pull_requests.py` lines 153, 169 | scripts/mcp_servers/github/tools_pull_requests.py | 2 | AC-1 | tests/mcp_servers/github/test_github_tool_registry.py | Confirmed by repository evidence |
| REQ-001 | Required Changes; `tools_repository.py` line 123 | scripts/mcp_servers/github/tools_repository.py | 2 | AC-1 | tests/mcp_servers/github/test_github_tool_registry.py | Confirmed by repository evidence |
| REQ-001 | Target Files (constants); `tool_constants.py` lines 184-217 | scripts/shared/tool_constants.py | 2 | AC-1 | tests/shared/test_tool_constants.py | Confirmed by repository evidence |
| REQ-002 | Required Changes (strict timeouts); PyGithub defaults | scripts/mcp_servers/github/github_models_config.py | 3 | AC-2 | tests/mcp_servers/github/test_github_config_strict_parsing.py | Derived from confirmed evidence |
| REQ-002 | Target Files (client initialization); `github_service_init.py` lines 22-24 | scripts/mcp_servers/github/github_service_init.py | 3 | AC-2 | tests/mcp_servers/github/test_github_write_outcomes.py | Confirmed by repository evidence |
| REQ-002 | Required Changes (timeouts) | config/github_mcp_server.toml | 3 | AC-2 | tests/mcp_servers/github/test_github_config_strict_parsing.py | Derived from confirmed evidence |
| REQ-003 | Required Changes (`outcome_unknown`); `_run_github` line 297 | scripts/mcp_servers/github/github_service_security.py | 3 | AC-3 | tests/mcp_servers/github/test_github_write_outcomes.py | Confirmed by repository evidence |
| REQ-003 | Required Changes (`outcome_unknown`) | scripts/mcp_servers/github/exception_handlers.py | 3 | AC-3 | tests/mcp_servers/github/test_github_exception_handlers.py | Explicit in issue |
| REQ-004 | Required Changes (intent audit fail closed); `_execute_with_dry_run` line 103 | scripts/mcp_servers/github/github_service_dispatch_writes.py | 3 | AC-2 | tests/mcp_servers/github/test_service_dispatch.py | Explicit in issue |
| REQ-004 | Required Changes (intent audit) | scripts/mcp_servers/github/github_service_security.py | 3 | AC-2 | tests/mcp_servers/github/test_github_mcp_service.py | Explicit in issue |
| REQ-005 | Required Changes (`applied_audit_failed`); audit calls at the cited lines | scripts/mcp_servers/github/github_service_file.py | 3 | AC-3, AC-4 | tests/mcp_servers/github/test_github_mcp_service.py | Confirmed by repository evidence |
| REQ-005 | Required Changes (`applied_audit_failed`) | scripts/mcp_servers/github/github_service_issues.py | 3 | AC-3, AC-4 | tests/mcp_servers/github/test_github_mcp_service.py | Confirmed by repository evidence |
| REQ-005 | Required Changes (`applied_audit_failed`) | scripts/mcp_servers/github/github_service_pull_requests.py | 3 | AC-3, AC-4 | tests/mcp_servers/github/test_github_mcp_service.py | Confirmed by repository evidence |
| REQ-005 | Required Changes (`applied_audit_failed`) | scripts/mcp_servers/github/github_service_repository.py | 3 | AC-3, AC-4 | tests/mcp_servers/github/test_github_mcp_service.py | Confirmed by repository evidence |
| REQ-005 | Required Changes (`applied_audit_failed`); `_handle_audit` bare 500 | scripts/mcp_servers/github/github_models_config.py | 3 | AC-3 | tests/mcp_servers/github/test_github_exception_handlers.py | Confirmed by repository evidence |
| REQ-005 | Required Changes (`applied_audit_failed`); `_dispatch_github_tool` line 193 | scripts/mcp_servers/github/github_server.py | 3 | AC-3, AC-4 | tests/mcp_servers/github/test_github_write_outcomes.py | Confirmed by repository evidence |
| REQ-006 | Required Changes (identifiers in every audit record); verification: none carried today | scripts/mcp_servers/github/github_service_security.py | 3 | AC-3 | tests/mcp_servers/github/test_github_write_outcomes.py | Confirmed by repository evidence |
| REQ-007 | Required Changes (shared write-outcome vocabulary and audit contract) | scripts/shared/write_outcome.py | 3 | AC-3 | tests/shared/test_write_outcome.py | Explicit in issue |
| REQ-008 | Required Changes (expose audit failures in health) | scripts/mcp_servers/github/github_server.py | 3 | AC-5 | tests/mcp_servers/github/test_github_write_outcomes.py | Explicit in issue |
| REQ-009 | Testing Expectations | tests/mcp_servers/github/test_github_write_outcomes.py | 1 | AC-2, AC-3, AC-4, AC-5 | itself | Explicit in issue |
| REQ-009 | Testing Expectations | tests/shared/test_write_outcome.py | 1 | AC-3 | itself | Explicit in issue |
| REQ-009 | Testing Expectations (classification consistency) | tests/shared/test_tool_constants.py | 1 | AC-1 | itself | Explicit in issue |
| REQ-009 | Testing Expectations (classification consistency) | tests/mcp_servers/github/test_github_tool_registry.py | 1 | AC-1 | itself | Explicit in issue |
| REQ-009 | Testing Expectations (timeouts) | tests/mcp_servers/github/test_github_config_strict_parsing.py | 1 | AC-2 | itself | Explicit in issue |
| REQ-009 | Testing Expectations (outcome-unknown) | tests/mcp_servers/github/test_github_exception_handlers.py | 1 | AC-3 | itself | Explicit in issue |
| REQ-009 | Testing Expectations (audit failure); tests at lines 202, 860 | tests/mcp_servers/github/test_github_mcp_service.py | 1 | AC-2, AC-3 | itself | Confirmed by repository evidence |
| REQ-009 | Testing Expectations (intent audit ordering) | tests/mcp_servers/github/test_service_dispatch.py | 1 | AC-2 | itself | Derived from confirmed evidence |
| REQ-010 | Documentation Impact | docs/22_mcp/mcp_04_01_web-search-file-read-github.md | 4 | AC-6 | docs gates | Explicit in issue |
| REQ-010 | Documentation Impact | docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md | 4 | AC-6 | docs gates | Explicit in issue |
| REQ-010 | Documentation Impact (configuration keys) | docs/22_mcp/mcp_06_01_configuration-file-inventory.md | 4 | AC-6 | docs gates | Derived from confirmed evidence |
| REQ-002 | Amendment 2026-11-25: The test pins the import-time Github() singleton (lines 31-63); the client moves to build_service(cfg) with explicit timeouts and retry=None | tests/mcp_servers/github/test_service_init.py | Phase 1 | AC-2 | itself | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261125-125134 -->
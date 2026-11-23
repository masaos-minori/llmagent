## Goal
- Make the shared MCP dispatcher act only on the atomic ownership ledger's typed acquisition result: one decision point per side-effecting call, a lease that stays alive while the handler runs, recovery of `interrupted` rows only where the tool's retry policy permits it, and tool results that name the state that caused a refusal, so exactly one caller executes a logical call at a time.

## Priority
High

## Scope
- **In-Scope**:
  - Removing the in-process duplicate-cache fast path from the durable-dedup path so `try_acquire_execution()` is the only decision point (its degraded-mode use stays).
  - Renewing the owner lease periodically **while** the handler executes, instead of one post-handler renewal.
  - Gating automatic recovery of `interrupted` ledger rows on the tool's declared retry policy.
  - Reporting the refusing state (`in_progress`, `interrupted`, `reconciliation_required`, `replay_unavailable`) in the tool result, with terminal evidence preserved and the handler never invoked.
  - Extracting the durable-dedup gate out of `scripts/mcp_servers/dispatch.py` so both modules stay inside the 24576 B module-size gate.
  - Dispatcher-level concurrency and lease tests, and the store-level gate tests.
- **Out-of-Scope**:
  - The ledger schema, ownership primitives, and store identity (completed by the mcpdl002 work); the logical call id, approval, and intent (completed by the mcpdl001 work).
  - Propagating the id and replay directives (mcpai004), dry-run and execution-context contract (mcpai005), GitHub-specific retry classification (mcpai006), Agent audit and transport DTO fields (mcpai007).
  - The final repository-wide MCP documentation sweep (mcpai012).
  - Any change to a persisted schema, `user_version`, or DDL, and any new `[dedup]` configuration key.
  - Any change to the dedup design document, the ADR, the governance exception entries, the skill definition files, or `scripts/shared/mcp_dedup_config.py` that the source Issue lists under Constraints — including their `reconciliation_required` and heartbeat wording, which the mcpai012 documentation sweep item aligns.
  - Writing or simulating a maintainer approval for the ADR-004 exceptions MCP-001 and MCP-002; their behavior is kept unchanged here.
- **Dependencies**: N/A: none. The predecessor work whose store primitives and state vocabulary this Plan consumes (mcpdl001, mcpdl002, mcpdl003) is implemented and archived. This Plan does not wait for the sibling call-state control API work (mcpdl004), whose Plan is archived and whose implementation has since landed on the remote branch (origin commits including `c339f82de`; its procedures are archived under `implementations/done/20261123-113815_*`), nor for the sibling retention-and-capacity Plan (mcpdl005), now archived in `plans/done/` with its procedures generated (`implementations/20261123-144326_*`) and awaiting execution; the file overlap with both is re-judged against the landed source in this cycle and recorded in Assumptions.

## Background
- The storage half of this backlog item (atomic acquisition, lease and attempt columns, immutable terminal evidence, attempt history, removal of the `force` path, store identity) was implemented by the mcpdl002 work (commit `4ee60e8cb`), and its configuration moved into the per-server `[dedup]` tables by the mcpdl003 work (commit `acefa30b5`). The mcpdl002 Plan explicitly carved "dispatcher integration beyond adopting the new store API (heartbeat task, structured tool results, dispatcher-level fail-closed rule redesign)" out as this item's scope.
- This item sits on the critical path `mcpdl001 -> mcpdl002 -> this item -> mcpai004 -> mcpai005 -> mcpai010 -> mcpai012`, and the GitHub, MDQ, and CI/CD items reuse the shared fail-closed rule defined here instead of redefining it.
- Related archived work: the MCP dedup store is classified as a disposable cache (Option B, `adrrev008`), and the retry-class classification was settled by `adrchk018`.

## Problem
Findings verified against the current source in Step 2; the Issue's three `Needs confirmation` claims are re-stated with their evidence outcome.

- **Lease protection is post-hoc, not concurrent.** `_renew_lease_if_needed()` is called after `await handler(args)` returns and returns early when the handler finished inside half the lease window. A handler that runs longer than `lease_seconds` (default 30 s) therefore loses its lease mid-execution while another caller can reconcile the row and take a new attempt. Verified (read of `scripts/mcp_servers/dispatch.py`, `dispatch_tool()` and `_renew_lease_if_needed()`).
- **`interrupted` rows bypass the retry-class policy.** `DedupLedger._acquire_locked()` reopens any `interrupted` row whose `attempt_number` is below the cap, moves it back to `pending`, and returns `acquired` — for retryable and non-retryable tools alike. A non-retryable side effect whose attempt was cancelled by `asyncio.CancelledError` (`mark_interrupted()`) is therefore auto-replayed. Verified (read of `scripts/shared/mcp_dedup_ledger.py`; no dispatcher-level test covers an `interrupted` row: `tests/mcp_servers/test_mcp_dispatch.py` has no such case, and `tests/shared/test_mcp_dedup.py::test_interrupted_row_survives_reopen` asserts the auto-reopen at store level).
- **The Issue's "two concurrent callers both execute" claim is not reproduced on the durable path.** Acquisition is one atomic `BEGIN IMMEDIATE` transaction guarded by the store's `threading.Lock`, and `tests/shared/test_mcp_dedup_concurrency.py::test_100_concurrent_callers_exactly_one_acquired` already proves it at store level; the in-process overlay is a completed-only fast path and cannot serialize in-flight calls. Residual duplicate-execution exposure exists only on the audited degraded path (store unavailable), which is the registered ADR-004 exception MCP-001 and is kept unchanged. Confirmed by Step 2/3 inspection.
- **The Issue's snapshot-mismatch / truncated-result claim is already implemented.** `completed` with a snapshot mismatch or a truncated payload, and `failed`, all return `replay_unavailable`; the dispatcher refuses them in every retry class with `error_type="dedup_unreplayable"` and never invokes the handler. Verified (`_acquire_locked()`, `_dedup_decision()`).
- **A second, weaker decision point remains in the dispatcher.** `dispatch_tool()` consults `_duplicate_cache` before the acquisition and writes `_idem_store()` after it, so in durable mode a call can be served or rejected by an in-process TTL cache instead of by the ledger. Verified; this is the last `lookup-plus-record` pattern in the production path.

## Reason for Change
- Duplicate execution of an external side effect is a correctness and data-integrity risk, and the states defined here are the contract the later MCP items (replay directive, execution context, GitHub retry policy, audit observability, control API) consume.
- The lease gap and the `interrupted` bypass are both live paths in code today, not hypothetical: one is a timing window, the other is a policy hole in a terminal state.
- No external deadline is known.

## Implementation Intent
- The dispatcher performs one acquisition per side-effecting call and acts only on its typed result. Active ownership is a renewable lease the dispatcher keeps alive for the duration of the handler.
- Retryability is a property of a known recovery procedure (the tool's declared retry policy), not of the transport, and it gates what the store is allowed to reopen.
- Control metadata (the state tag) stays separate from the human-readable output text.
- The store keeps no knowledge of tool retry policy: the dispatcher supplies the permission, the store enforces it. No DDL, no schema version change, no new configuration key.

## Requirements
- `REQ-001`: In durable-dedup mode the dispatcher's decision comes only from the typed acquisition result: `_duplicate_cache` is neither read nor written on the store-configured path, and it remains the cache for the audited degraded path only.
- `REQ-002`: Exactly one caller executes the handler for a new logical call when many async callers submit the same key through `dispatch_tool()`, proven at dispatcher level rather than only at store level.
- `REQ-003`: The owner renews its lease periodically while the handler runs (cadence derived from `lease_seconds`), and a lease lost during dispatch is reported as ownership loss and never re-dispatched.
- `REQ-004`: An `interrupted` ledger row is reopened only when the caller declares recovery permitted for that tool (the tool's retry policy is retryable); otherwise the acquisition refuses as `reconciliation_required` without mutating the row. Expired `pending` leases stay reconciliation-only, and `failed` rows stay never-reattempted.
- `REQ-005`: Refusals name the state that caused them in `dedup_state` (`in_progress`, `interrupted`, `reconciliation_required`, `replay_unavailable`) while `error_type` values stay stable, and no refusal mutates or re-executes the terminal row.
- `REQ-006`: The caller-supplied id contract is preserved: no content-derived key and no lookup-then-record sequence on any production path (verified current behavior, locked by tests).
- `REQ-007`: A non-retryable side-effecting tool fails closed when the durable store is unavailable, and a retryable tool keeps its current audited degraded behavior with a `store_error` marker; no maintainer approval is written for the ADR-004 exceptions.
- `REQ-008`: The decision logic is extracted into a dedicated gate module so `scripts/mcp_servers/dispatch.py` and the new module both stay under the 24576 B module-size gate and `dispatch_tool()` drops out of its current complexity grade.

## Implementation Target Files
**Freeze status**: Frozen (issue-to-plan Step 8's Implementation Target Files Validation
passed: `tools/audit_plan_target_paths.py` reported 0 findings and every row is `Verified`).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/dispatch.py | Modify: stop reading and writing the in-process overlay on the durable path, delegate the acquisition branch mapping to the new gate module, and run the lease heartbeat around `await handler(...)` | `dispatch_tool()` consults `_duplicate_cache` before `try_acquire_execution()` and calls `_idem_store()` after dispatch, and `_renew_lease_if_needed()` runs only after the handler returns | REQ-001, REQ-003, REQ-005, REQ-006, REQ-008; AC-1, AC-2, AC-5 | Step 2/3 read of `scripts/mcp_servers/dispatch.py`: `dispatch_tool()`, `_dedup_decision()`, `_renew_lease_if_needed()`, `_idem_store()`, `_duplicate_cache` | `tests/mcp_servers/test_mcp_dispatch_concurrency.py`, `tests/mcp_servers/test_mcp_dispatch.py` | Verified (checked in Step 2) |
| scripts/mcp_servers/dedup_gate.py | Create (New file): owns the durable-dedup gate — acquisition-result mapping, refusal constructors, degraded-mode cache helpers, the lease heartbeat, and the owner-nonce helper | `scripts/mcp_servers/dispatch.py` measures 24573 B against the 24576 B gate with no entry in `tools/check_module_size_baseline.txt`, and the Plan adds behavior to it | REQ-001, REQ-003, REQ-005, REQ-008; AC-7 | `wc -c scripts/mcp_servers/dispatch.py` = 24573; `uv run python tools/check_module_size.py --top 5` lists it second with 1 baselined module; `uv run radon cc scripts/mcp_servers/dispatch.py -s` reports `dispatch_tool` at cyclomatic 37 (checked in Step 5) | `tests/mcp_servers/test_mcp_dispatch_concurrency.py`, `tests/mcp_servers/test_mcp_dispatch.py` | Verified (checked in Step 3) |
| scripts/shared/mcp_dedup_ledger.py | Modify: add a keyword-only recovery-permission parameter (default `True`) to `try_acquire_execution()` and `_acquire_locked()` so an `interrupted` row is not reopened when recovery is not permitted, refusing as `reconciliation_required` | `_acquire_locked()` reopens every `interrupted` row below the attempt cap and returns `acquired`, so a cancelled non-retryable call is auto-replayed | REQ-004; AC-3, AC-4 | Step 2 read of `scripts/shared/mcp_dedup_ledger.py`: the `interrupted` branch of `_acquire_locked()` writes `status='pending'` and returns `acquired` | `tests/shared/test_mcp_dedup.py`, `tests/mcp_servers/test_mcp_dispatch.py` | Verified (checked in Step 2) |
| tests/mcp_servers/test_mcp_dispatch_concurrency.py | Create (New file): dispatcher-level concurrency and lease-protection tests | No `dispatch_tool`-level concurrency test exists; the only 100-caller test runs against the store API | REQ-002, REQ-003; AC-1, AC-2 | `grep -n "def test" tests/mcp_servers/test_mcp_dispatch.py` returns no concurrency case; `tests/shared/test_mcp_dedup_concurrency.py::test_100_concurrent_callers_exactly_one_acquired` and `test_multi_process_claim_race_exactly_one_winner` are store-level (checked in Step 3) | this file | Verified (checked in Step 3) |
| tests/mcp_servers/test_mcp_dispatch.py | Modify: replace the overlay fast-path assertions with durable-acquisition assertions, and add the `interrupted`-vs-`failed` policy matrix, expiry-boundary cases, and the refusal state tags | The `TestDispatchIdempotencyCache` cases import `_duplicate_cache` and assert its length, and `test_overlay_fast_path_still_hits` asserts the fast path that REQ-001 removes; `test_interrupted_non_retryable_refused` seeds an expired `pending` row, not an `interrupted` one | REQ-001, REQ-004, REQ-005, REQ-006, REQ-007; AC-1, AC-3, AC-5, AC-6 | Step 3 read of `tests/mcp_servers/test_mcp_dispatch.py` (re-checked this cycle): `from mcp_servers.dispatch import ... _duplicate_cache`, 7 `len(_duplicate_cache)` assertions, `test_overlay_fast_path_still_hits`, `TestDispatchIdempotencyCache`, `test_interrupted_non_retryable_refused`, `test_store_error_retryable_proceeds_non_retryable_fails_closed` | this file | Verified (checked in Step 3) |
| tests/shared/test_mcp_dedup.py | Modify: add store-level cases for the recovery-permission parameter (permitted reopen and refused reopen) | `test_interrupted_row_survives_reopen` asserts `acquired` with `attempt_number == 2` under the current unconditional reopen | REQ-004; AC-3 | Step 3 read of `tests/shared/test_mcp_dedup.py::test_interrupted_row_survives_reopen` and `test_expired_terminal_states_all_purged` | this file | Verified (checked in Step 3) |

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
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/shared/execution_snapshot.py | `build_execution_snapshot()` and `snapshots_equal()` are what the `replay_unavailable` refusal compares; `not affected: no change needed — the snapshot contract already drives the refusal the Issue asks for (Step 2 verification) | REQ-005 |
| scripts/shared/mcp_dedup.py | `DedupStore` subclasses `DedupLedger`, so the new keyword-only parameter is inherited with no facade change; `not affected: no re-export needed (checked in Step 3) | REQ-004 |
| scripts/shared/mcp_dedup_schema.py | `TERMINAL_STATES`, `ACQUISITION_STATES`, and the `status` CHECK constraint define the vocabulary this Plan must not extend | REQ-004, REQ-005 |
| scripts/shared/mcp_dedup_config.py | `lease_seconds` (default 30, validated range 1..3600) is the sole source of the heartbeat cadence; no new key is added | REQ-003 |
| scripts/shared/tool_metadata.py | `retry_policy_is_retryable()` is the policy the dispatcher passes as the recovery permission | REQ-004, REQ-007 |
| scripts/mcp_servers/models.py | `CallToolResponse.dedup_state` is a free-form string, so the new state tags need no model change; `not affected: no change needed (checked in Step 3) | REQ-005 |
| scripts/agent/tool_audit.py | Serializes `dedup_state` only when non-empty; the audit DTO extension is the mcpai007 item's scope; `not affected: no change needed (checked in Step 3) | REQ-005 |
| scripts/agent/tool_runner.py | `_logical_call_id()` supplies `X-Idempotency-Key` and states "Nothing is derived", confirming the caller-supplied id contract | REQ-006 |
| tests/mcp_servers/conftest.py | The autouse fixtures inject the store through `dispatch_mod.configure_dedup()` and clear `dispatch_mod._duplicate_cache`; `not affected: the moved cache helpers stay importable from `mcp_servers.dispatch` (D-1 compatibility impact) | REQ-001 |
| tests/mcp_servers/git/test_git_security_compliance.py | Its `_disable_dispatch_duplicate_cache` fixture disables the dispatcher's duplicate cache for the whole module; `not affected: same seam is preserved by the helper re-export (checked in Step 3) | REQ-001 |
| tests/shared/test_mcp_dedup_concurrency.py | Store-level race coverage (100 concurrent callers, multi-process claim, heartbeat blocking stale recovery, expired-lease reconcile-only) that the new dispatcher-level test must mirror rather than duplicate | REQ-002, REQ-003 |
| tests/integration/test_production_security_regression.py | Imports `DispatchResult` from `mcp_servers.dispatch`; `not affected: the public result type and `dispatch_tool` signature stay unchanged (Step 3 consumer scan candidate) | REQ-001, REQ-008 |
| scripts/mcp_servers/server.py | Bootstrap seam that calls `configure_dedup()` and `configure_tool_retry_policies()`; `not affected: the configure seam is unchanged (Step 3 consumer scan candidate) | REQ-007 |
| scripts/mcp_servers/git/git_server.py | Consumer of `DispatchResult` and `dispatch_tool`; `not affected: signatures unchanged (Step 3 consumer scan candidate) | REQ-001 |
| scripts/mcp_servers/github/github_server.py | Consumer of `DispatchResult`, `_to_call_tool_response`, `dispatch_tool`; `not affected: signatures unchanged (Step 3 consumer scan candidate) | REQ-001 |
| scripts/mcp_servers/mdq/mdq_server.py | Consumer of `DispatchResult`, `_to_call_tool_response`, `dispatch_tool`; `not affected: signatures unchanged (Step 3 consumer scan candidate) | REQ-001 |
| scripts/mcp_servers/cicd/cicd_server.py | Consumer of `dispatch_tool` and the retry-policy seam; `not affected: signatures unchanged (Step 3 consumer scan candidate) | REQ-001 |
| scripts/mcp_servers/file/read_server.py | Consumer of `DispatchResult`, `_to_call_tool_response`, `dispatch_tool`; `not affected: signatures unchanged (Step 3 consumer scan candidate) | REQ-001 |
| scripts/mcp_servers/file/write_server.py | Consumer of `DispatchResult`, `_to_call_tool_response`, `dispatch_tool`; `not affected: signatures unchanged (Step 3 consumer scan candidate) | REQ-001 |
| scripts/mcp_servers/file/delete_server.py | Consumer of `DispatchResult`, `_to_call_tool_response`, `dispatch_tool`; `not affected: signatures unchanged (Step 3 consumer scan candidate) | REQ-001 |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | Consumer of `DispatchResult`, `_to_call_tool_response`, `dispatch_tool`; `not affected: signatures unchanged (Step 3 consumer scan candidate) | REQ-001 |
| scripts/mcp_servers/shell/shell_server.py | Consumer of `DispatchResult`, `_to_call_tool_response`, `dispatch_tool` (importer added by the mcproute001 commit `de475540e`; found in this cycle's re-scan); `not affected: signatures unchanged | REQ-001 |
| scripts/mcp_servers/web_search/web_search_server.py | Consumer of `DispatchResult`, `_to_call_tool_response` (importer added by the mcproute001 commit `de475540e`; found in this cycle's re-scan); `not affected: signatures unchanged | REQ-001 |
| scripts/mcp_servers/web_search/formatters.py | Consumer of `DispatchResult`, `ToolArgs`, `dispatch_tool` (importer added by the mcproute001 commit `de475540e`; found in this cycle's re-scan); `not affected: signatures unchanged | REQ-001 |
| docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md | Registers exceptions MCP-001 (retryable fail-open) and MCP-002 (post-open warning-only); must be read and its behavior preserved; `not affected: no approval is written and no exception is retired by this Plan | REQ-007 |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Holds the open MCP-001 and MCP-002 entries (both `Status: open`, `Type: missing-documentation`) whose maintainer decision is unresolved; `not affected: the decision is the maintainer's | REQ-007 |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | Classifies the dedup store and its disposable-cache status; read to confirm no conflict with the recovery gate (no ADR change is proposed) | REQ-004, REQ-007 |
| docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | The dedup design document defines the store DDL, the `reconcile_execution()` state transition, and the acquisition vocabulary this Plan consumes, and its `reconciliation_required` and heartbeat sentences are the two descriptions the new behavior widens | REQ-003, REQ-004, REQ-005; `not affected: the source Issue's Constraints list this document as a file this item must not change, and the wording refresh belongs to the mcpai012 documentation sweep item (checked in Step 3) |
| rules/persisted-schema-change.md | Checklist that this Plan records as not applicable: no DDL, no schema version, no migration (see Design) | REQ-004, REQ-008 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002, REQ-006): One key submitted by 100 concurrent async callers through `dispatch_tool()` executes the handler exactly once, and no call on the durable path is served or rejected by the in-process overlay.
- AC-2 (REQ-003): A handler whose duration exceeds `lease_seconds` still owns its row at finalization (renewal observed during execution), and boundary calls immediately before and immediately after a lease expiry behave per policy.
- AC-3 (REQ-004, REQ-005): Only an expired `pending` lease or a policy-refused `interrupted` row enters the reconciliation path; `failed` rows never re-attempt; each refusal carries its state tag and leaves the row unmutated.
- AC-4 (REQ-003, REQ-004): Completion and finalization stay owner-conditional, and a zero-row finalization is reported as ownership loss (`lease_conflict`) and never re-dispatched.
- AC-5 (REQ-005): A snapshot mismatch or a truncated stored result refuses with `dedup_unreplayable` / `replay_unavailable` and does not invoke the handler, with the terminal row preserved.
- AC-6 (REQ-007): A non-retryable side-effecting tool is refused when the durable store is unavailable, and a retryable tool keeps its current degraded `store_error` behavior; no approval statement is added to any document.
- AC-7 (REQ-008): `uv run python tools/check_module_size.py` reports no new violation, and `dispatch_tool()`'s radon grade improves from `E` (37).

## Tests
- T-1 (REQ-002, AC-1): `tests/mcp_servers/test_mcp_dispatch_concurrency.py` — one key, 100 concurrent `dispatch_tool()` callers, exactly one handler execution; the other 99 results report `in_progress` or `duplicate_hit` and never call the handler. Written first and run against the unmodified dispatcher, per the Issue's implementation instruction.
- T-2 (REQ-003, AC-2): `tests/mcp_servers/test_mcp_dispatch_concurrency.py` — a handler that outlives half the lease window is still owned at finalization (renewal observed during execution); a handler that outlives the whole lease while renewals are blocked reports ownership loss and does not re-dispatch.
- T-3 (REQ-004, AC-3): `tests/shared/test_mcp_dedup.py` — `interrupted` row with recovery permitted reopens as `acquired` with the next attempt number (existing default behavior preserved), and with recovery not permitted returns `reconciliation_required` and leaves the row `interrupted`.
- T-4 (REQ-004, REQ-005, AC-3): `tests/mcp_servers/test_mcp_dispatch.py` — policy matrix for a non-retryable tool against an `interrupted` row: refusal, `error_type="dedup_unreplayable"`, `dedup_state="interrupted"`, handler not executed, row unchanged; the retryable counterpart reacquires once.
- T-5 (REQ-005, AC-5): `tests/mcp_servers/test_mcp_dispatch.py` — snapshot-mismatch and truncated-result cases refuse with the preserved terminal evidence and never re-execute; boundary tests immediately before and after lease expiry.
- T-6 (REQ-001, REQ-006, AC-1): `tests/mcp_servers/test_mcp_dispatch.py` — durable-mode calls never populate or consult `_duplicate_cache`; the degraded path still does; the reused-key-with-different-content rejection comes from `contract_mismatch` rather than the cache.
- T-7 (REQ-007, AC-6): `tests/mcp_servers/test_mcp_dispatch.py` — store-unavailable cases for retryable and non-retryable tools keep their current outcomes (`store_error` degraded dispatch, `dedup_store_error` refusal).
- T-8 (REQ-008, AC-7): `uv run python tools/check_module_size.py` and `uv run radon cc scripts/mcp_servers/dispatch.py -s` as the module-shape check, plus the full validation sequence below.

## Documentation Impact
No document is a modification target of this Plan. The source Issue's Constraints list the dedup
design document in the DB domain (`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`), the
ADR, the governance exception entries, and the skill definition files as files this item must not
change, and the repository-wide MCP documentation sweep belongs to the mcpai012 item. Reaching them
through `docs/00_index.md`'s "Document References by Task" rows for the MCP dedup store
(`22_mcp/mcp_00_document-guide.md`, `22_mcp/mcp_01_system_overview.md`, and the DB-domain dedup
document), the MCP server spec, and the MCP design docs backlog row, two behavior facts changed
here are recorded for that sweep to align: `reconciliation_required` also covers a recovery the
dispatcher's policy refuses on an `interrupted` row, and the dispatcher renews the lease while the
handler runs (REQ-003, REQ-004, REQ-005). ADR-004's MCP-001 and MCP-002 entries and the
governance-03 rows for them are deliberately left untouched: they record a maintainer decision that
has not been made (REQ-007), and no approval is written by this Plan.

## Assumptions
- The degraded path (durable store unavailable) keeps its current audited behavior byte-for-byte: retryable tools proceed with a `store_error` marker, non-retryable tools fail closed, and a failed post-open store write stays warning-only. No approval is written for MCP-001 or MCP-002.
- The overlap with the sibling call-state control API work (mcpdl004) is **compatible**, not a conflict. Its Plan is archived and its implementation has landed (`implementations/done/20261123-113815_*.md` procedures, origin commits including `c339f82de`), and its ledger-side half added result-metadata columns, a read-only `call_state_view()`, a `_USER_VERSION` bump (now `2` in `scripts/shared/mcp_dedup_schema.py`, re-checked this cycle), and a two-column fixture fix in `tests/mcp_servers/test_mcp_dispatch.py`, while this Plan adds one keyword-only acquisition parameter and dispatcher behavior. Its own rows never edit `scripts/mcp_servers/dispatch.py` (it lists that file as a reference with `not affected`). The two changes meet only in `scripts/shared/mcp_dedup_ledger.py` and `tests/shared/test_mcp_dedup.py`, in different functions (the landed `record_completed()`/`call_state_view()` and DDL pins there, `try_acquire_execution()` and `_acquire_locked()` and the `interrupted`-reopen cases here — the acquisition signature was re-read this cycle and is unchanged by the landed mcpdl004 work). Either landing order works; the implementation phase re-reads the ledger's acquisition signature before editing it. No ordering dependency on it is recorded in `Scope`.
- The overlap with the sibling retention-and-capacity Plan (mcpdl005) is **compatible** too: it is now archived in `plans/done/` with its procedures generated (`implementations/20261123-144326_*`, awaiting execution); its `scripts/shared/mcp_dedup_ledger.py` procedure changes `purge_expired()` and its `tests/shared/test_mcp_dedup.py` procedure extends the `TestTtlPurge` retention cases, neither of which touches the acquisition path or the `interrupted`-reopen cases this Plan adds. It owns the new `[dedup]` threshold keys in `scripts/shared/mcp_dedup_config.py`, which this Plan deliberately does not touch.
- `interrupted` rows below the attempt cap stay re-openable for callers that do not pass the new parameter (default `True`), so no existing store caller or test changes behavior.
- The dedup store stays a disposable cache (ADR-008, `adrrev008` Option B): `/opt/llm/db/mcp_dedup.sqlite` does not exist on this host, so there is no live row to migrate and no recreation to schedule for this change.
- The heartbeat cadence is derived from the already-validated per-server `lease_seconds` value; no new configuration key is introduced.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Issue claim that the dispatcher does not already serialize acquisition in-process | None: the claim is answered by repository evidence | Resolved in Step 2/3: `try_acquire_execution()` is one `BEGIN IMMEDIATE` transaction under the store's `threading.Lock`, and `tests/shared/test_mcp_dedup_concurrency.py::test_100_concurrent_callers_exactly_one_acquired` proves it; the residual exposure is only the degraded path, which the ADR-004 exception covers. T-1 confirms it at dispatcher level | False |
| UNK-02 | Issue claim that a retryable classification handles fresh pending, interrupted, and failed states too similarly | None: confirmed as a real gap | Resolved in Step 2 and turned into REQ-004: `_acquire_locked()` reopens `interrupted` rows for every retry class; expired `pending` stays reconciliation-only and `failed` stays terminal | False |
| UNK-03 | Heartbeat interval and lease duration values (the Issue's `不明`) | Operational measurement of the longest handler duration per MCP server | Cadence fixed at `lease_seconds / 2` from the validated per-server config (default 30 s, range 1..3600 in `scripts/shared/mcp_dedup_config.py`); per-server tuning is an operational decision taken at deploy time through the existing key, and the document that describes it is excluded from this item by the Issue's Constraints | False |
| UNK-04 | Final state vocabulary: the Issue's `review_required` label versus the implemented `replay_unavailable`, and how `interrupted` is named for callers (the Issue's `不明`, decided together with mcpdl004 and mcpdl006) | None: the shared contract module now exists (`scripts/shared/mcp_call_state_contract.py` landed with the mcpdl004 implementation, re-checked this cycle; `_USER_VERSION` is `2`) | This Plan keeps the implemented vocabulary (`replay_unavailable` already means "snapshot mismatch, truncated payload, or failed terminal row") and adds only the `interrupted` state tag; the landed contract's `agent_state_for()` already maps `interrupted -> reconciliation_required`, consistent with REQ-004's refusal tag; naming unification stays the mcpdl004 work's and the two-layer failure-verification item's decision | False |
| UNK-05 | Whether the maintainer approves or removes ADR-004 exceptions MCP-001 and MCP-002 (the Issue's `不明`); removal would change the dispatcher rule defined here | A maintainer decision, not repository evidence | Governance decision recorded in the ADR-004 `### Approval Record` and the governance-03 entries (both still `Status: open`). This Plan preserves the behavior and writes no approval | False |
| UNK-06 | The sibling retention-and-capacity Plan (mcpdl005) and the in-progress call-state control API implementation (mcpdl004) touch the same shared ledger file and the same shared test files as this Plan | Which of them changes `scripts/shared/mcp_dedup_ledger.py` first, and whether the acquisition signature is still the one this Plan's rows describe at implementation start | Resolved this cycle: the mcpdl004 half landed first (its ledger changes are in `scripts/shared/mcp_dedup_ledger.py`), the mcpdl005 procedures are generated but not yet executed, and `try_acquire_execution()`/`_acquire_locked()` were re-read — the signature is still the one this Plan's rows describe. `tools/check_plan_target_overlaps.py` and `tools/plan_dependency_order.py` reported the overlaps; each side's changed function was judged compatible in Assumptions (purge and metadata there, acquisition here). The implementation phase still re-reads `try_acquire_execution()` before editing it. This Plan waits for neither | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/dispatch.py | Modify | High: 17 modules import it (8 MCP server endpoints, the server bootstrap seam, and 8 test modules) | 8 commits | High: 99.9% of the last 180 days' lines are one author under two name spellings (`uv run git-fame --since 180.days --incl "scripts/mcp_servers/dispatch.py" .`) | not applicable (rsynced) |
| scripts/mcp_servers/dedup_gate.py | Create | Medium: imported by `scripts/mcp_servers/dispatch.py` only | N/A: new file | N/A: new file | not applicable (rsynced) |
| scripts/shared/mcp_dedup_ledger.py | Modify | Medium: the store API used by every MCP server process through the `shared.mcp_dedup` facade | 1 commit | High: single-author module | not applicable (rsynced) |
| tests/mcp_servers/test_mcp_dispatch_concurrency.py | Create | Low | N/A: new file | N/A: new file | not applicable (rsynced) |
| tests/mcp_servers/test_mcp_dispatch.py | Modify | Low: test-only, but it pins the dispatcher's current seams | 8 commits | High: single-author module | not applicable (rsynced) |
| tests/shared/test_mcp_dedup.py | Modify | Low: test-only; it pins the store DDL and vocabulary | 9 commits | High: single-author module | not applicable (rsynced) |

## Design

### Path B analysis record

Architecture analysis (Step 3, Step 5):
- `rg "^from|^import" scripts/mcp_servers/dispatch.py | sort -u`: the dispatcher depends on `mcp_servers.models` (`CallToolResponse`) and on the shared leaf (`shared.execution_snapshot.build_execution_snapshot`, the `shared.mcp_dedup` facade, `shared.tool_constants.ALL_SIDE_EFFECTING_TOOLS`, `shared.tool_metadata.retry_policy_is_retryable`) plus stdlib `asyncio`, `collections.OrderedDict`, `hashlib.sha256`, `json`, `logging`, `secrets`, `sqlite3`, `time`. No `agent` import.
- `uv run lint-imports`: 527 files, 3272 dependencies, `Contracts: 6 kept, 0 broken` — including `shared must not import from agent, mcp_servers, rag, or db` and `mcp_servers must not import from agent`. The new gate module therefore stays inside `scripts/mcp_servers/` and may import only `shared/`; placing the gate in `shared/` was rejected (see D-1).
- `DedupStore` subclasses `DedupLedger` in `scripts/shared/mcp_dedup.py`, so the new keyword-only parameter is inherited and no facade re-export is needed.

Dependency graphing (Step 3, Step 5):
- `rg "from mcp_servers.dispatch import|import mcp_servers.dispatch" scripts/ tests/` and `tools/scan_change_consumers.py` give the same candidate set, re-counted this cycle as 20 importing modules: the eight MCP server endpoint modules (`cicd`, `file` read/write/delete, `git`, `github`, `mdq`, `rag_pipeline`), the `scripts/mcp_servers/server.py` bootstrap seam (`configure_dedup`, `configure_tool_retry_policies`), eight test modules, and three modules added since Plan generation by the mcproute001 commit `de475540e` — `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/web_search/web_search_server.py`, and `scripts/mcp_servers/web_search/formatters.py`. Every one of them uses only `dispatch_tool`, `DispatchResult`, `_to_call_tool_response`, `ToolArgs`, `configure_dedup`, or `configure_tool_retry_policies`, all of which keep their signatures; each is recorded as a `Reference Files` row with `not affected`.
- `dedup_state` has exactly two readers outside the dispatcher: `scripts/mcp_servers/models.py` (`CallToolResponse.dedup_state`, a free-form `str`) and `scripts/agent/tool_audit.py` (serialized only when non-empty). Neither constrains the value set, so the new state tags need no model change; `scripts/scan_change_consumers.py --seed dedup_state` returned no candidate.
- Key supply is Agent-side and non-derived: `scripts/agent/tool_runner.py` `_logical_call_id()` feeds `X-Idempotency-Key` and its docstring states "Nothing is derived — the old key derivations collided". Content-derived keys no longer exist in either layer; `sha256` in the dispatcher is used only for the `args_hash` mismatch check.
- Symbol seeds that returned no consumer outside `scripts/mcp_servers/dispatch.py`: `_dedup_decision`, `_store_op`, `_renew_lease_if_needed`, `_new_owner_id`, `_idem_evict`, `_CacheEntry`, `_IDEMPOTENCY_CACHE_TTL_SECONDS`, `_IDEMPOTENCY_CACHE_MAX_ENTRIES`, `dedup_state`.
- Tool availability: `grimp`, `pydeps`, `radon`, `vulture`, `bandit`, `diff-cover`, `git-fame`, `import-linter` are installed; `universal-ctags` and a standalone `lint-imports` binary are not (`lint-imports` runs through `uv run`). `grimp` was exercised through the repository's own consumer scanner (`tools/scan_change_consumers.py`); `pydeps` was not run because the graph question was answered by the rg-based scan and the consumer scan.

Historical analysis (Step 5):
- `git log --name-only --pretty=format: --since=30.days -- scripts/ | sed '/^$/d' | sort | uniq -c | sort -rn | head -20`: `scripts/mcp_servers/dispatch.py` is not in the top 20 (its own count is 8 commits in 30 days); `scripts/shared/mcp_dedup.py` is 10, and `scripts/mcp_servers/server.py` is 11. Test churn is higher than source churn here: `tests/shared/test_mcp_dedup.py` 9, `tests/mcp_servers/test_mcp_dispatch.py` 8.
- Recent commits on the dispatcher: `4ee60e8cb` (mcpdl002 store rewrite plus dispatch acquisition), `acefa30b5` (mcpdl003 config isolation), `83879685e` (`adrrev008` fail-closed on a lost or recreated store). The dispatcher's current shape is two releases old, so the Issue's Problem/Evidence section is largely stale and this Plan's Problem section is the corrected one.
- Bus factor: `uv run git-fame --since 180.days --incl "scripts/mcp_servers/dispatch.py" .` attributes 99.9% of the module to a single author under two name spellings — flagged as high bus factor.

Operational dependency inspection (Step 5):
- `ss -ltnp`: no MCP server port is listening on this host (only `opencode`, SSH/SMB, and one unrelated high port), so no live MCP dispatcher process is affected by the change.
- Database lock check: `/opt/llm/db/mcp_dedup.sqlite` does not exist (the store has never been created on this host; `/opt/llm/db/` holds `eventbus.sqlite`, `mdq.sqlite`, `rag.sqlite`, `session.sqlite`, `workflow.sqlite`). `fuser` is not installed, so the lock check is recorded as **not run**; the file's absence is the evidence that there is no live store to guard or migrate.
- `pip-audit`: not run — no dependency addition or upgrade is planned by this Plan.

Consumer scan (Step 3): `uv run python tools/scan_change_consumers.py --seed <symbol>` was run for `_duplicate_cache`, `_idem_now`, `_is_side_effecting`, `DispatchResult`, `dispatch_tool`, `configure_dedup`, `_dedup_decision`, `_store_op`, `_finalize_dedup`, and `dedup_state`. Each seed with hits reported the same 17-module `patch-or-import` candidate inventory of `mcp_servers.dispatch` importers plus `adr-test-citation` candidates from `docs/10_adr/` test citations (documentation citations, not call sites); `_finalize_dedup` and `dedup_state` returned no candidate. Every candidate is recorded above as a target row, a `Reference Files` row with `not affected: {reason}`, or an ADR citation. The scanner reported `Testmon: used (.testmondata is 4.0 days old)`, so the implementation phase MUST delete `.testmondata` before relying on a test run's coverage (see Validation plan).

Predictable fallout check (Step 3):
- Module size: `wc -c scripts/mcp_servers/dispatch.py` = 24573 B against the 24576 B gate, and `uv run python tools/check_module_size.py --top 5` shows only one baselined module (`rag/ingestion/chunk_splitter.py`), so `dispatch.py` has 3 B of headroom and no baseline allowance. This Plan adds behavior to that file, so the extracted module row (`scripts/mcp_servers/dedup_gate.py`) is the split row this check requires. `scripts/shared/mcp_dedup_ledger.py` measures 23155 B after the landed mcpdl004 work (re-measured this cycle; it was 19160 B at Plan generation) — still under the 24576 B gate with no baseline entry, with room for the keyword-only parameter.
- Pinned counts: `grep -rn "review_required\|record_pending\|_duplicate_cache" tests/` finds no test that pins a count of dedup states or ADR nodes; the `review_required` hits are GitHub's unrelated `server.pr_review_required` health status. The length assertions on `len(_duplicate_cache)` inside `tests/mcp_servers/test_mcp_dispatch.py` are the pinned assertions and are a target row.
- Tool inventory: no `tools/*.py` is added or removed, so `tools/TOOL_DESCRIPTIONS.md` and `check_tool_descriptions_sync.py` are `not affected`.
- Generated blocks: no table, column, or registry entry changes, so `tools/generate_reference_table.py --check` and `tools/check_db_separation.py` are `not affected`; the drift test stays green because the DDL is untouched.

Persisted schema check: not applicable. No DDL, no `user_version` change, no migration, and no new persisted column is introduced by this Plan (`rules/persisted-schema-change.md` items therefore do not bind). The only persisted-state effect is a policy decision taken at acquisition time, and the store remains a disposable cache per ADR-008 (`adrrev008` Option B). The schema-shape change and version bump belonging to this store are owned by the mcpdl004 work, which has since landed: `_USER_VERSION` is `2` in `scripts/shared/mcp_dedup_schema.py` and `scripts/shared/mcp_call_state_contract.py` exists (re-checked this cycle); this Plan adds no DDL, version change, or migration on top of that.

Validation quality analysis baseline (Step 5, run before writing this Plan):
- `uv run radon cc scripts/mcp_servers/dispatch.py -s`: `dispatch_tool` cyclomatic complexity 37 (grade `E`), `_dedup_decision` 10 (`B`), `_idem_evict` 5 (`A`), `_renew_lease_if_needed` 4 (`A`), `_dedup_context` 4 (`A`); every other function `A`. The module-shape decision D-1 is grounded in `dispatch_tool`'s grade.
- `uv run vulture scripts/ --min-confidence 80`: exit 3 (unused code found); no finding names `dispatch.py` or a dedup module. The 16 findings are unrelated pre-existing items (for example an unused variable in `scripts/rag/ingestion/document_manager.py` and one in `scripts/shared/runtime_paths.py`) and are out of scope for this Plan.
- `uv run bandit -r scripts/ -c pyproject.toml -q`: 47 Low-severity findings, 0 Medium and 0 High severity, all `B101 assert_used`; no finding in `scripts/mcp_servers/dispatch.py` or the shared dedup modules. Baseline: no medium/high severity finding to fix.
- Diff-scoped coverage baseline (`rules/toolchain.md` section 7, run without `--fail-under`): `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"` then `uv run coverage xml` then `uv run diff-cover coverage.xml --compare-branch=master` reported "No lines with coverage information in this diff" — the working tree is identical to `master`, so the baseline number is 0 diff lines and the threshold to reach during implementation is `--fail-under=90` on the implementation diff.

### Design decisions

D-1: Extract the durable-dedup gate into `scripts/mcp_servers/dedup_gate.py`.
- **Decision**: move the acquisition-result mapping, refusal constructors, degraded-mode cache helpers, the owner-nonce helper, and the heartbeat out of `scripts/mcp_servers/dispatch.py`; move the `DispatchResult` and `ToolArgs` definitions into the gate module (the refusal constructors there build `DispatchResult` at runtime, and importing the class back from `dispatch.py` from the gate would be a circular import — corrected in this cycle's Step 3a, which found this Plan's original wording kept `DispatchResult` in `dispatch.py` while assigning the refusal constructors to the gate); keep `dispatch_tool`, `_to_call_tool_response`, `configure_dedup`, and `configure_tool_retry_policies` in `dispatch.py`, and re-export the moved helpers and result types from it so the existing test seams (`tests/mcp_servers/conftest.py`, `tests/mcp_servers/git/test_git_security_compliance.py`, `tests/mcp_servers/test_mcp_dispatch.py`) and every consumer keep importing the same names from `mcp_servers.dispatch`.
- **Alternatives considered**: keep everything in `dispatch.py` — rejected, 3 B of headroom under a hard gate with no baseline entry, and `dispatch_tool` already grades `E (37)`; move the gate to `scripts/shared/` — rejected, the gate needs `mcp_servers.models` and the dispatcher's retry-policy knowledge, and the `shared-is-leaf` contract forbids importing `mcp_servers` from `shared`.
- **Compatibility impact**: no consumer-visible change; all 17 importing modules keep their imports, and the private helpers stay importable from `mcp_servers.dispatch`.
- **Reversibility**: high — revert the extraction commit restores the previous single-module layout with no data or config change.

D-2: Keep the in-process cache for the degraded path only; remove it from the durable path.
- **Decision**: `_duplicate_cache` is no longer read or written when the durable store is configured; it remains the cache when the store is unavailable or a store write failed, which is the behavior ADR-004 MCP-001 describes.
- **Alternatives considered**: remove the cache entirely — rejected, it would change the registered exception's behavior (a retryable tool in degraded mode currently serves a duplicate from the cache) and the Issue forbids changing it here; keep the cache on the durable path — rejected, it is a second decision point that can serve a result the ledger would not serve (after a purge or a store replacement) and is the remaining `lookup-plus-record` sequence.
- **Compatibility impact**: a durable-mode duplicate hit is now decided by the store every time, so `dedup_state="duplicate_hit"` comes from `replay_completed` instead of from the cache; `contract_mismatch` becomes the single source of the reused-key rejection. `DispatchResult` and `CallToolResponse` shapes are unchanged.
- **Reversibility**: high — the fast path is one read block plus two call sites.

D-3: Renew the lease during handler execution at `lease_seconds / 2`, with no new configuration key.
- **Decision**: an asyncio renewal task runs while `await handler(args)` is in flight, renews every `lease_seconds / 2` while the lease is live, and stops when the handler finishes; a failed or conflicting renewal is recorded so finalization reports ownership loss instead of a silent overwrite, and never re-dispatches.
- **Alternatives considered**: the current single post-handler renewal — rejected, it cannot protect a handler longer than the lease (the defect T-2 confirms); a new `[dedup] heartbeat_interval_seconds` key — rejected, it would touch the validator in `scripts/shared/mcp_dedup_config.py` and the ten per-server `[dedup]` tables, and `lease_seconds` (default 30, validated 1..3600) already bounds the cadence; a `threading.Timer` — rejected, it puts store writes on a second thread outside the event loop while the existing writes are short `BEGIN IMMEDIATE` transactions guarded by the store's `threading.Lock`.
- **Compatibility impact**: up to two additional short store writes per long call; `PRAGMA busy_timeout` (default 5000 ms) and the existing lock absorb them. No signature or config change.
- **Reversibility**: high — remove the renewal task and the previous post-handler call stays functional.

D-4: Gate `interrupted` recovery with a keyword-only permission parameter on the acquisition.
- **Decision**: `try_acquire_execution(..., allow_interrupted_recovery=True)`; the dispatcher passes the tool's `retry_policy_is_retryable()` result. When recovery is not permitted, the acquisition returns the existing `reconciliation_required` status and does not mutate the row.
- **Alternatives considered**: have the dispatcher read the row with `get_execution()` before deciding — rejected, it re-introduces a lookup before the decision, which REQ-001 removes; add a new acquisition status such as `recovery_not_permitted` — rejected, it extends the acquisition vocabulary the sibling call-state control API Plan must map in its MCP-state to Agent-state table, and `reconciliation_required` already means "needs reconciliation, no owner granted"; teach the store the retry classes — rejected, the store is deliberately tool-policy-agnostic.
- **Compatibility impact**: additive and default-preserving; the existing store tests (`test_interrupted_row_survives_reopen`, `test_expired_terminal_states_all_purged`) and every current caller keep their behavior. Only `scripts/mcp_servers/dispatch.py` opts in.
- **Reversibility**: high — the parameter and its branch are one commit; no data change.

D-5: Report the refusing state in `dedup_state`, keep `error_type` values stable.
- **Decision**: refusals name their state in the existing free-form `dedup_state` tag (`in_progress`, `interrupted`, `reconciliation_required`, `replay_unavailable`), and the Issue's `review_required` case stays expressed by the implemented `replay_unavailable` / `dedup_unreplayable` pair rather than a new label.
- **Alternatives considered**: a new `error_type` value `dedup_review_required` — rejected, transport consumers and the later replay-directive and observability items key on `error_type`, and the naming is UNK-04's open decision; a separate control-metadata field on `DispatchResult` — rejected, the DTO extension is the mcpai007 item's scope.
- **Compatibility impact**: `CallToolResponse.dedup_state` is an unconstrained `str`, and `scripts/agent/tool_audit.py` serializes it only when non-empty, so a new tag value is additive. No response schema change.
- **Reversibility**: high.

D-6: No vocabulary, schema, or configuration extension in this Plan.
- **Decision**: keep the ledger states (`pending`, `completed`, `failed`, `interrupted`) and the acquisition vocabulary exactly as the mcpdl002 work shipped them.
- **Alternatives considered**: add a `review_required` ledger state — rejected, it changes the `status` CHECK constraint in `scripts/shared/mcp_dedup_schema.py`, bumps `_USER_VERSION`, and forces store recreation, which is the mcpdl004 work's decision (UNK-04).
- **Compatibility impact**: none; the store's identity classification and installation marker stay valid, so no re-initialization is planned.
- **Reversibility**: N/A: nothing to revert.

Phase list, per-phase verification, and rollback (applied narrowly from `skills/python-design/workflow.md` Steps 8a-8d to the phases below): Phase 1 and Phase 2 depend on nothing; Phase 3 depends on nothing (a pure move); Phase 4, Phase 5 and Phase 6 depend on Phase 3, and Phase 6 also depends on Phase 2; Phase 7 depends on Phases 4-6; Phase 8 depends on all of them. Each phase is verifiable by the named test command in the Validation plan, except the members of the `dispatcher-decision-change` unit (Phases 1, 4, 5, 6, 7), which are validated together. Each phase reverts by reverting its commit; no phase has a data-migration rollback risk because no persisted schema changes.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Confirm the defects with failing-at-first dispatcher tests** (member of the `dispatcher-decision-change` unit)
   - [ ] Write the 100-concurrent-caller exactly-once test and the lease-outlives-the-handler test against the unmodified dispatcher, and record which of them fail, per the Issue's implementation instruction (REQ-002, REQ-003; `tests/mcp_servers/test_mcp_dispatch_concurrency.py`)
   - [ ] Keep the tests on the `dispatch_tool()` seam only, mirroring rather than duplicating the store-level races already covered in `tests/shared/test_mcp_dedup_concurrency.py` (REQ-002; `tests/mcp_servers/test_mcp_dispatch_concurrency.py`)
2. **Phase 2: Store-side recovery permission**
   - [ ] Add the keyword-only `allow_interrupted_recovery` parameter (default `True`) to `try_acquire_execution()` and `_acquire_locked()`, returning `reconciliation_required` without mutation when it is `False` (REQ-004; `scripts/shared/mcp_dedup_ledger.py`)
   - [ ] Add the permitted-and-refused store-level cases, keeping the existing reopen case green (REQ-004; `tests/shared/test_mcp_dedup.py`)
3. **Phase 3: Extract the gate module without changing behavior**
   - [ ] Create the gate module holding the acquisition-branch mapping, refusal constructors, degraded-mode cache helpers, the owner-nonce helper, the lease-renewal heartbeat, and the `DispatchResult`/`ToolArgs` type definitions (D-1, corrected this cycle) (REQ-008; `scripts/mcp_servers/dedup_gate.py`)
   - [ ] Delegate from the dispatcher and re-export the moved private helpers from it so the existing test seams and consumers import the same names (REQ-001, REQ-008; `scripts/mcp_servers/dispatch.py`)
   - [ ] Confirm the existing dispatcher suite is green before any behavior change, which is this phase's isolation check (REQ-008; tests/mcp_servers/test_mcp_dispatch.py)
4. **Phase 4: Heartbeat during handler execution** (member of the `dispatcher-decision-change` unit)
   - [ ] Start the renewal task before `await handler(...)` and stop it when the handler returns or raises, renewing every `lease_seconds / 2` while the lease is live (REQ-003; `scripts/mcp_servers/dedup_gate.py`)
   - [ ] Carry a renewal failure or lease conflict to finalization so the result reports `lease_conflict` and the handler is never re-dispatched, keeping the `asyncio.CancelledError` path's `mark_interrupted()` behavior (REQ-003, REQ-004; `scripts/mcp_servers/dispatch.py`)
5. **Phase 5: One decision point in durable mode** (member of the `dispatcher-decision-change` unit)
   - [ ] Remove the overlay read and the two `_idem_store()` writes from the store-configured path, keeping them for the store-unavailable and failed-write degraded paths exactly as today (REQ-001, REQ-006, REQ-007; `scripts/mcp_servers/dispatch.py`)
   - [ ] Route the reused-key-with-different-content rejection only through `contract_mismatch` (REQ-001, REQ-006; `scripts/mcp_servers/dedup_gate.py`)
6. **Phase 6: Name the refusing state** (member of the `dispatcher-decision-change` unit)
   - [ ] Tag the policy-refused `interrupted` refusal with `dedup_state="interrupted"` while keeping `error_type="dedup_unreplayable"` and the existing tags for the other branches (REQ-004, REQ-005; `scripts/mcp_servers/dedup_gate.py`)
   - [ ] Keep `in_progress`, `reconciliation_required`, `replay_unavailable`, `outcome_unknown`, `duplicate_hit`, `store_error`, and `lease_conflict` reporting as they are today (REQ-005; `scripts/mcp_servers/dispatch.py`)
7. **Phase 7: Test seam and assertion updates** (member of the `dispatcher-decision-change` unit)
   - [ ] Replace the fast-path and cache-length assertions with durable-acquisition assertions, and add the `interrupted`-vs-`failed` policy matrix, the expiry-boundary pairs, and the snapshot/truncation no-re-execution cases (REQ-001, REQ-004, REQ-005, REQ-006, REQ-007; `tests/mcp_servers/test_mcp_dispatch.py`)
8. **Phase 8: Full validation and deploy hand-off**
   - [ ] Run the full `rules/toolchain.md` validation sequence for the implementation diff, including `uv run python tools/check_module_size.py`, `uv run lint-imports`, `uv run ast-grep`, `uv run bandit -r scripts/ -c pyproject.toml`, the full test suite, and `diff-cover --fail-under=90` (REQ-008; scripts/mcp_servers/dispatch.py, scripts/mcp_servers/dedup_gate.py, scripts/shared/mcp_dedup_ledger.py)
   - [ ] Confirm no document excluded by the source Issue's Constraints was modified, and carry the two behavior facts recorded in `Documentation Impact` forward for the documentation sweep item to align (REQ-003, REQ-004, REQ-005; scripts/mcp_servers/dispatch.py, scripts/mcp_servers/dedup_gate.py)
   - [ ] Hand off deployment to `skills/deploy/SKILL.md`: prerequisite is that the change is committed and pushed first, `scripts/`, `tests/`, and `docs/` are rsynced so no `deploy.sh` copy line changes, and deploying is the user's decision through that skill's approval gate (REQ-008)

### Release units
**Unit**: dispatcher-decision-change | **Phases**: 1, 4, 5, 6, 7 | **Reason**: the new tests fail until the heartbeat, the single decision point, and the state tags land, and the existing fast-path assertions fail until Phase 7 updates them, so these phases cannot each pass validation alone; Phases 2, 3, and 8 are validated on their own.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/dispatch.py | Unit and async-concurrency unit tests | `uv run pytest tests/mcp_servers/test_mcp_dispatch_concurrency.py tests/mcp_servers/test_mcp_dispatch.py -q` (delete `.testmondata` first: the consumer scan reported `Testmon: used`) | 100 callers execute the handler exactly once; the durable path never touches `_duplicate_cache`; all pre-existing dispatcher cases still pass |
| scripts/mcp_servers/dispatch.py | Module shape and complexity | `uv run python tools/check_module_size.py` and `uv run radon cc scripts/mcp_servers/dispatch.py -s` | No new size violation; `dispatch_tool` below its current `E (37)` grade |
| scripts/mcp_servers/dedup_gate.py | Unit tests through the dispatcher seam; import contract | `uv run pytest tests/mcp_servers/ -q`, `uv run lint-imports` | 6 contracts kept, 0 broken; the new module imports only `shared/` and stdlib (`DispatchResult`/`ToolArgs` are defined there per the D-1 correction, not imported from `mcp_servers.models`) |
| scripts/shared/mcp_dedup_ledger.py | Store-level unit tests, including the race and lease suites | `uv run pytest tests/shared/test_mcp_dedup.py tests/shared/test_mcp_dedup_concurrency.py tests/shared/test_mcp_dedup_identity.py -q` | Permitted reopen and refused reopen both asserted; the existing reopen case unchanged; store identity and fingerprint tests unchanged |
| tests/mcp_servers/test_mcp_dispatch_concurrency.py | New test module | `uv run pytest tests/mcp_servers/test_mcp_dispatch_concurrency.py -q` | Green after Phases 4-6; recorded red on the pre-change dispatcher for the lease case |
| tests/mcp_servers/test_mcp_dispatch.py | Updated assertions | `uv run pytest tests/mcp_servers/ tests/integration/test_production_security_regression.py -m "not production_paths_allowed" -q` | Green, with the policy matrix, boundary pairs, and no-re-execution cases added |
| tests/shared/test_mcp_dedup.py | Updated store assertions | `uv run pytest tests/shared/ -q` | Green; the DDL and vocabulary pins unchanged |
| All targets | Documentation and workitem consistency, with no document under the Issue's Constraints list appearing in the diff | `uv run python tools/check_doc_drift.py`, `uv run python tools/check_workitem_traceability.py`, then `uv run pre-commit run --all-files` | Green; the implementation diff contains no change to the dedup design document, the ADR, the governance entries, or the skill files the Issue excludes |
| All targets | Type, lint, security, coverage | `uv run ruff check .`, `uv run mypy scripts/`, `uv run bandit -r scripts/ -c pyproject.toml`, then the `rules/toolchain.md` section 7 sequence with `--fail-under=90` | Clean; no new Medium or High bandit finding (baseline: 47 Low `B101` findings, 0 Medium, 0 High); diff coverage at or above 90% on the implementation diff |

## Risks
- **Risk**: a per-call renewal task adds a concurrent store writer for every long-running call, increasing `BEGIN IMMEDIATE` contention → **Mitigation**: one renewal per `lease_seconds / 2` while the lease is live, short transactions under the store's existing `threading.Lock` and `PRAGMA busy_timeout` (5000 ms), and the concurrency test in `tests/mcp_servers/test_mcp_dispatch_concurrency.py` measures the 100-caller case.
- **Risk**: removing the durable-mode fast path sends every duplicate hit to SQLite, changing latency and the source of the `duplicate_hit` tag → **Mitigation**: the `replay_completed` branch already serves the same result and is already tested; the cache stays available on the degraded path; T-1 and T-6 assert both.
- **Risk**: the `interrupted` recovery gate changes behavior for cancelled non-retryable calls that previously auto-replayed → **Mitigation**: the gate applies only to tools whose declared retry policy is non-retryable, the row is left `interrupted` with its terminal evidence, the refusal is reported as `interrupted` with `dedup_unreplayable`, the store parameter defaults to the current behavior for every other caller, and T-3 and T-4 pin both sides.
- **Risk**: ADR-004's MCP-001 and MCP-002 wording cites dispatcher and store symbols that are already partly stale, so the gate extraction could make the exception text harder to verify → **Mitigation**: keep the degraded behavior unchanged (fail-open for retryable, fail-closed for non-retryable, warning-only post-open write), write no approval, and leave the citation refresh to the MCP documentation sweep item (mcpai012) and the maintainer decision recorded in the governance entries (UNK-05).
- **Risk**: this Plan, the generated-but-not-yet-executed mcpdl005 procedures, and the landed mcpdl004 implementation all touch `scripts/shared/mcp_dedup_ledger.py` and the same shared test files, so an interleaved implementation could overwrite either side's assertions → **Mitigation**: this cycle re-read the functions each side changes (the acquisition path here, where the landed mcpdl004 half changed `record_completed()`, added `call_state_view()`, and pins the DDL there; `purge_expired()` is the pending mcpdl005 change), and each was judged compatible; the shared worktree and single-cycle rule keeps the cycles out of each other's files; and the implementation phase re-reads the acquisition signature before editing (Assumptions, UNK-06).
- **Risk**: `scripts/mcp_servers/dispatch.py` sits 3 B under a hard module-size gate, so even the extraction could leave either module over the limit → **Mitigation**: Phase 3 is a pure move validated by `tools/check_module_size.py` before any behavior is added, and AC-7 makes the gate a completion criterion.
- **Risk**: exactly-once across processes depends on the store being present, and `/opt/llm/db/mcp_dedup.sqlite` does not exist on this host, so a deploy without the store keeps every retryable call on the audited degraded path → **Mitigation**: REQ-007 keeps non-retryable tools failing closed, the start-state refusals stay in place, and the deploy hand-off (`skills/deploy/SKILL.md`) is where the store's creation and its per-server `[dedup]` values are the user's decision.
- **Risk**: single-author modules (`dispatch.py` 99.9% by one author) mean no second reviewer for the state-machine semantics → **Mitigation**: the acceptance criteria are stated as executable tests (AC-1 to AC-7), and `python-code-review` is the designated review step of the implementation phase for this Plan.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Dispatcher concurrency and lease tests written first against the unmodified dispatcher (tests/mcp_servers/test_mcp_dispatch_concurrency.py) | Completed | — | 20261123-233715 | member of the `dispatcher-decision-change` unit; validated with Steps 4-7 |
| 2 | Store-side `allow_interrupted_recovery` parameter and its store tests (scripts/shared/mcp_dedup_ledger.py, tests/shared/test_mcp_dedup.py) | Completed | — | 20261123-233715 | Independently validatable |
| 3 | Gate module extraction with helper re-export (scripts/mcp_servers/dedup_gate.py, scripts/mcp_servers/dispatch.py) | Completed | — | 20261123-233715 | Behavior-preserving; `tools/check_module_size.py` clean |
| 4 | Lease heartbeat during handler execution (scripts/mcp_servers/dedup_gate.py, scripts/mcp_servers/dispatch.py) | Completed | — | 20261123-233715 | member of the `dispatcher-decision-change` unit |
| 5 | Single decision point: overlay removed from the durable path (scripts/mcp_servers/dispatch.py, scripts/mcp_servers/dedup_gate.py) | Completed | — | 20261123-233715 | member of the `dispatcher-decision-change` unit; degraded path unchanged |
| 6 | Refusal state tags including `interrupted` (scripts/mcp_servers/dedup_gate.py, scripts/mcp_servers/dispatch.py) | Completed | — | 20261123-233715 | member of the `dispatcher-decision-change` unit; depends on Step 2 |
| 7 | Dispatcher test seam and assertion updates (tests/mcp_servers/test_mcp_dispatch.py) | Completed | — | 20261123-233715 | member of the `dispatcher-decision-change` unit |
| 8 | Full validation sequence and deploy hand-off (scripts/mcp_servers/dispatch.py, scripts/mcp_servers/dedup_gate.py, scripts/shared/mcp_dedup_ledger.py) | Pending | — | — | No document excluded by the Issue's Constraints is modified; deploy is the user's decision via `skills/deploy/SKILL.md` full validation sequence ran 20261123: full suite 13645 passed, diff-cover 100% on changed lines, radon dispatch_tool D (25), pre-commit clean on changed files; deploy hand-off not performed - the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at Plan creation | N/A: no blocker recorded | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261123-205822_01_scripts_mcp_servers_dispatch.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261123-205822_02_scripts_mcp_servers_dedup_gate.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261123-205822_03_scripts_shared_mcp_dedup_ledger.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261123-205822_04_tests_mcp_servers_test_mcp_dispatch_concurrency.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261123-205822_05_tests_mcp_servers_test_mcp_dispatch.py.md | 7 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-130937
- **Related target files**: scripts/mcp_servers/dispatch.py, scripts/mcp_servers/dedup_gate.py, scripts/shared/mcp_dedup_ledger.py, tests/mcp_servers/test_mcp_dispatch_concurrency.py, tests/mcp_servers/test_mcp_dispatch.py, tests/shared/test_mcp_dedup.py

### Requirement Traceability
Source: `templates/requirement-traceability.md`.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes items 1 and 9; Step 2 read of `dispatch_tool()` | scripts/mcp_servers/dispatch.py | 3, 5 | AC-1 | T-6, Validation plan row for `scripts/mcp_servers/dispatch.py` | Verified |
| REQ-001 | Step 3 consumer scan (17 importer candidates) | scripts/mcp_servers/dedup_gate.py | 3 | AC-1, AC-7 | T-6, `uv run lint-imports` | Verified |
| REQ-002 | Acceptance Criteria item 1; Testing Expectations item 1 | tests/mcp_servers/test_mcp_dispatch_concurrency.py | 1 | AC-1 | T-1 | Needs confirmation → resolved by Step 2 evidence (store-level serialization exists; dispatcher-level proof is this test) |
| REQ-002 | Required Changes items 1-2; Step 2 read of `_dedup_decision()` | scripts/mcp_servers/dispatch.py | 5 | AC-1 | T-1, T-6 | Verified |
| REQ-003 | Required Changes item 3; Step 2 read of `_renew_lease_if_needed()` and `dispatch_tool()` | scripts/mcp_servers/dedup_gate.py | 4 | AC-2, AC-4 | T-2 | Verified |
| REQ-003 | Required Changes item 3 | scripts/mcp_servers/dispatch.py | 4 | AC-2, AC-4 | T-2 | Verified |
| REQ-004 | Problem item 2 as verified in Step 2; Required Changes items 3 and 6 | scripts/shared/mcp_dedup_ledger.py | 2 | AC-3, AC-4 | T-3 | Verified |
| REQ-004 | Testing Expectations item 2 | tests/shared/test_mcp_dedup.py | 2 | AC-3 | T-3 | Verified |
| REQ-004 | Problem item 2; Testing Expectations item 3 | tests/mcp_servers/test_mcp_dispatch.py | 7 | AC-3 | T-4 | Verified |
| REQ-004 | Required Changes items 6-7 | scripts/mcp_servers/dedup_gate.py | 6 | AC-3 | T-4 | Verified |
| REQ-005 | Required Changes items 2 and 7; Acceptance Criteria items 3 and 5 | scripts/mcp_servers/dedup_gate.py | 6 | AC-3, AC-5 | T-4, T-5 | Verified |
| REQ-005 | Required Change item 7 | scripts/mcp_servers/dispatch.py | 6 | AC-5 | T-5 | Verified |
| REQ-005 | Testing Expectations item 3 | tests/mcp_servers/test_mcp_dispatch.py | 7 | AC-3, AC-5 | T-4, T-5 | Verified |
| REQ-006 | Required Change item 8; Step 2 read of `scripts/agent/tool_runner.py` `_logical_call_id()` | scripts/mcp_servers/dispatch.py | 5 | AC-1 | T-6 | Verified |
| REQ-006 | Required Change item 8 | tests/mcp_servers/test_mcp_dispatch.py | 7 | AC-1 | T-6 | Verified |
| REQ-007 | Constraints item 4; Acceptance Criteria item 6; Required Change item 9 | scripts/mcp_servers/dispatch.py | 5 | AC-6 | T-7 | Verified |
| REQ-007 | Constraints item 4 | tests/mcp_servers/test_mcp_dispatch.py | 7 | AC-6 | T-7 | Verified |
| REQ-008 | Step 5 module-size and radon baseline | scripts/mcp_servers/dedup_gate.py | 3 | AC-7 | T-8 | Verified |
| REQ-008 | Step 3 predictable fallout check (module size) | scripts/mcp_servers/dispatch.py | 3 | AC-7 | T-8 | Verified |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261123-205822 -->
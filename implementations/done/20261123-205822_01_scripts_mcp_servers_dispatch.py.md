## Goal

- Make `dispatch_tool()`'s durable-dedup decision come from one typed acquisition through the new gate module, keep the owner lease alive while the handler runs, and stop reading or writing the in-process overlay on the store-configured path (REQ-001 single decision point, REQ-003 lease heartbeat, REQ-005 refusal state tags, REQ-006 caller-supplied id, REQ-008 module-size extraction).

## Scope
**Release unit**: dispatcher-decision-change

- Modify `scripts/mcp_servers/dispatch.py` only: delegate the acquisition-branch mapping to `scripts/mcp_servers/dedup_gate.py` (sibling document `20261123-205822_02`), add the heartbeat call site, remove the overlay from the durable path, and keep every consumer-facing name importable from `mcp_servers.dispatch`.

## Assumptions

- This cycle's re-read (20261123) confirmed the Plan's dispatcher claims: the overlay read block in `dispatch_tool()`, `_idem_store()` called after dispatch, the post-handler `_renew_lease_if_needed()`, and `_dedup_decision()` mapping the typed acquisition are all present as described.
- The mcpdl004 implementation has landed (`call_state_view()`, result-metadata columns, `_USER_VERSION = 2` in the ledger/schema); the mcpdl005 procedures are generated but not yet executed. Neither touches this file (Plan Assumptions).
- `tests/mcp_servers/conftest.py` monkeypatches `dispatch_mod._dedup_store`, `dispatch_mod._dedup_config`, `dispatch_mod._dedup_disabled`, and `dispatch_mod._dedup_start_state` and calls `dispatch_mod._duplicate_cache.clear()`: the four store globals stay in `dispatch.py`, and the cache re-export must expose the same cache object the gate module uses (a shared module-level binding, not a copy).
- `tests/mcp_servers/git/test_git_security_compliance.py` monkeypatches `dispatch._is_side_effecting`: `_is_side_effecting()` and `_write_tools` stay in `dispatch.py` (not moved to the gate).
- `DispatchResult` and `ToolArgs` move to the gate module and are re-exported here (Plan D-1, corrected this cycle) so all 20 importing modules keep their import paths.
- The gate module and the `allow_interrupted_recovery()` parameter are created by the seq 02 and seq 03 siblings of this Plan; this document references them before they exist.

## Design decisions

- Single decision point: the acquisition-branch mapping lives in the gate's `_dedup_decision()`; `dispatch_tool()` keeps only the `early is not None` return and the `_OWNED_STATES` ownership decision (REQ-001).
- Heartbeat: a gate-owned `_LeaseHeartbeat` (new) asyncio task renews every `store.lease_seconds / 2` while `await handler(args)` is in flight; a failed or conflicting renewal is recorded so finalization reports `lease_conflict` and never re-dispatches (REQ-003, D-3).
- The degraded path (store unavailable or failed store write) keeps its overlay read/write calls byte-for-byte (REQ-007, D-2).

## Alternatives considered

- Keep `_dedup_decision()` and the cache in `dispatch.py`: rejected — 24573 B against the 24576 B gate with no baseline entry, and `dispatch_tool()` is radon `E (37)` (REQ-008).
- Keep `DispatchResult` defined in `dispatch.py` while the gate's refusal constructors build it: rejected — the gate would import `dispatch.py`, a circular import; the Plan's D-1 was corrected this cycle to move the two type definitions instead.

## Implementation
### Target file
`scripts/mcp_servers/dispatch.py`

### Procedure
1. Phase 3 (behavior-preserving move): delete the local definitions of `DispatchResult`, `ToolArgs`, `_CacheEntry`, `_duplicate_cache`, `_idem_now()`, `_idem_evict()`, `_idem_store()`, `_IDEMPOTENCY_CACHE_TTL_SECONDS`, `_IDEMPOTENCY_CACHE_MAX_ENTRIES`, `_new_owner_id()`, `_dedup_decision()`, `_OWNED_STATES`, and `_renew_lease_if_needed()`; import them from `mcp_servers.dedup_gate` and re-export the same names at module level (the heartbeat replaces `_renew_lease_if_needed()`, whose consumer scan returned no candidate outside this file). Run `tools/check_module_size.py` at this point — Phase 3 is a pure move and both modules must be under the gate before any behavior is added. Landed deviation (Phase 3): `_renew_lease_if_needed()` and its post-handler call stay in `dispatch.py` until Phase 4 installs `_LeaseHeartbeat`, because removing the helper here would drop lease renewal before its replacement exists; Phase 3 stays a pure move without it.
2. Phase 4: when the call owns the row (`store is not None` and `dedup_state in _OWNED_STATES`), start the `_LeaseHeartbeat` (new) before `await handler(args)` and stop it when the handler returns or raises; delete the post-handler `_renew_lease_if_needed()` call; keep the `asyncio.CancelledError` path's `mark_interrupted()` behavior and the `record_failed()` finalization paths unchanged.
3. Phase 5: run the overlay read and its reused-key rejection only when `store is None` (degraded path); on the durable path the reused-key rejection comes only from the acquisition's `contract_mismatch`. Remove the post-dispatch `_idem_store()` write on the durable path; keep the degraded-path write.
4. Phase 6: pass `retryable=_retryable(name)` into `_dedup_decision()`; keep the existing `dedup_state` tags (`in_progress`, `reconciliation_required`, `replay_unavailable`, `outcome_unknown`, `duplicate_hit`, `store_error`, `lease_conflict`) and let the gate's new `interrupted` refusal tag pass through untouched.

### Method
- Stay in `dispatch.py` (the dispatcher's own state and seam): `configure_dedup()`, `configure_tool_retry_policies()`, `_retryable()`, `_tool_retry_policies`, `_dedup_store`, `_dedup_config`, `_dedup_disabled`, `_dedup_start_state`, `_purge_done`, `_dedup_context()`, `_purge_once()`, `_store_op()`, `_is_side_effecting()`, `_write_tools`, `_normalize_args_hash()`, `_is_dry_run_output()`, `_IDEMPOTENCY_DRY_RUN_MARKERS`, `_to_call_tool_response()`, `dispatch_tool()`.
- The gate never imports this module and never reads the retry-policy map: the permission is passed as the explicit `retryable` argument (no import cycle; `lint-imports` contracts unchanged).
- Current call-site anchors (re-read before editing): the overlay read block in `dispatch_tool()` starting at `entry = _duplicate_cache.get(key)`; the `_dedup_decision()` call after `_dedup_context()`; `if dedup_state in _OWNED_STATES:`; the `try: result = await handler(args)` block; the `_renew_lease_if_needed(store, store_key, owner, dispatched_at)` call in the finalization block; the final `if key and side_effecting and not dry_run: _idem_store(...)` write.

### Details
- Post-change durable flow inside `dispatch_tool()`: key/side-effecting gate → `_acquire_dedup()` (new helper: `_dedup_context()`, `_purge_once()`, `build_execution_snapshot()`, `_new_owner_id()`, gate `_dedup_decision(..., retryable=_retryable(name))` with the unchanged `store_error` except-clause, and the `_OWNED_STATES` ownership decision) → dispatch under the heartbeat → `_finalize_dedup()` (new helper) owner-conditional finalization. Degraded flow (`_degraded_decision()` (new), reached only when `_dedup_context()` returns no store): `_overlay_lookup()` read (reuse rejection included) → `store_error` dispatch → overlay write for real non-dry-run results only. Landed deviation: the Phase 5/6 branch removal alone left `dispatch_tool()` at radon `E (39)`, so its decision and finalization blocks were extracted into these module-level helpers; `dispatch_tool()` is now `D (25)` and the branch semantics are unchanged.
- Heartbeat bookkeeping: carry a `renewal_lost` (new) flag from `_LeaseHeartbeat.stop()`; a true flag sets `dedup_state = "lease_conflict"` exactly like the existing zero-row `record_completed()` failure does, and the handler is never re-dispatched (AC-4).
- `dispatch_tool()`'s docstring: update the dedup paragraph to state that the durable decision comes only from the acquisition and the lease is renewed during execution (no ADR or design document is touched — Documentation Impact).

## Compatibility considerations

- 20 importing modules (11 server-side including `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/web_search/web_search_server.py`, and `scripts/mcp_servers/web_search/formatters.py`; the `scripts/mcp_servers/server.py` bootstrap seam; 8 test modules) use only `dispatch_tool`, `DispatchResult`, `_to_call_tool_response`, `ToolArgs`, `configure_dedup`, or `configure_tool_retry_policies`; all signatures and import paths are preserved by the re-export.
- On the durable path `dedup_state="duplicate_hit"` now comes from the store's `replay_completed` branch and the reused-key rejection from `contract_mismatch` (D-2); response shapes are unchanged (`CallToolResponse.dedup_state` stays a free-form `str`).

## Security considerations

- The heartbeat reuses `renew_lease()` — short `BEGIN IMMEDIATE` transactions under the store's `threading.Lock` and `PRAGMA busy_timeout` — adding no new write surface (Risk 1 mitigation).
- Non-retryable fail-closed and the audited ADR-004 MCP-001/MCP-002 degraded behavior stay unchanged; no approval text is written (REQ-007).

## Rollback considerations

- Reverting this file's commit restores the pre-extraction single-module layout (D-1 reversibility: high); no persisted state changes.

## Validation plan

- Delete `.testmondata` first (the Plan's consumer scan reported `Testmon: used`), then `uv run pytest tests/mcp_servers/test_mcp_dispatch.py tests/mcp_servers/test_mcp_dispatch_concurrency.py -q`.
- `uv run python tools/check_module_size.py` (no new violation) and `uv run radon cc scripts/mcp_servers/dispatch.py -s` (`dispatch_tool` below its `E (37)` grade).
- `uv run lint-imports` (6 kept, 0 broken) and `uv run pytest tests/mcp_servers/ -q` green after the Phase 3 move alone.

## Completion criteria

- No read or write of `_duplicate_cache` remains on the store-configured path; the lease is renewed while the handler runs; both `dispatch.py` and the gate module are under 24576 B; every pre-existing dispatcher test class passes with the seq 05 assertion updates.

## Out of Scope

- The gate module's own contents (sibling `20261123-205822_02`), the ledger recovery parameter (sibling `20261123-205822_03`), the new and updated test modules (siblings `20261123-205822_04` and `20261123-205822_05`), and every document excluded by the source Issue's Constraints.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 3: pure move to the gate module plus same-name re-export; size gate clean before any behavior change | Completed | — | 20261123-224027 | gate extraction landed; dispatch.py 16735 B, gate 9771 B; pytest tests/mcp_servers/ 2727 passed; lint-imports 6 kept |
| 2 | Phase 4: `_LeaseHeartbeat` (new) call site around `await handler(...)`; remove post-handler renewal | Completed | 20261123-224027 | 20261123-225043 | Phase 4 heartbeat call site _LeaseHeartbeat call site via _dispatch_with_heartbeat; _renew_lease_if_needed and its post-handler call deleted; renewal_lost maps to lease_conflict |
| 3 | Phase 5: overlay removed from the durable path; degraded path unchanged | Completed | — | 20261123-232053 | overlay read/write gated on store is None via _overlay_lookup + _degraded_decision; durable reused-key rejection comes only from contract_mismatch |
| 4 | Phase 6: `retryable` argument wiring and `lease_conflict` finalization flag | Completed | — | 20261123-232053 | retryable=_retryable(name) wired; lease_conflict from heartbeat.renewal_lost via _finalize_dedup; decision/finalization extracted to _acquire_dedup/_finalize_dedup -> dispatch_tool radon D (25) |
| 5 | Run the validation sequence (`rules/toolchain.md` + this document's Validation plan) | Completed | 20261123-232054 | 20261123-233500 | release-unit validation sequence release-unit validation: ruff+ruff format, mypy 456 files, bandit 0 Medium/High, lint-imports 6 kept, check_module_size clean, radon dispatch_tool D (25), full suite 13645 passed, diff-cover 100% on changed lines |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (single durable decision point), REQ-003 (lease renewed during execution), REQ-005 (refusal state tags), REQ-006 (caller-supplied id contract), REQ-008 (gate extraction)
- **Source issue**: issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-205822
- **Related target files**: `scripts/mcp_servers/dispatch.py`
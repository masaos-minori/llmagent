## Goal

Make the shared MCP dispatcher's durable dedup store (`mcp_dedup.sqlite`) unable to cause a silent repeat of a non-retryable side effect when the store is lost or recreated. Concretely: add out-of-band "lost or recreated" detection (`REQ-003`) and expose an operator-resolution step that clears the lost/recreated flag (`REQ-001`). The post-open write-failure fail-closed path (`REQ-002`) is implemented in `dispatch.py` (seq 02), where `_store_op` actually lives — see Assumptions and Blocker Log.

## Scope
**Release unit**: Empty-store fail-closed (Plan release unit: Phases 1, 2 — the detection mechanism here must land before `dispatch.py`'s rejection path can be validated alone).

## Assumptions
- The maintainer's 2026-11-09 decision stands: `mcp_dedup.sqlite` is a disposable cache (Option B); recovery is recreation; no backup.
- The guarantee must survive loss of the DB file, so the lost/recreated marker CANNOT live inside that file (`tool_call_state_ops.py` confirms the dispatcher/agent boundary: the Agent never touches `mcp_dedup.sqlite`, so a pure Agent-side second layer is boundary-violating).
- `retry_class()` defaults unknown tools to `non_retryable` (`mcp_dedup.py` L166-170); moving config must not default any tool to a weaker class (`REQ-004`).
- **Plan discrepancy (verified, not fabricated).** The plan's `mcp_dedup.py` row attributes a `_store_op` fail-closed change to this file, but `_store_op` does NOT live in `mcp_dedup.py`. Verified against HEAD: `mcp_dedup.py` L208-220 is `_cap_result`; the write path `_write()` at L252-260 already raises on `sqlite3.Error`. The real `_store_op` (catches `(sqlite3.Error, OSError)`, warns, returns `False`, caller ignores) is `scripts/mcp_servers/dispatch.py` L209-216. So the REQ-002 post-open write-failure fix is implemented in `dispatch.py` (seq 02), and this file owns only REQ-001 (operator resolution) and REQ-003 (out-of-band detection). Flagged to the plan owner; the frozen plan table is left unchanged.
- Open (flag, do not fabricate): the exact sentinel shape/location and the "never seen" vs "lost" distinction (UNK-01) are design decisions. See Design decisions.

## Design decisions
- **Out-of-band sentinel (UNK-01, primary).** Because the marker cannot live in the lossable file, use a small flag OUTSIDE both databases: a sentinel file in the resolved config dir (`resolve_config_dir()`, `mcp_dedup.py` L80) or alongside the DB file. Presence = operator-acknowledged/resolved; absence after a loss = "lost" → fail closed for non-retryable until the operator resolves it. A genuine first-ever run also finds no sentinel, so the sentinel is operator-acknowledged, not merely "absent" (Plan Risks mitigation). The precise sentinel path and the never-seen-vs-lost discrimination are left open for the implementer to settle by reading existing data/config-dir conventions; assert BOTH states in `tests/shared/test_mcp_dedup.py`.
- **Scope note — the post-open write-failure fix is NOT here.** The plan's `mcp_dedup.py` row attributes a `_store_op` fail-closed change to this file, but `_store_op` does not live in `mcp_dedup.py` (verified: `mcp_dedup.py` L208-220 is `_cap_result`; the write path `_write()` at L252-260 already raises on `sqlite3.Error`). The real `_store_op` (warns, returns `False`, caller ignores) is in `dispatch.py` L209-216. So the REQ-002 post-open write-failure fail-closed change is implemented in `dispatch.py` (seq 02), not here. This file owns only REQ-001 (operator resolution) and REQ-003 (out-of-band detection).

## Alternatives considered
- **Agent-side second layer in `workflow.sqlite`** (rejected pending UNK-02): would violate the dispatcher/agent boundary (`tool_call_state_ops.py` never writes `mcp_dedup.sqlite`). Preferring the out-of-band sentinel respects ADR-008.
- **Purely "absent sentinel = fail closed".** Rejected: a brand-new store without prior pending state must still execute once (Plan Risks). The sentinel must be operator-acknowledged to distinguish "never seen" from "lost".

## Implementation
### Target file
`scripts/shared/mcp_dedup.py`

### Procedure
1. Add out-of-band lost/recreated detection. On store open via `open_dedup_store()` (`mcp_dedup.py` L398-403) or a new helper it calls, check the sentinel. If the sentinel is absent, the store is either genuinely fresh or was lost/recreated; surface this as a boolean on the returned handle (e.g. `DedupStore.lost_or_recreated`) rather than deciding fail-closed here — the dispatch flow decides. Do NOT change `DedupStore.__init__`'s `CREATE TABLE IF NOT EXISTS`/`PRAGMA user_version` success-on-missing-file behaviour (`mcp_dedup.py` L232-246); the sentinel is what breaks the fail-open, not the constructor.
2. Expose the operator-resolution step: a module function such as `resolve_lost_store()` (new) that creates/clears the sentinel, clearing the lost/recreated flag after an operator has reviewed the post-recreation state. Keep it minimal and explicit.

> Scope note: do NOT add a `_store_op` fail-closed change here. `_store_op` is in `dispatch.py` (seq 02); `mcp_dedup.py`'s `_write()` already raises. See Design decisions.

### Method
- `DedupStore` carries a `lost_or_recreated: bool` set at open time from the sentinel check.
- `resolve_lost_store()` (new): create or clear the sentinel flag file.

### Details
- Sentinel location: choose a path consistent with existing config-dir/data-dir conventions; document the choice in a module comment. It must be outside `mcp_dedup.sqlite` itself (REQ-003).
- Preserve `retry_class()` default (`mcp_dedup.py` L166-170) and retention semantics (`purge_expired`, L351-376).
- `classify_interrupted` (L379-395) is unchanged.

## Compatibility considerations
- `open_dedup_store` gains a sentinel read; a missing sentinel on an existing healthy store is treated as "not lost" (operator-acknowledgement model), so current deployments without a pre-existing sentinel are unaffected unless the store was actually recreated.
- The post-open write-failure path raises a new exception from `dispatch.py`'s own write path (seq 02), not here; this file only surfaces `lost_or_recreated` (new) on the handle.

## Security considerations
- The sentinel is a safety gate, not a security control; place it where an operator can see and manage it. Its absence must fail closed, not open.

## Rollback considerations
Revert the commit. The sentinel file is inert if left behind; removing it is optional cleanup.

## Validation plan
- `uv run pytest tests/shared/test_mcp_dedup.py -v`:
  - `DedupStore.__init__` still succeeds on a missing/recreated file (regression guard for the constructor; the fail-open was the bug).
  - After deleting the DB file, a reopened store reports `lost_or_recreated=True`; the sentinel is outside the DB file (REQ-003).
  - `resolve_lost_store()` creates and clears the sentinel flag.
  - `retry_class()` still defaults unknown tools to `non_retryable` after any config move (REQ-004).
- Impact-radius check (`rules/toolchain.md`) for `open_dedup_store`; full validation sequence.

## Completion criteria
- A store opened after its file was deleted reports lost/recreated without raising.
- `resolve_lost_store()` clears the flag; the sentinel lives outside `mcp_dedup.sqlite`.
- `tests/shared/test_mcp_dedup.py` covers all three points above.

## Out of Scope
- Wiring the rejection into `dispatch_tool` (`dispatch.py`, seq 02).
- Config isolation (`pending_timeout_minutes` move, `tool_runner.py` refactor) — seq 03/04/05/06.
- ADR/db documentation — seq 10-14.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement out-of-band detection + operator-resolution step in `mcp_dedup.py` | Pending | — | — | Depends on UNK-01 resolution (sentinel shape); post-open write-failure (REQ-002) is in `dispatch.py` seq 02 |
| 2 | Add/modify `tests/shared/test_mcp_dedup.py` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-003` — out-of-band lost/recreated detection, operator resolution
- **Source issue**: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-111905
- **Related target files**: `scripts/shared/mcp_dedup.py`

### Companion test files
- `tests/shared/test_mcp_dedup.py`
  - Procedure: add lost/recreated detection (`DedupStore.lost_or_recreated` after DB deletion), `resolve_lost_store()` create/clear, `retry_class` unknown default. The post-open write-failure asymmetry (REQ-002) lives in `tests/mcp_servers/test_mcp_dispatch.py` (seq 02), where `_store_op` lives.
  - Validation: `uv run pytest tests/shared/test_mcp_dedup.py -v` passes; constructor still succeeds on a missing file.

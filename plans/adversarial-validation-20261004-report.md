# Adversarial Validation Report — Plans 20261004-*

**Date:** 2026-10-04
**Scope:** All `plans/20261004-*-plan.md` files (18 plans total: 14 original + 4 additional)
**Validation dimensions:** Structural compliance, Implementation Target Files validity, cross-plan conflicts, factual accuracy of source claims, logic gaps in proposed solutions, shared vocabulary compliance

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| Critical | 2 | Cross-plan conflict on same file; proposed change breaks existing behavior |
| High | 7 | Factual claim mismatch with source code; logical gap in proposed solution |
| Medium | 12 | Structural non-compliance; incomplete evidence; overlapping scope; DESIGN.md violations |
| Low | 4 | Minor formatting/style issues |

---

## Critical Findings

### C-01: Cross-plan conflict — `scripts/agent/context.py` modified by 4 plans

Plans **7** (110000), **11** (114000), **12** (115000), and **14** (121000) all target `scripts/agent/context.py`. The changes overlap:

- **Plan 7**: Changes `from None` → `from e` at line 313 (exception chain preservation)
- **Plan 11**: Adds constructor validation in `AppServices.__init__()` (lines 256–281)
- **Plan 12**: Modifies both `startup_reporter.py` null checks AND `context.py` docstring
- **Plan 14**: Does NOT modify `context.py` directly (only `startup.py`)

**Impact:** Plans 7 and 11 modify different sections of the same file but were generated independently. If applied sequentially without coordination, Plan 11's constructor validation could cause failures that Plan 7's exception handling would mask.

**Recommendation:** Merge plans 7 + 11 into a single coordinated change. Plan 12 should be evaluated after Plan 11 is applied (since Plan 12's Option A depends on Plan 11's invariant enforcement).

### C-02: Proposed change in Plan 3 (102000) removes intentional behavior

Plan 3 proposes removing `remove_process_entry(server_key)` from before the try block in `shutdown_all()`. However, the current code includes an explicit comment:

```python
# Pop before termination to avoid double-shutdown if terminated fails
manager.remove_process_entry(server_key)
```

This is an intentional design decision, not a bug. Removing it could cause double-shutdown attempts when `terminate_with_timeout()` raises an exception and the process is later restarted.

**Severity:** High — this is a behavioral regression risk, not a bug fix.

**Recommendation:** Re-evaluate whether this is truly a bug or an intentional safety mechanism. If keeping the pop-before-termination approach, the mitigation should be to move `cleanup_server_key()` inside the except block only, not remove `remove_process_entry()`.

---

## High Findings

### H-01: Plan 1 (100000) — Missing required sections per template

Plan 1 lacks the following mandatory sections defined in `templates/plan.md`:
- `Goal`
- `Scope`
- `Background`
- `Problem`
- `Reason for change`
- `Implementation intent`
- `Requirements` (REQ-XXX format)
- `Acceptance criteria`
- `Tests`
- `Documentation Impact`
- `Unknowns` table
- `Affected areas`
- `Execution Status`
- `Traceability`

**Confidence:** High — verified against template.

### H-02: Plan 1 (100000) — Line numbers cited in violation of DESIGN.md §No source-code line numbers

Plan 1 cites specific line numbers:
- `delivery_repo.py` line 182-189
- `subscribe_route.py` line 126
- `ADR-006` line 362

DESIGN.md explicitly states: "Do not cite source-code line numbers in design documents."

**Recommendation:** Replace line references with class/function/method names.

### H-03: Plan 3 (102000) — Claimed line numbers don't match source

Plan 3 claims:
- Line 92: `manager.remove_process_entry(server_key)` called BEFORE termination ✓ (verified)
- Line 109-110: If termination fails, log warning ✓ (verified)
- Line 111: Always call `cleanup_server_key()` — even if termination failed ✓ (verified)

However, the proposed change moves BOTH `remove_process_entry()` AND `cleanup_server_key()` inside the try block. The current code has `remove_process_entry()` OUTSIDE the try block (line 92) and `cleanup_server_key()` INSIDE the finally-like path (line 111). The plan conflates these two separate calls.

**Confidence:** High — verified against actual source.

### H-04: Plan 4 (103000) — SIGKILL `else` clause verification is redundant

Plan 4 proposes adding an `else` clause with `wait_exited()` after SIGKILL escalation. However:
- After SIGKILL, the process MUST exit immediately (SIGKILL cannot be caught or ignored)
- Adding `wait_exited()` adds latency to the success path for no practical benefit
- If SIGKILL succeeds, the next `os.killpg(pgid, 0)` check will confirm the process is gone

**Confidence:** High — verified via Python docs and OS semantics.

### H-05: Plan 6 (105000) — Proposed change removes `finally` block incorrectly

Plan 6 proposes removing the `finally` block in `_create_and_validate_proc()`. However, the `finally` block ensures resource cleanup (stderr_fh close, `_http_procs`/`_http_pgids` removal) regardless of how the `except OSError` handler exits. Removing it means:
- If `terminate_with_timeout()` raises an unexpected exception (not OSError/TimeoutError), resources leak
- The current code handles this correctly by always cleaning up in `finally`

The plan's concern (tracking entries removed while process may still run) is valid, but the proposed fix is wrong. The correct fix is to keep the `finally` block but add tracking entry preservation logic inside the `except OSError` handler.

**Confidence:** High — verified against actual source.

### H-06: Plan 8 (111000) — `RagMaintenanceService` instance reuse doesn't solve resource leak

Plan 8 proposes reusing a `RagMaintenanceService` instance across calls. However:
- The current lambda creates a new instance each time (`lambda: RagMaintenanceService().consistency()`)
- If the service holds a SQLite connection, reusing it doesn't help — the connection lifecycle is independent
- The timeout addition is valid, but the instance reuse claim is misleading

**Confidence:** Medium — requires confirmation of `RagMaintenanceService` resource management.

### H-07: Plan 10 (113000) — `_is_current_approval()` method undefined

Plan 10 proposes adding `_is_current_approval()` method but does not define its logic. The method needs to determine whether the current `pending_approval_task_id` is "active" vs "stale", but there's no clear criterion:
- Is it based on timestamp comparison?
- Does the approval record still exist in the database?
- Has the approval been resolved/expired?

Without a concrete definition, this is an unimplementable requirement.

**Confidence:** High — the method signature exists but body is unspecified.

---

## Medium Findings

### M-01: Plans 3, 4, 5, 6, 13 — All propose creating `tests/agent/test_http_lifecycle.py`

Five plans independently propose creating the same test file. This is wasteful and risks conflicting test definitions. These plans should be consolidated into a single test creation effort.

### M-02: Plans 7, 11 — Both propose creating `tests/agent/test_context.py`

Two plans independently propose creating the same test file. Consolidate.

### M-03: Plan 1 (100000) — LEFT JOIN query semantic change acknowledged but not fully resolved

Plan 1 acknowledges that events with NO `consumer_delivery` record won't appear in the join result, and proposes a revised query using LEFT JOIN. However:
- The revised query uses `(cd.acked_at IS NULL OR cd.event_id IS NULL)` which is logically incorrect — `cd.event_id IS NULL` would match rows where the join didn't find a match, but `acked_at IS NULL` would also match rows where delivery was attempted but not yet acked
- The correct condition should be `cd.event_id IS NULL OR (cd.event_id IS NOT NULL AND cd.acked_at IS NULL)`

**Confidence:** High — SQL logic analysis.

### M-04: Plan 9 (112000) — ctypes fallback constant `CTRL_CLOSE_EVENT = 0` is fragile

Plan 9 uses hardcoded `CTRL_CLOSE_EVENT = 0`. While this value is consistent across Windows versions, hardcoding it violates the principle of using named constants. The plan should reference `win32con.CTRL_CLOSE_EVENT` even in the ctypes fallback path.

**Confidence:** Medium — Windows API documentation confirms consistency, but best practice suggests using the constant.

### M-05: Plan 12 (115000) — Option A depends on Plan 11 (114000) being applied first

Plan 12 presents two options:
- Option A: Enforce invariant + remove null checks (requires Plan 11's constructor validation)
- Option B: Keep null checks + document rationale

Option A is only viable if Plan 11 is applied first. Without Plan 11, enforcing the invariant at construction time would require duplicating the validation logic.

**Recommendation:** Evaluate Plan 12 only after Plan 11 is approved.

### M-06: Plan 13 (120000) — Claims inner client "shadows" outer client, but they're in different scopes

Plan 13 claims the inner `httpx.AsyncClient` shadows the passed-in client. However, looking at the actual code:
- The caller creates a client outside the method (line 466-468)
- The method receives `client` as a parameter (line 368)
- Inside the method, a NEW client is created (line 393-395)

These are indeed two separate clients. The inner one shadows the parameter name `client`, but more importantly, the inner one is used exclusively within the method while the outer one is closed after the method returns. The plan correctly identifies this as wasteful.

**Confidence:** High — verified against actual source.

### M-07: Plan 14 (121000) — Error message format change breaks existing parsing

Plan 14 changes the error message format from `"; ".join(fatal_messages())` to newline-separated parts with remediation. External tooling that parses the error message (e.g., CI/CD pipelines) may break.

**Recommendation:** Add REQ-004 verification for external tooling compatibility.

### M-08: Multiple plans use "Needs confirmation" for Validation Status without resolving

Plans 3, 4, 5, 6, 7, 8, 9, 11, 12, 13 all have `Validation Status: Needs confirmation` for their test files. Per `rules/workflow-lifecycle.md`, every row must be `Verified` before the section may be marked `Frozen`. These need resolution before any downstream workflow can proceed.

---

## Low Findings

### L-01: Plan 1 (100000) — No `Freeze status` field in Implementation Target Files

Per template, the Implementation Target Files section must include `**Freeze status**: Draft/Frozen`. Plan 1 omits this entirely.

### L-02: Plan 1 (100000) — No `Reference Files` section

Template requires a Reference Files section listing files that must be read but not modified. Plan 1 omits this.

### L-03: Plan 1 (100000) — No `Execution Status` table

Template requires Execution Status, Blocker Log, and Work Items Created tables. Plan 1 omits these.

### L-04: Plan 1 (100000) — No `Traceability` section

Template requires Traceability section with workflow phase, source issue, etc. Plan 1 omits this.

---

## Additional Findings — Plans Not Covered by Original Report

The original report covered 14 plans but there are 4 additional plans (`20261004-075440`, `20261004-081743`, `20261004-084356`, `20261004-094856`). Below are findings for each. Note: Plans 075440 and 081743 were later merged into `20261004-merged_075440_081743_plan.md`; Plans 084356 and 120000 were coordinated into `20261004-coordinated_084356_120000_plan.md`.

### M-09: Plan 075440 — Tighten CommandValidator python3 allowlist prefix

**Factual verification:** `startswith("python3")` at lines 82-84 of `http_lifecycle_command_validator.py` — VERIFIED ✓

**Cross-plan conflict:** This plan modifies `scripts/agent/http_lifecycle_command_validator.py` and `tests/agent/test_http_lifecycle_command_validator.py`, which also overlap with:
- Plan 081743 (same two files)
- Plan 121000 (Plan 14) — modifies `http_lifecycle_command_validator.py`

**DESIGN.md violation:** Implementation Target Files evidence column cites specific line numbers (e.g., "Current check at `CommandValidator.validate()` allowlist branch"), violating §No source-code line numbers rule.

**Assessment:** The plan itself is well-structured and follows the template. The core concern is the cross-plan overlap — three plans independently modifying the same validator module. These should be merged into a single coordinated change.

### M-10: Plan 081743 — filter_env strips inherited loader/interpreter env vars

**Factual verification:**
- `_ENV_KEY_DENYLIST` at `mcp_config.py:26` — VERIFIED ✓
- `filter_env()` at line 98 — VERIFIED ✓

**Cross-plan conflict:** Same two files as Plan 075440 and Plan 121000.

**DESIGN.md violation:** Evidence column cites line number ("denylist defined at `scripts/shared/mcp_config.py:26`").

**Assessment:** The plan correctly identifies that `filter_env()` seeds `result = dict(os.environ)` without stripping dangerous loader variables. However, the plan conflates two separate concerns: (a) stripping inherited dangerous vars and (b) centralizing the denylist import. Both are valid but should be evaluated together since they modify the same file.

### M-11: Plan 084356 — Remove dead outer AsyncClient

**Factual verification:**
- Outer `async with httpx.AsyncClient(...)` at lines 466-468 — VERIFIED ✓
- Inner `async with httpx.AsyncClient(...)` at line 393-395 — VERIFIED ✓
- `client` parameter at line 368 — VERIFIED ✓

**Verification detail:** The outer client IS passed to `_health_poll_until_ready()` at line 469-471, but inside that method the `client` parameter is immediately shadowed by the inner `as client:` at line 395. So the plan's claim that the outer client is unused/shadowed is CORRECT.

**Cross-plan conflict:** Modifies `scripts/agent/http_lifecycle.py`, which overlaps with Plan 120000 (Plan 13).

**DESIGN.md violation:** Evidence column cites specific line numbers ("Outer client at `start()` lines ~466-468", "inner client re-bound at `_health_poll_until_ready()` ~393-394", "`client` param at ~368").

**Assessment:** The plan is well-structured and the factual claims are accurate. The dead resource removal is a valid optimization. However, it must be coordinated with Plan 120000 since both modify the same file.

### M-12: Plan 094856 — HttpTransport fails loud instead of silently disabling auth

**Factual verification:**
- Line 51 has `cfg.auth_token if cfg is not None else ""` — VERIFIED ✓
- Lines 119-121 have `call()` header logic — VERIFIED ✓

**Cross-plan conflict:** Modifies `scripts/shared/http_transport.py` and two test files. Need to verify if any other plan targets these files.

**DESIGN.md violation:** Evidence column cites specific line numbers ("at line 43", "at lines 112-113").

**Assessment:** The plan is well-structured and the security concern is valid — `cfg=None` silently disables authentication. The plan correctly resolves UNK-01 (fail-loud default). However, the scope is significant (~20 test constructions across two files), making this more complex than Path A suggests.

### H-08: Plan 101000 — Claimed "only one caller" is factually wrong

Plan 101000 asserts: "Only one caller exists (`startup_mcp_starter.py::MCPStarter.start_servers()` and `verify_health()`) — verified via grep."

**Verification:** `retry_once_with_delay` is called at TWO locations in `startup_mcp_starter.py`:
- Line 96: `_start_servers()` method — wraps `_start_http_subprocess_once`
- Line 138: `_post_start_health_check()` method — wraps `_verify_single_health`

The claim of "only one caller" is INCORRECT. This affects REQ-004 (caller compatibility review) because the second call site may have different exception handling expectations.

**Factual verification of other claims:**
- Line 59 of `retry_helper.py`: `raise RuntimeError(masked_msg) from retry_err` — VERIFIED ✓
- startup_mcp_starter.py line 88: `except (OSError, RuntimeError)` — VERIFIED ✓
- No test coverage for `retry_once_with_delay` — VERIFIED ✓

**DESIGN.md violation:** Evidence column cites specific line number ("line 59").

**Assessment:** The core proposal (preserve original exception type) is sound. However, the caller count error means REQ-004 was incompletely addressed. Both callers must be reviewed for compatibility.

### H-09: Plan 104000 — Proposed API path doesn't match actual attribute access pattern

Plan 104000 proposes replacing `asyncio.all_tasks(loop)` with `self._ctx.turn.background_tasks`. However:

**Factual verification:**
- `resource_shutdown_coordinator.py` line 114: `asyncio.all_tasks(loop)` — VERIFIED ✓
- `context.py` line 184: `TurnState.background_tasks` exists — VERIFIED ✓
- `orchestrator.py` line 110: `_background_tasks` exists — VERIFIED ✓

**Issue:** The plan's Design section shows `self._ctx.turn.background_tasks` but the actual attribute name in `TurnState` is just `background_tasks`. Whether `turn` is an attribute of `self._ctx` depends on the context object structure, which the plan does not verify. If `self._ctx.turn` doesn't exist or isn't accessible from `ResourceShutdownCoordinator`, the proposed code won't compile.

**DESIGN.md violation:** Design section cites specific line numbers (lines 113-114, 121-122, 124, 184, 110).

**Assessment:** The core idea (narrow cancellation scope) is valid. But the implementation detail needs verification — the plan assumes `self._ctx.turn` is accessible without confirming it.

---

## Cross-Plan Dependency Map

```
Plan 11 (AS010) ──enforces invariant──▶ Plan 12 (RR011) Option A
Plan 11 (AS010) ──creates test file──▶ Plan 7 (AC005) test file
Plan 12 (RR011) ──depends on Plan 11──▶ Plan 12 Option A viability
Plan 3 (SC002) ──conflicts with──▶ Plan 4 (PT003) shutdown behavior
Plan 3 (SC002) ──shares test file──▶ Plans 4, 5, 6, 13
Plan 7 (AC005) ──shares test file──▶ Plan 11 (AS010)

# New cross-plan conflicts from additional plans:
Plan 075440 ──shares target file──▶ Plan 081743 (both: http_lifecycle_command_validator.py + test file)
Plan 075440 ──shares target file──▶ Plan 121000 (Plan 14: http_lifecycle_command_validator.py)
Plan 081743 ──shares target file──▶ Plan 121000 (Plan 14: http_lifecycle_command_validator.py)
Plan 084356 ──shares target file──▶ Plan 120000 (Plan 13: http_lifecycle.py)
Plan 094856 ──modifies http_transport.py──▶ ? (no known overlap yet)
```

---

## Recommendations

1. **Merge overlapping plans:** Plans targeting `scripts/agent/context.py` (7, 11, 12) should be coordinated. Plans creating the same test file (3+4+5+6+13 → `test_http_lifecycle.py`; 7+11 → `test_context.py`) should consolidate test creation.

2. **Re-evaluate Plan 3 (102000):** The intentional `remove_process_entry()` call before termination is a safety mechanism, not a bug. Reconsider the proposed change.

3. **Fix Plan 6 (105000):** Remove the `finally` block is incorrect. Instead, preserve tracking entries inside the `except OSError` handler while keeping the `finally` block for resource cleanup.

4. **Define `_is_current_approval()` in Plan 10 (113000):** Before implementation, specify the exact logic for determining whether a pending approval is active vs stale.

5. **Resolve all `Needs confirmation` validation statuses** before marking any Plan's Implementation Target Files as `Frozen`.

6. **Apply shared vocabulary rules:** Replace line-number references with class/function/method names per DESIGN.md §No source-code line numbers.

7. **Merge overlapping plans on `http_lifecycle_command_validator.py`:** Plans 075440, 081743, and 121000 (Plan 14) all independently modify the same validator module. These three should be consolidated into a single coordinated change covering both the python3 allowlist tightening AND the filter_env denylist stripping.

8. **Coordinate Plans 084356 and 120000 (Plan 13):** Both modify `http_lifecycle.py` — Plan 084356 removes the dead outer AsyncClient; Plan 120000 addresses inner client shadowing. Apply together to avoid conflicting edits.

9. **Verify Plan 094856 scope:** The ~20 test construction updates across two files suggest this may be larger than Path A. Confirm no other plan also targets `http_transport.py` or its test files before proceeding.

10. **Fix Plan 101000 caller count error:** The plan claims "only one caller" but there are actually TWO callers of `retry_once_with_delay` in `startup_mcp_starter.py` (lines 96 and 138). REQ-004 must address both callers' compatibility.

11. **Verify Plan 104000 API accessibility:** The plan proposes `self._ctx.turn.background_tasks` but doesn't confirm that `turn` is an accessible attribute of `self._ctx` from within `ResourceShutdownCoordinator`. Verify the object graph before implementation.

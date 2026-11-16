## Goal

Remove the inline copy of the degraded-but-live rule from `McpServerStarter.verify_health` and delegate to `HealthChecker.is_degraded_but_live` (`REQ-002`: no copy of the rule; `REQ-004`: object body with `liveness` true stays degraded-but-live and every other non-200 enters the retry path; `REQ-005`: `verify_health` tests).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the embedded 503 parsing block in `McpServerStarter.verify_health` in `scripts/agent/startup_mcp_starter.py` and the companion test file `tests/agent/test_startup_mcp_starter.py`.
- Out of scope: the outer `except Exception` retry handling, the retry count and delay, `_verify_single_health`, and the predicate itself (document `01`).

## Assumptions

- Execute after document `01` of this Plan (the predicate must already be strict and non-raising) and after the Plan `startrev002` procedures: that Plan edits the `retry_once_with_delay` call at the end of `verify_health`, while this change replaces the inline block earlier in the same method; the edits touch different lines and neither changes what the other asserts (sequencing dependency; overlap judged compatible).
- `HealthChecker` is already imported in this module and used by `_verify_single_health`, so no import is added.
- The `MagicMock`-based 503 tests in `tests/agent/test_startup_mcp_lifecycle.py` (reference file) keep passing: a `MagicMock` response has status 503, `resp.headers.get(...)` returns a mock for which `"application/json" in ...` is false, so the predicate returns false and the path ends in the existing failure (re-read in Step 3a).
- Test file `tests/agent/test_startup_mcp_starter.py` is a companion: it is a Plan row under `tests/`, only the `startup_mcp_starter.py` row names it in `Related Tests` (besides itself), and its cases are fully specified by the Plan.

## Design decisions

- Replace the whole nested block (`resp.status_code == 503`, content-type check, `resp.json()`, `body.get("liveness", False)`, `except httpx.DecodingError`) with a single `HealthChecker.is_degraded_but_live(resp)` call; keep the "degraded but live" info log and the `continue`.
- Keep the outer `except Exception` handler: it also covers connection errors and feeds the unchanged retry path.

## Alternatives considered

N/A: the Plan fixes the design (one predicate, delegation).

## Implementation
### Target file
`scripts/agent/startup_mcp_starter.py`

### Procedure
1. In `verify_health`, inside the `resp.status_code != httpx.codes.OK` branch, replace the embedded 503 parse block with `if HealthChecker.is_degraded_but_live(resp):` that logs the existing "Post-startup health check: %r is degraded but live" message and `continue`s.
2. Leave `raise RuntimeError(f"HTTP {resp.status_code}")` after it, so any non-degraded non-200 still raises into the outer handler and the retry path.

### Method
- Keep the log message text and arguments exactly as they are.
- The predicate already checks the status code, so no separate `== 503` test remains in `verify_health`.
- The resulting method must contain no `resp.json()`, `body.get` or JSON-parsing code (`AC-2`).

### Details
- Radon: `verify_health` is C (15) today and loses branches with this change; it must not increase.
- Do not touch `_verify_single_health`, which already delegates to the predicate.

### Companion test files
- `tests/agent/test_startup_mcp_starter.py`
  - Procedure: add httpx-level cases with the file's `respx` and `_starter_ctx` helpers, written first and confirmed failing where they exercise non-object bodies: (a) a 503 JSON object with `liveness` true makes `verify_health` finish without retry (route call count 1); (b) a 503 non-object body (array and string) goes through the retry path and ends in the existing `[fatal]` error after three probes (one main probe plus the two `retry_once_with_delay` calls to `_verify_single_health`; measured 20261116-135632, correcting the earlier "two probes" wording); (c) a 503 object with `liveness` `"false"` goes through the retry path; (d) a behavioral check that the degraded decision is the predicate's: patching `HealthChecker.is_degraded_but_live` to return true makes `verify_health` accept a response the old inline copy would reject. Patch `agent.startup_mcp_starter.RETRY_DELAY_SEC` to a small value so the retry does not sleep for the production delay.
  - Validation: `uv run pytest tests/agent/test_startup_mcp_starter.py tests/agent/test_startup_mcp_lifecycle.py -q`.

## Compatibility considerations

- Object bodies behave as before; a non-object body or a non-boolean `liveness` now ends in the retry path and the fatal error with the HTTP status instead of depending on which exception escapes.
- The outer retry path and its messages are unchanged.

## Security considerations

- N/A: no new input handling; the untrusted body parsing is the predicate's (document `01`).

## Rollback considerations

- Revert the commit; this change is independent of the predicate rewrite and can be reverted alone.

## Validation plan

- `uv run pytest tests/agent/test_startup_mcp_starter.py tests/agent/test_startup_mcp_lifecycle.py -q`; the existing `MagicMock` 503 tests pass unchanged.
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check`; diff coverage per `rules/toolchain.md` section 7.

## Completion criteria

- `McpServerStarter.verify_health` contains no `body.get`, `resp.json()` or JSON-parsing code and delegates to `HealthChecker.is_degraded_but_live` (`REQ-002`, AC-2).
- A 503 object body with `liveness` true is accepted without retry; any other non-200 response enters the existing retry path and ends in the fatal error after the retry (`REQ-004`, AC-4).
- The new tests exist (`REQ-005`, AC-5) and AC-6 checks pass.

## Out of Scope

- Predicate changes, retry count or delay changes, documentation text, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `verify_health` httpx-level tests (companion `tests/agent/test_startup_mcp_starter.py`) | Completed | 20261116-135721 | 20261116-135823 | 4 httpx-level tests added; 2 failed pre-change as designed (non_boolean_liveness accepted truthy string; delegate check showed call_count 2) |
| 2 | Replace the inline degraded block in `verify_health` with a call to the shared predicate | Completed | 20261116-135839 | 20261116-135907 | inline 503 block replaced by HealthChecker.is_degraded_but_live; radon verify_health C 15->12 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-135907 | 20261116-140914 | ruff/lint-imports(6 kept)/mypy CI(567 files Success)/bandit(-ll High 0)/module-size/reference-table/mock-patch-targets all pass; targeted 58 passed; full suite 12376 passed/7 skipped; diff-cover 100%; ast-grep Not available |

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
- **Requirement ID**: `REQ-002` (no inline copy), `REQ-004` (degraded and retry behavior kept), `REQ-005` (`verify_health` tests)
- **Source issue**: issues/20261115-214907_startrev007_degraded-live-nondict-body.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-220700_startrev007_degraded-live-nondict-body.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095125
- **Related target files**: `scripts/agent/startup_mcp_starter.py`, `tests/agent/test_startup_mcp_starter.py`
## Goal
Create `tests/shared/test_mcp_health.py` covering `McpServerHealthRegistry`'s
state-transition logic, per `REQ-003` — confirmed via investigation that no
existing test exercises this state machine directly (existing references only
assert that `record_failure()`/`record_success()` are *called*, not that they
transition state correctly).

## Scope
- In scope: a new test file with unit tests for the 4 scenarios listed in
  `REQ-003` (a) through (d).
- Out of scope: modifying `scripts/shared/mcp_health.py` itself; testing any
  caller of `McpServerHealthRegistry` (already covered elsewhere, e.g.
  `tests/shared/test_tool_transport_invoker.py`).

## Assumptions
- `McpServerHealthRegistry` is a plain, synchronous, dependency-free class
  (confirmed via full read of `scripts/shared/mcp_health.py`) — it can be
  instantiated directly in a test with no fixtures, no DB, no async.
- `tests/shared/` has no `conftest.py` (confirmed via `ls`) — no shared fixture
  contract to conform to beyond standard pytest conventions.
- A short `half_open_cooldown_sec` (e.g. `0.01`) passed to the constructor is
  used to keep the cooldown-elapse test fast and deterministic, rather than
  mocking `time.monotonic()` — both are valid; the short-value approach is
  simpler for the constructor's own `half_open_cooldown_sec` parameter, which
  is designed to be caller-configurable for exactly this reason.

## Design decisions
- One test class matching the module's own two dimensions: failure
  accumulation/threshold behavior and success-reset behavior on one side,
  cooldown/`HALF_OPEN` trial behavior on the other — or a flatter set of
  function-level tests; either is acceptable as long as all 4 `REQ-003`
  scenarios are covered. Match this repository's prevailing style in sibling
  `tests/shared/test_*.py` files (plain `def test_...` functions or classes,
  whichever that directory's existing files predominantly use).
- Test scenario (a): construct with `failure_threshold=3` (the default);
  assert `record_failure()` returns `DEGRADED` for the first 2 calls and
  `UNAVAILABLE` on the 3rd.
- Test scenario (b): after reaching `DEGRADED` or `UNAVAILABLE`, call
  `record_success()`; assert `get_state()` returns `HEALTHY` and that a
  subsequent `record_failure()` call again returns `DEGRADED` (not
  `UNAVAILABLE`), proving the failure count was reset to 0, not merely the
  state.
- Test scenario (c): drive a server to `UNAVAILABLE`, then use a short
  `half_open_cooldown_sec`; sleep past it (or otherwise let it elapse); call
  `is_unavailable()` and assert it returns `False` (the "one trial dispatch"
  signal) and that `get_state()` now reports `HALF_OPEN`; call `is_unavailable()`
  again immediately after and assert it now returns `True` again per the
  actual method's documented one-shot semantics — read
  `scripts/shared/mcp_health.py`'s `is_unavailable()` docstring again at
  implementation time to confirm this exact repeated-call behavior before
  asserting it, since the docstring itself warns "Callers must not assume
  repeated calls are idempotent."
- Test scenario (d): from `HALF_OPEN` (reached via scenario c's setup), call
  `record_failure()`; assert it returns `UNAVAILABLE` (not `DEGRADED`,
  regardless of the accumulated failure count), and that a fresh
  `is_unavailable()` call immediately after returns `True` (cooldown reset —
  confirm via the `_unavailable_since` reset by re-reading `record_failure()`'s
  `was_half_open` branch, not by inspecting the private attribute directly in
  the test — assert through the public `is_unavailable()` behavior instead).

## Alternatives considered
- Mock `time.monotonic()` instead of using a short real cooldown value —
  either works; a short real value is simpler and avoids coupling the test to
  the module's internal use of `time.monotonic()` specifically (an
  implementation detail that could change to `time.time()` without breaking a
  black-box test).

## Implementation
### Target file
`tests/shared/test_mcp_health.py`

### Procedure
1. Re-verify (idempotent recheck) that `tests/shared/test_mcp_health.py` still
   does not exist, and that `scripts/shared/mcp_health.py`'s public interface
   (`McpServerHealthRegistry.__init__(failure_threshold, half_open_cooldown_sec)`,
   `.record_failure()`, `.record_success()`, `.get_state()`,
   `.is_unavailable()`) is unchanged from this Plan's evidence-gathering.
2. Write the new test file with tests covering scenarios (a)-(d) above, using
   the module's real classes (`McpServerHealthRegistry`, `McpServerHealthState`)
   imported from `shared.mcp_health` (confirm the exact import path other
   `tests/shared/*.py` files use for `scripts/shared/*.py` modules — likely
   `from shared.mcp_health import ...` given the `PYTHONPATH=scripts` convention
   this repository uses).
3. Add a module-level docstring stating the file's purpose (state-transition
   coverage for `McpServerHealthRegistry`, added to close the gap `REQ-003`
   identified).

### Method
Write the file directly (new file, no existing content to preserve).

### Details
- Follow `rules/coding.md` conventions: comments/log output in English if any
  are added (test docstrings and assertions are the primary content), no bare
  `except:`, f-strings preferred.
- Do not import or depend on any fixture from a different test module.

## Compatibility considerations
N/A: new test file; does not change `scripts/shared/mcp_health.py`'s behavior
or public contract.

## Security considerations
N/A: no credentials, secrets, or external calls involved — pure in-memory
state-machine testing.

## Rollback considerations
New file — revert by deleting it (`git rm tests/shared/test_mcp_health.py` or
`git checkout` if already committed) if validation fails; no other file
depends on its existence yet at this point in the cycle (the sibling ADR-007
procedure's citation is added after this one, per Implementation Target Files
order).

## Validation plan
- `uv run pytest tests/shared/test_mcp_health.py -v` — all new tests pass.
- `uv run ruff format tests/shared/test_mcp_health.py && uv run ruff check tests/shared/test_mcp_health.py` — clean.
- `uv run mypy tests/shared/test_mcp_health.py` — no new errors.
- `uv run bandit tests/shared/test_mcp_health.py` — no findings (pure unit test, no subprocess/network/file I/O expected).

## Completion criteria
- All 4 scenarios `(a)`–`(d)` from `REQ-003` are covered by passing tests.
- `uv run pytest tests/shared/test_mcp_health.py -v` passes with at least 4
  collected tests (not 0-collected).
- Lint/type/security checks pass per Validation plan.

## Out of scope
- `scripts/shared/mcp_health.py` itself.
- `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` — covered by
  the sibling procedure,
  `implementations/20260915-190812_01_docs_adr_ADR-007-http-mcp-adoption-and-stdio-non-support.md.md`.
- Any caller of `McpServerHealthRegistry`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-190812 | 20260915-191407 | Created tests/shared/test_mcp_health.py with 9 tests covering all 4 REQ-003 scenarios; found and fixed a timing mismatch bug in test_failed_trial_resets_cooldown (cooldown 0.05s vs shared helper's fixed 0.02s sleep never elapsing) during Step 3e validation |
| 2 | Add or update tests per Validation plan | Completed | 20260915-191407 | 20260915-191407 | This step IS the test creation — see Step 1 This step IS the test creation, per procedure Notes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-191407 | 20260915-191407 | Use this document's own Validation plan (ruff/mypy/bandit/pytest) ruff format/check: clean; mypy: no issues; bandit: 19 B101 (assert_used) findings, confirmed identical accepted pattern in sibling tests/shared/test_tool_transport_invoker.py (15 similar findings); pytest: 9/9 passed, re-run 5x with no flakiness |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-191407 | 20260915-191407 | N/A: test-only change, no documentation update required for this file itself (the ADR-007 documentation update is the sibling procedure's responsibility) N/A: test-only change, no documentation update for this file itself |

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
- **Requirement ID**: REQ-003 — new test file covering McpServerHealthRegistry state transitions
- **Source issue**: issues/done/20260914-124601_docqa04_adr-007-circuit-breaker-states-not-in-invariants.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-190322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-190812
- **Related target files**: tests/shared/test_mcp_health.py
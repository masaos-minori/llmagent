# test_git_security_compliance.py fails only when run as part of the full file/suite, not in isolation (shared mutable git_server state)

## Priority
Medium

## Summary
13-14 tests in `tests/mcp_servers/git/test_git_security_compliance.py` fail when the file
runs as part of the full test suite or as a whole file, but individually-verified tests
from the same failing set (e.g.
`TestLiveCallToolAuthorization::test_checkout_protected_branch_denied`) pass when run
alone. Running the whole file with `-p no:randomly` (disabling `pytest-randomly`'s random
ordering) still produces 14 failures — a different-but-overlapping set from the
random-seed run (13-14 failures each time, exact members vary) — confirming this is
order-dependent state leakage within the file itself, not a random-seed-specific fluke and
not a single deterministic bug reproducible from any one test's own logic.

## Background
Confirmed via a `git worktree` checkout of `origin/master` at commit `df4a58671` that this
class of failure reproduces on that commit alone, unrelated to this session's own (Agent/
EventBus reference-table) work rebased on top of it afterward. Failures span several
unrelated test classes in the file (`TestDryRunAndDetachedHeadLivePath`,
`TestRemoteAuthorizationViaHTTP`, `TestLiveCallToolAuthorization`,
`TestGitServiceErrorHandlerIdentity`, `TestNewlyReachableToolsViaHTTP`), which is
consistent with shared state corruption rather than several independent bugs in each
class.

## Problem
Multiple tests in this file directly mutate module-level singletons —
`scripts.mcp_servers.git.git_server._cfg` and `git_server._service` (e.g.
`_cfg.allowed_repo_paths`, `_service._allowed_repo_paths`, `_cfg.allow_detached_head`,
`_service._allow_detached_head`, `_cfg.read_only`, `_service._read_only`) — saving and
restoring the originals in a `try/finally`. If any test's save/restore is incomplete
(missing one of the parallel `_cfg`/`_service` copies — the file's own comments already
note `_service` is "a `GitService` instance built once at import time from `_cfg`'s
then-current value" and is "unaffected by patching `_cfg`", i.e. there are at least two
copies of each flag to keep in sync), or if a test raises before reaching its `finally`,
a later test in the same run can observe stale/wrong `allowed_repo_paths`/
`allow_detached_head`/`read_only` values left over from an earlier test — exactly the
category of symptom observed (e.g. one such failure's setup log showed `allowed_repo_paths
is empty — all repo access denied`, and another showed a checkout still denied as
"detached HEAD" immediately after the test had set `allow_detached_head = True` on both
known copies).

## Reason for Change
A test file whose failures depend on execution order provides unreliable, non-reproducible
CI signal — the exact set of tests that "pass" or "fail" changes between runs (this
investigation observed both 13 and 14 failing, with different exact members, across two
different orderings). This erodes confidence in this file's coverage of the git MCP
server's security-critical authorization/detached-HEAD/dirty-worktree checks, and risks
either masking a real regression (a failure dismissed as "flaky") or wasting investigation
time on a phantom failure.

## Implementation Intent
Identify every place `_cfg`/`_service` (or any other module-level mutable singleton this
file's tests patch) is saved/restored, and either (a) fix every incomplete or
exception-unsafe save/restore so state is always fully restored regardless of test
outcome, or (b) replace the manual save/restore pattern with a `pytest` fixture
(`autouse` for this file, or applied per affected class) that snapshots and restores all
relevant `_cfg`/`_service` attributes automatically via `yield` + teardown, removing the
duplicated manual bookkeeping from each test. Prefer (b) if the number of distinct
attributes being patched across tests is large enough that manual `try/finally` blocks are
themselves error-prone (the evidence above suggests they already are). Do not silently
skip or mark these tests `xfail` — the underlying design/state-isolation gap should be
fixed, not hidden.

## Target Files or Areas
- `tests/mcp_servers/git/test_git_security_compliance.py` (multiple test classes)
- `scripts/mcp_servers/git/git_server.py` (module-level `_cfg`/`_service` singletons — read
  only, to confirm the full set of mutable attributes tests need to isolate)

## Required Changes
- Enumerate every `_cfg.*`/`_service.*` attribute any test in this file mutates.
- Introduce a fixture (or fix each existing `try/finally`) that guarantees full
  save/restore of all of them around every test that mutates any of them, independent of
  whether the test raises.
- Verify the fix by running the full file repeatedly with different `pytest-randomly`
  seeds (e.g. `--randomly-seed=1`, `--randomly-seed=2`, and the default random seed) and
  confirming a stable 0-failure result each time, not just once.

## Constraints
Do not change `scripts/mcp_servers/git/git_server.py`'s production `_cfg`/`_service`
architecture (e.g. do not merge the two into one object) as part of this fix unless
investigation shows that dual-copy design is itself the root defect rather than merely a
test-isolation gap — that would be a separate, larger change requiring its own review.

## Acceptance Criteria
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q` reports 0
  failures, run at least 3 times with different random seeds
  (`-p randomly --randomly-seed=<N>` for at least 2 different `N`, plus the default
  random run) with a stable 0-failure result each time.
- Running any single previously-failing test in isolation still passes (already true
  today — must remain true).

## Testing Expectations
Run `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q` multiple
times with different seeds as described above; also run the full `uv run pytest tests/ -q`
to confirm no new failures are introduced elsewhere.

## Documentation Impact
N/A: test-isolation fix, no production behavior or public API change.

## Out of Scope
Any other failing test file identified in the same investigation
(`tests/agent/test_orchestrator.py`, `tests/agent/services/test_config_reload.py`,
`tests/eventbus/test_eventbus_auth.py`,
`tests/agent/services/test_mcp_tool_discovery.py`) — each is tracked as its own issue.
Any production change to `scripts/mcp_servers/git/git_server.py`'s `_cfg`/`_service`
dual-copy architecture beyond what test isolation strictly requires.

## Dependencies
N/A: none.

## Unresolved Questions
- The exact earlier test (or tests) whose incomplete save/restore first corrupts shared
  state was not identified via bisection in this investigation — left as the implementer's
  first step (e.g. via `pytest --randomly-seed=<same seed that failed>` combined with
  `-x` and progressively narrowing the test selection, or by auditing every `finally`
  block by hand for a missing attribute).
- Whether `_service`'s "built once at import time from `_cfg`'s then-current value" design
  has additional un-audited copies beyond `_allowed_repo_paths`/`_read_only`/
  `_allow_detached_head` (e.g. inside a nested `RepositoryState`/`RepoValidationResult`
  object, given a `RepoValidationResult is deprecated; use RepositoryState instead`
  deprecation warning was observed during this investigation) is not confirmed.

## AI Implementation Instruction
Start by auditing every test in this file that reads or writes `git_server._cfg`/
`git_server._service` attributes, listing the full set of attributes involved before
deciding between a shared fixture and per-test `try/finally` fixes. Verify the fix with
multiple different random seeds, not a single run — a single passing run does not prove
the ordering issue is resolved. Do not silently reorder or skip failing tests as a
workaround.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-164345
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py, scripts/mcp_servers/git/git_server.py

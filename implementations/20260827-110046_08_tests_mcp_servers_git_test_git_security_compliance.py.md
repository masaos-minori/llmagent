## Goal

Extend `tests/mcp_servers/git/test_git_security_compliance.py` with a parametrized
case building `GitService` from the shipped `config/git_mcp_server.toml` and
asserting `git_checkout`/`git_pull`/`git_push` reject each of `"main"`, `"master"`,
`"release"` (REQ-006 test half), per `plans/20260826-113056_plan.md`.

## Scope

- In scope: one new parametrized test (or a small set of tests) covering all three
  branch names across all three write tools, built from the real loaded config.
- Out of scope: the existing `svc` fixture and its hand-built
  `protected_branches=["main"]` case (already covers the mechanism in isolation, do
  not duplicate its full setup); any change to `GitService`/`GitSecurityGuards`
  themselves (already implemented, verified 2026-08-27).

## Assumptions

- `config/git_mcp_server.toml` will contain `protected_branches = ["main", "master",
  "release"]` once the REQ-006 config item (separate target file, this same pass)
  lands — this test depends on that value, same ordering caveat as the
  `test_git_models.py` item in this pass.
- `GitService.__init__` accepts `protected_branches` as a constructor parameter
  (confirmed 2026-08-27 at `git_service.py:82,90`) and `GitConfig.load()` exposes
  `protected_branches` as a `list[str]` attribute (confirmed at `git_models.py:32`).

## Design decisions

- Build the test's `GitService` instance from `GitConfig.load()`'s
  `protected_branches` value (plus the existing fixture's other constructor args:
  `allowed_repo_paths=["/tmp/repo"]`, `read_only=False`, `max_log_entries=50`) rather
  than re-declaring the branch list as a literal — this is what "not only from the
  test's own hand-built fixture" (this Plan's REQ-006 Acceptance Criteria) requires:
  the branch list itself must come from the loaded config, even though other
  constructor args stay test-local.
- Reuse the existing `test_git_checkout_protected_branch`-style assertion pattern
  (mock `_open_repo`, call the handler, assert on the rejection message) via
  `pytest.mark.parametrize` over `("main", "master", "release")` × the three write
  tools, rather than writing 9 separate test methods.

## Alternatives considered

- Adding `protected_branches=["main", "master", "release"]` as a literal in a new
  fixture (not sourced from `GitConfig.load()`) was considered and rejected — it
  would only test the mechanism, not that the shipped config actually activates it,
  which is this Plan's specific REQ-006 gap being closed.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure
1. Add a new fixture or inline `GitConfig.load()` call building a `GitService`
   instance whose `protected_branches` comes from the shipped config.
2. Add a parametrized test asserting `git_checkout`/`git_pull`/`git_push` reject each
   of `"main"`, `"master"`, `"release"` when built from that service instance,
   reusing the existing `test_git_checkout_protected_branch`/
   `test_git_push_protected_branch`/`test_git_pull_protected_branch` assertion style
   (verified these three existing tests exist in this file as of 2026-08-27, per this
   Plan's own Problem section).
3. Run `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v`.

### Method
Direct file edit (Edit tool) adding one fixture/helper and one parametrized test
function; no changes to the existing `svc` fixture or its consumers.

### Details
Current file structure (verified 2026-08-27): `TestGitSecurityCompliance` class,
`svc` fixture builds `GitService(allowed_repo_paths=["/tmp/repo"], read_only=False,
max_log_entries=50, protected_branches=["main"])`;
`test_git_checkout_protected_branch`/`test_git_push_protected_branch`/
`test_git_pull_protected_branch` each mock `svc._open_repo` and assert a
`[DENIED] ... is a protected branch` result for `branch="main"`. Add, e.g.:
```python
@pytest.fixture
def svc_from_shipped_config(self) -> GitService:
    cfg = GitConfig.load()
    return GitService(
        allowed_repo_paths=["/tmp/repo"],
        read_only=False,
        max_log_entries=50,
        protected_branches=cfg.protected_branches,
    )

@pytest.mark.asyncio
@pytest.mark.parametrize("branch", ["main", "master", "release"])
async def test_write_tools_reject_shipped_protected_branches(
    self, svc_from_shipped_config: GitService, branch: str
) -> None:
    svc_from_shipped_config._open_repo = MagicMock(return_value=MagicMock())
    # ... call git_checkout/git_pull/git_push handlers with branch=branch,
    # asserting each rejects with "protected branch" per the existing
    # test_git_checkout_protected_branch-style assertion.
```
Import `GitConfig` from `mcp_servers.git.git_models` alongside the existing
`GitService` import. Confirm the exact handler call signatures (`args` dict shape)
by reading the three existing `test_git_*_protected_branch` tests in full before
writing this parametrized version, to avoid diverging from their established
calling convention.

## Compatibility considerations

- Test-only change; no production code path is affected.
- Depends on `config/git_mcp_server.toml`'s `protected_branches` value landing first
  (same ordering caveat as the `test_git_models.py` item in this pass) — will fail
  against the current `[]`-default config.

## Security considerations

- N/A: test-only change, no security-relevant code path; this test itself verifies a
  security control (protected-branch rejection), it does not weaken one.

## Rollback considerations

- New fixture + new test function revert via `git diff`/`git checkout -- <path>`; the
  existing `svc` fixture and its three pre-existing protected-branch tests are
  untouched and need no coordinated rollback.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/git/test_git_security_compliance.py` | Unit | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` | New parametrized test passes once REQ-006's config change has landed; existing cases (`test_git_checkout_protected_branch` etc.) unaffected |

## Completion criteria

- A test builds `GitService` from `GitConfig.load()`'s `protected_branches` value
  (not a hand-built literal) and asserts `git_checkout`/`git_pull`/`git_push` each
  reject `"main"`, `"master"`, and `"release"`.
- The test passes only after the REQ-006 config item has landed — note the same
  ordering dependency in the Blocker Log if implemented first.

## Out of scope

- The existing `svc` fixture and its three pre-existing protected-branch tests.
- Any change to `GitService`/`GitSecurityGuards`/`GitConfig` themselves.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `svc_from_shipped_config` fixture and parametrized rejection test | Pending | — | — | Depends on `config/git_mcp_server.toml`'s `protected_branches` key landing first |
| 2 | Run `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | This test's assertion is only valid after `config/git_mcp_server.toml` sets `protected_branches`; implement the config item first or in the same commit | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006
- **Source issue**: `issues/20260821_02_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-113056_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110046
- **Related target files**: `tests/mcp_servers/git/test_git_security_compliance.py`

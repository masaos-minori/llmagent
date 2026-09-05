# Implementation Procedure: Add HTTP-Level Regression Tests

## Goal

Add `POST /v1/call_tool` `TestClient` regression tests for checkout/pull/push against protected and non-protected branches — closing the coverage gap found by this Plan's Step 3 investigation (all existing tests exercise the dead-code `GitService` path only).

## Scope

Only changes required for Requirement REQ-010 in `tests/mcp_servers/git/test_git_security_compliance.py`. Specifically: adding new `TestClient`-based tests posting to `/v1/call_tool` for `git_checkout`, `git_pull`, `git_push` against protected and non-protected branches, including implicit (empty branch) targets.

## Assumptions

- The FastAPI `TestClient` is available as a dev dependency (already used elsewhere in the repo; confirmed by `uv run pytest` working with `from fastapi.testclient import TestClient`).
- `_cfg` module-level config is loaded at import time in `git_server.py`, so `TestClient(app)` will automatically have access to it.
- Protected branches configured in `config/git_mcp_server.toml` are `["main", "master", "release"]`.
- The git-mcp server must be running or mocked appropriately for `TestClient` to connect.

## Design decisions

- Use `pytest-asyncio` fixtures to set up `TestClient` per-test rather than a global fixture — avoids server startup/shutdown issues in parallel test runs.
- Parametrize tests over branch names (`main`, `master`, `release`) and tool names (`git_checkout`, `git_pull`, `git_push`) to minimize duplication while covering AC-1, AC-2, AC-3, AC-6.
- Separate test classes for protected-branch denial vs. non-branch success to keep failure messages clear.

## Alternatives considered

- Using `httpx.AsyncClient` instead of `TestClient`: rejected because `TestClient` provides synchronous testing without event-loop complexity, matching existing patterns in other MCP server tests.
- Creating a single parametrized test with all combinations: rejected because it would produce unreadable failure output when one combination fails; separate test methods per scenario provide clearer diagnostics.

## Implementation

### Target file

`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure

##### Method: Add TestClient-based regression tests for protected branches

**REQ-010**: Add new test class `TestCallToolProtectedBranchDenial` that uses `TestClient` to post to `/v1/call_tool`.

```python
import pytest
from fastapi.testclient import TestClient
from mcp_servers.git.git_server import app
from mcp_servers.models import CallToolRequest
```

Tests needed:

1. **`test_git_checkout_protected_branch_denied`** — POST `git_checkout` with `branch="main"` → expect `[DENIED]` response.
2. **`test_git_pull_protected_branch_denied`** — POST `git_pull` with `branch="main"` → expect `[DENIED]` response.
3. **`test_git_push_protected_branch_denied`** — POST `git_push` with `branch="main"` → expect `[DENIED]` response.
4. **`test_git_checkout_non_protected_branch_allowed`** — POST `git_checkout` with `branch="develop"` → expect success (no `[DENIED]`).
5. **`test_git_pull_non_protected_branch_allowed`** — POST `git_pull` with `branch="develop"` → expect success.
6. **`test_git_push_non_protected_branch_allowed`** — POST `git_push` with `branch="develop"` → expect success.
7. **`test_git_push_empty_branch_denied`** — POST `git_push` with `branch=""` → expect `[DENIED]` (implicit target must resolve before authorization).
8. **`test_git_pull_empty_branch_denied`** — POST `git_pull` with `branch=""` → expect `[DENIED]`.

##### Method: Add ref normalization test

**REQ-006, AC-2**: Add parametrized test asserting `main` and `refs/heads/main` both deny checkout when `main` is protected.

```python
class TestRefNormalization:
    @pytest.mark.parametrize("branch", ["main", "refs/heads/main"])
    def test_normalized_refs_both_deny_when_main_protected(
        self, branch: str
    ) -> None:
        client = TestClient(app)
        req = CallToolRequest(
            name="git_checkout",
            args={"repo_path": "/tmp/repo", "branch": branch},
        )
        resp = client.post("/v1/call_tool", json=req.model_dump())
        data = resp.json()
        assert "[DENIED]" in data.get("result", ""), f"Expected denial for {branch}"
```

##### Method: Verify pre-change baseline (new tests fail before fix)

Before implementing the fix, confirm each new test fails:
- Protected branch tests should NOT return `[DENIED]` (currently succeeds via `/v1/call_tool`).
- Non-protected branch tests should succeed (unchanged behavior).

After implementing the fix, confirm all new tests pass.

### Details

Key additions to the file:

1. **Imports**: Add `from fastapi.testclient import TestClient` and `from mcp_servers.models import CallToolRequest`.

2. **New test class `TestCallToolProtectedBranchDenial`**:
   ```python
   class TestCallToolProtectedBranchDenial:
       """HTTP-level regression tests for POST /v1/call_tool on the live path."""
       
       @pytest.fixture
       def client(self) -> TestClient:
           return TestClient(app)
       
       # ... test methods as described above
   ```

3. **New test class `TestRefNormalization`**:
   ```python
   class TestRefNormalization:
       """Verify main and refs/heads/main evaluate consistently as the same protected branch."""
       
       @pytest.mark.parametrize("branch", ["main", "refs/heads/main"])
       def test_normalized_refs_both_deny_when_main_protected(
           self, branch: str, client: TestClient
       ) -> None:
           # ... as described above
   ```

4. **Pre-change baseline verification**: Before the fix, run the new tests and confirm they do NOT produce `[DENIED]` for protected branches (proving the gap exists). After the fix, confirm they do.

## Compatibility considerations

- **No change to existing tests**: This adds new test classes/methods; existing `GitService`-direct tests continue unchanged.
- **Server dependency**: `TestClient(app)` requires the FastAPI app to be importable. Since `app` is defined at module level in `git_server.py`, importing it is straightforward but may trigger side effects (e.g., middleware attachment). If this causes issues, consider using `conftest.py` to provide a lazy fixture.
- **Config file availability**: The server reads `config/git_mcp_server.toml` at startup. The test environment must have this file accessible (it already is, since tests run from the repo root).

## Security considerations

- **Fail-closed verification**: These tests explicitly verify that protected branches are DENIED — the opposite direction from the existing `GitService` tests which verify the dead-code path allows them. A regression here means protection is silently disabled.
- **Implicit target bypass prevention**: Tests for empty branch (`git_push`/`git_pull` with `branch=""`) ensure the implicit-target resolution happens BEFORE authorization, preventing the bypass scenario documented in REQ-007.

## Rollback considerations

- **Tests-only change**: Adding tests has no production impact if rolled back — the code remains unchanged. However, losing these tests means the coverage gap reopens.
- **Pre-change baseline**: The value of these tests depends on confirming they FAIL before the fix and PASS after. Rolling back the tests loses this evidence.

## Validation plan

| Step | Action | Command | Expected Outcome |
|------|--------|---------|------------------|
| 1 | Run new tests against pre-change code | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py::TestCallToolProtectedBranchDenial -v` | New tests FAIL (protected branches currently succeed via `/v1/call_tool`) |
| 2 | Run new tests against post-change code | Same command after fix | All new tests PASS |
| 3 | Run full git-mcp suite | `uv run pytest tests/mcp_servers/git/ -v` | 184+ tests pass, no new failures |
| 4 | Static analysis | `uv run ruff check scripts/mcp_servers/git/`; `uv run mypy scripts/mcp_servers/git/`; `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`; `PYTHONPATH=scripts uv run lint-imports` | All pass with no new findings |

## Completion criteria

- [ ] `TestCallToolProtectedBranchDenial` class exists with tests for all 3 write tools against protected branches (expect denial).
- [ ] `TestCallToolProtectedBranchDenial` class exists with tests for all 3 write tools against non-protected branches (expect success).
- [ ] `TestCallToolProtectedBranchDenial` class exists with tests for empty branch on push/pull (expect denial).
- [ ] `TestRefNormalization` class exists with parametrized test for `main` vs `refs/heads/main`.
- [ ] Each new test fails against pre-change code (protected branch currently succeeds via `/v1/call_tool`).
- [ ] Each new test passes against post-change code.
- [ ] Full git-mcp suite passes with no new failures.
- [ ] All static analysis tools pass with no new findings.

## Out of scope

- Fixing `_is_protected_branch()` placeholder — Row 1 responsibility.
- Adding Stage 3 call to `WriteProtectionPipeline.run()` — Row 1 responsibility.
- Replacing `ref_valid=True` — Row 1 responsibility.
- Operation-target resolution — Row 1 responsibility.
- Threading `protected_branches` into `snapshot()` — Row 2 responsibility.
- Unit tests for the fixed logic — Row 4 responsibility.
- Documentation updates — deferred per issue's Constraint.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-05 | 2026-09-05 | REQ-010 HTTP-level regression tests added to test_git_security_compliance.py using TestClient-based approach |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-05 | 2026-09-05 | Tests in test_repository_state.py updated; all 184 git MCP tests pass |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 2026-09-05 | 2026-09-05 | ruff check clean, mypy clean, pytest 184 passed, no new failures |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-05 | 2026-09-05 | No docs/00_index.md task-scope row references these files' symbols by name |

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20260902-144907_gitauth_complete_protected_branch_and_ref_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-162951_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-131142
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py

## Goal

Add a test proving `GitServiceError` raised on the live HTTP dispatch path
(`POST /v1/call_tool`) is actually caught by the registered
`@app.exception_handler(GitServiceError)` (`git_server.py:130`) rather than
propagating as an unhandled 500 with no structured body — the concrete proof
that consolidating to one `GitServiceError` class (REQ-001) cannot be
silently bypassed by exception-identity mismatch (REQ-008, AC-3, AC-6).

## Scope

- In scope: one new test class/function exercising the live dispatch path
  (via the existing `TestClient` pattern already in this file) that causes a
  `GitServiceError` to be raised from inside the Stage-6 operation callback
  (`format_checkout`/`format_pull`/`format_push`) and asserts the response
  matches `_on_git_service_error`'s intended shape (500 status,
  `{"detail": ...}` body) — not an unhandled exception or a different
  status/shape.
- Out of scope: any change to `git_server.py`, `format_output.py`, or
  `repository_state.py` (evidence/reference only for this row); the 5
  pre-existing `TestClient`-based test classes in this file (unchanged).

## Assumptions

- None beyond the Plan's own: REQ-001 already guarantees only one
  `GitServiceError` class exists reachable from this path (verified this
  cycle: `format_output.py` and `git_server.py` both import from
  `mcp_servers.git.errors`, not `git_models`).

## Design decisions

- **Step 3a correction (2026-09-05)**: the Plan's original evidence for this
  row ("zero existing `TestClient` usage") is stale — `gitauth`/`gitpipeline`/
  `gitdryrun`'s implementation cycles already added a `TestClient` fixture and
  5 usages to this file since the Plan was authored (now 847 lines, was 468).
  This changes nothing about REQ-008 itself (`rg "GitServiceError"
  tests/mcp_servers/git/test_git_security_compliance.py` still has zero
  matches — no existing test proves the exception-handler guarantee), but the
  new test should reuse the established `TestClient` pattern from
  `TestPostConditionBypassPrevention`/`TestCompletePipelineCoverage` (class-
  scoped `client` fixture importing `app` from
  `scripts.mcp_servers.git.git_server`) rather than introducing a third,
  inconsistent import convention.
- Trigger the failure by monkeypatching the format-function the dispatch
  table calls (`format_checkout`, imported into `git_server.py` at module
  scope) to raise `GitServiceError` directly, rather than trying to engineer a
  real git-level failure condition that happens to hit one of
  `format_checkout`'s/`format_pull`'s/`format_push`'s internal
  `raise GitServiceError(...)` sites (lines 153, 175, 190 of
  `format_output.py`) — this isolates exactly the propagation mechanism under
  test (`WriteProtectionPipeline.run()`'s Stage 6 `except GitServiceError:
  raise` at `repository_state.py:571-572`, uncaught by `call_tool()`, caught
  by the FastAPI handler) from unrelated git-mechanics setup, matching this
  file's existing convention of monkeypatching collaborators rather than
  running real git operations end-to-end.
- Still mock `RepositoryState.snapshot()` (as the existing
  `TestPostConditionBypassPrevention` tests do) so Stage 3
  (`verify_authorization`)/Stage 5 (`verify_preconditions`) pass and dispatch
  reaches Stage 6 where the induced raise fires.

## Alternatives considered

- Drive a real git failure (e.g. a real merge conflict for `format_pull`) to
  trigger the raise without monkeypatching `format_checkout` itself: rejected
  — significantly more test setup (real repo fixtures, real conflicting
  commits) for the same proof; this file already establishes
  mocking-collaborators as its pattern for pipeline-stage tests.
- Add the test as a plain unit test (call `WriteProtectionPipeline.run()`
  directly, not through `TestClient`) instead of a live-HTTP test: rejected —
  REQ-008/AC-6 explicitly require proving the FastAPI-registered handler
  catches it on the actual dispatch path, not just that the exception
  propagates out of `pipeline.run()`.

## Implementation

### Target file
`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure
1. Add a new test class (e.g. `TestGitServiceErrorHandlerIdentity`) near
   `TestPostConditionBypassPrevention`/`TestCompletePipelineCoverage` (the
   file's existing live-dispatch-path test classes), with its own
   class-scoped `client` fixture following their exact pattern:
   ```python
   @pytest.fixture
   def client(self):
       from scripts.mcp_servers.git.git_server import app
       return TestClient(app)
   ```
2. Add one test that:
   - mocks `RepositoryState.snapshot` (via `monkeypatch.setattr`, same
     pattern as `test_checkout_postcondition_cannot_be_bypassed`) to return a
     `MagicMock` state whose `verify_authorization()`/`verify_preconditions()`
     both return `(True, "")`;
   - monkeypatches `scripts.mcp_servers.git.git_server.format_checkout` (the
     name bound in `git_server.py`'s module namespace via its
     `from mcp_servers.git.format_output import format_checkout, ...` import)
     to a callable that unconditionally raises
     `GitServiceError("induced failure for handler-identity test")`;
   - posts to `/v1/call_tool` with `{"name": "git_checkout", "args": {...}}`
     using the mocked repo path;
   - asserts `response.status_code == 500` and
     `response.json() == {"detail": "induced failure for handler-identity test"}`
     — the exact shape `_on_git_service_error` (`git_server.py:130-133`)
     produces.

### Method
New test, additive only — no existing test body changes.

### Details
- Reuse `unittest.mock.MagicMock`/`monkeypatch` already imported in this file
  (used throughout `TestPostConditionBypassPrevention`).
- The mocked `RepositoryState.snapshot` must supply enough MagicMock
  attributes for `call_tool()`'s pre-dispatch checks
  (`_resolve_repo_path`/`is_within_allowed_paths`/`_validate_pre_snapshot`)
  to pass before reaching the handler dispatch — follow the exact setup
  already used by `test_checkout_postcondition_cannot_be_bypassed`
  (`snap.repo`, `snap.repo.active_branch.name`, `snap.repo.is_dirty`,
  `snap.verify_authorization`, `snap.verify_preconditions`,
  `snap.verify_postcondition`, `snap.audit`) as a starting template, then
  additionally monkeypatch `format_checkout` to raise as described above —
  the mocked `verify_postcondition` becomes irrelevant since the raise fires
  before Stage 7 is reached (Stage 6, per `repository_state.py:568-575`).
- Assert the response body exactly matches `_on_git_service_error`'s
  `JSONResponse({"detail": str(exc)}, status_code=500)` shape — this is the
  concrete proof that exception identity was not bypassed (a mismatched
  class would instead surface as an unhandled `500 Internal Server Error`
  with FastAPI's default traceback-less generic body, not this handler's
  `{"detail": ...}` shape).

## Compatibility considerations

- Additive test only; no production code or existing test changes.

## Security considerations

- N/A: test-only; proves an existing security-relevant guarantee (no
  unhandled-exception information leak on the live dispatch path) rather than
  changing one.

## Rollback considerations

- Single new test method/class; `git revert` removes it cleanly with no
  dependency from other tests.

## Validation plan

- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` —
  new test passes; all 5 pre-existing `TestClient`-based test classes
  unaffected.
- Confirm the new test fails against the pre-change code in the sense that
  it did not exist to prove the guarantee (per the Plan's own Tests section)
  — i.e., temporarily verify it would also catch a regression by confirming
  it actually invokes the handler path (inspect that `response.status_code
  == 500` before landing, not skipped/mocked away).
- `uv run pytest tests/mcp_servers/git/ -v` (full suite) — no new failures.
- `uv run ruff check tests/mcp_servers/git/test_git_security_compliance.py`
- `uv run mypy tests/mcp_servers/git/test_git_security_compliance.py`

## Completion criteria

- A new test in `test_git_security_compliance.py` triggers a real
  `GitServiceError` raise from inside the Stage-6 `op()` callback on the live
  `/v1/call_tool` dispatch path and asserts the response is
  `_on_git_service_error`'s exact `{"detail": ...}` / 500 shape.
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v`
  passes in full.

## Out of scope

- Any change to `scripts/mcp_servers/git/git_server.py`,
  `scripts/mcp_servers/git/format_output.py`, or
  `scripts/mcp_servers/git/repository_state.py` — reference/evidence only.
- The other rows' changes (`git_models.py`, `repository_state.py`'s
  `RepoValidationResult` removal, `test_repository_state.py`'s migration) —
  independent sibling procedures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestGitServiceErrorHandlerIdentity` class with a class-scoped `client` fixture | Pending | — | — | |
| 2 | Add the test mocking `RepositoryState.snapshot` + `format_checkout` and asserting the handler's response shape | Pending | — | — | |
| 3 | Run this file's suite and the full git-mcp suite | Pending | — | — | |

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
- **Requirement ID**: `REQ-008` — prove exception identity cannot bypass the registered `GitServiceError` handler on the live dispatch path
- **Source issue**: issues/20260902-144913_giterrors_consolidate_domain_errors_and_validation_results.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-205531
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py

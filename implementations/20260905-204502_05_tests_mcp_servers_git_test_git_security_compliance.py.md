## Goal
Add live-path (`TestClient`) tests proving `git_pull`/`git_push` reject an unknown/
missing/changed/unauthorized remote (`REQ-001`, `REQ-004`; `AC-1`, `AC-2`) and never
leak embedded remote credentials in the rejection message or audit output (`REQ-003`;
`AC-3`).

## Scope
- In scope: new test classes/functions in this file exercising the HTTP
  `/v1/call_tool` path for `git_pull`/`git_push` against remote-authorization
  scenarios.
- Out of scope: concurrency/HEAD-drift tests (`tests/mcp_servers/git/
  test_git_concurrency.py`, a separate row).

## Assumptions
- Re-verified 2026-09-05: this file is now 847 lines with 5 existing `TestClient`
  usages (added by `gitauth`/`gitpipeline`/`gitdryrun` cycles), covering checkout/
  pull/push postcondition-bypass and pipeline-stage-order tests only — none exercise
  remote authorization or credential redaction, so this row's new tests are
  additive, not overlapping with existing coverage.

## Design decisions
- Reuse the existing `client` `TestClient` fixture pattern already established in
  this file (module-scoped `client()` fixture at line 490-496, and the
  class-scoped `client(self)` fixtures at lines 661-663/742-744) rather than
  introducing a third fixture shape — add a new test class using whichever existing
  fixture scope its scenario needs (module-scoped if state does not need per-test
  isolation; class-scoped if `monkeypatch`/mocked `RepositoryState.snapshot` state
  must not leak between tests, matching `TestPostConditionBypassPrevention`'s
  pattern at line 655).
- Simulate "remote resolves to an unauthorized URL" by mocking `git.Repo.remotes`
  (or the new `_resolve_remote_url` helper from `repository_state.py`'s row)
  rather than requiring a real, network-reachable remote — consistent with this
  file's existing pattern of mocking `RepositoryState.snapshot`/`RepositoryState`
  internals (e.g. `MagicMock()` snapshots at lines 476-486, 606-612) rather than
  operating against a live git remote.

## Alternatives considered
- Using a real local bare-repo remote (a second `git.Repo.init(bare=True)` fixture)
  was considered for `AC-2`'s "redirected remote" scenario; rejected in favor of
  mocking the resolved-URL helper directly — simpler, faster, and consistent with
  this file's existing mock-first testing style for `RepositoryState` internals.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure
1. Add a new test class (e.g. `TestRemoteAuthorization`) after
   `TestPostConditionBypassPrevention` (which ends around line 692) or alongside it,
   following the existing class-scoped `client` fixture pattern.
2. Add cases for: (a) `git_pull`/`git_push` with `remote` resolving to a URL not in
   `allowed_remote_urls` → rejected (`AC-1`); (b) a remote alias (e.g. `origin`)
   whose resolved URL has changed from an authorized value → rejected, not silently
   allowed (`AC-2`); (c) a remote URL containing embedded credentials
   (`https://user:token@host/repo.git`) → the rejection message and any audit-facing
   value never contains the raw credential substring (`AC-3`).

### Method
- Mock `RepositoryState.snapshot` (as existing tests do, e.g. lines 476-486) to
  return a `MagicMock` whose `.repo.remotes` is itself configured to simulate the
  target scenario (unauthorized URL, changed URL, credentialed URL), rather than
  mocking `format_pull`/`format_push` directly — exercises the real dispatch →
  pipeline → format function path end-to-end via `client.post("/v1/call_tool",
  ...)`.
- For `AC-3`, assert the credential substring (`user:token`) is absent from
  `response.json()`'s full serialized content — not merely from one specific field —
  to catch an accidental leak through any path.

### Details
- Follow this file's existing assertion style: `resp.status_code == 200`,
  `body.get("is_error") is True`, and a message-content assertion (see
  `TestHTTPSiblingPathRejection`'s pattern at line 500+ for the shape).
- Confirm each new test fails against the pre-change code (no authorization check
  exists yet, so the first two cases would currently *not* reject) and passes once
  `format_output.py`'s row lands.

## Compatibility considerations
- Purely additive test cases; no existing test in this file is modified.

## Security considerations
- Test fixtures using a credentialed URL string must use an obviously-fake
  placeholder credential (e.g. `user:faketoken123`), not a realistic-looking secret,
  to avoid the test file itself reading as containing a real credential.

## Rollback considerations
- N/A: additive test-only change; reverting removes coverage but has no runtime
  effect.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` — new
  cases fail before `format_output.py`'s row lands, pass after.
- `uv run pytest tests/mcp_servers/git/ -v` (full suite) — no regressions in the
  existing 847-line file's other cases.

## Completion criteria
- `AC-1`, `AC-2`, `AC-3` each have at least one passing test exercising the live
  `/v1/call_tool` HTTP path, added without modifying any existing test in this file.

## Out of scope
- Concurrency and HEAD-drift tests — `tests/mcp_servers/git/test_git_concurrency.py`,
  a separate row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-004, REQ-008
- **Source issue**: issues/20260902-144912_gitremote_define_remote_authorization_and_concurrency_control.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192131_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-204502
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py

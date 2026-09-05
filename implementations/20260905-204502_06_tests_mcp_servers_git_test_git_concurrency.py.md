## Goal
New test file proving concurrent writes to the same repository path are serialized
(`REQ-005`; `AC-4`), independent repository paths are not unnecessarily serialized
(`AC-5`), and a HEAD-identity change between authorization and mutation is rejected
(`REQ-006`; `AC-6`) — for both `git_pull` and `git_push` (`AC-7`).

## Scope
- In scope: this new file only, covering `WriteProtectionPipeline`'s lock and
  HEAD-recheck behavior (`repository_state.py`'s row).
- Out of scope: remote-authorization/credential-redaction tests
  (`test_git_security_compliance.py`, a separate row).

## Assumptions
- Confirmed 2026-09-05: no file named `test_git_concurrency.py` exists anywhere in
  the repository (`find` returned no match), and `tests/mcp_servers/git/` exists and
  holds this module's other test files — this is a new file in an existing
  directory, not a new directory.
- The lock is `threading.Lock` (not `asyncio.Lock`), per `repository_state.py`'s row
  Design decision (avoids requiring `WriteProtectionPipeline.run()` to become
  `async`) — tests must exercise real concurrent threads (`threading.Thread`), not
  `asyncio` tasks, to actually observe serialization.

## Design decisions
- Force deterministic interleaving with an explicit synchronization primitive
  (`threading.Event`) rather than wall-clock timing, per the Plan's own Risks
  section mitigation ("use explicit synchronization primitives... to force the
  interleaving under test rather than relying on wall-clock timing") — e.g. the
  mocked `op()` callable signals an `Event` when it starts and blocks on a second
  `Event` until released, letting the test assert the second thread's `op()` has not
  started while the first holds the lock.
- For the HEAD-drift test, mutate the repository's HEAD (e.g. via a direct
  `git.Repo.git.checkout(...)` call, or a mocked second `RepositoryState.snapshot()`
  call returning a different `active_branch`) between the pipeline's initial
  snapshot and its Stage 6 execution — using dependency injection/mocking of
  `RepositoryState.snapshot`, consistent with this module's existing test style,
  rather than a real timing-dependent race against an actual concurrent process.

## Alternatives considered
- Testing the lock via two concurrent `asyncio` tasks (as the Plan's Implementation
  intent originally suggested for `REQ-005`) was reconsidered given
  `repository_state.py`'s row settling on `threading.Lock`: `threading.Thread`-based
  concurrency is the correct test vehicle for a `threading.Lock`-based
  implementation — `asyncio.Lock` tests would not actually exercise it.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_concurrency.py` (new file)

### Procedure
1. Create the new file with the standard test-module header/imports consistent with
   sibling files in `tests/mcp_servers/git/` (e.g. `test_repository_state.py`'s
   import shape for `RepositoryState`/`WriteProtectionPipeline`).
2. Add a same-repo-path serialization test: two `threading.Thread`s each invoking
   `WriteProtectionPipeline.run(...)` against the same repo path with a mocked `op()`
   using `threading.Event`s to force interleaving; assert the second thread's `op()`
   only starts after the first's completes.
3. Add a cross-repo-path independence test: two threads against two distinct repo
   paths; assert both `op()` calls can be observed running concurrently (not
   serialized against each other).
4. Add HEAD-drift rejection tests for both `git_pull` and `git_push` (`AC-7`):
   mock a HEAD change between the pipeline's authorization-time snapshot and Stage 6;
   assert the pipeline rejects rather than proceeding.

### Method
- Use `unittest.mock.MagicMock`/`monkeypatch` for `RepositoryState.snapshot` and
  `git.Repo` internals, matching this module's established mocking style (see
  `test_repository_state.py` and `test_git_security_compliance.py`'s existing
  `MagicMock()` snapshot patterns) rather than operating against real `git.Repo`
  instances for the lock/HEAD-drift scenarios specifically (a real temp-dir repo
  fixture may still be used for setup/teardown convenience if simpler).

### Details
- Same-repo test: assert via a shared list/counter recorded inside each thread's
  mocked `op()` that entries are strictly non-overlapping (e.g. record
  `(thread_id, "start"/"end", timestamp_or_sequence)` and assert no
  `"start"`-before-other's-`"end"` interleaving for the same repo path).
- Cross-repo test: assert the two threads' `op()` calls *do* overlap (proving they
  were not serialized against each other) — a positive assertion that the lock is
  scoped per-path, not global.
- HEAD-drift test: assert `PipelineResult`'s rejection reason references the
  HEAD/identity mismatch (per `repository_state.py`'s row `"Stage 5b"` (or folded
  Stage 5) rejection label), for both `git_pull` and `git_push` tool names.

## Compatibility considerations
- New file only; no existing test is modified.

## Security considerations
- N/A: test-only file, no production code path.

## Rollback considerations
- N/A: additive new file; deleting it removes coverage but has no runtime effect.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_concurrency.py -v` — new file,
  confirm each test fails against pre-change `repository_state.py` (no lock/
  HEAD-recheck exists yet) and passes after that row lands.
- `uv run pytest tests/mcp_servers/git/ -v` (full suite) — no regressions.

## Completion criteria
- `AC-4`, `AC-5`, `AC-6`, `AC-7` each have at least one passing test in this new
  file, for both `git_pull` and `git_push` where applicable.

## Out of scope
- Remote-authorization/credential-redaction tests —
  `test_git_security_compliance.py`, a separate row.

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
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: issues/20260902-144912_gitremote_define_remote_authorization_and_concurrency_control.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192131_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-204502
- **Related target files**: tests/mcp_servers/git/test_git_concurrency.py

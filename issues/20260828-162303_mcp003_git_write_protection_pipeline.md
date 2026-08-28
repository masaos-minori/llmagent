# MCP-003: Git MCP write-protection pipeline — unify scattered guards behind a shared `RepositoryState`

## Priority
High

## Summary
`MCP-003` originally described Git MCP write protection as missing Dirty-Worktree/Detached-HEAD
checks, command-specific preconditions, and postcondition verification. Code inspection (done
while drafting `NC-019`/`GIT-001`/`GIT-002`) confirms most of these checks are actually already
implemented — but as ad hoc, per-call `git.Repo` queries scattered across `git_service.py` and
`format_output.py`, with no shared repository-state model reused across guards, verification,
audit, and tests. This issue reframes `MCP-003` around that architectural gap: adopt the proposed
9-stage pipeline (schema validation → repository resolution → common authorization → state
snapshot → command-specific precondition → execution → postcondition verification → audit →
structured result) built on a single shared `RepositoryState` dataclass, separating Agent-side
approval (user-intent confirmation only) from Git MCP's own technical safety guarantees, per
`ADR-012`.

## Background
`MCP-003` is tracked in `docs/04_mcp_90_inconsistencies_and_known_issues.md`; its Resolution
Notes already record that protected-branch enforcement and `branch`/`remote` option-injection
rejection are implemented (`REQ-006`), narrowing its original scope. `GIT-001`
(Dirty-Worktree/Detached-HEAD) and `GIT-002` (postcondition verification) are separately tracked
and, per this session's code inspection, are also already implemented — a correction to their
stale `open` status is tracked in a separate issue (`DOC-005`). `NC-019` (Tool Owner decision on
the residual empty-`branch` protected-branch bypass) and `NC-020` (audit `target` field
correctness) remain open and are directly relevant to this issue's Stage 5 and Stage 8 below.
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` (Status: Proposed) is the governing
ADR for all of this; it does not currently describe a unified pipeline or shared state model —
only the individual invariants (INV-01 through INV-04).

## Problem
Confirmed by reading `scripts/mcp_servers/git/git_service.py`, `git_security.py`, and
`format_output.py`:

- `GitSecurityGuards._check_dirty_worktree(repo: git.Repo)` and `_check_detached_head(repo: git.Repo)`
  each query `git.Repo` directly and are called individually, inline, from `git_checkout()`/`git_pull()`.
- `format_checkout()`/`format_pull()`/`format_push()` each independently re-inspect `repo` after
  the git command runs (`repo.active_branch.name`, `repo.index.unmerged_blobs()`, push-output
  string scanning) to verify postconditions — three different ad hoc checks, not one shared
  verification step.
- No dataclass or equivalent captures "the state of this repository right now" as a single,
  reusable value. Each guard and each postcondition check re-queries `git.Repo` on its own,
  so there is no single point where preconditions, postcondition comparison, audit logging, and
  tests can all reference the same observed state.
- `GitSecurityGuards._check_repo_path()` computes a canonical resolved path
  (`Path(repo_path).resolve()`) purely for the allowlist check and discards it; the Git MCP audit
  log (`git_server.py::call_tool()`) separately re-reads the raw, unvalidated `repo_path` argument
  as its `target` (tracked as `NC-020`).
- The residual empty-`branch` protected-branch bypass (`_validate_protected()` short-circuiting
  on a falsy `branch`, tracked as `NC-019`) is a direct symptom of preconditions being checked
  against raw request arguments instead of a resolved, canonical view of "what will actually
  happen" — exactly what Stage 4/5 below are meant to prevent structurally.
- Approval (`agent/tool_policy.py`/`tool_approval.py`) and Git MCP's own validation are already
  architecturally independent processes (confirmed — Git MCP's HTTP endpoint has no dependency on
  Agent-side approval state), consistent with the policy this issue restates, but nothing
  currently documents or enforces that separation as an explicit design invariant at the Git MCP
  layer.

## Reason for Change
The individual checks this issue's target architecture would unify already exist, but their
scattered, ad hoc form is precisely why `NC-019`'s empty-`branch` bypass and `NC-020`'s audit
`target` gap exist: each caller derives its own view of repository state from raw arguments or a
fresh `git.Repo` query, so there is no single, canonical point of truth that guards, postcondition
checks, and audit logging are all guaranteed to agree on. A shared `RepositoryState` snapshot,
computed once per call after schema validation and repository resolution, closes this class of
gap structurally rather than one bypass at a time, and gives `NC-020`'s audit-target work a
canonical `repository_id` to record instead of a raw argument string.

## Implementation Intent
Adopt the following pipeline for all Git MCP write operations (`git_checkout`, `git_pull`,
`git_push`, `git_add`, `git_commit`), implemented incrementally rather than as one large rewrite:

```
Request
  -> 1. Schema Validation            (existing: req.validate_args())
  -> 2. Repository Resolution        (existing allowlist check, extended to return the
                                       canonical resolved path instead of discarding it)
  -> 3. Common Authorization Guard   (existing: allowed_repo_paths + read_only)
  -> 4. Repository State Snapshot    (new: build one RepositoryState from the resolved repo)
  -> 5. Command-Specific Precondition Guard
                                     (existing checks re-expressed against the snapshot:
                                      dirty worktree, detached HEAD, protected-branch —
                                      checked against the *effective* branch, closing NC-019)
  -> 6. Git Command Execution        (existing)
  -> 7. Postcondition Verification   (existing per-tool checks re-expressed as: take a second
                                       RepositoryState snapshot, compare against the expected
                                       outcome using the same model as Stage 5)
  -> 8. Audit Recording              (existing _audit_log(), now given RepositoryState.repository_id
                                       as `target` instead of the raw argument — closes NC-020's
                                       canonical-identity requirement)
  -> 9. Structured Result
```

Shared state model, used consistently by Stages 5, 7, 8, error responses, and tests:

    @dataclass(frozen=True)
    class RepositoryState:
        repository_id: str
        repository_path: Path
        branch: str | None
        head_sha: str
        detached_head: bool
        staged_changes: bool
        unstaged_changes: bool
        untracked_files: bool
        conflicted_files: bool
        operation_in_progress: str | None
        upstream: str | None
        ahead: int | None
        behind: int | None

Explicitly restate and enforce as a design invariant (not just an implicit property of the
current code): Agent-side approval confirms user intent only; it MUST NOT be treated as a
substitute for, or evidence of, Git MCP's own technical safety checks, and Git MCP MUST NOT
assume a call it receives was already approved (matches `ADR-012` Decision Details #1).

## Target Files or Areas
- `scripts/mcp_servers/git/git_service.py` (`GitService`, `_wrap_git_op()`/`_run_tool()`,
  `git_checkout()`/`git_pull()`/`git_push()`/`git_add()`/`git_commit()`)
- `scripts/mcp_servers/git/git_security.py` (`GitSecurityGuards._check_repo_path()`,
  `_check_dirty_worktree()`, `_check_detached_head()`, `_check_protected_branch()`)
- `scripts/mcp_servers/git/format_output.py` (`format_checkout()`, `format_pull()`,
  `format_push()` — postcondition logic to be re-expressed against `RepositoryState`)
- `scripts/mcp_servers/git/git_models.py` (new `RepositoryState` dataclass; existing
  `RepoValidationResult` in `git_service.py` as a precedent for this kind of shared value type)
- `scripts/mcp_servers/git/git_server.py` (`call_tool()` — Stage 8 audit integration; see also
  `NC-020`, which scopes the audit-target fix independently)
- `scripts/mcp_servers/audit.py` (shared `AuditRecord`/`_audit_log()` — verify the new
  `repository_id` fits the existing `target` field without a schema change)
- `tests/mcp_servers/git/test_mcp_git.py`, `test_git_service_dispatch.py`,
  `test_git_security_compliance.py`

## Required Changes
- Introduce `RepositoryState` and a function that builds it once from a resolved `git.Repo` +
  canonical repository path.
- Extend repository resolution (Stage 2) to return and pass forward the canonical resolved path
  computed in `_check_repo_path()` instead of discarding it.
- Re-express `_check_dirty_worktree()`, `_check_detached_head()`, and `_check_protected_branch()`
  to read from a `RepositoryState` snapshot rather than querying `git.Repo` independently; fix
  `_check_protected_branch()`'s empty-`branch` short-circuit to check the effective (resolved)
  branch, per `NC-019`.
- Re-express `format_checkout()`/`format_pull()`/`format_push()`'s postcondition checks as a
  second `RepositoryState` snapshot compared against the expected outcome, using one shared
  comparison path rather than three separate ad hoc checks.
- Update `git_server.py::call_tool()`'s audit call to use `RepositoryState.repository_id` as
  `target`, and ensure an audit record is emitted (with a distinguishable outcome) for
  pre-dispatch rejections too, coordinating with `NC-020`'s scope rather than duplicating it.
- Update `ADR-012` to describe this pipeline and the `RepositoryState` model explicitly (it
  currently lists only the individual invariants), since this is a more detailed architecture
  than what the ADR currently records.

## Constraints
- Do not change the external `/v1/call_tool` request/response contract or the `git_*` tool
  input schemas — this is an internal refactor of how Git MCP validates and verifies, not a
  change to what callers send or receive.
- Do not weaken any currently-passing check while re-expressing it against `RepositoryState` —
  each re-expressed guard/postcondition check must be verified equivalent (or strictly stronger)
  via the existing test suite before being considered complete.
- ADR-012's single-operator/local-git trust-boundary assumption still bounds scope; this issue
  does not add a Force-Push capability or extend guards to GitHub MCP.

## Acceptance Criteria
- A `RepositoryState` dataclass (or equivalent) exists and is populated from one canonical
  snapshot function.
- `git_checkout`/`git_pull`/`git_push`'s precondition checks (dirty worktree, detached HEAD,
  protected branch) all read from a `RepositoryState` snapshot rather than independent `git.Repo`
  queries, and the protected-branch check no longer short-circuits on an empty `branch` argument
  (closing `NC-019`'s residual gap).
- Postcondition verification for all three tools compares a post-execution `RepositoryState`
  snapshot against the expected outcome via one shared comparison path.
- The Git MCP audit `target` field is populated from `RepositoryState.repository_id`, a
  canonical, validated identity — not a raw caller-supplied argument (closing `NC-020`'s
  canonical-identity requirement).
- Existing tests in `tests/mcp_servers/git/` continue to pass, and new tests cover the
  `RepositoryState` snapshot function directly plus each re-expressed guard/postcondition check.
- `ADR-012` is updated to describe the pipeline and `RepositoryState` model; `MCP-003`'s Status/
  Resolution Notes reflect the outcome.

## Testing Expectations
Unit tests for `RepositoryState` snapshot construction (clean repo, dirty worktree, detached
HEAD, conflicted merge, ahead/behind upstream). Regression tests confirming each re-expressed
guard/postcondition check behaves identically (or strictly more safely) to its current ad hoc
form. Integration tests in `test_mcp_git.py`/`test_git_service_dispatch.py` covering the full
pipeline for `git_checkout`/`git_pull`/`git_push`. Coordinate with `NC-020`'s planned
log-verification test for the audit-target field rather than duplicating it.

## Documentation Impact
Yes. `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` should be updated (or
superseded by a more detailed ADR) to document the 9-stage pipeline and `RepositoryState` model
as the target architecture, since it currently only lists the underlying invariants without this
structure. `docs/04_mcp_90_inconsistencies_and_known_issues.md`'s `MCP-003` entry should be
updated to describe the architectural gap (scattered ad hoc checks vs. a shared state model)
rather than "missing checks," consistent with what this session's code inspection confirmed.
Keep the documentation to design intent, responsibility boundaries, and the state-model contract
— not a restatement of the full `RepositoryState` field list or validation code.

## Out of Scope
- Implementing a Force-Push administrative capability (explicitly out of scope per `ADR-012`).
- GitHub MCP's protected-branch/force-push handling (already implemented separately).
- Changing the `git_*` tools' external input schemas or `/v1/call_tool` contract.
- `NC-019`'s and `NC-020`'s owner-decision/investigation steps themselves — this issue's
  implementation is expected to close their remaining scope as a side effect of Stages 5 and 8,
  but does not replace the decision-recording work tracked in those issues.

## Dependencies
- Related: `NC-019` (residual empty-`branch` bypass — closed via Stage 5), `GIT-001`/`GIT-002`
  (already implemented; being re-expressed against `RepositoryState`, not re-implemented from
  scratch — see `DOC-005` for their stale-status correction), `NC-020` (audit-target
  canonicalization — closed via Stage 8), `ADR-012` (governing ADR, needs updating alongside this
  work).
- Coordinate implementation order with `NC-019`/`NC-020` to avoid two separate changes touching
  the same guard/audit code independently.

## Unresolved Questions
- Whether `RepositoryState` should be computed via GitPython calls directly (as current guards
  do) or via `git` CLI invocations for consistency with `format_output.py`'s use of `repo.git.*`
  — an implementation-level choice to be resolved when the snapshot function is written, not a
  design-intent question.
- Whether Stage 2's "Repository Resolution" and Stage 4's "Repository State Snapshot" should be
  merged into one step (since both require opening/resolving the `git.Repo`) or kept separate for
  clarity — left to the implementer; either satisfies this issue's Acceptance Criteria.

## AI Implementation Instruction
Read `scripts/mcp_servers/git/git_service.py`, `git_security.py`, and `format_output.py` in full
before starting — do not re-implement Dirty-Worktree/Detached-HEAD/postcondition checks from
scratch; re-express the existing, already-working logic against `RepositoryState` and verify
equivalence via the existing test suite before adding new behavior. Implement incrementally
(snapshot model first, then Stage 5 re-expression, then Stage 7, then Stage 8's audit
integration) rather than as one large rewrite, and keep each step's tests passing throughout.
Coordinate with `NC-019`/`NC-020` rather than duplicating their fixes — closing the empty-`branch`
bypass and the audit-target gap should happen once, inside this pipeline. Update `ADR-012` and
`MCP-003` as part of the same body of work rather than leaving them stale.

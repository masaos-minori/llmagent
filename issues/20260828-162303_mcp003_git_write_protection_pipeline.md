# MCP-003: Git MCP write-protection pipeline — unify scattered guards behind a shared `RepositoryState`

## Priority
High

## Summary
`MCP-003` originally described Git MCP write protection as missing Dirty-Worktree/Detached-HEAD
checks, command-specific preconditions, and postcondition verification. Code inspection (done
while drafting `NC-019`/`GIT-001`/`GIT-002`) confirms most of these checks are actually already
implemented — but as ad hoc, per-call `git.Repo` queries scattered across `git_service.py` and
`format_output.py`, with no shared repository-state model reused across guards, verification,
audit, and tests. This issue reframes `MCP-003` around that architectural gap: adopt a 9-stage
pipeline (schema validation → repository resolution → common authorization → state snapshot →
command-specific precondition → execution → postcondition verification → audit → structured
result) built on a single shared `RepositoryState` dataclass, separating Agent-side approval
(user-intent confirmation only) from Git MCP's own technical safety guarantees, per `ADR-012`.
Adversarial verification confirmed the core architectural diagnosis is accurate, but found the
proposed pipeline order conflicts with the current, deliberate check ordering in at least one
place, omits one of the four scattered checks entirely, and understates the plumbing work needed
for Stage 8 — all addressed below. This issue is a **maintainability/consistency investment**,
not a prerequisite for closing `NC-019`/`NC-020`, which can each be fixed independently and more
cheaply; where this issue's scope overlaps theirs, it is explicitly gated on their own decisions
rather than assumed to supersede them.

## Background
`MCP-003` is tracked in `docs/04_mcp_90_inconsistencies_and_known_issues.md`; its Resolution
Notes already record that protected-branch enforcement and `branch`/`remote` option-injection
rejection are implemented (`REQ-006`), narrowing its original scope. `GIT-001`
(Dirty-Worktree/Detached-HEAD) and `GIT-002` (postcondition verification) are separately tracked
and, per this session's code inspection, are also already implemented — a correction to their
stale `open` status is tracked in a separate issue (`DOC-005`). `NC-019` (Tool Owner decision on
the residual empty-`branch` protected-branch bypass, confirmed by live reproduction to affect
`git_push`/`git_pull` only — `git_checkout` is confirmed unaffected) and `NC-020` (audit `target`
field correctness) remain open and are directly relevant to this issue's Stage 5 and Stage 8
below. `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` (Status: Proposed) is the
governing ADR for all of this; it does not currently describe a unified pipeline or shared state
model — only the individual invariants (INV-01 through INV-04).

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
  tests can all reference the same observed state. Confirmed: no `RepositoryState`-like type
  exists anywhere in `scripts/mcp_servers/git/` or `scripts/shared/` today.
- `GitSecurityGuards._check_repo_path()` computes a canonical resolved path
  (`Path(repo_path).resolve()`) purely for the allowlist check and discards it; the Git MCP audit
  log (`git_server.py::call_tool()`) separately re-reads the raw, unvalidated `repo_path` argument
  as its `target` (tracked as `NC-020`).
- **A fourth scattered check exists that the original pipeline draft omitted:**
  `GitSecurityGuards._is_safe_ref()`/`GitService._validate_ref()` (ref/remote option-injection
  rejection, `ADR-012` INV-01) is called independently from each of `git_checkout()`/`git_pull()`/
  `git_push()`, alongside — not through — the dirty-worktree/detached-head/protected-branch
  checks. Any unification effort that leaves this one out is incomplete.
- The residual empty-`branch` protected-branch bypass (`_validate_protected()` short-circuiting
  on a falsy `branch`, tracked as `NC-019`, confirmed live on `git_push`/`git_pull`, confirmed
  *not* present on `git_checkout`) is a symptom of the same scattered-checks pattern, but is not
  itself evidence that a full pipeline rewrite is *required* to fix it — `NC-019` proposes a
  much smaller, independent fix (resolve the effective branch before checking protection), which
  works with or without this issue's broader architecture.
- **Current check ordering does not match the pipeline's proposed stage order, and this is a
  real behavior question, not just a relabeling exercise.** In `git_checkout()`/`git_pull()`/
  `git_push()`, `_validate_ref()` and `_validate_protected()` run *before* `_run_tool()` — i.e.,
  before the repo-path allowlist and `read_only` checks (proposed Stages 3) even run. Only
  `_check_dirty_worktree()`/`_check_detached_head()` run after the repo is opened, inside the
  `_run_tool()`-wrapped closure. Adopting the proposed pipeline's strict Stage-3-before-Stage-5
  order would change which error a caller sees first for a request that is simultaneously
  invalid on multiple axes (e.g., an unauthorized repo path *and* a protected branch) — this is a
  real ordering decision to make explicitly, not an incidental detail of re-expression.
- Approval (`agent/tool_policy.py`/`tool_approval.py`) and Git MCP's own validation are already
  architecturally independent processes (confirmed — Git MCP's HTTP endpoint has no dependency on
  Agent-side approval state), consistent with the policy this issue restates, but nothing
  currently documents or enforces that separation as an explicit design invariant at the Git MCP
  layer.

## Reason for Change
The individual checks this issue's target architecture would unify already exist and already
work correctly — this is a maintainability and consistency investment, not a bug fix. Its
justification stands on its own: four scattered, independently-querying checks
(`_check_dirty_worktree`, `_check_detached_head`, `_check_protected_branch`, `_validate_ref`/
`_is_safe_ref`) and three independent postcondition checks currently have no shared model, which
means every future guard, every postcondition check, and every test must re-derive "the current
state of this repository" from scratch, with no guarantee that two call sites agree. A shared
`RepositoryState` snapshot closes this class of risk structurally. It is **not**, however, a
prerequisite for closing `NC-019` (a one-line fix to `_validate_protected()`, scoped to
`git_push`/`git_pull` only, does not require this architecture) or `NC-020` (whose audit-target
fix can and should proceed on its own timeline, referencing `mdq`'s existing
`extract_audit_target()` pattern rather than waiting on this pipeline). This issue is proposed
*alongside* those fixes as a broader investment, not *instead of* them, and should not block or
be blocked by their own decision processes.

## Implementation Intent
Adopt the following pipeline for all Git MCP write operations (`git_checkout`, `git_pull`,
`git_push`, `git_add`, `git_commit`), implemented incrementally in the phases below — not as one
large rewrite, and not gating on `NC-019`/`NC-020`'s own resolution except where explicitly noted.

```
Request
  -> 1. Schema Validation            (existing: req.validate_args())
  -> 2. Repository Resolution        (existing: currently fused with Stage 3 in one function,
                                       GitService._validate_repo() — extend to return the
                                       canonical resolved path instead of discarding it)
  -> 3. Common Authorization Guard   (existing: allowed_repo_paths + read_only, same function
                                       as Stage 2 today — decide whether to keep fused or split)
  -> 4. Repository State Snapshot    (new: build one RepositoryState from the resolved repo)
  -> 5. Command-Specific Precondition Guard
                                     (existing checks re-expressed against the snapshot: ref/remote
                                      validity (_validate_ref/_is_safe_ref), dirty worktree,
                                      detached HEAD, protected-branch. NOTE: today these run
                                      BEFORE Stage 2/3 for ref/protected-branch, and AFTER for
                                      dirty-worktree/detached-head — adopting a single Stage-5
                                      position is an explicit ordering change, see Phase 0 below)
  -> 6. Git Command Execution        (existing)
  -> 7. Postcondition Verification   (existing per-tool checks, currently fused into the same
                                       function bodies as Stage 6 in format_output.py — splitting
                                       them into a distinct step is a real restructuring, not a
                                       relabeling)
  -> 8. Audit Recording              (existing _audit_log(); giving it RepositoryState.repository_id
                                       depends on solving a cross-layer plumbing gap — see Phase 3)
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

Implement in these phases, each independently mergeable and independently testable:

- **Phase 0 (decision, before any code): resolve the check-ordering question.** Decide whether
  Stage 3 (common authorization) must run strictly before Stage 5 (command-specific
  preconditions) — a behavior change from today's actual ordering for `_validate_ref`/
  `_validate_protected` — or whether the pipeline's stage *numbering* is documentation-only and
  today's actual ordering is preserved. Do not proceed to Phase 1 with this undecided.
- **Phase 1: `RepositoryState` + Stage 5.** Introduce the snapshot type and re-express all four
  scattered precondition checks (including `_validate_ref`/`_is_safe_ref`, not just three of the
  four) against it. If `NC-019`'s Tool Owner decision has approved closing the empty-`branch`
  bypass by the time this phase starts, fix it here for `git_push`/`git_pull` only as part of the
  same re-expression (see Constraints) — otherwise, re-express the existing (still-bypassable)
  behavior faithfully and leave the bypass fix to `NC-019`'s own tracked resolution.
- **Phase 2: Stage 7.** Restructure `format_output.py`'s `format_checkout()`/`format_pull()`/
  `format_push()` to separate execution from postcondition verification, using a second
  `RepositoryState` snapshot compared via one shared path.
- **Phase 3: Stage 8.** Solve the audit-target plumbing gap (see Problem/Unresolved Questions)
  and integrate with whatever `NC-020` has already implemented or decided by this point — do not
  implement a second, competing target-resolution mechanism.

## Target Files or Areas
- `scripts/mcp_servers/git/git_service.py` (`GitService`, `_validate_repo()` (Stages 2+3, fused
  today), `_validate_ref()`, `_validate_protected()`, `_wrap_git_op()`/`_run_tool()`,
  `git_checkout()`/`git_pull()`/`git_push()`/`git_add()`/`git_commit()`)
- `scripts/mcp_servers/git/git_security.py` (`GitSecurityGuards._check_repo_path()`,
  `_is_safe_ref()`, `_check_dirty_worktree()`, `_check_detached_head()`, `_check_protected_branch()`)
- `scripts/mcp_servers/git/format_output.py` (`format_checkout()`, `format_pull()`,
  `format_push()` — Stage 6/7 split, not just re-expression)
- `scripts/mcp_servers/git/git_models.py` (new `RepositoryState` dataclass; existing
  `RepoValidationResult` in `git_service.py` as a precedent for this kind of shared value type)
- `scripts/mcp_servers/git/git_server.py` (`call_tool()` — Stage 8; coordinate with `NC-020`
  rather than duplicating its work)
- `scripts/mcp_servers/dispatch.py` (the generic `DispatchResult(output, is_error)` contract every
  MCP server's `call_tool()` uses — Stage 8 needs a way to carry `repository_id` across this
  boundary without changing it for the other 7 servers; see Unresolved Questions)
- `scripts/mcp_servers/audit.py` (shared `AuditRecord`/`_audit_log()` — verify the new
  `repository_id` fits the existing `target` field without a schema change)
- `tests/mcp_servers/git/test_mcp_git.py`, `test_git_service_dispatch.py`,
  `test_git_security_compliance.py`

## Required Changes
- **Phase 0:** Record an explicit decision on the check-ordering question (see Implementation
  Intent) before writing any pipeline code.
- **Phase 1:** Introduce `RepositoryState` and a function that builds it once from a resolved
  `git.Repo` + canonical repository path. Extend repository resolution to return and pass forward
  the canonical resolved path computed in `_check_repo_path()` instead of discarding it.
  Re-express `_validate_ref()`/`_is_safe_ref()`, `_check_dirty_worktree()`, `_check_detached_head()`,
  and `_check_protected_branch()` to read from the `RepositoryState` snapshot rather than querying
  `git.Repo`/raw arguments independently — all four scattered checks, not three.
- **Phase 2:** Split `format_checkout()`/`format_pull()`/`format_push()`'s postcondition checks
  out into a second `RepositoryState` snapshot compared against the expected outcome via one
  shared comparison path.
- **Phase 3:** Solve the `DispatchResult`/audit-plumbing gap so `git_server.py::call_tool()`'s
  audit call can use `RepositoryState.repository_id` as `target`; coordinate directly with
  `NC-020`'s own implementation rather than building a second mechanism.
- Update `ADR-012` to describe this pipeline and the `RepositoryState` model explicitly (it
  currently lists only the individual invariants), including an explicit statement of the
  Phase 0 ordering decision.

## Constraints
- Do not change the external `/v1/call_tool` request/response contract or the `git_*` tool
  input schemas — this is an internal refactor of how Git MCP validates and verifies, not a
  change to what callers send or receive. Note: this constrains how Phase 3 can solve the
  audit-plumbing gap — a `DispatchResult` schema change, if needed, affects all 8 MCP servers'
  shared contract, not just Git's; resolve this tension explicitly rather than assuming both
  constraints can be satisfied for free.
- Do not weaken any currently-passing check while re-expressing it against `RepositoryState` —
  each re-expressed guard/postcondition check must be verified equivalent (or strictly stronger)
  via the existing test suite before being considered complete. This includes not silently
  changing check *order* without the Phase 0 decision being made explicitly first.
- ADR-012's single-operator/local-git trust-boundary assumption still bounds scope; this issue
  does not add a Force-Push capability or extend guards to GitHub MCP.
- Do not implement `NC-019`'s empty-`branch` bypass fix as an unconditional part of this issue —
  it is gated on `NC-019`'s own Tool Owner decision (see Phase 1 above and Acceptance Criteria).

## Acceptance Criteria
Per phase, so partial progress is independently reviewable:

- **Phase 0:** The check-ordering question has a recorded decision (preserve current order, or
  adopt strict Stage-3-before-Stage-5 ordering with its behavior-change implications documented).
- **Phase 1:** A `RepositoryState` dataclass (or equivalent) exists and is populated from one
  canonical snapshot function. All four scattered precondition checks — ref/remote validity,
  dirty worktree, detached HEAD, protected branch — read from a `RepositoryState` snapshot rather
  than independent `git.Repo`/raw-argument queries. *If and only if* `NC-019`'s Tool Owner has
  approved closing the empty-`branch` bypass by this point, the protected-branch check no longer
  short-circuits on an empty `branch` argument for `git_push`/`git_pull` (not `git_checkout`,
  which is confirmed unaffected and must not be changed) — otherwise this phase re-expresses the
  existing behavior faithfully without implementing that fix itself.
- **Phase 2:** Postcondition verification for `git_checkout`/`git_pull`/`git_push` compares a
  post-execution `RepositoryState` snapshot against the expected outcome via one shared
  comparison path, with execution and verification as separable steps in `format_output.py`.
- **Phase 3:** The Git MCP audit `target` field is populated from `RepositoryState.repository_id`,
  coordinated with (not duplicating) `NC-020`'s own target-resolution work, without changing the
  `DispatchResult` contract for the other 7 MCP servers (or, if a contract change proves
  unavoidable, that change is proposed and reviewed as its own explicit decision).
- Existing tests in `tests/mcp_servers/git/` continue to pass throughout, and new tests cover the
  `RepositoryState` snapshot function directly plus each re-expressed guard/postcondition check.
- `ADR-012` is updated to describe the pipeline, the `RepositoryState` model, and the Phase 0
  ordering decision; `MCP-003`'s Status/Resolution Notes reflect the outcome.

## Testing Expectations
Unit tests for `RepositoryState` snapshot construction (clean repo, dirty worktree, detached
HEAD, conflicted merge, ahead/behind upstream). Regression tests confirming each re-expressed
guard/postcondition check behaves identically (or strictly more safely, and with any ordering
change from Phase 0 explicitly covered) to its current ad hoc form. Integration tests in
`test_mcp_git.py`/`test_git_service_dispatch.py` covering the full pipeline for
`git_checkout`/`git_pull`/`git_push`. Coordinate with `NC-020`'s planned log-verification test
for the audit-target field rather than duplicating it.

## Documentation Impact
Yes. `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` should be updated (or
superseded by a more detailed ADR) to document the 9-stage pipeline, the `RepositoryState`
model, and the Phase 0 ordering decision, since it currently only lists the underlying
invariants without this structure. `docs/04_mcp_90_inconsistencies_and_known_issues.md`'s
`MCP-003` entry should be updated to describe the architectural gap (scattered ad hoc checks vs.
a shared state model) rather than "missing checks," consistent with what this session's code
inspection confirmed. Keep the documentation to design intent, responsibility boundaries, and the
state-model contract — not a restatement of the full `RepositoryState` field list or validation
code.

## Out of Scope
- Implementing a Force-Push administrative capability (explicitly out of scope per `ADR-012`).
- GitHub MCP's protected-branch/force-push handling (already implemented separately).
- Changing the `git_*` tools' external input schemas or `/v1/call_tool` contract.
- `NC-019`'s Tool Owner decision itself — this issue's Phase 1 will implement the fix *if and
  only if* that decision has already approved it; this issue does not make or substitute for that
  decision.
- `NC-020`'s Phase 1 (live-log capture) and its own design decisions for target resolution — this
  issue's Phase 3 coordinates with and reuses `NC-020`'s outcome, not the other way around.
- Extending this pipeline or `RepositoryState` to any MCP server other than Git.

## Dependencies
- Related: `NC-019` (Phase 1 conditionally implements its fix, scoped to `git_push`/`git_pull`
  only, gated on that issue's own Tool Owner approval), `GIT-001`/`GIT-002` (already implemented;
  being re-expressed against `RepositoryState` in Phase 1/2, not re-implemented from scratch — see
  `DOC-005` for their stale-status correction), `NC-020` (Phase 3 depends on and coordinates with
  its target-resolution outcome rather than duplicating it), `ADR-012` (governing ADR, needs
  updating alongside this work).
- Phase 3 cannot start meaningfully until `NC-020`'s Phase 1/2 have produced a concrete design to
  coordinate with — do not implement Phase 3 in parallel with `NC-020` without synchronizing.

## Unresolved Questions
- **Check-ordering (Phase 0, blocking):** see Problem/Implementation Intent — must be decided
  before Phase 1 begins.
- **`DispatchResult` plumbing for Stage 8 (blocking for Phase 3):** `git_server.py::call_tool()`'s
  audit call is one layer above `GitService`, reached through the generic
  `DispatchResult(output: str, is_error: bool)` contract shared by all 8 MCP servers
  (`scripts/mcp_servers/dispatch.py`). There is currently no channel for a per-tool handler to
  hand a `repository_id` back up to `call_tool()`'s audit call without either extending
  `DispatchResult` (touching every MCP server, in tension with the "do not change the contract"
  Constraint) or having `git_server.py` independently re-resolve/re-open the repo a second time
  (duplicating work `GitService` already did). Resolve this concretely — ideally in coordination
  with `NC-020`, which has the same problem — before Phase 3 implementation begins.
- Whether `RepositoryState` should be computed via GitPython calls directly (as current guards
  do) or via `git` CLI invocations for consistency with `format_output.py`'s use of `repo.git.*`
  — an implementation-level choice to be resolved when the snapshot function is written, not a
  design-intent question.

## AI Implementation Instruction
Read `scripts/mcp_servers/git/git_service.py`, `git_security.py`, and `format_output.py` in full
before starting — do not re-implement Dirty-Worktree/Detached-HEAD/postcondition/ref-validation
checks from scratch; re-express the existing, already-working logic against `RepositoryState` and
verify equivalence via the existing test suite before adding new behavior. Resolve Phase 0's
ordering question and Stage 8's `DispatchResult`-plumbing question explicitly (do not guess) before
writing the corresponding phase's code. Implement strictly in phase order (0 → 1 → 2 → 3), keeping
each phase's tests passing before starting the next, and treat each phase as independently
reviewable/mergeable rather than one large rewrite. Do not implement `NC-019`'s empty-`branch` fix
unless that issue's own Tool Owner decision has already approved it by the time Phase 1 starts —
check its current status first. Coordinate Phase 3 with `NC-020`'s own implementation rather than
building a second, competing target-resolution mechanism. Update `ADR-012` and `MCP-003` as part
of the same body of work rather than leaving them stale.

# Enforce the complete write-protection pipeline and operation-specific postconditions

## Priority
High

## Summary
Turn `RepositoryState`'s documented nine-stage write-protection pipeline into the actually
enforced sequence for every Git write tool: capture immutable pre/post-operation snapshots,
enforce stage ordering, and verify operation-specific outcomes instead of a placeholder
success.

## Background
`issues/done/20260902-094746_h01_git_mcp_write_protection_status_contradiction.md` planned to
mark `docs/04_mcp_90_inconsistencies_and_known_issues.md`'s `MCP-003` resolved on the premise
that write-protection guards are implemented and tested. Its follow-on plan
(`plans/20260901-223706_plan.md`) has not yet been executed, and `MCP-003`'s `Status` is still
`open`. Separately from that plan's own scope, this issue documents a specific gap that
investigation found in `RepositoryState.WriteProtectionPipeline` itself: `run()`
(`scripts/mcp_servers/git/repository_state.py`) is real, live code called from
`git_service.py`/`git_server.py`, but its own Stage 3 (`verify_authorization()`) has zero call
sites, and Stage 7 (`verify_postcondition()`) unconditionally returns success. Actual
postcondition enforcement instead happens through a different mechanism —
`format_checkout()`/`format_pull()`/`format_push()` (`scripts/mcp_servers/git/format_output.py`)
raising `GitServiceError` — which does work, but leaves the pipeline's own stage list and
result reporting inaccurate.

## Problem
The current pipeline invokes preconditions, execution, and a postcondition method, but
authorization is not visibly executed within it, stage records are not populated to reflect
what actually ran, and postcondition verification is a placeholder that always succeeds.
Reusing the pre-operation snapshot cannot prove that checkout, pull, push, add, or commit
produced the intended result. This creates a risk that failed, partial, or unsafe operations
are reported as successful by the pipeline's own bookkeeping, even though the separate
`format_output.py` mechanism happens to catch real failures today.

## Reason for Change
`MCP-003`'s "Observed Implementation" text and this pipeline's own stage list should describe
what actually executes, not an aspirational nine-stage design — leaving the gap undocumented
risks a future change trusting `PipelineResult.all_stages_succeeded` as ground truth when it is
not.

## Implementation Intent
Define the canonical pipeline stages and their responsibilities in one implementation
location, run repository validation, write permission checks, authorization, state capture,
command-specific preconditions, execution, postcondition verification, audit preparation, and
structured-result generation in the documented order, and prevent execution when any required
stage fails. Authorization and target resolution from `gitauth` (filed alongside this issue)
must be consumed by this pipeline rather than reimplemented separately.

## Target Files or Areas
- `scripts/mcp_servers/git/repository_state.py`
- `scripts/mcp_servers/git/git_service.py`
- `scripts/mcp_servers/git/git_server.py`
- `scripts/mcp_servers/git/format_output.py`
- `tests/test_git_security_compliance.py`

Confirm file existence and responsibility before editing; modify only files required by the
verified implementation path.

## Required Changes
- Define the canonical pipeline stages and their responsibilities in one implementation location.
- Run repository validation, write permission checks, authorization, state capture, command-specific preconditions, execution, postcondition verification, audit preparation, and structured-result generation in the documented order; prevent execution when any required stage fails.
- Capture a fresh `RepositoryState` after execution instead of reusing the pre-operation snapshot as the postcondition state.
- Implement operation-specific postconditions for checkout, pull, push, add, and commit — consolidating with or replacing `format_output.py`'s existing, working checks rather than leaving both as separate, partially-overlapping mechanisms.
- For checkout, verify the resulting branch or explicitly permitted detached-HEAD state.
- For pull, detect unresolved conflicts and incomplete merge or rebase states.
- For push, use structured GitPython results where possible and detect rejected, error, forced, deleted, and partial outcomes.
- Record successful, failed, and skipped stages in `PipelineResult`.
- Include the resolved operation target, pre-state, post-state, rejection stage, and rejection reason in the structured result without exposing credentials.
- Correct `MCP-003`'s "Observed Implementation" text once the actual behavior is verified, so it no longer contradicts `GIT-002`'s Resolution Notes.

## Constraints
- Do not guess unverified behavior; record unresolved design decisions as Needs Confirmation.
- Preserve unrelated behavior.
- Do not introduce a second authorization or dispatch path.
- Update documentation only after implementation and tests establish the current behavior.
- If investigation disproves an assumption in this issue, update the issue with evidence before implementation.

## Acceptance Criteria
- Authorization is executed before every Git write operation.
- A failed stage prevents all subsequent unsafe stages from running.
- `verify_postcondition()` no longer returns unconditional success.
- Pre-operation and post-operation states are separate snapshots.
- The pipeline stage list reflects actual execution and ordering.
- `all_stages_succeeded` and `last_failed_stage` report accurate results.
- Partial or rejected Git operations are not reported as successful.
- Tests prove that the complete pipeline cannot be bypassed through the HTTP or service dispatch path.
- `MCP-003`'s Status and "Observed Implementation" text in `docs/04_mcp_90_inconsistencies_and_known_issues.md` accurately reflect the landed behavior.

## Testing Expectations
Add focused unit tests for all changed rules. Add or update integration tests for the HTTP and
service dispatch paths. Confirm each new test fails before the fix and passes after the fix.
Run the complete existing Git MCP test suite and resolve regressions. Do not treat
documentation statements as proof of runtime behavior.

## Documentation Impact
Update `MCP-003` in `docs/04_mcp_90_inconsistencies_and_known_issues.md` and
`docs/04_mcp_04_05_git.md`'s pipeline description once implementation and tests establish the
current behavior.

## Out of Scope
- Protected-branch/ref authorization content itself (`gitauth`), though this pipeline must call into it.
- Detached-HEAD/dry-run precondition behavior (`gitdryrun`).
- Tool dispatch unification (`gitdispatch`).
- Repository-path containment and audit hardening (`gitpathaudit`).
- Remote authorization and concurrency control (`gitremote`).
- Re-executing `plans/20260901-223706_plan.md`'s own NC-019/MCP-003 documentation-only scope — that plan should be re-evaluated against this issue's findings before it proceeds, not superseded by this issue.

## Dependencies
Depends on `gitauth`'s authorization/target-resolution outcome (filed alongside this issue) to
be consumed by Stage 3 rather than reimplemented. Blocks `plans/20260901-223706_plan.md`'s
`MCP-003 → resolved` step — that plan should not mark `MCP-003` resolved until this issue's
gap is closed or the discrepancy is otherwise reconciled.

## Unresolved Questions
Whether the pipeline's own postcondition stage should absorb `format_output.py`'s existing
checks, or whether `format_output.py`'s mechanism should remain the actual enforcement point
with the pipeline's stage merely reporting on it — an implementation decision to make with
evidence from both code paths, not assumed here.

## AI Implementation Instruction
Before editing, re-confirm `WriteProtectionPipeline.run()`'s current call sites and stage
implementations (`grep -rn "verify_authorization\|verify_postcondition" scripts/mcp_servers/git/`),
since this issue's evidence may go stale. Do not remove `format_output.py`'s existing,
working checks until the pipeline's own postcondition stage is proven equivalent or superior by
tests. Update `MCP-003` only after the landed behavior is verified against this issue's
Acceptance Criteria.

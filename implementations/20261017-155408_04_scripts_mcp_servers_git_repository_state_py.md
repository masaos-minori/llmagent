# Implementation Procedure — `scripts/mcp_servers/git/repository_state.py`

## Goal

Fill the known postcondition gaps in the git pipeline: add checkout verification and
replace the documented no-op TOCTOU re-check with a real re-check (`REQ-003`).

## Scope

Modify only `scripts/mcp_servers/git/repository_state.py`. Extend `verify_postcondition`
and the pipeline `run` method to verify checkout landed on the requested branch and to
perform a genuine post-operation re-check where the snapshot makes it possible.

## Assumptions

- `verify_postcondition(result, post_state, tool_name, requested_branch)` is at line 192.
- The current docstring states git_checkout is intentionally NOT branch-checked here
  because the shared snapshot only holds the pre-checkout state; the real postcondition is
  enforced in `format_checkout`. pull/push ARE verified (conflict check).
- The TOCTOU re-check referenced near line 304 (Stage 5b HEAD-identity re-check) is a
  documented no-op that must become a real re-check.

## Design decisions

- Add checkout verification only where a post-checkout snapshot is available without
  falsely rejecting successful checkouts — i.e. where `verify_postcondition` can observe
  the actual landed state, not the pre-checkout state. Where the shared-snapshot limitation
  still holds, preserve the documented delegation to `format_checkout` and note it.
- Replace the no-op TOCTOU re-check with a re-read of the relevant state (e.g. HEAD
  identity / protected-branch membership) immediately after the mutating call, guarded so
  it cannot reject legitimately successful operations.

## Alternatives considered

- Copying the git pattern wholesale into other servers: rejected — the plan scopes this
  row to git only; other categories are separate rows.
- Branch-checking every checkout unconditionally: rejected — contradicts the existing
  documented rationale and would reject valid checkouts.

## Implementation

### Target file

`scripts/mcp_servers/git/repository_state.py`

### Procedure

1. Read `verify_postcondition` (192–216) and the `run` pipeline (321+) including the Stage
   5b re-check area (around 304) to understand the current no-op.
2. Add checkout-landing verification for the cases where a post-state snapshot is
   observable; keep the format_checkout delegation where the shared snapshot only holds
   pre-checkout state, but make the delegation explicit and tested.
3. Replace the Stage 5b no-op re-check with a real re-check of the protected-branch / HEAD
   identity after the mutating Git call, scoped so it fails closed only on genuine drift.

### Method

- Locate the re-check insertion point in `run` (between the mutating Git call and
  postcondition verification).
- Add the re-check and any needed snapshot refresh; do not alter precondition logic.

### Details

- The re-check must fail closed (reject) on genuine post-condition drift but must not fire
  on the pre-checkout-state false-positive the docstring warns about.
- Regression-test the dry-run and detached-head paths explicitly (plan Risk).

## Compatibility considerations

Changing checkout timing/behavior could affect callers relying on the current pipeline.
Keep the change scoped to post-operation state verification; regression-test existing
paths.

## Security considerations

A real TOCTOU re-check strengthens the protected-branch guarantee. Ensure the re-check
reads authoritative repo state under the existing repo lock to avoid races.

## Rollback considerations

Revert the commit to `repository_state.py`.

## Validation plan

- Postcondition negative test: assert verification fails closed on partial/unintended
  results.
- Regression: existing dry-run / detached-head / pull-conflict paths still behave correctly.
- Command: `uv run pytest tests/mcp_servers/git/ -q`.

## Completion criteria

git checkout landing is verified where observable, the TOCTOU re-check is real (not a
no-op), and existing checkout/detached-head/pull paths remain correct.

## Out of scope

Other servers' postconditions, and any redesign of the five-layer model.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fill postcondition gaps in repository_state.py | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: git doc is a separate row |

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
- **Requirement ID**: `REQ-003` (postcondition verification; git checkout + TOCTOU gaps)
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `scripts/mcp_servers/git/repository_state.py`

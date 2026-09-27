## Goal

Fix 2 unrelated test-fixture gaps in `tests/agent/test_tool_runner.py`: (1) initialize `ctx.turn.pending_approval_id = None` in the shared `_make_ctx()` helper, since it currently defaults to a truthy Mock and causes `RepositoryGateway._gate_write()` to always deny writes as "approval pending" (REQ-001); (2) add valid `owner`/`repo` args to `test_two_scope_groups_all_execute`'s `github_push_files` call, which currently trips an unrelated `check_allowed_repo` preflight check (REQ-002).

## Scope

In scope: `_make_ctx()`'s field initialization and `test_two_scope_groups_all_execute`'s `github_pc` args, both in this file. Out of scope: `scripts/agent/repository_gateway.py::_gate_write`'s pending-approval-deny check and `scripts/agent/tool_policy.py::check_allowed_repo` — both confirmed already correct and intentional.

## Assumptions

- No other test in this file currently depends on `ctx.turn.pending_approval_id` being truthy-by-default — to be confirmed by running the full file after the fix (per the Plan's own Risk mitigation); if a regression appears, scope the `None` initialization to only `TestRunApprovalGateEndToEnd`'s own test(s) instead of the shared helper.

## Design decisions

- REQ-001: initialize `ctx.turn.pending_approval_id = None` in `_make_ctx()` alongside its existing explicit field assignments (`ctx.turn.current_turn_id`, etc.) — the minimal, most natural place for this fix given the helper's own existing style.
- REQ-002: add `{"owner": "org", "repo": "repo"}` to `github_pc`'s args, matching `cfg`'s `approval_github_allowed_repos=["org/repo"]` fixture value exactly.

## Alternatives considered

- REQ-001: scoping the `None` initialization only to `TestRunApprovalGateEndToEnd`'s tests via a local override, rather than the shared helper: considered as the fallback if the full-file rerun (Validation plan) reveals a conflict — this document's primary approach is the shared-helper fix, per the Plan's stated preference, with this alternative held in reserve.

## Implementation

### Target file

`tests/agent/test_tool_runner.py`

### Procedure

1. **REQ-001**: re-confirm `_make_ctx()`'s exact current body via Read (lines 105-125) — confirm `ctx.turn.pending_approval_id` is still never set (adversarial re-verification). Add `ctx.turn.pending_approval_id = None` immediately after the existing `ctx.turn.current_turn_id = "test-turn-id"` line (or an equivalent natural position among the other `ctx.turn.*`/`ctx.stats.*` assignments).
2. **REQ-002**: re-confirm `test_two_scope_groups_all_execute`'s exact current `github_pc` construction via Read — confirm its `args` is still `{}`. Change it to `{"owner": "org", "repo": "repo"}`.
3. Run the full file (`uv run pytest tests/agent/test_tool_runner.py -q`) after both changes to confirm no other test regresses from REQ-001's shared-helper change — if one does, apply the Alternatives-considered fallback (scope the `None` initialization to only the affected test class) instead.

### Method

Step 1: single-line addition to a shared fixture helper. Step 2: single-value args-dict change in one test. Step 3: full-file verification gate before considering REQ-001 complete.

### Details

- REQ-001 before: `_make_ctx()` sets `ctx.turn.current_turn_id`, `ctx.turn.pending_approval_task_id`, `ctx.session.session_id`, `ctx.workflow.workflow_id`, `ctx.workflow.approval_pending` explicitly, but never `ctx.turn.pending_approval_id` (confirmed absent — this is a *different* file's `_make_ctx` than `test_orchestrator.py`'s own, which does set `ctx.workflow.approval_pending = False`; re-verify this exact file's own field list via Read, since the Plan's evidence describes `tests/agent/test_tool_runner.py`'s own `_make_ctx`, not to be confused with `agent008`'s `test_orchestrator.py` file).
- REQ-001 after: adds `ctx.turn.pending_approval_id = None`.
- REQ-002 before: `github_pc = _pc("github_push_files", {}, spec=ToolSpec(call_id="call_github_push_files", name="github_push_files", resource_scopes=("github_repo:github",), is_write=True))`.
- REQ-002 after: `github_pc = _pc("github_push_files", {"owner": "org", "repo": "repo"}, spec=ToolSpec(...))` (spec unchanged).

## Compatibility considerations

- No production code changes; both fixes are test-fixture corrections.

## Security considerations

N/A: test-only fixes, no security-relevant behavior change (the `check_allowed_repo`/pending-approval production checks themselves are unchanged and remain fully enforced).

## Rollback considerations

- `git revert` the commit, or manually remove the added `pending_approval_id` initialization and revert `github_pc`'s args to `{}`.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_tool_runner.py` | Unit | `uv run pytest tests/agent/test_tool_runner.py -q` | All tests pass, including both previously-failing tests, with no regression from the shared-helper change |

## Completion criteria

- `uv run pytest tests/agent/test_tool_runner.py::TestRunApprovalGateEndToEnd -q` passes, with `executor.execute` genuinely awaited once after the mocked prompt approves.
- `uv run pytest tests/agent/test_tool_runner.py::TestExecuteWithDag::test_two_scope_groups_all_execute -q` passes, with all 3 tools (`write_file`, `github_push_files`, `read_text_file`) executing.
- `uv run pytest tests/agent/test_tool_runner.py -q` (full file) passes with no other regression.

## Out of scope

- `scripts/agent/repository_gateway.py`, `scripts/agent/tool_policy.py` (both confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing the existing 2 tests' fixture gaps is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001, REQ-002: fix `_make_ctx()`'s `pending_approval_id` initialization and `test_two_scope_groups_all_execute`'s args
- **Source issue**: issues/20260927-075258_agent007_tool_runner-execute-not-awaited-and-policy-violation-failures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-085308_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093320
- **Related target files**: tests/agent/test_tool_runner.py

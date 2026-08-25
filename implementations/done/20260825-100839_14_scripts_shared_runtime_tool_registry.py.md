## Goal
- Remove `RuntimeToolRegistry.degraded_servers`, which has no live production
  consumer and is always empty in practice (REQ-007, part 1).

## Scope
- In scope: `RuntimeToolRegistry.__init__()`'s `degraded_servers` parameter, the
  `self._degraded_servers` attribute, the `degraded_servers` property, and the
  reference inside `_is_excluded_server()`. Also, in this same file,
  `apply_policy()`'s `requires_approval` computation/`dataclasses.replace(...)`
  keyword (required in lockstep with `RuntimeTool.requires_approval`'s removal in
  the companion `scripts/shared/runtime_tool.py` document).

## Assumptions
- Pending UNK-02 sign-off; this document assumes the Plan's default (remove). Do not
  implement before sign-off is recorded per `rules/coding.md` Explicit sign-off
  gates, on `plans/20260825-095817_plan.md`.
- The only real production constructor call site,
  `scripts/agent/services/mcp_tool_discovery.py::discover_all()` (both its
  `_dedupe_and_build()` return and its `filtered_registry` construction), never
  passes `degraded_servers=` today — confirmed by reading that file. Removal has no
  effect on that call site.

## Design decisions
- `degraded_servers` is never populated by any real caller, so
  `_is_excluded_server()`'s degraded branch is live code that never triggers in
  practice. Leaving it in place risks a future reader assuming degraded-server
  exclusion is active.
- This file's `apply_policy()` must drop its `requires_approval` computation in the
  same change, since `RuntimeTool` will no longer accept that keyword once the
  companion document's field removal lands — otherwise `dataclasses.replace(...)`
  raises `TypeError` for an unexpected keyword argument.

## Alternatives considered
- Wiring `degraded_servers` to a real health/circuit-breaker signal (UNK-02's other
  option) — deferred; no concrete definition of "degraded" exists yet, and this
  would require new design work the Plan does not yet scope.
- Keeping `degraded_servers` but also fixing `unavailable_servers` to double as the
  degraded signal — rejected; conflates two independent exclusion reasons into one
  mechanism.

## Implementation
### Target file
`scripts/shared/runtime_tool_registry.py`

### Procedure
1. Remove the `degraded_servers: frozenset[str] | None = None` parameter from
   `__init__()`.
2. Remove the `self._degraded_servers = degraded_servers or frozenset()`
   initialization line.
3. Remove `or server_key in self._degraded_servers` from `_is_excluded_server()`,
   leaving only the `unavailable_servers` check; update the docstring's "degraded"
   mention accordingly.
4. Remove the `degraded_servers` property (`@property def degraded_servers`).
5. In `apply_policy()`, remove the `requires_approval` local-variable computation and
   the `requires_approval=requires_approval` keyword from its
   `dataclasses.replace(...)` call (companion change for
   `scripts/shared/runtime_tool.py`'s field removal).

### Method
- Pure deletion refactor. Grep every reference to `degraded_servers` across the
  repository before starting, to confirm the call-site count matches what this
  document assumes.

### Details
- Update the class docstring if it mentions `degraded_servers`.
- Update `apply_policy()`'s docstring if it describes re-deriving
  `requires_approval`/`enabled_for_llm`, removing the `requires_approval` part.

## Compatibility considerations
- `tests/shared/test_runtime_tool_registry.py::test_degraded_servers_excludes_tools_from_degraded_server()` and
  `test_both_unavailable_and_degraded_servers_filter_correctly()` must be removed or
  rewritten to only exercise `unavailable_servers`.
- `test_apply_policy_updates_tier_and_approval_and_llm_visibility()` (and any other
  case asserting `updated.requires_approval`) must drop that assertion, in lockstep
  with the companion `runtime_tool.py` field removal.
- `docs/99_documentation_sync_report.md` already notes `degraded_servers` as an
  existing-but-never-populated field — this change resolves that specific note (the
  document itself is not edited here).

## Security considerations
- N/A: no security/approval decision logic changes. This is dead-code removal; the
  set of excluded tools does not change (it was always effectively governed by
  `unavailable_servers` alone), so no previously-excluded tool becomes exposed.

## Rollback considerations
- Restoring the deleted lines from the commit fully reverts this change. Since the
  field was never load-bearing, reverting has no production-behavior effect either
  way.

## Validation plan
- `uv run pytest tests/shared/test_runtime_tool_registry.py -v` — full suite passes
  after the field removal and the corresponding test updates/deletions above.
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` — confirms no
  impact on the call site (it never passed `degraded_servers=`).

## Out of scope
- `scripts/shared/runtime_tool.py`'s `RuntimeTool.requires_approval` field removal
  itself — companion document.
- `scripts/agent/startup.py`'s read of `runtime_tools.degraded_servers` — separate
  document (this reference must be removed in the same rollout as this file's
  property removal, or `startup.py` will raise `AttributeError`).
- `scripts/agent/services/mcp_tool_discovery.py` — confirmed no change needed
  (separate document records this finding).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260825-144000 | 20260825-144500 | UNK-02 sign-off obtained: remove (the Plan's default option). Landed together with `scripts/shared/runtime_tool.py` and `scripts/agent/startup.py` in one pass |
| 2 | Add or update tests per Validation plan | Completed | 20260825-144500 | 20260825-145500 | Removed `test_degraded_servers_excludes_tools_from_degraded_server` and `test_both_unavailable_and_degraded_servers_filter_correctly`; rewrote 2 `apply_policy` tests to drop `requires_approval` assertions |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260825-145500 | 20260825-150000 | ruff/mypy/lint-imports clean across all 3 coupled files; 216 tests pass across all affected files (`test_runtime_tool.py`, `test_runtime_tool_registry.py`, and 6 caller test files needing the `requires_approval=` kwarg removed); `tests/agent/services/test_mcp_tool_discovery.py` confirmed unaffected (70/72, 2 pre-existing failures) |
| 4 | Update documentation | Completed | 20260825-150000 | 20260825-150300 | Updated CI-003 in `docs/90_shared_90_inconsistencies_and_known_issues.md` (routing.md-mapped) to reflect `requires_approval` removal and flag ADR-013 as stale |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-02 (Plan `plans/20260825-095817_plan.md`): maintainer sign-off needed on wiring vs. removing `degraded_servers`/`requires_approval` | Yes — remove | 20260825-144000 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `scripts/shared/runtime_tool_registry.py` change | 1 | Code Change | Completed | — | — |
| `tests/shared/test_runtime_tool_registry.py` update | 2 | Test | Completed | — | — |
| 6 caller test files' `requires_approval=` kwarg removal | 2 | Test | Completed | — | — |
| `docs/90_shared_90_inconsistencies_and_known_issues.md` CI-003 update | 4 | Doc Change | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/shared/runtime_tool_registry.py

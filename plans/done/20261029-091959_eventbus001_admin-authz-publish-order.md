# Plan: Build and publish the principal map before the configuration in the admin authorization update

## Goal
- Make `update_topics_authorization()` build the replacement `EventBusConfig` and the replacement principal map first and publish both only after every build step succeeded, so a failed principal-map build leaves the previous configuration and the previous principal generation fully active.

## Priority
Low

## Scope
- **In-Scope**: reordering the publish steps in `update_topics_authorization()` (`scripts/eventbus/admin_route.py`); splitting the build half out of `_populate_token_maps()` (`scripts/eventbus/auth.py`) so the build can run without publishing; one failure-path regression test and one no-op publish assertion in `tests/eventbus/test_admin_topics_authorization.py`.
- **Out-of-Scope**: serializing concurrent admin updates, a generation-counter object, any change to the token-to-role matrix or to `Principal` shape, persistence of the update, audit record content, removal of the all-roles tests, changes to startup behavior of `_populate_token_maps()`, and `docs/` edits.
- **Dependencies**: `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md` also edits `update_topics_authorization()` (audit call arguments, lines 139-147) and `tests/eventbus/test_admin_topics_authorization.py`; the regions differ, so land the audit plan first or rebase carefully (sequencing dependency, recorded in Assumptions). `plans/20261028-231549_ebgen001_authz-generation-role-tests.md` is related and needs no ordering (different test file).

## Background
`update_topics_authorization()` (`scripts/eventbus/admin_route.py:74`) validates the body, then for an effective change builds `config = dataclasses.replace(config, **replacements)` and assigns `request.app.state.config = config` (lines 130-131), and only afterwards calls `_populate_token_maps(config)` (lines 134-135). `_populate_token_maps()` (`scripts/eventbus/auth.py:105`) builds the new map in a local dict and publishes it through `publish_principals()` (line 206, defined at line 209) with one assignment; the archived in-place `clear()` window no longer exists. The remaining defect is the order across the two publish targets: if the build raises, the new configuration stays published next to the old principal map.

## Problem
The configuration publish and the principal-map publish are two separate steps in a fixed order. A failure of the second leaves a mixed generation. The existing failure-path test `test_invalid_body_rejected_without_corrupting_state` (`tests/eventbus/test_admin_topics_authorization.py:242`) covers only body validation (a 422 before any state change), not a failing principal-map build.

## Reason for Change
Authorization state is security-sensitive, and a failed update should leave the previous generation fully active. Severity is Low: no route-reachable input was found that makes the build raise (the update replaces only `consumer_authorization` and `topic_authorization`, and the token-field checks depend on token fields the update does not touch). This is a defensive ordering fix, not a reproduced defect, and it is not time-sensitive.

## Implementation Intent
Order the steps as: validate, build the replacement `EventBusConfig` without publishing it, build the replacement principal map from that config, then publish both. Keep `_populate_token_maps()` as the startup entry point (build then publish, behavior unchanged) and expose the build half as a private helper in `scripts/eventbus/auth.py` that returns the map. Prefer this smallest split over a generation object.

## Requirements
- `REQ-001`: `update_topics_authorization()` assigns `request.app.state.config` and publishes the principal map only after both the replacement config and the replacement principal map were built successfully; if any build step raises, neither is published.
- `REQ-002`: the principal-map build is available as a function that returns the map without publishing it, and `_populate_token_maps()` keeps its current startup behavior and its fail-closed errors (duplicate non-empty token, `consumer_token` without `consumer_authorization`) without exposing token values.
- `REQ-003`: a regression test shows that when the principal-map build raises during an effective admin update, `app.state.config` and the active principal map are unchanged and the route does not report success.
- `REQ-004`: the route's request and response contract (`status`, `persistent`, `changed`), the runtime-only persistence contract, and the no-op behavior (neither config nor principal map published) are unchanged and pinned by tests.

## Implementation Target Files
**Freeze status**: Frozen (every row is `Verified`; `issue-to-plan` Step 8b
Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/eventbus/auth.py | Modify | Split `_populate_token_maps()` into a map-returning build helper and the existing publish; startup behavior unchanged | REQ-002; AC-2 | `auth.py:105` `_populate_token_maps` builds `new_map` (line 148) and calls `publish_principals(new_map)` at line 206; `publish_principals` defined at line 209 (checked in Step 2) | tests/eventbus/test_eventbus_auth.py (existing build-new-then-swap tests, lines ~1725-1806), tests/eventbus/test_eventbus_config.py | Verified |
| scripts/eventbus/admin_route.py | Modify | Build the replacement config and principal map first, then publish both; import the build helper and `publish_principals` | REQ-001, REQ-004; AC-1, AC-3 | `admin_route.py:130-131` config assigned, `:134-135` `_populate_token_maps(config)` called after it; import at line 11 (checked in Step 2) | tests/eventbus/test_admin_topics_authorization.py | Verified |
| tests/eventbus/test_admin_topics_authorization.py | Modify | Add the failing-build regression test and the no-op publish assertion | REQ-003, REQ-004; AC-1, AC-3 | `TestValidation.test_invalid_body_rejected_without_corrupting_state` at line 242 covers only body validation; `admin_client` fixture at lines 17-73 builds the app via `TestClient(eb_app.app)` (checked in Step 3) | The new tests themselves | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| tests/eventbus/eventbus_helpers.py | `principal_map()` accessor used by the existing tests resolves the live module-level map (lines ~197-198) | REQ-003 |
| tests/eventbus/test_eventbus_auth.py | Existing atomic-publish and build-failure tests of `_populate_token_maps` (lines ~1725-1806) must stay green | REQ-002 |
| scripts/eventbus/app.py | Startup caller of `_populate_token_maps(app.state.config)` (line 76) that must keep its behavior | REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-003): when the principal-map build raises during an effective admin update, `app.state.config` is the previous config object, the active principal map is the previous map object, and the response is not a success (`status_code` is not 200, or the exception propagates).
- `AC-2` (REQ-002): `_populate_token_maps()` still publishes exactly the map the build helper returns, and the existing tests of duplicate-token and missing-`consumer_authorization` failures pass unchanged.
- `AC-3` (REQ-001, REQ-004): a successful effective update publishes the new config and the new principal map; a no-op update publishes neither; the response keeps `status`, `persistent`, `changed`.

## Tests
- `T1` (REQ-003): new test patches the build helper as imported in `eventbus.admin_route` to raise during an effective update, then asserts the unchanged `app.state.config`, the unchanged principal map object, and a non-success outcome.
- `T2` (REQ-004): extend or add a test asserting that a no-op update leaves the principal map object and `app.state.config` identical.
- `T3` (REQ-001, REQ-002, REQ-004): existing tests in `tests/eventbus/test_admin_topics_authorization.py` and `tests/eventbus/test_eventbus_auth.py` pass unchanged.

## Documentation Impact
N/A: no `docs/*.md` update required. The build helper is private (`_`-prefixed), so the generated `docs/24_eventbus/eventbus_08_reference_api.md` table is not affected, and no `docs/24_eventbus/` text was found that states the old order (`rg` for `principal` and `update_topics_authorization` in `docs/24_eventbus/`, checked in Step 2). `tools/generate_reference_table.py --check` is run to confirm (REQ-002).

## Assumptions
- The build and publish are split with a private helper rather than a generation object (judgment call per the Issue's Implementation Intent); falsifiable if the implementation shows the helper cannot return the map without changing startup behavior.
- Sequencing with `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`: both touch `scripts/eventbus/admin_route.py` and `tests/eventbus/test_admin_topics_authorization.py` in different regions (publish order versus audit call arguments); compatible, with a rebase needed if the audit plan lands first.
- No thread-based reader of the authorization config or principal map was found: `get_config(request)` / `request.app.state.config` reads in `ack_route.py:128,159`, `health_route.py:38`, `subscribe_route.py:42,114` are inside async handlers, and after `await request.json()` the update handler has no further `await`, so coroutines cannot interleave between the two publishes (checked in Step 3).
- The route does not catch a build exception: an unhandled exception yields a 500 (or propagates through `TestClient`), which counts as "not success"; adding a handler is out of scope.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner wants production code changed for a build-failure path that no route input reaches | Owner decision; the Issue states it is a defensive fix and allows closing it as not needed | Confirm at plan approval; if declined, stop before the implementation procedure and report | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/eventbus/admin_route.py | Modify | Low — one route handler; the response contract is unchanged (checked in Step 3) | N/A | N/A | not applicable (rsynced) |
| scripts/eventbus/auth.py | Modify | Medium — `_populate_token_maps` is called at startup (`app.py:76`) and by many tests; its behavior must not change (checked in Step 3) | N/A | N/A | not applicable (rsynced) |
| tests/eventbus/test_admin_topics_authorization.py | Modify | Low — test-only addition | N/A | N/A | not applicable (rsynced) |

## Design
Path A classification: 3 target files, no public or runtime-facing interface change (the new helper is private), no schema change.

Resulting order in `update_topics_authorization()` for an effective change: build `new_config = dataclasses.replace(config, **replacements)`; build `new_map` from `new_config` with the private helper; then assign `request.app.state.config = new_config` and call `publish_principals(new_map)`. No `await` sits between the two publishes, so the pair is observed together by coroutines. `_populate_token_maps(config)` becomes build-then-publish and keeps its current docstring guarantee (previous generation stays in force on a build error). Validation quality baseline (Step 5): `radon cc` grades `update_topics_authorization` C (16) and `_populate_token_maps` C (19), `auth.py` is 15596 B and `admin_route.py` 5842 B (both under the 20480 B gate, no baseline entry); `vulture` reports only pre-existing findings outside `scripts/eventbus/`; `bandit` reports Low only (0 Medium/High). The `diff-cover` baseline number was not measured in this phase (coverage run deferred to implementation; the Plan requires reaching the `rules/toolchain.md` threshold).

## Implementation steps
1. **Phase 1: Split the principal-map build from its publish**
   - [ ] Move the map-building body of `_populate_token_maps()` into a private helper that returns `dict[str, Principal]`; `_populate_token_maps()` calls it and then `publish_principals()` (REQ-002; File Path: scripts/eventbus/auth.py)
2. **Phase 2: Reorder the admin update**
   - [ ] In `update_topics_authorization()`, build the replacement config and the replacement map first, then assign `app.state.config` and call `publish_principals()`; keep the no-op, response, audit-call, and logging behavior unchanged (REQ-001, REQ-004; File Path: scripts/eventbus/admin_route.py)
3. **Phase 3: Regression tests**
   - [ ] Add the failing-build test and the no-op identity assertion, patching the helper at its import location in `eventbus.admin_route` (REQ-003, REQ-004; File Path: tests/eventbus/test_admin_topics_authorization.py)
4. **Phase 4: Deployment & Verification**
   - [ ] Run the validation plan below; commit and push, then hand off to `skills/deploy/SKILL.md` (deploying is the user's decision, it has an approval gate) (REQ-001, REQ-002; File Path: scripts/eventbus/admin_route.py, scripts/eventbus/auth.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_admin_topics_authorization.py | Unit/Integration (new failure path, no-op identity) | `uv run pytest tests/eventbus/test_admin_topics_authorization.py -v` | New tests pass; existing tests unchanged |
| scripts/eventbus/auth.py | Regression | `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_eventbus_config.py -v` | Existing build-new-then-swap and fail-closed tests pass unchanged |
| scripts/eventbus | Package regression | `uv run pytest tests/eventbus` | All pass |
| scripts/eventbus/admin_route.py, scripts/eventbus/auth.py | Static | `uv run ruff check scripts/eventbus tests/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/eventbus -c pyproject.toml -ll` | No errors; no Medium/High |
| scripts/eventbus | Generated reference | `uv run python tools/generate_reference_table.py --check`; `uv run python tools/check_module_size.py`; `uv run python tools/check_mock_patch_targets.py` | Exit 0 |
| whole change | Architecture / coverage | `PYTHONPATH=scripts uv run lint-imports`; `uv run diff-cover coverage.xml --compare-branch=master` | No violations; changed-line coverage meets `rules/toolchain.md` threshold |

## Risks
- **Risk**: the split changes startup behavior or the fail-closed errors of `_populate_token_maps()` → **Mitigation**: the helper is a pure move of the build body; existing tests of duplicate-token, missing-`consumer_authorization`, and atomic publish run unchanged (`T3`).
- **Risk**: the new test patches the wrong symbol and never takes effect (the route imports the symbol at module level) → **Mitigation**: patch `eventbus.admin_route.<helper>`; `tools/check_mock_patch_targets.py` verifies the target.
- **Risk**: merge conflict with the audit plan in `update_topics_authorization()` and the same test file → **Mitigation**: regions differ; land the audit plan first or rebase; Step 8b overlap report is recorded in Assumptions.
- **Risk**: the change is unreachable from any route input and adds code for no observed defect → **Mitigation**: UNK-01 records the owner decision; the change is small and defensive.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Split principal-map build from publish (scripts/eventbus/auth.py) | In Progress | — | — | REQ-002 |
| 2 | Reorder publish steps in `update_topics_authorization()` (scripts/eventbus/admin_route.py) | In Progress | — | — | REQ-001, REQ-004 |
| 3 | Add failing-build and no-op regression tests (tests/eventbus/test_admin_topics_authorization.py) | In Progress | — | — | REQ-003, REQ-004 |
| 4 | Run validation plan; deploy hand-off | Pending | — | — | Deploy is user-gated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261029-101422_01_scripts_eventbus_auth.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261029-101422_02_scripts_eventbus_admin_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261029-101422_03_tests_eventbus_test_admin_topics_authorization.py.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-090157_eventbus001_admin-authz-publish-order.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-091959
- **Related target files**: scripts/eventbus/admin_route.py, scripts/eventbus/auth.py, tests/eventbus/test_admin_topics_authorization.py

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (reorder); confirmed at `admin_route.py:130-135` (Step 2) | scripts/eventbus/admin_route.py | Phase 2 | AC-1, AC-3 | T1, T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (split build/publish); confirmed at `auth.py:105,148,206,209` (Step 2) | scripts/eventbus/auth.py | Phase 1 | AC-2 | T3 | Confirmed by repository evidence |
| REQ-003 | Required Changes (regression test); Acceptance Criteria 1 | tests/eventbus/test_admin_topics_authorization.py | Phase 3 | AC-1 | T1 | Explicit in issue |
| REQ-004 | Constraints; Acceptance Criteria 2-3 | scripts/eventbus/admin_route.py | Phase 2 | AC-3 | T2, T3 | Explicit in issue |
| REQ-004 | Constraints; Acceptance Criteria 2-3 | tests/eventbus/test_admin_topics_authorization.py | Phase 3 | AC-3 | T2 | Explicit in issue |
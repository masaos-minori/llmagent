## Goal
- Make the conditional publication of an authorization generation explicit and tested: one publish-if-current function in `scripts/eventbus/auth.py` used by both writers (the admin route and the TTL sweep), and authorization state owned by the generation snapshot instead of being split between `app.state.config` and `AuthzGeneration`, so a later change cannot reintroduce lost updates.

## Priority
Medium

## Scope
- **In-Scope**: Add a publish-if-current function to `scripts/eventbus/auth.py`; use it from `scripts/eventbus/admin_route.py` (the losing request returns 409) and `scripts/eventbus/authz_ttl.py` (the losing sweep aborts and retries on the next interval); make the admin writer derive its base config from the in-force generation and stop both writers from replacing `app.state.config`; add the interleaving, race, mixed-generation, and service-config-stability tests; regenerate the generated reference output; name the new function in the ADR-013 implementation references.
- **Out-of-Scope**: request validation order and the metadata-only rejection (the admin TTL-precedence Plan); ADR-013 invariant coverage registration (adrr003); multi-process deployments (authorization state stays process-local); any change to the 409 contract, the audit output, or ADR decisions; a signature change of `sweep_expired_authorizations`.
- **Dependencies**: Should follow the admin TTL-precedence Plan (adrr001) to avoid overlapping edits in `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`, and ADR-013 (a sequencing dependency judged in Step 8b). Blocks the ADR-013 invariant coverage Plan (adrr003), which needs the final test node names.
  - **Depends on**: plans/20261128-172318_adrr001_admin-ttl-precedence.md | phase all | both Plans edit `scripts/eventbus/admin_route.py`, its test file, and ADR-013; implementing adrr001 first avoids merge conflicts and keeps test names stable

## Background
Verified against `HEAD` cc659c70a on 2026-11-28 (checked in Step 2, Step 3). The Issue's source note claims lost updates and mixed-generation reads today; that is not reproducible in the current design:
- `publish_generation()` is a plain module-level assignment (`scripts/eventbus/auth.py:227-235`).
- The admin handler reads `current_generation()`, builds the next generation, then assigns `request.app.state.config` and calls `publish_generation()` (`scripts/eventbus/admin_route.py:211-212`). The only `await` in the handler is `await request.json()` at the top. The sweep re-checks `current_generation() is not gen` and then publishes (`scripts/eventbus/authz_ttl.py:80-95`) with no await in between; `authz_sweep_loop` calls it synchronously on the event loop. The service starts as one uvicorn process (`uvicorn.Config("eventbus.app:app", ...)` has no `workers` argument, `scripts/eventbus/app.py:273-279`) and `deploy/` sets no worker count.
- The two assignments (`app.state.config`, then `publish_generation`) are separate statements in both writers (`admin_route.py:211-212`, `authz_ttl.py:94-95`). ADR-013 Decision Detail 14 describes the sweep as compare-and-swap.
- `test_same_expected_generation_second_request_409` (`tests/eventbus/test_admin_topics_authorization.py:235`) and `test_racing_updates_publish_one_generation` (`tests/eventbus/test_authz_generation_ttl.py:82`) cover two updates from one generation without a forced interleave; `test_sweep_aborts_on_concurrent_generation_bump` (`:172`) covers the sweep abort.
- No request-time reader reads `consumer_authorization` from `app.state.config`: `rg consumer_authorization scripts/eventbus` shows only the principal-map builder (`auth.py:159-175`, from the config passed to it), the sweep (`authz_ttl.py`, from `gen.config`), and the admin writer, which reads the base from `get_config(request)` (`admin_route.py:153,162`). `resolve_principal` reads only `generation.principals` (`auth.py:251-257`).
- Worker-thread readers: `current_generation()` is called from `admin_route.py`, `authz_ttl.py`, `app.py:77` (startup) and `auth.py` (`resolve_principal`, an `async def`); the only `asyncio.to_thread` use is the database helper in `route_helpers.py:131-169`. No authorization reader runs in a worker thread.
- Not found: any evidence of duplicate `N -> N+1` audit records or a reader that observes mixed state.

## Problem
The correctness of generation publication depends on an unwritten property (no suspension point inside the critical section). The conditional-publish logic is duplicated between the admin route and the sweep, and runtime authorization state is split between `app.state.config` (the admin writer's read-modify-write base) and `AuthzGeneration`.

## Reason for Change
A future `await` inside either writer would silently introduce lost updates, and no test would fail. Making the boundary explicit is cheap now and removes the split authority.

## Implementation Intent
Provide one function in `scripts/eventbus/auth.py` that publishes a new generation only when the in-force generation is the one the writer built from, and returns whether it published. Both writers use it. The admin writer takes its base config from the in-force generation, so `app.state.config` keeps only startup-wide service configuration. Tests force the interleaving by hooking the principal-map builder between read and publish.

## Requirements
- `REQ-001`: `scripts/eventbus/auth.py` provides a publish-if-current function (publish only when the in-force generation `is` the expected object, return a bool); the admin route and the sweep both use it. A losing admin request returns 409 `generation_conflict`; a losing sweep publishes nothing, emits no audit record, and retries on the next interval.
- `REQ-002`: Neither writer replaces `app.state.config`; the admin writer derives its base config from the in-force generation's config, so authorization config and principals always come from one generation snapshot and unrelated service configuration is unchanged by an authorization update.
- `REQ-003`: Tests force an interleave between read and publish for two admin updates and for an admin update racing a sweep, and add a mixed-generation consistency test and a service-config stability test; the existing restart-baseline test stays green.
- `REQ-004`: Single, uncontended requests behave exactly as before: the 409 body, the audit records, the response fields, and the sweep's return values do not change.
- `REQ-005`: The generated reference output and the ADR-013 implementation references name the new function; the restart behavior is already stated by ADR-013 Decision Detail 15 and is not reworded.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/auth.py` | Modify: add the publish-if-current function next to `publish_generation` | Both writers need one conditional publication; `publish_generation` is unconditional (used for the startup baseline and stays) | `REQ-001`, `REQ-004`; AC-1, AC-2, AC-5 | `publish_generation` at `:227-235`; `current_generation` at `:238`; file is 15636 B against the 24576 B gate (checked in Step 3) | `tests/eventbus/test_authz_generation_ttl.py` | Verified |
| `scripts/eventbus/admin_route.py` | Modify: base config from `current_gen.config`, publish through the new function, return 409 on a lost race, drop the `app.state.config` assignment and the `get_config` import | The writer reads `get_config(request)` and replaces `request.app.state.config` before publishing | `REQ-001`, `REQ-002`, `REQ-004`; AC-1, AC-3, AC-5 | `config = get_config(request)` at `:153`; `request.app.state.config = new_gen.config` and `publish_generation(new_gen)` at `:211-212` (checked in Step 3) | `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_authz_generation_ttl.py` | Verified |
| `scripts/eventbus/authz_ttl.py` | Modify: replace the check-then-publish with the new function, drop the `app.state.config` assignment | The sweep re-checks identity and then publishes in two statements and replaces `app.state.config` | `REQ-001`, `REQ-002`, `REQ-004`; AC-2, AC-3, AC-5 | `if current_generation() is not gen` at `:80`; `app.state.config = new_gen.config` and `publish_generation(new_gen)` at `:94-95` (checked in Step 3) | `tests/eventbus/test_authz_generation_ttl.py` | Verified |
| `tests/eventbus/test_admin_topics_authorization.py` | Modify: add the forced-interleave admin test and change the assertion that expects `app.state.config` to be replaced | `test_effective_update_publishes_config_and_map` asserts `eb_app.app.state.config is not config_before` (`:564`), which contradicts `REQ-002` | `REQ-002`, `REQ-003`; AC-1, AC-3 | Assertion at `:564`; failed-rebuild and no-op tests assert `is config_before` (`:520`, `:543`) and stay valid (checked in Step 3) | `tests/eventbus/test_admin_topics_authorization.py` | Verified |
| `tests/eventbus/test_authz_generation_ttl.py` | Modify: add the admin-versus-sweep race test, the publish-if-current unit tests, the mixed-generation test, and the service-config stability test | No test forces an interleave between read and publish or checks that service config is unchanged by an update | `REQ-001`, `REQ-002`, `REQ-003`; AC-1 to AC-4 | Existing classes `TestGenerationSemantics`, `TestTTLExpirySweep`, `TestRestartBaselineAudit` (`:49`, `:106`, `:278`); `:234-249` already asserts `app.state.config is config_before` for a failed rebuild (checked in Step 3) | `tests/eventbus/test_authz_generation_ttl.py` | Verified |
| `registry/manifests/eventbus_api.yaml` | Modify (generated): regenerate so it lists the new function | The manifest is generated from `scripts/eventbus/` signatures and docstring first lines | `REQ-005`; AC-6 | Entries for `publish_generation` at `:86-90` (checked in Step 3) | `tests/tools/test_generate_reference_table.py` | Verified |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify (generated): regenerate the `auth.py` table | The generated block lists each `auth.py` function | `REQ-005`; AC-6 | Row for `publish_generation` at `:65` (checked in Step 3) | `tests/tools/test_generate_reference_table.py` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify: name the new function in the `auth.py` line of "Implementation References" | The component list names functions per file; no decision text changes | `REQ-005`; AC-6 | `auth.py` line at `:312` lists `attach_request_id_middleware()`, `require_role()`, `require_consumer_identity()` (checked in Step 3) | `N/A: documentation row, checked by ADR checkers` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.
- Write every `File Path` cell, every `tests/...py` path in `Related Tests`, and every path in
  `Implementation steps` in backticks.
- Order rows by implementation sequence: row N is the Nth implementation unit, and
  `plan-to-implementation-procedure` derives each procedure's `seq` from this 1-indexed
  position, so the rows of a `Frozen` table MUST NOT be reordered. Canonical
  implementation order lives in this table.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/route_helpers.py` | `get_config` and `app_get_config` stay for the startup-wide service config; the Issue listed this file, but no change is needed because the admin writer reads the generation instead (see Design) | `scripts/eventbus/admin_route.py`; `REQ-002` |
| `scripts/eventbus/app.py` | Startup publishes the baseline through `build_and_publish_generation`; the sweep task and `uvicorn.Config` (single process) are created here | `scripts/eventbus/authz_ttl.py`; `REQ-001` |
| `tests/eventbus/eventbus_helpers.py` | `post_topics_authorization` and `current_principals` are the helpers the new tests use | `tests/eventbus/test_admin_topics_authorization.py`; `REQ-003` |
| `tools/generate_reference_table.py` | Generates the two reference outputs; run it, do not hand-edit them | `registry/manifests/eventbus_api.yaml`; `REQ-005` |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-003`): two admin updates from one expected generation, with a forced interleave between read and publish, produce exactly one 200 and one 409 `generation_conflict`; the loser changes no state and emits no audit record.
- AC-2 (`REQ-001`, `REQ-003`): an admin update racing a sweep never loses a committed update; the losing side publishes nothing; generation numbers stay strictly increasing without duplicates.
- AC-3 (`REQ-002`, `REQ-003`): after authorization updates and a sweep, `app.state.config` is the same object as before and unrelated service fields are unchanged, while `current_generation().config` carries the new authorization.
- AC-4 (`REQ-002`, `REQ-003`): for every published generation, `principals` equals the principal map rebuilt from that generation's own `config` (no mixed-generation state).
- AC-5 (`REQ-004`): the existing admin and TTL tests pass unchanged except the one assertion changed by `REQ-002`.
- AC-6 (`REQ-005`): `uv run python tools/generate_reference_table.py --check`, `check_adr_structure.py`, and `check_adr_invariant_matrix.py` pass.

## Tests
- `REQ-001`: a unit test of the publish-if-current function (match publishes and returns `True`; mismatch publishes nothing and returns `False`); a barrier-controlled concurrent admin update test; an admin-versus-sweep race test in both orders.
- `REQ-002`: a service-config stability test (`app.state.config` identity and unrelated fields after updates and a sweep); the changed assertion in `test_effective_update_publishes_config_and_map`.
- `REQ-003`: a mixed-generation test (each generation's principals match its own config); the existing `TestRestartBaselineAudit::test_runtime_only_removal_is_restored_by_restart` covers the restart baseline and is cited, not duplicated.
- `REQ-004`: the existing 409, audit, and sweep tests run unchanged.
- `REQ-005`: reference generation check and ADR checkers.

## Documentation Impact
- `REQ-005` drives regeneration of the EventBus reference output (found through `docs/00_index.md` "Document References by Task", EventBus row) and a one-line addition to the ADR-013 "Implementation References" component list. No ADR decision text changes; Decision Detail 15 already states the restart behavior.

## Assumptions
- The service is single-process; an in-process identity compare is sufficient. Evidence: `uvicorn.Config(...)` has no `workers` argument and `deploy/` sets none (checked in Step 3). A future multi-worker deployment is out of scope.
- No authorization reader runs in a worker thread (checked in Step 3 by `rg` over `scripts/eventbus`).
- The interleave in tests is forced by hooking the principal-map builder (`_build_principal_map`) so a competing generation is published between the writer's read and its publish; the handlers keep no `await` between those points, so no async barrier is available or needed.
- `sweep_expired_authorizations(app, clock)` keeps its signature (ten call sites in tests plus monkeypatch targets); after the change `app` is unused inside it, which is acceptable for a compatibility-preserving hardening and is noted in the docstring.
- Overlap with the admin TTL-precedence Plan is a sequencing dependency (Step 8b judgment): this Plan is implemented after it.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The admin TTL-precedence Plan (adrr001) is not yet implemented; this Plan edits the same module, test file, and ADR | Its Execution Status rows are `Pending` | Implement adrr001 first (structured `Depends on` in Scope); re-read `scripts/eventbus/admin_route.py` before generating procedures | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/auth.py` | Modify | Medium: imported by every EventBus route module; only an addition, `publish_generation` is unchanged | 8 | High (100% single author) | not applicable (rsynced) |
| `scripts/eventbus/admin_route.py` | Modify | Medium: single router, included by `scripts/eventbus/app.py:241` | 5 | High (single author) | not applicable (rsynced) |
| `scripts/eventbus/authz_ttl.py` | Modify | Low: used by `scripts/eventbus/app.py` and tests only | 5 | High (single author) | not applicable (rsynced) |
| `tests/eventbus/test_admin_topics_authorization.py` | Modify | Low: test-only | 8 | High (100% single author) | not applicable (rsynced) |
| `tests/eventbus/test_authz_generation_ttl.py` | Modify | Low: test-only | 8 | High (100% single author) | not applicable (rsynced) |
| `registry/manifests/eventbus_api.yaml` | Modify | Low: generated manifest | 14 | High (single author) | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify | Low: generated documentation | 16 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Low: documentation only | 13 | High (100% single author) | not applicable (rsynced) |

## Design
- Path B (adds a function to a shared module, changes the runtime ownership of authorization state, more than 3 target rows).
- New function (name for the procedure to settle, for example `publish_generation_if_current(expected, new_generation) -> bool`): compare `_CURRENT_GENERATION is expected`; on a match assign and return `True`, otherwise return `False`. `publish_generation` stays unconditional for the startup baseline (`build_and_publish_generation`). The compare and assignment contain no `await`, so the function is atomic on the event loop; its docstring states that property.
- Admin writer: take `current_gen.config` as the base for `dataclasses.replace`, replace `get_config(request)` and the `config.consumer_authorization` read with `current_gen.config`, publish through the new function, and on `False` return the same 409 body as the stale-generation path (`expected_generation` from the request, `current_generation` re-read). Remove the `request.app.state.config` assignment and the `get_config` import. The audit record and success response stay as they are.
- Sweep: build the removal generation as now, then `if not publish_if_current(gen, new_gen): log and return None`; remove the earlier identity check (now inside the function) and the `app.state.config` assignment. The audit record and return value stay as they are.
- Why `route_helpers.py` is not a target: `get_config`/`app_get_config` remain for startup-wide service config (`authz_sweep_interval_seconds` is read by `authz_sweep_loop` through `app_get_config`); the generation snapshot already carries the authorization config, so no new helper is needed.
- Alternatives rejected: an `asyncio.Lock` around the writers (does not protect the sweep's synchronous path and hides the invariant); making `AuthzGeneration` own the whole service config (widens scope beyond authorization).
- Consumer scan (`rg` over `scripts/` and `tests/`): readers of `app.state.config` after this change keep working because the field values other than `consumer_authorization` are unchanged; no `scripts/` module reads `app.state.config.consumer_authorization`; tests reading `app.state.config` (`tests/eventbus/test_eventbus_auth.py:1401-1409`, `tests/eventbus/test_eventbus_requeue_edge_cases.py:331`, `tests/eventbus/test_eventbus_restart_resume.py`) do not depend on an authorization replacement (not affected). Tests asserting replacement: `tests/eventbus/test_admin_topics_authorization.py:564` (target row).
- Predictable fallout check: module size of `scripts/eventbus/auth.py` is 15636 B against the 24576 B gate and gains under 1 KB (not affected); no instruction file gains text (not affected); no tool is added or removed (not affected); pinned counts: `rg` over `tests/` finds no assertion on the number of `auth.py` functions (not affected, confirm with the full suite); generated blocks: the new function changes `registry/manifests/eventbus_api.yaml` and `docs/24_eventbus/eventbus_08_reference_api.md` (target rows, regenerate with `generate_reference_table.py`).
- Persisted schema check: not applicable (no DDL; authorization state is process-local and never persisted, ADR-013 Decision Details 15-16).
- Operational dependency inspection: single EventBus process; the change restarts only that service on deploy.

## Implementation steps
1. **Phase 1: Publish-if-current function (`REQ-001`, `REQ-004`)**
   - [ ] Add the function and its docstring to `scripts/eventbus/auth.py` (`REQ-001`, `REQ-004`)
2. **Phase 2: Admin writer (`REQ-001`, `REQ-002`, `REQ-004`)**
   - [ ] Switch the admin writer to the generation base config and the new function, return 409 on a lost race, drop the `app.state.config` assignment (`REQ-001`, `REQ-002`, `REQ-004`; `scripts/eventbus/admin_route.py`)
3. **Phase 3: Sweep writer (`REQ-001`, `REQ-002`, `REQ-004`)**
   - [ ] Switch the sweep to the new function and drop the `app.state.config` assignment (`REQ-001`, `REQ-002`, `REQ-004`; `scripts/eventbus/authz_ttl.py`)
4. **Phase 4: Admin tests (`REQ-002`, `REQ-003`)**
   - [ ] Add the forced-interleave admin test and change the assertion at `:564` (`REQ-002`, `REQ-003`; `tests/eventbus/test_admin_topics_authorization.py`)
5. **Phase 5: Generation and race tests (`REQ-001`, `REQ-002`, `REQ-003`)**
   - [ ] Add the unit, admin-versus-sweep race, mixed-generation, and service-config stability tests (`REQ-001`, `REQ-002`, `REQ-003`; `tests/eventbus/test_authz_generation_ttl.py`)
6. **Phase 6: Generated reference output (`REQ-005`)**
   - [ ] Run `uv run python tools/generate_reference_table.py` and review the diff (`REQ-005`; `registry/manifests/eventbus_api.yaml`, `docs/24_eventbus/eventbus_08_reference_api.md`)
7. **Phase 7: ADR component list, validation, and deploy hand-off (`REQ-005`)**
   - [ ] Name the new function in the `auth.py` line of "Implementation References" (`REQ-005`; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
   - [ ] Run the validation plan; because `scripts/` changes, commit and push first, then hand off to the deploy skill (the user decides whether to deploy; it has an approval gate)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/auth.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/authz_ttl.py` | Unit and integration (TestClient through the production lifespan, forced interleave) | `uv run pytest tests/eventbus -q` | All pass, including the new tests |
| `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_authz_generation_ttl.py` | Integration | `uv run pytest tests/eventbus/test_admin_topics_authorization.py tests/eventbus/test_authz_generation_ttl.py -q` | New and existing tests pass |
| `scripts/eventbus/auth.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/authz_ttl.py` | Static | `uv run ruff format scripts/eventbus && uv run ruff check scripts/eventbus && uv run mypy --no-namespace-packages scripts/ tests/eventbus tools && uv run bandit -c pyproject.toml -r scripts/eventbus` | Clean |
| `scripts/eventbus/authz_ttl.py` | Complexity | `uv run radon cc scripts/eventbus/authz_ttl.py scripts/eventbus/auth.py -s` | `sweep_expired_authorizations` stays at or below its baseline C (13) |
| `registry/manifests/eventbus_api.yaml`, `docs/24_eventbus/eventbus_08_reference_api.md` | Generated-output check | `uv run python tools/generate_reference_table.py --check` | No drift |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Documentation checks | `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_invariant_matrix.py` | No findings |
| All target files | Gate run | `uv run python tools/run_validation_gates.py --full` | Pass; run `diff-cover` per `rules/toolchain.md` section 7 and meet its threshold (baseline recorded at implementation time) |

## Risks
- **Risk**: Removing the `app.state.config` replacement breaks a test or reader that relied on it → **Mitigation**: the consumer scan found no `scripts/` reader of `app.state.config.consumer_authorization`; one test assertion (`:564`) is a target row; run the whole `tests/eventbus` suite and the full gate run.
- **Risk**: A forced interleave that hooks `_build_principal_map` couples the tests to that private name → **Mitigation**: the existing tests already patch `eventbus.admin_route._build_principal_map`; keep the hook in one helper inside each test file.
- **Risk**: Overlapping edits with the admin TTL-precedence Plan → **Mitigation**: the structured `Depends on` in Scope; re-read the module before generating procedures.
- **Risk**: The sweep's unused `app` parameter invites a later cleanup that breaks ten call sites → **Mitigation**: the docstring records why the signature stays; any removal is a separate Issue.
- **Risk**: A multi-worker deployment would make the identity compare process-local only → **Mitigation**: out of scope and stated in Scope and Assumptions; ADR-013 Decision Detail 16 already makes authorization state process-local.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the publish-if-current function to `scripts/eventbus/auth.py` | In Progress | — | — |  |
| 2 | Switch the admin writer in `scripts/eventbus/admin_route.py` | In Progress | — | — |  |
| 3 | Switch the sweep writer in `scripts/eventbus/authz_ttl.py` | In Progress | — | — |  |
| 4 | Add the admin interleave test and fix the assertion in `tests/eventbus/test_admin_topics_authorization.py` | In Progress | — | — |  |
| 5 | Add the race, mixed-generation, and stability tests in `tests/eventbus/test_authz_generation_ttl.py` | In Progress | — | — |  |
| 6 | Regenerate `registry/manifests/eventbus_api.yaml` and `docs/24_eventbus/eventbus_08_reference_api.md` | In Progress | — | — |  |
| 7 | ADR-013 component list in `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, validation, deploy hand-off | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261128-173946_01_scripts_eventbus_auth.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261128-173946_02_scripts_eventbus_admin_route.py.md | 2, 4 | Procedure | Pending | — | — |
| implementations/20261128-173946_03_scripts_eventbus_authz_ttl.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261128-173946_05_tests_eventbus_test_authz_generation_ttl.py.md | 5 | Procedure | Pending | — | — |
| implementations/20261128-173946_06_registry_manifests_eventbus_api.yaml.md | 6 | Procedure | Pending | — | — |
| implementations/20261128-173946_07_docs_24_eventbus_eventbus_08_reference_api.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261128-173946_08_docs_10_adr_adr_02_04_013_eventbus-authentication-authorization.md.md | 7 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261125-103308_adrr002_authz-publication-invariant.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261128-172526
- **Evidence revision**: cc659c70a1811c504ec226a087ba3a39e85578bb
- **Related target files**: `scripts/eventbus/auth.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/authz_ttl.py`, `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_authz_generation_ttl.py`, `registry/manifests/eventbus_api.yaml`, `docs/24_eventbus/eventbus_08_reference_api.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (publish-if-current); `scripts/eventbus/auth.py:227-235` | `scripts/eventbus/auth.py` | Step 1 | AC-1, AC-2 | Publish-if-current unit tests | Confirmed by repository evidence |
| REQ-001 | Issue Required Changes; `scripts/eventbus/admin_route.py:211-212` | `scripts/eventbus/admin_route.py` | Step 2 | AC-1 | Forced-interleave admin test | Confirmed by repository evidence |
| REQ-001 | Issue Required Changes; `scripts/eventbus/authz_ttl.py:80-95` | `scripts/eventbus/authz_ttl.py` | Step 3 | AC-2 | Admin-versus-sweep race test | Confirmed by repository evidence |
| REQ-001 | Issue Testing Expectations | `tests/eventbus/test_admin_topics_authorization.py` | Step 4 | AC-1 | Forced-interleave admin test | Explicit in issue |
| REQ-001 | Issue Testing Expectations | `tests/eventbus/test_authz_generation_ttl.py` | Step 5 | AC-1, AC-2 | Unit and race tests | Explicit in issue |
| REQ-002 | Issue Required Changes (stop replacing `app.state.config`); `scripts/eventbus/admin_route.py:153,211`; no reader of `app.state.config.consumer_authorization` found by `rg` | `scripts/eventbus/admin_route.py` | Step 2 | AC-3, AC-4 | Service-config stability test | Derived from confirmed evidence |
| REQ-002 | Same; `scripts/eventbus/authz_ttl.py:94` | `scripts/eventbus/authz_ttl.py` | Step 3 | AC-3 | Service-config stability test | Derived from confirmed evidence |
| REQ-002 | Same; assertion at `tests/eventbus/test_admin_topics_authorization.py:564` | `tests/eventbus/test_admin_topics_authorization.py` | Step 4 | AC-3 | Changed assertion in `test_effective_update_publishes_config_and_map` | Confirmed by repository evidence |
| REQ-002 | Issue Testing Expectations (mixed-generation reader, service-config stability) | `tests/eventbus/test_authz_generation_ttl.py` | Step 5 | AC-3, AC-4 | Mixed-generation and stability tests | Explicit in issue |
| REQ-003 | Issue Testing Expectations; existing `TestRestartBaselineAudit` | `tests/eventbus/test_admin_topics_authorization.py` | Step 4 | AC-1 | Barrier-style admin test | Explicit in issue |
| REQ-003 | Issue Testing Expectations (admin-versus-sweep race, restart baseline) | `tests/eventbus/test_authz_generation_ttl.py` | Step 5 | AC-2, AC-4 | Race and mixed-generation tests; existing restart test cited | Explicit in issue |
| REQ-004 | Issue Constraints (no behavior change for uncontended requests) | `scripts/eventbus/auth.py` | Step 1 | AC-5 | Existing admin and TTL tests run unchanged | Explicit in issue |
| REQ-004 | Issue Constraints | `scripts/eventbus/admin_route.py` | Step 2 | AC-5 | Existing 409 and audit tests | Explicit in issue |
| REQ-004 | Issue Constraints | `scripts/eventbus/authz_ttl.py` | Step 3 | AC-5 | Existing sweep tests | Explicit in issue |
| REQ-005 | Issue Documentation Impact; generated output lists each `auth.py` function (`docs/24_eventbus/eventbus_08_reference_api.md:65`) | `registry/manifests/eventbus_api.yaml` | Step 6 | AC-6 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-005 | Same | `docs/24_eventbus/eventbus_08_reference_api.md` | Step 6 | AC-6 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-005 | Issue Documentation Impact (ADR component list only); ADR-013 `:312` | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 7 | AC-6 | ADR checkers | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261128-173946 -->
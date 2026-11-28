## Goal
- Make `POST /admin/topics/authorization` follow ADR-013 Decision Detail 13 (invalid `ttl_seconds` is rejected with HTTP 422 before the `expected_generation` comparison is acted on) and reject a body that carries no `consumer_authorization` with HTTP 422, so that 409 is returned only for a structurally valid request with a stale generation.

## Priority
High

## Scope
- **In-Scope**: Reorder the checks in `update_topics_authorization` (TTL type and range validation before the generation-mismatch 409); reject a body without `consumer_authorization` with 422 (maintainer decision recorded in Assumptions); keep an explicitly present but unchanged `consumer_authorization` as 200 with `changed=false`; add the missing tests; update the API reference wording; add one clarifying sentence to ADR-013 Decision Detail 12 for the metadata-only rule.
- **Out-of-Scope**: generation publication atomicity and the publish-if-current function; ADR-013 invariant coverage registration (index and manifest); a non-object JSON body (see UNK-02); changes to the 401/403 precedence; any change to the audit output.
- **Dependencies**: This Plan blocks the ADR-013 invariant coverage Plan (adrr003), which needs the final test node names, and should be implemented before the publication-boundary Plan (adrr002) to avoid overlapping edits in `scripts/eventbus/admin_route.py` and its test file. No other open Issue overlaps `scripts/eventbus/admin_route.py`.

## Background
Verified against `HEAD` cc659c70a on 2026-11-28 (checked in Step 2, Step 3):
- `scripts/eventbus/admin_route.py` compares `expected_generation` against the in-force generation and returns 409 (`:125-133`) before `ttl_seconds` type and range validation (`:135-151`). ADR-013 Decision Detail 13 requires the opposite order for an invalid TTL.
- `consumer_authorization` is optional (`:101-105`); a body with only `expected_generation`, or `expected_generation` plus `ttl_seconds`, reaches the `changed=false` no-op response (`:169-180`). ADR-013 Decision Detail 12 rejects only the empty body `{}` and says a well-formed no-change body returns 200 with `changed: false`; it is silent on a metadata-only body.
- No test combines a stale generation with an invalid TTL. `test_stale_expected_generation_on_noop_body_still_409` covers stale generation with a valid explicit mapping; `test_invalid_ttl_rejected_without_state_change` covers invalid TTL with a current generation.
- The API reference row for the admin endpoint is in `docs/24_eventbus/eventbus_02_api-reference-index.md` (roles table, ADMIN row).
- The issue cited `:166-178` for the no-op response; the current lines are `:169-180` (line drift only, claim confirmed).

## Problem
The order of checks in the admin route differs from the accepted ADR decision, so a stale request with an invalid TTL returns 409 instead of 422. A body without `consumer_authorization` is reported as a successful no-op update.

## Reason for Change
The route is a privileged API whose response codes clients and tests rely on. A documented precedence that the code does not follow makes the contract untrustworthy, and the ADR-013 coverage work (adrr003) needs stable test names for it.

## Implementation Intent
Keep the accepted ADR-013 order: authentication (401) and role (403) via the `require_role` dependency first, then body shape, `consumer_authorization` presence and type, `expected_generation` type, and TTL validation (422), then the generation-conflict handling (409) last. The in-force generation is read once, only to obtain `authz_max_ttl_seconds` for TTL validation and the generation number for the conflict check. Extract the TTL validation into a helper so the handler's cyclomatic complexity (currently D, 22) does not grow.

## Requirements
- `REQ-001`: A request whose `ttl_seconds` is invalid (`0`, a negative number, above `authz_max_ttl_seconds`, a string, or a boolean) returns 422 even when `expected_generation` is stale; the 422 check runs before the generation comparison.
- `REQ-002`: A structurally valid request with a stale `expected_generation` (and a valid or absent `ttl_seconds`) still returns 409 with `error="generation_conflict"`.
- `REQ-003`: A body without `consumer_authorization` (only `expected_generation`, or `expected_generation` plus `ttl_seconds`) returns 422 and changes nothing; an explicitly present but unchanged `consumer_authorization` returns 200 with `changed=false`.
- `REQ-004`: Every rejected request leaves the generation identity, `app.state.config`, principals, expiries, and audit output unchanged; unauthenticated invalid requests return 401 and authenticated non-Admin requests return 403.
- `REQ-005`: The API reference and ADR-013 Decision Detail 12 state the check order and the metadata-only rejection; no ADR decision changes.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/admin_route.py` | Modify: reorder checks, add the `consumer_authorization` presence check, extract TTL validation into a helper | The 409 comparison precedes TTL validation and a metadata-only body falls through to the no-op response | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`; AC-1, AC-2, AC-3, AC-5 | `update_topics_authorization` has the 409 return at `:125-133`, TTL validation at `:135-151`, optional `consumer_authorization` at `:101-105` (checked in Step 3) | `tests/eventbus/test_admin_topics_authorization.py` | Verified |
| `tests/eventbus/test_admin_topics_authorization.py` | Modify: add stale-generation plus invalid-TTL, stale-generation plus valid-TTL, metadata-only body, and 401/403-precedence tests with state-identity and no-audit assertions | No test covers the new order or the metadata-only rejection | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`; AC-1 to AC-5 | Existing `TestTTLValidation::test_invalid_ttl_rejected_without_state_change` (`:343`) and `test_stale_expected_generation_on_noop_body_still_409` (`:275`) cover only the pre-change order; helper `post_topics_authorization` always sends `expected_generation` (`tests/eventbus/eventbus_helpers.py:304-319`) (checked in Step 3) | `tests/eventbus/test_admin_topics_authorization.py` | Verified |
| `docs/24_eventbus/eventbus_02_api-reference-index.md` | Modify: state the check order and the metadata-only 422 in the ADMIN row | The row mentions only `expected_generation`, 409, and optional `ttl_seconds` | `REQ-005`; AC-6 | ADMIN row of the roles table names `POST /admin/topics/authorization` without the check order (checked in Step 3) | `tests/tools/test_generate_reference_table.py` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify: add one sentence to Decision Detail 12 that a body without `consumer_authorization` is rejected with 422 | Decision Detail 12 covers only the empty body `{}` and says a well-formed no-change body returns 200 | `REQ-005`; AC-6 | Decision Detail 12 at `:103` and Decision Detail 13 at `:107` (checked in Step 3) | `N/A: documentation row, checked by ADR checkers` | Verified |

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
| `tests/eventbus/eventbus_helpers.py` | `post_topics_authorization` builds the payload and always adds `expected_generation`; metadata-only tests need a raw `client.post` | `tests/eventbus/test_admin_topics_authorization.py`; `REQ-003` |
| `scripts/eventbus/auth.py` | `current_generation()`, `AuthzGeneration`, and `require_role` define the generation read and the 401/403 dependency | `scripts/eventbus/admin_route.py`; `REQ-004` |
| `registry/manifests/eventbus_api.yaml` | Holds the generated summary of `update_topics_authorization` (the docstring's first line); it stays unchanged when that first line is unchanged | `scripts/eventbus/admin_route.py` |

## Acceptance Criteria
- AC-1 (`REQ-001`): a stale generation with an invalid TTL (`0`, `-1`, `86401`, `"3600"`, `True`) returns 422 and the detail names `ttl_seconds`.
- AC-2 (`REQ-002`): a stale generation with a valid TTL returns 409 with `error="generation_conflict"`.
- AC-3 (`REQ-003`): a body with only `expected_generation`, and a body with `expected_generation` plus a valid `ttl_seconds`, return 422; an unchanged explicit `consumer_authorization` returns 200 with `changed=false`.
- AC-4 (`REQ-004`): each rejection path leaves `current_generation()` the same object, `app.state.config` the same object, `current_principals()` the same object, expiries unchanged, and `log_authorization_change` uncalled.
- AC-5 (`REQ-004`): an unauthenticated invalid request returns 401 and an authenticated non-Admin invalid request returns 403.
- AC-6 (`REQ-005`): the API reference and ADR-013 Decision Detail 12 state the metadata-only rejection and the check order; `check_adr_structure.py`, `check_adr_invariant_matrix.py`, and `generate_reference_table.py --check` pass.

## Tests
- `REQ-001`: parametrized stale-generation plus invalid-TTL tests with state-identity and no-audit assertions.
- `REQ-002`: a stale-generation plus valid-TTL regression test.
- `REQ-003`: metadata-only body tests (`expected_generation` only; `expected_generation` plus `ttl_seconds`) and an unchanged-explicit-mapping 200 test.
- `REQ-004`: 401 and 403 precedence tests with an invalid body and a stale generation.
- `REQ-005`: the ADR and reference-generation checkers.

## Documentation Impact
- `REQ-005` drives updates to the EventBus API reference (found through `docs/00_index.md` "Document References by Task", EventBus row) and to ADR-013 Decision Detail 12. No ADR decision changes; the added sentence records the maintainer's confirmation of the metadata-only contract.

## Assumptions
- The maintainer confirmed in the working conversation on 2026-11-28 that a body without `consumer_authorization` MUST be rejected with 422 (option "422 で拒否"). ADR-013 is silent on this case.
- `ttl_seconds` validation keeps its current semantics (number, not boolean, `0 < ttl <= authz_max_ttl_seconds`); only its position changes.
- The 503 response for "no generation published yet" stays before TTL validation because the TTL bound comes from the in-force generation.
- The first line of the handler docstring stays unchanged, so the generated reference summary does not change.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether ADR-013 Decision Detail 12 wording is the right place for the metadata-only rule | The ADR is silent; the maintainer confirmed only the behavior | Add one sentence to Decision Detail 12 and run the ADR checkers; the owner reviews the wording in the commit | False |
| UNK-02 | A JSON body that is not an object (for example a list) makes `body.get` raise and likely returns 500 | Not exercised by any test and not claimed by the Issue | Out of scope; file a separate Issue if the behavior is confirmed | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/admin_route.py` | Modify | Medium: one router module included by `scripts/eventbus/app.py:241`; imported in `tests/eventbus/test_eventbus_auth.py:131` | 5 | High (100% single author) | not applicable (rsynced) |
| `tests/eventbus/test_admin_topics_authorization.py` | Modify | Low: test-only | 8 | High (100% single author) | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_02_api-reference-index.md` | Modify | Low: documentation only | 2 | High (100% single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Low: documentation only | 13 | High (100% single author) | not applicable (rsynced) |

## Design
- Path B (public/runtime interface: the response code of a privileged route changes; 4 target rows).
- Order after the change: `require_role(Role.ADMIN)` (401/403) -> body is non-empty (422) -> `consumer_authorization` present and valid (422) -> `expected_generation` required and plain int (422) -> `current_generation()` is not `None` (503) -> `ttl_seconds` valid (422) -> generation mismatch (409) -> no-op detection and publication (unchanged).
- Extract a private helper (for example `_validate_ttl_seconds(value, max_ttl)`) from the inline TTL block so `update_topics_authorization` does not gain branches; radon baseline for the handler is D (22).
- Consumer scan (`rg` over `scripts/` and `tests/`): the only callers of the route are `tests/eventbus/eventbus_helpers.py::post_topics_authorization`, `tests/eventbus/test_authz_generation_ttl.py` (all bodies carry `consumer_authorization`), and `tests/eventbus/test_eventbus_auth.py:1231` (carries `consumer_authorization`); none sends a metadata-only body, so no existing test changes. `scripts/eventbus/app.py:241` includes the router (not affected: no signature change).
- Predictable fallout check: module size of `scripts/eventbus/admin_route.py` is 9484 B against the 24576 B gate (not affected); no skill or instruction file gains text (not affected); no tool is added or removed (not affected); the `eventbus_api.yaml` summary is the docstring's first line, which stays unchanged (not affected, verify with `generate_reference_table.py --check`); pinned counts: the ADR-013 cited-test total is not touched because no new cited test is registered here (not affected; adrr003 registers them).
- Persisted schema check: not applicable (no DDL, no persisted state change).
- Operational dependency inspection: no DB or MCP change; the change affects only the EventBus process, which is single-process.

## Implementation steps
1. **Phase 1: Check order and metadata-only rejection (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`)**
   - [ ] Reorder the checks and extract the TTL helper in `scripts/eventbus/admin_route.py` (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`)
   - [ ] Update the handler docstring body, keeping its first line unchanged (`REQ-005`; `scripts/eventbus/admin_route.py`)
2. **Phase 2: Tests (`REQ-001` to `REQ-004`)**
   - [ ] Add the stale-plus-invalid-TTL, stale-plus-valid-TTL, metadata-only, unchanged-explicit-mapping, and 401/403 precedence tests (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`; `tests/eventbus/test_admin_topics_authorization.py`)
3. **Phase 3: API reference (`REQ-005`)**
   - [ ] Update the ADMIN row for the check order and the metadata-only 422 (`REQ-005`; `docs/24_eventbus/eventbus_02_api-reference-index.md`)
4. **Phase 4: ADR wording, validation, and deploy hand-off (`REQ-005`)**
   - [ ] Add one sentence to Decision Detail 12 (`REQ-005`; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
   - [ ] Run the validation plan commands; because `scripts/` changes, commit and push first, then hand off to the deploy skill (the user decides whether to deploy; it has an approval gate)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/admin_route.py` | Integration (TestClient through the production lifespan) | `uv run pytest tests/eventbus/test_admin_topics_authorization.py tests/eventbus/test_authz_generation_ttl.py tests/eventbus/test_eventbus_auth.py -q` | All pass, including the new tests |
| `scripts/eventbus/admin_route.py` | Static | `uv run ruff format scripts/eventbus/admin_route.py && uv run ruff check scripts/eventbus/admin_route.py && uv run mypy --no-namespace-packages scripts/ tests/eventbus tools && uv run bandit -c pyproject.toml scripts/eventbus/admin_route.py` | Clean |
| `scripts/eventbus/admin_route.py` | Complexity | `uv run radon cc scripts/eventbus/admin_route.py -s` | Handler complexity does not exceed the baseline D (22) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md` | Documentation checks | `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/generate_reference_table.py --check` | No findings |
| All target files | Gate run | `uv run python tools/run_validation_gates.py` | Pass; run `diff-cover` per `rules/toolchain.md` section 7 and meet its threshold (baseline recorded at implementation time) |

## Risks
- **Risk**: A client that sends a metadata-only body and relies on the 200 no-op now receives 422 → **Mitigation**: the maintainer confirmed the contract; no in-repo caller sends such a body (consumer scan); record the change in the API reference.
- **Risk**: Moving TTL validation before the 409 check lets a stale caller learn the `authz_max_ttl_seconds` bound from a 422 detail → **Mitigation**: the caller is already authenticated as Admin, and ADR-013 Decision Detail 13 mandates this order.
- **Risk**: Adding branches to a complexity-D handler → **Mitigation**: extract the TTL helper and re-run `radon cc`.
- **Risk**: Overlapping edits with the publication-boundary Plan (adrr002) in the same module → **Mitigation**: implement this Plan first (Scope Dependencies).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Check order, metadata-only rejection, and TTL helper in `scripts/eventbus/admin_route.py` | Pending | — | — | |
| 2 | Add the new tests in `tests/eventbus/test_admin_topics_authorization.py` | Pending | — | — | |
| 3 | Update the ADMIN row in `docs/24_eventbus/eventbus_02_api-reference-index.md` | Pending | — | — | |
| 4 | ADR-013 Decision Detail 12 sentence in `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, validation, deploy hand-off | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261125-103307_adrr001_admin-ttl-precedence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261128-172318
- **Evidence revision**: cc659c70a1811c504ec226a087ba3a39e85578bb
- **Related target files**: `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (move TTL validation); `scripts/eventbus/admin_route.py:125-151` | `scripts/eventbus/admin_route.py` | Step 1 | AC-1 | Parametrized stale-plus-invalid-TTL tests; pytest command in Validation plan | Confirmed by repository evidence |
| REQ-001 | Issue Testing Expectations | `tests/eventbus/test_admin_topics_authorization.py` | Step 2 | AC-1 | Same tests | Confirmed by repository evidence |
| REQ-002 | Issue Acceptance Criteria (stale generation with valid TTL) | `scripts/eventbus/admin_route.py` | Step 1 | AC-2 | Stale-plus-valid-TTL regression test | Explicit in issue |
| REQ-002 | Issue Testing Expectations | `tests/eventbus/test_admin_topics_authorization.py` | Step 2 | AC-2 | Same test | Explicit in issue |
| REQ-003 | Issue Required Changes (metadata-only rejection); maintainer decision 2026-11-28; `scripts/eventbus/admin_route.py:101-105,169-180` | `scripts/eventbus/admin_route.py` | Step 1 | AC-3 | Metadata-only body tests | Confirmed by repository evidence |
| REQ-003 | Issue Testing Expectations | `tests/eventbus/test_admin_topics_authorization.py` | Step 2 | AC-3 | Metadata-only and unchanged-mapping tests | Explicit in issue |
| REQ-004 | Issue Constraints and Acceptance Criteria | `scripts/eventbus/admin_route.py` | Step 1 | AC-4, AC-5 | State-identity, no-audit, 401/403 tests | Explicit in issue |
| REQ-004 | Issue Testing Expectations | `tests/eventbus/test_admin_topics_authorization.py` | Step 2 | AC-4, AC-5 | Same tests | Explicit in issue |
| REQ-005 | Issue Documentation Impact | `docs/24_eventbus/eventbus_02_api-reference-index.md` | Step 3 | AC-6 | `generate_reference_table.py --check` | Explicit in issue |
| REQ-005 | Issue Target Files (ADR wording, conditional); ADR-013 Decision Detail 12 at `:103` | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 4 | AC-6 | `check_adr_structure.py`, `check_adr_invariant_matrix.py` | Derived from confirmed evidence |

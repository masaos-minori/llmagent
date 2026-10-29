# Plan: align auth tests with generated-role behavior (ebgen001)

## Goal
- Remove the two synthetic all-roles tests from `tests/eventbus/test_eventbus_auth.py` so the test suite no longer encodes a token-role model that the production map generation, the ADR and the config docs all contradict.

## Priority
Medium

## Scope
- **In-Scope**:
  - Delete `test_admin_token_grants_all_roles` (line 874) and `test_shared_token_grants_all_roles_for_backward_compat` (line 902) from `tests/eventbus/test_eventbus_auth.py`.
  - Confirm the generated map shape stays pinned after the deletion (`test_distinct_tokens_get_exactly_their_documented_role`, line 1618, already asserts shared/admin tokens hold exactly `{OPERATOR, MONITORING, ADMIN}` and each per-role token exactly one role).
- **Out-of-Scope**: any change to `scripts/eventbus/auth.py` or other production code; ADR or config-doc edits (verified consistent with the code, see Reference Files); the identifier-comment cleanup in `test_eventbus_auth.py` filed under `issues/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md` (sequenced after this Plan).
- **Dependencies**: The pairwise-authorization Plan `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` is archived and all its procedures are implemented (`implementations/` top level is empty), so `tests/eventbus/test_eventbus_auth.py` has no active procedure row. N/A: no other active Plan in `plans/` targets this file.

## Background
`_populate_token_maps` in `scripts/eventbus/auth.py` gives the shared `auth_token` and `admin_token` only the control-plane roles (`_CONTROL_PLANE_ROLES = {OPERATOR, MONITORING, ADMIN}`, no Publisher, no Consumer) and each per-role token exactly one role. ADR-013 (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, Decision Details #1 and INV-07) and the config docs state the same model. The suite already pins this shape in `test_distinct_tokens_get_exactly_their_documented_role`.

## Problem
`test_admin_token_grants_all_roles` and `test_shared_token_grants_all_roles_for_backward_compat` inject a hand-built `Principal(roles=frozenset(Role), ...)` directly into `_TOKEN_PRINCIPAL_MAP` and assert it round-trips. They assert a resolution mechanism against a principal shape the production map can never produce, and their names and shape advertise an all-roles model the docs forbid.

## Reason for Change
The issue's premise is confirmed: the tests contradict the documented model and would keep passing even if map generation regressed into granting Consumer to a shared token. Cleanup keeps the suite a reliable contract record. Not time-sensitive.

## Implementation Intent
Pure deletion of the two tests. No replacement test is needed: the generated shape is already pinned by `test_distinct_tokens_get_exactly_their_documented_role` (verified in this cycle), and the route-level 403 behavior for shared/admin tokens on Consumer routes is covered by `test_shared_and_admin_tokens_have_no_consumer_bypass` and `test_control_plane_token_cannot_use_consumer_routes`. Do not touch production code.

## Requirements
- `REQ-001`: `tests/eventbus/test_eventbus_auth.py` no longer contains the two all-roles synthetic tests; test collection drops by exactly 2 and every remaining test passes.
- `REQ-002`: After the deletion the suite still pins the documented role shape (the pinning tests listed in Implementation Intent remain present and green).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 2026-10-29: all target rows Verified; `tools/check_workitem_structure.py` clean; `tools/check_plan_target_overlaps.py` findings reviewed as documented sequencing dependencies).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/eventbus/test_eventbus_auth.py | Remove two synthetic all-roles tests | They encode a role model contradicted by `auth.py`, ADR-013 and the config docs | REQ-001, REQ-002; AC-1, AC-2 | Lines 874 and 902 inject `Principal(roles=frozenset(Role), ...)` into `_TOKEN_PRINCIPAL_MAP`; `auth.py` `_CONTROL_PLANE_ROLES` grants shared/admin tokens only control-plane roles | The file's own remaining tests (collection count 2 lower) | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/auth.py | Confirms `_populate_token_maps`, `_CONTROL_PLANE_ROLES` and `Principal` fields; must not be modified | REQ-001 |
| docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md | States the authoritative role model (Decision Details #1, INV-07); verified consistent, no edit needed | REQ-002 |
| tests/eventbus/test_eventbus_auth.py lines 1618-1656 | `test_distinct_tokens_get_exactly_their_documented_role` is the surviving shape pin | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): neither `test_admin_token_grants_all_roles` nor `test_shared_token_grants_all_roles_for_backward_compat` exists in the file; `uv run pytest tests/eventbus/test_eventbus_auth.py` collects 2 fewer tests and passes.
- AC-2 (REQ-002): `test_distinct_tokens_get_exactly_their_documented_role`, `test_shared_and_admin_tokens_have_no_consumer_bypass` and `test_control_plane_token_cannot_use_consumer_routes` remain present and green.

## Tests
- REQ-001/REQ-002: `uv run pytest tests/eventbus/test_eventbus_auth.py` then `uv run pytest tests/eventbus` (expected: 409 passed, 1 skipped — today's baseline is 411 passed, 1 skipped, minus the 2 removed tests).
- ruff on the changed file.

## Documentation Impact
N/A: no doc change. ADR-013 and the EventBus config docs were verified consistent with the code in this cycle; the issue's doc-consistency item resolves to "no drift found".

## Assumptions
- The two tests are pure tautologies over the injection mechanism; deleting them loses no coverage because the shape is pinned elsewhere (verified by reading `test_distinct_tokens_get_exactly_their_documented_role`).
- No CI job or test-selection list references the two test names by name. `grep` over `.github`/`pyproject.toml` found none.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | None. The issue's two open questions (whether `require_consumer_identity` grants all roles; whether any publisher relies on all-roles shared tokens) were resolved by direct reads: the map grants control-plane roles only, and no test or script mints an all-roles principal outside the two deleted tests. | N/A | Resolved in this cycle | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tests/eventbus/test_eventbus_auth.py | Delete 2 tests | Tests only; no runtime path depends on them | 15 | 2 | N/A: test file is not deployed |

## Design
Deletion-only change. The surviving contract tests are: the map-shape pin (`test_distinct_tokens_get_exactly_their_documented_role`), the deny-all and pairwise-matrix classes, and the route-level 403 tests. No new test code is introduced; keeping a hand-injected all-roles test would re-introduce the contradiction the issue is about.

## Implementation steps

1. **Phase 1: Core change**
   - [ ] Delete `test_admin_token_grants_all_roles` and `test_shared_token_grants_all_roles_for_backward_compat` from `tests/eventbus/test_eventbus_auth.py` (REQ-001; tests/eventbus/test_eventbus_auth.py)
2. **Phase 2: Verification**
   - [ ] Run the file and the full EventBus suite; confirm the expected collection delta and green result (REQ-001, REQ-002; tests/eventbus/test_eventbus_auth.py)
   - [ ] ruff on the changed file (REQ-001; tests/eventbus/test_eventbus_auth.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_auth.py | Suite run before/after with collection-count comparison | `uv run pytest tests/eventbus/test_eventbus_auth.py; uv run pytest tests/eventbus` | 409 passed, 1 skipped suite-wide (411 baseline minus 2 removed) |
| tests/eventbus/test_eventbus_auth.py | Lint | `uv run ruff check tests/eventbus/test_eventbus_auth.py` | clean |

## Risks
- **Risk**: deleting coverage that is not actually duplicated → **Mitigation**: the replacement-coverage claim was verified by reading the surviving pinning tests in this cycle (Implementation Intent); AC-2 makes it checkable.

## Validation Quality Analysis
Baseline (2026-10-28, before implementation):
- radon cc: no production file is touched; baseline for the EventBus package is `Average complexity: A (3.48)`, recorded in `.opencode/verification/radon_cc_20261028.txt`. No new code is introduced, so the radon gate (new-function C threshold, file average drop >30%) cannot trip.
- vulture: no production file is touched; baseline in `.opencode/verification/vulture_20261028.txt`. Deleting tests removes code, so no new dead-code report is possible.
- bandit: baseline `.opencode/verification/bandit_20261028.json` reports 3 findings, all `B101 assert` LOW/HIGH in `auth.py` and `subscribe_route.py` (both untouched by this Plan). Gate: no new bandit finding may appear.
- diff-cover: baseline `uv run pytest tests/eventbus --cov=eventbus` reports TOTAL 91% (72s, 411 passed, 1 skipped, 2026-10-28). This Plan changes no production lines; the incremental-coverage gate applies only to changed production lines and is vacuous here.
- Gate for implementers: if any step drifts into editing `auth.py`, stop — the Plan's frozen table has no production row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the two all-roles tests (REQ-001) | Completed | — | 20261029-103640 |  |
| 2 | Run EventBus suite, confirm collection delta (REQ-001, REQ-002) | Pending | — | — |  |
| 3 | ruff on the changed file (REQ-001) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261029-072757_01_tests_eventbus_test_eventbus_auth.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261028-122206_ebgen001_authz-generation-role-tests.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-231549
- **Related target files**: `tests/eventbus/test_eventbus_auth.py`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Background bullet 1-2 (test wording at lines 874/902) | tests/eventbus/test_eventbus_auth.py | Phase 1 | AC-1 | Suite run with collection-count delta | Explicit in issue |
| REQ-002 | Issue Background (ADR/config/docs model); repo read of line 1618 pin | tests/eventbus/test_eventbus_auth.py | Phase 2 | AC-2 | Surviving pinning tests green | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261029-072757 -->
# Plan: Remove the EventBus authentication compatibility state and standardize generation-based authorization

## Goal
- Delete the `_TOKEN_PRINCIPAL_MAP` compatibility alias, the `principal_map()` test helper, and the `_populate_token_maps` name, so that one published, complete, immutable `AuthzGeneration` is the only authentication and authorization state in production code and tests.

## Priority
High

## Scope
- **In-Scope**: Production alias removal in `scripts/eventbus/auth.py` (`_TOKEN_PRINCIPAL_MAP`, `resolve_principal()` rewiring, `publish_generation()` alias rebinding); rename `_populate_token_maps()` to `build_and_publish_generation()` with callers updated; test-helper and fixture redesign (`tests/eventbus/eventbus_helpers.py`, `tests/eventbus/conftest.py`) so no test mutates a global principal dictionary; updated auth/authorization test files; removed-name patterns in `tools/check_compat_shims.py`; ADR-013 wording correction.
- **Out-of-Scope**: Changing the EventBus role model, token storage or distribution, token refresh protocols, aliases for external callers, and the final checker-configuration consolidation owned by `issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md`.
- **Dependencies**: Can run in parallel with `issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md`. Must complete before `issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md`.
  - **Depends on**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md | phase all | 004 finalizes the checker configuration that consumes the removed-name patterns this Plan adds.

## Background
- Initiative issue H-2 of `memo-issue.md`, second of four. Verified 2026-11-07 against current source:
  - `_TOKEN_PRINCIPAL_MAP` is defined at `scripts/eventbus/auth.py:96` and carries an explicit "Compatibility alias (owner-approved 2026-11-01)" comment; `publish_generation()` rebinds it in the same global block (auth.py:266-268); `resolve_principal()` reads it at auth.py:310/326.
  - `_populate_token_maps` is defined at auth.py:234 and referenced in 12 files: `scripts/eventbus/app.py` (import line 26, call line 84), `scripts/eventbus/config.py` (comment line 384), and eight test files (`test_eventbus_auth.py`, `test_eventbus_config.py`, `test_eventbus_consumer_authorization.py`, `test_eventbus_crash_ack.py`, `test_eventbus_ack_endpoint.py`, `test_eventbus_ack_nack.py`, `test_eventbus_dlq_pagination.py`, `test_admin_topics_authorization.py`), plus `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`.
  - `principal_map()` is defined at `tests/eventbus/eventbus_helpers.py:218-230` and falls back to `auth._TOKEN_PRINCIPAL_MAP` when no generation is published. Its importers/callers are `tests/eventbus/test_eventbus_auth.py`, `test_eventbus_config.py`, `test_eventbus_consumer_authorization.py` (via `eb_auth._TOKEN_PRINCIPAL_MAP`), `test_eventbus_subscribe.py`, `test_admin_topics_authorization.py`, and `test_authz_generation_ttl.py`.
  - Direct global-dictionary mutation appears in `test_eventbus_subscribe.py`, `test_eventbus_ack_nack.py`, `test_eventbus_ack_endpoint.py`, `test_eventbus_consumer_authorization.py`, `test_eventbus_auth.py`, and the `principal_map().clear()/update()` restore pattern in `test_eventbus_auth.py`; an object-identity assertion `generation.principals is auth._TOKEN_PRINCIPAL_MAP` exists at `tests/eventbus/test_eventbus_auth.py:1840`; an autouse fixture preserving `_TOKEN_PRINCIPAL_MAP` is at `tests/eventbus/conftest.py:55-68`; a no-op restore monkeypatch is at `tests/deploy/test_setup_services_eventbus.py:339`.
  - Production reads outside `auth.py`: none. `scripts/eventbus/admin_route.py` and `scripts/eventbus/authz_ttl.py` already use only `current_generation()` / `publish_generation()` / `_build_principal_map()` and are unaffected by the rename (reference-only).
  - `tools/check_compat_shims.py` already carries the removed-name pattern mechanism (`COMPAT_PATTERNS`, e.g. the "post-execution approval stage removed" entries) and the `tools/compat_exceptions.toml` manifest, including a self-reference exception for the checker source itself; `tests/tools/test_check_compat_shims.py` iterates `COMPAT_PATTERNS` generically and pins only the approval-stage subset, so adding patterns needs no test-file edit (verified 2026-11-07).
  - Docs describing the alias: only `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` (line 65 "…`_TOKEN_PRINCIPAL_MAP` is only an alias for that published map"). `docs/24_eventbus/eventbus_08_reference_api.md` documents `AuthzGeneration`, `publish_generation`, `current_generation` only — all survive — so it needs no edit (verified).

## Problem
- Two apparent sources of truth for principal state (`_TOKEN_PRINCIPAL_MAP` plus `AuthzGeneration.principals`) weaken the immutable-generation design, let tests bypass the publication boundary by mutating a live dictionary, and make atomic authorization updates harder to reason about.

## Reason for Change
- A single published, complete, immutable generation is the design intent; the alias contradicts it and is exactly the compatibility surface this initiative removes.

## Implementation Intent
- Make one published `AuthzGeneration` the complete and exclusive source of authentication and authorization state: every reader observes either the previous complete generation or the next complete generation, and no caller reads or mutates a parallel module-level principal dictionary. Production and test changes land in one atomic change.

## Requirements
- `REQ-001`: Delete `_TOKEN_PRINCIPAL_MAP` from `scripts/eventbus/auth.py`; `resolve_principal()` reads `current_generation().principals` and fails closed (401 authentication-failure path) when no generation has been published; `publish_generation()` rebinds only `_CURRENT_GENERATION`.
- `REQ-002`: Rename `_populate_token_maps()` to `build_and_publish_generation()` (public name; no alias for the old name); update `scripts/eventbus/app.py` and the stale comment in `scripts/eventbus/config.py`; all test callers use the new name.
- `REQ-003`: Delete `principal_map()` from `tests/eventbus/eventbus_helpers.py`; replace every direct global-dictionary mutation and `clear()/update()` restore with explicit `AuthzGeneration` construction and publication; `tests/eventbus/conftest.py` autouse fixture snapshots and restores `_CURRENT_GENERATION`; delete the object-identity test in `tests/eventbus/test_eventbus_auth.py`.
- `REQ-004`: Preserve the constraint set: failed generation construction leaves the previous generation in force (no partial/empty publication window), authorization decisions use one generation snapshot, duplicate-token validation stays fail closed, consumer ID and topic authorization stay enforced, and raw bearer tokens never appear in logs or assertion messages.
- `REQ-005`: Add removed-name patterns for `_TOKEN_PRINCIPAL_MAP`, `principal_map`, and `_populate_token_maps` to `tools/check_compat_shims.py` `COMPAT_PATTERNS` (checker-configuration consolidation itself stays with compatrm004).
- `REQ-006`: Update `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`: remove alias wording, name `build_and_publish_generation()` as the construction/publication entry point.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed 2026-11-07: every row `Verified` against current
source; `tools/check_plan_target_overlaps.py` judged compatible (see Assumptions);
`tools/check_workitem_structure.py` clean.)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/eventbus/auth.py | MODIFY | Delete `_TOKEN_PRINCIPAL_MAP` (line 96); `resolve_principal()` reads `current_generation().principals` (lines 310, 326); remove alias rebinding from `publish_generation()` (lines 266-268); rename `_populate_token_maps` (line 234) to `build_and_publish_generation` | REQ-001, REQ-002 / AC-001, AC-002 | Verified by grep and source read 2026-11-07 | tests/eventbus/test_eventbus_auth.py, tests/eventbus/test_authz_generation_ttl.py | Verified |
| scripts/eventbus/app.py | MODIFY | Lifespan imports (line 26) and calls (line 84) the renamed function | REQ-002 / AC-001 | lines 26, 84 | tests/deploy/test_setup_services_eventbus.py | Verified |
| scripts/eventbus/config.py | MODIFY | Comment at line 384 names `_populate_token_maps()` | REQ-002 / AC-001 | line 384 | — | Verified |
| tests/eventbus/eventbus_helpers.py | MODIFY | Delete `principal_map()` (lines 218-230); add generation-based helpers: read current generation principals for assertions and publish a complete custom-principal generation for injection tests | REQ-003 / AC-003 | definition site verified | consumed by all tests/eventbus auth tests below | Verified |
| tests/eventbus/conftest.py | MODIFY | `_reset_auth_state` fixture (lines 55-68) snapshots/restores `_TOKEN_PRINCIPAL_MAP`; switch to snapshot-and-republish `_CURRENT_GENERATION` | REQ-003 / AC-003 | lines 55-68 | — | Verified |
| tests/eventbus/test_eventbus_auth.py | MODIFY | 29 `_populate_token_maps` references, map-mutation/restore helpers (lines 862-911, 1583-1592, 1719-1726, 1749-1815), identity assertion (line 1840) | REQ-003 / AC-003, AC-004 | grep-verified | — | Verified |
| tests/eventbus/test_eventbus_consumer_authorization.py | MODIFY | Four snapshot/mutate/restore blocks via `eb_auth._TOKEN_PRINCIPAL_MAP` (lines 290-395) | REQ-003 / AC-003 | grep-verified | — | Verified |
| tests/eventbus/test_eventbus_config.py | MODIFY | `principal_map()` import/calls (lines 12, 523-524) and `_populate_token_maps` calls (4) | REQ-002, REQ-003 / AC-001, AC-003 | grep-verified | — | Verified |
| tests/eventbus/test_eventbus_subscribe.py | MODIFY | Direct map mutation (lines 131-137, 207-218) and alias comments (lines 596-597) | REQ-003 / AC-003 | grep-verified | — | Verified |
| tests/eventbus/test_eventbus_ack_nack.py | MODIFY | Direct map mutation (lines 167-187) and `_populate_token_maps` calls (3) | REQ-002, REQ-003 / AC-001, AC-003 | grep-verified | — | Verified |
| tests/eventbus/test_eventbus_ack_endpoint.py | MODIFY | Direct map mutation (lines 83-89) and `_populate_token_maps` calls (6) | REQ-002, REQ-003 / AC-001, AC-003 | grep-verified | — | Verified |
| tests/eventbus/test_eventbus_crash_ack.py | MODIFY | Alias comments (lines 83, 93) and `_populate_token_maps` calls (4) | REQ-002 / AC-001 | grep-verified | — | Verified |
| tests/eventbus/test_eventbus_dlq_pagination.py | MODIFY | `_populate_token_maps` calls (2) | REQ-002 / AC-001 | grep-verified | — | Verified |
| tests/eventbus/test_admin_topics_authorization.py | MODIFY | `principal_map` import (line 23), generation-identity assertion (line 269), principal read (line 441), `_populate_token_maps` calls (6) | REQ-002, REQ-003 / AC-001, AC-003 | grep-verified | — | Verified |
| tests/eventbus/test_authz_generation_ttl.py | MODIFY | `principal_map` import (line 23) and calls (lines 136, 229, 244) | REQ-003 / AC-003, AC-004 | grep-verified | — | Verified |
| tests/deploy/test_setup_services_eventbus.py | MODIFY | No-op alias-restore monkeypatch (line 339) becomes a generation restore aligned with the conftest pattern | REQ-003 / AC-003 | line 339 | — | Verified |
| tools/check_compat_shims.py | MODIFY | Add `COMPAT_PATTERNS` entries for `_TOKEN_PRINCIPAL_MAP`, `principal_map`, `_populate_token_maps` (word-boundary regexes; `\bprincipal_map\b` does not match `_build_principal_map`) | REQ-005 / AC-007 | pattern mechanism exists (approval-stage precedent) | tests/tools/test_check_compat_shims.py (no edit: generic iteration verified) | Verified |
| docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md | MODIFY | Line 65 alias parenthetical and `_populate_token_maps` mention describe the removed compatibility state | REQ-006 / AC-009 | grep-verified | — | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/admin_route.py | Rebuild path already uses `current_generation()`/`publish_generation()`/`_build_principal_map()`; confirms no production alias read survives | REQ-001 |
| scripts/eventbus/authz_ttl.py | TTL sweep publishes new generations; confirms the atomic-publication contract after the alias removal | REQ-004 |
| docs/24_eventbus/eventbus_08_reference_api.md | Documents `AuthzGeneration`, `publish_generation`, `current_generation` (all survive); verified it does not name the removed symbols | REQ-006 |
| tests/tools/test_check_compat_shims.py | Confirms adding `COMPAT_PATTERNS` entries does not break its generic assertions | REQ-005 |
| tools/compat_exceptions.toml | Exceptions manifest the checker reads; no new exception should be required once all references are deleted | REQ-005 |

## Acceptance Criteria
- AC-001: `_TOKEN_PRINCIPAL_MAP`, `principal_map()`, and `_populate_token_maps` have no definition or reference anywhere (REQ-001, REQ-002, REQ-003); verified by repository grep and the shim checker.
- AC-002: All authentication readers obtain principal state from `current_generation()`, and `publish_generation()` publishes one complete generation (REQ-001).
- AC-003: Tests do not mutate a global principal dictionary (REQ-003).
- AC-004: A failed rebuild leaves the previous generation active, and concurrent readers never observe a partial generation (REQ-004).
- AC-005: Duplicate-token validation stays fail closed; consumer ID and topic authorization stay enforced (REQ-004).
- AC-006: Raw bearer tokens are excluded from logs (REQ-004).
- AC-007: The compatibility checker rejects reintroduction of the removed names (REQ-005).
- AC-008: The authentication design document states that `AuthzGeneration` is the only source of authentication state (REQ-006).

## Tests
- Full EventBus authentication and authorization suite must pass after the atomic change (AC-001–AC-006): valid/invalid token, duplicate-token rejection, one-role-per-token, consumer ID and topic authorization, failed generation reconstruction (`test_authz_generation_ttl.py`), concurrent readers during generation replacement, and the audit-log token-leakage test.
- Generation-restore discipline: conftest teardown restores the complete previous generation; cross-file leakage is detected by running the whole `tests/eventbus/` suite in its existing order (AC-003).
- Shim check: after the change, `uv run python tools/check_compat_shims.py` reports clean, and a reintroduced reference fails (AC-007); validated by the existing checker self-test pattern in `tests/tools/test_check_compat_shims.py` (pattern-matching test data only, no new allowlist entry).
- Repository grep gate for the three removed names returns nothing outside `tools/check_compat_shims.py` and its test data (AC-001, AC-007).

## Documentation Impact
Yes: REQ-006 drives the authentication design document update (`docs/00_index.md` "Document References by Task" → EventBus authentication ADR row). Only ADR-013 names the alias; verified no other active document does.

## Assumptions
- Overlap judgments (Step 8b): `tools/check_plan_target_overlaps.py` reports `tests/deploy/test_setup_services_eventbus.py` in both this Plan and the Frozen `plans/20261107-061846_compatrm001_...` Plan. Judgment: **compatible** — compatrm001 edits the workflow-schema fixture lines (25, 133) and this Plan edits the auth-restore line (339); different regions, same file. Sequencing note: compatrm001 lands first (memo order), this Plan re-verifies line numbers at implementation time.
- Overlap judgments vs the Frozen `plans/20261107-063921_compatrm003_...` Plan (all **compatible**): `scripts/eventbus/app.py` (002 edits auth import/call lines 26/84; 003 edits the facade import line 42), `tests/eventbus/test_eventbus_ack_nack.py`, `test_eventbus_ack_endpoint.py`, `test_eventbus_crash_ack.py` (002 edits auth map/fixture regions; 003 edits facade import lines and NACK call sites — disjoint regions), `tools/check_compat_shims.py` (both only add `COMPAT_PATTERNS` entries; non-contradictory, consolidated by compatrm004).
- The new name is `build_and_publish_generation` (issue's suggested name adopted; resolves the Issue's Unresolved Question). Public module-level name because `app.py` imports it cross-module.
- `AuthzGeneration.principals` stays a plain dict; immutability is enforced by discipline and tests (publish-only, never mutate), not by `MappingProxyType` — hardening is out of this Plan's scope.
- `_build_principal_map()` keeps its name: it is not one of the removed names and does not match `\bprincipal_map\b` (underscore-adjacent word characters).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether test files outside `tests/eventbus/` and `tests/deploy/test_setup_services_eventbus.py` construct EventBus auth state indirectly via `make_eventbus_client` lifespan side effects that assume the alias | Not traced: helper lifespan behavior | The conftest generation-restore fixture covers lifespan leakage; verified by full-suite run in Phase 1 validation | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/eventbus/auth.py | MODIFY | every authenticated EventBus request path | 10 | 1 (EBAUTHGEN001 author set) | Yes — file sync + eventbus service restart |
| scripts/eventbus/app.py | MODIFY | lifespan baseline publication | 12 | 1 | Yes — service restart |
| scripts/eventbus/config.py | MODIFY | comment only | 9 | 1 | Yes — file sync |
| tests/eventbus/eventbus_helpers.py | MODIFY | shared helper for the whole EventBus test suite | 10 | 1 | No |
| tests/eventbus/conftest.py | MODIFY | autouse fixture for the whole EventBus test suite | 4 | 1 | No |
| tests/eventbus/test_eventbus_auth.py | MODIFY | largest auth test surface | 19 | 1 | No |
| tests/eventbus/test_eventbus_consumer_authorization.py | MODIFY | authorization test blocks | 6 | 1 | No |
| tests/eventbus/test_eventbus_config.py | MODIFY | config reload tests | 10 | 1 | No |
| tests/eventbus/test_eventbus_subscribe.py | MODIFY | subscribe authz tests | 9 | 1 | No |
| tests/eventbus/test_eventbus_ack_nack.py | MODIFY | ack/nack authz tests | 14 | 1 | No |
| tests/eventbus/test_eventbus_ack_endpoint.py | MODIFY | ack endpoint tests | 10 | 1 | No |
| tests/eventbus/test_eventbus_crash_ack.py | MODIFY | crash-ack comments/calls | 8 | 1 | No |
| tests/eventbus/test_eventbus_dlq_pagination.py | MODIFY | dlq pagination calls | 14 | 1 | No |
| tests/eventbus/test_admin_topics_authorization.py | MODIFY | admin topics authz tests | 13 | 1 | No |
| tests/eventbus/test_authz_generation_ttl.py | MODIFY | TTL generation tests | — (not in 30d list) | 1 | No |
| tests/deploy/test_setup_services_eventbus.py | MODIFY | deploy-gate auth restore line | 3 | 1 | No |
| tools/check_compat_shims.py | MODIFY | CI checker patterns | 10 | 1 | No (tools/ is not deployed) |
| docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md | MODIFY | auth design doc | 6 | 1 | Yes — docs sync |

## Design
- **Single source of state**: `_CURRENT_GENERATION` becomes the only module-level auth state in `scripts/eventbus/auth.py`. `publish_generation()` rebinds only it. `current_generation()` keeps returning `None` before the baseline; `resolve_principal()` treats `None` as "no principals" and takes the existing 401 authentication-failure path (audit-logged, no token echo), which is the fail-closed behavior the Constraints require.
- **Construction/publication entry point**: `_populate_token_maps()` → `build_and_publish_generation()` (build via `_build_principal_map()`, then publish one `AuthzGeneration`), matching the Issue's example name and the actual behavior already documented in its docstring. `_build_principal_map()` (build-only, used by `admin_route.py`/`authz_ttl.py`) keeps its name and contract.
- **Test discipline**: the mutation pattern (`snapshot → mutate global map → clear/update restore`) is replaced by publish-restore: build a complete new `dict[str, Principal]`, publish it as a new generation (via `build_and_publish_generation(config)` for config-driven tests, or a small helpers-module function that wraps `publish_generation(AuthzGeneration(generation=current+1, ...))` for custom-principal injection), then let the conftest fixture republish the snapshotted previous generation on teardown. `tests/eventbus/conftest.py::_reset_auth_state` snapshots `auth._CURRENT_GENERATION` instead of the map. Identity assertions (`generation.principals is auth._TOKEN_PRINCIPAL_MAP`) are deleted; generation-number advancement and principal content are asserted instead.
- **Removed-name protection**: three word-boundary patterns added to `COMPAT_PATTERNS` (`\b_TOKEN_PRINCIPAL_MAP\b`, `\bprincipal_map\b`, `\b_populate_token_maps\b`). `\bprincipal_map\b` cannot match `_build_principal_map` (no word boundary between `_` and `p`). No new `tools/compat_exceptions.toml` entry is needed because every reference is deleted in the same change; the existing checker self-reference exception already covers the pattern literals inside `tools/check_compat_shims.py`.
- **Atomicity**: production rename and test redesign are one phase; no intermediate state has two sources of truth (Issue's AI Implementation Instruction).
- **Path B grounding**: dependency inspection — production importers of the renamed function are exactly `app.py` (import+call) and test importers (8 files); `admin_route.py`/`authz_ttl.py` import `_build_principal_map`/`current_generation`/`publish_generation` only (grep-enumerated). Historical data — 30-day churn above shows the auth layer and its tests are actively maintained together, confirming the atomic single-change requirement. Import-linter contracts are untouched (no cross-package import changes; `eventbus → shared` only). `tools/check_compat_shims.py` current-state inspection — mechanism exists, extended not rebuilt.

## Implementation steps
1. **Phase 1: Atomic production + test cutover**
   - [ ] Rewrite `scripts/eventbus/auth.py`: delete the alias and its comment, rename `_populate_token_maps` → `build_and_publish_generation`, rewire `resolve_principal()` to `current_generation().principals` with fail-closed `None` handling, strip alias rebinding from `publish_generation()` (REQ-001, REQ-002).
   - [ ] Update `scripts/eventbus/app.py` import/call and the `scripts/eventbus/config.py` comment (REQ-002).
   - [ ] Redesign `tests/eventbus/eventbus_helpers.py` (delete `principal_map()`, add generation read/publish helpers) and `tests/eventbus/conftest.py::_reset_auth_state` (generation snapshot/republish) (REQ-003).
   - [ ] Convert every mutation/restore/import site in `tests/eventbus/test_eventbus_auth.py`, `test_eventbus_consumer_authorization.py`, `test_eventbus_config.py`, `test_eventbus_subscribe.py`, `test_eventbus_ack_nack.py`, `test_eventbus_ack_endpoint.py`, `test_eventbus_crash_ack.py`, `test_eventbus_dlq_pagination.py`, `test_admin_topics_authorization.py`, `test_authz_generation_ttl.py`, `tests/deploy/test_setup_services_eventbus.py` to generation-based construction/publication; delete the identity assertion (REQ-003).
   - [ ] Add the three removed-name patterns to `tools/check_compat_shims.py` `COMPAT_PATTERNS` (REQ-005).
2. **Phase 2: Documentation**
   - [ ] Update `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`: remove the alias parenthetical, name `build_and_publish_generation()` (REQ-006).
3. **Phase 3: Verification and deploy check**
   - [ ] Run `uv run pytest tests/eventbus/ tests/deploy/`, then the full suite and `rules/toolchain.md` §1–§8 gates; run `uv run python tools/check_compat_shims.py` and repository grep for the three removed names (AC-001–AC-008).
   - [ ] Deployment: file sync + eventbus service restart (auth state lives in process memory; no persisted data touched). No deploy without explicit user approval.

### Release units
N/A: no release unit — Phase 1 is a single atomic phase; no intermediate phase leaves callers broken.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/auth.py | Unit: 401/403 matrix, fail-closed no-generation case, failed-rebuild keeps previous generation, concurrent-reader test | `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_authz_generation_ttl.py` | All pass; `current_generation()` is the only state read |
| tests/eventbus/ suite | Integration: whole suite in order, cross-file leakage detection | `uv run pytest tests/eventbus/ -q` | Green; no fixture-order dependence |
| tools/check_compat_shims.py | Unit: new patterns match reintroduced names, self-check clean | `uv run python tools/check_compat_shims.py`; `uv run pytest tests/tools/test_check_compat_shims.py` | Clean before, fail on reintroduction |
| scripts/eventbus/app.py + config.py | Integration via deploy-gate test | `uv run pytest tests/deploy/test_setup_services_eventbus.py` | Green |
| Whole repository | Grep gate + full gates | `grep -rn "_TOKEN_PRINCIPAL_MAP\|_populate_token_maps" scripts/ tests/ docs/` (plus `\bprincipal_map\b` word-boundary grep); `uv run ruff check .`; `uv run mypy scripts/`; `uv run bandit -q -r scripts/ -c pyproject.toml`; `uv run radon cc scripts/eventbus/ -s -n B`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`; pre-commit | Zero references; baselines preserved |

## Risks
- **Risk**: 11 test files change auth setup/teardown at once; a missed restore site leaks a test-published generation into later tests → **Mitigation**: autouse conftest fixture republishes the snapshotted generation for every EventBus test; full-suite run plus the existing cross-file leakage guards verify it.
- **Risk**: `\bprincipal_map\b` pattern could match future legitimate names containing the phrase → **Mitigation**: word-boundary regex excludes `_build_principal_map`; if a future name collides, compatrm004's configuration stage adds an exception entry with owner/expiry.
- **Risk**: The eventbus service restart mid-session drops in-memory generations → **Mitigation**: restart publishes the baseline generation at lifespan start (existing behavior, `app.py:84`); no persisted state is touched by this Plan.
- **Risk**: Overlapping edit of `tests/deploy/test_setup_services_eventbus.py` with compatrm001 → **Mitigation**: recorded compatible judgment in Assumptions; land compatrm001 first and re-verify line positions before editing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Atomic production + test cutover | Pending | — | — | |
| 2 | Phase 2: Documentation | Pending | — | — | |
| 3 | Phase 3: Verification and deploy check | Pending | — | — | |

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
- **Source issue**: issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-063003
- **Related target files**: scripts/eventbus/auth.py, scripts/eventbus/app.py, scripts/eventbus/config.py, tests/eventbus/eventbus_helpers.py, tests/eventbus/conftest.py, tests/eventbus/test_eventbus_auth.py, tests/eventbus/test_eventbus_consumer_authorization.py, tests/eventbus/test_eventbus_config.py, tests/eventbus/test_eventbus_subscribe.py, tests/eventbus/test_eventbus_ack_nack.py, tests/eventbus/test_eventbus_ack_endpoint.py, tests/eventbus/test_eventbus_crash_ack.py, tests/eventbus/test_eventbus_dlq_pagination.py, tests/eventbus/test_admin_topics_authorization.py, tests/eventbus/test_authz_generation_ttl.py, tests/deploy/test_setup_services_eventbus.py, tools/check_compat_shims.py, docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md

### Requirement Traceability
| Requirement ID | Source | Acceptance Criteria | Implementation Target Files | Procedure | Status |
|---|---|---|---|---|---|
| REQ-001 | issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md Required Changes | AC-001, AC-002 | scripts/eventbus/auth.py | — | Planned |
| REQ-002 | same, Required Changes | AC-001 | scripts/eventbus/auth.py, scripts/eventbus/app.py, scripts/eventbus/config.py | — | Planned |
| REQ-003 | same, Required Changes | AC-001, AC-003 | tests/eventbus rows in Implementation Target Files | — | Planned |
| REQ-004 | same, Constraints | AC-004, AC-005, AC-006 | scripts/eventbus/auth.py, tests/eventbus/test_eventbus_auth.py, tests/eventbus/test_authz_generation_ttl.py | — | Planned |
| REQ-005 | same, Required Changes | AC-007 | tools/check_compat_shims.py | — | Planned |
| REQ-006 | same, Required Changes (documentation) | AC-008 | docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md | — | Planned |

## Freeze Decision Log

| Timestamp | Freeze status | Validation evidence |
|---|---|---|
| 2026-11-07 06:35 | Frozen | All `Implementation Target Files` rows `Verified` against HEAD `1b2dded66`: alias definition `auth.py:96`, rebinding `auth.py:266-268`, `resolve_principal` reads `auth.py:310/326`, `_populate_token_maps` definition `auth.py:234` with callers `app.py:26/84` + comment `config.py:384` + 8 test files, helper `eventbus_helpers.py:218-230`, fixture `conftest.py:55-68`, identity assertion `test_eventbus_auth.py:1840`, monkeypatch `test_setup_services_eventbus.py:339`, alias doc `adr_02_04_013` line 65 — all spot-checked by grep in this cycle. `tools/check_workitem_structure.py` clean. No blocking Unknown: UNK-01 `Blocking? = False`. `tools/check_plan_target_overlaps.py` after freeze reported `tests/deploy/test_setup_services_eventbus.py` shared with Frozen plan `plans/20261107-061846_compatrm001_...`; judged **compatible** per Step 8b (disjoint regions: compatrm001 edits workflow-schema fixture lines 25/133, this Plan edits the auth-restore line 339) and recorded in `Assumptions` with a sequencing note. |

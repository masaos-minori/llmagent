## Goal
Make runtime authorization-state updates one consistent, auditable operation: configuration and the token→principal map are published as a single generation so no concurrent request observes a mixed or empty authorization state, the endpoint states whether an update is runtime-only or persistent, every effective change emits a redacted privileged-action audit record, empty/no-op updates are not reported as successful changes, and authorization is exercised through the production config-loader path in tests so a regression fails the suite.

## Priority
Medium

## Scope
- **In-Scope**:
  - Publish configuration and the token→principal map under one lock and one generation so every request observes exactly one authorization generation. Build the new principal map completely and publish it together with the new config via one reference swap (no in-place `_TOKEN_PRINCIPAL_MAP.clear()`), so a failed rebuild leaves the previous generation intact and no request observes an empty map during an update.
  - Decide and document whether an admin update is runtime-only or persistent; return that status explicitly in the response (`persistent: true/false`) and describe restart behavior.
  - Reject or explicitly report empty and no-op updates (owner decision on status code, see UNK-02); do not return a bare success for a body that changes nothing.
  - Emit a redacted privileged-action audit record (`log_privileged_action`) for every effective change in `admin_route.py`.
  - Require exactly HTTP 403 for an unauthorized consumer ID before any delivery-state check, and unify the handler-level authorization check with the `require_consumer_identity` dependency check (concrete list of duplicated checks is an owner decision, UNK-03).
  - Remove the `%r` debug logging of `_principal`/`_identity` in `ack_route.py` (hygiene; `Principal` carries a token fingerprint, not the token).
  - Build principals through the production config-loader path in tests and remove direct mutation of the private `_TOKEN_PRINCIPAL_MAP` globals (`test_eventbus_crash_ack.py`); keep `_populate_token_maps()` as the single population entry point.
  - Document the runtime-only-vs-persistent semantics, the audit record, the failure behavior, and the one-generation invariant in `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`.
- **Out-of-Scope**:
  - Token uniqueness and loader fixes (memo H-02); startup gate (H-03).
  - Changing the public admin API shape except where the persistence decision requires it.
  - Any change to `resolve_principal`'s 401/500 fail-closed contract beyond publishing atomically.
  - Lazy loading of the Step 0 mandatory-load set — no action required (fixed load absorbed by prompt cache, user decision 2026-10-24).
- **Dependencies**:
  - Depends on memo task H-02 (loader-built principals in tests). No open issue under `issues/` overlaps.
  - Owner decisions on the three unknowns below gate implementation; they are recorded, not guessed.

## Background
Confirmed against HEAD (adversarial re-verification):
- `update_topics_authorization()` (`scripts/eventbus/admin_route.py:73-112`) validates the body fully, then at line 107 does `config = dataclasses.replace(config, **replacements)` and `request.app.state.config = config`, and only at line 109 calls `_populate_token_maps(config)` as a separate step. The swapped `app.state.config` is visible to concurrent requests before the principal map is rebuilt — a mixed-generation window.
- `_populate_token_maps()` (`scripts/eventbus/auth.py:97-186`) calls `_TOKEN_PRINCIPAL_MAP.clear()` at line 106 and repopulates the same dict in place. There is a window in which the map is empty (concurrent requests see 401), and if the function raises after the clear — e.g. `consumer_token is configured but consumer_authorization is missing` at lines 137-141 — the map is left partially populated while the config has already been replaced. This is a stronger form of the memo's "mixed generation" claim.
- The admin handler never writes the configuration file, so the update is runtime-only, and it never calls `log_privileged_action()` (`scripts/eventbus/audit.py:129`); it logs only `admin: topics authorization updated` (admin_route.py:111). `dlq_route.py:72` and `replay_route.py:38` are the existing callers and define the convention `log_privileged_action(consumer_id, request_id, route, target, detail="")`.
- An empty body `{}` produces no replacements (the `if replacements:` block at admin_route.py:101 is skipped), yet the function still calls `_populate_token_maps(config)` and returns `{"status": "ok"}` — a no-op reported as success.
- `tests/eventbus/test_eventbus_ack_endpoint.py:228` and `tests/eventbus/test_eventbus_crash_ack.py:277` both assert `resp.status_code in (403, 409)`, which masks the missing 403-before-409 ordering requirement.
- `tests/eventbus/test_eventbus_crash_ack.py` assigns `_TOKEN_PRINCIPAL_MAP["consumer-token"] = Principal(...)` directly (lines 85-91 and 102-109), bypassing the production population path; `_TOKEN_PRINCIPAL_MAP` is referenced 82 times across `tests/`.
- `ack_route.py:39` logs `_principal` and `_identity` with `%r` at debug level. `Principal` carries a token fingerprint (`_derive_token_fingerprint`, SHA-256 prefix), not the token, so the exposure is low; removal is hygiene.
- `ack_route.py::_do_ack` (lines 50-62) and `ack_route.py::nack` (lines 140-149) each repeat the `allowed_consumer_ids` membership check that `require_consumer_identity()` (`scripts/eventbus/auth.py:279-348`) performs as a FastAPI dependency. The concrete list of duplicated checks is not enumerated in this review (owner decision, UNK-03).
- `ADR-013` INV-01 (401), INV-02/INV-07 (no superuser bypass; explicit consumer_id/topic bindings), INV-05 (audit records never include secret/token values) govern this area.

## Problem
Configuration and principal-map swaps are separate operations, so concurrent requests can observe a mixed authorization generation (or an empty map mid-update); the change is runtime-only without saying so, so it may be mistaken for durable configuration; security-sensitive changes lack structured audit evidence; empty/no-op updates are reported as successful; and authorization tests can pass while consumer authorization is skipped or while the 403-before-409 ordering is unenforced.

## Reason for Change
Security-sensitive updates need one consistent generation, explicit persistence semantics and audit evidence, and a regression in authorization must fail the test suite rather than accept either of two status codes.

## Implementation Intent
Update configuration and token-principal maps under one lock and one generation; decide and document runtime-only versus persistent behavior and return it in the response; reject or explicitly report empty and no-op updates; emit a redacted privileged-action audit record for every effective change; require exactly 403 for unauthorized consumer IDs before delivery-state checks and unify the duplicated authorization check; build principals through the production config-loader path in tests and remove direct mutation of private token-map globals and the `%r` principal logging.

## Requirements
- `REQ-001`: A request MUST observe exactly one authorization generation. The new principal map MUST be built completely and published together with the new config via one reference swap; there MUST NOT be an in-place `_TOKEN_PRINCIPAL_MAP.clear()` window, and a failed rebuild MUST leave the previous generation in force. (Acceptance 1, 5)
- `REQ-002`: The admin response MUST state whether the update is runtime-only or persistent, and restart behavior MUST match the documented contract. (Acceptance 2; UNK-01)
- `REQ-003`: Every effective admin authorization change MUST emit a redacted privileged-action audit record via `log_privileged_action()`. (Acceptance 2; INV-05)
- `REQ-004`: Empty and no-op updates MUST NOT be reported as successful changes. (Acceptance 3; UNK-02)
- `REQ-005`: An unauthorized consumer ID MUST return exactly HTTP 403 before any delivery-state check, and the handler-level authorization check MUST be unified with the `require_consumer_identity` dependency check. (Acceptance 3; UNK-03)
- `REQ-006`: Tests MUST build principals through the production config-loader path (`_populate_token_maps()` / `load_config()`) and MUST NOT mutate `_TOKEN_PRINCIPAL_MAP` directly. (Acceptance 4)
- `REQ-007`: The `%r` debug logging of `_principal`/`_identity` in `ack_route.py` MUST be removed. (Hygiene)
- `REQ-008`: Token values MUST stay out of audit records and logs. (Constraint; INV-05)

## Implementation Target Files
**Freeze status**: Frozen (set once `issue-to-plan` Step 8's Implementation Target
Files Validation passed — `check_workitem_structure.py` reports No findings;
`check_plan_target_overlaps.py` reports one cross-plan overlap on
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, shared with
`plans/20261025-113939_eventbus004_shutdown-safe-during-sweep.md` and
`plans/20261025-120857_eventbus005_nack-idempotency-retries.md`. Non-contradictory: those
two record INV-01/EVENTBUS-022 and EVENTBUS-023 in that ADR; this Plan edits
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` (a different ADR).
Every row is `Verified`.

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/admin_route.py` | Publish config + principal map as one generation (build-new-then-swap, no in-place clear window); return `persistent` status; reject/report empty and no-op updates; emit `log_privileged_action` for every effective change | Core atomicity + persistence + audit fix | REQ-001, REQ-002, REQ-003, REQ-004; Acceptance 1, 2, 3, 5 | `update_topics_authorization()` admin_route.py:73-112 (swap 107, populate 109, log 111, return 112) | `tests/eventbus/test_admin_topics_authorization.py` | Verified |
| `scripts/eventbus/auth.py` | `_populate_token_maps()`: build the new map into a fresh dict and publish via one reference swap instead of in-place `clear()`; keep `resolve_principal()`/`require_consumer_identity()` fail-closed; add a module-level publish helper if needed | Removes the empty-map window and the partial-population-on-raise defect (stronger mixed-generation form) | REQ-001; Acceptance 1, 5 | `_populate_token_maps()` auth.py:97-186 (clear at 106; raise at 137-141); `require_consumer_identity()` auth.py:279-348 | `tests/eventbus/test_eventbus_auth.py`, `test_eventbus_consumer_authorization.py` | Verified |
| `scripts/eventbus/ack_route.py` | Remove `%r` debug logging of `_principal`/`_identity` (line 39); unify the handler-level `allowed_consumer_ids` check with the `require_consumer_identity` dependency check per UNK-03 | Hygiene + single authorization boundary | REQ-005, REQ-007; Acceptance 3 | `_do_ack()` ack_route.py:50-62; `nack()` ack_route.py:140-149; debug log ack_route.py:39 | `tests/eventbus/test_eventbus_ack_endpoint.py`, `test_eventbus_crash_ack.py` | Verified |
| `scripts/eventbus/audit.py` | No code change unless the admin endpoint needs a new field; confirm `log_privileged_action()` signature/convention is reusable as-is | Reference for the audit-call convention (caller added in `admin_route.py`) | REQ-003, REQ-008; Acceptance 2 | `log_privileged_action()` audit.py:129; callers dlq_route.py:72, replay_route.py:38 | N/A | Verified |
| `scripts/eventbus/app.py` | Confirm startup wiring reuses the one publish entry point; no change unless the lifecycle must call the new publish helper | Read to preserve startup population semantics | REQ-001; Acceptance 1 | `_populate_token_maps()` call in lifespan app.py | `tests/eventbus/test_eventbus_app_isolation.py` | Verified |
| `tests/eventbus/test_admin_topics_authorization.py` | Assert one-generation publish (no empty-map window), persistence-status field, empty/no-op handling, and audit emission; build principals via `_populate_token_maps()`/`load_config()` | Covers Acceptance 2, 3, 5 at the admin layer | REQ-002, REQ-003, REQ-004; Acceptance 2, 3, 5 | `_populate_token_maps()` usage test_admin_topics_authorization.py:91-93; map reads 147-186 | this file | Verified |
| `tests/eventbus/test_eventbus_auth.py` | Assert `_populate_token_maps()` publishes atomically and a failed rebuild leaves the previous generation intact | Covers Acceptance 1, 5 at the auth layer | REQ-001; Acceptance 1, 5 | `_populate_token_maps()` auth.py:97-186 | this file | Verified |
| `tests/eventbus/test_eventbus_consumer_authorization.py` | Assert 403-before-409 ordering and that the unified check rejects unauthorized consumer IDs/topics | Covers Acceptance 3 | REQ-005; Acceptance 3 | `require_consumer_identity()` auth.py:279-348 | this file | Verified |
| `tests/eventbus/test_eventbus_ack_endpoint.py` | Replace `status_code in (403, 409)` with exactly `403` for the unauthorized-consumer case; assert 403 precedes delivery-state checks | Removes the masking assertion (line 228) | REQ-005; Acceptance 3 | unauthorized-consumer assertion test_eventbus_ack_endpoint.py:228 | this file | Verified |
| `tests/eventbus/test_eventbus_crash_ack.py` | Remove direct `_TOKEN_PRINCIPAL_MAP` mutation (lines 85-91, 102-109); build the per-consumer restriction via `_populate_token_maps()` with a config that carries it | Enforces production-path principal construction (REQ-006) | REQ-006; Acceptance 4 | direct map assign crash_ack.py:85-91, 102-109 | this file | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Document the one-generation invariant, runtime-only-vs-persistent semantics, the audit record, and the failure/empty-update behavior; extend the verification matrix | Canonical governance record | REQ-002, REQ-003, REQ-004; Acceptance 2, 3 | INV-01/02/05/07 adr_02_04_013:171-176; verification matrix adr_02_04_013:212-223 | N/A | Verified |

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

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/config.py` | `EventBusConfig.__post_init__()` validation rules the validators rely on; how `load_config()` builds the config the tests must use | `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`; REQ-002 |
| `scripts/eventbus/route_helpers.py` | `get_config(request)` / `get_db(request)` request-scoped accessors used by the admin handler and the ACK/NACK routes | `scripts/eventbus/admin_route.py`, `scripts/eventbus/ack_route.py`; REQ-001 |
| `scripts/eventbus/dlq_route.py`, `scripts/eventbus/replay_route.py` | Existing `log_privileged_action()` callers defining the audit convention to reuse | `scripts/eventbus/audit.py`; REQ-003 |
| `scripts/eventbus/db.py` | Facade re-exports; needed to know what the publish helper re-exports and how the route imports it | `scripts/eventbus/auth.py`; REQ-001 |
| `tests/eventbus/test_eventbus_auth.py` | Existing auth unit tests to preserve when `_populate_token_maps()` changes its publication mechanism | `scripts/eventbus/auth.py`; REQ-001 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | EVENTBUS-023 tracking (Part 1); confirms scope and that deploy/readiness gaps are separate | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`; Scope |

## Acceptance Criteria
- Every request observes one authorization generation; no request sees an empty map during an update, and a failed principal-map rebuild leaves the previous generation in force (REQ-001; Acceptance 1, 5).
- Restart behavior matches the documented persistence contract and every effective admin change is auditable (REQ-002, REQ-003; Acceptance 2).
- Empty updates are not reported as successful changes; unauthorized consumer IDs return exactly 403 before delivery-state checks (REQ-004, REQ-005; Acceptance 3).
- An authorization regression fails the test suite (tests build principals through the production path and assert exactly 403) (REQ-006; Acceptance 4).
- Token values stay out of audit records and logs (REQ-008; INV-05).

## Tests
- One-generation publish: concurrent admin update and ACK/NACK never observe a mixed or empty map; two concurrent admin updates both resolve to a single consistent generation. (REQ-001; Acceptance 1, 5)
- Failed rebuild: forcing `_populate_token_maps()` to raise after the clear leaves the previous generation's principals intact and in force. (REQ-001; Acceptance 5)
- Empty and no-op updates: `{}` and a body equal to the current value are not reported as successful changes (per UNK-02). (REQ-004; Acceptance 3)
- Persistence contract: restart after an update restores the documented state; the response states `persistent: true/false` and restart matches it. (REQ-002; Acceptance 2)
- Audit redaction: an effective change emits `log_privileged_action` with no token value; a no-op does not emit one. (REQ-003, REQ-008; Acceptance 2)
- 403-before-409: an unauthorized consumer ID returns exactly 403 before any delivery-state check; the unified check rejects unauthorized topics too. (REQ-005; Acceptance 3)
- Production-path principals: tests build principals via `_populate_token_maps()`/`load_config()`; no `_TOKEN_PRINCIPAL_MAP` direct mutation remains. (REQ-006; Acceptance 4)
- All role-token route boundaries still pass (operator/monitoring/admin hold no Consumer role; a Consumer token with an authorized `consumer_id` succeeds; an unauthorized `consumer_id` or topic returns 403). (INV-02, INV-07)
- Then ruff and mypy.

## Documentation Impact
Yes. The runtime-only-vs-persistent semantics, the audit record, the failure/empty-update behavior, and the one-generation invariant must be documented. Target docs named via `docs/00_index.md` / `routing.md` Docs mapping:
- `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` — one-generation invariant, persistence contract, audit record, empty/update-failure behavior; extend the verification matrix. Drives REQ-002, REQ-003, REQ-004.
No deployment-script documentation is in scope.

## Assumptions
- `app.state.config` is read per request via `get_config(request)` and the swap is a single reference assignment visible atomically to other handlers.
- Building the new map into a fresh dict and assigning `_TOKEN_PRINCIPAL_MAP = new_map` (or a published holder) is sufficient to avoid the empty-map window; the GIL makes a single module-level assignment atomic.
- The admin endpoint today has no external caller under `scripts/`, so the response shape can carry a new `persistent` field without breaking a client.
- `log_privileged_action()`'s existing signature/convention is reusable without changing `audit.py`.
- `deploy.sh` rsyncs `scripts/` and `docs/` wholesale to `/opt/llm/`, so every target row's `deploy.sh Impact` is "not applicable (rsynced)".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Is an admin authorization update runtime-only or persistent? Today it is runtime-only (no config file write) but the response does not say so. What should the default be, and what should `persistent:` report? | Owner availability; no existing policy in repo | Owner decision; documented in ADR-013; non-blocking sign-off gate before implementation (per `rules/coding.md` Explicit sign-off gates) | False |
| UNK-02 | Should an empty or no-op update return 422/400, or 200 with `changed: false`? Needs confirmation against API consumers. | No API consumers found under `scripts/` | Confirm with owner; documented in ADR-013; non-blocking sign-off gate | False |
| UNK-03 | What is the concrete list of duplicated authorization checks between the ACK/NACK handler-level check and `require_consumer_identity()`? The memo does not enumerate them. | Not enumerated in this review | Engineering decision; recorded in design; drives `ack_route.py` change (or none if already unified) | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/admin_route.py` | One-generation publish + persistence flag + empty/no-op handling + audit call | Admin endpoint only; 1 prod caller (`app.py` lifecycle) + agent client | 0 (last change 2026-09-28) | N/A (git-fame unavailable) | not applicable (rsynced) |
| `scripts/eventbus/auth.py` | `_populate_token_maps()` build-new-then-swap; publish helper | All authorization resolution (every protected route) | 12 (last change 2026-10-15) | N/A | not applicable (rsynced) |
| `scripts/eventbus/ack_route.py` | Remove `%r` logging; unify handler auth check | ACK/NACK routes | 8 (last change 2026-10-23) | N/A | not applicable (rsynced) |
| `tests/eventbus/test_admin_topics_authorization.py` | One-generation/persistence/empty/audit assertions | Test-only | 6 (last change 2026-10-22) | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_auth.py` | Atomic-publish + failed-rebuild assertions | Test-only | 6 (last change 2026-10-22) | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_consumer_authorization.py` | 403-before-409 ordering assertion | Test-only | 6 (last change 2026-10-22) | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_ack_endpoint.py` | Replace `(403,409)` mask with exactly 403 | Test-only | 6 (last change 2026-10-22) | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_crash_ack.py` | Remove direct `_TOKEN_PRINCIPAL_MAP` mutation | Test-only | 6 (last change 2026-10-22) | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | One-generation + persistence + audit doc | Doc-only | 0 | N/A | not applicable (rsynced) |

Baseline complexity (radon): `update_topics_authorization` = B (6); `require_consumer_identity` = B (9); `resolve_principal` = A (4); validators = B (7).
bandit reports only `B101 assert_used` (Low, contract-invariant asserts); vulture is
clean. Keep `require_consumer_identity` at or below baseline (B 9) when unifying the
handler check.

## Design
**North star (REQ-001):** every request observes exactly one authorization generation.
Every candidate mechanism below serves that invariant; the empty-map window and the
partial-population-on-raise defect are removed by publishing a fully built map together
with the new config in one reference swap.

**Publication mechanism.** `_populate_token_maps()` builds the entire new map into a
fresh local dict, then publishes it with a single module-level assignment
(`_TOKEN_PRINCIPAL_MAP = new_map`) — or, cleaner, a small `publish_principals(new_map)`
helper in `auth.py` that both the startup lifecycle (`app.py`) and the admin handler
call. Because the assignment is atomic under the GIL, no request ever observes an empty
map, and if building the new map raises (e.g. `consumer_token` configured but
`consumer_authorization` missing) the previous generation is already in force — the
config swap in `admin_route.py` happens only after a successful publish, or the handler
rolls back the config swap when the publish fails. Either way the two publications
(config swap + principal map) are ordered so they cannot diverge: build-and-publish the
map first, then commit the config swap; on failure, revert the config swap.

**Persistence semantics (UNK-01).** Decide and document whether the admin update is
runtime-only or persistent. If runtime-only (the current de-facto behavior), the
response returns `{"status": "ok", "persistent": false}` and ADR-013 documents that the
change is lost on restart and must be made in `config/eventbus.toml`. If persistent, the
handler writes the config file atomically (temp file + rename) in addition to the
runtime swap, returns `{"status": "ok", "persistent": true}`, and ADR-013 documents the
write. This is an owner decision; the plan records both branches, not a prescription.

**Empty / no-op handling (UNK-02).** An empty body `{}` or a body equal to the current
value changes nothing. Decide: reject with 422/400, or return 200 with
`{"status": "ok", "changed": false}`. Document the choice in ADR-013. Either way the
current behavior (returning a bare success while still repopulating the map) is removed.

**Audit record (REQ-003).** Every *effective* change emits
`log_privileged_action(consumer_id="", request_id=request.state.request_id,
route="/admin/topics/authorization", target="topics_authorization", detail="<redacted summary>")`
reusing the existing convention from `dlq_route.py`/`replay_route.py`. No token values
are passed (INV-05). A no-op emits nothing.

**Unify authorization check (UNK-03).** The ACK/NACK handler-level `allowed_consumer_ids`
checks (`ack_route.py::_do_ack:50-62`, `nack:140-149`) duplicate `require_consumer_identity()`.
The concrete list of duplicated checks is an engineering decision (UNK-03): either route
ACK/NACK consumer identity through the dependency (removing the handler duplicates) or
document why the handler check is retained. Either way, unauthorized consumer IDs must
return exactly 403 before any delivery-state check.

**`%r` principal logging (REQ-007).** Remove `logger.debug("DEBUG _do_ack: _principal=%r, _identity=%r", ...)` from `ack_route.py:39`. `Principal` carries a token fingerprint, not the token, so exposure is low; removal is hygiene.

**Import-linter:** `eventbus-is-isolated` is KEPT (verified above). No file crosses into
`shared/`; the publish helper stays within `auth.py`.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: One-generation publish in `auth.py`**
   - [ ] Add a `publish_principals(new_map)` helper (or equivalent) to `scripts/eventbus/auth.py` that atomically replaces the module-level map; refactor `_populate_token_maps()` to build into a fresh dict and publish via it. (REQ-001; `scripts/eventbus/auth.py`)
   - [ ] Update the startup lifecycle in `scripts/eventbus/app.py` to reuse the one publish entry point; confirm no empty-map window at startup. (REQ-001; `scripts/eventbus/app.py`)
2. **Phase 2: Atomic, audited admin handler in `admin_route.py`**
   - [ ] Order the operations so the new map is built and published before the config swap, and roll back the config swap if the publish raises. (REQ-001; `scripts/eventbus/admin_route.py`)
   - [ ] Return `persistent: <bool>` reflecting the UNK-01 decision; document the restart behavior. (REQ-002; `scripts/eventbus/admin_route.py`)
   - [ ] Reject or explicitly report empty/no-op updates per UNK-02; emit `log_privileged_action` for every effective change only. (REQ-003, REQ-004; `scripts/eventbus/admin_route.py`)
3. **Phase 3: Unify authorization + remove logging in `ack_route.py`**
   - [ ] Route ACK/NACK consumer identity through `require_consumer_identity()` or document the retained duplicate per UNK-03; ensure exactly 403 before delivery-state checks. (REQ-005; `scripts/eventbus/ack_route.py`)
   - [ ] Remove the `%r` `_principal`/`_identity` debug log (line 39). (REQ-007; `scripts/eventbus/ack_route.py`)
4. **Phase 4: Tests**
   - [ ] `tests/eventbus/test_admin_topics_authorization.py`: one-generation publish, persistence field, empty/no-op handling, audit emission; build principals via `_populate_token_maps()`/`load_config()`. (REQ-002, REQ-003, REQ-004; `tests/eventbus/test_admin_topics_authorization.py`)
   - [ ] `tests/eventbus/test_eventbus_auth.py`: atomic publish + failed-rebuild leaves previous generation intact. (REQ-001; `tests/eventbus/test_eventbus_auth.py`)
   - [ ] `tests/eventbus/test_eventbus_consumer_authorization.py`: 403-before-409 ordering. (REQ-005; `tests/eventbus/test_eventbus_consumer_authorization.py`)
   - [ ] `tests/eventbus/test_eventbus_ack_endpoint.py`: replace `status_code in (403, 409)` with exactly 403. (REQ-005; `tests/eventbus/test_eventbus_ack_endpoint.py`)
   - [ ] `tests/eventbus/test_eventbus_crash_ack.py`: remove direct `_TOKEN_PRINCIPAL_MAP` mutation; build via `_populate_token_maps()`. (REQ-006; `tests/eventbus/test_eventbus_crash_ack.py`)
5. **Phase 5: Documentation**
   - [ ] Document the one-generation invariant, persistence contract, audit record, and empty-update behavior in `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`; extend the verification matrix. (REQ-002, REQ-003, REQ-004; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
6. **Phase 6: Validation**
   - [ ] Run ruff, mypy, bandit, vulture, lint-imports, and the affected test files; confirm no empty-map window, exactly 403 before 409, and INV-02/07 boundaries intact. (Acceptance 1-5)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/auth.py`, `scripts/eventbus/admin_route.py` | Unit: atomic publish; failed rebuild leaves previous generation; empty/no-op not reported as success; audit emitted only on effective change | `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_admin_topics_authorization.py` | No empty-map window; failed rebuild intact; empty/no-op not success; audit present only on change |
| `scripts/eventbus/ack_route.py`, `scripts/eventbus/auth.py` | Integration: unauthorized consumer ID returns exactly 403 before delivery-state checks; role-token boundaries | `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py tests/eventbus/test_eventbus_consumer_authorization.py tests/eventbus/test_eventbus_crash_ack.py` | Exactly 403 before 409; no `_TOKEN_PRINCIPAL_MAP` direct mutation |
| `scripts/eventbus/*` | Static: complexity, dead code, security | `uv run radon cc scripts/eventbus/auth.py scripts/eventbus/admin_route.py scripts/eventbus/ack_route.py`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml` | `require_consumer_identity` ≤ B(9); bandit/vulture clean |
| Import boundaries | Architecture contract | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |
| Types / format | Quality gates | `uv run mypy`, `uv run ruff` | Pass |

## Risks
- **Risk**: Changing `_populate_token_maps()`'s publication mechanism breaks the 82 direct `_TOKEN_PRINCIPAL_MAP` references in tests. → **Mitigation**: keep `_populate_token_maps()` as the single population entry point; the map remains a module global; update only the tests that mutate it directly (`test_eventbus_crash_ack.py`) and add atomic-publish assertions (`test_eventbus_auth.py`).
- **Risk**: Ordering the config swap against the publish could leave them divergent on failure. → **Mitigation**: build-and-publish the map first, then commit the config swap; roll back the config swap if the publish raises. Documented in design.
- **Risk**: Unifying the ACK/NACK handler check (UNK-03) could remove a needed guard if the dependency does not cover every case. → **Mitigation**: record the concrete duplicated-check list as an owner decision; keep exactly-403-before-409 enforced regardless.
- **Risk**: The persistence decision (UNK-01) implemented wrong reintroduces silent runtime-only behavior. → **Mitigation**: non-blocking sign-off gate; the response always reports `persistent:` regardless of the chosen default.
- **Risk**: Requiring exactly 403 in `test_eventbus_ack_endpoint.py`/`test_eventbus_crash_ack.py` could fail if production currently returns 409 first. → **Mitigation**: this is the defect being fixed; the implementation makes 403 precede 409, then the test asserts it.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: one-generation publish in `auth.py` + `app.py` startup reuse | In Progress | — | — | Sign-off gate on UNK-01 before implementation |
| 2 | Phase 2: atomic, audited admin handler in `admin_route.py` (ordering, persistence flag, empty/no-op, audit) | In Progress | — | — |  |
| 3 | Phase 3: unify ACK/NACK auth check + remove `%r` logging in `ack_route.py` (UNK-03) | In Progress | — | — |  |
| 4 | Phase 4: repo/admin/ack/consumer/crash-ack tests | In Progress | — | — |  |
| 5 | Phase 5: document one-generation + persistence + audit in ADR-013 | In Progress | — | — |  |
| 6 | Phase 6: ruff/mypy/bandit/vulture/lint-imports + affected test runs | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-01: runtime-only vs persistent is an owner decision (sign-off gate) | Classified non-blocking by owner approval 2026-10-25 — sign-off remains a pre-implementation gate, not a generation blocker | Yes | 20261025 |
| 2 | UNK-02: empty/no-op status code is an owner decision; UNK-03: duplicated-check list is an engineering decision | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261026-090956_01_scripts_eventbus_admin_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261026-090956_02_scripts_eventbus_auth.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261026-090956_03_scripts_eventbus_ack_route.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261026-090956_04_scripts_eventbus_audit.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261026-090956_05_scripts_eventbus_app.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261026-090956_06_tests_eventbus_test_admin_topics_authorization.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261026-090956_07_tests_eventbus_test_eventbus_auth.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261026-090956_08_tests_eventbus_test_eventbus_consumer_authorization.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261026-090956_09_tests_eventbus_test_eventbus_ack_endpoint.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261026-090956_10_tests_eventbus_test_eventbus_crash_ack.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261026-090956_11_docs_10_adr_adr_02_04_013_eventbus-authentication-authorization_md.md | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261023-154326_eventbus006_runtime-authorization-update-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-122243
- **Related target files**: `scripts/eventbus/admin_route.py`, `scripts/eventbus/auth.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/audit.py`, `scripts/eventbus/app.py`, `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_consumer_authorization.py`, `tests/eventbus/test_eventbus_ack_endpoint.py`, `tests/eventbus/test_eventbus_crash_ack.py`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Required change 1,6; Acceptance 1, 5 | `scripts/eventbus/auth.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/app.py` | 1 | One authorization generation; no empty map; failed rebuild intact | Atomic-publish + failed-rebuild tests | Draft |
| REQ-002 | Unresolved Q1; Acceptance 2 | `scripts/eventbus/admin_route.py`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | 2 | Persistence status returned; restart matches doc | Persistence-field + restart test | Draft |
| REQ-003 | Problem; Required change 3; Acceptance 2 | `scripts/eventbus/admin_route.py`, `scripts/eventbus/audit.py` | 2 | Effective change emits redacted audit record | Audit-emission test | Draft |
| REQ-004 | Problem; Required change 3; Acceptance 3 | `scripts/eventbus/admin_route.py` | 2 | Empty/no-op not reported as success | Empty/no-op test | Draft |
| REQ-005 | Required change 4; Acceptance 3 | `scripts/eventbus/ack_route.py`, `scripts/eventbus/auth.py`, `tests/eventbus/test_eventbus_consumer_authorization.py` | 3 | Exactly 403 before delivery-state checks; unified check | 403-before-409 test | Draft |
| REQ-006 | Required change 5; Acceptance 4 | `tests/eventbus/test_eventbus_crash_ack.py`, `tests/eventbus/test_admin_topics_authorization.py` | 4 | Principals built via production path; no direct map mutation | Crash-ack refactor test | Draft |
| REQ-007 | Background; hygiene | `scripts/eventbus/ack_route.py` | 3 | `%r` principal logging removed | Log removal / suite pass | Draft |
| REQ-008 | Constraint; INV-05 | `scripts/eventbus/audit.py`, `scripts/eventbus/admin_route.py` | 2 | Token values absent from audit/logs | Audit-redaction test | Draft |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261026-090956 -->
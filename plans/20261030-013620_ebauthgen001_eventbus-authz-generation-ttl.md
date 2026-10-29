## Goal
- Give every effective runtime change to EventBus consumer and topic authorization a unique generation number with immutable generation metadata, reject stale concurrent updates through a mandatory expected-generation check, support optional TTL for temporary grants that expires through an atomic generation update, and make the loss of runtime overrides at restart explicit and auditable — while preserving the already-implemented fail-closed, one-generation publication behavior and the already-landed audit identity fields.

## Priority
Medium

## Scope
- **In-Scope**:
  - Runtime authorization generation counter + immutable generation snapshot (config + principal map + effective time + configuration-baseline hash) published through one atomic swap.
  - Mandatory `expected_generation` on `POST /admin/topics/authorization`; stale updates rejected without partial change.
  - Optional TTL for temporary grants; expiry applied as an atomic generation update by a periodic sweep with an injectable clock; invalid TTL values rejected.
  - Audit records extended additively with previous/new generation; restart emits an audit record for the removal of runtime overrides (baseline restored).
  - ADR-013 and EventBus operations docs updated, including a fix for the stale `detail="updated"` claim in ADR-013.
- **Out-of-Scope**:
  - Persisting runtime overrides to configuration files (runtime-only contract preserved).
  - Changes to the token-to-role matrix, authentication, or principal derivation rules.
  - Audit identity fields (request ID, actor fingerprint, count detail) — already implemented; this Plan only adds generation fields on top.
  - Unrelated refactoring or formatting-only changes.
- **Dependencies**:
  - Publish-order work is already implemented (verified 2026-10-30: `scripts/eventbus/admin_route.py:137-147` builds replacement config + principal map before publishing; `scripts/eventbus/auth.py:105-110` "previous generation stays in force"; test `tests/eventbus/test_admin_topics_authorization.py:274-295`). The issue's claim that its procedures are "not yet implemented" is stale — procedures are archived at `implementations/done/20261029-101422_01_scripts_eventbus_auth.py.md`, `_02_scripts_eventbus_admin_route.py.md`, `_03_tests_eventbus_test_admin_topics_authorization.py.md`. No ordering wait; build on the landed behavior.
  - Audit identity plan is already landed: `plans/done/20261028-234417_ebaudit005_privileged-audit-actor-context.md` (the issue cites it as in-flight at `plans/` — stale path). Its fields (`request_id=request.state.request_id` at `scripts/eventbus/admin_route.py:157`, `actor=principal.token_fingerprint` at `:161`, `detail="name:count;...;persistent:false"` at `:153-154`) exist; this Plan extends, never re-adds.
  - Shared target files with no conflicting in-flight plan: `plans/` scan shows no active plan targets `scripts/eventbus/auth.py`, `admin_route.py`, or `test_admin_topics_authorization.py` (the dlqbox001 plan targets `eventbus/app.py`/`config.py` — sequenced note added in Dependencies of that pairing if the overlap checker confirms).

## Background
Source: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`, adversarially re-verified against current source on 2026-10-30. Verified findings:

- ADR-013 runtime-only contract confirmed verbatim at `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md:89`; INV-05 "Audit records MUST never include secret/token values" at `:191`.
- Response shape confirmed: `return {"status": "ok", "persistent": False, "changed": changed}` — real location `scripts/eventbus/admin_route.py:164` (issue cited `:149`, which is the log line; anchor stale by ~15 lines after the ebaudit005 landing).
- No numeric generation concept exists: `expected_generation`, `ttl`, `expires`, `epoch` have zero hits across `scripts/eventbus/` `.py` files and schema SQL (absence search). The word "generation" appears only as prose in three comments: `scripts/eventbus/auth.py:110`, `auth.py:211`, `admin_route.py:141`, describing the immutable map swap, not a counter. Correction to the issue: the claim "only a comment in `auth.py:111`" understates — three such comments exist; and the ebgen001 issue (`issues/done/20261028-122206_ebgen001_authz-generation-role-tests.md`) introduced the runtime immutable-generation swap concept itself, not merely test fixtures.
- Audit records already carry identity fields (ebaudit005 landed): `log_privileged_action(consumer_id="admin", request_id=request.state.request_id, route=..., target="topics_authorization", detail=";".join(counts + persistent:false), actor=principal.token_fingerprint)` at `scripts/eventbus/admin_route.py:152-162`. The issue's "currently `request_id=""` and `detail=\"updated\"`" is stale. Consequential real defect found: ADR-013 `:93` still states `detail="updated"` — the docs are stale against the code and this Plan corrects them.
- Publish-order behavior landed (see Dependencies): build-first-then-publish in `admin_route.py:137-147`; `publish_principals` (`auth.py:216-224`) is a single module-level assignment under the GIL.
- No-op behavior confirmed with tests: no publish and `changed: false` (`admin_route.py:120-136`; `tests/eventbus/test_admin_topics_authorization.py:170-186`, `:209`, `:297-310`).
- "EventBus authorization models" location resolved: `scripts/eventbus/config.py:71-72` frozen `@dataclass EventBusConfig` with `consumer_authorization` (`:99`) and `topic_authorization` (`:102`); principals are `Principal` (`scripts/eventbus/auth.py:35`). No dedicated authorization/middleware module exists.
- Test surface resolved: `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_eventbus_auth.py` (secret-leak regression at `:1272`), `tests/eventbus/test_eventbus_consumer_authorization.py` exist. `tests/eventbus/test_eventbus_audit.py` does NOT exist (audit tests are distributed); no plan row may assume it.
- Doc surface resolved: there is no authz-dedicated `docs/24_eventbus/` file; the admin endpoint signature tables live in `docs/24_eventbus/eventbus_08_reference_api.md` (`:52`, `:65`), with `eventbus_02_api-reference-index.md` and `eventbus_07_configuration-and-operations.md` as the index/operations homes.

## Problem
Responses and audit records do not identify which authorization generation is in effect, and a concurrent administrative update can silently overwrite an earlier decision (last-write-wins with no precondition). A temporary grant stays active until restart or the next update unless someone removes it manually. Because runtime overrides disappear at restart, an operator cannot tell from the record that a previously granted exception no longer exists.

## Reason for Change
Authorization state is security-sensitive and runtime edits are an operational tool, so conflict-awareness, bounded temporary access, and visible baseline drift reduce the chance of an unnoticed grant or an overwritten decision. Priority Medium: enhancements to an already atomic, fail-closed mechanism with no incident cited. Owner decision recorded 2026-10-30: expected generation is mandatory (not optional), and TTL expiry runs as a periodic sweep.

## Implementation Intent
Introduce an `AuthzGeneration` snapshot: an immutable object bundling the effective `EventBusConfig`, the principal map, a monotonic generation number, effective time, and a configuration-baseline hash (SHA-256 over the canonicalized consumer/topic authorization pair sets). `scripts/eventbus/auth.py` publishes it through the existing single-assignment mechanism (one-generation publication preserved). `scripts/eventbus/admin_route.py` requires `expected_generation` in the request body, rejects mismatches with an explicit error before any state change, and returns previous/new generation plus the existing fields. TTL expiry: temporary grants carry an expiry timestamp in the generation metadata; a periodic sweep task in the app lifespan detects expired grants with an injectable clock and removes them by building a new generation (same build-first-then-publish path), auditing the removal. At startup, if the baseline config differs from a previously recorded runtime state marker, a startup audit record documents that runtime overrides do not survive restart.

## Requirements
- `REQ-001`: Every effective authorization update produces one unique, monotonic generation; the generation snapshot (config + principal map + effective time + baseline hash) is immutable and published in one assignment, preserving the failed-rebuild-keeps-previous-generation behavior.
- `REQ-002`: Mutating admin updates require `expected_generation`; a mismatch returns an explicit rejection with no partial change and no audit "changed" record.
- `REQ-003`: The update response returns `previous_generation`, `new_generation`, `changed_count`, `effective_at`, `persistent`, `baseline_hash` additively, keeping `status`, `persistent`, `changed` unchanged (owner decision 2026-10-30: response extension only).
- `REQ-004`: Audit records for effective updates carry previous and new generation in addition to the already-landed identity fields; no token values or secrets in any record (ADR-013 INV-05).
- `REQ-005`: Optional TTL on temporary grants: request may carry `ttl_seconds`; invalid values (non-positive, above configured max) are rejected; expiry is applied as an atomic generation update by the periodic sweep and audited.
- `REQ-006`: Restart observability: startup emits one audit record stating that runtime overrides from the previous process lifetime are not in effect (baseline restored), including the baseline hash of the loaded configuration.
- `REQ-007`: No-op updates keep publishing nothing and reporting `changed: false` (existing behavior preserved; expected-generation check runs before change detection).
- `REQ-008`: ADR-013 documents the generation contract, stale rejection, TTL semantics, and restart behavior, and the stale `detail="updated"` description at `:93` is corrected to the actual count-summary format.
- `REQ-009`: The already-landed publish-order (build-first, one-generation publication) and audit identity fields (ebaudit005) are reused, not duplicated; the failed-rebuild-keeps-previous-generation behavior is regression-guarded.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on
2026-10-30: every row exists-or-is-new-with-evidence, is linked to a Plan requirement,
and is `Verified` against `HEAD c5a8285dd` — the corrected anchors (`admin_route.py:137-147`
publish-order landed, audit block `:152-162` with identity fields already landed, return
`:164`, `auth.py:105-110/:216-224`, `EventBusConfig` `config.py:71-102`, ADR-013 `:89/:93/:191`,
endpoint tables `eventbus_08_reference_api.md:52/:65`) re-confirmed by direct read; the
issue's stale "not yet implemented"/"in-flight" claims corrected in Background;
`check_workitem_structure.py` reports no findings; cross-plan pairs reported by
`check_plan_target_overlaps.py` are recorded sequenced in Dependencies.)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/eventbus/auth.py | modify | `AuthzGeneration` immutable snapshot; generation counter; publish through the existing single-assignment swap (`publish_principals` `:216-224`); current-generation accessor for routes and sweep | REQ-001, REQ-005 | exists; build-first comment `:105-110`, `publish_principals` `:216-224`, `Principal` `:35` | tests/eventbus/test_eventbus_auth.py, tests/eventbus/test_authz_generation_ttl.py | Verified |
| scripts/eventbus/config.py | modify | baseline-hash helper over canonicalized `consumer_authorization`/`topic_authorization` sets (frozen dataclass `:71-72`, fields `:99/:102`); TTL bounds config fields | REQ-001, REQ-005 | exists; `EventBusConfig` `scripts/eventbus/config.py:71-102` | tests/eventbus/test_authz_generation_ttl.py | Verified |
| scripts/eventbus/admin_route.py | modify | mandatory `expected_generation` validation (reject-before-change), response extension, TTL acceptance/validation, audit record gains previous/new generation | REQ-002, REQ-003, REQ-004, REQ-005, REQ-007 | exists; publish-order block `:137-147`, audit block `:152-162`, return `:164` | tests/eventbus/test_admin_topics_authorization.py | Verified |
| scripts/eventbus/authz_ttl.py | new | TTL registry (grant → expiry) + sweep coroutine with injectable clock; builds removal generation via the auth.py build-first path and audits removals | REQ-005 | new file; no `ttl`/`expires` symbol exists in `scripts/eventbus/` (absence search 2026-10-30) | tests/eventbus/test_authz_generation_ttl.py | Verified |
| scripts/eventbus/app.py | modify | lifespan wiring: start/stop the TTL sweep task; startup restart-loss audit record (REQ-006) | REQ-005, REQ-006 | exists; app lifespan hosts startup/shutdown hooks (dlqbox001 plan precedent `app.py` wiring) | tests/eventbus/test_authz_generation_ttl.py, tests/eventbus/test_admin_topics_authorization.py | Verified |
| scripts/eventbus/audit.py | modify | `log_privileged_action` (`:132-139`) gains additive `previous_generation`/`new_generation` parameters (keyword-only, default None; no secret fields) | REQ-004 | exists; signature `scripts/eventbus/audit.py:132-139` | tests/eventbus/test_eventbus_auth.py | Verified |
| config/eventbus.toml | modify | TTL sweep interval and max TTL bounds | REQ-005 | exists; canonical EventBus config consumed by `scripts/eventbus/config.py` | tests/eventbus/test_authz_generation_ttl.py | Verified |
| tests/eventbus/test_admin_topics_authorization.py | modify | stale-update rejection matrix, response extension contract, TTL grant validation, no-op + expected-generation ordering, audit generation fields | REQ-002, REQ-003, REQ-004, REQ-005, REQ-007 | exists; existing tests at `:170-186`, `:209`, `:274-295`, `:297-310` | — | Verified |
| tests/eventbus/test_authz_generation_ttl.py | new | generation monotonicity, racing updates (with/without expected generation), expiry with injected clock, sweep atomicity, restart audit record, failed-rebuild keeps generation number unchanged | REQ-001, REQ-005, REQ-006 | new file | — | Verified |
| tests/eventbus/test_eventbus_auth.py | modify | generation immutability of the published snapshot; secret-leakage regression extended to the new generation/hash fields (`:1272` test extended, not duplicated) | REQ-001, REQ-004 | exists | — | Verified |
| tests/eventbus/eventbus_helpers.py | modify | shared test fixtures: injectable clock helper and generation-aware request helpers reused by the new test file | REQ-001, REQ-005 | exists; helper module used by EventBus tests | — | Verified |
| docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md | modify | generation contract, stale rejection, TTL semantics, restart behavior; correct the stale `detail="updated"` description at `:93` | REQ-008 | exists; `:89` runtime-only text verified, `:93` stale against code, INV-05 `:191` | docs checkers (ADR gates) | Verified |
| docs/24_eventbus/eventbus_08_reference_api.md | modify | admin endpoint request/response signature tables (`:52`, `:65`) extended with expected_generation/TTL inputs and generation response fields | REQ-003, REQ-008 | exists; signature tables at `:52`/`:65` | `generate_reference_table.py --check` | Verified |
| docs/24_eventbus/eventbus_02_api-reference-index.md | modify | endpoint index reflects the extended contract | REQ-008 | exists | docs checkers | Verified |
| docs/24_eventbus/eventbus_07_configuration-and-operations.md | modify | TTL bounds config keys, sweep behavior, restart semantics for operators | REQ-005, REQ-006, REQ-008 | exists | docs checkers | Verified |

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
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md | primary authority: runtime-only contract (`:89`), INV-05 no-secrets rule (`:191`) | all REQs |
| plans/done/20261028-234417_ebaudit005_privileged-audit-actor-context.md | landed audit identity fields this Plan builds on — do not re-implement | REQ-004 |
| implementations/done/20261029-101422_01_scripts_eventbus_auth.py.md | landed publish-order procedures (build-first semantics to preserve) | REQ-001 |
| implementations/done/20261029-101422_02_scripts_eventbus_admin_route.py.md | landed admin-route publish-order procedures | REQ-001, REQ-002 |
| implementations/done/20261029-101422_03_tests_eventbus_test_admin_topics_authorization.py.md | landed test expectations this Plan extends | REQ-002, REQ-007 |
| scripts/eventbus/route_helpers.py | request-scoped config/principal access patterns the generation accessor must stay compatible with | REQ-001, `scripts/eventbus/app.py` |
| tests/eventbus/test_eventbus_consumer_authorization.py | existing authorization behavior locked by characterization tests | REQ-002 |
| tests/eventbus/conftest.py | existing EventBus test fixtures (app/client factories) | REQ-001, new test file |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002): Every effective update produces one unique monotonic generation; concurrent stale updates are rejected with zero partial change (state, principals, and audit unchanged by the rejected request).
- AC-2 (REQ-005): Temporary grants expire deterministically under the injected-clock sweep; expiry removal is one atomic generation update plus an audit record; invalid TTL values never take effect.
- AC-3 (REQ-001): A failed generation rebuild keeps the previous generation (config + principals + number) fully active.
- AC-4 (REQ-006): Restart-related loss of runtime overrides is observable as one startup audit record carrying the loaded baseline hash.
- AC-5 (REQ-004): No audit record (including new generation/hash fields) contains token values or other secrets.
- AC-6 (REQ-003, REQ-007): `status`, `persistent`, `changed` semantics unchanged; no-op behavior unchanged.
- AC-7 (REQ-008): ADR-013 and the EventBus ops docs state the generation contract, stale rejection, TTL semantics, restart behavior; the stale `detail="updated"` text is gone.

## Tests
- Concurrency (REQ-001, REQ-002): deterministic racing-update tests in `tests/eventbus/test_admin_topics_authorization.py` and `tests/eventbus/test_authz_generation_ttl.py` — two updates with the same expected generation: one succeeds, one rejected; rejected request leaves principals and config byte-identical (characterization comparison).
- Expiry (REQ-005): injected clock advances past TTL → sweep publishes exactly one new generation, grant gone, audit record emitted; TTL validation boundaries rejected.
- Restart (REQ-006): app restart test asserts the startup audit record and baseline-only state.
- Failed rebuild (REQ-001): build error during a TTL removal generation keeps the previous generation and number active (extends `test_failed_principal_build_keeps_previous_generation` at `tests/eventbus/test_admin_topics_authorization.py:274-295`).
- No-op + expected-generation ordering (REQ-007): stale expected generation on a would-be no-op is still rejected before change detection.
- Secret hygiene (REQ-004): extend `test_no_credential_leakage_in_audit_records` (`tests/eventbus/test_eventbus_auth.py:1272`) to generation/hash fields.
- Suite commands: `uv run pytest tests/eventbus`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_docs_consistency.py --domain eventbus`.

## Documentation Impact
Yes. Per `docs/00_index.md` task-scope mapping (EventBus + ADR rows): ADR-013 gains the generation contract, stale rejection, TTL semantics, restart audit semantics, and the correction of the stale `detail` description (REQ-008); `docs/24_eventbus/eventbus_08_reference_api.md` endpoint signatures (REQ-003); `docs/24_eventbus/eventbus_02_api-reference-index.md` index (REQ-008); `docs/24_eventbus/eventbus_07_configuration-and-operations.md` TTL bounds, sweep interval, restart behavior (REQ-005/REQ-006). Operational behavior and failure semantics only (`skills/DESIGN.md` Docs content policy).

## Assumptions
- `expected_generation` mandatory is the owner decision (2026-10-30); clients that omit it receive a validation error — accepted as a deliberate admin-API break, documented in ADR-013.
- Generation numbers are process-local (monotonic within one process lifetime); after restart numbering restarts from the baseline generation, and the restart audit record plus baseline hash provide the cross-restart correlation (numbers alone are not globally unique).
- Baseline hash covers only authorization pair sets (consumer/topic authorization), not the whole config, so unrelated config fields do not churn it.
- The sweep runs in the EventBus app lifespan (single writer for expiry); no cross-process scheduler is introduced.
- Temporary grants are expressed as authorization pairs carrying an expiry inside the generation metadata — the pair sets themselves remain the source of truth for authz decisions.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Maximum TTL value | No operational guidance on record | Default cap 86400s (24h) in `config/eventbus.toml`; owner confirms before production enablement | False |
| UNK-02 | Sweep interval (default 60s assumed) | No latency requirement for grant revocation | Config-keyed interval; tune after first operational use | False |
| UNK-03 | Whether generation numbers should persist across restarts (e.g. last-known number stored) | Would require persistence, out of scope (runtime-only contract) | Assumption: no persistence; restart audit + baseline hash are the correlation mechanism; revisit only if an Accepted ADR changes the persistence contract | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/eventbus/auth.py | generation snapshot + counter | every authenticated EventBus request path reads the published generation | 9 | 2 | eventbus service restart |
| scripts/eventbus/admin_route.py | mandatory expected_generation, response extension | admin API contract (breaking for callers that omit the field) | 3 | 2 | eventbus service restart |
| scripts/eventbus/app.py | sweep task + startup audit wiring | app lifespan | 9 | 3 | eventbus service restart |
| scripts/eventbus/config.py | baseline hash + TTL bounds | config consumers | 7 | 3 | Config sync on deploy |
| scripts/eventbus/audit.py | additive generation fields | audit record schema consumers | 1 | 1 | No |
| scripts/eventbus/authz_ttl.py | new module | new surface only | 0 | new (2 owners planned) | No |
| config/eventbus.toml | TTL bounds keys | EventBus config surface | — (see rules/env.md; consumed via config.py) | — | Config sync on deploy |
| tests/eventbus/test_admin_topics_authorization.py | rejection matrix + response contract | admin authz test surface | 10 | 2 | No |
| tests/eventbus/test_eventbus_auth.py | generation immutability + secret hygiene | auth test surface | 18 | 2 | No |

## Design
- Generation object (Phase 1). `AuthzGeneration` (frozen dataclass in `scripts/eventbus/auth.py`): `generation: int`, `config: EventBusConfig`, `principals: dict[str, Principal]`, `effective_at`, `baseline_hash: str`. `publish_principals` evolves into publishing a full generation snapshot while keeping the single-assignment-under-GIL property (`auth.py:216-224` semantics preserved; readers get config+principals from one object, removing the current two-source read in route helpers). Build-first-then-publish (`admin_route.py:137-147`, `auth.py:105-110`) is retained: the next generation is built completely, then swapped; a build failure leaves number and state untouched.
- Concurrency contract (Phase 1). `expected_generation` is validated first, before diff computation: request carries `expected_generation == current.generation` or the request is rejected (HTTP 409 with previous/new current numbers, no state touch). This makes last-write-wins races explicit. Owner decision: mandatory, no compatibility fallback.
- Response (Phase 1). Additive fields only: `previous_generation`, `new_generation`, `changed_count`, `effective_at`, `baseline_hash`; `status`/`persistent`/`changed` unchanged (AC-6).
- Audit (Phase 2). `log_privileged_action` gains keyword-only `previous_generation`/`new_generation` (`audit.py:132`); detail keeps the landed `name:count;...;persistent:false` format — extended with `gen:<prev>-><new>`. Secrets remain excluded (INV-05; baseline hash is a hash, not contents).
- TTL (Phase 2). Request accepts `ttl_seconds` for newly added pairs; expiry metadata lives in the generation snapshot (pair → expiry map, carried alongside the pair sets). `scripts/eventbus/authz_ttl.py` sweep: injectable clock; on expiry, builds a removal generation through the same build-first path, publishes once, audits `target="ttl_expiry"`. Invalid TTLs rejected at validation before any state change. Bounds from `config/eventbus.toml` (max TTL, sweep interval).
- Restart audit (Phase 2). Startup (`scripts/eventbus/app.py` lifespan) computes the loaded baseline hash and emits one `log_privileged_action(consumer_id="system", route="/startup", target="authz_baseline", ...)` record documenting that any runtime overrides from the previous lifetime are gone. No persistence is added (Out-of-Scope preserved).
- Docs (Phase 3): ADR-013 amendment (incl. `:93` staleness fix), endpoint tables, ops runbook text.

## Implementation steps
1. **Phase 1: Generation core + optimistic concurrency**
   - [ ] Implement `AuthzGeneration` snapshot + monotonic counter + baseline hash (REQ-001; `scripts/eventbus/auth.py`, `scripts/eventbus/config.py`)
   - [ ] Route readers to the single generation object (REQ-001; `scripts/eventbus/auth.py`, compatibility with `scripts/eventbus/route_helpers.py` semantics)
   - [ ] Mandatory `expected_generation` validation + response extension (REQ-002, REQ-003; `scripts/eventbus/admin_route.py`)
   - [ ] Characterization + race + no-op ordering tests (REQ-001, REQ-002, REQ-007; `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/eventbus_helpers.py`)
2. **Phase 2: Audit extension, TTL sweep, restart observability**
   - [ ] Additive audit parameters (REQ-004; `scripts/eventbus/audit.py`)
   - [ ] TTL validation + expiry metadata in the generation snapshot (REQ-005; `scripts/eventbus/admin_route.py`, `scripts/eventbus/config.py`, `config/eventbus.toml`)
   - [ ] Sweep module with injectable clock + atomic removal generation (REQ-005; `scripts/eventbus/authz_ttl.py`)
   - [ ] Lifespan wiring: sweep start/stop + restart baseline audit record (REQ-005, REQ-006; `scripts/eventbus/app.py`)
   - [ ] Expiry/race/restart/failed-rebuild/secret-hygiene tests (REQ-001, REQ-004, REQ-005, REQ-006; `tests/eventbus/test_authz_generation_ttl.py`, `tests/eventbus/test_eventbus_auth.py`)
3. **Phase 3: Documentation**
   - [ ] ADR-013 amendment incl. `:93` staleness correction (REQ-008; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
   - [ ] Endpoint tables + index + ops docs (REQ-003, REQ-008; `docs/24_eventbus/eventbus_08_reference_api.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`)
4. **Phase 4: Deployment & verification**
   - [ ] Full validation sequence: `uv run pytest tests/eventbus`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_docs_consistency.py --domain eventbus`, `ruff`/`bandit` per `rules/toolchain.md`; deploy.sh config sync check per `skills/deploy` (all REQs)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/auth.py | Unit (snapshot immutability, counter monotonicity, failed-build preservation) | `uv run pytest tests/eventbus/test_authz_generation_ttl.py tests/eventbus/test_eventbus_auth.py` | One published generation at a time; failures keep previous active |
| scripts/eventbus/admin_route.py | Integration (stale rejection matrix, response contract, TTL validation, no-op ordering) | `uv run pytest tests/eventbus/test_admin_topics_authorization.py` | Stale writes rejected with zero partial change; additive fields present |
| scripts/eventbus/authz_ttl.py + app.py | Integration with injected clock + restart | `uv run pytest tests/eventbus/test_authz_generation_ttl.py` | Deterministic expiry, one atomic removal, restart audit record present |
| scripts/eventbus/audit.py | Contract + secret hygiene | `uv run pytest tests/eventbus/test_eventbus_auth.py` | Generation fields present; no secrets in any record |
| docs + ADR-013 | Docs checkers | `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_docs_consistency.py --domain eventbus`, `check_adr_structure.py` | Stale `detail="updated"` removed; tables match code |

## Risks
- **Risk**: mandatory `expected_generation` breaks existing admin callers → **Mitigation**: breaking change is owner-approved (2026-10-30); ADR-013 documents the new contract; callers (runbooks/scripts) updated in the same landing window.
- **Risk**: generation-snapshot refactor (readers moving to a single object) touches every authenticated request path (`auth.py` churn 9/30d) → **Mitigation**: Phase 1 lands with characterization tests (`test_eventbus_consumer_authorization.py`) run before/after; route helpers keep their read APIs.
- **Risk**: TTL sweep racing an admin update could publish out of order → **Mitigation**: sweep builds removal generations through the same build-first path and performs the compare-and-swap against the current generation; a concurrent admin bump makes the sweep's removal abort and retry on the next interval.
- **Risk**: restart audit record could be mistaken for a security event → **Mitigation**: distinct `consumer_id="system"`/`target="authz_baseline"` vocabulary documented in the ops doc.
- **Risk**: baseline hash instability from pair-ordering differences → **Mitigation**: hash computed over canonically sorted pair sets; test asserts equality across permutations.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Generation core + optimistic concurrency | Pending | — | — | |
| 2 | Phase 2: Audit extension, TTL sweep, restart observability | Pending | — | — | |
| 3 | Phase 3: Documentation | Pending | — | — | |
| 4 | Phase 4: Deployment & verification | Pending | — | — | |

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
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261030-013620
- **Related target files**: `scripts/eventbus/auth.py`, `scripts/eventbus/config.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/app.py`, `scripts/eventbus/audit.py`, `config/eventbus.toml`, `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_authz_generation_ttl.py`, `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/eventbus_helpers.py`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/24_eventbus/eventbus_08_reference_api.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; verified absence of counter (`scripts/eventbus/` absence search 2026-10-30) | `scripts/eventbus/auth.py`, `scripts/eventbus/config.py` | Phase 1 | AC-1, AC-3 | `tests/eventbus/test_authz_generation_ttl.py`, `tests/eventbus/test_eventbus_auth.py` | Explicit in issue + verified 2026-10-30 |
| REQ-002 | Required Changes; owner decision 2026-10-30 (mandatory) | `scripts/eventbus/admin_route.py` | Phase 1 | AC-1 | `tests/eventbus/test_admin_topics_authorization.py` | Confirmed by owner decision |
| REQ-003 | Required Changes; Constraints (existing fields preserved); return anchor corrected to `:164` | `scripts/eventbus/admin_route.py`, `docs/24_eventbus/eventbus_08_reference_api.md` | Phase 1, 3 | AC-6 | response-contract tests | Explicit in issue + verified 2026-10-30 |
| REQ-004 | Required Changes; audit block `admin_route.py:152-162` (identity fields already landed) | `scripts/eventbus/audit.py`, `scripts/eventbus/admin_route.py` | Phase 2 | AC-5 | `tests/eventbus/test_eventbus_auth.py:1272` extension | Explicit in issue + verified 2026-10-30 |
| REQ-005 | Required Changes; owner decision 2026-10-30 (sweep); TTL absence verified | `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/app.py`, `scripts/eventbus/config.py`, `config/eventbus.toml` | Phase 2 | AC-2 | `tests/eventbus/test_authz_generation_ttl.py` | Confirmed by owner decision |
| REQ-006 | Required Changes | `scripts/eventbus/app.py` | Phase 2 | AC-4 | `tests/eventbus/test_authz_generation_ttl.py` | Explicit in issue |
| REQ-007 | Background (no-op verified by tests `:170-186`, `:209`, `:297-310`) | `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py` | Phase 1 | AC-6 | ordering tests | Explicit in issue + verified 2026-10-30 |
| REQ-008 | Documentation Impact; new finding: ADR-013 `:93` stale vs code | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Phase 3 | AC-7 | docs checkers | Derived from confirmed evidence |
| REQ-009 | Dependencies (ebaudit005 + publish-order already landed; build on them, do not duplicate) | `scripts/eventbus/audit.py`, `scripts/eventbus/auth.py` | Phase 1-2 | AC-3 | characterization regression (`test_failed_principal_build_keeps_previous_generation`) | Derived from confirmed evidence |

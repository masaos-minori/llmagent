# Plan: Preserve EventBus authorization mappings through `load_config()` and enforce one-role-per-token bindings

## Goal
Make `scripts/eventbus/config.py::load_config()` the authoritative path that carries the validated `consumer_authorization` and `topic_authorization` mappings into `EventBusConfig` (normalized to the runtime collection types), and make `scripts/eventbus/auth.py::_populate_token_maps()` reject duplicate non-empty token values before building principal maps and assign each token exactly its documented role, removing the collision-driven union/overwrite behavior.

## Priority
High

## Scope
- **In-Scope**:
  - Pass `consumer_authorization` and `topic_authorization` through `load_config()` to `EventBusConfig` (currently dropped after being accepted as known keys).
  - Normalize the TOML authorization-mapping value types to the `EventBusConfig` dataclass annotations (`topic_authorization` values → `set[str]`; `consumer_authorization` values stay `list[str]`).
  - Reject duplicate non-empty token values across every token field before principal maps are built, reporting the colliding field names without logging values.
  - Remove the union (`existing.roles | {role}`) and `admin_token` overwrite behavior from `_populate_token_maps()` so each configured token holds exactly its documented role set.
  - Keep missing and empty mapping semantics distinct: a missing required mapping still raises; an empty mapping stays deny-all.
  - Add regression and failure-injection tests for every acceptance criterion, including a file-load-through-startup integration test.
  - Document the token-uniqueness and mapping semantics in ADR-013.
  - Add a commented example of the authorization mappings to `config/eventbus.toml` (documentation only; no secrets).
- **Out-of-Scope**:
  - Runtime authorization updates through the admin API (the M-01 issue).
  - Schema validation and deployment gates (H-03).
  - Any change to the five-role route map, the control-plane role set, or the consumer-identity admission rule (`require_consumer_identity`).
  - Token distribution / rotation policy (not in repository evidence reviewed).
- **Dependencies**:
  - Siblings under `issues/`: none touch EventBus; this issue is independent and may go first.
  - Related memo tasks: M-01 (runtime authorization updates should reuse the loader-built principals) depends on this fix taking effect at startup but does not block this Plan; H-03 (startup preflight reuses this validation) is referenced but does not block this Plan.

## Background
Confirmed against HEAD by adversarial re-verification (Steps 2/3):
- `load_config()` in `scripts/eventbus/config.py` builds `EventBusConfig(...)` without `consumer_authorization` or `topic_authorization` (lines 326-347), although both are listed in `_KNOWN_CONFIG_KEYS` (lines 217-218) and validated in `EventBusConfig.__post_init__` (lines 160-192). A TOML value is accepted as a known key and then silently dropped. Dataclass-built configs in tests do not exercise this file-loading path.
- The defect is latent in the shipped configuration: `config/eventbus.toml` sets `auth_token` only; every per-role token is empty and no authorization table is present. It surfaces when an operator sets `consumer_token` and adds the mapping: `_populate_token_maps()` in `scripts/eventbus/auth.py` raises `consumer_token is configured but consumer_authorization is missing` (lines 137-141) because the loaded config has `consumer_authorization = None`.
- `_validate_token_combinations()` (`scripts/eventbus/config.py:48`) has no duplicate-token check. In `_populate_token_maps()` a per-role token equal to an existing map key gets `existing.roles | {role}` (line 167); a `consumer_token` equal to `auth_token` therefore yields a principal holding the control-plane roles plus CONSUMER, contradicting ADR-013 INV-02/INV-07 (the shared `auth_token` never holds the CONSUMER role). `admin_token` equal to another token silently overwrites that entry (lines 178-186).
- `_populate_token_maps()` is the single choke point that builds `_TOKEN_PRINCIPAL_MAP`: it is called from `scripts/eventbus/app.py` lifespan (line 74) and `_main()`'s config path (line 297-298) and from `scripts/eventbus/admin_route.py` on runtime authorization updates, so a guard placed here covers every production and test caller.
- Aggregated from the memo's preserve-authorization-mappings item and the duplicate-token subset of its M-04.

## Problem
A valid TOML file loses its authorization mappings before principal generation, so a configured consumer token can fail startup because its required mapping disappears. Duplicate non-empty token values are not rejected, which lets a token collide with the shared control-plane token (gaining the CONSUMER role it must not hold) or overwrite another principal, contradicting the documented one-role-per-token model.

## Reason for Change
Fail-closed authorization requires configuration ambiguity and ambiguous token-role bindings to be rejected before the server starts, and the production file-loading path must be the one tests exercise.

## Implementation Intent
Make `load_config()` the authoritative path: preserve validated mappings, normalize TOML arrays to the runtime collection types the dataclass annotation specifies, and reject token-value collisions (naming the colliding fields, never the values) before token maps are built. Place the duplicate-token guard in `_populate_token_maps()`, the function that constructs the maps, so it applies to startup and runtime rebuilds alike. Remove the collision-driven union/overwrite behavior from map construction. Keep missing and empty mapping semantics distinct.

## Requirements
- `REQ-001`: `load_config()` passes `consumer_authorization` and `topic_authorization` from the loaded TOML into `EventBusConfig` instead of dropping them.
- `REQ-002`: `load_config()` normalizes the authorization-mapping value types to the `EventBusConfig` annotations: `topic_authorization` values become `set[str]`; `consumer_authorization` values remain `list[str]`.
- `REQ-003`: `_populate_token_maps()` rejects duplicate non-empty token values across every token field before building the maps, raising a `ValueError` that names the colliding fields and never logs the values.
- `REQ-004`: `_populate_token_maps()` assigns each configured token exactly its documented role set, removing the union and `admin_token` overwrite behavior.
- `REQ-005`: missing and empty mapping semantics stay distinct — a missing required mapping still raises; an empty mapping remains deny-all.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified` per `issue-to-plan` Step 8; see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/config.py` | Modify | Add `consumer_authorization` and `topic_authorization` to the `EventBusConfig(...)` call in `load_config()` (currently absent at lines 326-347) and normalize their value types to the annotations. | REQ-001, REQ-002 | `EventBusConfig(...)` at lines 326-347 omits both keys though they are in `_KNOWN_CONFIG_KEYS` (lines 217-218) and validated in `__post_init__` (lines 160-192) | `test_eventbus_config.py` | Verified |
| `scripts/eventbus/auth.py` | Modify | Remove `existing.roles | {role}` union (line 167) and `admin_token` overwrite (lines 178-186); add a duplicate-non-empty-token check that names colliding fields and never logs values, placed before map construction. | REQ-003, REQ-004, REQ-005 | Union at line 167 gives a colliding per-role token the control-plane roles plus its own; admin overwrite at lines 181-186; no duplicate check anywhere | `test_eventbus_auth.py`, `test_admin_topics_authorization.py` | Verified |
| `config/eventbus.toml` | Modify | Add a commented example of `consumer_authorization`/`topic_authorization` shape (documentation only; no secrets, no new keys). | Supports REQ-001, REQ-002 | File currently documents per-role tokens but shows no authorization-mapping example | (none; doc-only) | Verified |
| `tests/eventbus/test_eventbus_config.py` | Add/modify | Test that `load_config()` surfaces a valid mapping on the built config, that `topic_authorization` values are `set`/`consumer_authorization` values are `list`, and that a duplicate token value via the load path is rejected. | REQ-001, REQ-002, REQ-003 | Existing `test_load_config_*` tests build configs via `load_config(toml_path)` (checked in Step 3) | `scripts/eventbus/config.py` | Verified |
| `tests/eventbus/test_eventbus_auth.py` | Add/modify | Test that no principal gains the control-plane roles + CONSUMER when a per-role token equals `auth_token`, and that duplicate values raise naming the fields. | REQ-003, REQ-004 | `_populate_token_maps` union/overwrite currently produces the collided principal; tests call `_populate_token_maps(cfg)` directly (checked in Step 3) | `scripts/eventbus/auth.py` | Verified |
| `tests/eventbus/test_eventbus_consumer_authorization.py` | Add/modify | Test that a mapping loaded through the config path reaches the consumer principal, and that an empty mapping stays deny-all while a missing required mapping raises. | REQ-001, REQ-005 | Empty-mapping deny-all vs missing-missing-raises distinction lives in `_populate_token_maps` (lines 137-157) | `scripts/eventbus/auth.py`, `scripts/eventbus/config.py` | Verified |
| `tests/eventbus/test_admin_topics_authorization.py` | Add/modify | Test one-role-per-token for each token and duplicate rejection through `_populate_token_maps` (covers the admin runtime-rebuild caller too). | REQ-003, REQ-004 | `admin_route.py` calls `_populate_token_maps(config)` at runtime (checked in Step 3) | `scripts/eventbus/auth.py`, `scripts/eventbus/admin_route.py` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Record the token-uniqueness invariant and the mapping pass-through / missing-vs-empty semantics; close the EVENTBUS-020 known deviation. | REQ-003, REQ-005 | Known Deviations section lists EVENTBUS-020 (config drops mappings; duplicate values accepted) | (none; doc-only) | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/config_loader.py` | `ConfigLoader.load()` supplies the raw dict to `load_config()`; confirm key filtering does not drop the authorization keys and that the merge path is unchanged. | `scripts/eventbus/config.py`, REQ-001 |
| `scripts/shared/config_utils.py` | `resolve_env_ref()` must still resolve `${ENV:...}` token references before validation; the normalization must not touch token values. | `scripts/eventbus/config.py`, Constraints |
| `scripts/eventbus/app.py` | Production call sites: `load_config(get_config_path())` in lifespan (line 71) and `_main()` (line 297), and `_populate_token_maps(app.state.config)` in lifespan (line 74) — confirms the authoritative order and that maps are built after load. | `scripts/eventbus/config.py`, `scripts/eventbus/auth.py`, REQ-001, REQ-003 |
| `scripts/eventbus/admin_route.py` | Calls `_populate_token_maps(config)` on runtime authorization updates; the duplicate guard must apply here too. | `scripts/eventbus/auth.py`, REQ-003 |
| `tests/eventbus/conftest.py` | Shared fixtures used by the four test files under edit. | test support |
| `tests/eventbus/eventbus_helpers.py` | Helper that monkeypatches `load_config`; shows how tests build configs without the file-load path. | test support |

## Acceptance Criteria
- A valid consumer/topic mapping loaded from a TOML file appears on the generated config and, after `_populate_token_maps()`, in the consumer principal; a consumer token with a valid mapping starts successfully. (REQ-001, REQ-005)
- On the config built by `load_config()`, `topic_authorization` values are `set[str]` and `consumer_authorization` values are `list[str]`. (REQ-002)
- Any two distinct token fields sharing a non-empty value are rejected before startup, and the error names the colliding fields without logging the values. (REQ-003)
- `auth_token`/`admin_token` equal to another token are rejected; each accepted token has exactly its documented role set (no control-plane-plus-CONSUMER principal). (REQ-003, REQ-004)
- A missing required mapping fails with an actionable message; an empty mapping remains deny-all. (REQ-005)

## Tests
- `load_config()` end-to-end: a real TOML file with `consumer_token` + `consumer_authorization` + `topic_authorization` yields a config carrying both mappings and a consumer principal that can subscribe; a missing required mapping raises; an empty mapping stays deny-all (REQ-001, REQ-005).
- Type normalization: `topic_authorization` values are `set`, `consumer_authorization` values are `list` after `load_config()` (REQ-002).
- Duplicate tokens: every relevant pair among `auth_token`, `publisher_token`, `consumer_token`, `operator_token`, `monitoring_token`, `admin_token` with the same non-empty value raises, naming the fields, via both the `load_config()` path and a direct `_populate_token_maps()` call (REQ-003).
- One-role-per-token: a `consumer_token` equal to `auth_token` is rejected (not admitted with control-plane + CONSUMER); a distinct-token config gives each token exactly its role (REQ-004).
- Runtime rebuild: `_populate_token_maps()` called as `admin_route.py` calls it still enforces REQ-003/REQ-004 (REQ-003, REQ-004).
- Distinct-token configuration still starts through the normal application lifespan (integration). (REQ-001)
- Then ruff, mypy, bandit, `lint-imports`, and the EventBus test directory.

## Documentation Impact
Yes. ADR-013 documents the token model and must record: the token-uniqueness invariant (one role per token; duplicate non-empty values rejected), the mapping pass-through and type normalization, and the missing-vs-empty mapping semantics; the EVENTBUS-020 known deviation is closed. Driven by REQ-003 and REQ-005. Target resolved via `docs/00_index.md` "Document References by Task" → the `eventbus` governance area (ADR-013, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`).

## Assumptions
- Two non-empty tokens with the same value are a hard configuration error in every deployment, per the fail-closed rule; this resolves UNK-01. (REQ-003)
- The rejection covers all six token fields including `auth_token` versus `admin_token` (identical control-plane roles today, so currently harmless) for uniformity; this resolves UNK-02. (REQ-003)
- `topic_authorization` TOML arrays are normalized to `set[str]` and `consumer_authorization` arrays stay `list[str]`, matching the `EventBusConfig` annotations `dict[str, set[str]]` and `dict[str, list[str]]`; this resolves UNK-03. (REQ-002)
- The duplicate-token guard lives in `_populate_token_maps()` (the map-builder choke point) rather than in `load_config()` alone, so it also covers the `admin_route.py` runtime rebuild and direct test callers; `load_config()` owns only the mapping pass-through and type normalization. (REQ-003)
- The `config/eventbus.toml` addition is comment-only and introduces no new keys, so it cannot change parsing or runtime behavior.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether two tokens with the same value must be a hard configuration error in every deployment. | No token distribution/rotation policy in the repository evidence reviewed; the fail-closed rule is the only guidance. | Resolved by REQ-003 (hard error, per fail-closed). Documented in the Plan's Assumptions. | False |
| UNK-02 | Whether the rejection must cover `auth_token` versus `admin_token` (identical control-plane roles today, so currently harmless). | No explicit statement restricting the check to per-role tokens only. | Resolved by REQ-003 (all six token fields, for uniformity). Documented in the Plan's Assumptions. | False |
| UNK-03 | Whether a TOML `topic_authorization` array is stored as a list or normalized to a `set` (dataclass annotation says `dict[str, set[str]]`; validators accept both). | The annotation and the validators disagree on the runtime type. | Resolved by REQ-002 (normalize to `set[str]` per the annotation). Documented in the Plan's Assumptions. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/config.py` | Modify | Low — additive: return type stays `EventBusConfig`; only `app.py` calls `load_config()`. | 5 commits | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `scripts/eventbus/auth.py` | Modify | Medium — `_populate_token_maps()` mutates global `_TOKEN_PRINCIPAL_MAP`; removing union/overwrite changes principal roles; reached from `app.py` lifespan and `admin_route.py`. | 6 commits | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `config/eventbus.toml` | Modify | Low — comment-only example; no new keys, no secrets. | 3 commits | Multiple contributors over time; not flagged | not applicable (existing cp line; content edit only) |
| `tests/eventbus/test_eventbus_config.py` | Modify | Low — test-only. | 4 commits | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_auth.py` | Modify | Low — test-only; high churn means re-run to confirm no regression. | 10 commits | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_consumer_authorization.py` | Modify | Low — test-only. | 2 commits | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `tests/eventbus/test_admin_topics_authorization.py` | Modify | Low — test-only. | 3 commits | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Low — documentation only. | N/A | Multiple contributors over time; not flagged | not applicable (rsynced) |

## Design
Path B (affects more than 3 files and changes runtime authorization behavior — duplicate values are currently silently accepted and mappings are dropped; reclassified from the provisional Path A because the fix changes what principals are admitted at startup even though no public function signature changes). Full four-dimension analysis performed:

- **Architecture**: `scripts/eventbus/config.py` imports only `shared.config_loader.ConfigLoader` and `shared.config_utils.resolve_env_ref` (no `eventbus` internal imports); `scripts/eventbus/auth.py` imports `eventbus.audit.log_auth_failure` plus FastAPI/Starlette. `lint-imports` reports all 6 contracts KEPT (incl. `eventbus must not import from agent, mcp_servers, rag, db`); the change adds no imports, so the boundary stays KEPT.
- **Dependency graphing**: `load_config()` is called only from `scripts/eventbus/app.py` (lifespan line 71, `_main()` line 297), both passing `get_config_path()` (locked by `test_load_config_call_sites_pass_get_config_path()`). `_populate_token_maps()` is called from `app.py` lifespan (line 74), `_main()`, and `admin_route.py` (runtime rebuild); tests call it directly with dataclass configs. No external service or other package reaches these symbols.
- **Historical** (30-day churn above): `auth.py` 6, `config.py` 5, `test_eventbus_auth.py` 10, `test_eventbus_config.py` 4 — moderate, active ownership.
- **Operational**: no process holds DB locks or a listener during this change; `_populate_token_maps()` runs at startup/runtime only. `ss`/`fuser` not needed (no port or DB file touched by the validation logic).

Key decisions:
- **Guard placement.** Put the duplicate-non-empty-token check in `_populate_token_maps()`, the single function that constructs `_TOKEN_PRINCIPAL_MAP`, rather than in `load_config()`. This covers the `app.py` startup path, the `admin_route.py` runtime rebuild, and direct test callers uniformly, and matches the issue's "before token maps are built" wording. `load_config()` keeps the mapping pass-through and type normalization (REQ-001, REQ-002).
- **Field set for the check.** Consider all six token fields (`auth_token`, `publisher_token`, `consumer_token`, `operator_token`, `monitoring_token`, `admin_token`), not just the per-role fields in `_PER_ROLE_TOKEN_FIELDS` (which omits `auth_token`). Collect `(value -> [field names])` for non-empty values; any value with more than one field name is a collision. Raise `ValueError` naming the fields; never interpolate or log the values.
- **Remove union and overwrite.** In the per-role loop, assign each token exactly `{role}` (its documented role) instead of `existing.roles | {role}`; since duplicates are rejected, no token is both a per-role token and a control-plane token, so `existing` is always `None`. Keep the `admin_token` block but it now only ever adds a fresh entry (no silent overwrite possible once duplicates are rejected).
- **Type normalization.** Convert `topic_authorization` values (TOML arrays → Python `list`) to `set[str]` to match the annotation `dict[str, set[str]]`; leave `consumer_authorization` values as `list[str]` per its annotation. The validators in `__post_init__` already accept both types, and `_populate_token_maps()` already wraps values in `set(...)`, so normalization is safe.
- **Preserve missing-vs-empty.** Keep the existing guard: a missing `consumer_authorization` while `consumer_token` is set still raises (lines 137-141); an empty mapping resolves to deny-all (`frozenset()`) distinct from `None` (unrestricted). Unchanged by this Plan.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Mapping pass-through and type normalization** (`scripts/eventbus/config.py`)
   - [ ] Add `consumer_authorization` and `topic_authorization` to the `EventBusConfig(...)` call in `load_config()` from `data.get(...)` (REQ-001).
   - [ ] Normalize `topic_authorization` values to `set[str]` and keep `consumer_authorization` values as `list[str]` before constructing the config (REQ-002).
2. **Phase 2: Token-role binding and duplicate rejection** (`scripts/eventbus/auth.py`)
   - [ ] Add a duplicate-non-empty-token check over all six token fields that raises naming the colliding fields without logging values, placed before `_TOKEN_PRINCIPAL_MAP` is populated (REQ-003).
   - [ ] Remove the `existing.roles | {role}` union and simplify the per-role assignment to the single documented role; retain the `admin_token` block as a fresh add only (REQ-004).
   - [ ] Confirm the missing-required-mapping raise and the empty-mapping deny-all are unchanged (REQ-005).
3. **Phase 3: Tests** (`tests/eventbus/test_eventbus_config.py`, `test_eventbus_auth.py`, `test_eventbus_consumer_authorization.py`, `test_admin_topics_authorization.py`)
   - [ ] Add file-load-through-startup, type-normalization, duplicate-rejection (every pair, both call paths), one-role-per-token, and missing-vs-empty tests covering every acceptance criterion (all REQs).
4. **Phase 4: Documentation** (`config/eventbus.toml`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
   - [ ] Add a commented authorization-mapping example to `config/eventbus.toml` (comment-only, no new keys).
   - [ ] Document token uniqueness, mapping pass-through/normalization, and missing-vs-empty semantics in ADR-013 and close the EVENTBUS-020 known deviation (REQ-003, REQ-005).
5. **Phase 5: Deployment & Verification**
   - [ ] Run ruff, mypy, bandit, `lint-imports`, the EventBus test directory, and diff-cover; confirm no union/overwrite remains in `_populate_token_maps()` and the architecture contracts stay KEPT (all REQs). Deployment is a hand-off to `skills/deploy/SKILL.md`: commit and push first; deploying is the user's decision.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/config.py` | Unit: mapping pass-through, type normalization, duplicate rejection via load path | `uv run pytest tests/eventbus/test_eventbus_config.py` | mappings present; `topic_authorization` is `set`, `consumer_authorization` is `list`; duplicate value rejected |
| `scripts/eventbus/auth.py` | Unit: duplicate rejection (every pair, direct call), one-role-per-token, admin overwrite gone | `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_admin_topics_authorization.py` | no control-plane+CONSUMER principal; each token has exactly its role |
| `scripts/eventbus/auth.py`, `scripts/eventbus/config.py` | Integration: empty deny-all vs missing-raises, startup through lifespan | `uv run pytest tests/eventbus/` | empty mapping denies all; missing required mapping raises |
| `scripts/eventbus/auth.py` | Static: no `existing.roles | {role}` union, no unconditional admin overwrite | `rg "roles \| \{" scripts/eventbus/auth.py` | zero matches |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | clean; all contracts KEPT |

## Risks
- **Risk**: Removing the union/overwrite in `_populate_token_maps()` changes principal roles for any deployment currently relying on a token that equals another credential. → **Mitigation**: the same change rejects those duplicate configurations at startup, so no deployment can silently depend on the collided principal; covered by the duplicate-rejection and one-role-per-token tests.
- **Risk**: Placing the guard in `_populate_token_maps()` rather than `load_config()` leaves a directly-constructed `EventBusConfig` (bypassing both) unvalidated. → **Mitigation**: `_populate_token_maps()` is the sole map-builder and is called on every startup and runtime rebuild; the issue scopes the guard to "before token maps are built," which is exactly this function.
- **Risk**: Normalizing `topic_authorization` to `set[str]` diverges from the raw TOML list and could surprise a reader of `cfg.topic_authorization`. → **Mitigation**: the normalization matches the dataclass annotation `dict[str, set[str]]` and `_populate_token_maps()` already wraps values in `set(...)`; a test asserts the concrete type.
- **Risk**: High churn on `test_eventbus_auth.py` (10 commits/30d) increases regression exposure. → **Mitigation**: run the full EventBus suite after the change and rely on the clean baseline (329 passed, 1 skipped) to isolate regressions.
- **Risk**: A duplicate-value error message could accidentally leak a token value. → **Mitigation**: the requirement forbids logging values; the implementation names only field names, and a test asserts the value substring is absent from the message.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Mapping pass-through and type normalization (`scripts/eventbus/config.py`) | Pending | — | — | Path B |
| 2 | Token-role binding and duplicate rejection (`scripts/eventbus/auth.py`) | Pending | — | — | Path B |
| 3 | Regression and failure-injection tests | Pending | — | — | Path B |
| 4 | Documentation: config example + ADR-013 | Pending | — | — | Path B |
| 5 | Deployment & verification (ruff/mypy/bandit/lint-imports/pytest/diff-cover) | Pending | — | — | Path B |

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
- **Source issue**: `issues/20261023-154326_eventbus002_config-authorization-token-roles.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-101136
- **Related target files**: `scripts/eventbus/config.py`, `scripts/eventbus/auth.py`, `config/eventbus.toml`, `tests/eventbus/test_eventbus_config.py`, `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_consumer_authorization.py`, `tests/eventbus/test_admin_topics_authorization.py`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; Summary; Background | `scripts/eventbus/config.py` | Step 1 | AC 1 | mapping appears on config/principal | Confirmed by repository evidence |
| REQ-002 | Unresolved Questions (UNK-03); Required Changes | `scripts/eventbus/config.py` | Step 1 | AC 2 | topic `set` / consumer `list` types | Derived from confirmed evidence |
| REQ-003 | Required Changes; Background (duplicate subset of M-04); Constraints | `scripts/eventbus/auth.py` | Step 2 | AC 3, AC 4 | duplicate rejection, one-role-per-token | Confirmed by repository evidence |
| REQ-004 | Required Changes; Background | `scripts/eventbus/auth.py` | Step 2 | AC 4 | no union/overwrite principal | Confirmed by repository evidence |
| REQ-005 | Required Changes; Background | `scripts/eventbus/auth.py`, `scripts/eventbus/config.py` | Step 2 | AC 5 | missing-raises / empty-deny-all | Confirmed by repository evidence |

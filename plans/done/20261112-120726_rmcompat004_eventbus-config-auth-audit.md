## Goal
- Validate each EventBus configuration rule once with messages that describe the current rules, keep one authorization format (`consumer_authorization`) read strictly, make admin authorization audit records always carry both generation fields in one place, and remove copied vocabulary, history notes, and tolerant `getattr`/`hasattr` reads from the EventBus config, auth, and audit code. Roles, route protection, and the credential model stay unchanged.

## Priority
Medium

## Scope
- **In-Scope**: a single required-token and loopback-bind check in `EventBusConfig.__post_init__`; removal of `topic_authorization` from the server, the TTL sweep, the agent-side admin client, and the configuration comments; strict attribute reads in `scripts/eventbus/auth.py`; deletion of `_CONSUMER_ID_ALLOWLIST`; a dedicated authorization-change audit function with required generation fields and no `gen:` suffix; `error_type` constants; removal of "Precedent", "Mirrors", and `REQ-` comments in the three named files; the documents and the generated manifest that describe these.
- **Out-of-Scope**: merging `auth_token` and `admin_token`; authorization generation persistence across restarts and the no-op contract of the admin endpoint; DLQ and delivery code (rmcompat005); replacing `json` with `orjson` in the baseline hash; `getattr` reads outside `auth.py` (`subscribe_route.py`, `app.py`); deleting `_ROUTE_ROLE_MAP` (see Background); the history-comment sweep (rmcompat007); aliases or compatibility parsing for the removed format (`compatrm001`).
- **Dependencies**: None open. The adrrev010 Issue is closed (its Plan, a docs-only ADR-013 correction, is archived in `plans/done/`); it recorded the token merge as an undecided maintainer item, so the token key names used here (`auth_token`, `admin_token`) stay. The adrrev014, adrrev016, adrrev017, and adrrev019 Plans are archived in `plans/done/` and their procedure documents are completed under `implementations/done/` (verified 2026-11-13; adrrev014's only open step is its deployment gate), so no open procedure edits `eventbus_08` or `eventbus_03`; their text is however already changed, so re-read each document before editing it. This Plan runs before the history-comment sweep (`plans/20261112-122030_rmcompat007_history-comment-sweep.md`), which sweeps the comments this Plan leaves in `scripts/eventbus/`. `plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md` regenerates `docs/24_eventbus/eventbus_08_reference_api.md` and `registry/manifests/eventbus_api.yaml` and edits `docs/24_eventbus/eventbus_07_configuration-and-operations.md`; sequencing only, run this Plan first.

## Background
Re-verified 2026-11-12 (Step 2 and Step 3), re-checked 2026-11-13 (this cycle, `rg` plus Read over the target files, and `git log --all -S` for every symbol this Plan deletes):
- `config.py`: the required `auth_token` check appears in `EventBusConfig.__post_init__` (line 150), `_validate_deployment_mode` (line 69), and `load_config` (lines 378-379); `_validate_cross_field` (called only at line 424, after the dataclass is built) runs `_validate_token_combinations`, which cannot fail because `auth_token` is non-empty by then, and `_validate_deployment_mode`, which repeats both `__post_init__` checks. The bind error (lines 66-67 and 147-148) says "set auth_token or bind to loopback" although every non-loopback host raises regardless of tokens.
- `topic_authorization` exists in `config.py` (field, validation, key lists, load conversion, `authorization_baseline_hash`), `auth.py:185-201`, `admin_route.py` (validator, request key, counts, replacements, `_authorization_pairs`), `authz_ttl.py` (`_removal_config`, removal counts), `config/eventbus.toml` (comments), the agent client `scripts/agent/eventbus_topic_admin_client.py`, the manifest `registry/manifests/eventbus_api.yaml`, and tests and documents.
- `auth.py` reads config through `getattr`/`hasattr` at lines 156, 174, 185-188, 207, 217, and 270; `_CONSUMER_ID_ALLOWLIST` (line 90) has no reference anywhere in `scripts`, `tests`, `tools`, or `docs`.
- `audit.py`: `previous_generation` and `new_generation` are `NotRequired` and added only when not `None`; `admin_route.py:264-276` and `authz_ttl.py:128-140` also append `gen:<prev>-><new>` to `detail`; `log_privileged_action` is also used by the startup baseline record, DLQ requeue, and replay, which have no generation. The module docstring copies the mdq and web_search vocabularies and starts with "Mirrors scripts/mcp_servers/audit.py".
- The values `error_type` takes in the EventBus: `authentication_failed`, `authorization_failed` (default), `consumer_identity_rejected`, `topic_authorization_rejected` (`auth.py:312,349,381,399,421`), and `""` for successful privileged actions.

Corrections found against the Issue's claims:
- `_ROUTE_ROLE_MAP` is not unreferenced: `tools/generate_reference_table.py` (`_route_role_entries`, line 572) reads it from `auth.py` by AST to build the EventBus route-role inventory, and `tests/tools/test_generate_reference_table.py:163` pins its text. The Issue searched only `scripts/eventbus/`. It stays; only `_CONSUMER_ID_ALLOWLIST` is deleted.
- `_validate_deployment_mode` is dead for the same reason as `_validate_token_combinations`, which the Issue did not state.
- `topic_authorization` is also handled in `authz_ttl.py`, the agent client `scripts/agent/eventbus_topic_admin_client.py` (no caller outside its test), and the generated manifest, none of which the Issue lists.
- The unknown-key rejection in `load_config` already fails a configuration that carries a key not in the allowed list, so removing `topic_authorization` from the lists yields the explicit load error without new parsing.
- `rg -n "REQ-[0-9]+" scripts/eventbus/audit.py scripts/eventbus/auth.py config/eventbus.toml` matches `auth.py:144` and `eventbus.toml:47,53` only.
- The test at `tests/eventbus/test_eventbus_config.py:619` expects the `load_config` message "must not be empty"; it moves to the `__post_init__` message.
- The repository `config/eventbus.toml` carries `topic_authorization` only in comments (lines 29, 42, 45), so a deployed file that copies it as an active key would be rejected at startup (UNK-03).
- The load-time unknown-key rejection is `config.py:346-351`. `_CONFIG_KEY_TYPES` (`config.py:286-312`) holds no entry for `consumer_authorization` or `topic_authorization`, so the shape of either mapping is checked only in `__post_init__`.
- The agent client sends no `expected_generation` while `admin_route.py:144-146` requires it, so a request from `EventBusTopicAdminClient.update_topics_authorization` is rejected with 422 today; `rg` finds no caller outside `tests/agent/test_eventbus_topic_admin_client.py`. Recorded as UNK-06: repairing that call is a separate scope decision, not part of this Plan's rows.

## Problem
Three copies of one check can drift, and two of the functions are dead; the bind error tells operators to set a token for a bind that no token permits; two formats for one fact allow contradictory configurations; tolerant reads accept a missing or misspelled attribute silently in the module that enforces authorization; generation fields that appear only sometimes and a duplicate `detail` suffix make admin audit records ambiguous; copied vocabulary and "Precedent" notes describe other servers and how the code was written.

## Reason for Change
The current-only policy (`compatrm001`) forbids tolerant fallbacks and duplicate formats; the bind message is the only item that can lead an operator to a wrong action today. No external deadline.

## Implementation Intent
- One check per rule, in the dataclass that every construction path (load, `dataclasses.replace`) goes through.
- One authorization format, read strictly; an unknown key fails load with the existing unknown-key error.
- `auth.py` reads attributes directly and holds no unused table.
- Authorization changes are logged by one function that requires both generation fields; other privileged actions keep their record unchanged.

## Requirements
- `REQ-001`: The required `auth_token` and the loopback bind are checked once, in `EventBusConfig.__post_init__`; `_validate_cross_field`, `_validate_token_combinations`, `_validate_deployment_mode`, and the `load_config` empty check are deleted; the bind error keeps the prefix `Event Bus bound to non-loopback address {host}` and states that only loopback addresses are allowed; each remaining failure message has a test.
- `REQ-002`: `topic_authorization` is removed from `config.py`, `auth.py`, `admin_route.py`, `authz_ttl.py`, the agent client, and the `eventbus.toml` comments; a configuration carrying it fails load with the unknown-key error; `consumer_authorization` accepts lists only.
- `REQ-003`: `auth.py` has no `getattr(config, ...)` or `hasattr(config, ...)` default and no `_CONSUMER_ID_ALLOWLIST`; `_ROUTE_ROLE_MAP` stays.
- `REQ-004`: Admin authorization audit records (admin update and TTL sweep) contain `previous_generation` and `new_generation`, required by the function that writes them, and `detail` has no `gen:` suffix; the startup, DLQ, and replay records are unchanged.
- `REQ-005`: `audit.py` documents only the `error_type` values the EventBus emits, defined as constants used by `auth.py`.
- `REQ-006`: `rg -n "Precedent|Mirrors scripts/|REQ-[0-9]+" scripts/eventbus/audit.py scripts/eventbus/auth.py config/eventbus.toml` returns nothing.
- `REQ-007`: Documents and the generated manifest describe the single authorization format, the bind rule, and the audit record; ADR-013's `Approval Record` section (lines 289-297) already records the task-level approval as acceptance evidence, so no new record is added; individual maintainer statements remain governed by UNK-05.
- `REQ-008`: Tests cover the single required-token message, the bind message, the rejected removed format, and the generation fields on every admin authorization record.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/config.py` | Config validation and format | Delete the three cross-checks and the load empty check; reword the bind error; remove `topic_authorization` (field, validation, key lists, load conversion, hash) | REQ-001, REQ-002 / AC-1, AC-2 | lines 40-70, 73-87, 118-121, 145-151, 222-237, 265-266, 346-351, 378-390, 408-409, 424 (re-checked 2026-11-13) | `tests/eventbus/test_eventbus_config.py` | Verified |
| `scripts/eventbus/auth.py` | Principal map and middleware | Remove `topic_authorization` pairs; replace `getattr`/`hasattr` reads; delete `_CONSUMER_ID_ALLOWLIST`; remove "Precedent" and `REQ-003` comments; use the `error_type` constants | REQ-002, REQ-003, REQ-005, REQ-006 / AC-2, AC-3, AC-5, AC-6 | lines 22-23, 90, 144, 156, 174, 185-201, 207, 217, 270, 312, 349, 381, 399, 421 (checked in Step 2) | `tests/eventbus/test_eventbus_auth.py` | Verified |
| `scripts/eventbus/audit.py` | Audit records | Add the `error_type` constants, the authorization-change record and function with required generation fields; drop the generation parameters from `log_privileged_action`; replace the copied docstring | REQ-004, REQ-005, REQ-006 / AC-4, AC-5, AC-6 | lines 1-34, 47-62, 134-177 (checked in Step 2) | `tests/eventbus/test_eventbus_auth.py` | Verified |
| `scripts/eventbus/admin_route.py` | Admin endpoint | Remove `topic_authorization` handling; call the authorization-change function; drop the `gen:` suffix | REQ-002, REQ-004 / AC-2, AC-4 | lines 64-99, 107, 128-140, 190-212, 264-276 (checked in Step 2) | `tests/eventbus/test_admin_topics_authorization.py` | Verified |
| `scripts/eventbus/authz_ttl.py` | TTL sweep | Remove `topic_authorization` handling; call the authorization-change function; drop the `gen:` suffix | REQ-002, REQ-004 / AC-2, AC-4 | lines 37-68, 110-140 (checked in Step 2) | `tests/eventbus/test_authz_generation_ttl.py` | Verified |
| `config/eventbus.toml` | Configuration comments | Remove the `topic_authorization` comments, the `REQ-005` and `REQ-007` comment labels | REQ-002, REQ-006 / AC-2, AC-6 | lines 25-27, 35-42, 47, 53 (checked in Step 2) | acceptance search | Verified |
| `scripts/agent/eventbus_topic_admin_client.py` | Agent-side admin client | Remove the `topic_authorization` parameter and body key | REQ-002 / AC-2 | lines 55-68; no caller outside its test (checked in Step 3) | `tests/agent/test_eventbus_topic_admin_client.py` | Verified |
| `registry/manifests/eventbus_api.yaml` | Generated API manifest | Regenerate; the endpoint summary names `topic_authorization` | REQ-007 / AC-7 | line 25 (checked in Step 2) | `generate_reference_table.py --check` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Decision text | Describe one authorization format; add the decision record with the approval pending | REQ-007 / AC-7 | lines 93, 193, 247, 268 (checked in Step 2) | `tools/check_adr_preservation.py` | Verified |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Configuration doc | Authorization format, bind rule, audit record without the `gen:` suffix | REQ-007 / AC-7 | lines 60, 90-91 (checked in Step 2) | docs checkers | Verified |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | DLQ operations doc | Authorization allowlist sentence | REQ-007 / AC-7 | line 108 (checked in Step 2) | docs checkers | Verified |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Reference API | Regenerate the guarded block; update the endpoint and audit rows | REQ-007 / AC-7 | lines 53, 56-57 (checked in Step 2) | `generate_reference_table.py --check` | Verified |
| `tests/eventbus/test_eventbus_config.py` | Config tests | Cover the single messages; the rejected removed format; drop the `topic_authorization` load tests; move the "must not be empty" expectation | REQ-001, REQ-002, REQ-008 / AC-1, AC-2 | lines 180-195, 619, 698-722 (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_auth.py` | Auth tests | Drop `topic_authorization` arguments; assert the generation fields through the new function; use the constants | REQ-002, REQ-004, REQ-005 / AC-2, AC-4 | lines 875, 931, 975, 1166, 1252-1253, 1517 (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_admin_topics_authorization.py` | Admin endpoint tests | Replace the `log_privileged_action` generation kwargs assertions and the `gen:` detail assertion; add the every-record test | REQ-004, REQ-008 / AC-4 | lines 208, 397-414, 610 (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_authz_generation_ttl.py` | TTL tests | Drop `topic_authorization`; assert the sweep record through the new function | REQ-002, REQ-004 / AC-2, AC-4 | lines 147-148, 310-320 (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_consumer_authorization.py` | Consumer authorization tests | Replace the TOML fixture that uses `topic_authorization` | REQ-002 / AC-2 | line 303 (checked in Step 3) | itself | Verified |
| `tests/agent/test_eventbus_topic_admin_client.py` | Client tests | Remove the `topic_authorization` cases | REQ-002 / AC-2 | lines 57, 65, 84 (checked in Step 3) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/generate_reference_table.py` | `_route_role_entries` reads `_ROUTE_ROLE_MAP` from `auth.py`, so the table stays | REQ-003 |
| `tests/tools/test_generate_reference_table.py` | Pins the `_ROUTE_ROLE_MAP` text | REQ-003 |
| `scripts/eventbus/app.py` | Startup baseline record uses `log_privileged_action` (unchanged) | REQ-004 |
| `scripts/eventbus/dlq_route.py` | DLQ record uses `log_privileged_action` (unchanged) | REQ-004 |
| `scripts/eventbus/replay_route.py` | Replay record uses `log_privileged_action` (unchanged) | REQ-004 |
| `docs/24_eventbus/eventbus_02_api-reference-index.md` | Names the response fields `previous_generation`/`new_generation`; unchanged | REQ-007 |
| `plans/done/20261111-000400_adrrev010_eventbus-authz-harden.md` | Closed dependency; token key names stay | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): `rg -n "auth_token is required|must not be empty" scripts/eventbus/config.py` returns one required-token message; the bind error contains no instruction to set a token; each remaining failure message has a test.
- AC-2 (REQ-002): `rg -n "topic_authorization" scripts config registry tests` returns only the test that asserts a configuration carrying it fails load and the `topic_authorization_rejected` audit value; a configuration with the key fails load with an explicit error.
- AC-3 (REQ-003): `auth.py` has no `getattr(config`, no `hasattr(config`, and no `_CONSUMER_ID_ALLOWLIST`; `_ROUTE_ROLE_MAP` is unchanged.
- AC-4 (REQ-004): every authorization-change audit record has both generation fields and `detail` has no `gen:` suffix, covered by a test.
- AC-5 (REQ-005): `audit.py` defines the four `error_type` constants and `auth.py` uses them; the docstring names no other server's vocabulary.
- AC-6 (REQ-006): `rg -n "Precedent|Mirrors scripts/|REQ-[0-9]+" scripts/eventbus/audit.py scripts/eventbus/auth.py config/eventbus.toml` returns nothing.
- AC-7 (REQ-007): the documents and the manifest match the code; `generate_reference_table.py --check` and the docs and ADR checkers pass.
- AC-8 (REQ-008): `uv run pytest tests/eventbus tests/agent/test_eventbus_topic_admin_client.py` passes.

## Tests
- REQ-001: one test per remaining message (empty token, bind), with the bind test keeping the `non-loopback` match used by `test_eventbus_startup.py`.
- REQ-002: a `load_config` test with `topic_authorization` in the TOML expecting the unknown-key error; the client test asserts the body has no such key.
- REQ-004, REQ-008: an endpoint test and a sweep test assert both generation fields on the record and no `gen:` in `detail`.
- REQ-005: the `topic_authorization_rejected` audit test uses the constant.

## Documentation Impact
- Documentation must be updated (REQ-007): ADR-013 (decision text; its `Approval Record` section at lines 289-297 already records the task-level approval as acceptance evidence, and individual maintainer statements remain governed by UNK-05), the EventBus configuration and operations document, the DLQ operations document, and the reference API document, located through `docs/00_index.md` "Document References by Task". Describe intent, boundaries, and failure behavior only. Run the `routing.md` checkers, `check_docs_consistency.py --domain eventbus`, and the ADR checkers.

## Assumptions
- `__post_init__` is the right single place: every construction path (load, `dataclasses.replace` in the admin route and TTL sweep) passes through it. The load-time message for an empty referenced environment value becomes the `__post_init__` message; the existing test only changes its expected text.
- A new `log_authorization_change` function plus an `AuthzChangeRecord` type keeps `log_privileged_action` unchanged for records that have no generation, rather than making the generation fields required for every privileged action (DLQ requeue and replay have no generation).
- `_ROUTE_ROLE_MAP` is kept because the reference generator reads it; removing it would need a separate generator change (UNK-02).
- The audit `error_type` values are unchanged strings, so existing log queries and tests keep working.
- Overlap judgements (`tools/check_plan_target_overlaps.py`, re-run 2026-11-13; report-only candidates, judged here): `plans/20261112-122030_rmcompat007_history-comment-sweep.md` names `scripts/eventbus/config.py`, `auth.py`, `audit.py`, `admin_route.py`, `authz_ttl.py`, `config/eventbus.toml`, `docs/24_eventbus/eventbus_08_reference_api.md`, and `registry/manifests/eventbus_api.yaml` — compatible, sequencing only: rmcompat007 sweeps the `REQ-`/`EBAUTHGEN`/`ADR-` label comments this Plan leaves behind (for example `config.py:382`, `admin_route.py:114,143,171,238`, `authz_ttl.py:4`), so this Plan runs first and must not delete labels outside its own row scope. `plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md` names `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/24_eventbus/eventbus_08_reference_api.md`, and `registry/manifests/eventbus_api.yaml` — compatible, sequencing only: that Plan edits DLQ sentences and regenerates the same guarded blocks; run this Plan first and regenerate rather than hand-edit. The adrrev014, adrrev016, adrrev017, and adrrev019 Plans are archived in `plans/done/` with completed procedures, so their edits are already applied: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` now carries an `Implementation` column in the Automated Tests table (rows 242-262) and Decision Detail 12 sits at line 103, and `scripts/eventbus/auth.py` `attach_auth_middleware` (line 454) already has its corrected docstring — re-read each location before editing, and edit different sentences than those documents changed.
- The `getattr` reads in `subscribe_route.py` and `app.py` are out of scope; `auth.py` is the only module named.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether audit records written before this change must stay readable (only new records change) | Maintainer statement | The change affects new records only; ask before deploy | False |
| UNK-02 | Whether `_ROUTE_ROLE_MAP` should be removed together with a change to the reference generator | Maintainer decision | Kept here; file a separate Issue if wanted | False |
| UNK-03 | Whether the deployed `/opt/llm/config/eventbus.toml` carries an active `topic_authorization` key | Read access to production configuration | Operator checks before deploy; an active key stops startup with the unknown-key error | False |
| UNK-04 | Whether an operator script calls `POST /admin/topics/authorization` with `topic_authorization` | Operator knowledge | No caller in the repository besides the agent client; ask before deploy | False |
| UNK-05 | Whether individual maintainer approval statements are required for ADR-013: the `Approval Record` section (ADR-013:289-297) already records the task-level approval as acceptance evidence and states that no individual-name record exists | The statement | Maintainer writes individual statements per `governance_05` if required; not written here | False |
| UNK-06 | Whether `EventBusTopicAdminClient` should send `expected_generation`, which `admin_route.py:144-146` requires and the client does not send today | Maintainer decision on the client contract | Out of scope here (row 7 removes `topic_authorization` only); file a separate Issue if the client is meant to work against the endpoint | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/config.py` | Modify | High | 9 | N/A | not applicable (rsynced) |
| `scripts/eventbus/auth.py` | Modify | High | 8 | N/A | not applicable (rsynced) |
| `scripts/eventbus/audit.py` | Modify | Medium | 2 | N/A | not applicable (rsynced) |
| `scripts/eventbus/admin_route.py` | Modify | Medium | 5 | N/A | not applicable (rsynced) |
| `scripts/eventbus/authz_ttl.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `config/eventbus.toml` | Modify | Medium | 6 | N/A | not applicable (rsynced) |
| `scripts/agent/eventbus_topic_admin_client.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `registry/manifests/eventbus_api.yaml` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Low | 11 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Modify | Low | 19 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify | Low | 23 | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_config.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_auth.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_admin_topics_authorization.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_authz_generation_ttl.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_consumer_authorization.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_eventbus_topic_admin_client.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Consumer scan (`rg` over `scripts tests docs tools config registry`): `topic_authorization` consumers are the target rows above; `_validate_cross_field` is called only by `load_config`; `log_privileged_action` callers are `app.py`, `dlq_route.py`, `replay_route.py`, `admin_route.py`, `authz_ttl.py`, and tests patch it in `test_eventbus_dlq.py` and `test_eventbus_replay_pagination.py` (unchanged signature for non-generation calls). The scan is text-only.
- Wire contract: the request body of `POST /admin/topics/authorization` loses `topic_authorization`; the 422 text for an empty body names `consumer_authorization` and `expected_generation` only. The response is unchanged. The audit record for authorization changes keeps its keys; only the guarantee that the generation fields are present, and the removal of the duplicate `detail` suffix, change.
- Audit design: `AuthzChangeRecord` extends the record type with required `previous_generation` and `new_generation`; `log_authorization_change(...)` takes both as required keyword arguments and is called by the admin route and the TTL sweep. Alternative rejected: making the fields required on `log_privileged_action` (breaks DLQ, replay, and the startup record).
- Config design: `EventBusConfig.__post_init__` keeps the port, retry, bind, token, and threshold checks; the module keeps `_is_public_host` for the startup bind guard in `app.py`.
- Import architecture: `lint-imports` baseline recorded in the rmcompat001 Plan Design (6 contracts kept, repository state unchanged for `eventbus`); the change adds no import and keeps the eventbus-is-isolated contract. The agent client change removes a parameter only.
- Complexity (`radon cc`): `EventBusConfig` D (30), `__post_init__` D (29), `update_topics_authorization` D (28) shrink; `_build_principal_map` C (19). `vulture` and `bandit` baselines are in the rmcompat001 Plan Design; deletions add no finding.
- No persisted schema, port, process, or dependency change (`rules/persisted-schema-change.md`, `ss`, `fuser`, `pip-audit` N/A). Historical: churn above from `git log --since=30.days`; bus factor not measured.

## Implementation steps
1. **Phase 1: Single validation**
   - [ ] Delete the three cross-checks and the load empty check; reword the bind error (REQ-001; `scripts/eventbus/config.py`)
   - [ ] Cover each remaining message (REQ-001, REQ-008; `tests/eventbus/test_eventbus_config.py`)
2. **Phase 2: Remove `topic_authorization` from the server**
   - [ ] Remove the field, validation, key lists, conversion, and hash use (REQ-002; `scripts/eventbus/config.py`)
   - [ ] Remove the pairs in the principal map (REQ-002; `scripts/eventbus/auth.py`)
   - [ ] Remove the validator, request key, counts, and pairs (REQ-002; `scripts/eventbus/admin_route.py`, `scripts/eventbus/authz_ttl.py`)
   - [ ] Remove the comments and the `REQ-005`/`REQ-007` labels (REQ-002, REQ-006; `config/eventbus.toml`)
3. **Phase 3: Remove it from the client and update tests**
   - [ ] Remove the parameter and body key (REQ-002; `scripts/agent/eventbus_topic_admin_client.py`, `tests/agent/test_eventbus_topic_admin_client.py`)
   - [ ] Drop or replace the fixtures and add the rejected-format test (REQ-002, REQ-008; `tests/eventbus/test_eventbus_config.py`, `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_authz_generation_ttl.py`, `tests/eventbus/test_eventbus_consumer_authorization.py`, `tests/eventbus/test_admin_topics_authorization.py`)
4. **Phase 4: Strict reads in `auth.py`**
   - [ ] Replace `getattr`/`hasattr`, delete `_CONSUMER_ID_ALLOWLIST`, remove the "Precedent" and `REQ-003` comments (REQ-003, REQ-006; `scripts/eventbus/auth.py`)
5. **Phase 5: Audit records**
   - [ ] Add the constants, the record type, and `log_authorization_change`; trim `log_privileged_action`; rewrite the docstring (REQ-004, REQ-005, REQ-006; `scripts/eventbus/audit.py`)
   - [ ] Use the new function and drop the `gen:` suffix (REQ-004; `scripts/eventbus/admin_route.py`, `scripts/eventbus/authz_ttl.py`); use the constants (REQ-005; `scripts/eventbus/auth.py`)
6. **Phase 6: Audit tests**
   - [ ] Update the generation-field and `gen:` assertions and add the every-record test (REQ-004, REQ-005, REQ-008; `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_authz_generation_ttl.py`, `tests/eventbus/test_eventbus_auth.py`)
7. **Phase 7: Documents and manifest**
   - [ ] Update the decision text where this Plan changes behavior; the `Approval Record` section (lines 289-297) already records the task-level approval, so no new record is added (REQ-007; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
   - [ ] Update the three EventBus documents (REQ-007; `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_08_reference_api.md`) and regenerate the manifest (REQ-007; `registry/manifests/eventbus_api.yaml`)
8. **Phase 8: Deployment and verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (approval gate). Prerequisite: the operator confirms the deployed `config/eventbus.toml` has no active `topic_authorization` key (UNK-03). Run the acceptance searches, the validation sequence, and the docs and ADR checkers (REQ-001 to REQ-008)

### Release units
**Unit**: single-authorization-format | **Phases**: 2, 3 | **Reason**: removing the dataclass field breaks `dataclasses.replace` callers, the client, and every test that passes it until all land.
**Unit**: authorization-audit-record | **Phases**: 5, 6 | **Reason**: removing the generation parameters from `log_privileged_action` breaks the admin and sweep callers and the tests that assert its keyword arguments until the new function and tests land.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| EventBus config, auth, audit, routes | Unit | `uv run pytest tests/eventbus` | Pass |
| Agent client | Unit | `uv run pytest tests/agent/test_eventbus_topic_admin_client.py` | Pass |
| Changed Python files | Static | `uv run ruff format`, `ruff check`, `mypy --no-namespace-packages`, `lint-imports`, `bandit -r scripts/ -c pyproject.toml`, `python tools/check_module_size.py` | No new finding |
| Whole change | Search | the AC-1 to AC-6 `rg` commands | Match the criteria |
| Manifest and reference | Generator | `uv run python tools/generate_reference_table.py --check` (and `--type eventbus` to refresh) | No drift |
| Documents and ADR | Docs | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain eventbus`, `check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_reference.py`, `check_known_deviation_sync.py` | No findings |
| Coverage | Coverage | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the threshold |

## Risks
- **Risk**: A deployed `eventbus.toml` still has an active `topic_authorization` key and the Event Bus stops at startup → **Mitigation**: UNK-03 and the Phase 8 prerequisite; the repository copy has the key only in comments.
- **Risk**: An operator script sends `topic_authorization` to the admin endpoint → **Mitigation**: UNK-04; the server ignores unknown body keys, and an empty effective body returns the existing 422.
- **Risk**: Deleting `_ROUTE_ROLE_MAP` as the Issue says breaks the reference generator and the generated docs → **Mitigation**: it is kept; only `_CONSUMER_ID_ALLOWLIST` goes.
- **Risk**: An open rmcompat005 or rmcompat007 procedure edits `eventbus_08` or the manifest at the same time → **Mitigation**: re-read before editing; regenerate the guarded block with the tool rather than by hand.
- **Risk**: Moving the empty-token check changes the message an operator sees at load → **Mitigation**: the `__post_init__` message is the existing one used on every other path; the test and the documents carry the new text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Single validation in `__post_init__` and its tests | Completed | 20261113-164012 | 20261113-164012 |  |
| 2 | Remove `topic_authorization` from the server code and `eventbus.toml` | Completed | 20261113-164012 | 20261113-164012 | Release unit single-authorization-format with step 3 |
| 3 | Remove it from the client and update tests | Completed | 20261113-164012 | 20261113-164012 | Release unit single-authorization-format with step 2 |
| 4 | Strict attribute reads and dead table in `auth.py` | Completed | 20261113-164012 | 20261113-164012 |  |
| 5 | Authorization-change audit function, constants, call sites | Completed | 20261113-164012 | 20261113-164012 | Release unit authorization-audit-record with step 6 |
| 6 | Audit tests | Completed | 20261113-164012 | 20261113-164012 | Release unit authorization-audit-record with step 5 |
| 7 | Documents and generated manifest | Completed | 20261113-164012 | 20261113-164012 | manifest regenerated; ADR-013, eventbus_07/03/08 updated; adr_006 WI-01 reword included |
| 8 | Deployment hand-off and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261113-135237_01_scripts_eventbus_config.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261113-135237_02_scripts_eventbus_auth.py.md` | 2, 4, 5 | Procedure | Pending | — | — |
| `implementations/20261113-135237_03_scripts_eventbus_audit.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261113-135237_04_scripts_eventbus_admin_route.py.md` | 2, 5 | Procedure | Pending | — | — |
| `implementations/20261113-135237_05_scripts_eventbus_authz_ttl.py.md` | 2, 5 | Procedure | Pending | — | — |
| `implementations/20261113-135237_06_config_eventbus.toml.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261113-135237_07_scripts_agent_eventbus_topic_admin_client.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261113-135237_08_registry_manifests_eventbus_api.yaml.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261113-135237_09_docs_10_adr_adr_02_04_013_eventbus-authentication-authorization.md.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261113-135237_10_docs_24_eventbus_eventbus_07_configuration-and-operations.md.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261113-135237_11_docs_24_eventbus_eventbus_03_dlq_operations.md.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261113-135237_12_docs_24_eventbus_eventbus_08_reference_api.md.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261113-135237_14_tests_eventbus_test_eventbus_auth.py.md` | 3, 6 | Procedure | Pending | — | — |
| `implementations/20261113-135237_17_tests_eventbus_test_eventbus_consumer_authorization.py.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261112-120726
- **Related target files**: `scripts/eventbus/config.py`, `scripts/eventbus/auth.py`, `scripts/eventbus/audit.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/authz_ttl.py`, `config/eventbus.toml`, `scripts/agent/eventbus_topic_admin_client.py`, `registry/manifests/eventbus_api.yaml`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_08_reference_api.md`, `tests/eventbus/test_eventbus_config.py`, `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_authz_generation_ttl.py`, `tests/eventbus/test_eventbus_consumer_authorization.py`, `tests/agent/test_eventbus_topic_admin_client.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `config.py:40-70,150,377` | `scripts/eventbus/config.py` | 1 | AC-1 | `tests/eventbus/test_eventbus_config.py` | Confirmed by repository evidence |
| REQ-001 | Acceptance Criteria 1-2 | `tests/eventbus/test_eventbus_config.py` | 1 | AC-1 | itself | Explicit in issue |
| REQ-002 | Required Changes 2; `config.py:117-121,265-266,382-390` | `scripts/eventbus/config.py` | 2 | AC-2 | `tests/eventbus/test_eventbus_config.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 2; `auth.py:185-201` | `scripts/eventbus/auth.py` | 2 | AC-2 | `tests/eventbus/test_eventbus_auth.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 2; `admin_route.py:64-99,190-212` | `scripts/eventbus/admin_route.py` | 2 | AC-2 | `tests/eventbus/test_admin_topics_authorization.py` | Confirmed by repository evidence |
| REQ-002 | Derived from `authz_ttl.py:37-68,110-126` | `scripts/eventbus/authz_ttl.py` | 2 | AC-2 | `tests/eventbus/test_authz_generation_ttl.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes 2 and 6; `eventbus.toml:25-42` | `config/eventbus.toml` | 2 | AC-2 | acceptance search | Explicit in issue |
| REQ-002 | Derived from the client parameter `eventbus_topic_admin_client.py:58-68` | `scripts/agent/eventbus_topic_admin_client.py` | 3 | AC-2 | `tests/agent/test_eventbus_topic_admin_client.py` | Derived from confirmed evidence |
| REQ-002 | Testing Expectations; test fixtures | `tests/eventbus/test_eventbus_auth.py` | 3 | AC-2 | itself | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; `test_authz_generation_ttl.py:310-320` | `tests/eventbus/test_authz_generation_ttl.py` | 3 | AC-2 | itself | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; `test_eventbus_consumer_authorization.py:303` | `tests/eventbus/test_eventbus_consumer_authorization.py` | 3 | AC-2 | itself | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; `test_admin_topics_authorization.py:610` | `tests/eventbus/test_admin_topics_authorization.py` | 3 | AC-2 | itself | Confirmed by repository evidence |
| REQ-002 | Derived from the client; `test_eventbus_topic_admin_client.py:57-84` | `tests/agent/test_eventbus_topic_admin_client.py` | 3 | AC-2 | itself | Confirmed by repository evidence |
| REQ-003 | Required Changes 3; `auth.py:90,156,174,185-217,270` | `scripts/eventbus/auth.py` | 4 | AC-3 | `tests/eventbus/test_eventbus_auth.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 4; `audit.py:134-177`, `admin_route.py:264-276` | `scripts/eventbus/audit.py` | 5 | AC-4 | `tests/eventbus/test_admin_topics_authorization.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 4; `admin_route.py:264-276` | `scripts/eventbus/admin_route.py` | 5 | AC-4 | `tests/eventbus/test_admin_topics_authorization.py` | Confirmed by repository evidence |
| REQ-004 | Derived from `authz_ttl.py:128-140` | `scripts/eventbus/authz_ttl.py` | 5 | AC-4 | `tests/eventbus/test_authz_generation_ttl.py` | Derived from confirmed evidence |
| REQ-004 | Testing Expectations; `test_admin_topics_authorization.py:208,397-414` | `tests/eventbus/test_admin_topics_authorization.py` | 6 | AC-4 | itself | Confirmed by repository evidence |
| REQ-004 | Testing Expectations; `test_authz_generation_ttl.py:147-148` | `tests/eventbus/test_authz_generation_ttl.py` | 6 | AC-4 | itself | Confirmed by repository evidence |
| REQ-004 | Testing Expectations; `test_eventbus_auth.py:1252-1253` | `tests/eventbus/test_eventbus_auth.py` | 6 | AC-4 | itself | Confirmed by repository evidence |
| REQ-005 | Required Changes 5; `audit.py:10-22`, `auth.py:312-421` | `scripts/eventbus/auth.py` | 5 | AC-5 | `tests/eventbus/test_eventbus_auth.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes 6; `auth.py:22-23,144` | `scripts/eventbus/auth.py` | 4 | AC-6 | acceptance search | Confirmed by repository evidence |
| REQ-006 | Required Changes 6; `audit.py:5-8` | `scripts/eventbus/audit.py` | 5 | AC-6 | acceptance search | Confirmed by repository evidence |
| REQ-006 | Required Changes 6; `eventbus.toml:47,53` | `config/eventbus.toml` | 2 | AC-6 | acceptance search | Confirmed by repository evidence |
| REQ-007 | Documentation Impact; ADR-013 lines 93, 193, 247, 268 | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | 7 | AC-7 | ADR checkers | Explicit in issue |
| REQ-007 | Documentation Impact; `eventbus_07:60,90-91` | `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | 7 | AC-7 | docs checkers | Explicit in issue |
| REQ-007 | Documentation Impact; `eventbus_03:108` | `docs/24_eventbus/eventbus_03_dlq_operations.md` | 7 | AC-7 | docs checkers | Derived from confirmed evidence |
| REQ-007 | Documentation Impact; `eventbus_08:53,56-57` | `docs/24_eventbus/eventbus_08_reference_api.md` | 7 | AC-7 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-007 | Derived from `eventbus_api.yaml:25` | `registry/manifests/eventbus_api.yaml` | 7 | AC-7 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-008 | Testing Expectations; the new config-message and rejected-format tests | `tests/eventbus/test_eventbus_config.py` | 1 | AC-8 | `tests/eventbus` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261113-135237 -->
## Goal
- Remove the confirmed defects in the EventBus authorization code and ADR-013 that need no owner decision (duplicate principal build, unreachable 500 branch, ambiguous middleware name, incomplete ADR-013 Scope and Implementation References, undocumented TTL baseline behavior, undefined requeue `delivery` value), and record the option tables for every owner-decision item without changing authorization behavior.

## Priority
High

## Scope
- **In-Scope**:
  - Build the `admin_token` principal once in `_build_principal_map` (REQ-001).
  - Remove the unreachable 500 branch in `resolve_principal` and the then-unused `get_auth_token` (REQ-002).
  - Rename the EventBus request-ID middleware function and update every caller, test, docstring cross-reference, and ADR-013 mention (REQ-003).
  - ADR-013 corrections that change no Decision, Invariant, Blocking value, authority edge, or Approval text: Scope, Implementation References, TTL baseline note, decision-reference and formatting re-check (REQ-004).
  - Define the requeue response value `delivery: "replay"` in the DLQ semantics guide (REQ-005).
  - Characterization tests that pin the TTL baseline behavior before it is documented (REQ-006).
  - Regenerate the generated EventBus API manifest and reference block (REQ-007).
  - Record the option tables for the owner-decision items in this Plan's Design section.
- **Out-of-Scope**:
  - Implementing any owner-decision item: per-role token presence rule, consumer identity binding, role concentration, publish authorization and the JSONL role, new ADR-013 Invariants, audit event separation. Each is an Unknown (UNK-01 to UNK-06) and needs its own Plan after the decision is recorded.
  - Database schema or DDL changes.
  - The subscribe route (not reviewed).
  - The `_fingerprint` helper and duplicate `hashlib` import in `auth.py` (owned by the EventBus task supervision issue, adrchk017).
  - Writing, paraphrasing, or simulating a maintainer approval statement.
- **Dependencies**: The EventBus task supervision issue (adrchk017) also edits `auth.py` and `authz_ttl.py`; the contract manifest sources issue (adrchk014) names the same files. Both are sequencing-only overlaps in disjoint hunks, so no ordering is imposed here (UNK-09). The ADR approval governance issue (adrchk011) is closed: its Issue is archived and the ADR Pending Amendment Form exists in the documentation policy.

## Background
The EventBus authorization code and ADR-013 disagree on consumer identity, role concentration, publish authorization, configuration validation, and auditing. The issue was filed from a consolidated ADR review whose claims carry the evidence label `Documentation only`. Step 2 re-verified each claim against current source; the verdicts are in Design.

## Problem
Confirmed in current source: one `consumer_token` principal holds every `consumer_authorization` pair; the shared `auth_token` and `admin_token` hold Operator, Monitoring, and Admin together; `/publish` has no per-topic check and takes `producer` from the body; `admin_token` is built twice; the 500 branch in `resolve_principal` cannot run; the EventBus `attach_auth_middleware` shares a name with the MCP authentication middleware; ADR-013 Scope and Implementation References omit `admin_route.py`, `authz_ttl.py`, and their tests. Several issue claims were refuted or narrowed (see Design).

## Reason for Change
Implementation Intent of the issue requires that every authorization behavior maps to an ADR-013 statement and that no unreachable security branch remains. The no-decision subset can land now; the decision subset must wait for a recorded decision (issue Constraints).

## Implementation Intent
Land the verified no-decision fixes as small revertable phases, pin the TTL baseline behavior with tests before documenting it, regenerate derived artifacts, and keep all decision-gated changes out of the code until an owner decision exists.

## Requirements
- `REQ-001`: `_build_principal_map` builds the `admin_token` principal exactly once, with the control-plane roles and no Consumer or Publisher role; observable behavior is unchanged.
- `REQ-002`: `resolve_principal` has no unreachable 500 branch, and `get_auth_token`, which that branch alone used, is removed.
- `REQ-003`: The EventBus request-ID middleware function is renamed to `attach_request_id_middleware`, and every caller, test, docstring cross-reference, and ADR-013 mention of the EventBus function is updated; the MCP function of the same old name and its callers stay unchanged.
- `REQ-004`: ADR-013 Scope (Components and Tests) and Implementation References list `admin_route.py`, `authz_ttl.py`, `test_admin_topics_authorization.py`, and `test_authz_generation_ttl.py`; Implementation Notes states the verified TTL baseline behavior; the decision-reference and formatting claims are re-checked and fixed only if reproduced; no Decision, Invariant, Blocking value, authority edge, or Approval text changes.
- `REQ-005`: The DLQ semantics guide defines the `delivery: "replay"` value returned by the requeue endpoint.
- `REQ-006`: Characterization tests pin the TTL baseline behavior (baseline hash ignores expiries, restart baseline carries no expiries, carried-over pairs keep their expiry, the sweep removes an expired pair from runtime config only) without changing behavior.
- `REQ-007`: `registry/manifests/eventbus_api.yaml` and the guarded block in `docs/24_eventbus/eventbus_08_reference_api.md` are regenerated, not hand-edited, after REQ-002 and REQ-003.

## Implementation Target Files
**Freeze status**: Frozen (set to `Frozen` only once `issue-to-plan` Step 8's
Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/auth.py` | Modify | Drop `admin_token` from the per-role loop so the dedicated control-plane block is its only build; remove the 500 branch in `resolve_principal` and `get_auth_token`; rename `attach_auth_middleware` | REQ-001, REQ-002, REQ-003 / AC-1, AC-2, AC-3 | `_PER_ROLE_TOKEN_FIELDS` contains `admin_token` and the later `admin_token` block overwrites that entry; `get_auth_token` is called only by `resolve_principal`; `EventBusConfig.__post_init__` rejects an empty `auth_token` (checked in Step 2) | `tests/eventbus/test_eventbus_config.py::test_admin_token_grants_control_plane_roles_only`, `tests/eventbus/test_eventbus_auth.py` | Verified |
| `scripts/eventbus/app.py` | Modify | Import and call the renamed middleware function | REQ-003 / AC-3 | `app.py` imports `attach_auth_middleware` and calls it once on the app (checked in Step 2) | `tests/eventbus/test_eventbus_app_isolation.py`, `tests/eventbus/test_eventbus_startup.py` | Verified |
| `tests/eventbus/test_eventbus_auth.py` | Modify | Update the import and the call in the fixture app builder | REQ-003 / AC-3 | The test imports `attach_auth_middleware` from `eventbus.auth` and calls it on the local app (checked in Step 2) | `tests/eventbus/test_eventbus_auth.py` | Verified |
| `scripts/mcp_servers/server.py` | Modify | Update the docstring cross-reference to the EventBus function (fallout of the rename; not in the issue's Target Files) | REQ-003 / AC-3 | The `attach_auth_middleware` docstring names `eventbus.auth.attach_auth_middleware` (checked in Step 2) | `tests/mcp_servers/test_mcp_server_base.py` | Verified |
| `tests/eventbus/test_authz_generation_ttl.py` | Modify | Add characterization tests for the TTL baseline behavior | REQ-006 / AC-6 | The file exercises generation and TTL behavior of `admin_route.py` and `authz_ttl.py`; `AuthzGeneration.expiries` and `authorization_baseline_hash` define the behavior (checked in Step 3) | `tests/eventbus/test_authz_generation_ttl.py` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Rename the EventBus function in Current State, Decision Details 1, and Implementation References; add missing Scope and Implementation References entries; add the TTL baseline note to Implementation Notes | REQ-003, REQ-004 / AC-3, AC-4 | Scope and Implementation References do not list `admin_route.py`, `authz_ttl.py`, or their tests; three mentions refer to the EventBus function (checked in Step 2) | `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_authz_generation_ttl.py` | Verified |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Modify | Define the `delivery: "replay"` value near the requeue description | REQ-005 / AC-5 | `dlq_route.py` returns `"delivery": "replay"` on a successful requeue; only `eventbus_09_publish_durability.md` explains it (checked in Step 2) | N/A: documentation only; checkers in Validation plan | Verified |
| `registry/manifests/eventbus_api.yaml` | Modify | Regenerate with `tools/generate_reference_table.py --manifests`; never hand-edit | REQ-007 / AC-7 | The manifest holds an `attach_auth_middleware` entry and a `get_auth_token` entry (checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify | Regenerate the guarded `AUTO-GENERATED` block; never hand-edit | REQ-007 / AC-7 | The guarded block lists `attach_auth_middleware` and `get_auth_token` rows (checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |

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
| `scripts/eventbus/config.py` | Confirms `auth_token` rejection and the stale per-role token comment (UNK-01) | REQ-002, UNK-01 |
| `scripts/eventbus/authz_ttl.py` | Defines the sweep behavior that REQ-006 pins and REQ-004 documents | REQ-004, REQ-006 |
| `scripts/eventbus/admin_route.py` | Defines the TTL grant and carried-over expiry behavior | REQ-004, REQ-006 |
| `scripts/eventbus/audit.py` | Event and `error_type` vocabulary for UNK-06 | UNK-06 |
| `scripts/eventbus/dlq_route.py` | Source of the `delivery: "replay"` response value | REQ-005 |
| `scripts/eventbus/publish_route.py` | Publish authorization, `producer`, and JSONL behavior for UNK-04 | UNK-04 |
| `scripts/eventbus/ack_route.py` | ACK and NACK pair authorization for UNK-02 | UNK-02 |
| `scripts/eventbus/replay_route.py` | Replay has no topic authorization (UNK-03) | UNK-03 |
| `config/eventbus.toml` | Shipped config: per-role tokens empty, stale comment (UNK-01) | UNK-01 |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | JSONL is already a secondary audit log; INV-02 locks best-effort append (UNK-04) | UNK-04 |
| `docs/10_adr/adr_01_index.md` | Invariant matrix rows that cite ADR-013 tests | REQ-004, UNK-05 |
| `docs/00_governance/governance_01_documentation-policy.md` | Defines which ADR edits reopen approval and the Pending Amendment Form | REQ-004, UNK-05, UNK-06 |
| `docs/24_eventbus/eventbus_09_publish_durability.md` | Existing explanation of `delivery: "replay"` | REQ-005 |
| `tests/eventbus/test_eventbus_config.py` | Holds the admin principal role test and the publisher-only and monitoring-only acceptance tests | REQ-001, UNK-01 |
| `tests/eventbus/test_eventbus_consumer_authorization.py` | Pins that one consumer token ACKs as every mapped consumer | UNK-02 |
| `tests/eventbus/test_admin_topics_authorization.py` | Existing admin endpoint tests cited by ADR-013 | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): `_build_principal_map` yields one `Principal` per distinct token; the `admin_token` principal holds exactly Operator, Monitoring, and Admin; `test_admin_token_grants_control_plane_roles_only` passes unchanged.
- AC-2 (REQ-002): `rg "get_auth_token" scripts tests` finds nothing; `resolve_principal` has no 500 path; an empty `auth_token` still fails at `EventBusConfig` construction.
- AC-3 (REQ-003): `rg "attach_auth_middleware" scripts/eventbus tests/eventbus registry/manifests/eventbus_api.yaml docs/24_eventbus` finds nothing; the ADR-013 mentions of the MCP function remain; `scripts/mcp_servers/server.py` references the new EventBus name; every EventBus response still carries `X-Request-Id`.
- AC-4 (REQ-004): ADR-013 Scope and Implementation References list the four files named in REQ-004; Implementation Notes states the TTL baseline behavior exactly as pinned by REQ-006; `tools/check_adr_preservation.py` reports no change to a Decision, Failure Policy, Invariant, Known Deviations, or Approval text; the decision-reference and formatting re-check outcome is recorded in the commit message.
- AC-5 (REQ-005): The DLQ semantics guide defines `delivery: "replay"` and points to the publish durability guide.
- AC-6 (REQ-006): The new tests pass against unchanged code; a test that exposes a defect stops the phase and is filed as an issue, not fixed here.
- AC-7 (REQ-007): `uv run python tools/generate_reference_table.py --check` exits 0.
- Not covered by this Plan: the issue's criteria for per-consumer token 403, a config without a required-role token failing load, and the Invariant-to-test mapping of `admin_route.py` and `authz_ttl.py`; each depends on an owner decision (UNK-01, UNK-02, UNK-05).

## Tests
- REQ-001: existing `test_admin_token_grants_control_plane_roles_only` and `tests/eventbus/test_eventbus_auth.py` guard the refactor; no new test, because behavior does not change.
- REQ-002: existing `test_load_config_rejects_empty_auth_token` guards the removal.
- REQ-003: existing `tests/eventbus/test_eventbus_auth.py` (rename in the fixture builder) and the X-Request-Id assertions.
- REQ-006: new characterization tests in `tests/eventbus/test_authz_generation_ttl.py`, written first and passing on unchanged code.
- REQ-004, REQ-005, REQ-007: documentation and generated artifacts, verified by the checkers in the Validation plan.

## Documentation Impact
Yes. ADR-013 (Scope, Implementation References, Implementation Notes, renamed symbol) driven by REQ-003 and REQ-004; the DLQ semantics guide driven by REQ-005; the generated EventBus reference block driven by REQ-007. Target docs are those named under the EventBus section of `docs/00_index.md` "Document References by Task". The JSONL role in ADR-006, the Invariants, and the Index matrix stay unchanged until UNK-04 and UNK-05 are decided.

## Assumptions
- The new middleware name `attach_request_id_middleware` is a judgment call; it describes the only behavior (X-Request-Id injection) and no symbol with that name exists in `scripts`, `tests`, `tools`, `docs`, or `registry`.
- Renaming a symbol inside ADR-013 Decision Details 1 is wording and reference maintenance and does not reopen approval (`docs/00_governance/governance_01_documentation-policy.md` states that wording, evidence, and reference edits do not reopen approval).
- Removing `get_auth_token` is safe because only `resolve_principal`, the generated reference table, and the manifest mention it; falsified if `rg get_auth_token` finds a caller at implementation time.
- Edits to `auth.py` in this Plan touch the `admin_token` block, `resolve_principal`, and the middleware function only; the adrchk017 hunks (`_fingerprint`, `hashlib` import) are disjoint, so landing order is not constrained.
- The ADR-013 TTL note describes only behavior that REQ-006 tests pin; if a test contradicts the draft note, the note follows the test.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | What "per-role token presence" the config must enforce at load. The issue labels it no-decision, but the `config.py` comment says "at least one per-role token ... when using role-based access control", the issue criterion says "a required role", the shipped `config/eventbus.toml` leaves every per-role token empty, and `test_eventbus_config.py` accepts publisher-only and monitoring-only deployments | An owner decision on which roles are required and when; whether an `auth_token`-only deployment is valid | Owner picks option O-A or O-B (Design); a follow-up Plan implements it and edits `config.py`, `config/eventbus.toml`, and tests | False |
| UNK-02 | Consumer identity: per-consumer tokens or a recorded accepted risk. Today one `consumer_token` acts as every mapped `consumer_id`, and `test_eventbus_consumer_authorization.py::TestPairwiseGrantsOverHttp` asserts that behavior | Owner decision; a config key design for per-consumer tokens | Owner picks from the D1 table; follow-up Plan (public config interface change) | False |
| UNK-03 | Role concentration in the shared `auth_token` and `admin_token`, and topic scope of `/replay` | Owner decision between splitting and recording the accepted risk | Owner picks from the D2 table; follow-up Plan | False |
| UNK-04 | Publish authorization: per-topic grants, `producer` from the principal, and the JSONL role. ADR-006 already calls JSONL a secondary audit log and INV-02 locks best-effort append by test | Owner decision; whether best-effort append stays | Owner picks from the D3 table; a JSONL change amends ADR-006 and needs an approval record | False |
| UNK-05 | New ADR-013 Invariants for generation compare-and-swap, the 409 conflict, the TTL bound, the expiry sweep, and the restart baseline, each with a test | Owner decision and an approval record; the Pending Amendment Form now exists | Owner approves wording; follow-up Plan adds Invariants, matrix rows, and tests | False |
| UNK-06 | Audit event separation. The issue calls it no-decision, but ADR-013 Decision Details 10 requires no audit record on a 409 and Decision Details 11 requires the `privileged_action` event type for authorization changes | An approval record for changing those Decision texts | Owner picks from the D4 table; follow-up Plan with the approval record in the same change | False |
| UNK-07 | Exact meaning of "a TTL grant loses its expiry when it returns to the baseline" | Which scenario the review meant | REQ-006 characterizes the candidate scenarios; document verified behavior; file a new issue if a defect shows | False |
| UNK-08 | The claim that ADR-013 Decision Details references do not match the list was not reproduced: every in-document reference resolves | The reviewer's concrete example | Re-run the check in Phase 4; fix only a reproduced mismatch and record the evidence | False |
| UNK-09 | Landing order against the EventBus task supervision issue (adrchk017) and the contract manifest sources issue (adrchk014) | Owner order decision | Sequencing only; the second change rebases onto the first | False |
| UNK-10 | The subscribe route authorization was not reviewed; `subscribe_route.py` and `route_helpers.py` exist at the assumed paths | A review of those files | Out of Scope per the issue; file a separate review issue if wanted | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/auth.py` | Modify | Medium: imported by every EventBus route module | 9 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `scripts/eventbus/app.py` | Modify | Low: one import and one call | 17 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_auth.py` | Modify | Low: fixture builder only | 15 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `scripts/mcp_servers/server.py` | Modify | Low: docstring only | 9 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_authz_generation_ttl.py` | Modify | Low: new tests only | 5 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Medium: cited by ADR checkers and the index | 14 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Modify | Low | 9 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `registry/manifests/eventbus_api.yaml` | Modify | Low: generated | 11 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify | Low: generated block | 25 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |

## Design
**Classification**: Path B (more than 3 files; a module-level function is renamed).

**Adversarial verification outcomes (Step 2)**

| Issue claim | Verdict | Evidence |
|---|---|---|
| One consumer token holds all mapped pairs, so it can ACK and NACK as another consumer | Confirmed | `_build_principal_map` grants the full pair set to the CONSUMER principal; `authorize_event_pair` checks only the pair; `TestPairwiseGrantsOverHttp` ACKs as both consumers with one token |
| Shared `auth_token` holds Operator, Monitoring, Admin; `/replay` has no topic check | Confirmed | `_CONTROL_PLANE_ROLES`; `replay_route.py` requires only the Operator role |
| Publish is open, `producer` comes from the body, JSONL failure is only logged | Confirmed | `publish_route.py` |
| ADR-006 does not say what the JSONL file is | Refuted in part | ADR-006 calls it a secondary audit log and not the primary store; INV-02 and a test lock best-effort append; `eventbus_06` still calls it a replica |
| Nothing validates the per-role token rule a config comment states | Confirmed, but the rule is undefined | See UNK-01 |
| `admin_token` principal is built twice | Confirmed | per-role loop entry is overwritten by the later block |
| The 500 branch cannot run | Confirmed | `EventBusConfig.__post_init__` rejects an empty `auth_token`, including through `dataclasses.replace`; no test reaches the branch |
| ADR-013 lacks Invariants for CAS, 409, TTL, sweep, restart baseline | Confirmed | Invariants stop at INV-07 |
| Scope and Implementation References omit `admin_route.py`, `authz_ttl.py`, `test_admin_topics_authorization.py` | Confirmed | Also missing: `test_authz_generation_ttl.py` |
| Decision Details references do not match the list | Not reproduced | UNK-08 |
| A TTL grant loses its expiry when it returns to the baseline | Ambiguous | UNK-07 |
| `delivery: "replay"` is undefined | Refuted in part | Defined in `eventbus_09_publish_durability.md`, absent from the DLQ semantics guide |
| Authorization changes, 409, and TTL removal cannot be told apart in the audit log | Narrowed | TTL removal carries `target="ttl_expiry"`; ADR-013 Decision Details 10 and 11 deliberately emit no 409 record and keep `privileged_action`; see UNK-06 |
| The EventBus `attach_auth_middleware` shares a name with the MCP function | Confirmed | Callers: `app.py`, one test, docs, manifest, one MCP docstring |

**Consumer scan (`tools/scan_change_consumers.py`)**: seeds `attach_auth_middleware`, `get_auth_token`, `_PER_ROLE_TOKEN_FIELDS`. The report is dominated by ADR test-citation noise; the direct consumers were enumerated with `rg` and are the target rows above. Every candidate is a target row, a reference row, or not affected: the MCP servers that call their own `attach_auth_middleware` are not affected (a different function in `scripts/mcp_servers/server.py`).

**Architecture**: `lint-imports` reports 6 contracts kept, 0 broken; the `eventbus` isolation contract is untouched. Persisted schema check: not applicable, no DDL or schema version change.

**Option tables for owner decisions (no behavior change in this Plan)**

D0 / UNK-01, per-role token rule:

| Option | Effect | Risk | Effort |
|---|---|---|---|
| O-A: require at least one per-role token at load | Matches the comment; rejects the shipped template unless it gains placeholders | A control-plane-only deployment stops starting | Low |
| O-B: no rule; delete the stale comment | Keeps every current deployment valid | Misconfiguration (no publisher, no consumer) surfaces only at runtime | Low |

D1 / UNK-02, consumer identity:

| Option | Effect | Risk | Effort |
|---|---|---|---|
| Per-consumer tokens (recommended by the issue) | One token binds one `consumer_id`; new config key; INV-02 holds literally | Public config change; rewrites `TestPairwiseGrantsOverHttp` | High |
| Record accepted risk | Amend INV-02 wording and Ongoing Risks (the current risk bullet is also inconsistent with Decision Details 6) | One leaked consumer token acts as every consumer | Low |

D2 / UNK-03, role concentration:

| Option | Effect | Risk | Effort |
|---|---|---|---|
| Split `auth_token` into per-role credentials | Least privilege; replay gets topic scope | Breaking config change | Medium |
| Record accepted risk in ADR-013 | Documents the single-operator model | One leaked token replays all topics and rewrites authorization | Low |

D3 / UNK-04, publish and JSONL:

| Option | Effect | Risk | Effort |
|---|---|---|---|
| Per-topic publisher grants, `producer` from the principal | Closes forgery and open publish | New config; amends ADR-013 and clients | High |
| Keep open publish; align the JSONL wording only | Terminology fix across ADR-006 and `eventbus_06` | Forged `producer` remains | Low |
| Make the JSONL append fail the publish | Canonical file | Breaks ADR-006 INV-02 and its test | High |

D4 / UNK-06, audit separation:

| Option | Effect | Risk | Effort |
|---|---|---|---|
| Keep current records; document the vocabulary in `audit.py` | No ADR text change | Event name stays shared with other privileged actions | Low |
| New event names for change, conflict, and expiry | Separable records | Amends Decision Details 10 and 11, needs an approval record, breaks log consumers that filter `privileged_action` | Medium |

**Validation quality baseline (Step 5)**: `radon cc` grade C or worse: `_build_principal_map` C(15), `EventBusConfig.__post_init__` D(23), `update_topics_authorization` D(22), none touched beyond REQ-001; `vulture` at confidence 80 reports nothing for `scripts/eventbus`; `bandit` reports no medium or high severity finding; the diff-cover baseline is N/A because the clean tree has no diff against master, and the 90 percent threshold of `rules/toolchain.md` applies after implementation.

## Implementation steps
1. **Phase 1: Principal build and dead branch** (release unit with Phases 2 and 5)
   - [ ] Re-run the Acceptance Criteria searches and `uv run pytest tests/eventbus -q` for a green baseline (REQ-001; `scripts/eventbus/auth.py`)
   - [ ] Remove `admin_token` from `_PER_ROLE_TOKEN_FIELDS` so the control-plane block is its only build (REQ-001; `scripts/eventbus/auth.py`)
   - [ ] Remove the 500 branch in `resolve_principal` and `get_auth_token` (REQ-002; `scripts/eventbus/auth.py`)
2. **Phase 2: Middleware rename**
   - [ ] Rename to `attach_request_id_middleware` and update the import and call (REQ-003; `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`)
   - [ ] Update the test import and call, and the MCP docstring cross-reference (REQ-003; `tests/eventbus/test_eventbus_auth.py`, `scripts/mcp_servers/server.py`)
3. **Phase 3: TTL characterization tests**
   - [ ] Write tests that pin the behaviors in REQ-006 against unchanged code; stop and file an issue if one exposes a defect (REQ-006; `tests/eventbus/test_authz_generation_ttl.py`)
4. **Phase 4: Documentation**
   - [ ] ADR-013: rename the EventBus function in three places, extend Scope and Implementation References, add the TTL baseline note to Implementation Notes, re-check decision references (REQ-003, REQ-004; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
   - [ ] Define `delivery: "replay"` (REQ-005; `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`)
5. **Phase 5: Regenerate derived artifacts** (release unit with Phases 1 and 2)
   - [ ] Run `uv run python tools/generate_reference_table.py --manifests`, then `--check` (REQ-007; `registry/manifests/eventbus_api.yaml`, `docs/24_eventbus/eventbus_08_reference_api.md`)
6. **Phase 6: Deployment & Verification**
   - [ ] Run the Validation plan commands, commit and push, then hand off to `skills/deploy/SKILL.md`; deploying is the user's decision and requires the change to be committed and pushed first (REQ-001, REQ-002, REQ-003; `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/mcp_servers/server.py`)

### Release units
**Unit**: eventbus-api-surface | **Phases**: 1, 2, 5 | **Reason**: Phases 1 and 2 change the public symbol set of `scripts/eventbus`, so `generate_reference_table.py --check` and the CI lint job fail on manifest drift until Phase 5 regenerates the manifest and the reference block.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/mcp_servers/server.py` | Unit and integration | `uv run ruff format --check` and `uv run ruff check` on the changed files; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `PYTHONPATH=scripts uv run lint-imports` | No findings; 6 contracts kept |
| `tests/eventbus/` | Unit and integration | `uv run pytest tests/eventbus -v`; `uv run pytest tests/mcp_servers/test_mcp_server_base.py -v` | All pass |
| Diff-scoped coverage | Coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent on changed lines |
| Generated artifacts | Drift check | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| ADR-013 and the DLQ guide | Documentation | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain eventbus`, `check_docs_japanese.py`, `check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_reference.py` (all `uv run python tools/...`) | No findings beyond the expected additive Implementation References change |
| ADR-cited tests | Integration | `uv run python .github/run_cited_adr_tests.py` | Pass |
| Work items | Structure | `uv run python tools/check_workitem_structure.py --file <plan>` | No findings |

## Risks
- **Risk**: The rename misses a caller outside the searched paths → **Mitigation**: the consumer scan plus `rg` over `scripts`, `tests`, `tools`, `docs`, `registry`, and `.importlinter`; a failing import fails the test suite.
- **Risk**: Dropping `admin_token` from the per-role loop changes a principal's roles → **Mitigation**: `test_admin_token_grants_control_plane_roles_only` and the no-bypass tests run unchanged; the dedicated block already overwrote the loop entry.
- **Risk**: The ADR-013 edit trips `check_adr_preservation.py` because Implementation References change → **Mitigation**: the change is additive and carries no Decision text; if the tool reports an ERROR, record it as the expected finding and confirm no Decision, Invariant, Known Deviations, or Approval text moved.
- **Risk**: Characterization tests expose a real TTL defect → **Mitigation**: Phase 3 stops and files an issue; this Plan does not change authorization behavior.
- **Risk**: Edits to `auth.py` and ADR-013 collide with adrchk017 or adrchk014 → **Mitigation**: disjoint hunks, sequencing-only; the later change rebases (UNK-09).
- **Risk**: The blast radius of removing `get_auth_token` is larger than measured → **Mitigation**: `rg -l 'get_auth_token' tests/` currently matches no test file; re-run before editing.
- **Risk**: The decision-gated findings stay unaddressed and the security gaps persist → **Mitigation**: UNK-01 to UNK-06 each carry an option table and a follow-up path; none blocks this Plan, and the final report lists them for the owner.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Principal build once and dead 500 branch removal | Pending | — | — | |
| 2 | Middleware rename and callers | Pending | — | — | |
| 3 | TTL characterization tests | Pending | — | — | |
| 4 | ADR-013 and DLQ guide documentation | Pending | — | — | |
| 5 | Regenerate manifest and reference block | Pending | — | — | |
| 6 | Validation, commit, and deploy hand-off | Pending | — | — | |

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
- **Source issue**: issues/20261117-123002_adrchk002_eventbus-authz-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-092411
- **Related target files**: `scripts/eventbus/auth.py`; `scripts/eventbus/app.py`; `tests/eventbus/test_eventbus_auth.py`; `scripts/mcp_servers/server.py`; `tests/eventbus/test_authz_generation_ttl.py`; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`; `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`; `registry/manifests/eventbus_api.yaml`; `docs/24_eventbus/eventbus_08_reference_api.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Reason for Change (roles); Required Changes (build each principal once) | `scripts/eventbus/auth.py` | Phase 1 | AC-1 | `test_admin_token_grants_control_plane_roles_only`; `tests/eventbus/test_eventbus_auth.py` | Confirmed by repository evidence |
| REQ-002 | Reason for Change (unreachable 500 branch); Required Changes | `scripts/eventbus/auth.py` | Phase 1 | AC-2 | `test_load_config_rejects_empty_auth_token`; ruff, mypy, vulture | Confirmed by repository evidence |
| REQ-002 | Derived: `get_auth_token` has no other caller | `registry/manifests/eventbus_api.yaml` | Phase 5 | AC-7 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-002 | Derived: `get_auth_token` appears in the generated block | `docs/24_eventbus/eventbus_08_reference_api.md` | Phase 5 | AC-7 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-003 | Reason for Change (audit); Required Changes (rename middleware) | `scripts/eventbus/auth.py` | Phase 2 | AC-3 | `tests/eventbus/test_eventbus_auth.py`; mypy | Confirmed by repository evidence |
| REQ-003 | Required Changes (update callers) | `scripts/eventbus/app.py` | Phase 2 | AC-3 | `tests/eventbus/test_eventbus_startup.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes (update tests) | `tests/eventbus/test_eventbus_auth.py` | Phase 2 | AC-3 | `uv run pytest tests/eventbus/test_eventbus_auth.py` | Confirmed by repository evidence |
| REQ-003 | Derived: the MCP docstring names the EventBus function | `scripts/mcp_servers/server.py` | Phase 2 | AC-3 | `tests/mcp_servers/test_mcp_server_base.py`; ruff | Derived from confirmed evidence |
| REQ-003 | Required Changes (decision references); Constraints (check docs callers) | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Phase 4 | AC-3 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-003 | Derived: the manifest holds the old name | `registry/manifests/eventbus_api.yaml` | Phase 5 | AC-7 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-003 | Derived: the generated block holds the old name | `docs/24_eventbus/eventbus_08_reference_api.md` | Phase 5 | AC-7 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-004 | Reason for Change (ADR-013 incomplete); Required Changes (Scope, References, TTL baseline) | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Phase 4 | AC-4 | `check_adr_preservation.py`; `check_adr_structure.py`; `check_docs_structure.py` | Confirmed by repository evidence |
| REQ-005 | Reason for Change (`delivery: "replay"` undefined); Required Changes | `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Phase 4 | AC-5 | `check_docs_quality.py`; `check_docs_content_policy.py --strict` | Confirmed by repository evidence |
| REQ-006 | Required Changes (document the TTL baseline behavior); Testing Expectations | `tests/eventbus/test_authz_generation_ttl.py` | Phase 3 | AC-6 | `uv run pytest tests/eventbus/test_authz_generation_ttl.py` | Needs confirmation |
| REQ-007 | Constraints (regenerate generated files, do not hand-edit) | `registry/manifests/eventbus_api.yaml` | Phase 5 | AC-7 | `generate_reference_table.py --check` | Explicit in issue |
| REQ-007 | Constraints (regenerate guarded blocks) | `docs/24_eventbus/eventbus_08_reference_api.md` | Phase 5 | AC-7 | `generate_reference_table.py --check` | Explicit in issue |

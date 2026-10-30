# Implementation Procedure: `tests/eventbus/test_admin_topics_authorization.py` (EBAUTHGEN001 Phase 1)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-002, REQ-003, REQ-004, REQ-005, REQ-007)

## Goal
Extend the admin-endpoint suite with the stale-rejection matrix, the additive response
contract, TTL validation, no-op + expected-generation ordering, and audit generation
fields.

## Scope
- `admin_client` fixture `:17-54` (distinct `admin-tok`/`consumer-tok`,
  `consumer_authorization={"c1": ["topicA"]}`, production lifespan).
- `TestAdminGating` `:57` (`test_empty_body_rejected` `:81-88`,
  `test_response_includes_persistent_and_changed` `:90-103`, no-op `changed=false` `:105-122`).
- Anchor drift note: plan cites `:170-186`, `:209`, `:274-295`, `:297-310` verified at
  freeze HEAD `c5a8285dd` (474 lines); after `474dc2888` the file is 409 lines and the
  landed tests are `test_update_reflected_...` `:165-179`, `TestValidation` `:182-205`,
  `TestPublishOrder` `:208-269` (incl. `test_failed_principal_build_keeps_previous_generation`
  `:209-230`, `test_noop_update_publishes_nothing` `:232-247`,
  `test_effective_update_publishes_config_and_map` `:249-269`), `TestUpdateRemovesPairs`
  `:272-291`. These landed tests are the extension points.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
### New / extended tests
1. Stale-rejection matrix (AC-1): two updates with the same `expected_generation` -> one
   200, one 409 `generation_conflict`; rejected request leaves config, principals, and
   audit byte-identical (compare via `eventbus_helpers` generation accessor + a
   `log_privileged_action` patch like `:154`).
2. Missing / non-integer `expected_generation` -> 422 (extends `TestAdminGating`).
3. No-op + ordering (REQ-007): stale `expected_generation` on an otherwise no-op body
   still returns 409 before change detection.
4. Response contract (REQ-003, AC-6): successful update carries `previous_generation`,
   `new_generation`, `changed_count`, `effective_at`, `baseline_hash` alongside
   `status`/`persistent`/`changed`; no-op carries `changed_count: 0` with
   `previous_generation == new_generation`.
5. TTL validation (REQ-005): `ttl_seconds` 0/negative/above `authz_max_ttl_seconds` /
   non-numeric -> 422 with zero state change; valid TTL grant accepted.
6. Audit generation fields (REQ-004): patch `eventbus.admin_route.log_privileged_action`,
   assert `previous_generation`/`new_generation` kwargs on effective change and absence
   on no-op.
7. Extend `test_failed_principal_build_keeps_previous_generation` `:209-230` to also
   assert the generation number and hash are unchanged after the failed rebuild (AC-3).
8. Adapt `TestOneRolePerTokenAdminRebuild` snapshot/restore helpers (`:298-309`, currently
   reach into `auth._TOKEN_PRINCIPAL_MAP`) to the generation accessor from doc 11 —
   required because doc 01 removes the bare map.

## Compatibility considerations
**Dependencies**:
- Upstream: docs 01-03 (generation core + admin contract), doc 11 (shared helpers)
**Blocks**: none

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert or remove the added test rows; no production change to unwind.

## Validation plan
- `uv run pytest tests/eventbus/test_admin_topics_authorization.py` (row gate);
  `uv run pytest tests/eventbus` at Phase 4.

## Completion criteria
- AC-1/AC-3/AC-6 regression-locked; every plan Tests bullet `:126`, `:130` mapped to a
  named test here.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-141000_01_scripts_eventbus_auth.py.md` | 1 (dependency) | Procedure | Pending | — | — |
| `20261030-141000_11_tests_eventbus_eventbus_helpers.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- No production constructs introduced by this row; helpers referenced come from doc 11's
  `reset_generation_state` (new) and `current_generation` (new, doc 01). No `(new)`
  markers applied in this document beyond those named references.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-003, REQ-004, REQ-005, REQ-007
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 08
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `tests/eventbus/test_admin_topics_authorization.py`

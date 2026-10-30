# Implementation Procedure: `scripts/eventbus/admin_route.py` (EBAUTHGEN001 Phase 1-2)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-002, REQ-003, REQ-004, REQ-005, REQ-007; Design `:168-171`)

## Goal
Require `expected_generation` on `POST /admin/topics/authorization`, extend the response
additively, accept/validate `ttl_seconds`, and extend the audit call with generation
fields — all rejections before any state change.

## Scope
- `update_topics_authorization(request, principal)` `:79-164`.
- Body parse `:92`; empty-body 422 `:95-99`; per-key validation `:101-111`
  (`_validate_consumer_authorization` `:17-43`, `_validate_topic_authorization` `:51-76`).
- No-op diff `:120-136` (`_changed_count` `:46-48`).
- Build-first publish block `:137-147`: `dataclasses.replace` `:144`,
  `_build_principal_map` `:145`, `request.app.state.config = config` `:146`,
  `publish_principals(new_principals)` `:147`.
- Audit block `:152-162`: `detail` = `name:count;...;persistent:false` `:153-154`,
  `log_privileged_action(consumer_id="admin", request_id=request.state.request_id,
  route="/admin/topics/authorization", target="topics_authorization", actor=principal.token_fingerprint)` `:155-162`.
- Return `{"status": "ok", "persistent": False, "changed": changed}` `:164`.
- Route registration lives in `scripts/eventbus/app.py:304-305` (row 05) — path and
  ADMIN gating unchanged.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- Request body gains: `expected_generation` (int, mandatory) and `ttl_seconds`
  (int|float, optional). Missing or non-integer `expected_generation` -> 422
  (Assumption `:138`: deliberate admin-API break, owner-approved).
- Order: body validation -> `expected_generation == current_generation().generation`
  check BEFORE the diff (`:120`) -> TTL validation -> diff/publish. A stale expected
  generation on a would-be no-op is still rejected (REQ-007; AC-1).
- Mismatch -> HTTP 409 `JSONResponse` `{"error": "generation_conflict",
  "expected_generation": <n>, "current_generation": <m>}` (new error shape); zero state
  touch, zero audit (REQ-002).
- `ttl_seconds` valid range: `0 < ttl_seconds <= cfg.authz_max_ttl_seconds`; out-of-range
  or non-numeric -> 422 before any change (REQ-005). Applies only to pairs newly present
  in the new config (`ttl` records `effective_at + ttl_seconds`); existing unchanged
  pairs keep their expiry entries untouched; removed pairs drop their expiry entries.
- Publish block `:137-147` evolves to: build replacement config -> build principals via
  `_build_principal_map` -> compute new `baseline_hash` -> compose `AuthzGeneration(
  generation=current+1, ...)` -> `request.app.state.config = new_gen.config` ->
  `publish_generation(new_gen)` (same build-first-then-single-swap order, REQ-009).
- Response `:164` extends additively (REQ-003): `previous_generation`, `new_generation`,
  `changed_count` (sum of `counts` values), `effective_at`, `baseline_hash`;
  `status`/`persistent`/`changed` semantics unchanged (AC-6). On no-op:
  `previous_generation == new_generation == current`, `changed_count: 0`, current hash
  and effective time.
- Audit call `:155-162` gains `previous_generation=`/`new_generation=` keyword arguments
  (doc 06 signature) and appends `gen:<prev>-><new>` to `detail` (Design `:170`); the
  landed identity fields and count-summary format are preserved verbatim.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Parse/validate `expected_generation` and `ttl_seconds` in `:92-111` region.
2. Insert the generation precondition between validation and diff (before `:120`).
3. Extend the publish block `:137-147` per the contract above.
4. Extend the audit block `:152-162` and the return `:164`.

## Compatibility considerations
**Dependencies**:
- Upstream: doc 01 (`current_generation()`, `publish_generation`, `AuthzGeneration`),
**Blocks**: docs 08, 13, 14, 15 (contract consumers)

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/eventbus/test_admin_topics_authorization.py` (row 08 owns the
  rejection matrix, response contract, TTL validation, no-op ordering).

## Completion criteria
- AC-1: one of two same-expected-generation updates succeeds, the other gets 409 with
  byte-identical state/principals/audit; AC-6: existing no-op response semantics hold.

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

## Marker record
- `(new)` markers applied: the 409 `generation_conflict` response shape (Contract
  section); `expected_generation`, `ttl_seconds` request fields; `previous_generation`,
  `new_generation`, `changed_count`, `effective_at`, `baseline_hash` response fields.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-003, REQ-004, REQ-005, REQ-007
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 03
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `scripts/eventbus/admin_route.py`

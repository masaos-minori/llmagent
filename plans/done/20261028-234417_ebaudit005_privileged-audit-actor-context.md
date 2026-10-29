# Plan: record request id and authenticated actor in privileged-action audit records (ebaudit005)

## Goal
- Make every privileged-action audit record (admin topics authorization, DLQ requeue, replay) carry
  the originating `request_id` and the acting principal's `token_fingerprint`, replace the
  always-empty `error_type` on successful records (UNK-01 resolved 2026-10-29: keep the current
  `error_type=""` shape; the module docstring documents `""` as the success convention), and give the
  authorization-update record a non-sensitive scope-change summary plus `persistent=false` --
  without logging raw credentials and without renaming existing fields.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/eventbus/audit.py`: additive `actor` field (fingerprint) in `log_privileged_action`
    records; success `error_type` keeps its current `""` shape (UNK-01 resolved 2026-10-29; only a
    module-docstring clarification records the convention).
  - `scripts/eventbus/app.py` route wrappers passing the already-resolved `Principal` into the
    admin/DLQ/replay route functions; the three route modules passing `request_id` and fingerprint
    to `log_privileged_action`; admin record gains a scope summary and `persistent=false`.
  - Unit tests on record shape (`tests/eventbus/test_eventbus_audit.py`, new file) and route audit
    assertions in `tests/eventbus/test_admin_topics_authorization.py`,
    `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_replay_pagination.py`.
  - `docs/24_eventbus/eventbus_08_reference_api.md` audit signature rows updated to the final
    signatures.
- **Out-of-Scope**: `log_auth_failure` records; audit log storage/rotation/shipping; authorization
  model changes; configured token labels as an actor identity (UNK-02 resolved 2026-10-29:
  `token_fingerprint` only is approved; a label variant would be a follow-up issue).
- **Dependencies**: The auth Plan `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md`
  is archived and its procedure `implementations/20261028-114911_04_scripts_eventbus_app.py.md`
  (ACK/NACK wiring in `scripts/eventbus/app.py`) is implemented (`implementations/` top level is
  empty); this Plan edits the admin/DLQ/replay wrappers, a different region of the same file --
  plain rebase caution. Same-batch file overlap: `tests/eventbus/test_eventbus_dlq.py` is also a
  target of `plans/20261028-231610_ebdlqrecon002_rebuild-missing-dlq-files.md` (distinct tests;
  coordinate implementation order); `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`
  lists this file only in its terminology audit report, not as a target row, and edits only a new
  fixture-mapping section of `docs/24_eventbus/eventbus_08_reference_api.md` (this Plan edits the
  audit signature rows -- different sections of the same doc).

## Background
`log_privileged_action()` (`scripts/eventbus/audit.py:129-135`) builds records through
`_build_audit_record` (line 60) whose `error_type` parameter defaults to `""`; no privileged caller
passes one, so every privileged record carries `error_type=""` although the module docstring
(line 12) defines `error_type` as a failure-mode identifier and `AuditRecord.error_type` (line 56)
is a required `str`. `admin_route.py:141-147` passes `consumer_id="admin"`, `request_id=""` (the
handler has the `Request` but does not read `request.state.request_id`) and `detail="updated"`,
which says nothing about what changed. `dlq_route.py:70` and `replay_route.py:38-44` pass
`consumer_id=""` (rendered `-`) with the real request id. No caller records which credential acted,
although `Principal.token_fingerprint` exists for exactly this purpose (`auth.py:41`, "non-secret
identifier for audit logging"; derived at `:97/:158/:193/:202`) and the app wrappers already resolve
the principal via `Depends(require_role(...))` (`app.py`, `_principal` currently unused on the
admin/DLQ/replay routes). Only the admin path has audit tests
(`test_admin_topics_authorization.py:187`/`:203`, re-verified 2026-10-29), and they assert call
count and redaction only.

## Problem
A privileged action cannot be tied to the request that caused it (admin updates) or to the
credential that performed it (all three actions), and successful records carry an always-empty
failure field; an investigator cannot answer "which token changed the authorization mapping".

## Reason for Change
These are the highest-privilege operations on the bus and their audit trail is the only record of
who did them. No incident cited; Medium (security-relevant observability gap, no demonstrated
misuse); not time-sensitive.

## Implementation Intent
Keep the change additive and limited to audit fields: add an actor parameter to
`log_privileged_action` and emit it as a new `actor` key; pass the wrapper-resolved principal and
the real request id at the three call sites; replace the admin `detail="updated"` with a
counts-and-mappings summary and record `persistent=false`; the success `error_type` shape stays
`""` (UNK-01 resolved 2026-10-29). Never log raw tokens; keep one JSON line per record and all
existing field names. If plumbing the principal into a route requires changes beyond the wrappers,
stop and report.

## Requirements
- `REQ-001`: the admin topics-authorization audit record carries `request.state.request_id`
  (non-empty).
- `REQ-002`: all three privileged-action records carry the acting principal's
  `token_fingerprint` as a new `actor` field; no raw token value appears in any emitted record.
- `REQ-003`: the success `error_type` shape stays exactly as today (`error_type=""` present in every
  privileged record; UNK-01 resolved 2026-10-29: owner chose to keep the current behavior); the
  module docstring documents `""` as the documented success value and `AuditRecord` typing is
  unchanged.
- `REQ-004`: the authorization-update record states what changed without secrets: which mappings
  changed and their counts, plus `persistent=false`; the no-op case still emits no record.
- `REQ-005`: tests assert the new fields for all three actions (admin update, DLQ requeue, replay),
  including a captured-log check that no token string appears.
- `REQ-006`: the EventBus API reference doc's audit rows match the final signatures and record
  shape (current behavior only).
- `REQ-007`: cross-cutting constraint: existing field names, one-JSON-line shape and current
  redaction behavior are preserved (additive change).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 2026-10-29: all target rows Verified; `tools/check_workitem_structure.py` clean; `tools/check_plan_target_overlaps.py` findings reviewed as documented sequencing dependencies; corrected 2026-10-29 after source re-verification: call-site line ranges, wrapper ranges, no-redaction-helper finding, UNK-01/UNK-02 owner decisions).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/eventbus/audit.py | Add `actor` parameter/field to `log_privileged_action`; document the success `error_type=""` convention in the module docstring (no shape change, UNK-01 resolved) | Records lack an actor and carry `error_type=""` on success | REQ-002, REQ-003, REQ-007; AC-1, AC-2 | `audit.py:129-135` signature; `_build_audit_record` `error_type=""` default (lines 67, 91); `AuditRecord.error_type: str` (line 56); module docstring line 12 | tests/eventbus/test_eventbus_audit.py (new) | Verified |
| scripts/eventbus/app.py | Pass the resolved `Principal` from admin/DLQ/replay wrappers into their route functions | Wrappers already resolve `_principal` but the route functions never see it | REQ-002; AC-1 | `app.py` wrappers `_principal: Principal = Depends(require_role(...))`: replay wrapper `:201-211` (`_principal` at `:208`), `dlq_requeue` wrapper `:253-260` (`_principal` at `:254`), admin wrapper `:303-310` (`_principal` at `:304`); ack/nack wrappers already pass `_principal` (ebauth001 region, disjoint) (re-verified 2026-10-29) | Route audit tests below | Verified |
| scripts/eventbus/admin_route.py | Pass `request.state.request_id` + fingerprint; `detail` becomes a mappings/counts summary; record `persistent=false` | Emits `request_id=""` and `detail="updated"` | REQ-001, REQ-002, REQ-004; AC-1, AC-3 | `admin_route.py:141-147` call site; response `persistent: False` at line 149 | tests/eventbus/test_admin_topics_authorization.py | Verified |
| scripts/eventbus/dlq_route.py | Pass the acting principal's fingerprint (wrapper-supplied) into the requeue audit call | Requeue record has no actor | REQ-002; AC-1 | `dlq_route.py:70` call site (`consumer_id=""` rendered `-`) | tests/eventbus/test_eventbus_dlq.py new audit assertions | Verified |
| scripts/eventbus/replay_route.py | Pass the acting principal's fingerprint (wrapper-supplied) into the replay audit call | Replay record has no actor | REQ-002; AC-1 | `replay_route.py:38-44` call site | tests/eventbus/test_eventbus_replay_pagination.py new audit assertions | Verified |
| tests/eventbus/test_eventbus_audit.py | New file: field-shape unit tests for `_build_audit_record`/`log_privileged_action` | No direct record-shape tests exist today | REQ-003, REQ-005, REQ-007; AC-2 | grep 2026-10-28: no existing audit-module unit tests | The new tests themselves | Verified |
| tests/eventbus/test_admin_topics_authorization.py | Extend the two existing audit tests to assert request id, actor and scope summary | Existing tests assert call count/redaction only | REQ-001, REQ-004, REQ-005; AC-1, AC-3 | `test_admin_topics_authorization.py:188-213` mock-based audit tests | Updated tests | Verified |
| tests/eventbus/test_eventbus_dlq.py | Add requeue audit assertions (patch `eventbus.dlq_route.log_privileged_action`) | No DLQ audit-field test exists | REQ-002, REQ-005; AC-1, AC-4 | grep 2026-10-28: no `log_privileged_action` assertions in this file | New assertions | Verified |
| tests/eventbus/test_eventbus_replay_pagination.py | Add replay audit assertions on `GET /replay` (patch `eventbus.replay_route.log_privileged_action`) | No replay audit-field test exists | REQ-002, REQ-005; AC-1, AC-4 | File already drives `GET /replay?format=json` (line 54); audit call at `replay_route.py:38` | New assertions | Verified |
| docs/24_eventbus/eventbus_08_reference_api.md | Update `AuditRecord` and `log_privileged_action` signature rows after the code lands | Doc rows would go stale against the new signature/typing | REQ-006 | `eventbus_08_reference_api.md:64-66` audit rows | `tools/check_docs_consistency.py --domain eventbus` | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/auth.py | `Principal.token_fingerprint` definition and derivation (never log the raw token) | REQ-002 |
| scripts/eventbus/dlq.py | DLQ requeue/promotion paths the requeue route delegates to | REQ-002 |
| docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md | Contains narrative audit mentions to confirm they stay true (no edit expected) | REQ-006 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002): every privileged-action record contains a non-empty `request_id` and an
  actor fingerprint, and no raw credential.
- AC-2 (REQ-003): a successful record keeps `error_type=""` exactly as today, and the module
  docstring documents `""` as the success convention (UNK-01 resolved 2026-10-29).
- AC-3 (REQ-004): the authorization update record states what changed without listing secrets and
  records `persistent=false`.
- AC-4 (REQ-005): tests assert the new fields for the admin update, DLQ requeue and replay, and a
  captured-log check shows no token value.
- AC-5 (REQ-006): `eventbus_08_reference_api.md` audit rows match the final code;
  `check_docs_consistency.py --domain eventbus` passes.

## Tests
- REQ-003/REQ-007: unit tests in `tests/eventbus/test_eventbus_audit.py` -- new key present, all
  existing keys unchanged, one JSON line, `detail` never empty, success `error_type` keeps `""`;
  at least one caplog-based test asserting the emitted line contains no token substring.
- REQ-001/REQ-004: extend `test_audit_emitted_on_effective_change` and `test_audit_not_emitted_on_noop`
  in `tests/eventbus/test_admin_topics_authorization.py` (request id non-empty, actor == admin
  principal fingerprint, detail names changed mappings + counts, `persistent=false` recorded).
- REQ-002: requeue audit assertions in `tests/eventbus/test_eventbus_dlq.py`; replay audit
  assertions in `tests/eventbus/test_eventbus_replay_pagination.py`; for each action the captured
  record contains the request's `request_id` and the acting principal's fingerprint.
- Gates: `uv run pytest tests/eventbus`; ruff and mypy on changed files;
  `tools/check_docs_consistency.py --domain eventbus`.

## Documentation Impact
Yes, small: the EventBus API reference doc named in `docs/00_index.md`'s task mapping for the
EventBus reference API (`docs/24_eventbus/eventbus_08_reference_api.md`) audit rows describe the
final record fields and signatures (operational notes, current behavior only). No other EventBus doc
describes these record fields (grep verified 2026-10-28).

## Assumptions
- `request.state.request_id` is populated by middleware for all three privileged routes (verified
  at the dlq/replay call sites; the admin handler already receives the `Request`, so the same state
  is available).
- `token_fingerprint` is precomputed at Principal construction, so emitting it adds no per-request
  hashing cost.
- Log parsers ignore unknown JSON keys, so the additive `actor` key is safe without owner approval;
  the UNK-01 resolution (2026-10-29) removes the only parser-breaking candidate by keeping the
  `error_type` shape unchanged.
- Phase 1+2 (additive fields) can ship before the UNK-01 answer; only the error_type edit is gated.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | ~~Should `error_type` be omitted on success or carry a fixed non-empty value (e.g. `none`)?~~ RESOLVED 2026-10-29: owner chose to keep the current behavior (`error_type=""` present in every privileged record); no shape change, no parser impact. Module docstring documents `""` as the success value. | None -- owner decision obtained 2026-10-29 | Closed | False |
| UNK-02 | ~~Is `token_fingerprint` an acceptable actor identifier for operators, or is a configured token label wanted?~~ RESOLVED 2026-10-29: owner approved `token_fingerprint` only. A label variant would be a follow-up issue. | None -- owner decision obtained 2026-10-29 | Closed | False |
| UNK-03 | Exact scope-summary `detail` format (which mappings + counts) that satisfies the current redaction vocabulary | No existing multi-mapping audit detail precedent | Fixed during procedure writing with a redaction review; Phase 2 tests pin it | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/eventbus/audit.py | Additive actor field; `error_type` shape unchanged (docstring note only) | Audit log consumers | 0 | 1 | Yes: deployed; audit logger restart required |
| scripts/eventbus/app.py | Wrapper wiring passes Principal (region distinct from ebauth001 edits) | Route wiring | 8 | 2 | Yes: deployed; service restart required |
| scripts/eventbus/admin_route.py | Request id + scope summary in audit call | Admin route | 1 | 1 | Yes: deployed; service restart required |
| scripts/eventbus/dlq_route.py | Actor in requeue audit call | DLQ route | 2 | 2 | Yes: deployed; service restart required |
| scripts/eventbus/replay_route.py | Actor in replay audit call | Replay route | 0 | 2 | Yes: deployed; service restart required |
| tests/eventbus/test_eventbus_audit.py | New test file | Tests only | 0 | 0 (new file) | N/A: test file is not deployed |
| tests/eventbus/test_admin_topics_authorization.py | Extended audit assertions | Tests only | 7 | 2 | N/A: test file is not deployed |
| tests/eventbus/test_eventbus_dlq.py | New audit assertions (coordinate with ebdlqrecon002 row) | Tests only | 11 | 2 | N/A: test file is not deployed |
| tests/eventbus/test_eventbus_replay_pagination.py | New audit assertions | Tests only | 3 | 2 | N/A: test file is not deployed |
| docs/24_eventbus/eventbus_08_reference_api.md | Signature rows update | Docs only | 18 | 2 | N/A: docs are deployed read-only if changed |

## Design
- Call-site plumbing: wrappers keep `Depends(require_role(...))` and pass the resolved `Principal`
  as an explicit argument to `update_topics_authorization_route`, `dlq_requeue` and the replay
  handler -- signature additions inside the already-resolved wrapper chain; verified 2026-10-28 that
  no middleware change is needed, so the issue's stop-and-report trigger does not apply.
- `log_privileged_action(consumer_id, request_id, route, target, detail="", actor="")`:
  `actor` is emitted as a new record key; empty actor is rejected by an assertion in tests (AC-1
  requires non-empty for all privileged calls).
- `error_type` (UNK-01 resolved 2026-10-29): keep the current shape -- every privileged record
  carries `error_type: str` with value `""` (`AuditRecord` typing and `_build_audit_record` unchanged);
  only the module docstring gains an explicit "`\"\"` on success" note. Failure records
  (`log_auth_failure` keep their vocabulary) are untouched.
- Admin scope summary: built from the same `changed` computation the route already has
  (`admin_route.py`); content is mapping keys + counts only. There are no existing redaction helper
  functions in `scripts/eventbus/` (grep 2026-10-29), so sanitization is structural: consumer ids and
  topic names are already non-secret config values and the summary carries counts of changed
  mappings; no token or grant-set dump; `persistent` recorded as part of the record (key or detail
  -- decided at procedure level, UNK-03's format note covers both).
- Phasing: additive Phases 1-2 ship independently; Phase 3 carries the docstring note, route tests
  and doc rows (no gated decision remains after UNK-01 resolved 2026-10-29).

## Implementation steps
1. **Phase 1: Audit record shape (additive)**
   - [ ] Add the `actor` parameter and emitted `actor` key in `scripts/eventbus/audit.py` (REQ-002, REQ-007; scripts/eventbus/audit.py)
   - [ ] Add `tests/eventbus/test_eventbus_audit.py` field-shape unit tests (REQ-003 partial -- shape tests without the error_type decision, REQ-005, REQ-007; tests/eventbus/test_eventbus_audit.py)
2. **Phase 2: Callers carry actor and request context**
   - [ ] Pass the resolved `Principal` from the admin/DLQ/replay wrappers in `scripts/eventbus/app.py` into their route functions (REQ-002; scripts/eventbus/app.py)
   - [ ] Update `scripts/eventbus/admin_route.py` to pass the real request id, the fingerprint, a mappings/counts `detail` and `persistent=false` (REQ-001, REQ-002, REQ-004; scripts/eventbus/admin_route.py)
   - [ ] Update `scripts/eventbus/dlq_route.py` and `scripts/eventbus/replay_route.py` call sites with the fingerprint (REQ-002; scripts/eventbus/dlq_route.py, scripts/eventbus/replay_route.py)
3. **Phase 3: Success error_type docstring clarification (UNK-01 resolved 2026-10-29) + route tests + docs**
   - [ ] Document the `""`-on-success convention in the `scripts/eventbus/audit.py` module docstring (REQ-003; scripts/eventbus/audit.py)
   - [ ] Add audit assertions to `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_replay_pagination.py`, incl. caplog no-token check (REQ-005; those three test files)
   - [ ] Update the audit signature rows in `docs/24_eventbus/eventbus_08_reference_api.md` (REQ-006; docs/24_eventbus/eventbus_08_reference_api.md)
4. **Phase 4: Verification & Deployment**
   - [ ] `uv run pytest tests/eventbus`; ruff and mypy on changed files; `tools/check_docs_consistency.py --domain eventbus` (REQ-001..REQ-007)
   - [ ] Deployment/scripts check: deploy changed `scripts/eventbus/*.py` via `deploy.sh` and restart the EventBus service; confirm one emitted privileged record end-to-end in the deployed log shows `actor` + `request_id` (REQ-001, REQ-002)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/audit.py | Unit (record shape, caplog emission) | `uv run pytest tests/eventbus/test_eventbus_audit.py` | New keys present; old keys unchanged; no token substring |
| scripts/eventbus/app.py + three route modules | Route integration (mocked audit capture) | `uv run pytest tests/eventbus` | All three actions emit non-empty `request_id` + `actor` |
| tests/eventbus/test_admin_topics_authorization.py | Extended existing tests | `uv run pytest tests/eventbus/test_admin_topics_authorization.py` | Request id, actor, scope summary, persistent assertions pass |
| docs/24_eventbus/eventbus_08_reference_api.md | Docs consistency | `uv run python tools/check_docs_consistency.py --domain eventbus` | Clean |
| Changed files | Static gates | `uv run ruff check`, `uv run mypy` | Clean; bandit baseline (3 B101 findings, none in these files) gains no new finding |

## Risks
- **Risk**: a hypothetical downstream parser depends on a future error_type shape change →
  **Mitigation**: UNK-01 resolved 2026-10-29: no shape change; `error_type=""` stays exactly as today.
- **Risk**: the scope-summary detail leaks more topic information than `detail="updated"` →
  **Mitigation**: mappings + counts only (no secret values; `scripts/eventbus/` has no redaction
  helper functions -- grep 2026-10-29), tests assert content shape
  (UNK-03).
- **Risk**: editing `app.py` wrappers collides with the recently implemented ebauth001 ACK/NACK
  region → **Mitigation**: regions verified disjoint (admin/DLQ/replay vs ACK/NACK wrappers);
  rebase during procedure implementation.
- **Risk**: mock-only audit tests never see the real JSON line → **Mitigation**: at least one
  caplog-based emission test in `test_eventbus_audit.py` pins the on-disk shape.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Additive actor field + shape unit tests (REQ-002, REQ-003 partial, REQ-007) | In Progress | 2026-10-29 | — |  |
| 2 | Wrapper + call-site context plumbing (REQ-001, REQ-002, REQ-004) | In Progress | 2026-10-29 | — |  |
| 3 | error_type docstring clarification + route tests + docs (REQ-003, REQ-005, REQ-006) | In Progress | 2026-10-29 | — | UNK-01 resolved 2026-10-29; no longer blocked |
| 4 | Verification + deploy (REQ-001..REQ-007) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | Owner decision on `error_type` success shape (UNK-01) | Yes | 2026-10-29 (keep current `""` shape) |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261029-115727_01_scripts_eventbus_audit.py.md | 1, 3 | Procedure | Pending | — | — |
| implementations/20261029-115727_02_scripts_eventbus_app.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261029-115727_03_scripts_eventbus_admin_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261029-115727_04_scripts_eventbus_dlq_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261029-115727_05_scripts_eventbus_replay_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261029-115727_06_tests_eventbus_test_eventbus_audit.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261029-115727_07_tests_eventbus_test_admin_topics_authorization.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261029-115727_08_tests_eventbus_test_eventbus_dlq.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261029-115727_09_tests_eventbus_test_eventbus_replay_pagination.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261029-115727_10_docs_24_eventbus_eventbus_08_reference_api.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261028-122415_ebaudit005_privileged-audit-actor-context.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-234417
- **Related target files**: `scripts/eventbus/audit.py`, `scripts/eventbus/app.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/replay_route.py`, `tests/eventbus/test_eventbus_audit.py`, `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_replay_pagination.py`, `docs/24_eventbus/eventbus_08_reference_api.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullet 1 | scripts/eventbus/admin_route.py | Phase 2 | AC-1 | Admin route audit assertions | Explicit in issue |
| REQ-002 | Issue Required Changes bullet 2 | scripts/eventbus/audit.py | Phase 1 | AC-1 | Field-shape unit tests | Explicit in issue |
| REQ-002 | Issue Required Changes bullet 2 | scripts/eventbus/app.py, scripts/eventbus/dlq_route.py, scripts/eventbus/replay_route.py | Phase 2 | AC-1 | Route audit assertions | Explicit in issue |
| REQ-003 | Issue Required Changes bullet 3 | scripts/eventbus/audit.py | Phase 3 | AC-2 | Field-shape unit tests | Resolved 2026-10-29 (UNK-01: keep `error_type=""`; docstring note only) |
| REQ-004 | Issue Required Changes bullet 4 | scripts/eventbus/admin_route.py | Phase 2 | AC-3 | Extended admin audit tests | Explicit in issue |
| REQ-005 | Issue Required Changes bullet 5 | tests/eventbus/test_eventbus_audit.py, tests/eventbus/test_admin_topics_authorization.py, tests/eventbus/test_eventbus_dlq.py, tests/eventbus/test_eventbus_replay_pagination.py | Phases 1-3 | AC-4 | New + extended tests, caplog no-token check | Explicit in issue |
| REQ-006 | Issue Documentation Impact | docs/24_eventbus/eventbus_08_reference_api.md | Phase 3 | AC-5 | check_docs_consistency run | Explicit in issue |
| REQ-007 | Issue Constraints | scripts/eventbus/audit.py | Phases 1-3 | AC-1, AC-2 | Shape tests (additive-only check) | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261029-115727 -->
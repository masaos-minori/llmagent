# Plan: define one owner for the published_at timestamp (ebpubat006)

## Goal
- Make code, schema, tests and docs state the same ownership model for `published_at`. Phase 1
  corrects the one factually wrong statement (the `event_repo.py` docstring calls the field
  "server-generated" although every current insert stores the publisher-supplied value); every
  behavioral change is gated on the owner's open model decision per the issue's explicit
  instruction.

## Priority
Medium

## Scope
- **In-Scope**:
  - Docstring alignment in `scripts/eventbus/event_repo.py` (current behavior, model-neutral).
  - An owner-decision gate: the plan delivers Phase 1 and reports the open question; Phase 2 rows
    (route/schema/docs/tests) execute only after UNK-01 is answered, under the chosen model.
- **Out-of-Scope**: event ordering (that is `seq`); timezone conversion for display; JSONL archive
  format changes beyond this field; schema DDL changes before the owner decision.
- **Dependencies**: `plans/done/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md`
  -- its `scripts/eventbus/schema.sql` procedure is implemented (`idx_events_dlq_unique` present at
  `schema.sql:154`; `implementations/` top level empty), so the issue's "implement after it"
  ordering for a server-owned DDL change is already satisfied. The sibling Plan
  `plans/20261028-231610_ebdlqrecon002_rebuild-missing-dlq-files.md` touches
  `docs/24_eventbus/eventbus_03_dlq_operations.md`; if Phase 2 of this Plan edits the same doc
  (required-fields line), implement after it. Durability docs (`eventbus_09_publish_durability.md`,
  archived ebdurable003 procedures) are implemented; docs-sequencing constraint satisfied.

## Background
Three statements about `published_at` disagree. `event_repo.py:20-23` documents it as "excluded from
canonical equality (server-generated)" -- wrong about current behavior: `publish_route.py:97` reads
the value from the request body and `event_repo.py:85-92` stores it unchanged; `schemas/event_envelope.json`
lists it as required with `format: date-time`. `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md:56`
says it is "supplied by the client and may differ between retries" -- matching runtime.
`schema.sql:9` declares `DEFAULT (strftime(...))`, a server-side default no insert uses (all three
insert call sites -- publish, admin ingest, replay DLQ -- pass the column). No `format_checker` is
passed to `jsonschema.validate` anywhere under `scripts/eventbus` (grep-verified 2026-10-28), so any
string is accepted -- pinned by `test_eventbus_publish_contract.py:146`
(`test_published_at_format_not_validated_by_jsonschema`). A retry of the same `event_id` with a
different `published_at` is treated as a duplicate because the field is excluded from canonical
equality. In-repo publisher evidence: `scripts/agent/eventbus_client.py:120` generates
`datetime.now(timezone.utc).isoformat()`.

## Problem
The code comment, the schema and the documentation disagree on the owner of `published_at`, and the
value's format, timezone and clock-skew rules are undefined although consumers and replay sort or
display it.

## Reason for Change
The mismatch can mislead a publisher or consumer author about whether the timestamp is trustworthy
and whether it can change on retry. No incident cited; Medium (ambiguous public contract); not
time-sensitive.

## Implementation Intent
Per the issue's AI instruction: do not choose the ownership model; start with the documentation and
docstring correction that holds under either model (Phase 1), then stop and report the open question
before changing behavior; do not change schema DDL without the owner's decision. Phase 2 applies the
chosen model everywhere at once (contract, validation, docs, tests land together).

## Requirements
- `REQ-001`: The ownership decision is recorded (by the owner) and Phase 2 makes repo code, schema,
  route, tests and docs state the same model. Blocked on UNK-01; no Phase 2 file executes before it.
- `REQ-002`: `scripts/eventbus/event_repo.py`'s docstring describes actual current behavior
  (publisher-supplied, stored unchanged) without endorsing it as a ratified model. (Phase 1.)
- `REQ-003` (publisher-owned branch): malformed `published_at` values are rejected deterministically
  (format checker or explicit parse); timezone (UTC), maximum skew and future-time rules defined.
  Blocked on UNK-01/UNK-02.
- `REQ-004` (publisher-owned branch): retry-with-different-`published_at` semantics (duplicate vs
  conflict) named and tested. Blocked on UNK-03.
- `REQ-005` (server-owned branch): remove the field from the required envelope (or accept-and-ignore
  with a documented deprecation), set it at insert time, and update JSONL, broker notification,
  replay and DLQ output. Blocked on UNK-01.
- `REQ-006`: existing publishers keep working: the in-repo publisher's UTC `isoformat()` value stays
  valid under any validation tightening; external publisher inventory precedes enforcement; any
  breaking envelope change requires owner approval.
- `REQ-007`: docs state the owner, format and retry semantics of `published_at` (current behavior
  only) once Phase 2 lands.

## Implementation Target Files
**Freeze status**: Draft (cannot freeze: 8 Phase 2 target rows are `Needs confirmation` pending the UNK-01 ownership decision; Phase 1 rows are Verified).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/eventbus/event_repo.py | Phase 1: docstring states actual current behavior (publisher-supplied, stored unchanged) | Docstring contradicts runtime ("server-generated") | REQ-002 | `event_repo.py:20-23` docstring vs `:85-92` insert storing the passed value | Existing publish/dedup tests (behavior unchanged) | Verified |
| scripts/eventbus/publish_route.py | Phase 2 (model-dependent): format enforcement (publisher-owned) or set-at-insert (server-owned) | Validation gap: any string accepted today | REQ-003, REQ-005; AC-2 | `publish_route.py:97` stores body value unchanged; no format checker anywhere in `scripts/eventbus` | tests/eventbus/test_eventbus_publish_contract.py | Needs confirmation (blocked on UNK-01) |
| schemas/event_envelope.json | Phase 2 (conditional, server-owned only): remove from required or document deprecation | Required-field contract changes only under server-owned | REQ-005 | Schema lists `published_at` required with `format: date-time` | Contract tests | Needs confirmation (blocked on UNK-01) |
| scripts/eventbus/schema.sql | Phase 2 (conditional): live DEFAULT (server-owned) or DEFAULT cleanup (DDL, owner-approved); no DDL change pending from sibling Plans | Dead `DEFAULT (strftime(...))` at line 9 misleads about ownership | REQ-001, REQ-005 | `schema.sql:9`; all insert call sites pass the column; `schema.sql` is read-only in `ebdlqrecon002` and `ebpage003` (verified 2026-10-28) | tests/eventbus/test_eventbus_schema.py | Needs confirmation (blocked on UNK-01) |
| tests/eventbus/test_eventbus_publish_contract.py | Phase 2: contract matrix (valid/malformed/missing/future) under the chosen model | `test_published_at_format_not_validated_by_jsonschema` encodes today's lax behavior and must flip or go away atomically | REQ-003, REQ-004, REQ-005; AC-2 | `test_eventbus_publish_contract.py:99` (missing rejected), `:146-157` (malformed accepted) | The updated tests themselves | Needs confirmation (blocked on UNK-01) |
| tests/eventbus/test_eventbus_publish.py | Phase 2: explicit duplicate-publish test with differing `published_at` | Retry semantics are de-facto but unnamed | REQ-004; AC-3 | Repo dedup path (canonical equality excludes `published_at`) | The new test | Needs confirmation (blocked on UNK-01/UNK-03) |
| docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md | Phase 2: state chosen owner, format, timezone/skew and retry semantics | Canonical-equality rationale (line 56) must match the ratified model | REQ-001, REQ-007; AC-1 | Doc line 56 | `tools/check_docs_consistency.py --domain eventbus` | Needs confirmation (blocked on UNK-01) |
| docs/24_eventbus/eventbus_03_dlq_operations.md | Phase 2 (conditional): required-fields line 54 only if server-owned removes the field | Doc lists `published_at` (ISO-8601) as required | REQ-005, REQ-007 | Doc line 54 | check_docs_consistency run | Needs confirmation (blocked on UNK-01) |
| docs/24_eventbus/eventbus_08_reference_api.md | Phase 2 (conditional): `insert_event` signature row 106 only if the signature changes | Row must match code | REQ-007 | `eventbus_08_reference_api.md:106` | check_docs_consistency run | Needs confirmation (blocked on UNK-01) |

Phase 1 executes only the `scripts/eventbus/event_repo.py` row; every `Needs confirmation` row
stays unexecuted until UNK-01 (and UNK-02/UNK-03 for behavior edges) is answered. The table is
therefore not freezable beyond this gated state in this workflow cycle: it is frozen with the
blocked rows recorded, and amended (re-freeze) when the owner decides.

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/eventbus_client.py | In-repo publisher; its `published_at` generation (line 120) defines the compatibility baseline for validation tightening | REQ-006 |
| scripts/eventbus/event_repo.py (canonical-equality helpers) | Confirms the field stays excluded from equality under both models | REQ-001 |
| docs/24_eventbus/eventbus_09_publish_durability.md | Establishes durability/retry context the retry-semantics wording must agree with | REQ-004, REQ-007 |

## Acceptance Criteria
- AC-1 (REQ-001): code, schema, tests and docs name the same owner and semantics for
  `published_at` (after the owner decision; Phase 1 alone must not contradict AC-1 -- its wording is
  behavior-descriptive, not model-ratifying).
- AC-2 (REQ-003, REQ-005): malformed values are rejected (publisher-owned) or ignored
  (server-owned) deterministically.
- AC-3 (REQ-004): retry behavior with a different `published_at` is documented and tested.
- AC-4 (REQ-002): after Phase 1, `event_repo.py` contains no statement contradicted by runtime, and
  the open decision is reported to the owner.

## Tests
- Phase 1 gate (REQ-002): `uv run pytest tests/eventbus` unchanged green + `uv run python
  tools/check_docs_consistency.py --domain eventbus` (docstring-only change).
- Phase 2 matrix (REQ-003/REQ-005): contract tests for a valid value, a malformed value, a missing
  value and a future value under the chosen model.
- Phase 2 retry (REQ-004): duplicate-publish test with differing `published_at` as an explicit named
  assertion.
- Gates after Phase 2: `uv run pytest tests/eventbus`, mypy and ruff, `tools/check_docs_consistency.py
  --domain eventbus`.

## Documentation Impact
Yes (Phase 2): the persistence/schema doc and the publish/API docs named via `docs/00_index.md`'s
task mapping for EventBus persistence and reference API -- `published_at` owner, format and retry
semantics stated as current behavior. Phase 1 requires no doc edit: the persistence doc already
matches runtime (line 56), and no doc may pre-announce an undecided model.

## Assumptions
- Phase 1 wording ("publisher-supplied, stored unchanged; owner decision open") holds under either
  model because it states observed behavior, not the contract.
- The admin ingest path validates the same envelope and supplies `published_at` like publish; both
  are publisher-owned today (verified at call sites).
- Format enforcement call-site choice (publish route only vs all envelope-validating routes) is a
  Phase 2 implementation decision inside the chosen model, not a pre-decision of this Plan.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner of `published_at`: publisher (current runtime) or server? | Open owner decision; the issue forbids AI selection | Owner decision; then re-freeze this table with the chosen Phase 2 rows | True |
| UNK-02 | Timezone, max clock skew and future-time rules under publisher-owned | No published policy exists | Owner decision informed by the publisher inventory (UNK-04) | True (Phase 2 behavior rows) |
| UNK-03 | Retry with differing `published_at`: duplicate (today) or conflict? | Idempotency policy not written down | Owner decision; test named per the answer | True (Phase 2 behavior rows) |
| UNK-04 | Do external publishers rely on a particular format or timezone? In-repo: `scripts/agent/eventbus_client.py` sends UTC isoformat | No inventory of external publishers exists | Inventory under `scripts/` and known integrations before enforcement; owner approval covers any breaking change | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/eventbus/event_repo.py | Phase 1 docstring only | Data layer docs-in-code | 3 | 2 | Yes: deployed; service restart for consistency (no behavior change) |
| scripts/eventbus/publish_route.py | Phase 2 validation or generation | Publish hot path | 0 | 2 | Yes: deployed; service restart required |
| schemas/event_envelope.json | Phase 2 conditional contract change | Public envelope contract | 0 | 1 | Yes: schema file is deployed; envelope consumers affected |
| scripts/eventbus/schema.sql | Phase 2 conditional DDL | Schema (fresh init + recreate policy) | 7 | 2 | Yes: DDL changes follow the recreate policy and `tools/check_db_separation.py` |
| tests/eventbus/test_eventbus_publish_contract.py | Phase 2 contract matrix | Tests only | 3 | 2 | N/A: test file is not deployed |
| tests/eventbus/test_eventbus_publish.py | Phase 2 retry test | Tests only | 5 | 2 | N/A: test file is not deployed |
| docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md | Phase 2 contract statement | Docs only | 14 | 2 | N/A: docs are deployed read-only if changed |
| docs/24_eventbus/eventbus_03_dlq_operations.md | Phase 2 conditional line | Docs only | 21 | 2 | N/A: docs are deployed read-only if changed |
| docs/24_eventbus/eventbus_08_reference_api.md | Phase 2 conditional row | Docs only | 18 | 2 | N/A: docs are deployed read-only if changed |

## Design
- Two-gate structure: Phase 1 is model-independent (docstring fix + report); Phase 2 is atomic
  (contract, validation, docs, tests land together) and only exists after UNK-01.
- Publisher-owned design sketch (not selected, for the owner's decision sheet): enable validation via
  an explicit parse in `publish_route.py` (RFC 3339 / UTC with offset acceptance compatible with
  `datetime.now(timezone.utc).isoformat()`), reject future timestamps beyond a stated skew; keep the
  schema's `format` keyword documented as enforced; leave `schema.sql` DEFAULT removal as an
  owner-approved cleanup item.
- Server-owned design sketch: envelope deprecation (accept-and-ignore documented), insert-time
  `strftime` default becomes live, output paths (JSONL/broker/replay/DLQ) switch to the stored
  value; requires the `schema.sql` row and owner-approved DDL (no sibling Plan modifies
  `schema.sql`; verified 2026-10-28).
- Canonical equality and `event_id` idempotency semantics are unchanged under both models (issue
  constraint): the field remains excluded from equality.
- Format-checker blast radius: `jsonschema` `FormatChecker` enforces every `format:` keyword in the
  shared envelope; call-site scoping (publish vs admin ingest) must keep both paths consistent --
  recorded for Phase 2 procedure design.

## Implementation steps
1. **Phase 1: Model-independent docstring alignment**
   - [ ] Rewrite the `published_at` docstring in `scripts/eventbus/event_repo.py` to state actual current behavior (REQ-002; scripts/eventbus/event_repo.py)
   - [ ] Report the open ownership question to the owner and STOP before any Phase 2 row (issue instruction) (REQ-001; —)
2. **Phase 2: Apply the chosen model (BLOCKED on UNK-01; rows amended at re-freeze)**
   - [ ] Implement the chosen generation/validation model in `scripts/eventbus/publish_route.py` (REQ-003 or REQ-005; scripts/eventbus/publish_route.py)
   - [ ] Amend `schemas/event_envelope.json` and `scripts/eventbus/schema.sql` if the chosen model requires it (REQ-005; schemas/event_envelope.json, scripts/eventbus/schema.sql)
   - [ ] Update the contract matrix in `tests/eventbus/test_eventbus_publish_contract.py` and add the differing-`published_at` duplicate test in `tests/eventbus/test_eventbus_publish.py` (REQ-003, REQ-004; those two test files)
   - [ ] Update `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` and the conditional rows in `docs/24_eventbus/eventbus_03_dlq_operations.md` and `docs/24_eventbus/eventbus_08_reference_api.md` (REQ-007; those three doc files)
3. **Phase 3: Verification & Deployment**
   - [ ] `uv run pytest tests/eventbus`, mypy, ruff; `tools/check_docs_consistency.py --domain eventbus`; if DDL changed: `tools/check_db_separation.py` + recreate policy (REQ-001..REQ-007)
   - [ ] Deployment/scripts check: deploy changed files via `deploy.sh` and restart the EventBus service; Phase 1-only delivery also deploys the docstring change with service restart (no behavior change) (REQ-002)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/event_repo.py | Docstring-only change regression | `uv run pytest tests/eventbus` | Suite green, counts unchanged |
| scripts/eventbus/publish_route.py + schemas/event_envelope.json | Contract matrix (valid/malformed/missing/future) per chosen model | `uv run pytest tests/eventbus/test_eventbus_publish_contract.py` | Deterministic accept/reject per AC-2 |
| scripts/eventbus/event_repo.py dedup path | Duplicate-publish with differing `published_at` | `uv run pytest tests/eventbus/test_eventbus_publish.py` | Named retry-semantics assertion (AC-3) |
| scripts/eventbus/schema.sql (conditional) | Schema-shape test + separation gate | `uv run pytest tests/eventbus/test_eventbus_schema.py`; `uv run python tools/check_db_separation.py` | DDL matches chosen model |
| Changed docs | Docs consistency | `uv run python tools/check_docs_consistency.py --domain eventbus` | Clean |
| Changed files | Static gates | `uv run ruff check`, `uv run mypy` | Clean; bandit baseline (3 B101, none in these files) unchanged |

## Risks
- **Risk**: tightening `date-time` validation breaks an existing external publisher sending a
  non-strict format → **Mitigation**: UNK-04 inventory before enforcement; owner approval required
  for any breaking envelope change (issue constraint); in-repo baseline value stays valid.
- **Risk**: Phase 1 alone is misread as ratifying the publisher-owned model → **Mitigation**:
  wording states behavior + open decision; AC-4 makes the report a completion gate.
- **Risk**: enabling a global `FormatChecker` rejects payloads that pass today → **Mitigation**:
  call-site-scoped enforcement decided in Phase 2 procedure; envelope has a single `format` keyword
  (verified 2026-10-28).
- **Risk**: Phase 2 `schema.sql` edits collide with a sibling Plan's schema work →
  **Mitigation**: verified 2026-10-28 that neither `ebdlqrecon002` nor `ebpage003` modifies
  `schema.sql` (both list it read-only); the only gate is owner-approved DDL (UNK-01) before any
  edit lands.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Docstring alignment + owner report (REQ-002, REQ-001 gate) | Pending | — | — | |
| 2 | Apply chosen model (REQ-003/REQ-005 + tests + docs) | Pending | — | — | Blocked on UNK-01 |
| 3 | Verification + deploy | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Ownership model is an open owner decision (UNK-01); validation rules (UNK-02) and retry semantics (UNK-03) follow from it | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261028-122454_ebpubat006_published-at-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-233320
- **Related target files**: `scripts/eventbus/event_repo.py`, `scripts/eventbus/publish_route.py`, `schemas/event_envelope.json`, `scripts/eventbus/schema.sql`, `tests/eventbus/test_eventbus_publish_contract.py`, `tests/eventbus/test_eventbus_publish.py`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_08_reference_api.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullet 1 | Phase 2 rows (amended at re-freeze) | Phase 2 | AC-1 | Full suite + docs consistency | Needs confirmation (UNK-01) |
| REQ-002 | Issue Required Changes bullet 2 (first half) + AI Instruction | scripts/eventbus/event_repo.py | Phase 1 | AC-4 | Suite green + owner report | Explicit in issue |
| REQ-003 | Issue Required Changes bullet 2 (validation half) | scripts/eventbus/publish_route.py, tests/eventbus/test_eventbus_publish_contract.py | Phase 2 | AC-2 | Contract matrix | Needs confirmation (UNK-01/UNK-02) |
| REQ-004 | Issue Required Changes bullet 2 (retry semantics) | tests/eventbus/test_eventbus_publish.py | Phase 2 | AC-3 | Duplicate-publish test | Needs confirmation (UNK-03) |
| REQ-005 | Issue Required Changes bullet 3 (server-owned branch) | scripts/eventbus/publish_route.py, schemas/event_envelope.json, scripts/eventbus/schema.sql | Phase 2 | AC-1, AC-2 | Contract + schema tests | Needs confirmation (UNK-01) |
| REQ-006 | Issue Constraints bullet 2 | — (inventory + test design across Phase 2) | Phase 2 | AC-2 | UNK-04 inventory; compatible-format tests | Needs confirmation (UNK-04) |
| REQ-007 | Issue Documentation Impact | docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md, docs/24_eventbus/eventbus_03_dlq_operations.md, docs/24_eventbus/eventbus_08_reference_api.md | Phase 2 | AC-1 | check_docs_consistency run | Needs confirmation (UNK-01) |

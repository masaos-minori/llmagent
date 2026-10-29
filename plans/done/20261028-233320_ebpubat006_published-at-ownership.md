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
    Resolved 2026-10-29: the owner chose publisher-supplied (UNK-01), FormatChecker format-only
    enforcement (UNK-02), and current duplicate retry semantics (UNK-03).
- **Out-of-Scope**: event ordering (that is `seq`); timezone conversion for display; JSONL archive
  format changes beyond this field; schema DDL changes before the owner decision.
- **Dependencies**: `plans/done/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md`
  -- its `scripts/eventbus/schema.sql` procedure is implemented (commit `a711abe1f`; the redelivery
  uniqueness index is `idx_events_redelivered_from` at `schema.sql:21` -- the earlier claim of an
  `idx_events_dlq_unique` at `schema.sql:154` was re-verified 2026-10-29 against the current tree
  and the index name/line corrected), so the issue's "implement after it" ordering for a
  server-owned DDL change is already satisfied. The sibling Plan
  `plans/done/20261028-231610_ebdlqrecon002_rebuild-missing-dlq-files.md` (archived 2026-10-29)
  touches `docs/24_eventbus/eventbus_03_dlq_operations.md`; this Plan no longer edits that doc (the
  conditional row was removed at re-freeze), so the sequencing constraint no longer applies.
  Durability docs (`eventbus_09_publish_durability.md`,
  archived ebdurable003 procedures) are implemented; docs-sequencing constraint satisfied.

## Background
Three statements about `published_at` disagree. `event_repo.py:32-33` documents it as "excluded from
canonical equality (server-generated)" -- wrong about current behavior: `publish_route.py:50` reads
the value from the request body (passed to the insert at `:63`) and `event_repo.py:35-38` stores it
unchanged; `schemas/event_envelope.json` lists it as required with `format: date-time`. `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md:56`
says it is "supplied by the client and may differ between retries" -- matching runtime.
`schema.sql:9` declares `DEFAULT (strftime(...))`, a server-side default no insert uses (both INSERT
statements into `events` -- `event_repo.py:36-37` for publish and `dlq_repo.py:104` for DLQ replay --
pass the column; re-verified 2026-10-29). No `format_checker` is
passed to `jsonschema.validate` anywhere under `scripts/eventbus` (grep-verified 2026-10-28), so any
string is accepted -- pinned by `test_eventbus_publish_contract.py:146`
(`test_published_at_format_not_validated_by_jsonschema`). A retry of the same `event_id` with a
different `published_at` is treated as a duplicate because the field is excluded from canonical
equality. In-repo publisher evidence: `scripts/agent/eventbus_client.py:72` generates
`datetime.now(UTC).isoformat()`.

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
  route, tests and docs state the same model. Resolved 2026-10-29: publisher-supplied (UNK-01).
- `REQ-002`: `scripts/eventbus/event_repo.py`'s docstring describes actual current behavior
  (publisher-supplied, stored unchanged) without endorsing it as a ratified model. (Phase 1.)
- `REQ-003` (chosen model): malformed `published_at` values are rejected deterministically via
  `jsonschema.FormatChecker` on the envelope validation call (UNK-02 decision 2026-10-29: format-only;
  no timezone/skew/future-time enforcement this cycle -- rules deferred until the UNK-04 inventory).
- `REQ-004` (chosen model): retry-with-different-`published_at` semantics are duplicate retention
  (first write wins; field excluded from canonical equality) -- named and tested (UNK-03 decision
  2026-10-29).
- `REQ-005` (server-owned branch): NOT SELECTED 2026-10-29; retained as decision history only, no
  row executes under it.
- `REQ-006`: existing publishers keep working: the in-repo publisher's UTC `isoformat()` value stays
  valid under any validation tightening; external publisher inventory precedes enforcement; any
  breaking envelope change requires owner approval.
- `REQ-007`: docs state the owner, format and retry semantics of `published_at` (current behavior
  only) once Phase 2 lands.

## Implementation Target Files
**Freeze status**: Frozen (re-frozen 2026-10-29: owner decisions UNK-01 publisher-supplied, UNK-02
FormatChecker format-only enforcement, UNK-03 duplicate-retention unblock every Phase 2 row; the
server-owned conditional rows -- `schemas/event_envelope.json`, `docs/24_eventbus/eventbus_03_dlq_operations.md`,
`docs/24_eventbus/eventbus_08_reference_api.md` -- are removed from the table because their trigger
condition (server-owned model) did not occur). Rows for `tests/eventbus/test_eventbus_schema_version.py`,
`pyproject.toml` and `uv.lock` were appended at re-freeze: additional target files discovered during
Step 3c -- the row-03 version bump breaks the pinned version lock (2026-10-29), and `FormatChecker`
needs the optional `rfc3339-validator` dependency to validate `date-time` at all (Plan Gap decided
by the owner 2026-10-29).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/eventbus/event_repo.py | Phase 1: docstring states actual current behavior (publisher-supplied, stored unchanged) | Docstring contradicts runtime ("server-generated") | REQ-002 | `event_repo.py:32-33` docstring vs `:35-38` insert storing the passed value (re-verified 2026-10-29) | Existing publish/dedup tests (behavior unchanged) | Verified |
| scripts/eventbus/publish_route.py | Phase 2: enable `jsonschema.FormatChecker` on the envelope validation call so the declared `format: date-time` is enforced (publisher-supplied model, format-only per UNK-02) | Validation gap: any string accepted today | REQ-001, REQ-003; AC-2 | `publish_route.py:42` is the only `jsonschema.validate` call site in `scripts/eventbus` and passes no `format_checker` (verified 2026-10-29); `:50` stores the body value unchanged | tests/eventbus/test_eventbus_publish_contract.py | Verified |
| scripts/eventbus/schema.sql | Phase 2: remove the dead `DEFAULT (strftime(...))` on `published_at` (DDL cleanup the publisher-supplied model requires so the schema stops asserting server ownership); bump `PRAGMA user_version` 2 -> 3 per the recreate policy | Dead `DEFAULT (strftime(...))` at line 9 misleads about ownership | REQ-001; AC-1 | `schema.sql:9` DEFAULT clause; `schema.sql:45` stamps `user_version = 2`; fingerprint gate compares column definitions, so the bump and recreate policy apply (`scripts/shared/eventbus_schema_fingerprint.py:160-175`) | tests/eventbus/test_eventbus_schema_version.py (row 07) | Verified |
| tests/eventbus/test_eventbus_publish_contract.py | Phase 2: contract matrix under the chosen model -- flip `test_published_at_format_not_validated_by_jsonschema` to format-enforced (malformed -> 422), keep the missing-rejection test, add a future-value acceptance case (no skew limit per UNK-02) | The test encodes today's lax behavior and must flip atomically with the route change | REQ-003, REQ-004; AC-2, AC-3 | `test_eventbus_publish_contract.py:99` (missing rejected), `:146-157` (malformed accepted) (verified 2026-10-29) | The updated tests themselves | Verified |
| tests/eventbus/test_eventbus_publish.py | Phase 2: explicit duplicate-publish test with differing `published_at` asserting duplicate retention (UNK-03 decision) | Retry semantics are de-facto but unnamed | REQ-004; AC-3 | Repo dedup path: canonical equality excludes `published_at` (`event_repo.py:32-33`) | The new test | Verified |
| docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md | Phase 2: state the ratified publisher-supplied owner, the format-enforcement rule, the no-future-skew-limit state and duplicate-retention retry semantics | Canonical-equality rationale (line 56) must state the ratified model, not only observed behavior | REQ-001, REQ-007; AC-1 | Doc line 56 matches current runtime (verified 2026-10-29) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| tests/eventbus/test_eventbus_schema_version.py | Phase 2 (appended 2026-10-29 as additional target file discovered during Step 3c): flip `test_schema_version_is_pinned_to_two` to pin `user_version = 3` | The test hardcodes the contract lock `user_version = 2`; the row-03 DEFAULT cleanup bumps the stamped version, so the lock must flip atomically with it | REQ-001; AC-1 | `test_eventbus_schema_version.py:71-72` pins "schema.sql must stamp PRAGMA user_version = 2" (verified 2026-10-29) | The updated test itself | Verified |
| pyproject.toml | Phase 2 (appended 2026-10-29 as additional target file discovered during Step 3c; owner approved the dependency 2026-10-29): add `rfc3339-validator>=0.1.4` to `dependencies` (version corrected 2026-10-29: PyPI max is 0.1.4 per `pip index versions`, so `>=1.0` was unresolvable) | `jsonschema.FormatChecker()` registers no `date-time` checker without this optional dependency -- verified 2026-10-29: `'date-time' in jsonschema.FormatChecker().checkers` is `False` in the current env, so row 02 cannot reject malformed values without it | REQ-003; AC-2 | `pyproject.toml:5-20` dependency list has no rfc3339-validator (verified 2026-10-29); runtime import check confirmed the missing checker | The flipped contract test (row 04) | Verified |
| uv.lock | Phase 2 (appended 2026-10-29 with row 08): regenerate the lockfile via `uv add rfc3339-validator` after the pyproject change | The tracked lockfile must match the declared dependency for `uv sync` and deployment | REQ-003 | `uv.lock` is Git-tracked (verified 2026-10-29) | `uv sync --dev --system-certs` resolves cleanly | Verified |

Removed rows (condition did not occur): `schemas/event_envelope.json` (already declares the field
required with `format: date-time`; unchanged under publisher-supplied),
`docs/24_eventbus/eventbus_03_dlq_operations.md` (line 54 already lists `published_at` as required,
matching the chosen model; verified 2026-10-29), `docs/24_eventbus/eventbus_08_reference_api.md`
(`insert_event` signature row 106 already matches the code and the signature does not change;
verified 2026-10-29).

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
- Re-verified 2026-10-29: there is no EventBus admin ingest path (the earlier "admin ingest"
  assumption was stale -- `admin_route` only manages topic authorization). The only INSERTs into
  `events` are the publish path and DLQ replay (`dlq_repo.py:104`, which copies the stored row's
  value); both supply `published_at` explicitly, so both are publisher-owned today.
- Re-verified 2026-10-29: exactly one envelope-validation call site exists (`publish_route.py:42`),
  so Phase 2 call-site scoping (publish vs other routes) is moot; enforcement applies wherever that
  call is reached.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner of `published_at`: publisher (current runtime) or server? | RESOLVED 2026-10-29 (owner decision): publisher-supplied; the chosen Phase 2 rows are in the frozen table | Owner decision taken; table re-frozen | False (resolved) |
| UNK-02 | Timezone, max clock skew and future-time rules under publisher-owned | RESOLVED 2026-10-29 (owner decision): FormatChecker `date-time` enforcement only; no timezone/skew/future-time rules this cycle, deferred until the UNK-04 inventory | Recorded in REQ-003 | False (resolved) |
| UNK-03 | Retry with differing `published_at`: duplicate (today) or conflict? | RESOLVED 2026-10-29 (owner decision): duplicate retention (first write wins) | Recorded in REQ-004; test named per the answer | False (resolved) |
| UNK-04 | Do external publishers rely on a particular format or timezone? In-repo: `scripts/agent/eventbus_client.py` sends UTC isoformat | No inventory of external publishers exists | Inventory under `scripts/` and known integrations before enforcement; owner approval covers any breaking change | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/eventbus/event_repo.py | Phase 1 docstring only | Data layer docs-in-code | 3 | 2 | Yes: deployed; service restart for consistency (no behavior change) |
| scripts/eventbus/publish_route.py | Phase 2 format enforcement | Publish hot path | 0 | 2 | Yes: deployed; service restart required |
| scripts/eventbus/schema.sql | Phase 2 DDL cleanup + version bump | Schema (fresh init + recreate policy) | 7 | 2 | Yes: DDL changes follow the recreate policy and `tools/check_db_separation.py` |
| tests/eventbus/test_eventbus_publish_contract.py | Phase 2 contract matrix | Tests only | 3 | 2 | N/A: test file is not deployed |
| tests/eventbus/test_eventbus_publish.py | Phase 2 retry test | Tests only | 5 | 2 | N/A: test file is not deployed |
| docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md | Phase 2 contract statement | Docs only | 14 | 2 | N/A: docs are deployed read-only if changed |
| tests/eventbus/test_eventbus_schema_version.py | Phase 2 pinned-version flip | Tests only | 3 | 2 | N/A: test file is not deployed |
| pyproject.toml | Phase 2 dependency addition | Dependency manifest | 2 | 1 | Yes: `uv sync` re-resolves the production venv |
| uv.lock | Phase 2 lockfile regeneration | Lockfile | 2 | 1 | Yes: deployed with the manifest; production venv updated via `uv sync` |

## Design
- Two-gate structure: Phase 1 is model-independent (docstring fix + report); Phase 2 is atomic
  (contract, validation, docs, tests land together) and only exists after UNK-01.
- Publisher-owned design sketch -- SELECTED 2026-10-29 (owner decision): enable validation via
  `jsonschema.FormatChecker` on the envelope validation call in `scripts/eventbus/publish_route.py`
  (RFC 3339 `date-time`; compatible with `datetime.now(UTC).isoformat()` as generated by
  `scripts/agent/eventbus_client.py:72`); no future-time or skew rule this cycle (UNK-02 decision);
  the `schema.sql` DEFAULT removal executes as an owner-approved cleanup with the `user_version`
  bump (2 -> 3) and the recreate policy.
- Server-owned design sketch -- NOT SELECTED 2026-10-29: envelope deprecation (accept-and-ignore
  documented), insert-time `strftime` default becomes live, output paths (JSONL/broker/replay/DLQ)
  switch to the stored value.
- Canonical equality and `event_id` idempotency semantics are unchanged under both models (issue
  constraint): the field remains excluded from equality.
- Format-checker blast radius: `jsonschema` `FormatChecker` enforces every `format:` keyword in the
  shared envelope; re-verified 2026-10-29: `publish_route.py:42` is the only `jsonschema.validate`
  call site under `scripts/eventbus`, and the envelope has a single `format` keyword, so enabling
  the checker there has no collateral format enforcement. Re-verified 2026-10-29 (Plan Gap, owner
  decided the same day): `FormatChecker` registers a `date-time` checker only when the optional
  `rfc3339-validator` package is importable -- `'date-time' in jsonschema.FormatChecker().checkers`
  is `False` in the current env -- so rows 08/09 add that dependency and regenerate the lockfile.

## Implementation steps
1. **Phase 1: Model-independent docstring alignment**
   - [ ] Rewrite the `published_at` docstring in `scripts/eventbus/event_repo.py` to state actual current behavior (REQ-002; scripts/eventbus/event_repo.py)
   - [ ] Report the open ownership question to the owner and STOP before any Phase 2 row (issue instruction) (REQ-001; —)
2. **Phase 2: Apply the chosen model (owner decisions recorded 2026-10-29)**
   - [ ] Add the `rfc3339-validator` dependency in `pyproject.toml` and regenerate `uv.lock` (REQ-003; pyproject.toml, uv.lock)
   - [ ] Implement the chosen generation/validation model in `scripts/eventbus/publish_route.py` (REQ-003; scripts/eventbus/publish_route.py)
   - [ ] Amend `scripts/eventbus/schema.sql` (DEFAULT cleanup + version bump) and flip the pinned version lock in `tests/eventbus/test_eventbus_schema_version.py` (REQ-001; those two files)
   - [ ] Update the contract matrix in `tests/eventbus/test_eventbus_publish_contract.py` and add the differing-`published_at` duplicate test in `tests/eventbus/test_eventbus_publish.py` (REQ-003, REQ-004; those two test files)
   - [ ] Update `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` (REQ-007; the conditional rows `docs/24_eventbus/eventbus_03_dlq_operations.md` and `docs/24_eventbus/eventbus_08_reference_api.md` were removed at re-freeze -- their trigger condition did not occur)
3. **Phase 3: Verification & Deployment**
   - [ ] `uv run pytest tests/eventbus`, mypy, ruff; `tools/check_docs_consistency.py --domain eventbus`; if DDL changed: `tools/check_db_separation.py` + recreate policy (REQ-001..REQ-007)
   - [ ] Deployment/scripts check: deploy changed files via `deploy.sh` and restart the EventBus service; Phase 1-only delivery also deploys the docstring change with service restart (no behavior change) (REQ-002)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/event_repo.py | Docstring-only change regression | `uv run pytest tests/eventbus` | Suite green, counts unchanged |
| scripts/eventbus/publish_route.py + schemas/event_envelope.json | Contract matrix (valid/malformed/missing/future) per chosen model | `uv run pytest tests/eventbus/test_eventbus_publish_contract.py` | Deterministic accept/reject per AC-2 |
| scripts/eventbus/event_repo.py dedup path | Duplicate-publish with differing `published_at` | `uv run pytest tests/eventbus/test_eventbus_publish.py` | Named retry-semantics assertion (AC-3) |
| scripts/eventbus/schema.sql (conditional) | Schema-shape test + separation gate | `uv run pytest tests/eventbus/test_eventbus_schema_version.py`; `uv run python tools/check_db_separation.py` | DDL matches chosen model |
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
| 1 | Docstring alignment + owner report (REQ-002, REQ-001 gate) | Completed | 20261029-153434 | 20261029-160105 |  |
| 2 | Apply chosen model (REQ-003/REQ-005 + tests + docs) | Completed | 20261029-153434 | 20261029-160105 | Unblocked 2026-10-29 by owner decisions (UNK-01/02/03) Implemented 2026-10-29 (all 9 procedures archived); dependent test fixtures adapted, recorded in procedure 03 Notes |
| 3 | Verification + deploy | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Ownership model is an open owner decision (UNK-01); validation rules (UNK-02) and retry semantics (UNK-03) follow from it | Yes | 2026-10-29 (publisher-supplied; FormatChecker format-only; duplicate retention) |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261029-103639_01_scripts_eventbus_event_repo.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261029-103639_02_scripts_eventbus_publish_route.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261029-103639_03_scripts_eventbus_schema.sql.md | 2 | Procedure | Completed | — | — |
| implementations/20261029-103639_04_tests_eventbus_test_eventbus_publish_contract.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261029-103639_05_tests_eventbus_test_eventbus_publish.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261029-103639_06_docs_24_eventbus_eventbus_06_persistence_schema.md | 2 | Procedure | Completed | — | — |
| implementations/20261029-103639_07_tests_eventbus_test_eventbus_schema_version.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261029-103639_08_pyproject.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261029-103639_09_uv.lock.md | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261028-122454_ebpubat006_published-at-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-233320
- **Related target files**: `scripts/eventbus/event_repo.py`, `scripts/eventbus/publish_route.py`, `scripts/eventbus/schema.sql`, `tests/eventbus/test_eventbus_publish_contract.py`, `tests/eventbus/test_eventbus_publish.py`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `tests/eventbus/test_eventbus_schema_version.py`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullet 1 | Phase 2 rows (re-frozen 2026-10-29) | Phase 2 | AC-1 | Full suite + docs consistency | Resolved (owner decisions UNK-01/02/03) |
| REQ-002 | Issue Required Changes bullet 2 (first half) + AI Instruction | scripts/eventbus/event_repo.py | Phase 1 | AC-4 | Suite green + owner report | Explicit in issue |
| REQ-003 | Issue Required Changes bullet 2 (validation half) | scripts/eventbus/publish_route.py, tests/eventbus/test_eventbus_publish_contract.py | Phase 2 | AC-2 | Contract matrix | Resolved (UNK-02 decision 2026-10-29) |
| REQ-004 | Issue Required Changes bullet 2 (retry semantics) | tests/eventbus/test_eventbus_publish.py | Phase 2 | AC-3 | Duplicate-publish test | Resolved (UNK-03 decision 2026-10-29) |
| REQ-005 | Issue Required Changes bullet 3 (server-owned branch) | — (branch not selected; no row executes) | — | AC-1, AC-2 | — | Not selected (2026-10-29) |
| REQ-006 | Issue Constraints bullet 2 | — (inventory + test design across Phase 2) | Phase 2 | AC-2 | UNK-04 inventory; compatible-format tests | Needs confirmation (UNK-04 inventory open, non-blocking caveat) |
| REQ-007 | Issue Documentation Impact | docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md | Phase 2 | AC-1 | check_docs_consistency run | Resolved (2026-10-29) |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261029-103639 -->
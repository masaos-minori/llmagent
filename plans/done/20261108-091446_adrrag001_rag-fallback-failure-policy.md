## Goal
- Publish one cause-based failure-handling decision table for the RAG HTTP-delegation fallback in ADR-010, and align ADR-004 and the RAG specifications with the runtime behavior verified in the current source, without changing runtime behavior or tests.

## Priority
High

## Scope
- **In-Scope**: a decision table in ADR-010 that maps each failure cause to one outcome; correction of the contradictory identity wording (ADR-010 item 11 and the Amendment, `rag_05_07`); documentation of how the remote and local corpus identities are obtained, how fresh they are, and the trust assumption; documentation of the parse-failure versus valid-empty behavior as the current contract; ADR-004 and `rag_05_04` wording aligned to the table; registration of the open decisions as Needs confirmation items.
- **Out-of-Scope**: general RAG redesign; additional fallback providers; unrelated transport or authentication changes; ADR-010 wording cleanup unrelated to the failure policy (tracked by `issues/20261107-050702_adrrag002_reconcile-adr-010-contract.md`); any runtime or test change (requires an owner decision, see UNK-01 to UNK-03).
- **Dependencies**: none on another open Plan. Ordering note: this Plan is implemented first; the adrrag002 reconcile Plan and the final mapping step of the adrver001 verification Plan take their failure-policy wording from this Plan's Phase 1 (they record the dependency on their side).

## Background
ADR-010 Decision Details item 6 lists the fallback conditions: timeouts and connection errors, HTTP 5xx after retries, HTTP 4xx other than 401/403, and HTTP 200 with `is_error=true`. The Fallback Policy section lists a response parse error as a non-fallback condition (treated as an empty result). ADR-004 (Decision Group 10 items 25-27) allows fallback only where an Accepted ADR defines it, names ADR-010 as the sole exception, and forbids converting a safety/integrity failure into a fallback.

Verified against current source (checked in Step 2):
- `call_rag_service()` in `scripts/rag/pipeline_service.py` returns `auth_error` for 401/403, `transient_failure` for any other 4xx (no retry), for 5xx and transport errors after retries, and for `is_error=true`, and returns `empty` with `""` for a parse failure or a non-string `result`.
- `tests/rag/test_rag_pipeline_service.py::TestAuthErrorHandling::test_400_still_triggers_fallback` locks the 4xx fallback; `TestFallbackReasonCallback::test_json_parse_error_does_not_call_set_fallback_reason` locks the parse-failure-as-empty behavior; an `is_error=true` case exists at line 564 of the same file.
- `_identity_gate()` in `scripts/rag/identity_gate.py` rejects (or degrades) only when both identities are present and unequal; a missing identity on either side proceeds and records the unverifiable state. Its docstring records this as the user-approved 2026-10-31 semantics, because the fallback path always carries `remote_identity=None`.
- `config/` sets no `rag_query_service_url`; `docs/21_rag/rag_01_system_overview.md` states HTTP delegation is not used in production.

## Problem
The Issue's concern is a contract ambiguity, not a confirmed runtime defect. The verification found concrete document defects behind it:
- ADR-010 item 11 and the Amendment say an unverifiable identity "is enforced per `rag_identity_mismatch_policy` (`reject` default)", and `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` line 26 says the augment gate "refuses fallback while the identity is unverified". The code proceeds when an identity is missing, and `rag_01_system_overview.md` states the same ("an unverifiable identity preserves the fallback"). The documents contradict each other and the ADR contradicts the code.
- The Issue refers to "doc 08" and "doc 14" as specifications to update. They are RAGCORPUS001 plan document numbers, not files under `docs/`; the identity contract is spread over ADR-010, `rag_01`, `rag_05_01`, `rag_05_07`.
- ADR-010 item 6 treats every 4xx other than 401/403 and every `is_error=true` response as a technical failure, but the wire body carries no cause for either, so a contract or integrity failure reported that way falls back. ADR-010 INV-04 omits the `is_error` condition that item 6 lists.
- A parse failure and a valid empty answer both return `kind="empty"` with `""`, so the caller cannot distinguish them (ADR-010 INV-07 states this as intended).

## Reason for Change
Without one table, components and later implementations can apply incompatible policies, and a future production use of the HTTP path could mask a security or integrity failure behind an availability fallback. The documents currently also disagree on the identity gate. It is High because it concerns the fail-closed guarantee and the empty-versus-failed distinction; it is not time-critical because the HTTP path is inactive in production.

## Implementation Intent
Document the established contract first. Add a decision table to ADR-010 whose outcomes match the code and the tests (valid empty; availability failure eligible for fallback; request or protocol contract failure; authentication/authorization failure; data-integrity failure; corpus identity mismatch or unverifiable identity). Correct the identity wording to the approved semantics. Where the established contract is itself questionable (non-401/403 4xx, `is_error=true` without a cause, parse failure as empty), record the current behavior, mark it Needs confirmation, and leave the decision to the owner instead of inventing policy. No runtime change is made in this Plan.

## Requirements
- `REQ-001`: ADR-010 contains a decision table mapping each failure cause to one outcome (fallback, fail closed with `RagPipelineError`, empty result, fail-fast, identity gate outcome), consistent with `call_rag_service()` and the tests listed in its Verification table.
- `REQ-002`: The unverifiable-identity wording in ADR-010 (Decision Details item 11 and the Amendment) and in `rag_05_07` states the approved semantics: the gate rejects or degrades only when both identities are present and unequal; a missing identity proceeds and is recorded. Invariant identifiers and invariant text stay unchanged.
- `REQ-003`: The documents state how each identity is obtained and its trust assumption: the remote identity is parsed from the `corpus_identity` object of a successful response and is absent whenever the remote call failed; the local identity is read from the local corpus metadata at fallback time; the value is per request (no cache); the remote value is self-reported by the authenticated service and is not independently verified.
- `REQ-004`: ADR-010 states the current parse-failure and non-string-result behavior (empty result, no fallback, distinguishable from a valid empty answer only through the log) and marks the open decision Needs confirmation.
- `REQ-005`: ADR-004 references the ADR-010 decision table where it restates the fallback conditions, and its text no longer restates a condition list that can drift from ADR-010. ADR-004 invariants stay unchanged.
- `REQ-006`: `rag_05_04-error-handling-reference.md` describes the `rag_query_service_url` failure row by cause outcome and points to the ADR-010 table instead of the single "Fallback to in-process pipeline" line.
- `REQ-007`: Each open decision (UNK-01 to UNK-03) that is written into a document as Needs confirmation is registered in the governance inventory.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Authoritative fallback policy (ADR-010) | Add the decision table; correct item 11 and the Amendment unverifiable-identity wording; state identity sources, freshness and trust; state parse-failure behavior; add Needs confirmation markers; keep INV text unchanged (invariant edits are owned by `issues/20261107-050702_adrrag002_reconcile-adr-010-contract.md`) | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` / AC-01, AC-02, AC-03, AC-04 | Item 6 at L72, item 11 at L77, Amendment at L82, INV-04 at L168, Fallback Policy at L197 (checked in Step 2); gate semantics at `scripts/rag/identity_gate.py` L68-90 (checked in Step 2) | `tests/rag/test_rag_pipeline_service.py`, `tests/rag/test_identity_gate.py`, `tests/rag/test_rag_http_mode.py`, `tests/rag/test_pipeline_http_result_kind.py` (existing, run unchanged) | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Platform failure-handling policy (ADR-004) | Replace the restated baseline condition list in the cross-cutting audit with a reference to the ADR-010 decision table; no invariant or decision text change | `REQ-005` / AC-05 | L291 restates "HTTP errors other than authentication errors, timeouts, connection errors" as the ADR-010 baseline (checked in Step 2); Decision Group 10 item 27 at L110 (checked in Step 2) | `tests/rag/test_rag_pipeline_service.py::TestFallbackMarkerLockGuard` (existing, run unchanged) | Verified |
| `docs/21_rag/rag_05_04-error-handling-reference.md` | RAG error-handling reference | Replace the single fallback row for the HTTP delegation failure with cause-based outcomes referencing the ADR-010 table | `REQ-006` / AC-06 | L98 row "Failure when setting `rag_query_service_url` / Fallback to in-process pipeline" (checked in Step 2) | `tests/rag/test_rag_pipeline_service.py` (existing, run unchanged) | Verified |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | RAG index consistency and identity gate description | Correct L26 so it no longer says the gate refuses fallback while the identity is unverified; state the approved semantics and identity sources | `REQ-002`, `REQ-003` / AC-02, AC-03 | L26 says "the augment gate then refuses fallback while the identity is unverified"; contradicted by `identity_gate.py` L68-90 and `rag_01_system_overview.md` L180 (checked in Step 2) | `tests/rag/test_identity_gate.py` (existing, run unchanged) | Verified |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Needs confirmation inventory | Register the Needs confirmation items added to ADR-010 | `REQ-007` / AC-07 | L100 and L130 define the inventory and its registration rule; `tools/check_needs_confirmation_inventory.py` enforces it (checked in Step 2) | `tools/check_needs_confirmation_inventory.py` (checker, run unchanged) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/pipeline_service.py` | Source of truth for the failure outcomes of `call_rag_service()` (L76-237) | `REQ-001`, `REQ-004` |
| `scripts/rag/identity_gate.py` | Source of truth for the gate semantics and local identity read | `REQ-002`, `REQ-003` |
| `scripts/rag/pipeline.py` | `augment()` HTTP-then-in-process flow and gate call (L240-330) | `REQ-001`, `REQ-002` |
| `scripts/rag/http_augment.py` | Result-kind mapping and the empty-versus-`None` contract | `REQ-001` |
| `scripts/rag/corpus_identity.py` | `parse_remote_identity()` returns `None` for an incomplete identity | `REQ-003` |
| `scripts/rag/augment.py` | Stores `last_remote_identity` per call (L96) | `REQ-003` |
| `docs/21_rag/rag_01_system_overview.md` | Already states the approved unverifiable-identity behavior (L180) and that HTTP delegation is not used in production | `REQ-002` |
| `docs/21_rag/rag_05_01-configuration-reference.md` | `rag_identity_mismatch_policy` description (L95) must stay consistent | `REQ-002` |
| `docs/10_adr/adr_01_index.md` | Invariant matrix rows for ADR-010 INV-03/INV-04 must remain valid | `REQ-001` |
| `tests/rag/test_rag_pipeline_service.py` | Locks the 4xx, parse-failure, auth and `is_error=true` outcomes | `REQ-001`, `REQ-004` |
| `tests/rag/test_identity_gate.py` | Locks the gate decisions | `REQ-002` |
| `tests/rag/test_rag_http_mode.py` | Locks result source and fallback behavior | `REQ-001` |
| `tests/rag/test_pipeline_http_result_kind.py` | Locks result-kind and fail-closed auth behavior | `REQ-001` |

## Acceptance Criteria
- AC-01 (`REQ-001`): ADR-010 contains a decision table with one explicit outcome for each of: valid empty result, 401/403, other 4xx, 5xx and transport failure after retries, `is_error=true`, parse failure or non-string result, identity mismatch, identity unverifiable, and local database open failure.
- AC-02 (`REQ-002`): No inspected document says an unverifiable identity refuses the fallback; ADR-010 item 11, its Amendment, `rag_05_07` and `rag_01` agree with `_identity_gate()`.
- AC-03 (`REQ-003`): The documents state the identity sources, the per-request freshness, and the self-reported trust assumption.
- AC-04 (`REQ-004`): ADR-010 states that a parse failure returns an empty result without fallback, and the open decision is marked Needs confirmation.
- AC-05 (`REQ-005`): ADR-004 contains no restated list of ADR-010 fallback conditions and references the ADR-010 table; `check_adr_preservation.py` reports no ERROR for ADR-004.
- AC-06 (`REQ-006`): `rag_05_04` describes the HTTP delegation failure by cause and references ADR-010.
- AC-07 (`REQ-007`): Every Needs confirmation marker added to `docs/` is registered; `check_needs_confirmation_inventory.py` passes.
- AC-08: `git diff --stat` shows only the five target documents changed; `uv run pytest tests/rag` passes with no test or source edits.

## Tests
- `REQ-001`, `REQ-004`: existing tests in `tests/rag/test_rag_pipeline_service.py`, `tests/rag/test_rag_http_mode.py`, `tests/rag/test_pipeline_http_result_kind.py` run unchanged and confirm that each table row matches an existing assertion; a table row without an asserting test is recorded as an unverified item in the ADR, not covered by a new test in this Plan.
- `REQ-002`, `REQ-003`: `tests/rag/test_identity_gate.py` runs unchanged.
- `REQ-005`, `REQ-006`, `REQ-007`: documentation checkers (see Validation plan).
- No new or changed test is planned. If the owner decides to change a runtime outcome (UNK-01 to UNK-03), a separate Plan adds the focused tests.

## Documentation Impact
Yes. ADR-010 (Decision Details, Amendment, Failure Policy, Verification), ADR-004 (cross-cutting audit baseline), `rag_05_04`, `rag_05_07`, and the governance Needs confirmation inventory (target docs located through `docs/00_index.md` "Document References by Task" for RAG and ADR domains). Driven by `REQ-001` to `REQ-007`. Document intent, boundaries, failure behavior, trust assumptions, and the open items; do not copy code-level detail (Docs content policy in `skills/DESIGN.md`). All text in English.

## Assumptions
- The code and the existing tests express the established contract. This Plan documents it and changes no behavior (Issue Assumption: runtime changes are needed only if a decided policy contradicts current behavior; no such decision exists).
- The user-approved 2026-10-31 identity semantics recorded in `identity_gate.py` is the intended contract, and the ADR-010 wording is the stale side (falsifiable: an owner statement that unverifiable identity must reject).
- The follow-up Plan for `adrrag002` edits the same ADR after this Plan's Phase 1 and owns the invariant rewording; this Plan's table and the later invariant text must agree on the `is_error` condition (falsifiable by comparing the two at that Plan's Step 8b).
- The HTTP delegation path stays inactive in production (`config/` sets no `rag_query_service_url`; `rag_01` L180 states it).
- Compatible with the in-flight `plans/20261108-075301_ragvec001_rag-embedding-float32-overflow.md`: it lists `docs/21_rag/rag_05_04-error-handling-reference.md` only as a read-only reference and edits other RAG docs (judged in Step 8b).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a non-401/403 4xx response (for example a contract violation) is intended to fall back. ADR-010 item 6, the ADR-004 audit baseline and `test_400_still_triggers_fallback` all state fallback, which sits uneasily with ADR-004 item 27. | Owner decision on 4xx classification; the remote error payload carries no cause | Owner decides; if changed, a follow-up Plan edits `call_rag_service()`, the locking test, and ADR-010 INV-04. Until then the documents record the current behavior as Needs confirmation | False |
| UNK-02 | Whether a parse failure or non-string `result` should be an empty result or an error. ADR-010 INV-07 states empty. | Owner decision | Same as UNK-01; the current behavior is documented and marked Needs confirmation | False |
| UNK-03 | Whether `is_error=true` should be classified by underlying cause before falling back. | The wire body carries only the flag; the remote error contract is not defined in the inspected files | Owner decision plus a remote error-payload contract; documented as current behavior, marked Needs confirmation | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Modify | Medium | 4 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | Medium | 6 | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_05_04-error-handling-reference.md` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Low | 37 | N/A | not applicable (rsynced) |

## Design
Classification: Path B, because the change touches 5 files (more than 3), although it is documentation-only.

Analysis (Path B, all four recorded):
- Architecture: no Python import or module boundary changes; `lint-imports` is not run because no Python file is a target (checked in Step 3).
- Dependency: the ADR-010 invariants are cited by the `adr_01_index.md` invariant matrix and by tests listed in ADR Verification; INV identifiers and text are not changed, so the matrix and `check_adr_invariant_matrix.py` stay valid. `rag_01`, `rag_05_01` already agree with the code and are references only.
- Historical: 30-day churn from `git log` (table above); `docs/00_governance/governance_03_issue-and-uncertainty-management.md` is the highest-churn row, so its edit is a single registration entry. Bus factor not measured (`git-fame` not run).
- Operational: no ports, databases, or dependencies are touched; no process or lock check is needed.
- Persisted schema and consumer scan: not applicable (no schema, public API, or shared constant change).

Design decisions:
1. The decision table goes into ADR-010 Decision Details as a new item or sub-table placed so existing item numbers and invariant ids do not change; ADR-004 and `rag_05_04` reference it and do not copy it (single source, Docs content policy). Alternative considered: a new specification document; rejected because ADR-010 is the sole authority for the fallback (ADR-004 item 27) and a second table would drift.
2. `check_adr_preservation.py` reports an ERROR when invariant text changes. This Plan therefore does not edit any invariant; the INV-04 omission of `is_error` is carried by the decision table row, and the invariant rewording is owned by the dependent Issue `issues/20261107-050702_adrrag002_reconcile-adr-010-contract.md` (INV-01, INV-04, INV-07, INV-09), which must report the resulting intended preservation ERRORs.
3. Outcomes follow current behavior. The questionable outcomes (UNK-01 to UNK-03) are recorded as Needs confirmation rather than silently changed or silently blessed.
4. The decision table outcomes: valid empty = result `""`, no fallback; 401/403 = `auth_error`, fail closed (`RagPipelineError`); other 4xx = fallback (`transient_failure`, no retry, Needs confirmation); 5xx and transport failure = fallback after bounded retries; `is_error=true` = fallback (Needs confirmation); parse failure or non-string result = empty, no fallback (Needs confirmation); identity mismatch = reject by default, or degraded by policy; identity unverifiable = proceed and record; local database open failure = fail fast, no further fallback.

## Implementation steps
1. **Phase 1: ADR-010 decision table and corrections**
   - [ ] Add the decision table and the identity-source, freshness and trust statement; correct item 11 and the Amendment wording; state parse-failure behavior; add Needs confirmation markers; leave INV text untouched (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`; `docs/10_adr/adr_02_06_010_rag-fallback.md`)
2. **Phase 2: ADR-004 wording**
   - [ ] Replace the restated baseline condition list in the cross-cutting audit with a reference to the ADR-010 table (`REQ-005`; `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`)
3. **Phase 3: RAG specifications**
   - [ ] Rewrite the HTTP delegation failure row by cause and reference ADR-010 (`REQ-006`; `docs/21_rag/rag_05_04-error-handling-reference.md`)
   - [ ] Correct L26 and state the identity sources (`REQ-002`, `REQ-003`; `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`)
4. **Phase 4: Register open items**
   - [ ] Register the Needs confirmation items added in Phase 1 (`REQ-007`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
5. **Phase 5: Verification**
   - [ ] Run the checkers and `uv run pytest tests/rag`; confirm each table row against an existing test or record it as unverified (`REQ-001` to `REQ-007`; all target files). No deploy step: no `scripts/` or `config/` file changes, so `skills/deploy/SKILL.md` is not involved.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All five target documents | Documentation structure and quality | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_japanese.py` | No findings |
| `docs/21_rag/*`, `docs/10_adr/*` | Cross-check against code | `uv run python tools/check_docs_consistency.py --domain rag` | No findings |
| ADR-010, ADR-004 | Invariant and structure preservation | `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_adr_invariant_matrix.py`; `uv run python tools/check_adr_structure.py`; `uv run python tools/check_adr_authority.py` | No ERROR; invariants unchanged |
| Governance inventory and ADR-010 | Needs confirmation registration | `uv run python tools/check_needs_confirmation_inventory.py`; `uv run python tools/check_known_deviation_sync.py` | Every marker registered |
| RAG behavior (unchanged) | Integration/Unit | `uv run pytest tests/rag` | Pass with no source or test edit |

## Risks
- **Risk**: `check_adr_preservation.py` reports an ERROR if invariant text is edited → **Mitigation**: this Plan leaves INV text unchanged; run the checker before finishing and expect no ERROR.
- **Risk**: The documented current behavior for 4xx, `is_error=true` and parse failure is later judged wrong and blesses an insecure rule → **Mitigation**: each is marked Needs confirmation and registered (`REQ-007`); no runtime change is made.
- **Risk**: ADR-010 and the adrrag002 reconcile work edit the same ADR concurrently → **Mitigation**: this Plan is ordered first (Scope Dependencies); adrrag002 edits only wording unrelated to the failure policy.
- **Risk**: The corrected identity wording contradicts a reader's expectation that an unverifiable identity rejects → **Mitigation**: state the reason (the fallback path always has no remote identity, so rejecting would reject every fallback) and cite the 2026-10-31 approval recorded in the code.
- **Risk**: A table row has no asserting test → **Mitigation**: record it as unverified in the ADR instead of claiming coverage.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | ADR-010 decision table and corrections | In Progress | — | — |  |
| 2 | ADR-004 wording | In Progress | — | — |  |
| 3 | RAG specifications (`rag_05_04`, `rag_05_07`) | In Progress | — | — |  |
| 4 | Register Needs confirmation items | In Progress | — | — |  |
| 5 | Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261108-111044_01_docs_10_adr_adr_02_06_010_rag-fallback.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261108-111044_02_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261108-111044_03_docs_21_rag_rag_05_04-error-handling-reference.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261108-111044_04_docs_21_rag_rag_05_07-rag-index-consistency-checks.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261108-111044_05_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-091446
- **Related target files**: `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/21_rag/rag_05_04-error-handling-reference.md`, `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 2-3; ADR-010 L72, `pipeline_service.py` L76-237 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 1 | AC-01 | Existing `tests/rag` suite; `check_adr_preservation.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 5-6; ADR-010 L77, `identity_gate.py` L68-90 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 1 | AC-02 | `tests/rag/test_identity_gate.py`; `check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-002 | `rag_05_07` L26 versus `rag_01` L180 | `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Phase 3 | AC-02 | `tests/rag/test_identity_gate.py`; `check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-003 | Required Changes 5; `corpus_identity.py` `parse_remote_identity`, `augment.py` L96 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 1 | AC-03 | `check_docs_quality.py`; `check_docs_content_policy.py` | Derived from confirmed evidence |
| REQ-003 | Required Changes 5; `identity_gate.py` `compute_local_identity` | `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Phase 3 | AC-03 | `check_docs_quality.py`; `check_docs_content_policy.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes 4; `pipeline_service.py` L218-225 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 1 | AC-04 | `test_json_parse_error_does_not_call_set_fallback_reason`; `check_needs_confirmation_inventory.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 6; ADR-004 L291 | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Phase 2 | AC-05 | `check_adr_preservation.py`; `check_adr_structure.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes 6; `rag_05_04` L98 | `docs/21_rag/rag_05_04-error-handling-reference.md` | Phase 3 | AC-06 | `check_docs_consistency.py --domain rag`; `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-007 | Documentation Impact (register per `routing.md`); governance L100, L130 | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 4 | AC-07 | `check_needs_confirmation_inventory.py` | Explicit in issue |
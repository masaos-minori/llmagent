## Goal
- Make `docs/10_adr/adr_02_06_010_rag-fallback.md` describe one current contract: consistent configuration name, separate statements for database sharing, corpus identity and search-result equivalence, fallback conditions equal to the `adrrag001` decision table, and superseded statements marked historical.

## Priority
High

## Scope
- **In-Scope**: edits to ADR-010 only: Context, Assumptions, Decision Details item 11 and the Amendment, Consequences, Invariants INV-01, INV-04, INV-07 and INV-09, Failure Policy, Data Ownership, Review Triggers and the stale Implementation References entry; a new Amendment record that names each reworded invariant.
- **Out-of-Scope**: runtime or configuration changes; renaming any configuration key; new architectural decisions; redefining the failure policy (taken from the `adrrag001` Plan); cross-file verification matrix updates (`issues/20261107-050705_adrver001_align-invariant-verification-claims.md`); adding new Implementation References.
- **Dependencies**: the failure-policy wording and the decision table come from `plans/20261108-091446_adrrag001_rag-fallback-failure-policy.md`, which also edits ADR-010 (item 11, Amendment, Fallback Policy, Verification) and must land first so the two edits do not conflict. Cross-ordering also with `issues/20261107-050705_adrver001_align-invariant-verification-claims.md`, which depends on both.
  - **Depends on**: plans/20261108-091446_adrrag001_rag-fallback-failure-policy.md | phase 1 | ADR-010 decision table and corrected item 11 wording must exist before this Plan syncs the invariants and fallback conditions to them.

## Background
Verified by reading the complete ADR and the code (checked in Step 2):
- Item 11 and the Amendment (L77, L82) require a corpus identity comparison on every fallback, but Consequences > Negative (L150) still says a divergent `rag_db_path` configuration "is not detected", and INV-09 (L173) says consistency "is not guaranteed" without the identity comparison.
- Context (L43) and Decision use `rag_query_service_url` and note the rename from `rag_service_url`; INV-01 (L165) and the Implementation References entry for `rag_pipeline_models.py` (L304) still say `rag_service_url`. The code reads only `rag_query_service_url` (`scripts/rag/pipeline.py` L257, `scripts/shared/types.py` L97), and `tests/rag/test_config_resolution.py` (L185-193) asserts the old spelling is ignored.
- Item 6 (L72) lists `is_error=true` as a fallback condition; INV-04 (L168) omits it.
- Assumptions (L60) call the `rag_db_path` values identical "by configuration convention only"; Data Ownership (L202) calls `rag.sqlite` "shared by both" modes. Four configuration files (`config/agent.toml`, `config/crawler.toml`, `config/ingester.toml`, `config/rag_pipeline_mcp_server.toml`) set the same path, and `docs/21_rag/rag_01_system_overview.md` L180 states the sameness is a convention that is not enforced.
- Not in the Issue, found during verification: item 11, the Amendment (L82) and Review Triggers (L268) cite "doc 08" and "doc 14", which are RAGCORPUS001 plan document numbers, not documents under `docs/`, so a reader cannot resolve them.

## Problem
Sections of the same ADR describe different revisions of the contract, so an implementer can follow an obsolete statement. Identity equivalence can also be read as identical search results, and "shared database" reads as a requirement although it is a convention.

## Reason for Change
ADR-010 is the sole authority for the RAG fallback (ADR-004 Decision Group 10 item 27). It is High because the inconsistencies concern corpus identity and fallback eligibility. The invariant and fallback wording must wait for the `adrrag001` Plan.

## Implementation Intent
Edit the ADR so five things are stated separately and consistently: physical database sharing (a convention that is not enforced), logical corpus identity (compared at fallback, a detection and not a synchronization), search-result equivalence (never promised), the configuration name (`rag_query_service_url`), and fallback eligibility (as decided by the `adrrag001` Plan). Keep section structure, invariant identifiers and anchors. Keep superseded statements as explicitly historical through the existing Amendment pattern.

## Requirements
- `REQ-001`: INV-01 and the Implementation References entry for `rag_pipeline_models.py` use `rag_query_service_url`; the Context rename statement remains the only mention of `rag_service_url`.
- `REQ-002`: Item 11, the Amendment, INV-09 and Consequences > Negative distinguish database sharing, corpus identity and search-result equivalence; the identity comparison is stated as detection, never as identical results, and the stale "divergent configuration is not detected" statement is corrected.
- `REQ-003`: The "doc 08" and "doc 14" labels in item 11, the Amendment and Review Triggers are replaced by references to documents that exist (`rag_05_07-rag-index-consistency-checks.md` for the gate, `rag_05_01-configuration-reference.md` for the policy key).
- `REQ-004`: Assumptions, Consequences and Data Ownership give one statement of database sharing: all configured paths point to the same canonical `rag.sqlite` by convention, sharing is a deployment arrangement that is not enforced and has no repository-recorded requirement, and a divergence is detected only at fallback time by the identity comparison.
- `REQ-005`: Item 6, INV-04, INV-07, the Fallback Policy and the Implementation Notes carry the same fallback conditions as the `adrrag001` decision table (including `is_error=true`), copied from that outcome and not redefined here.
- `REQ-006`: A new Amendment record names every reworded invariant and every changed Implementation Reference, states that no decision changed, and marks the superseded statements as historical. The record contains none of the change-history markers rejected by the `history_marker_in_active_doc` rule of `config/doc_quality_rules.json` (an `(Added <date>` annotation, an `issues/`, `plans/` or `implementations/` `done/` path, a `REQ-NNN` identifier, a `Resolved` bullet, strikethrough, or a `Traceability` heading).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Authoritative RAG fallback ADR | Reconcile configuration name, identity/sharing/equivalence statements, unresolved "doc 08/14" labels, invariant wording and the failure-policy sections; add the Amendment record | `REQ-001` to `REQ-006` / AC-01 to AC-07 | `rag_service_url` at L165 and L304; "not detected" at L150; INV-09 at L173; INV-04 at L168 versus item 6 at L72; L60 versus L202; "doc 08/14" at L77, L82, L268 (checked in Step 2); code name at `scripts/rag/pipeline.py` L257 (checked in Step 3) | `tests/rag/test_config_resolution.py` (old key ignored), `tests/rag/test_pipeline_http_result_kind.py::test_no_http_mode` (existing, run unchanged) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/pipeline.py` | Confirms `rag_query_service_url` selects the HTTP mode (L257) | `REQ-001` |
| `scripts/shared/types.py` | Confirms the config field name (L97) | `REQ-001` |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Confirms the empty `rag_query_service_url` (L171) cited by the stale reference entry | `REQ-001` |
| `tests/rag/test_config_resolution.py` | Confirms the old key is ignored, so no compatibility statement is needed | `REQ-001` |
| `config/agent.toml` | `rag_db_path` evidence for the sharing convention | `REQ-004` |
| `config/rag_pipeline_mcp_server.toml` | `rag_db_path` evidence for the sharing convention | `REQ-004` |
| `config/crawler.toml` | `rag_db_path` evidence for the sharing convention | `REQ-004` |
| `config/ingester.toml` | `rag_db_path` evidence for the sharing convention | `REQ-004` |
| `docs/21_rag/rag_01_system_overview.md` | States the sharing convention and identity detection (L180) | `REQ-002`, `REQ-004` |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Target of the replacement for the "doc 08" label | `REQ-003` |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Target of the replacement for the "doc 14" label | `REQ-003` |
| `docs/10_adr/adr_01_index.md` | Confirms no status or summary line must follow (L54 title only; INV-04 matrix row unaffected) | `REQ-005` |

## Acceptance Criteria
- AC-01 (`REQ-001`): `rg -n "rag_service_url" docs/10_adr/adr_02_06_010_rag-fallback.md` shows only the Context rename statement; INV-01 and the Implementation References entry say `rag_query_service_url`.
- AC-02 (`REQ-002`): Item 11, the Amendment, INV-09 and Consequences distinguish database sharing, corpus identity and result equivalence, and none claims identical results or says a divergence is never detected.
- AC-03 (`REQ-003`): No "doc 08" or "doc 14" remains in the ADR; each replacement reference resolves to an existing document (internal link reachability check passes).
- AC-04 (`REQ-004`): Assumptions, Consequences and Data Ownership agree on the database-sharing statement.
- AC-05 (`REQ-005`): Item 6, INV-04, INV-07, the Fallback Policy and the Implementation Notes list the same fallback conditions as the `adrrag001` decision table.
- AC-06 (`REQ-006`): The Amendment names each reworded invariant and changed reference and states that no decision changed; superseded statements are marked historical; `check_adr_preservation.py` reports ERROR only for those named intended changes.
- AC-07: Front matter, the H2 heading sequence, invariant identifiers and anchors are unchanged; the document checkers pass; the complete document has been read after editing.

## Tests
- Documentation-only; no new test (`Testing Expectations`: not required). `uv run pytest tests/rag` is run once to confirm no runtime or test file changed behavior (`REQ-001`, `REQ-005`).
- Review the complete document after editing (`REQ-001` to `REQ-006`).

## Documentation Impact
Yes; this Plan is the documentation change. Target: ADR-010 only (located through `docs/10_adr/adr_01_index.md`). Driven by `REQ-001` to `REQ-006`. Document intent, boundaries, failure behavior and configuration names; keep history through the Amendment. English only.

## Assumptions
- `rag_query_service_url` is the authoritative name: code and a test agree, and no configuration file sets either key (falsifiable by a deployed configuration that uses `rag_service_url`; none exists in `config/`).
- Sharing the physical `rag.sqlite` is described as a deployment arrangement by convention; the repository records no requirement for it (falsifiable by an owner decision, see UNK-01).
- Sequencing dependency on the `adrrag001` Plan (overlap on the same ADR): this Plan runs after that Plan's Phase 1 and takes its decision table as the single source of the fallback conditions. Its Phase 1 leaves invariant text untouched, so this Plan owns every invariant edit.
- The `check_adr_preservation.py` ERROR for reworded invariants and a changed Implementation Reference is an expected consequence of the Issue's explicit scope, and is reported with its explanation rather than suppressed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether physical sharing of `rag.sqlite` between the two modes is a requirement or only a deployment arrangement | No requirement or deployment decision is recorded in `docs/` or `config/` | Owner decision; until then the ADR states the verified facts (same path by convention, not enforced, no recorded requirement) | False |
| UNK-02 | The final failure-policy wording depends on the outcome of the `adrrag001` Plan, which is not yet implemented, and on its open owner decisions (4xx, parse failure, `is_error`) | Implementation status of `plans/20261108-091446_adrrag001_rag-fallback-failure-policy.md` | Implement that Plan's Phase 1 first; this Plan copies its table (`Depends on` above) | False |
| UNK-03 | Whether the Implementation References should also list `scripts/rag/identity_gate.py` and `scripts/rag/corpus_identity.py`, which implement item 11 | Owner decision; adding a reference is a preservation ERROR and may need an ADR marker in those files (`check_adr_reference.py`) | Out of scope here; raise as a separate Issue if wanted | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Modify | Medium | N/A | N/A | not applicable (rsynced) |

## Design
Classification: Path A (1 target file, no interface or schema change); architecture, dependency, historical and operational analyses are skipped. Direct verification of consumers: the ADR is referenced by `adr_01_index.md`, `adr_00_document-guide.md`, `rag_00_document-guide.md`, `rag_05_01-configuration-reference.md`, ADR-004 and the governance inventory; none quotes the changed wording (checked in Step 3). Validation quality baseline: `N/A: no Python target`.

Decisions:
1. The Amendment pattern the ADR already uses carries the history; the new record follows it and lists the reworded invariants, so the intended preservation ERRORs have a recorded explanation.
2. INV-01 and the reference entry are corrected to the current name instead of adding an alias statement, because the old key is ignored by the code (fail-safe).
3. The fallback conditions are never restated independently: they are copied from the `adrrag001` table at implementation time.

## Implementation steps
1. **Phase 1: Names and references**
   - [ ] Correct INV-01 and the `rag_pipeline_models.py` reference entry; replace the "doc 08"/"doc 14" labels (`REQ-001`, `REQ-003`; `docs/10_adr/adr_02_06_010_rag-fallback.md`)
2. **Phase 2: Sharing, identity and equivalence statements**
   - [ ] Reconcile Assumptions, Data Ownership, Consequences > Negative, item 11, the Amendment and INV-09 (`REQ-002`, `REQ-004`; `docs/10_adr/adr_02_06_010_rag-fallback.md`)
3. **Phase 3: Failure-policy sync and Amendment record** (starts after the `adrrag001` Plan's Phase 1)
   - [ ] Align item 6, INV-04, INV-07, the Fallback Policy and the Implementation Notes with the decision table; add the Amendment record and the historical markers (`REQ-005`, `REQ-006`; `docs/10_adr/adr_02_06_010_rag-fallback.md`)
4. **Phase 4: Verification**
   - [ ] Read the complete ADR; run the checkers in the Validation plan; report each preservation ERROR with its explanation (`REQ-001` to `REQ-006`; `docs/10_adr/adr_02_06_010_rag-fallback.md`). No deploy step: no `scripts/` or `config/` file changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| ADR-010 | Documentation structure, quality, policy, language | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_japanese.py` | No findings |
| ADR-010 and `docs/21_rag` | Cross-check with code | `uv run python tools/check_docs_consistency.py --domain rag` | No findings |
| ADR-010 | ADR preservation, structure, invariant matrix | `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_adr_structure.py`; `uv run python tools/check_adr_invariant_matrix.py` | Preservation ERROR only for the named intended edits; the other two pass |
| RAG behavior (unchanged) | Regression | `uv run pytest tests/rag` | Pass |

## Risks
- **Risk**: The preservation checker reports ERROR for the reworded invariants and the changed reference, and the checker is a pre-commit/CI gate → **Mitigation**: record the intended changes in the Amendment, report each ERROR with its explanation, and ask the owner before committing if the gate blocks the commit; do not suppress the checker.
- **Risk**: This Plan and the `adrrag001` Plan edit the same ADR sections (item 11, Amendment, Fallback Policy) → **Mitigation**: order this Plan after that Plan's Phase 1 (`Depends on`) and take the corrected wording as the base.
- **Risk**: The sharing statement is read as a new requirement or as a removed one → **Mitigation**: state only the verified facts (same path by convention, not enforced, no recorded requirement) and keep the open question as UNK-01.
- **Risk**: A new Amendment record adds change history to an active document, which the Current-Specification-Only Policy of `governance_01` discourages, and may carry a marker that `check_docs_quality.py` rejects as ERROR → **Mitigation**: follow the existing Amendment form of the ADR, avoid the rejected markers, run the quality checker, and treat the policy question as the owner's decision (see the `adrdoc001` Plan).
- **Risk**: Replacing "doc 08/14" breaks anchors or links → **Mitigation**: use existing document file names and run the structure checker's link reachability check.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Names and references | Completed | — | 20261108-112927 |  |
| 2 | Sharing, identity and equivalence statements | Completed | — | 20261108-112927 |  |
| 3 | Failure-policy sync and Amendment record | Completed | — | 20261108-112927 |  |
| 4 | Verification | Completed | — | 20261108-112927 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261108-111420_01_docs_10_adr_adr_02_06_010_rag-fallback.md.md | 1, 2, 3, 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261107-050702_adrrag002_reconcile-adr-010-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-091719
- **Related target files**: `docs/10_adr/adr_02_06_010_rag-fallback.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (resolve the configuration name); ADR L165, L304; `pipeline.py` L257 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 1 | AC-01 | `rg` check; `tests/rag/test_config_resolution.py`; `check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-002 | Required Changes (identity statements without identical results); ADR L77, L82, L150, L173 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 2 | AC-02 | Full read-through; `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes (obsolete references); ADR L77, L82, L268 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 1 | AC-03 | `check_docs_structure.py` link reachability | Derived from confirmed evidence |
| REQ-004 | Required Changes (database sharing); ADR L60, L202; `config/*.toml`; `rag_01` L180 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 2 | AC-04 | Full read-through; `check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes (synchronize fallback conditions); ADR L72, L168, L171, L197 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 3 | AC-05 | Comparison with the `adrrag001` table; `check_adr_preservation.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes (mark superseded decisions as historical); Implementation Intent (Amendment pattern) | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 3 | AC-06, AC-07 | `check_adr_preservation.py`; `check_adr_structure.py`; `check_adr_invariant_matrix.py` | Explicit in issue |
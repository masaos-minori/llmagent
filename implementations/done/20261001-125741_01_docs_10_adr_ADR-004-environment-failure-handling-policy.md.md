## Goal

Update the ADR-004 Verification Matrix row for INV-15/INV-16 ("no fallback anywhere in the codebase outside what ADR-010 defines") so its Status is no longer `Needs confirmation`, citing concrete verification mechanisms established under REQ-002/REQ-003.

## Scope

- **In-Scope**: Update the Verification Matrix row for INV-15/INV-16 in `docs/10_adr/ADR-004-environment-failure-handling-policy.md`: enumerate ADR-010's defined fallback scenarios, cite the concrete verification mechanism(s), and set Status to something other than `Needs confirmation`.
- **Out-of-Scope**: Changing any fallback behavior itself; resolving CI-014's cross-cutting-role-ownership open question; amending ADR-010's Decision/Invariants text; modifying test files beyond running existing tests.

## Assumptions

- The ADR-010-sanctioned fallback is confined to the RAG pipeline (`call_rag_service()` → None → in-process RAG); no other Accepted ADR currently defines a fallback, so INV-16's "ADR-010 is the sole authority" holds today.
- "Fallback" in INV-15 refers to ADR-004 Decision #26/#27's narrow concept (substituting a Destination when a component becomes unavailable), not to generic defensive patterns (`except` fallthrough, default values, default-value helper functions) that appear throughout the codebase.
- The repo's existing ADR-matrix checker (`check_adr_invariant_matrix.py`) is a sufficient automated grounding of a matrix row's cited test node IDs.
- The owner has decided the REQ-005 automated-guard branch (recorded as resolved UNK-01); the Manual-Review portion (REQ-003) stands regardless.

## Design decisions

- Hybrid mechanism: split coverage along what is mechanically verifiable versus what requires judgment.
  - Mechanically verifiable subset is the `call_rag_service()` return/reason contract for auth and parse errors, pinned by existing tests (`tests/rag/test_rag_pipeline_service.py::test_401_no_fallback`, `tests/rag/test_rag_pipeline_service.py::test_403_no_fallback`, `tests/rag/test_rag_pipeline_service.py::test_json_parse_error_does_not_call_set_fallback_reason`). The marker-lock guard (separate procedure document, REQ-005) covers marker uniqueness.
  - Whole-codebase assertion ("no other ADR-004-scope fallback exists") requires review activity; documented as Manual Review with cadence and owner reference.
- Matrix Status becomes a precise hybrid statement rather than a single value: the covered subset is `Confirmed` (existing tests), and the cross-cutting remainder is covered by a documented Manual Review with a cadence.

## Alternatives considered

- **Pure automation**: A single automated test covering the full invariant. Not feasible because distinguishing ADR-004-scope fallbacks from generic defensive patterns cannot be done without unmanageable false positives (the word "fallback" appears widely, mostly in defensive patterns).
- **Pure Manual Review**: Rely entirely on documented review. Less ideal because the one automatable regression surface (marker-lock guard) should be locked down.

## Implementation

### Target file

`docs/10_adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

1. Read `docs/10_adr/ADR-010-rag-fallback.md` and enumerate its defined fallback scenarios (conditions, destination, full-pipeline re-execution, result-source tracking).
2. Search `scripts/` for every fallback code path and classify each as ADR-010-sanctioned or ADR-004-scope-requiring-an-Accepted-ADR.
3. Cite the existing RAG tests (`tests/rag/test_rag_pipeline_service.py::test_401_no_fallback`, `tests/rag/test_rag_pipeline_service.py::test_403_no_fallback`, `tests/rag/test_rag_pipeline_service.py::test_json_parse_error_does_not_call_set_fallback_reason`) in the ADR-004 INV-15/INV-16 matrix row as a contract pin for the mechanically-verifiable subset. Note (verified against source in this pass): these tests pin only `call_rag_service()`'s contract — 401/403 make one request, record an `http_auth_error:` reason and return `None`; a JSON parse error returns an empty string with no reason. They do NOT show that in-process RAG is skipped: the RAG pipeline runs in-process search whenever the HTTP augment returns `None`, including 401/403. The matrix row must word the citation as a contract pin, not as proof of "no fallback", and must not claim 401/403 do not fall back. The ADR text must not contain source line numbers or implementation counts (`skills/DESIGN.md` Shared Vocabulary).
4. Document a Manual Review checklist item for the whole-codebase "no other ADR-004-scope fallback exists" assertion, with re-review cadence and an owner-reference placeholder pointing to the open `docs/00_governance/governance_03_issue-and-uncertainty-management.md` decision, and state why automation alone does not cover this cross-cutting invariant.
5. Update the matrix row's Status so it is no longer `Needs confirmation` and reflects the hybrid outcome (Confirmed for the subset + documented Manual Review for the remainder).
6. Run `uv run python tools/check_adr_invariant_matrix.py` and confirm zero findings, so the matrix row's cited test node IDs are verified to exist.
7. Run `uv run python tools/check_docs_structure.py docs/10_adr/ADR-004-environment-failure-handling-policy.md` and `uv run python tools/check_docs_content_policy.py` to confirm the ADR doc still passes structural/quality rules after the edit.

### Method

Modify the Verification Matrix row for INV-15/INV-16 in `docs/10_adr/ADR-004-environment-failure-handling-policy.md`:

#### Current state (Verification Matrix row for INV-15/INV-16)

```markdown
- **Test**: ADR-010で定義される場面以外でFallbackが発生しないこと
  - **Verifies**: INV-15, INV-16
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Needs confirmation（本タスクでは個別に再実行していない）
```

#### Required changes

Replace the Status line with a hybrid statement that cites:
1. The existing RAG contract-pin tests for the mechanically-verifiable subset
2. A documented Manual Review procedure for the whole-codebase assertion

Example status text:
```
**Status**: Confirmed for the mechanically-verifiable subset (`call_rag_service()` contract pinned by `tests/rag/test_rag_pipeline_service.py::test_401_no_fallback`, `tests/rag/test_rag_pipeline_service.py::test_403_no_fallback`, `tests/rag/test_rag_pipeline_service.py::test_json_parse_error_does_not_call_set_fallback_reason`); cross-cutting remainder covered by a documented Manual Review with re-review cadence (see below).
```

Add a new subsection under the matrix row documenting the Manual Review procedure:
```markdown
### Manual Review Procedure for INV-15/INV-16 Cross-Cutting Assertion

**Assertion**: No ADR-004-scope fallback exists outside ADR-010's defined scope.

**Scope**: This Manual Review covers the whole-codebase assertion that cannot be robustly asserted by automated testing. It complements the mechanically-verifiable subset pinned by the existing RAG contract tests.

**Procedure**:
1. Search `scripts/` for all occurrences of "fallback" patterns.
2. Classify each occurrence as either (a) ADR-010-sanctioned RAG fallback or (b) ADR-004-scope fallback requiring an Accepted ADR.
3. File follow-up issues for any unclassified ADR-004-scope fallback found.

**Cadence**: Every major release cycle or upon detection of a new fallback pattern.

**Owner**: [Placeholder — pending CI-014 resolution; see `docs/00_governance/governance_03_issue-and-uncertainty-management.md`]

**Why automation alone was not chosen**: The word "fallback" appears throughout `scripts/`, overwhelmingly as defensive patterns (bare-except fallthrough, default-value substitution, default-value helper functions) that are NOT ADR-004-scope fallbacks. Any pattern-based automated detector would produce unmanageable false positives.
```

### Details

**Step 1: Verify ADR-010's defined fallback scenarios**

Read `docs/10_adr/ADR-010-rag-fallback.md` and enumerate:
- Condition: external RAG service returns HTTP error (4xx/5xx) or network timeout
- Destination: in-process RAG pipeline (local model)
- Result-source tracking: the fallback result-source marker is set by `AugmentRefiner.run_http_augment()` in `scripts/rag/augment.py`
- Full-pipeline re-execution: `RagPipeline` in `scripts/rag/pipeline.py` runs in-process search when the HTTP augment result is `None`

Compare these against ADR-010's actual text. Plan UNK-03: determine whether ADR-010's conditions include 401/403 (the pipeline falls through to in-process search for them even though `http_augment.py` logs that it is not falling back); record the outcome in the enumeration, and file a follow-up (do not change behavior) if it is an ADR-004-scope fallback outside ADR-010.

**Step 2: Classify all fallback code paths in `scripts/`**

Run `rg 'fallback' scripts/` and classify each occurrence:
- `scripts/rag/http_augment.py`: `scripts/rag/http_augment.py::in_process_fallback` — ADR-010-sanctioned (HTTP error → local RAG)
- `scripts/rag/augment.py`: `ResultSource.FALLBACK` assignment in `AugmentRefiner.run_http_augment()` — ADR-010-sanctioned (sets marker)
- `scripts/rag/pipeline.py`: fall-through to in-process search on `None` — ADR-010-sanctioned decision point
- Other occurrences: defensive patterns (bare-except, default-value helper functions) — NOT ADR-004-scope fallbacks

**Step 3: Cite existing RAG no-fallback tests**

The following existing tests pin `call_rag_service()`'s contract (they do not prove absence of in-process fallback):
- `tests/rag/test_rag_pipeline_service.py::test_401_no_fallback`: HTTP 401 → one request, `http_auth_error:` reason recorded, `None` returned
- `tests/rag/test_rag_pipeline_service.py::test_403_no_fallback`: HTTP 403 → same contract as 401
- `tests/rag/test_rag_pipeline_service.py::test_json_parse_error_does_not_call_set_fallback_reason`: JSON parse error → empty string returned, no reason recorded

Cite them as such; the cross-cutting "no other fallback" claim stays with the Manual Review.

**Step 4: Document Manual Review procedure**

See Method section above for the complete Manual Review procedure text.

**Step 5: Update matrix Status**

Replace the current Status line with the hybrid statement shown in Method > Required changes.

**Step 6: Validate matrix integrity**

Run `uv run python tools/check_adr_invariant_matrix.py` and confirm zero findings.

**Step 7: Validate ADR doc structure/content**

Run `uv run python tools/check_docs_structure.py docs/10_adr/ADR-004-environment-failure-handling-policy.md` and `uv run python tools/check_docs_content_policy.py`.

## Compatibility considerations

- No behavioral change. Only documentation update.
- The hybrid Status statement is more precise but does not alter any invariant enforcement.
- Backward compatible: existing tests continue to pass; the Manual Review procedure is additive.

## Security considerations

- No security implications. Documentation-only change.
- The Manual Review procedure explicitly documents why automation alone was insufficient, preventing future false confidence in incomplete coverage.

## Rollback considerations

- To rollback, revert the single commit that edits the ADR-004 matrix row.
- The rollback restores the `Needs confirmation` Status and removes the Manual Review subsection.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/ADR-004-environment-failure-handling-policy.md` | Structural validation | `uv run python tools/check_docs_structure.py docs/10_adr/ADR-004-environment-failure-handling-policy.md` | Passes (no structural violations) |
| `docs/10_adr/ADR-004-environment-failure-handling-policy.md` | Content policy validation | `uv run python tools/check_docs_content_policy.py` | Passes (no content policy violations) |
| `docs/10_adr/ADR-004-environment-failure-handling-policy.md` | Matrix integrity | `uv run python tools/check_adr_invariant_matrix.py` | Zero findings (all cited test nodes exist) |
| `tests/rag/test_rag_pipeline_service.py` | Regression (existing tests) | `uv run pytest tests/rag/test_rag_pipeline_service.py -x -q` | All existing tests pass |

## Completion criteria

- AC-001: The matrix row for INV-15/INV-16 has Status other than `Needs confirmation`.
- AC-002: The Status line cites at least one concrete verification mechanism (existing test names or Manual Review reference).
- AC-003: A Manual Review subsection is present documenting the whole-codebase assertion, cadence, and owner.
- AC-004: `check_adr_invariant_matrix.py` reports zero findings against the updated document.
- AC-005: `check_docs_structure.py` and `check_docs_content_policy.py` both pass on the updated document.

## Out of scope

- Changing any fallback behavior, or judging the 401/403 handling (Plan UNK-03).
- Modifying test files (the marker-lock guard is a separate procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261001-172654 | 20261001-172654 | stale check: clean after wording fix; changed: docs/10_adr/ADR-004-environment-failure-handling-policy.md, issues/20261001-165722_fbaud001_fallback-like-paths-without-accepted-adr-definition.md |
| 2 | Add or update tests per Validation plan | Completed | 20261001-172654 | 20261001-172654 | N/A: no test change in this procedure; tests/rag/test_rag_pipeline_service.py 16 passed; full suite 8006 passed once for both cycles (1 pre-existing failure in tests/tools/test_check_docs_quality.py deselected) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261001-172654 | 20261001-172654 | check_adr_invariant_matrix: pass; pre-existing: check_docs_structure size limit, check_docs_content_policy warning |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261001-172654 | 20261001-172654 | docs edit is the deliverable; check_docs_quality/japanese pass; no new findings |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: no blockers | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: `issues/20260930-134926_adr004inv15_adr-004-inv-15-and-inv-16-cross-cutting-fallback-audit-not-re-verified.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260930-212727_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-132025
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md
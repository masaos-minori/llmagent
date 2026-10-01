## Goal

Update the ADR-004 Verification Matrix row for INV-15/INV-16 ("no fallback anywhere in the codebase outside what ADR-010 defines") so its Status is no longer `Needs confirmation`, citing concrete verification mechanisms established under REQ-002/REQ-003.

## Scope

- **In-Scope**: Update the Verification Matrix row for INV-15/INV-16 in `docs/10_adr/ADR-004-environment-failure-handling-policy.md`: enumerate ADR-010's defined fallback scenarios, cite the concrete verification mechanism(s), and set Status to something other than `Needs confirmation`.
- **Out-of-Scope**: Changing any fallback behavior itself; resolving CI-014's cross-cutting-role-ownership open question; amending ADR-010's Decision/Invariants text; modifying test files beyond running existing tests.

## Assumptions

- The ADR-010-sanctioned fallback is confined to the RAG pipeline (`call_rag_service()` → None → in-process RAG); no other Accepted ADR currently defines a fallback, so INV-16's "ADR-010 is the sole authority" holds today.
- "Fallback" in INV-15 refers to ADR-004 Decision #26/#27's narrow concept (substituting a Destination when a component becomes unavailable), not to generic defensive patterns (`except` fallthrough, default values, `_or_default`) that appear throughout the codebase.
- The repo's existing ADR-matrix checker (`check_adr_invariant_matrix.py`) is a sufficient automated grounding of a matrix row's cited test node IDs.
- The owner has decided the REQ-005 automated-guard branch (recorded as resolved UNK-01); the Manual-Review portion (REQ-003) stands regardless.

## Design decisions

- Hybrid mechanism: split coverage along what is mechanically verifiable versus what requires judgment.
  - Mechanically verifiable subset (RAG pipeline must not fall back on non-transport errors) is covered by existing tests (`test_401_no_fallback`, `test_403_no_fallback`, `test_json_parse_error_does_not_call_set_fallback_reason`).
  - Whole-codebase assertion ("no other ADR-004-scope fallback exists") requires review activity; documented as Manual Review with cadence and owner reference.
- Matrix Status becomes a precise hybrid statement rather than a single value: the covered subset is `Confirmed` (existing tests), and the cross-cutting remainder is covered by a documented Manual Review with a cadence.

## Alternatives considered

- **Pure automation**: A single automated test covering the full invariant. Not feasible because distinguishing ADR-004-scope fallbacks from generic defensive patterns cannot be done without unmanageable false positives (~100+ "fallback" occurrences, most defensive).
- **Pure Manual Review**: Rely entirely on documented review. Less ideal because the one automatable regression surface (marker-lock guard) should be locked down.

## Implementation

### Target file

`docs/10_adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

1. Read `docs/10_adr/ADR-010-rag-fallback.md` and enumerate its defined fallback scenarios (conditions, destination, full-pipeline re-execution, result-source tracking).
2. Search `scripts/` for every fallback code path and classify each as ADR-010-sanctioned or ADR-004-scope-requiring-an-Accepted-ADR.
3. Cite the existing RAG no-fallback tests (`test_401_no_fallback`, `test_403_no_fallback`, `test_json_parse_error_does_not_call_set_fallback_reason`) in the ADR-004 INV-15/INV-16 matrix row as covering the mechanically-verifiable subset.
4. Document a Manual Review checklist item for the whole-codebase "no other ADR-004-scope fallback exists" assertion, with re-review cadence and an owner-reference placeholder pointing to the open `governance_03` decision, and state why automation alone does not cover this cross-cutting invariant.
5. Update the matrix row's Status so it is no longer `Needs confirmation` and reflects the hybrid outcome (Confirmed for the subset + documented Manual Review for the remainder).
6. Run `uv run python tools/check_adr_invariant_matrix.py` and confirm zero findings, so the matrix row's cited test node IDs are verified to exist.
7. Run `uv run python tools/check_docs_structure.py docs/10_adr/ADR-004-environment-failure-handling-policy.md` and `uv run python tools/check_docs_content_policy.py` to confirm the ADR doc still passes structural/quality rules after the edit.

### Method

Modify the Verification Matrix row for INV-15/INV-16 in `docs/10_adr/ADR-004-environment-failure-handling-policy.md`:

#### Current state (line ~422-426)

```markdown
- **Test**: ADR-010で定義される場面以外でFallbackが発生しないこと
  - **Verifies**: INV-15, INV-16
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Needs confirmation（本タスクでは個別に再実行していない）
```

#### Required changes

Replace the Status line with a hybrid statement that cites:
1. The existing RAG no-fallback tests for the mechanically-verifiable subset
2. A documented Manual Review procedure for the whole-codebase assertion

Example status text:
```
**Status**: Confirmed for mechanically-verifiable subset (existing RAG no-fallback tests: `test_401_no_fallback`, `test_403_no_fallback`, `test_json_parse_error_does_not_call_set_fallback_reason`); cross-cutting remainder covered by documented Manual Review with re-review cadence (see below).
```

Add a new subsection under the matrix row documenting the Manual Review procedure:
```markdown
### Manual Review Procedure for INV-15/INV-16 Cross-Cutting Assertion

**Assertion**: No ADR-004-scope fallback exists outside ADR-010's defined scope.

**Scope**: This Manual Review covers the whole-codebase assertion that cannot be robustly asserted by automated testing. It complements the mechanistically-verifiable subset covered by existing RAG no-fallback tests.

**Procedure**:
1. Search `scripts/` for all occurrences of "fallback" patterns.
2. Classify each occurrence as either (a) ADR-010-sanctioned RAG fallback or (b) ADR-004-scope fallback requiring an Accepted ADR.
3. File follow-up issues for any unclassified ADR-004-scope fallback found.

**Cadence**: Every major release cycle or upon detection of a new fallback pattern.

**Owner**: [Placeholder — pending CI-014 resolution; see `docs/00_governance/governance_03_issue-and-uncertainty-management.md`]

**Why automation alone was not chosen**: The word "fallback" appears ~100 times across `scripts/`, overwhelmingly as defensive patterns (bare-except fallthrough, default-value substitution, `_or_default`) that are NOT ADR-004-scope fallbacks. Any pattern-based automated detector would produce unmanageable false positives.
```

### Details

**Step 1: Verify ADR-010's defined fallback scenarios**

Read `docs/10_adr/ADR-010-rag-fallback.md` and enumerate:
- Condition: external RAG service returns HTTP error (4xx/5xx) or network timeout
- Destination: in-process RAG pipeline (local model)
- Result-source tracking: `ResultSource.FALLBACK` marker set via `augment.py` line 87
- Full-pipeline re-execution: `pipeline_service.py` delegates to `call_rag_service()` which triggers the fallback

**Step 2: Classify all fallback code paths in `scripts/`**

Run `rg 'fallback' scripts/` and classify each occurrence:
- `scripts/rag/http_augment.py`: `in_process_fallback` — ADR-010-sanctioned (HTTP error → local RAG)
- `scripts/rag/augment.py`: `result_source = ResultSource.FALLBACK` — ADR-010-sanctioned (sets marker)
- Other occurrences: defensive patterns (bare-except, `_or_default`) — NOT ADR-004-scope fallbacks

**Step 3: Cite existing RAG no-fallback tests**

The following tests already verify that non-transport errors do NOT trigger fallback:
- `test_401_no_fallback`: HTTP 401 → no fallback (authentication error)
- `test_403_no_fallback`: HTTP 403 → no fallback (authorization error)
- `test_json_parse_error_does_not_call_set_fallback_reason`: JSON parse error → no fallback

These tests cover the mechanically-verifiable subset: the RAG pipeline must not fall back on non-transport errors.

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

- To rollback, restore the original Status line from git history: `git checkout HEAD~1 -- docs/10_adr/ADR-004-environment-failure-handling-policy.md`.
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

- Changing how approvals are requested or resolved during a live session.
- Altering the approval table schema.
- Unifying the two validation implementations into one.
- Re-wiring `_fetch_server_tools()` as the live path.
- Modifying test files beyond running existing tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Source issue**: N/A: the Plan's own Traceability section carries `{path}` placeholder (not filled)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260930-212727_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-132025
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md

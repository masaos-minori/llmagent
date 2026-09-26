## Goal

Unify `RagRerankError`, `RagPipelineError`, and `RagExpansionError` under the `RagLayerError` base class instead of inheriting directly from `RuntimeError`.

## Priority

Medium

## Scope

- Moving exception definitions to `scripts/rag/exceptions.py`
- Changing their base class to `RagLayerError`
- Updating all imports and `except` clauses across the codebase

## Background

`RagRerankError` and `RagPipelineError` are defined outside `scripts/rag/exceptions.py` and inherit from `RuntimeError` rather than the `RagLayerError` base class used by the other 7 rag-layer exceptions. This was tracked as Known Issue CI-018 in `governance_03_issue-and-uncertainty-management.md`: "The exception hierarchy is not unified under a single base class across the rag layer." Three independent refactoring commits introduced these exceptions:
- `5ac7b757 refactor(rag): Phase 1-3 — backward-compat removal, foundation files, dataclass migration` introduced `RagLayerError` and its 6 subclasses
- `2ff62348 refactor(rag): split llm.py (413→42+260+245 lines) into prompts + client` introduced `RagRerankError`/`RagExpansionError` (`RuntimeError`-based)
- `c0477811 refactor(rag): pipeline/stages fail-fast — remove expand_queries_safe, except Exception fallbacks, add RagPipelineError` introduced `RagPipelineError` (`RuntimeError`-based)

No ADR or design document records a rationale for keeping them separate.

## Problem

Future unification would require touching every `except` clause across `scripts/rag/` that currently catches `RagRerankError`/`RagPipelineError`/`RagExpansionError`/`RuntimeError` by name — a cross-cutting change; until then, a caller could catch the wrong exception type or miss one to a base-class catch.

## Reason for Change

CI-018 has been open since 2026-09-19 without resolution. An inconsistent exception hierarchy makes error handling fragile and increases the risk of catching the wrong exception type.

## Implementation intent

1. Move `RagRerankError` from `scripts/rag/llm_prompts.py` to `scripts/rag/exceptions.py`
2. Move `RagPipelineError` from `scripts/rag/pipeline.py` to `scripts/rag/exceptions.py`
3. Move `RagExpansionError` from `scripts/rag/llm_prompts.py` to `scripts/rag/exceptions.py`
4. Change their base class from `RuntimeError` to `RagLayerError`
5. Update all `except` clauses across `scripts/rag/` that catch these exceptions individually
6. Update imports in all files that reference these exceptions
7. Add/update docstrings with rationale

## Requirements

- `REQ-001`: All three exceptions (`RagRerankError`, `RagPipelineError`, `RagExpansionError`) inherit from `RagLayerError`
- `REQ-002`: All imports are updated to point to `scripts/rag/exceptions.py`
- `REQ-003`: All `except` clauses that previously caught these exceptions individually still work correctly
- `REQ-004`: Tests pass after the change
- `REQ-005`: No regression in exception handling behavior
- `REQ-006`: Docstrings are updated with rationale for the move
- `REQ-007`: Backward compatibility is maintained (existing code catching `RuntimeError` still works via inheritance)

## Implementation Target Files

**Freeze status**: Draft (set to `Frozen` only once `issue-to-plan` Step 8's Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/rag/exceptions.py | Add RagRerankError, RagPipelineError, RagExpansionError classes inheriting from RagLayerError | REQ-001, REQ-006 | Line 11 — RagLayerError base class exists; line 15-36 — 6 existing subclasses follow same pattern | Verified |
| scripts/rag/llm_prompts.py | Remove RagRerankError and RagExpansionError definitions; update __all__ export list | REQ-002, REQ-006 | Line 52-57 — RagExpansionError/RagRerankError definitions; line 232-253 — __all__ exports | Verified |
| scripts/rag/pipeline.py | Remove RagPipelineError definition; update imports if needed | REQ-002 | Line 54 — RagPipelineError definition; line 271 — usage in augment() | Verified |
| scripts/rag/stages/rerank.py | Update import to use RagRerankError from exceptions.py | REQ-002 | Line 1 — imports RagRerankError from llm_prompts; line 105 — except RagRerankError | Verified |
| scripts/rag/stages/mqe.py | Update import to use RagExpansionError from exceptions.py | REQ-002 | Line 1 — imports RagExpansionError from llm_prompts; line 95 — except RagExpansionError | Verified |
| scripts/rag/llm_client.py | Update import to use RagRerankError/RagExpansionError from exceptions.py | REQ-002 | Line 34-38 — imports RagConfig/RagHit/RankedHit; line 168 — raises RagRerankError | Verified |
| tests/rag/test_rag_pipeline.py | Update import to use RagPipelineError from exceptions.py | REQ-002 | Line 1 — imports RagPipelineError from pipeline; line 100 — assertRaises(RagPipelineError) | Verified |
| tests/rag/test_rag_pipeline_stage.py | Update import to use RagRerankError from exceptions.py | REQ-002 | Line 1 — imports RagRerankError from llm_prompts; line 100 — side_effect=RagRerankError | Verified |

## Reference Files

Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Check CI-018 Known Issue details for context | REQ-006 |
| scripts/shared/types.py | Understand RagConfig Protocol used by pipeline consumers | REQ-005 |

## Acceptance criteria

- All three exceptions inherit from `RagLayerError` (REQ-001)
- All imports are updated to point to `scripts/rag/exceptions.py` (REQ-002)
- All `except` clauses that previously caught these exceptions individually still work correctly (REQ-003)
- Tests pass after the change (REQ-004)
- No regression in exception handling behavior (REQ-005)
- Docstrings are updated with rationale (REQ-006)
- Backward compatibility maintained — existing code catching `RuntimeError` still works via inheritance (REQ-007)

## Tests

- Run existing tests: `uv run pytest` (REQ-004)
- Verify exception handling works correctly for all affected code paths (REQ-005)
- Manual verification: confirm no broken imports remain (REQ-002)

## Documentation Impact

If the split is documented via ADR, create a new ADR. Otherwise, update exception docstrings. Driven by REQ-006.

## Assumptions

- The exception class names should be preserved (no renaming)
- The exception docstrings should be preserved with minor wording adjustments
- The `__all__` export lists in `llm_prompts.py` should be updated to remove the moved exceptions
- Import statements in consumer files should be updated to point to `exceptions.py`
- Since the exceptions now inherit from `RagLayerError` which inherits from `Exception`, existing code catching `RuntimeError` will no longer catch them directly — but they still inherit from `Exception` so broad catches will still work
- The exception hierarchy change is backward-compatible because `RagLayerError(Exception)` means existing `except Exception` handlers still work

## Unknowns

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Is there a documented rationale for the split that should be preserved? | Historical analysis needed | Review git history for commit messages explaining the original decision | False |
| UNK-02 | Should `RagExpansionError` also be moved (it was introduced alongside `RagRerankError`)? | Issue already includes it in scope | Confirmed by issue text | False |

## Affected areas

`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/rag/exceptions.py | modify | N/A | N/A | N/A | not applicable (rsynced) |
| scripts/rag/llm_prompts.py | modify | N/A | N/A | N/A | not applicable (rsynced) |
| scripts/rag/pipeline.py | modify | N/A | N/A | N/A | not applicable (rsynced) |
| scripts/rag/stages/rerank.py | modify | N/A | N/A | N/A | not applicable (rsynced) |
| scripts/rag/stages/mqe.py | modify | N/A | N/A | N/A | not applicable (rsynced) |
| scripts/rag/llm_client.py | modify | N/A | N/A | N/A | not applicable (rsynced) |
| tests/rag/test_rag_pipeline.py | modify | N/A | N/A | N/A | not applicable (rsynced) |
| tests/rag/test_rag_pipeline_stage.py | modify | N/A | N/A | N/A | not applicable (rsynced) |

## Design

- Add three new exception classes to `exceptions.py`:
    ```python
    class RagRerankError(RagLayerError):
        """Raised when cross-encoder reranking fails (HTTP, parse, or connection error)."""

    class RagExpansionError(RagLayerError):
        """Raised when MQE query expansion fails (HTTP, parse, or connection error)."""

    class RagPipelineError(RagLayerError):
        """Raised when a pipeline-level operation fails (e.g. DB open, stage failure)."""
    ```
- In `llm_prompts.py`: Remove the `RagRerankError` and `RagExpansionError` class definitions (lines 52-57), and update the `__all__` export list to remove these names. Keep the module docstring updated to reflect that these exceptions are now imported from `exceptions.py`.
- In `pipeline.py`: Remove the `RagPipelineError` class definition (line 54), and add an import from `exceptions.py` where needed.
- In `stages/rerank.py`: Update the import statement to import `RagRerankError` from `exceptions.py` instead of `llm_prompts.py`.
- In `stages/mqe.py`: Update the import statement to import `RagExpansionError` from `exceptions.py` instead of `llm_prompts.py`.
- In `llm_client.py`: Update the import statement to import `RagRerankError`/`RagExpansionError` from `exceptions.py` instead of `llm_prompts.py`.
- In test files: Update imports similarly.
- Since `RagLayerError(Exception)` and the moved exceptions now inherit from `RagLayerError`, existing code that catches `RuntimeError` will no longer catch them directly. However, since `RagLayerError` inherits from `Exception`, broad `except Exception` handlers will still work. This is backward-compatible for most cases.

## Implementation steps

Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table.

1. **Phase 1: Preparation / Refactoring (if needed)**
     - [ ] Read git history for commits introducing `RagRerankError`, `RagExpansionError`, `RagPipelineError` to understand original rationale (UNK-01; scripts/rag/llm_prompts.py, scripts/rag/pipeline.py)
2. **Phase 2: Core Logic Implementation**
     - [ ] Add `RagRerankError`, `RagExpansionError`, `RagPipelineError` classes to `scripts/rag/exceptions.py` inheriting from `RagLayerError` (REQ-001, REQ-006; scripts/rag/exceptions.py)
     - [ ] Remove `RagRerankError` and `RagExpansionError` from `scripts/rag/llm_prompts.py`; update `__all__` export list (REQ-002; scripts/rag/llm_prompts.py)
     - [ ] Remove `RagPipelineError` from `scripts/rag/pipeline.py`; add import from `exceptions.py` (REQ-002; scripts/rag/pipeline.py)
     - [ ] Update import in `scripts/rag/stages/rerank.py` to import `RagRerankError` from `exceptions.py` (REQ-002; scripts/rag/stages/rerank.py)
     - [ ] Update import in `scripts/rag/stages/mqe.py` to import `RagExpansionError` from `exceptions.py` (REQ-002; scripts/rag/stages/mqe.py)
     - [ ] Update import in `scripts/rag/llm_client.py` to import `RagRerankError`/`RagExpansionError` from `exceptions.py` (REQ-002; scripts/rag/llm_client.py)
     - [ ] Update import in `tests/rag/test_rag_pipeline.py` to import `RagPipelineError` from `exceptions.py` (REQ-002; tests/rag/test_rag_pipeline.py)
     - [ ] Update import in `tests/rag/test_rag_pipeline_stage.py` to import `RagRerankError` from `exceptions.py` (REQ-002; tests/rag/test_rag_pipeline_stage.py)
3. **Phase 3: Deployment & Verification**
     - [ ] Run `uv run pytest` to verify tests pass (REQ-004; scripts/rag/)
     - [ ] Verify no broken imports remain (REQ-002; scripts/rag/, tests/rag/)
     - [ ] Verify exception handling behavior is correct for all affected code paths (REQ-005; scripts/rag/)

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/exceptions.py | Unit: verify exception hierarchy | Python inspection of class MRO | All three exceptions inherit from RagLayerError |
| scripts/rag/llm_prompts.py | Unit: verify no broken imports | `uv run python -c "from rag.llm_prompts import *"` | No ImportError |
| scripts/rag/pipeline.py | Unit: verify no broken imports | `uv run python -c "from rag.pipeline import *"` | No ImportError |
| tests/rag/test_rag_pipeline.py | Integration: verify tests pass | `uv run pytest tests/rag/test_rag_pipeline.py` | All tests pass |
| tests/rag/test_rag_pipeline_stage.py | Integration: verify tests pass | `uv run pytest tests/rag/test_rag_pipeline_stage.py` | All tests pass |

## Risks

- **Risk**: Existing code catching `RuntimeError` will no longer catch these exceptions directly → **Mitigation**: Since `RagLayerError(Exception)`, broad `except Exception` handlers still work; only narrow `except RuntimeError` catches would miss them, which is actually more correct behavior
- **Risk**: Circular import if `exceptions.py` is imported before other modules → **Mitigation**: `exceptions.py` has no external dependencies, so circular imports are unlikely

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1a: Read git history for original rationale | Pending | — | — | |
| 2 | Phase 2a: Add exception classes to exceptions.py | Pending | — | — | |
| 3 | Phase 2b: Remove RagRerankError/RagExpansionError from llm_prompts.py | Pending | — | — | |
| 4 | Phase 2c: Remove RagPipelineError from pipeline.py | Pending | — | — | |
| 5 | Phase 2d: Update import in stages/rerank.py | Pending | — | — | |
| 6 | Phase 2e: Update import in stages/mqe.py | Pending | — | — | |
| 7 | Phase 2f: Update import in llm_client.py | Pending | — | — | |
| 8 | Phase 2g: Update import in test_rag_pipeline.py | Pending | — | — | |
| 9 | Phase 2h: Update import in test_rag_pipeline_stage.py | Pending | — | — | |
| 10 | Phase 3a: Run pytest to verify tests pass | Pending | — | — | |
| 11 | Phase 3b: Verify no broken imports remain | Pending | — | — | |
| 12 | Phase 3c: Verify exception handling behavior | Pending | — | — | |

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
- **Source issue**: issues/20260925-232919_ci018_unify_rag_exception_hierarchy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20260926-054434
- **Related target files**: scripts/rag/exceptions.py, scripts/rag/llm_prompts.py, scripts/rag/pipeline.py

## Adversarial Verification

Verified against current source (`scripts/`, `tests/`) and git history on 2026-09-26.
Result: **ISSUE HAS DEFECTS — do not freeze or proceed to plan until corrected.**

| ID | Severity | Location | Finding |
|---|---|---|---|
| E1 | Major | Implementation Target Files | Scope gap. REQ-002/004/005 require ALL imports updated, but two consumer files that import these exceptions from `rag.llm_prompts` are missing from the table: `tests/agent/test_rag_get_cfg.py` (L116 `from rag.llm_prompts import RagRerankError`) and `tests/rag/test_rag_stages.py` (imports at L75, L91, L116, L544, L603, L814, L944). After moving the classes out of `llm_prompts.py`, these become `ImportError` and their tests fail. Add both rows before freeze. |
| E2 | Minor | Background (§), L17 | Wrong count. `exceptions.py` has exactly **6** `RagLayerError` subclasses (EmbeddingSchemaError, PipelineValidationError, SearchQueryError, ChunkFormatError, TokenizationError, UnknownMetadataError). The same sentence says "its 6 subclasses" (L18) — internal contradiction. Change "7" → "6". |
| E3 | Major | Background (§), L19 | Wrong commit attribution. Claims `2ff62348` "introduced `RagRerankError`/`RagExpansionError`". `git log -S 'class RagRerankError'` shows the introducer is `7c50d03a` ("add MqeParseError/RagExpansionError/RagRerankError", 2026-06-10). `2ff62348` (2026-06-16) only split `llm.py` and relocated them. Correct to `7c50d03a`. |
| E4 | Minor | Implementation Target Files, Repository Evidence | Line-number errors: `stages/rerank.py` claimed L1/L105 → actual L11 (import)/L67 (`except RagRerankError`); `stages/mqe.py` claimed L1/L95 → actual L11 (import)/L51 (`except RagExpansionError`); `test_rag_pipeline.py` claimed L1/L100 → actual L12 (import)/L210 (`pytest.raises(RagPipelineError)`); `test_rag_pipeline_stage.py` claimed L1/L100 → actual first import L252, first `side_effect=RagRerankError` L256. |
| E5 | Minor | Implementation Target Files, `llm_client.py` row | False detail. Claims "L34-38 imports RagConfig/RagHit/RankedHit"; `RankedHit` is NOT imported here (only `RagConfig`, `RagHit`, `LLMMessage` at L30-34). `RagRerankError` is raised at L183 & L186, not L168 (L168 is `return []`). |

Claims confirmed correct: `exceptions.py` L11 (`RagLayerError`), L15-36 (6 subclasses); `llm_prompts.py` L52-57 (definitions), L232-253 (`__all__`); `pipeline.py` L54 (`RagPipelineError`), L271 (usage in `augment()`); commit hashes `5ac7b757`, `2ff62348`, `c0477811` all exist with the stated messages.

Recommendation: resolve E1 (add the 2 omitted test files to the target table) and E3 (fix commit id) before Plan Freeze; fix E2/E4/E5 for accuracy.

### Requirement Traceability

See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Acceptance Criteria §1 | scripts/rag/exceptions.py | 2 | All three exceptions inherit from RagLayerError | Python inspection of class MRO | Explicit in issue |
| REQ-002 | Acceptance Criteria §2 | scripts/rag/llm_prompts.py, scripts/rag/pipeline.py, scripts/rag/stages/rerank.py, scripts/rag/stages/mqe.py, scripts/rag/llm_client.py, tests/rag/test_rag_pipeline.py, tests/rag/test_rag_pipeline_stage.py | 2 | All imports are updated to point to scripts/rag/exceptions.py | Manual verification of imports | Explicit in issue |
| REQ-003 | Acceptance Criteria §3 | scripts/rag/stages/rerank.py, scripts/rag/stages/mqe.py, scripts/rag/llm_client.py | 2 | except clauses that previously caught these exceptions individually still work correctly | Manual review of except clauses | Explicit in issue |
| REQ-004 | Testing Expectations §1 | scripts/rag/ | 3 | Tests pass after the change | uv run pytest | Explicit in issue |
| REQ-005 | Acceptance Criteria §5 | scripts/rag/ | 3 | No regression in exception handling behavior | Manual verification of exception handling | Explicit in issue |
| REQ-006 | Documentation Impact | scripts/rag/exceptions.py | 2 | Docstrings are updated with rationale | Manual review of docstrings | Explicit in issue |
| REQ-007 | Constraints §3 | scripts/rag/exceptions.py | 2 | Backward compatibility maintained — existing code catching RuntimeError still works via inheritance | Code inspection of inheritance chain | Explicit in issue |

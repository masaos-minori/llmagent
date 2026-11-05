## Goal

Document the RAG consistency verification-failure contract in the task doc so operators and
consumers understand how an unverified dimension is reported and acted on. The update is
append-only: the existing numeric-consistency description stays intact.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The canonical location is `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`,
  section 8 ("RAG Consistency Checks"). The Plan previously cited a non-existent
  `...-rag-write-integrity.md`; the correct file was confirmed against `docs/00_index.md`.
- Section 8 currently documents `check_rag_consistency`, `is_consistent`, `summarize_issues`,
  and `RagConsistencyReport` as numeric-only (it lists the `_CHECKS` predicates but states no
  verification-status field). See UNK-05.
- The report gains per-dimension unverified flags (`scripts/db/models.py`, seq 03) and the
  recovery path branches on them (`scripts/db/recovery_verification.py`, seq 04). The doc must
  describe both the contract field and consumer expectations (REQ-006).

## Design decisions

- Append a new subsection (e.g. "8.1 Verification Status") after the existing numeric
  description. Do not rewrite or remove the current content, preserving the numeric-contract
  history and the `docs/00_index.md` cross-references.
- Describe three things: (1) the unverified flags and what sets them; (2) how
  `is_consistent` relates to them (orthogonal — numeric vs. status); (3) consumer expectation
  (recovery drill and recovery verification treat an unverified dimension as a verification
  failure, not a pass).

## Alternatives considered

- Rewriting section 8 to fold in the new contract versus appending. Chose append: the numeric
  description is accurate and referenced; rewriting risks drift and loses the incremental
  history. An added subsection keeps both contracts discoverable.
- Documenting only the `RagConsistencyReport` field versus also documenting consumer behavior.
  Chose both: AC-006 requires "the new verification status AND consumer expectations."

## Implementation
### Target file
`docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`

### Procedure
1. Open section 8 (`docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`, L46-L60)
   and confirm the existing numeric description is preserved verbatim.
2. Append a new subsection after the current section 8 body (before the `## Keywords` section):
   - State that `RagConsistencyReport` now carries per-dimension unverified flags
     (`fk_unverified`, `embedding_unverified`, `schema_unverified`), each defaulting to
     `False`, set by `check_rag_consistency` when the corresponding probe raises
     `sqlite3.Error` or `sqlite-vec` is unavailable.
   - Clarify how `is_consistent(report)` relates to the flags. Adjustment (2026-11-05, seq 05
     interlock): the flags are also fail-closed `_CHECKS` rules (predicate-only, no issue
     builder, like `diagnostic_errors`/`read_smoke_test_ok`), so a flag-set report is
     inconsistent even at all-zero counts; they are no longer purely "orthogonal".
   - State consumer expectations: recovery verification and the recovery drill treat any
     unverified dimension as a verification failure (not a pass), per REQ-004/AC-004.
3. Cross-reference the numeric `_CHECKS` predicates already documented above so readers see the
   two layers (numeric vs. verification-status) side by side. Adjustment (2026-11-05): the
   existing L50 predicate list and the L57 "two rules with no builder" claim are stale against
   shipped `_CHECKS` (they omit `fk_inconsistency_count`, `dimension_mismatch`,
   `unknown_schema`, `corpus_meta_verified`, and the new flag rules). Update those two stale
   claims minimally so the appended subsection does not contradict them; this supersedes the
   strict "no existing sentence altered" constraint for those two sentences only.
4. Confirm the `docs/00_index.md` mapping for this doc still points here and that no other doc
   cites the old `...-rag-write-integrity.md` name.

### Method
Append-only Markdown additions to an existing section. No existing sentence is altered.

### Details
- Current section 8 (L46-L60) documents `check_rag_consistency(db, embed_failed=0)`,
  `is_consistent(report) -> bool` (the `_CHECKS` predicate list), `summarize_issues(report)`,
  and the `RagConsistencyReport` fields. Leave all of that unchanged.
- The new subsection describes the additive status layer on top of that numeric contract. Keep
  the tone descriptive (this is a reference doc), matching the existing section.

## Compatibility considerations
Documentation-only. No code, config, or deployment impact. Ensure the appended text does not
contradict the numeric description it follows.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Confirm the file renders cleanly and section 8's numeric description is intact.
- If the repo runs a doc linter/checker listed in `routing.md`, run it (see AGENTS.md Phase
  9). Otherwise a manual read-back of the appended section suffices.

## Completion criteria
- Section 8 documents the new verification-status contract and consumer expectations (AC-006).
- The existing numeric-consistency description is unchanged.
- No lingering reference to the removed `...-rag-write-integrity.md` filename.

## Out of Scope
Defining the report fields (seq 03), the probe/orchestrator changes (seq 01/02), and consumer
branching (seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261105-184806 | 20261105-184806 | Appended `### 8.1 Verification Status (unverified-dimension flags)` at the end of section 8 (before `---`/`## Keywords`). Minimal stale-claim fixes applied to the L50 `_CHECKS` predicate list (added `fk_inconsistency_count`, `dimension_mismatch`, `unknown_schema`, `corpus_meta_verified`, flag rules) and the L57 "two rules with no builder" sentence, per the interlock adjustment recorded in this doc's Procedure step 3. |
| 2 | Add or update tests per Validation plan | Completed | 20261105-184806 | 20261105-184806 | N/A: docs only. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261105-184806 | 20261105-184806 | `tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain db` all pass (exit 0). One follow-up fix at the pre-commit gate run: `check_docs_quality` initially rejected the appended 8.1 line for carrying `REQ-004/AC-004` traceability markers (Current-Specification-Only Policy); markers removed, checker re-passed, and `run_validation_gates.py` re-verified with 0 Fail/Blocked. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261105-184806 | 20261105-184806 | This document's target: `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`. `docs/00_index.md` carries no db_06-specific mapping row (nothing to repoint); no doc references the removed `...-rag-write-integrity.md` name. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-006` (documentation describes the verification-failure contract and consumer expectations)
- **Source issue**: issues/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-153113
- **Related target files**: docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md
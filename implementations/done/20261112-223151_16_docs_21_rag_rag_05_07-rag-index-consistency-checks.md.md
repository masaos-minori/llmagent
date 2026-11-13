## Goal

Remove the unverifiable-corpus-generation fatal class and all identity wording from the RAG
index consistency-checks document (`REQ-010`).

## Scope
**Release unit**: N/A: not part of a release unit (phase 9, after the `corpus-meta-removal` unit)

## Verification Findings (2026-11-13)
- All five references confirmed against the current file: lines 25, 27, 32-34, 46, 104. The
  Plan target-table cites 25, 26, 33, 45, 103 — off by one; this procedure's numbers are the
  current ones.
- This procedure is the only procedure targeting this document; the earlier "a sibling
  procedure edits the same document" note was stale (the Plan no longer has a second row for
  this file).
- Checkers referenced by the validation commands: `tools/check_docs_quality.py`,
  `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`,
  `tools/check_docs_consistency.py` all exist and pass. Correction at execution
  (2026-11-13): `docs_checkers/check_docs_21_rag_index_boundaries.py` does NOT exist in this
  repository (no `docs_checkers/` directory); the earlier "exists" claim was wrong and the
  command was skipped.

## Assumptions
- The class appears in four places: the Fatal-findings bullet, the CRITICAL example code
  block, the Severity Classes table Fatal row, and the findings table row.
- Identity wording appears in the "A failed or timed-out check" bullet (the
  `corpus_generation` diagnostic sentence and the `identity-unverified` reference).

## Design decisions
- Drop the five class references and the identity sentence; keep every other fatal/degraded
  finding and the surrounding structure intact.

## Alternatives considered
N/A: removal is the decided Option B; leaving the wording would contradict REQ-010 and
AC-9 (`identity-unverified` must not appear in docs).

## Implementation
### Target file
`docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
### Procedure
- Remove `unverifiable corpus generation` from the Fatal-findings bullet (line 25).
- Remove the whole fenced example block ```` ```text [CRITICAL] Unverifiable corpus
  generation detected ... ``` ```` including its fences (lines 32-34; re-read exact fences
  before editing).
- Remove `unverifiable corpus generation` from the Severity Classes table Fatal row (line 46).
- Remove the whole `unverifiable corpus generation` row from the findings table (line 104).
- Reword the "A failed or timed-out check" bullet (line 27): keep the continue-startup
  meaning, drop `identity-unverified` and the whole `corpus_generation`/corpus-metadata
  sentence.
### Method
Five localized deletions plus one reword; confirm no `identity-unverified`,
`corpus_generation`, or `corpus_meta_verified` remains.
### Details
- Verified 2026-11-13: all five reference locations match the current file; line numbers
  shift as earlier deletions land within the same editing pass (edit bottom-up).

## Compatibility considerations
N/A: documentation-only; the runtime class is removed by the sibling code documents (seq 10,
11).

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- Scoped: `rg -n "identity-unverified|unverifiable corpus" docs/21_rag docs/41_db` returns
  nothing once seq 16 and 17 land (full cross-file AC-10 search runs at phase 9 end). The
  ADR-010 decision record (seq 01) legitimately names the removed constructs and is excluded
  per the ADR preservation rule.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag` report no
  findings.

## Completion criteria
The document names no unverifiable-generation class and no identity wording; the RAG docs
checkers pass.

## Out of Scope
The startup warning prefix (`REQ-009`, seq 15) and the consistency class (seq 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261113 | cycle G 20261113 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113 | cycle G 20261113 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113 | Documentation checkers only cycle G 20261113 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113 | cycle G 20261113 |

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
- **Requirement ID**: `REQ-010`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
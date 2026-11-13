## Goal

Remove the `RAG identity-unverified:` prefix from the two startup consistency warnings so
the warning category no longer names the removed corpus identity (`REQ-009`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Both warnings live in `scripts/agent/startup_validation.py` around lines 246-261: one for
  the 30s timeout path and one for the exception path.
- Severity routing (`add_warning("rag_consistency", ...)`) and continue-startup behavior are
  unchanged; only the message text changes.

## Design decisions
- Strip the leading `RAG identity-unverified: ` token from both warning messages; keep the
  rest of each message and the surrounding error handling.

## Alternatives considered
N/A: removal is the decided Option B; keeping the prefix would name a removed concept.

## Implementation
### Target file
`scripts/agent/startup_validation.py`
### Procedure
- Change the timeout-path warning string (lines 248-249) to drop the `RAG
  identity-unverified: ` prefix; keep the timeout and continue-startup text.
- Change the exception-path warning string (lines 257-259) to drop the prefix; keep the
  category, exception-type, and continue-startup text.
### Method
Two message-text edits; keep severity, category, and timeout text intact.
### Details
- This region overlaps `rmcompat001` (sequencing dependency): that Plan edits the same two
  warnings' prefix. Apply this edit to a re-read of the file.

## Compatibility considerations
N/A: warning-message text change only; the `rag_consistency` warning category is retained.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "identity-unverified" scripts tests docs` returns nothing only after the companion
  startup test rows (seq 34, 35) and the `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
  edit (seq 16) also land; run this acceptance search at phase 9 end (AC-9).
  At this cycle alone, the `docs/` hit at `rag_05_07` line 27 is expected until seq 16 lands.
- `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_startup.py tests/agent/test_startup_severity_classification.py`
  passes once all three startup rows land; tests keep their severity/continue-startup
  assertions and assert the category and timeout text (Plan Validation note).

## Completion criteria
Neither warning carries the `identity-unverified` prefix; severity and continue-startup
behavior are unchanged.

### Companion test files
- `tests/agent/test_startup_validation.py`
  - Procedure: drop the `identity-unverified` assertion at lines 265 and 291 and the wording
    in the docstring bullet at line 255; keep every other assertion.
  - Validation: `uv run pytest tests/agent/test_startup_validation.py` passes.

## Out of Scope
The other two startup test files that assert the same prefix (standalone docs 34, 35).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261113 | cycle G 20261113 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113 | Covers companion `test_startup_validation.py` cycle G 20261113 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113 | cycle G 20261113 |
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
- **Requirement ID**: `REQ-009`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `scripts/agent/startup_validation.py`, `tests/agent/test_startup_validation.py`
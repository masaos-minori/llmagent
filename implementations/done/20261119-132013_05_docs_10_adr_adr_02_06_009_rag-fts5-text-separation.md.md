## Goal

Record the owner decision on the English normalization shape in `ADR-009` as an invariant
restatement (with the tradeoff), resolving the previously pending approval
(`REQ-008`).

## Scope
**Release unit**: english-content-stopword-loss

## Assumptions

- Shape B is locked by the owner decision (UNK-01, 20261119-130500): English
  `normalized_content` is `NULL`; English behaves like code/markdown under INV-04.
- The ADR's INV-01/02/04/06 wording (`adr_02_06_009` lines 158-163) already describes this
  behavior; only the approval record is missing.

## Design decisions

- **Invariant restatement, not an exception.** Shape B makes English conform to INV-04
  (`normalized_content = NULL` for English/code/non-normalized text), so the decision is
  recorded as a clarification/restatement of INV-04 plus the recorded tradeoff — not as
  an exception to any invariant.
- **Record the rejected Shape-A tradeoff.** Note that Shape A (store the
  stopword-stripped projection as `content`, FTS5 indexes stripped text) was considered
  and rejected because no FTS quality measurement favors it and it would require amending
  INV-04.

## Alternatives considered

- `N/A: the shape is locked to Shape B by the owner decision; the ADR records that
  decision and the rejected alternative, not a new design.`

## Implementation
### Target file
`docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`

### Procedure
Add a short, clearly-marked section (e.g. under the invariants or a new "English
normalization shape" subsection) that states:

1. **Decision (Shape B).** For English, `chunks.normalized_content` is `NULL` and
   `chunks.content` is the original crawled text region. English therefore follows INV-04
   exactly; no exception is made.
2. **Basis.** Resolved by owner on 20261119-130500 (UNK-01): INV-04 already dictates
   `NULL` for English, so Shape B restores the documented invariant without an exception;
   Shape A (storing the stopword-stripped projection as `content`) was rejected because no
   FTS quality measurement favors keeping the projection and it would require amending
   INV-04.
3. **Tradeoff.** Under Shape B, FTS5 indexes the original `content` via
   `COALESCE(normalized_content, content)`; search-time tokenization no longer drops
   stopwords, which may change English BM25 ranking but preserves the LLM-facing original.

Then record the approval: set the "Current Decision Approval (pending)" entry
(`adr_02_06_009` line 279) to the approver and date (leave approver/date for the owner to
fill if unknown, but mark the decision as approved rather than pending).

### Method

Locate the INV-04 passage (`adr_02_06_009` line ~161) and the approval block
(line ~279) and add the three points above near the invariants; update the approval line
from "pending" to the resolved decision. Do not alter INV-01/02/05/06 or the Japanese
path description. Keep the ADR's existing structure and tone.

### Details

- Docs-only change. No code, symbols, or imports are affected.
- This is the only ADR modified; the ChunkSplitter detail doc is covered by the sibling
  procedure.

## Compatibility considerations

- `N/A: documentation-only; no runtime or API impact. The ADR records a resolved
  decision, not a behavior change.`

## Security considerations

`N/A: documentation-only.`

## Rollback considerations

Revert the commit that edits the ADR.

## Validation plan

- Read-back: confirm the Shape B decision, its basis, and the rejected Shape-A tradeoff
  are recorded, and the approval line is no longer "pending".
- `tools/check_workitem_structure.py` / doc linter per `routing.md` Tools "When to run
  which tool".

## Completion criteria

- `ADR-009` states English `normalized_content` is `NULL` (Shape B) as an INV-04
  restatement, records the owner resolution date and the rejected Shape-A tradeoff, and
  marks the decision approved.

## Out of Scope

- Production code (`chunk_english.py`, `chunk_splitter.py`), the test, and the
  ChunkSplitter detail doc — covered by the sibling procedures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the ADR per Implementation > Procedure/Method/Details | Completed | 2026-11-19 | 2026-11-19 | Added Shape B invariant restatement + approved entry (UNK-01) |
| 2 | Run the documentation checkers (`rules/toolchain.md`, `routing.md`) | Completed | 2026-11-19 | 2026-11-19 | check_adr_authority/structure/reference/invariant_matrix/known_deviation_sync all pass |

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
- **Requirement ID**: `REQ-008` (ADR-009 records the decision as an invariant or
  explicit exception, with the tradeoff)
- **Source issue**: `issues/20261119-112014_ragcrv002_english-content-stopword-loss.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-123746_ragcrv002_english-content-stopword-loss.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-132013
- **Related target files**: `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`

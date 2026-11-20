## Goal
- Rewrite the removed-import history note in governance_05 as a present-tense statement of the current import boundary (Plan REQ-002: rewrite the note as boundary text).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Re-run the Plan AC-1 history search on this file immediately before editing; if the statement is already gone, skip it and record the evidence (source issue AI Implementation Instruction). Verified present on 20261120 (line 138).
- Line 23 ("if a documented command is removed or renamed") is conditional policy text, not history; it stays (Plan AC-1 explicit carve-out).

## Design decisions
- State the boundary in present tense only: the paragraph already asserts `imports nothing from scripts/rag/`; the former-import clause adds nothing current, so it is deleted rather than rephrased.

## Alternatives considered
- Keep a neutral pointer to the RAGCORPUS001 decision record — rejected: decision history lives in the plans and git; the Current-Specification-Only policy bars it here.

## Implementation
### Target file
- `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`

### Procedure
- Edit only the prose paragraph around line 138 (the `Not an edge: Agent → RAG` paragraph). Do not touch any `## Software Runtime Dependency Graph` edge-list line (`- A → B`), which `tools/check_dependency_graph_cycles.py` parses.

### Method
- Delete the clause "; its former `rag.corpus_identity` import was removed with RAGCORPUS001 Option B" so the sentence reads: "... maintains `rag.sqlite` through the `db` layer and imports nothing from `scripts/rag/`."

### Details
- Leave every edge-list line and every other paragraph byte-identical; the paragraph rewrite must keep the two sentences' meaning (maintenance path via `db`, RAG reached only via the generic `Agent → MCP` edge).

## Compatibility considerations
- Docs-only prose edit; the graph edge data is unchanged, so the cycle checker and the generated graph consumers are unaffected.

## Security considerations
- N/A: prose-only edit with no security behavior.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_dependency_graph_cycles.py` (Plan AC-1).
- History search re-run on this file returns no hit for the Plan AC-1 pattern.

## Completion criteria
- No removed-import statement remains in this file; the `Agent → RAG` boundary paragraph reads as present-tense specification; the edge list is unchanged and the cycle checker passes.

## Out of Scope
- Any other governance document; any change to graph node/edge data or to line 23 policy text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) with the doc-quality, structure, and graph-cycle checkers named in the Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (rewrite the governance_05 removed-import note as a present-tense boundary statement)
- **Source issue**: issues/20261117-123022_adrchk022_history-comment-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-201816_adrchk022_history-comment-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-202848
- **Related target files**: `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`

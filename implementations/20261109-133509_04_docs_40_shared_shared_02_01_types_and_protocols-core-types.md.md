## Goal

State the `None` absent-marker semantics of `distance` and `bm25_score` in the shared-types documentation (`REQ-007`: document the hit field semantics).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: section 5 of `docs/40_shared/shared_02_01_types_and_protocols-core-types.md`.
- Plan step 3 (documentation); apply after the code procedures.

## Assumptions

- Re-verified at generation time: section 5 (`## 5. RawHit, MergedHit, RankedHit, RagHit`) describes the incremental field model and says only `rerank_score` may be `None`; that sentence becomes inaccurate once the two signal fields are optional.
- `docs/21_rag/rag_04_dto-models-types.md` contains no field-default claim for these fields (Plan Step 3 grep), so it is not a target.
- Docs must be written in English (`skills/DESIGN.md` Output language) and follow the Docs content policy: describe the contract, not the merge algorithm.

## Design decisions

- Add one short paragraph to section 5: `distance` and `bm25_score` are `float | None`, `None` means no retrieval list produced that signal for the chunk, and a merged hit carries the best available value (minimum) of each across the merged lists.
- Reword the existing "only `rerank_score` may be `None`" clause so it no longer contradicts the new paragraph.

## Alternatives considered

N/A: single-paragraph documentation edit.

## Implementation
### Target file
`docs/40_shared/shared_02_01_types_and_protocols-core-types.md`

### Procedure
1. Edit section 5: correct the `rerank_score`-only-`None` wording and add the paragraph described under Design decisions.
2. Keep the heading, anchors, front matter, and the Import line unchanged.

### Method
- Plain prose; no code block of the merge logic and no implementation-derived detail (`tools/check_docs_content_policy.py`).

### Details
- Mention that a valid `0.0` distance is a real perfect match and is distinct from `None`.
- Do not edit any other document; a needed change elsewhere is an additional target file discovery.

## Compatibility considerations

N/A: documentation only; no document is renamed or removed, so no link changes.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/40_shared/shared_02_01_types_and_protocols-core-types.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain shared`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- Section 5 names the `None` semantics for `distance` and `bm25_score` and no longer claims only `rerank_score` may be `None`.
- All five checkers report no findings.

## Out of Scope

- Code, tests, and other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit section 5 of the shared-types document | Pending | — | — | |
| 2 | Run the documentation checkers named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (shared-types documentation states the absent-marker semantics)
- **Source issue**: issues/20261108-131010_ragrev006_rrf-merge-drops-signals.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165114_ragrev006_rrf-merge-drops-signals.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-133509
- **Related target files**: `docs/40_shared/shared_02_01_types_and_protocols-core-types.md`

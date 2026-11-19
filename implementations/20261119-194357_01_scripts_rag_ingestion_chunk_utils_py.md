## Goal

Add the single accumulation collaborator under `scripts/rag/ingestion/chunk_utils.py` that owns the shared min/max/overlap accumulation loop and exposes the oversized-item strategy, short-tail strategy, separator, and optional paired-companion stream as explicit inputs (`REQ-001`). Keep `start_next_buf` and `_split_overlong` as the overlap and segmentation primitives behind it, and make `merge_text_items` a thin delegating wrapper so the code path's entry point (`_chunk_code`'s call site) stays unchanged (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The collaborator lives inside the `rag.ingestion` layer (importlinter `rag` package boundary), so it depends only on `start_next_buf`/`_split_overlong` and does not alter the package's import contracts.
- `merge_text_items` keeps its current signature `(items, sep, min_chunk, max_chunk, chunk_overlap)` and delegates to the collaborator, so `chunk_splitter._chunk_code` (its sole caller, `scripts/rag/ingestion/chunk_splitter.py:308`) needs no change.
- The three paths' divergent oversized-item/short-tail semantics are intentional per-language behavior to preserve, not a defect to unify (`Plan Assumptions`). The collaborator reproduces each via explicit strategy inputs; the choice of shared vs per-language strategy values affects maintainability, not output.

## Design decisions
- The collaborator takes ordered items, separator, `min_chunk`, `max_chunk`, `chunk_overlap`, an oversized-item strategy selector, a short-tail strategy selector, and an optional per-item companion value plus merge/overlap handler (Japanese paired stream) or none (code/English). Strategy selectors encode the oversized/short-tail axes (Plan `UNK-01`) as explicit inputs rather than hard-coded choices.
- `start_next_buf` (overlap-from-tail) and `_split_overlong` (segment overlong item within `max_chunk`) remain the primitive building blocks the collaborator composes; nothing about their behavior changes.

## Alternatives considered
- Inlining the strategy logic as parameters vs. small strategy objects: parameters (callable or enum) keep the collaborator a single tight loop and match the existing primitive style; strategy objects add a layer with no behavioral benefit for a two-axis choice.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_utils.py`

### Procedure
1. Add the accumulation collaborator (a module-level function or a small class) that owns the min/max/overlap loop and accepts the strategy/companion inputs described above.
2. Route `merge_text_items` through the collaborator as a thin wrapper preserving its exact signature and return value.
3. Leave `start_next_buf` and `_split_overlong` untouched.

### Method
- The loop iterates items, applying the oversized-item strategy (segment via `_split_overlong` or keep whole), the short-tail strategy (grow buffer / emit as own chunk / merge into last), and overlap via `start_next_buf`, exactly mirroring the current `merge_text_items` body so output is byte-identical.
- `merge_text_items` becomes `return <collaborator>(items, "\n\n", min_chunk, max_chunk, chunk_overlap)` (or equivalent), with no logic of its own.

### Details
- Preserve the existing docstring contract of `merge_text_items`; note delegation to the collaborator.
- Do not change `_split_overlong` or `start_next_buf` signatures or behavior.

## Compatibility considerations
- `merge_text_items`' public signature and output are unchanged; `chunk_splitter._chunk_code` is unaffected. English/Japanese routing rows handle their own delegation.

## Security considerations
N/A: pure text-accumulation logic with no I/O or untrusted-data handling beyond existing behavior.

## Rollback considerations
N/A: revert the commit; the collaborator is additive and `merge_text_items` reverts to its prior inline body.

## Validation plan
- Unit: run `uv run pytest tests/rag/ingestion/test_chunk_utils.py`; existing `merge_text_items` cases stay green and new collaborator branch tests (oversized/short-tail/overlap/companion) pass.
- Mutation: confirm mutations to the collaborator's branches are caught by the new tests.

## Completion criteria
- `merge_text_items` delegates to exactly one accumulator; its existing test assertions pass unchanged; `start_next_buf`/`_split_overlong` are byte-for-byte unchanged.

## Out of Scope
- Routing the English (`chunk_english.py`) and Japanese (`chunk_japanese.py`) paths through the collaborator — covered by their own rows.
- Removing the per-mixin buffer fields — sequenced to `ragcrv006`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the accumulation collaborator and route `merge_text_items` through it | Pending | — | — | |
| 2 | Add mutation-sensitive unit tests for the collaborator branches | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (one accumulation loop owns the shared accumulation) and `REQ-002` (`merge_text_items` entry point unchanged for `_chunk_code`)
- **Source issue**: `issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-185003_ragcrv005_unify-chunk-merge-strategies.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-194357
- **Related target files**: `scripts/rag/ingestion/chunk_utils.py`

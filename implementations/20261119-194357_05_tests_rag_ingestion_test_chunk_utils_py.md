## Goal

Add the per-path characterization fixtures that pin each current chunk list (and pair list for Japanese) for representative inputs, and mutation-sensitive unit tests for the collaborator's oversized-item, short-tail (mid-stream and end-of-stream), overlap, and paired-companion branches (`REQ-005`, `REQ-008`). Host these in `tests/rag/ingestion/test_chunk_utils.py`.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The existing `merge_text_items` tests already anchor the code path (`Plan Implementation Target Files`, row 5 evidence); new fixtures extend the same module.
- Characterization fixtures reproduce each path's exact current output from representative fixture documents without live corpus runs (`Plan Assumptions` UNK-01).
- Per-path fixture placement (new file vs. `test_chunk_utils.py`) is decided in implementation but kept under `tests/rag/ingestion/` (`Plan UNK-02`); this procedure hosts them in `test_chunk_utils.py` unless a size convention dictates a separate file.

## Design decisions
- Characterization fixtures assert the exact returned chunk list (code/English) and exact pair list incl. `None` (Japanese) as golden references captured pre-extraction.
- Mutation tests target each collaborator branch independently so a mutation in any branch is caught.

## Alternatives considered
- A single parametrized fixture vs. per-path fixtures: per-path fixtures mirror the three independent paths and make a regression in one path attributable without ambiguity.

## Implementation
### Target file
`tests/rag/ingestion/test_chunk_utils.py`

### Procedure
1. Add characterization fixtures asserting the exact current output of `merge_text_items` (code path) for representative inputs; capture as golden reference before extraction.
2. Add mutation-sensitive unit tests for the collaborator's oversized-item, short-tail (mid-stream and end-of-stream), overlap, and paired-companion branches.

### Method
- Code path: assert exact chunk lists for overlong-item, short-tail, overlap, and empty inputs (extend the existing `TestMergeTextItems` style).
- Collaborator branches: drive the collaborator directly with each strategy/companion input and assert the exact output; include a `None`-companion case mirroring the Japanese contract.
- Keep the existing `start_next_buf`/`_split_overlong` tests intact.

### Details
- Mark symbols this test file introduces as `(new)` for the detector (e.g. new test class/function names) via `tools/mark_procedure_new_symbols.py` if needed.

## Compatibility considerations
- Pure additions to the test module; existing tests are preserved.

## Security considerations
N/A: tests only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Unit: `uv run pytest tests/rag/ingestion/test_chunk_utils.py` all pass; mutations caught.
- Regression: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` and `test_ingester.py` stay green.

## Completion criteria
- Characterization fixtures pin each path's exact current output and pass unchanged; collaborator branch tests exist and pass; mutation testing catches the branches.

## Out of Scope
- Changing the assertions' expected values to match a behavior change — behavior locking requires zero diff, not adjusted expectations (`REQ-005`).

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
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005` (behavior locked via characterization + regression) and `REQ-008` (mutation-sensitive unit tests)
- **Source issue**: `issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-185003_ragcrv005_unify-chunk-merge-strategies.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-194357
- **Related target files**: `tests/rag/ingestion/test_chunk_utils.py`

## Goal

- Confirm the split generated agent indexes pass the documentation size gate without touching `tools/check_docs_structure.py`; touch this file only if regeneration still produces a document above the ceiling (`REQ-012`, `REQ-015`; `AC-013`).

## Scope
**Release unit**: reference-completeness

## Assumptions

- Plan default (`D-14`, owner decision 2026-11-19 resolving UNK-08): the split is the fix, not an exception. The expected measured sizes are 25835 B for `agent_13_reference-api-generated.md`, which keeps its 171 top-level entries, and about 30206 B for `agent_14_reference-api-subpackages-generated.md`, both below `MAX_SIZE = 32768`.
- The checker itself needs no change for this plan: it already applies `MAX_SIZE` to every document and reads `SIZE_EXCEPTIONS` only for basenames that need a higher ceiling.

## Design decisions

- Default action is verification with no edit: run the checker after rows 15, 22 and 30 land and record the measured sizes.
- Conditional action: only if a regenerated agent document still exceeds `MAX_SIZE`, add a `SIZE_EXCEPTIONS` entry (line 81) keyed by basename whose ceiling equals the measured size, with a dated rationale naming this plan. A ceiling above the measured size is not permitted: the existing entries record actual sizes, not headroom.

## Alternatives considered

- Raise `MAX_SIZE` globally: rejected - the ceiling is a whole-suite constraint and raising it would silence findings in unrelated documents.
- Add the exception preemptively so the gate cannot fail: rejected by `REQ-013` - an exception for a size that was never measured is a tolerant fallback.

## Implementation
### Target file
`tools/check_docs_structure.py`
### Procedure
1. After rows 15, 22, 30 land, run `uv run python tools/check_docs_structure.py` and record the reported size of both agent generated documents.
2. If both are under `MAX_SIZE = 32768`, leave this file unmodified and record the measured sizes in the Execution Status notes.
3. Only if a document still exceeds the ceiling, add its basename to `SIZE_EXCEPTIONS` (line 81) with the measured size and a dated rationale naming this plan, then re-run the checker.

### Method
- Verification-first conditional row; the checker's logic and thresholds stay as they are.

### Details
- `tools/check_docs_structure.py`: `MAX_SIZE = 32768` (line 40), `SIZE_EXCEPTIONS: dict[str, int]` (line 81), applied as `limit = SIZE_EXCEPTIONS.get(path.name, MAX_SIZE)` (line 115).
- Measured 2026-11-19 baselines: `agent_13_reference-api-generated.md` 25835 B (block 24770 B, 171 entries) and `agent_11_04_memory-module-reference-generated.md` 10072 B. Corrected by adversarial verification 2026-11-19: this procedure earlier recorded 32022 B for the memory document, a mis-measurement; `wc -c` reports 10072 B. The largest generated document in the suite is `docs/90_deployment/deployment_01_deployment.md` at 27764 B.
- The subpackage blocks measured 29141 B rendered together, which is what makes the split sufficient without an exception.

## Compatibility considerations

- This file is a checker, not a generated artifact: the only permitted change is a data-table entry with a rationale, and the plan default is none.

## Security considerations

- N/A: no credential or path-exposure change.

## Rollback considerations

- N/A under the default path (no edit). If an exception were added, revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py` — no size finding for any agent generated document (docs: documentation structure)
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — the rendered subpackage document stays under `MAX_SIZE` (unit (T-015): ceiling and completeness)

## Completion criteria

- Default path: the checker passes with both agent documents under `MAX_SIZE` and `SIZE_EXCEPTIONS` is unchanged.
- Conditional path: an exception entry exists only with a measured size and a dated rationale naming this plan.

## Out of Scope

- Raising `MAX_SIZE`.
- Adding exceptions for documents other than the two agent generated indexes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate first, then run the checker | Completed | 20261119-231642 | 20261119-231642 | after rows 15, 22, 30 ran uv run python tools/check_docs_structure.py 2026-11-19: All checks passed |
| 2 | Record both measured document sizes | Completed | 20261119-231642 | 20261119-231642 | no edit expected measured agent_13 25931 B and agent_14 30498 B, both under MAX_SIZE 32768 |
| 3 | Add a dated `SIZE_EXCEPTIONS` entry only if a document is still over the ceiling | N/A | — | — | conditional path no generated document exceeded the ceiling: SIZE_EXCEPTIONS unchanged |

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
- **Requirement ID**: `REQ-012` (agent_api covers the scripts/agent/ subpackages (workflow/, services/, commands/, shared/) so the generated API reference is complete), `REQ-015` (the generated agent API index stays within the documentation size ceiling)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `tools/check_docs_structure.py`
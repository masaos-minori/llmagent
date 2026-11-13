## Goal

Stop `RagPipeline` from computing or reporting a corpus generation so no code path returns
a placeholder identity for a now-absent table (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `SCHEMA_VERSION` is imported by `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
  (sibling document, seq 04) and by the identity test being deleted; removing it here and
  in that server document leaves no importer.
- `compute_local_identity` is used only in `augment()`; no other method reads it.
- Overlap with `plans/..._rmcompat001_rag-delegation-leftovers.md` is a sequencing
  dependency (that plan edits `ingester.py` and the startup warnings, not this file).

## Design decisions
- Delete the import, the module constant, the instance attribute, the compute block, and
  the diagnostics append as five independent removals; the surrounding pipeline logic is
  unchanged.
- Do not add an alias or tolerant branch: `augment()` simply no longer records a
  generation.

## Alternatives considered
N/A: the Plan fixes removal; keeping a zeroed generation would contradict Option B.

## Implementation
### Target file
`scripts/rag/pipeline.py`
### Procedure
- Remove `from rag.identity_gate import compute_local_identity` (import line).
- Remove the `SCHEMA_VERSION` module constant and its comment block.
- Remove the `self._last_corpus_generation` attribute in `__init__`.
- Remove the compute block in `augment()` that assigns `self._last_corpus_generation`.
- Remove the `diagnostics["corpus_generation"] = getattr(...)` append in `get_diagnostics()`.
### Method
Five localized deletions; verify no remaining reference to each removed symbol after editing.
### Details
- After removing the append, `get_diagnostics()` returns the same shape minus one key;
  `tests/rag/test_diagnostics.py` was verified not to pin `corpus_generation`, so no test
  edit is needed for this file.
- `SCHEMA_VERSION` removal must be confirmed against the server document so both go together.

## Compatibility considerations
N/A: the MCP response stops carrying `corpus_identity` via the sibling server document; no
wire compatibility key is kept.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "SCHEMA_VERSION|_last_corpus_generation|corpus_generation|compute_local_identity" scripts/rag/pipeline.py` returns nothing.
  (Scoped to this file: `scripts/rag/identity_gate.py` legitimately still matches until the
  release-unit documents remove it in phase 6.)
- `uv run pytest tests/rag` passes.

## Completion criteria
None of the five symbols remain in `pipeline.py`; `RagPipeline.augment()` runs without
computing an identity; the RAG diagnostics tests pass.

## Out of Scope
The MCP server identity view (`REQ-003`), the ingester bump call (`REQ-004`), and the
`SearchDiagnostics` model field (sibling document, seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-095937 | 20261113-100523 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113-100523 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113-100523 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113-100523 |  |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `scripts/rag/pipeline.py`
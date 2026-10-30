# Implementation Procedure: `scripts/rag/models_result.py` (RAGCORPUS001 Phase 3)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-004)

## Goal
Add the recorded corpus generation (and degraded marker) to the result/diagnostics
models, extending ADR-010 INV-06 result-source tracking.

## Scope
- `class ResultSource(StrEnum)` `:21`; `HttpResultKind` `:29`;
  `class SearchDiagnostics` `:101` with `result_source: ResultSource` at `:109` and the
  "Remote mode fields (new)" comment block `:108-113` (file is 113 lines).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `SearchDiagnostics` gains `corpus_generation: int | None = None` (new) and
  `identity_degraded: bool = False` (new), appended after the existing remote-mode
  fields.
- `scripts/rag/diagnostics.py` (`SearchDiagnostics` wrapper `:23`, `to_dict` `:31`,
  `PipelineDiagnostics` `:55`/`to_dict` `:70`, `from_run_result` `:124`) is Reference
  Files only — its `to_dict` serialization must surface the two new fields; if
  `to_dict` enumerates fields explicitly, that enumeration lives in diagnostics.py and
  cannot be edited under this frozen table. Resolution (Needs Confirmation, recorded in
  doc 08): prefer deriving `to_dict` output from the dataclass fields so no diagnostics.py
  edit is needed; if an explicit enumeration exists there, raise the frozen-table gap
  before implementing rather than editing an unlisted file.
- Log line: the pipeline logs `corpus_generation` on every accepted result (REQ-004) —
  the logging call itself lands in doc 08.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Append the two defaulted fields to `SearchDiagnostics`.
2. Verify `scripts/rag/diagnostics.py:31` `to_dict` behavior against the new fields; if
   it is dataclass-driven, no further action; otherwise record the gap as a blocker.

## Compatibility considerations
**Dependencies**: upstream: doc 08 (gate decisions feed diagnostics), doc 12 is this row
**Blocks**: docs 18, 23

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/rag/test_pipeline_http_result_kind.py` (doc 18: generation
  recorded on each result kind).

## Completion criteria
- Every accepted RAG result's diagnostics carry the generation used; degraded gate
  results carry `identity_degraded=True`; no existing field changed.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_08_scripts_rag_pipeline.py.md` | 1 (dependency) | Procedure | Pending | — | — |
| `20261030-140156_12_scripts_rag_models_result.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `corpus_generation`, `identity_degraded` (Contract section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 12
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/rag/models_result.py`

# RAG docs content policy cleanup (batch 2)

## Priority
Medium

## Summary
Remove the mechanically-derivable content flagged by `tools/check_docs_content_policy.py`
(`GV-021`) in four RAG design documents — plain field/type/default tables and
code-fallback-vs-operational-value comparisons — per `skills/DESIGN.md` Docs content
policy — remove/retain.

## Background
`docscope1`/`docscope2` (see `issues/done/`) established the Docs content policy and the
`check_docs_content_policy.py` detection tool. A prior batch of RAG cleanup issues
(`issues/done/20260905-153715_dcp005_rag_docs_content_policy_cleanup.md` and related
`doccfgtool01`/`doccfgval01` issues dated 2026-09-20) already addressed earlier findings
in this domain, but a fresh run of the tool today still reports new findings in different
sections of the same domain — see Problem.

## Problem
`uv run python tools/check_docs_content_policy.py` (run 2026-09-20) reports the
following unresolved findings in RAG documents:
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md:32` — plain field/type/default
  table header (`PipelineContext` dataclass fields)
- `03_rag_04_02_dto-models_result.md:70`, `:98`, `:107` — plain field/type/default table
  headers (`PipelineExecutionResult`, `SearchDiagnostics` Local/Remote counter tables)
- `03_rag_05_1-configuration-reference.md:93`, `:94`, `:96`, `:99` —
  code-fallback-vs-operational-value comparisons (`top_k_search`, `top_k_rerank`,
  `rag_min_score`, `refiner_max_chars_per_chunk` rows stating both the code default and
  the operational config value in the same cell)
- `03_rag_05_4-error-handling-reference.md:18` — error-handling table (Crawler retry/skip
  behavior)

## Reason for Change
Each finding duplicates a claim whose canonical source is the code or the operational
config file (per `docs/00_governance_01_documentation-policy.md` Claim Type Taxonomy:
`configuration-schema` → the dataclass/TypedDict definition, `production-effective-value`
→ `config/*.toml`). A table cell stating both the code default and the current
operational value (e.g. `03_rag_05_1` line 93) is a directly observed instance of the
drift risk this policy targets: the two numbers must be hand-kept in sync and will go
stale independently.

## Implementation Intent
For each flagged table, apply `skills/DESIGN.md` Avoid implementation-reference
duplication and Docs content policy — remove: replace the field/type/default listing
with a concise reference to the owning dataclass/config file, and keep only the
information that is not code-derivable — cross-field constraints, why a field exists,
what happens when it is empty/unset, and default-value rationale (per Docs content
policy — retain and `skills/DESIGN.md` "No concrete configuration values"). For the
error-handling table in `03_rag_05_4`, keep the failure-mode/severity intent (e.g.
"tokenization errors are non-fatal and skip only the affected chunk") and drop the
literal action strings that just restate a `try/except` branch visible in
`scripts/rag/`.

## Target Files or Areas
- `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `docs/03_rag_04_02_dto-models_result.md`
- `docs/03_rag_05_1-configuration-reference.md`
- `docs/03_rag_05_4-error-handling-reference.md`

## Required Changes
1. `03_rag_03_03`: replace the `PipelineContext` field/type/default table with a pointer
   to `scripts/rag/stage.py::PipelineContext` and retain only the "Modified By" stage
   ownership information (not code-derivable).
2. `03_rag_04_02`: replace the `PipelineExecutionResult` and `SearchDiagnostics`
   (Local/Remote) field tables with pointers to their dataclass definitions; retain the
   prose distinguishing "Always aggregated" vs. "Meaningful only in Remote mode" (design
   intent, not code-derivable).
3. `03_rag_05_1`: remove the four code-fallback-vs-operational-value comparison cells;
   state once, in prose, that code defaults and operational config values may differ and
   point to the config file as canonical for the current value.
4. `03_rag_05_4`: remove the literal error-handling action column entries that restate
   visible `try/except` behavior; retain the severity/continuation intent (fatal vs.
   non-fatal, skip-unit granularity).
5. Re-run `uv run python tools/check_docs_content_policy.py` and confirm zero findings
   for these four files.

## Constraints
- Do not alter any other content in these four files beyond the flagged
  tables/comparisons and their immediately surrounding prose.
- Do not remove the "Modified By" / mode-applicability distinctions called out in
  Implementation Intent — those are design intent, not mechanical restatement.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero findings for the four
  files in Target Files or Areas.
- Each edited section still reads coherently and states what governs the current value
  (dataclass or config file) instead of the value itself.
- `uv run python tools/check_docs_structure.py docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md docs/03_rag_04_02_dto-models_result.md docs/03_rag_05_1-configuration-reference.md docs/03_rag_05_4-error-handling-reference.md` passes.

## Testing Expectations
Documentation-only change. Run `uv run python tools/check_docs_content_policy.py`,
`uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`
(scoped to the four files), and
`uv run python tools/check_docs_consistency.py --domain rag`. No `pytest`/`mypy`/`ruff`
run required.

## Documentation Impact
Yes — this issue is itself a documentation cleanup. No `docs/*.md` outside the four
listed files should need changes.

## Out of Scope
- Any RAG document not listed in Target Files or Areas.
- The `03_rag_05_1-configuration-reference.md` `sqlite_busy_timeout_ms`/`llm_url`/
  `embed_url`/etc. rows that were not flagged by the tool run cited in Problem — leave
  them as-is unless a separate finding covers them.
- Extending `check_docs_content_policy.py`'s detection rules — file a separate issue if
  a new pattern is identified during implementation.

## Dependencies
N/A: none — independent of the MCP/Agent/EventBus/Shared batches filed alongside this
issue (different files, no shared edit surface).

## Unresolved Questions
N/A: none — each finding above was confirmed by a direct tool run and file read on
2026-09-20.

## AI Implementation Instruction
Process the four files independently, one at a time. For each: read the flagged
line(s) and enough surrounding context to preserve meaning, replace the
mechanically-derivable listing with a canonical-source pointer, keep any
non-code-derivable intent noted in Implementation Intent, then re-run
`tools/check_docs_content_policy.py` scoped mentally to that file before moving to the
next. Do not touch files outside Target Files or Areas. Stop and report if a flagged
table also contains content that Docs content policy — retain would keep intact (do not
delete it along with the mechanical part).

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-154305
- **Related target files**: see Target Files or Areas above

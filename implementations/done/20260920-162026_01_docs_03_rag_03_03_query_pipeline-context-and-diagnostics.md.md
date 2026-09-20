## Goal
Replace the `PipelineContext` field/type/default table (lines 32-42) in
`docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` with a pointer to
`scripts/rag/stage.py::PipelineContext`, per `REQ-001` (Plan
`plans/20260920-155829_plan.md`), so `tools/check_docs_content_policy.py` reports no
finding at this table's location while the "Modified By" stage-ownership content is
preserved as prose.

## Scope
In scope: the `## 4. PipelineContext Dataclass` section's field table (lines 32-42)
only. Out of scope: everything else in this file, including the `### 4.2
SearchDiagnostics` (lines 44-59) and `### 4.3 get_diagnostics() Return Value` (lines
61-97) sections, neither of which was flagged by `check_docs_content_policy.py` and
neither of which this Plan's `REQ-001` covers.

## Assumptions
The finding at line 32 and the table's exact current content (re-verified via Read
during this document's creation, matching the Plan's own Step 2/Step 3 findings
unchanged) have not shifted since the Plan was frozen — no commit has touched this file
since.

## Design decisions
Replace the table with a one-sentence pointer to the dataclass, followed by a bullet
list restating each stage-populated field's owning stage — preserving the exact
"Modified By" information (including `search_diagnostics`'s multi-clause
`dataclasses.replace()` explanation) as prose rather than table cells, since a bullet
list carries the same information without the `| Field | Type | Default | Modified By
|` header pattern `check_docs_content_policy.py` flags. Per `skills/DESIGN.md` Avoid
implementation-reference duplication, the field/type/default columns (which are fully
code-derivable) are dropped entirely in favor of the pointer.

## Alternatives considered
- Keep the table shape but replace each `Type`/`Default` cell with `"see
  stage.py"`: rejected — the table still restates every field name and the
  `_FIELD_TYPE_TABLE_HEADER_RE` pattern would likely still match the header row,
  reproducing the same finding.
- Remove the table with no pointer at all: rejected — this would lose the
  "Modified By" design-intent information the Plan's Constraints explicitly require
  retaining (per `skills/DESIGN.md` Docs content policy — retain).

## Implementation
### Target file
`docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`

### Procedure
1. Read lines 26-42 of `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` to
   confirm the current table content is unchanged from the Plan's recorded evidence.
2. Replace lines 28-42 (the code block and the field table) with:
   - The unchanged `ctx = PipelineContext(...)` example code block (keep as-is — it is
     a usage illustration, not a field listing, and was not flagged).
   - A sentence stating that `PipelineContext`'s fields and defaults are defined in
     `scripts/rag/stage.py::PipelineContext`.
   - A bullet list, one bullet per stage-populated field (`queries`, `search_results`,
     `merged`, `reranked`, `augment_result`, `stage_results`, `search_diagnostics`),
     each stating exactly which stage/method writes it, preserving the current table's
     "Modified By" column text verbatim (including the full `search_diagnostics`
     multi-sentence explanation covering both the `SearchStage` population and the
     HTTP-mode `dataclasses.replace()` behavior).
   - Do not create a bullet for `query`/`history_context` (their "Modified By" column
     is `—`, meaning no stage-ownership information exists to preserve).
3. Leave the `### 4.2 SearchDiagnostics` heading and everything from line 44 onward
   unchanged.

### Method
Single localized `Edit`, replacing the exact `old_string` spanning the code block
through the end of the table (lines 28-42) with the `new_string` described in Procedure
step 2. Do not touch any line outside this range.

### Details
The "Modified By" cell for `search_diagnostics` currently reads: "`SearchStage` —
Replaced by a new `SearchDiagnostics` object containing populated
`embed_ok`/`embed_failed`/`fts_errors` during search; In HTTP mode, the HTTP augment
handler replaces it using `dataclasses.replace()` with `result_source`,
`http_result_kind`, `remote_status_code`, and `remote_latency_ms`." — this exact text
(only reformatted from a table cell into a bullet, not summarized or shortened) MUST
carry over, since it is the specific design-intent content
`skills/DESIGN.md` Docs content policy — retain protects (not code-derivable: it
explains *how* and *when* the field is replaced, not just its type/default).

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
`N/A: no security-relevant content is touched — the flagged table is a field/type/default
listing, not security-boundary or fail-safe-default content`.

## Rollback considerations
Revert via `git checkout` on this one file. The edit is a single localized replacement,
independently revertable without affecting any other file in the Plan.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` (Plan `AC-1`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm the
  pre-existing "Content similarity detected" warning (recorded in the Plan's Scope as
  out-of-scope and pre-existing) is unaffected and no new warning appears.
- `uv run python tools/check_docs_structure.py docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`
  — confirm it passes.
- `uv run python tools/check_docs_consistency.py --domain rag` — confirm no new drift
  finding.

## Completion criteria
The `## 4. PipelineContext Dataclass` section no longer contains a `| Field | Type |
Default | Modified By |` table; it instead states the canonical source
(`scripts/rag/stage.py::PipelineContext`) and preserves every stage-ownership fact from
the former "Modified By" column as prose; `check_docs_content_policy.py` reports zero
findings for this file.

## Out of scope
- `### 4.2 SearchDiagnostics` and `### 4.3 get_diagnostics() Return Value` sections of
  this same file (not flagged; not part of `REQ-001`).
- Any other `docs/*.md` file — see the Plan's other three target-file rows
  (`REQ-002`/`REQ-003`/`REQ-004`), each with its own implementation procedure document.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-165501 | 20260920-165501 | Step 2.5 stale_detector.py flagged 4 false positives (old_string/new_string/Edit/other-file symbol references, not actual target-file symbols) - manually verified and confirmed non-blocking; docs/03_rag_03_03...md's PipelineContext table replaced with canonical-source pointer |
| 2 | Add or update tests per Validation plan | Completed | 20260920-165501 | 20260920-165501 | N/A: documentation-only, no automated test beyond the doc checkers already listed check_docs_content_policy.py: zero findings for this file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-165501 | 20260920-165501 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) N/A: documentation-only change, no scripts/ validation sequence applicable |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-165501 | 20260920-165501 | N/A: this document IS the documentation change N/A: this document IS the documentation change; check_docs_structure.py passed, pre-existing Content similarity warning unaffected |

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
- **Requirement ID**: `REQ-001` — replace the `PipelineContext` field table with a canonical-source pointer
- **Source issue**: issues/20260920-154305_dcp009_rag-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-155829_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-162026
- **Related target files**: docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md
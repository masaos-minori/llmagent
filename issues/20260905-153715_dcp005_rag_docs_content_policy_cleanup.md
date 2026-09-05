# Remove class/function index tables and residual listings from RAG docs

## Priority
Medium

## Summary
Remove class/function/method index tables and remaining file-tree/location-
mapping findings from the RAG domain documents:
`docs/03_rag_01_system_overview.md`,
`03_rag_02_04_ingestion_pipeline-ingester.md`,
`03_rag_02_05_ingestion_pipeline-document-manager.md`,
`03_rag_02_06_ingestion_pipeline-supporting-components.md`,
`03_rag_02_07_ingestion_pipeline-utils.md`, and
`03_rag_02_08_ingestion_pipeline-shared.md`, per `skills/DESIGN.md` Docs
content policy — remove/retain.

## Background
`docscope1`/`docscope2` (in `issues/done/`) established the policy and the
`check_docs_content_policy.py` detection tool (`GV-021`). Their own evidence
section already named `03_rag_02_08_ingestion_pipeline-shared.md`'s "Public
Functions" table as a concrete class/function-index violation example.

## Problem
`uv run python tools/check_docs_content_policy.py` reports 13 findings
across six files: `03_rag_01_system_overview.md` (5),
`03_rag_02_04_ingestion_pipeline-ingester.md` (2),
`03_rag_02_05_ingestion_pipeline-document-manager.md` (2),
`03_rag_02_07_ingestion_pipeline-utils.md` (2),
`03_rag_02_06_ingestion_pipeline-supporting-components.md` (1), and
`03_rag_02_08_ingestion_pipeline-shared.md` (1). Concretely,
`03_rag_02_08_ingestion_pipeline-shared.md`'s "## 9. Pipeline Utils" section
has a "**Public Functions**" `| Function | Signature | Description |` table
cataloging `pipeline_utils.py`'s exported functions, and a
"**Module-level Constants**" table doing the same for constants — both are
class/function-index content the policy targets. The same section's
"**TypedDict**" table describing `ChunkJsonRaw`'s fields is a closely
related pattern (a field-catalog table for a specific symbol) that should be
reviewed against the same policy even though it is not a function/method
signature table per se.

## Reason for Change
Function-signature and constant-value tables duplicate what the module's
own docstrings/type annotations already state authoritatively, and go stale
on every signature change or added/removed constant — the same failure mode
`skills/DESIGN.md` "Class/function/method signature-and-description index
table" names explicitly.

## Implementation Intent
Remove each Public Functions / Module-level Constants / signature-index
table. Where the surrounding prose already states the module's purpose and
design intent (e.g. `03_rag_02_08`'s "## 8. Chunk Japanese Mixin" "Module
Overview" paragraph describing `ChunkJapaneseMixin`'s morphological-analysis
responsibility), keep that prose — it is retain-category content (component
responsibility) already correctly written, not affected by this cleanup.
Replace a removed table with, at most, a one-sentence pointer to the source
file for exhaustive signature detail, per `skills/DESIGN.md` Avoid
implementation-reference duplication.

## Target Files or Areas
- `docs/03_rag_01_system_overview.md`
- `docs/03_rag_02_04_ingestion_pipeline-ingester.md`
- `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`
- `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`
- `docs/03_rag_02_07_ingestion_pipeline-utils.md`
- `docs/03_rag_02_08_ingestion_pipeline-shared.md`

## Required Changes
1. Remove `03_rag_02_08_ingestion_pipeline-shared.md`'s "Public Functions"
   and "Module-level Constants" tables under "## 9. Pipeline Utils",
   replacing them with a one-sentence pointer to `pipeline_utils.py`.
2. Review the same file's "TypedDict" field-catalog table for `ChunkJsonRaw`
   against the same policy and remove/compress it if it is a
   signature-and-description index in substance.
3. Read and resolve the remaining findings in
   `03_rag_01_system_overview.md` (5),
   `03_rag_02_04_ingestion_pipeline-ingester.md` (2),
   `03_rag_02_05_ingestion_pipeline-document-manager.md` (2), and
   `03_rag_02_07_ingestion_pipeline-utils.md` (2), applying the same
   remove/replace pattern for genuine index-table or file-tree/location-
   mapping content.
4. Preserve every existing module-purpose/design-intent prose paragraph
   (e.g. "## 8. Chunk Japanese Mixin" "Module Overview") unchanged.

## Constraints
- Do not remove a module-purpose prose paragraph that is not itself a
  table/index (only the tabular signature-catalog content is in scope).
- Do not alter `03_rag_02_01_ingestion_pipeline-overview.md`,
  `-02_...-crawler.md`, `-03_...-chunksplitter.md`, or `-09_...-shared-
  utilities.md` — linked from these files but not flagged, out of scope.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero findings
  for all six target files.
- Every removed table is replaced by a pointer sentence to its source file,
  not silently deleted with no trace.
- Existing module-purpose/design-intent prose is unchanged.
- `uv run python tools/check_docs_consistency.py --domain rag` passes.

## Testing Expectations
Documentation-only change. Run
`uv run python tools/check_docs_content_policy.py`,
`uv run python tools/check_docs_structure.py docs/03_rag_01_system_overview.md
docs/03_rag_02_04_ingestion_pipeline-ingester.md
docs/03_rag_02_05_ingestion_pipeline-document-manager.md
docs/03_rag_02_06_ingestion_pipeline-supporting-components.md
docs/03_rag_02_07_ingestion_pipeline-utils.md
docs/03_rag_02_08_ingestion_pipeline-shared.md`, and
`uv run python tools/check_docs_consistency.py --domain rag`. No
`pytest`/`mypy`/`ruff` run required.

## Documentation Impact
Yes — this issue's deliverable is the table removal/replacement described
above across the six listed files.

## Out of Scope
- `03_rag_02_01`, `-02`, `-03`, `-09` (linked, not flagged).
- Any file outside the RAG domain (tracked in `dcp002`–`dcp004`, `dcp006`).

## Dependencies
N/A: none. Independent of `dcp001`–`dcp004`, `dcp006`.

## Unresolved Questions
N/A: none — every finding in this domain is a straightforward
index-table/file-tree removal.

## AI Implementation Instruction
Remove only tabular signature/constant/field-catalog content; do not touch
prose module-purpose paragraphs in the same sections. Replace each removed
table with a single pointer sentence to the source file, not a longer
substitute listing. Run `tools/check_docs_content_policy.py` after each
file to confirm zero findings before moving to the next.

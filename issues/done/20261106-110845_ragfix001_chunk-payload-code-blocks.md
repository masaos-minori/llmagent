# Chunk artifact payloads omit the code_blocks key required by the chunk validator

## Priority
High

## Summary
`ChunkSplitter` writes chunk JSON payloads that lack the `code_blocks` key, while
`read_chunk_json` enforces an exact key-set check that requires it. Every ChunkSplitter
output file therefore fails validation and is silently skipped by `ChunkGroupingStrategy`,
so ingestion writes zero documents from chunk files. Fix the producer/validator contract so
chunk payloads and the validator agree.

## Background
Found during adversarial verification of
`issues/20261106-073538_raging004_force-rechunk-stale-chunks.md` (recorded as UNK-01 in
`plans/20261106-101257_raging004_force-rechunk-stale-chunks.md`). Reproduction at HEAD
`bdb9bed66`: a forced re-chunk run wrote 20 chunk files; `ChunkGroupingStrategy.group`
produced 0 URL groups because every file raised `ChunkFormatError` on the missing key.
The canonical artifact-field contract (chunk payloads carry `code_blocks`) is documented in
the chunksplitter doc's cross-field rules discussion (see archived
`issues/done/20260913-183022_missing_pipeline_utils_cross_field_rules.md`). Existing tests
do not catch the mismatch because their harnesses hand-write chunk payloads that include
`code_blocks`, bypassing the real `ChunkSplitter` writer.

## Problem
- `ChunkSplitter._extract_chunk_metadata` (`scripts/rag/ingestion/chunk_splitter.py:263-277`)
  emits 8 document-level keys and `_build_chunk_payload` (`:278-296`) adds only
  `chunk_index`, `chunk_type`, `content`, `normalized_content` (plus the 3 envelope keys) —
  `code_blocks` is never written.
- `read_chunk_json` (`scripts/rag/ingestion/pipeline_utils.py:164-182`) requires an exact
  key set that includes `code_blocks` and raises `ChunkFormatError` on any missing key.
- `ChunkGroupingStrategy.group` (`scripts/rag/ingestion/chunk_grouping.py:30`) catches
  `ChunkFormatError` per file and skips it — 100% of ChunkSplitter output is silently
  dropped at ingestion; a chunking run appears to succeed ("chunked N chunks") while the
  ingester persists nothing.

## Reason for Change
Correctness and data-integrity: file-based ingestion currently produces no documents at all
from real ChunkSplitter output, with no error surfaced. The corruption path that
`plans/20261106-101257_raging004_force-rechunk-stale-chunks.md` designs against (stale
chunk residue) also only becomes reachable once payloads validate, so this fix gates that
plan's real-world effect.

## Implementation Intent
Make the producer satisfy the documented canonical contract: the chunk payload builder emits
`code_blocks` (empty list `[]` for text-split chunks; document-level code blocks where a
future code-chunk path supplies them) so payloads pass `read_chunk_json` unchanged. Prefer
fixing the producer over relaxing the validator — the validator's exact key-set check is the
documented contract. End-to-end coverage (ChunkSplitter output fed to the ingester through
`group()`) must replace hand-written payload reliance.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_splitter.py` (payload builder / metadata)
- `scripts/rag/ingestion/pipeline_utils.py` (reference only unless the contract decision goes the other way)
- `tests/rag/ingestion/` — chunk_splitter payload tests, ingester/grouping end-to-end tests

## Required Changes
- Add `code_blocks` to the chunk JSON payload written by `ChunkSplitter` (`[]` for the current
  text/heading chunk paths; preserve the crawl document's code-block content where the design
  chooses to carry it into chunks).
- Add a payload key-set pin test asserting ChunkSplitter-written files pass `read_chunk_json`
  (current writer output, not hand-written fixtures).
- Add at least one end-to-end regression test: ChunkSplitter `process_file` output →
  `ChunkGroupingStrategy.group` returns non-empty groups → ingester persists documents.
- Check docs state of the canonical contract (`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
  artifact-field section) and align it with the fixed behavior.

## Constraints
- Do not weaken `read_chunk_json`'s exact key-set check or its unknown-key rejection.
- Keep the envelope keys (`schema_version`, `artifact_type`, `created_by`) handling unchanged.
- Chunk payloads already consumed by `is_already_processed` and the 9-field group signature
  (`chunk_type`, `chunking_strategy`, etc.) must keep their current values — only the missing
  key is added.
- Do not change the crawl artifact contract (`read_crawl_json` already requires `code_blocks`
  and the crawler writes it).

## Acceptance Criteria
- ChunkSplitter-written chunk files pass `read_chunk_json` (key-set pin test).
- `ChunkGroupingStrategy.group` returns a non-empty group from real ChunkSplitter output
  (end-to-end test).
- Ingestion of a ChunkSplitter-produced directory persists documents (regression test).
- Full `uv run pytest tests/rag/ingestion` passes with no regression.

## Testing Expectations
- Unit: payload key-set equality against `read_chunk_json`'s required set using the real
  writer.
- Integration/regression: ChunkSplitter → group → ingest pipeline test (currently impossible
  to write green against the broken contract — expect RED before the fix).
- Run targeted tests, then `uv run pytest tests/rag/ingestion` per `rules/toolchain.md`.

## Documentation Impact
Verify the chunk artifact-field contract description in
`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` matches the fixed payload shape;
update only if it currently describes the broken behavior. No new implementation-derived
details (per `skills/DESIGN.md` docs policy).

## Out of Scope
- Carrying per-chunk code-block content into chunk payloads with non-empty values (future
  code-chunk feature; this issue only closes the key contract, empty list allowed).
- Changing `code_blocks` semantics in crawl artifacts.
- The stale-chunk pruning behavior designed in
  `plans/20261106-101257_raging004_force-rechunk-stale-chunks.md` (separate, already planned).

## Dependencies
- `plans/20261106-101257_raging004_force-rechunk-stale-chunks.md` — co-targets
  `scripts/rag/ingestion/chunk_splitter.py` (write-loop region `:249-261` vs payload-builder
  region `:278-296`; disjoint). This issue should be implemented after the 004 Plan to keep
  same-file edits serialized; 004's payload-defect note (UNK-01) is resolved by this issue.
  depends on ordering: 004 Plan → this issue.
- `plans/20261106-095808_raging003_recrawled-chunk-group-poisoning.md` — its tests construct
  hand-written chunk payloads because of this defect; after this fix they may optionally use
  real ChunkSplitter output. No blocking order; blocks: this issue makes 003's corruption
  path reachable in production.

## Unresolved Questions
- Whether `code_blocks` in a chunk payload should stay `[]` always or carry the parent
  document's code blocks per chunk — contract wording (cross-field rule "empty content
  requires non-empty code_blocks") applied to chunks suggests carrying them for code-region
  chunks, but no code-chunk writer exists today. Needs confirmation against
  `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`'s canonical field table during
  planning.

## AI Implementation Instruction
Fix the producer (payload builder), not the validator. Keep the diff to the payload-builder
metadata and tests; do not alter chunk selection, splitting, or group-signature fields. Add
the end-to-end test that is currently impossible against the broken contract. Stop and report
if the docs' canonical table contradicts the empty-list choice.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-101257_raging004_force-rechunk-stale-chunks.md` (UNK-01)
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-110845
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`,
  `scripts/rag/ingestion/pipeline_utils.py`, `tests/rag/ingestion/`

# Align the RAG artifact contract documentation with strict reader behavior

## Priority
High

## Summary
The production RAG ingestion flow uses `read_crawl_json()` for crawler artifacts and
`read_chunk_json()` for chunk artifacts, both of which reject missing/invalid fields with
`ChunkFormatError`. Several Specification documents still describe the former permissive
`read_json_file()` reader's fallback behavior (`lang = "en"` default, `chunk_index = 0`
default, empty-string fallback for `source_file`/`chunk_type`) as if it were current, and do
not consistently distinguish a missing key from an explicit `null` or an empty value.

## Background
The strict-reader migration itself is implemented and code-side documentation was already
addressed by `issues/done/20260819_02_issue.md` ("Replace permissive RAG payload handling
with strict crawl and chunk contracts"). That issue's `Documentation Impact` was limited to
docstrings; it did not update the `docs/03_rag_*.md` Specification set. This issue covers the
remaining Specification-level documentation only.

## Problem
Documentation describing `read_json_file()`'s lenient fallback behavior as current can lead
developers or AI agents to conclude that incomplete legacy artifacts are still supported by
the production ingestion path, or that new artifact producers may emit incomplete payloads.
Required/Nullable/Conditional field classification is also inconsistent across documents, and
crawler-artifact fields are not clearly separated from chunk-artifact fields.

## Reason for Change
Ambiguity between current strict-reader behavior and former lenient-reader behavior increases
the risk that obsolete parsing assumptions are reintroduced, or that new artifact producers
rely on outdated fallback documentation.

## Implementation Intent
Establish one clear, canonical artifact contract based on current strict-reader behavior:
crawler artifacts via `read_crawl_json()`, chunk artifacts via `read_chunk_json()`, missing
required fields and invalid types rejected with `ChunkFormatError`, Required/Nullable/
Conditional fields explicitly distinguished, missing keys distinguished from explicit `null`
or empty values, and historical lenient-reader behavior retained only in Migration History.

## Target Files or Areas
- `docs/03_rag_01_system_overview.md`
- `docs/03_rag_02_01_ingestion_pipeline-overview.md`
- `docs/03_rag_02_02_ingestion_pipeline-crawler.md`
- `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `docs/03_rag_02_04_ingestion_pipeline-ingester.md`
- `docs/03_rag_02_08_ingestion_pipeline-shared.md`
- `docs/03_rag_04_01_dto-models_data.md`
- `docs/03_rag_05_4-error-handling-reference.md`
- `docs/03_rag_05_5-constraints-reference.md`
- `docs/03_rag_90_inconsistencies_and_known_issues.md`
- Reference for current behavior (do not modify): `scripts/rag/ingestion/` readers, `ChunkDocument` DTO

## Required Changes
- Find every documentation reference to `read_json_file()` and its fallback behavior.
- Remove descriptions that present `read_json_file()` as a supported production reader.
- Remove legacy fallback tables from current specifications.
- Document `read_crawl_json()` as the canonical reader for crawler artifacts, and state that `ChunkSplitter` uses it.
- Document `read_chunk_json()` as the canonical reader for chunk artifacts, and state that `RagIngester` uses it.
- Document that missing required fields and invalid types result in `ChunkFormatError`.
- Document `chunk_index` as a non-negative integer without implicit conversion from strings or booleans.
- Separate crawler-artifact fields from chunk-artifact fields; classify each as Required, Nullable, or Conditional.
- Distinguish missing keys, explicit `null` values, and empty values.
- Document the non-empty requirements for `url` and `content`, and the supported `lang` values (`en`, `ja`).
- Explain why `etag`, `last_modified`, and `normalized_content` may be `null`.
- Confirm and document whether `title` and `source_file` may be empty, and the allowed values for `chunk_type`/`chunking_strategy`.
- Select one canonical document for the complete artifact-field contract; replace duplicated field tables elsewhere with links to it.
- Move necessary legacy-reader descriptions to Migration History or Change History.
- Update the related Known Issue entry and mark it resolved once documentation and implementation agree.

## Constraints
Documentation-only. Do not modify `scripts/rag/ingestion/` reader implementations, remove the
obsolete reader from source code, or change test files as part of this issue.

## Acceptance Criteria
- No current specification identifies `read_json_file()` as a supported production path.
- Crawler and chunk artifact contracts are documented separately.
- Required, Nullable, and Conditional have consistent meanings across all affected documents.
- Missing keys are clearly distinguished from explicit `null` and empty values.
- Reader, DTO, `ChunkSplitter`, and `RagIngester` documentation are consistent with each other.
- The complete artifact-field contract has one canonical source; other documents link to it.
- Legacy-reader information appears only in clearly marked historical sections.

## Testing Expectations
Not required — documentation-only change with no behavior impact. Verify with
`uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_consistency.py --domain rag`.

## Documentation Impact
Yes — this issue's entire scope is the `docs/03_rag_*.md` Specification set listed above.
Keep additions to design intent, responsibility boundaries, and field classification; do not
duplicate implementation-level parsing logic already covered by source code and docstrings
(`issues/done/20260819_02_issue.md`'s prior scope).

## Out of Scope
- Source-code removal of the obsolete `read_json_file()` reader.
- Test changes.
- Artifact migration or regeneration of existing stored artifacts.
- Making `schema_version`, `artifact_type`, or `created_by` mandatory.

## Dependencies
`issues/done/20260819_02_issue.md` already implemented the strict-reader behavior this issue
documents — this issue depends on that implementation being current and does not change it.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Read the current reader implementations and `ChunkDocument` DTO in full before editing any
document, to confirm exact field requirements rather than trusting this issue's restatement.
Keep edits to design intent and field-contract description; do not restate implementation
logic. If a field's Required/Nullable/Conditional classification cannot be confirmed from
code, mark it `Needs Confirmation` rather than guessing.

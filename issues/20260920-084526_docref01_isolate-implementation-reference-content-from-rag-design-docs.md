# Isolate implementation-reference content from RAG design docs

## Priority
Medium

## Summary
Several `docs/*.md` design documents embed exhaustive implementation-reference
content — TypedDict field lists, DTO attribute tables, method signature catalogs,
full JSON payload examples, CLI argument tables, and per-exception handling tables —
that `skills/DESIGN.md`'s existing "Avoid implementation-reference duplication"
policy already prohibits. Remediate these documents by moving this content to its
proper canonical source and retaining only design-intent information.

## Background
`skills/DESIGN.md`'s "Avoid implementation-reference duplication" section already
states: "do not copy exhaustive file lists, method catalogs, DTO/config-key field
tables, or long command/JSON examples into the document — recommend or write a
concise, evidence-grounded summary instead, and point to the source for exhaustive
detail." Confirmed via direct inspection that at least one live document violates
this: `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` contains a full
`TypedDict` field enumeration (`CrawlJsonPayload`/`ChunkJsonPayload`/`ChunkMetadata`),
a full example JSON payload, a CLI argument table, a per-case error-handling table,
and a section explicitly titled "Canonical Artifact-Field Contract" that
hand-maintains a 13-row field/validator/classification table mirroring
`scripts/rag/ingestion/pipeline_utils.py`'s actual validators (`Evidence: Explicit in
code`). `grep -rl "DocumentManager\|ETagManager\|ChunkSplitter\|WebCrawler" docs/`
finds 17 candidate files that mention these classes; which of the others (beyond
`chunksplitter.md`) actually contain implementation-reference content, versus a
passing mention, has not been individually confirmed (see Unresolved Questions).

## Problem
This kind of content (a) goes stale the moment the underlying type, validator, CLI,
or exception definition changes, since nothing enforces doc/code agreement, and (b)
bloats the RAG-indexed document corpus with implementation detail that duplicates
what code, `--help`, or a schema already answers authoritatively — lowering the
signal-to-noise ratio of retrieved chunks for design-intent queries.

## Reason for Change
Documentation drift risk (these docs restate `TypedDict`/DTO/CLI/exception
definitions with no automated check against the actual code) and RAG corpus quality
(these design documents are themselves the RAG-indexed source; padding them with
implementation reference reduces retrieval quality for design-intent questions).

## Implementation Intent
For each affected document, replace exhaustive implementation-reference content with
a concise pointer to its actual canonical source, following this per-category
guidance:
- TypedDict/DTO field lists → the type definition itself, or a JSON Schema if one
  exists or should exist.
- API/HTTP request-response contracts → OpenAPI or JSON Schema, if one exists or
  should exist.
- CLI argument tables → generated from `--help`, not hand-maintained.
- Python method signatures → generated from docstrings/type annotations, not
  hand-maintained prose.
- DB column listings → DDL or schema-generation code.

Design documents should retain only: what boundary the data model forms, whether it
is an external public contract or an internal DTO, the compatibility range that must
be preserved, whether it may contain sensitive information, whether it is persisted
or ephemeral, and how missing, duplicate, or out-of-order data is handled.

Also expand `skills/DESIGN.md`'s "Avoid implementation-reference duplication"
wording to explicitly name the categories found in practice here (TypedDict field
lists, HTTP request/response examples, CLI argument tables, per-exception handling
tables) alongside its existing "DTO/config-key field tables ... method catalogs ...
command/JSON examples" wording, so the policy is unambiguous for future authors and
for the detection tool tracked in this issue's companion issue (see Dependencies).

## Target Files or Areas
- `skills/DESIGN.md` (Avoid implementation-reference duplication — wording expansion
  only)
- `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` (confirmed: TypedDict
  fields, JSON example, CLI table, exception table, "Canonical Artifact-Field
  Contract" section)
- Other files among: `docs/03_rag_05_2-execution-guide.md`,
  `docs/00_governance_03_issue-and-uncertainty-management.md`,
  `docs/03_rag_02_07_ingestion_pipeline-utils.md`,
  `docs/03_rag_02_08_ingestion_pipeline-shared.md`,
  `docs/03_rag_04_04_dto-models_config.md`, `docs/03_rag_01_system_overview.md`,
  `docs/03_rag_05_4-error-handling-reference.md`,
  `docs/03_rag_02_04_ingestion_pipeline-ingester.md`,
  `docs/03_rag_04_01_dto-models_data.md`,
  `docs/05_agent_09_02_data-layer-access-patterns.md`,
  `docs/03_rag_00_document-guide.md`,
  `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`,
  `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`,
  `docs/adr/ADR-005-rag-source-derived-index-relationships.md`,
  `docs/03_rag_02_02_ingestion_pipeline-crawler.md`,
  `docs/adr/ADR-009-rag-ft5-text-separation.md` — Unknown whether each actually
  contains implementation-reference content; confirm individually before editing
  (see Unresolved Questions).

## Required Changes
- Expand `skills/DESIGN.md` Avoid implementation-reference duplication's category
  list per Implementation Intent above.
- For each file in Target Files or Areas, confirm whether it actually contains
  implementation-reference content (not every `grep` match necessarily does).
- For each confirmed file, replace the implementation-reference content with the
  canonical-source pointer per Implementation Intent, keeping the design-intent
  content listed there.
- Run `tools/check_docs_quality.py` and `tools/check_docs_structure.py` on every
  edited file.

## Constraints
Do not remove design-intent content — only implementation-reference detail (see
Implementation Intent for the retained-content list). Do not change the underlying
code, TypedDicts, DTOs, or CLI behavior — this is a documentation-only issue.

## Acceptance Criteria
- `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` no longer contains a full
  TypedDict field enumeration, a full example JSON payload, a CLI argument table, or
  a hand-maintained field/validator table — each is replaced with a pointer to its
  actual source.
- `skills/DESIGN.md` Avoid implementation-reference duplication explicitly names
  TypedDict field lists, HTTP request/response examples, CLI argument tables, and
  per-exception handling tables.
- `tools/check_docs_quality.py` and `tools/check_docs_structure.py` pass on every
  edited file.

## Testing Expectations
Not required for code (documentation-only, no behavior or public API change). Run
`tools/check_docs_quality.py` and `tools/check_docs_structure.py` on every edited
`docs/*.md` file, and `tools/check_skills_references.py` after editing
`skills/DESIGN.md`.

## Documentation Impact
This issue is itself a documentation change, including to `skills/DESIGN.md`'s own
policy wording (Avoid implementation-reference duplication) — apply `routing.md`'s
Documentation row per `AGENTS.md` Global Rule 10.

## Out of Scope
- Building the detection tool for finding all remaining violations — tracked as a
  separate, companion issue (see Dependencies).
- Any change to the actual TypedDicts, DTOs, CLI argument parsing, or
  exception-handling code.
- Remediating a `docs/*.md` file not yet confirmed to actually contain
  implementation-reference content.

## Dependencies
Complements a companion issue that creates a documentation-implementation-reference
detection tool (filed alongside this one). That tool's output can scope the "Other
files" row above beyond what this issue's own manual `grep` found, but this issue's
`chunksplitter.md` remediation does not require the tool to exist first.

## Unresolved Questions
Which of the 16 other `docs/*.md`/`docs/adr/*.md` files found by `grep -rl
"DocumentManager\|ETagManager\|ChunkSplitter\|WebCrawler" docs/` actually contain
implementation-reference content (versus a passing mention) is not yet confirmed —
the implementer's first step for any file beyond `chunksplitter.md`.

## AI Implementation Instruction
Confirm each target file actually contains implementation-reference content (per
Implementation Intent's five categories) before editing it — do not edit a file
solely because it appeared in the `grep` match list. Keep the diff scoped to
removing/replacing implementation-reference content only; do not restructure
sections that are already design-intent-only. Do not touch source code, TypedDicts,
DTOs, or CLI argument parsing.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-084526
- **Related target files**: skills/DESIGN.md,
  docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md

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

**Adversarial verification note**: the companion tool issue
(`issues/done/20260920-084638_docreftool01_add-a-docs-checker-for-implementation-reference-content.md`)
has since been implemented and merged (`tools/check_docs_content_policy.py` now
detects TypedDict/DTO tables, CLI argument tables, error-handling tables, and full
JSON payload examples). Running it against the full `docs/` tree and cross-checking
its findings against the 16 "Other files" below resolves most of this issue's own
Unresolved Questions with concrete evidence — see the corrected Target Files or
Areas and Unresolved Questions sections. One additional detection gap was found in
the process: the "Canonical Artifact-Field Contract" table in `chunksplitter.md`
itself (header `| Field | Classification | Validator | Notes |`) is *not* caught by
any of the tool's 15 checks — its column shape (no `Type`/`Default` column) does not
match `check_field_type_table`'s pattern. This does not change this issue's own
manual finding for that section (still confirmed by direct reading, per Acceptance
Criteria), but is noted as a residual gap for any future extension of the companion
tool, not something this issue's own scope covers fixing.

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
  fields at line 44, CLI argument table at line 188, full JSON example at line 195,
  error-handling table at line 288 — all four confirmed by
  `tools/check_docs_content_policy.py`; plus the "Canonical Artifact-Field
  Contract" section, confirmed only by direct reading — see Background's
  adversarial-verification note)
- Confirmed via `tools/check_docs_content_policy.py` (run after the companion tool
  issue landed) to contain at least one of this issue's named categories:
  - `docs/03_rag_02_02_ingestion_pipeline-crawler.md` (TypedDict table line 39, CLI
    argument table line 103, error-handling table line 125 — the `WebCrawler` doc
    the source memo named directly)
  - `docs/03_rag_02_04_ingestion_pipeline-ingester.md` (CLI argument tables lines
    146/224, error-handling tables lines 172/250)
  - `docs/03_rag_04_04_dto-models_config.md` (DTO field/type/default tables lines
    20/34/43/54/63)
  - `docs/03_rag_05_4-error-handling-reference.md` (error-handling table line 18)
- No automated finding from `tools/check_docs_content_policy.py` for this issue's
  named categories — spot-check manually before treating as clean, since the tool
  is heuristic and its "Canonical Artifact-Field Contract"-style gap (see
  Background) shows it does not catch every shape: `docs/03_rag_05_2-execution-guide.md`,
  `docs/03_rag_02_07_ingestion_pipeline-utils.md`,
  `docs/03_rag_02_08_ingestion_pipeline-shared.md`, `docs/03_rag_01_system_overview.md`,
  `docs/03_rag_04_01_dto-models_data.md`,
  `docs/agent_09_02_data-layer-access-patterns.md`, `docs/03_rag_00_document-guide.md`,
  `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`,
  `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`,
  `docs/adr/ADR-005-rag-source-derived-index-relationships.md`,
  `docs/adr/ADR-009-rag-ft5-text-separation.md`
- `docs/00_governance_03_issue-and-uncertainty-management.md` — the tool flags 2
  findings here, but both are "default-value restatement outside a table"
  (lines 451/454), a different `skills/DESIGN.md` category not named by this
  issue — not a target for this issue's remediation.

## Required Changes
- Expand `skills/DESIGN.md` Avoid implementation-reference duplication's category
  list per Implementation Intent above.
- For each file in Target Files or Areas, confirm whether it actually contains
  implementation-reference content (not every `grep` match necessarily does).
- For each confirmed file, replace the implementation-reference content with the
  canonical-source pointer per Implementation Intent, keeping the design-intent
  content listed there.
- Run `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, and
  `tools/check_docs_content_policy.py` on every edited file — the last of these
  did not exist when this issue was originally filed, but is now the direct,
  automated check for whether a remediated file still trips this issue's target
  categories (per `routing.md`'s "When to run which tool", added this session).

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
- `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, and
  `tools/check_docs_content_policy.py` pass (report zero findings) on every edited
  file.

## Testing Expectations
Not required for code (documentation-only, no behavior or public API change). Run
`tools/check_docs_quality.py`, `tools/check_docs_structure.py`, and
`tools/check_docs_content_policy.py` on every edited `docs/*.md` file, and
`tools/check_skills_references.py` after editing `skills/DESIGN.md`.

## Documentation Impact
This issue is itself a documentation change, including to `skills/DESIGN.md`'s own
policy wording (Avoid implementation-reference duplication) — apply `routing.md`'s
Documentation row per `AGENTS.md` Global Rule 10.

## Out of Scope
- Further extending the detection tool (`tools/check_docs_content_policy.py`,
  already built and merged via the companion issue — see Dependencies), including
  closing its "Canonical Artifact-Field Contract" detection gap noted in
  Background.
- Any change to the actual TypedDicts, DTOs, CLI argument parsing, or
  exception-handling code.
- Remediating a `docs/*.md` file not yet confirmed to actually contain
  implementation-reference content (the 11 files listed in Target Files or Areas
  with no automated finding).
- `docs/00_governance_03_issue-and-uncertainty-management.md`'s "default-value
  restatement" findings — a different `skills/DESIGN.md` category not named by
  this issue.

## Dependencies
N/A: none remaining. The companion tool issue
(`issues/done/20260920-084638_docreftool01_add-a-docs-checker-for-implementation-reference-content.md`)
that this issue originally depended on for scoping is now implemented and merged —
its output has already been used (see Background/Target Files or Areas) to resolve
this issue's own Unresolved Questions for 15 of the 16 candidate files. No
outstanding dependency blocks this issue's remediation work from proceeding.

## Unresolved Questions
**Mostly resolved by adversarial verification** (see Background note): running the
now-implemented `tools/check_docs_content_policy.py` against all 16 other
`docs/*.md`/`docs/adr/*.md` candidates confirms 4 of them contain at least one of
this issue's named categories (see Target Files or Areas) and shows no automated
finding for the remaining 11. The 11 with no finding are not proven clean — the
tool is heuristic and known to miss at least one table shape (the
"Canonical Artifact-Field Contract" pattern) — so a manual spot-check remains the
implementer's first step for any of those 11 specifically, but the 4 confirmed
files no longer need that initial confirmation step.

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

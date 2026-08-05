# Implementation Procedure: 03_rag_02_02_ingestion_pipeline-crawler-part2.md

## Goal
- Remove duplicated content from `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md`
  by replacing the "### 2.4 出力JSON形式" section with a reference to
  `docs/03_rag_04_01_dto-models_data.md`, and the "### 2.6 ロギング" section with a
  reference to `docs/03_rag_05_3-logging.md`, per `plans/20260802-185027_plan.md`.

## Scope
- In scope: replace the two named subsections' body content with a one-line
  cross-reference each; update `related`/`Related Documents` front-matter only if the
  new reference targets are not already listed.
- Out of scope: content of `docs/03_rag_04_01_dto-models_data.md` (handled in a separate
  document for that target file) and `docs/03_rag_05_3-logging.md` (explicitly
  out-of-scope per the plan).

## Assumptions
- The JSON example currently duplicated in this file is the same content already
  canonicalized in `docs/03_rag_04_01_dto-models_data.md` (plan Assumption #2).
- A single-line pointer ("詳細は ... を参照。") is sufficient to replace each section body,
  matching the style already used elsewhere in this file (e.g. section 2.7's reference to
  `03_rag_05_1-configuration-reference.md`).

## Design decisions
- Keep both subsection headings ("2.4 出力JSON形式", "2.6 ロギング") in place and only
  replace their body text with a reference line, rather than deleting the headings —
  preserves the document's existing section numbering/ToC structure and any external
  anchors/links that target these headings.
- Use the same reference-line phrasing pattern already established in section 2.7
  (`[label](relative-path.md) を参照。`) for consistency within the same file.

## Alternatives considered
- Delete the subsections entirely (no heading, no reference): rejected — breaks
  section numbering continuity (2.3 → 2.5/2.7) and removes a discoverable pointer for
  readers who land on this file first.
- Replace with a full re-explanation instead of a reference: rejected — reintroduces the
  duplication the plan explicitly aims to remove.

## Implementation
### Target file
- `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md`

### Procedure
1. Locate "### 2.4 出力JSON形式" (heading) and its body.
2. Replace the body with: reference line pointing to
   `docs/03_rag_04_01_dto-models_data.md`.
3. Locate "### 2.6 ロギング" (heading) and its body.
4. Replace the body with: reference line pointing to `docs/03_rag_05_3-logging.md`.
5. Confirm `related` front-matter already lists both target docs; add entries only if
   missing.

### Method
- Manual documentation edit (no code generation, no scripts/ changes).

### Details
- Investigated via `grep -n '^#'` on the file (headings at lines 77, 81, 90, 94) and a
  targeted `Read` of lines 77-100.
- Finding (evidence, not assumption): the target file **already contains** the reference
  line under "### 2.4 出力JSON形式" (line 79: `詳細は [docs/03_rag_04_01_dto-models_data.md](03_rag_04_01_dto-models_data.md) を参照。`)
  and under "### 2.6 ロギング" (line 92: `詳細は [docs/03_rag_05_3-logging.md](03_rag_05_3-logging.md) を参照。`).
  No duplicated JSON block or logging prose remains in this file's current on-disk
  content. The described replacement appears already applied.
- This document still describes the intended procedure per the plan/workflow contract;
  the "already implemented" check for this workflow phase is filename-based only, so
  this document is generated regardless. See final report for this discrepancy.

## Compatibility considerations
- N/A — documentation only; no external link format change (relative Markdown links
  already used elsewhere in this file).

## Security considerations
- N/A — no secrets involved.

## Rollback considerations
- Single-file Markdown edit; revert via `git revert` of the commit touching this file.
- No runtime/deploy impact if rolled back.

## Validation plan
- Manual inspection: `cat docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md` —
  confirm sections 2.4 and 2.6 contain only the reference lines, no duplicated content.
- `uv run python tools/check_rag_docs_consistency.py` — validates internal Markdown
  links (including the two new/kept references) and cross-file consistency across
  `docs/03_rag_*.md`.

## Out of scope
- Any change to `docs/03_rag_04_01_dto-models_data.md` content (separate document).
- Any change to `docs/03_rag_05_3-logging.md`.
- Any change to `scripts/rag/` source code.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260802-185027_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-125419
- Related target files: 03_rag_02_02_ingestion_pipeline-crawler-part2.md

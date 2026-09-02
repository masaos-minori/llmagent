# Finalize the canonical Documentation Metadata schema and rewrite `docs/00_governance_02_documentation-metadata.md`

## Priority
High

## Summary
`docs/00_governance_02_documentation-metadata.md` ("Documentation Metadata") contradicts
itself and contradicts the tooling that actually enforces front matter: it lists `category`
as one of five required fields, but its own Front Matter Example uses `area`, its own file's
actual front matter uses `area`, and all three enforcement tools in `tools/` treat `area` as
the only recognized field. Separately, `keywords` is documented as a required front-matter
field but is never used that way in practice — every document instead uses a `## Keywords`
body section, which is what the tooling actually checks. The document's eight "Recommended
Additional Fields" (`scope`, `audience`, `status`, `priority`, `version`, `last_updated`,
`author`, `completeness`) have zero real-world adoption across the entire active
documentation set except inside this document's own illustrative example. This issue
finalizes one canonical, machine-readable schema and rewrites the governance document to
match it.

## Background
A repository-wide grep across all 178 files under `docs/*.md` and `docs/adr/*.md` found:
- `area:` present in 132 files; `category:` present in 4 files; both present in 0 files;
  neither present in 42 files (front matter missing entirely).
- The 4 files using `category:` use the exact same value vocabulary as `area:` (`overview`,
  `mcp`), confirming this is a naming inconsistency, not a semantically distinct field.
- `tools/check_docs_structure.py`'s `check_front_matter()` hardcodes the required field
  tuple as `("title", "area", "tags", "related")` — `category` is never referenced anywhere
  in `tools/`.
- `tools/manage_frontmatter.py` (`add-missing`) only ever writes/checks `area:`
  (`extract_area_from_filename()`, `has_area`) — it has no knowledge of `category`.
- `keywords:` as a front-matter key: 0/178 files. `check_docs_structure.py` instead checks
  for a `## Keywords` Markdown heading (`re.search(r"^## Keywords", ...)`), which is the
  actual, enforced convention.
- `scope`, `audience`, `priority`, `version`, `last_updated`, `author`, `completeness`:
  0/178 files (excluding the illustrative YAML block inside the governance document itself).
  `scope`'s documented allowed-value enum is identical to `area`'s — it is a second name for
  the same concept, never adopted.
- `status:` as a front-matter key: 0/178 real files (the only match is inside the governance
  document's own example block). The document's own text is internally ambiguous about
  whether `status` is required ("recommended field," but "a document in the active
  documentation set must carry one of these two values").
- Real `area:` values in use: `agent`(34), `rag`(31), `mcp`(26), `adr`(11), `overview`(8),
  `eventbus`(8), `shared`(7), `governance`(5), `security`(2), `deployment`(1). `adr` and
  `security` are not part of the document's stated 8-value area/scope enum. The document's
  enum also spells the shared-DB area `shared-db`, while every real file uses `shared`.
- A related, already-closed issue (`issues/done/20260802-072818_governance_06_metadata_fields_usage_unverified.md`)
  raised the same underlying question ("are these recommended fields actually parsed by any
  tooling?") against a since-renumbered/merged predecessor document
  (`docs/00_governance_06_ai-reading-metadata.md`, which no longer exists). That issue was
  archived without the requested usage-reality statement ever landing in the successor
  document — this issue is the overdue, evidence-backed follow-through.

## Problem
There is no single, unambiguous, machine-readable definition of what front matter a document
must carry. Three different documents/tools disagree in practice (`area` vs `category` vs
`scope`), one field (`keywords`) is documented as front matter but implemented as a body
section, and eight fields are "recommended" with zero adoption, creating maintenance noise
and false signals for anyone reading the governance document as a checklist.

## Reason for Change
Document search, classification, structural validation, and AI-agent doc routing all need to
agree on which field is authoritative. As long as the governance document and the tooling
diverge, any future validation work (see companion issues `docmeta02`, `docmeta03`) has no
single source of truth to implement against.

## Implementation Intent
Treat `area` as the canonical field (it is what the tooling already enforces and what 132/178
documents already use) and correct the governance document and all illustrative examples to
match it, rather than trying to migrate the ecosystem onto the unused `category`/`scope`
names. Remove documentation for fields with zero adoption instead of leaving aspirational
guidance that nothing implements. Keep the schema small and tied to what is actually checked
today; do not invent new enforcement behavior in this issue (see `docmeta03` for that).

## Target Files or Areas
- `docs/00_governance_02_documentation-metadata.md` (rewrite "Existing Metadata Fields",
  "Recommended Additional Fields", "Front Matter Example", "Metadata Requirements for Active
  Documents")
- `docs/00_governance_03_issue-and-uncertainty-management.md` (register new Needs
  Confirmation entries produced by this issue's open questions)
- A new machine-readable schema file — exact path is `Unknown`; candidates include
  `schemas/doc-front-matter.schema.json` or a location alongside `tools/`. Decide during
  implementation, consistent with existing repository conventions for non-`docs/`,
  non-`scripts/` assets.

## Required Changes
- Declare `area` the single canonical field; remove `category` from "Existing Metadata
  Fields" and from the Front Matter Example.
- Reclassify `keywords` as a documented `## Keywords` body-section requirement (not a
  front-matter key), matching `tools/check_docs_structure.py`'s actual check.
- Resolve the `status` MUST/SHOULD ambiguity: make `status` an optional front-matter field
  that defaults to `stable` when absent, with `draft` as the only other allowed value —
  remove the "must carry one of these two values" MUST-reading language.
- Remove the seven other "Recommended Additional Fields" (`scope`, `audience`, `priority`,
  `version`, `last_updated`, `author`, `completeness`) from the document — zero adoption, and
  `scope` duplicates `area`'s semantics.
- Finalize the `area` enum to match actual usage: add `adr` and `security`; correct
  `shared-db` to `shared`.
- Author a JSON Schema (or equivalent machine-readable schema) expressing: required fields
  (`title`, `area`, `tags`, `related`), the finalized `area` enum, `status`'s optional
  draft/stable enum with a stated default, and array-typed `tags`/`related`.
- Register the following as new Needs Confirmation entries in
  `docs/00_governance_03_issue-and-uncertainty-management.md` (do not resolve them in this
  issue): whether `adr` and `security` should be permanent `area` values or folded into an
  existing area; the relationship between the front-matter `related` field and the `##
  Related Documents` body section (intentional duality or drift); whether the schema should
  set `additionalProperties: false` or allow forward-compatible extension fields.

## Constraints
- Do not change `tools/check_docs_structure.py`'s or `tools/manage_frontmatter.py`'s
  enforcement logic in this issue — this issue only fixes the documentation and produces the
  schema artifact; wiring/enforcement changes belong to `docmeta03`.
- Do not migrate any individual document's front matter in this issue — that is `docmeta02`'s
  scope.
- Per `skills/DESIGN.md` Avoid implementation-reference duplication, do not restate
  `tools/check_docs_structure.py`'s implementation in the governance document — describe the
  policy, and reference the tool by name where useful.

## Acceptance Criteria
- `docs/00_governance_02_documentation-metadata.md` no longer references `category` as a
  required field, and its own Front Matter Example matches its own required-field list
  exactly.
- The document no longer lists any of the seven zero-adoption "Recommended Additional
  Fields," and states `keywords` as a `## Keywords` body-section requirement rather than a
  front-matter key.
- `status`'s optional/default-`stable` behavior is stated unambiguously (no MUST-reading
  language remains).
- The `area` enum listed in the document includes `adr` and `security`, and spells the
  shared-DB value `shared`.
- A machine-readable schema file exists, validates a real, compliant document's extracted
  front matter, and rejects a front matter block using `category` instead of `area`.
- Three new Needs Confirmation entries (per Required Changes) are registered in
  `docs/00_governance_03_issue-and-uncertainty-management.md` per that document's existing
  registration format.

## Testing Expectations
`uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py
docs/00_governance_02_documentation-metadata.md` must pass after the rewrite. If a
JSON-Schema-validation library is used to author or self-check the new schema file, run it
against at least one known-compliant document's front matter and one known-violating example
(e.g. a `category`-only front matter block) to confirm the schema actually discriminates
between them.

## Documentation Impact
Yes — this issue is itself a documentation-policy change. Update
`docs/00_governance_02_documentation-metadata.md` (primary target) and
`docs/00_governance_03_issue-and-uncertainty-management.md` (new Needs Confirmation entries).

## Out of Scope
- Migrating any individual document's actual front matter to the finalized schema (see
  `docmeta02`).
- Implementing or wiring automated CI/tooling enforcement of the new schema (see `docmeta03`).
- Resolving the three Needs Confirmation items registered by this issue (`adr`/`security`
  enum inclusion, `related` field/section duality, `additionalProperties` strictness) — they
  are recorded for a future owner decision, not decided here.
- Changing `tools/check_docs_structure.py`'s or `tools/manage_frontmatter.py`'s source code.

## Dependencies
- Blocks `docmeta02` (bulk migration of all documents) and `docmeta03` (CI enforcement) —
  both require this issue's finalized field set, `area` enum, and schema artifact before they
  can proceed.
- Related to (but does not duplicate) the already-archived
  `issues/done/20260802-072818_governance_06_metadata_fields_usage_unverified.md`, which
  raised the same underlying question against a predecessor document that no longer exists.
- N/A: no other open issue or plan currently targets this document, confirmed by
  `grep -rl "00_governance_02_documentation-metadata" issues/ plans/` returning no matches at
  investigation time (aside from this issue itself).

## Unresolved Questions
- Exact file path for the new machine-readable schema artifact (see Target Files or Areas) —
  not blocking; decide during implementation using existing repository conventions.
- The three Needs Confirmation items this issue registers (see Required Changes) are
  themselves open questions for a future owner decision — recording them is this issue's job,
  not resolving them.

## AI Implementation Instruction
Before editing `docs/00_governance_02_documentation-metadata.md`, re-run the repository-wide
front-matter survey (`grep -l "^area:"` / `"^category:"` / `"^status:"` etc. across
`docs/*.md docs/adr/*.md`) to confirm the counts in this issue have not drifted since it was
filed. Do not restate `tools/check_docs_structure.py`'s Python logic inside the governance
document — reference the tool by name. Do not resolve the three Needs Confirmation items
registered by this issue; record them and stop. Keep the JSON Schema minimal — it should
express exactly the fields this issue finalizes, not anticipate future fields.

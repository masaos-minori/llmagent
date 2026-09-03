## Goal
Finalize `docs/00_governance_02_documentation-metadata.md`'s "Existing Metadata
Fields", "Recommended Additional Fields", "Front Matter Example", and "Metadata
Requirements for Active Documents" sections into one canonical, self-consistent
front-matter contract: `area` as the sole category-style field, `keywords`
reclassified to the `## Keywords` body-section convention, the seven
zero-adoption "Recommended Additional Fields" removed, `status`'s MUST/SHOULD
ambiguity resolved, and the `area` enum corrected to match real usage.

## Scope
- **In-Scope**: this document's four sections named in Goal (lines 17-141 as of
  2026-09-03).
- **Out-of-Scope**: `schemas/doc_front_matter.json` (seq 02 of this Plan),
  `docs/00_governance_03_issue-and-uncertainty-management.md` (seq 03); this
  document's "Terminology Glossary" section (lines 151+ as of 2026-09-03) — a
  separate, already-implemented Plan (`plans/done/20260903-090945_plan.md`) added
  content there; migrating any individual document's actual front matter
  (`docmeta02`'s scope); `tools/check_docs_structure.py` /
  `tools/manage_frontmatter.py` source code (unchanged by this row).

## Assumptions
- Lines 17-141 (Existing Metadata Fields through Metadata Requirements for Active
  Documents) are unchanged from the Plan's own citation — re-verified 2026-09-03
  by direct `Read`, matching exactly (17 fields listed, 8 numbered "Recommended"
  subsections at lines 31-112, Front Matter Example at 114-134, Metadata
  Requirements at 136-141). This span is entirely before the "Terminology
  Glossary" section (line 151+) that the separate, already-implemented
  `plans/done/20260903-090945_plan.md` added content to — confirmed no overlap,
  and that Plan's insertion (within "Usage Rules", itself inside "Terminology
  Glossary") does not shift any line number this row cites, since it is later in
  the file.
- `tools/check_docs_structure.py`'s required-field tuple is `("title", "area",
  "tags", "related")` — re-verified at line 80 (the Plan's original citation,
  "line 67", has drifted due to unrelated intervening tool changes this session;
  the tuple's actual value is unchanged).
- `tools/manage_frontmatter.py` has zero `category` handling and now also
  includes a `rename-category-to-area` subcommand (added during this session's
  earlier tool-review work, after this Plan's own creation) — this is
  reinforcing evidence for REQ-001 (`area` is the tooling's sole recognized
  category-style field), not a contradiction; that subcommand's own migration
  work remains `docmeta02`'s scope, not touched here.
- Current `area:` value distribution (re-verified 2026-09-03,
  `grep -rn "^area:" docs/*.md docs/adr/*.md | sed 's/.*area: *//' | sort |
  uniq -c`): `agent`(33), `rag`(31), `mcp`(25), `adr`(11), `overview`(8),
  `eventbus`(7), `shared`(6), `governance`(5), `security`(2), `deployment`(1) —
  exactly 10 distinct values, matching the Plan's Background exactly with no
  drift. The finalized enum (REQ-005) must therefore contain exactly these 10
  values.

## Design decisions
- **`status` stays under "Recommended Additional Fields" as the section's only
  remaining subsection**, rather than folding it into "Existing Metadata
  Fields" or deleting the section entirely — REQ-004 requires removing "the
  seven zero-adoption fields... including their subsections", implying the
  section itself (and its one adopted-but-optional field) survives; moving
  `status` into "Existing Metadata Fields" would blur that section's now-strict
  "these four are required" meaning with an optional field.
- **The finalized `area` enum keeps the original 8 values in their original
  order and appends `adr`, `security` at the end**, rather than reordering
  alphabetically or by usage frequency — REQ-005 says "add `adr` and
  `security`", which this reads as an addition, not a restatement of the whole
  list's order; minimizing incidental diff keeps the change reviewable.
- **The Front Matter Example drops `status` down to a single optional line
  rather than omitting it entirely**, since `status` remains a real, defined
  (if now-optional) field per REQ-003 — an example that never shows it would
  under-illustrate a field the document itself still defines.
- **"Metadata Requirements for Active Documents" states the required/optional
  split explicitly** ("four required... `status` is optional; when present it
  must be one of...; when absent it defaults to `stable`") rather than only
  removing the old MUST-reading sentence — REQ-003 asks to "state it as an
  optional front-matter field defaulting to `stable`", which requires
  affirmative wording, not just deletion of the old ambiguous sentence.

## Alternatives considered
- **Delete "Recommended Additional Fields" entirely, moving `status` into
  "Existing Metadata Fields" as a fifth, optional-but-required-adjacent
  bullet** — rejected (see Design decisions): this would make "Existing
  Metadata Fields" a mix of required and optional fields, undermining its own
  "the following four... are required" framing this row establishes.
- **Reorder the `area` enum by usage frequency** (`agent, rag, mcp, adr,
  overview, eventbus, shared, governance, security, deployment`) — rejected in
  favor of preserving original order + append (see Design decisions): a
  frequency-based reorder is a larger diff than REQ-005 asks for and could
  itself go stale as usage counts shift over time, whereas the additive edit
  is stable regardless of future usage drift.

## Implementation
### Target file
`docs/00_governance_02_documentation-metadata.md`

### Procedure
1. Re-read lines 17-141 in full immediately before editing to reconfirm no
   drift (done above; confirmed identical to the Plan's citation).
2. Rewrite "Existing Metadata Fields" (REQ-001, REQ-002, REQ-005).
3. Rewrite "Recommended Additional Fields" to keep only `status` (REQ-003,
   REQ-004).
4. Rewrite "Front Matter Example" (REQ-001, REQ-002, REQ-003, REQ-004).
5. Rewrite "Metadata Requirements for Active Documents" (REQ-003).

### Method
Direct text edit (e.g. via the `Edit` tool) using the exact before/after blocks
in Details, as four independent edits (the four sections are contiguous as a
whole span but are replaced as separate blocks for precision).

### Details

**Edit 1 — Existing Metadata Fields (REQ-001, REQ-002, REQ-005)**:

Before:
```
## Existing Metadata Fields

The following five metadata fields should be preserved in all documents:

- **title** — Document title
- **category** — Document category (e.g., overview, deployment, rag, mcp, agent, eventbus, shared-db, governance)
- **tags** — Keywords describing the document content
- **related** — Links to related documents
- **keywords** — Additional search terms for document retrieval
```

After:
```
## Existing Metadata Fields

The following four metadata fields are required in every document's front matter:

- **title** — Document title
- **area** — Document area: one of `overview`, `deployment`, `rag`, `mcp`, `agent`, `eventbus`, `shared`, `governance`, `adr`, `security`. The sole category-style field — `category` is not a valid front-matter key.
- **tags** — Keywords describing the document content
- **related** — Links to related documents

`keywords` is not a front-matter key. Every document instead uses a `## Keywords` body-section heading — see `tools/check_docs_structure.py`'s own check, which looks for that heading, not a front-matter key.
```

**Edit 2 — Recommended Additional Fields (REQ-003, REQ-004)**:

Before:
```
## Recommended Additional Fields

Eight new metadata fields to enhance AI agent document selection:

### 1. scope

Defines the boundary of what the document covers.

- Allowed values: overview, deployment, rag, mcp, agent, eventbus, shared-db, governance
- Example:
```yaml
scope: agent
```

### 2. audience

Intended reader level.

- Allowed values: beginner, intermediate, advanced, developer, operator
- Example:
```yaml
audience: developer
```

### 3. status

Current state of the document. A document in the active documentation set must carry
one of these two values; a document that would otherwise need `deprecated` or
`superseded` is removed from the active set rather than marked with a historical
status.

- Allowed values: draft, stable
- Example:
```yaml
status: stable
```

### 4. priority

Importance level for AI selection.

- Allowed values: critical, high, medium, low
- Example:
```yaml
priority: high
```

### 5. version

Document version number.

- Allowed values: semantic versioning (e.g., 1.0.0, 2.1.3)
- Example:
```yaml
version: 1.0.0
```

### 6. last_updated

Date of last modification.

- Allowed values: ISO 8601 date format (YYYY-MM-DD)
- Example:
```yaml
last_updated: "2026-07-22"
```

### 7. author

Primary author or responsible team.

- Allowed values: Free text, but prefer team names over individuals
- Example:
```yaml
author: agent-team
```

### 8. completeness

How complete the document is relative to its scope.

- Allowed values: complete, partial, outline
- Example:
```yaml
completeness: partial
```
```

After:
```
## Recommended Additional Fields

One optional metadata field beyond the four required fields in "Existing Metadata Fields":

### status

Current state of the document. Optional — defaults to `stable` when absent. A
document that would otherwise need `deprecated` or `superseded` is removed from
the active set rather than marked with a historical status.

- Allowed values: `stable` (default), `draft`
- Example:
```yaml
status: stable
```
```

**Edit 3 — Front Matter Example (REQ-001, REQ-002, REQ-003, REQ-004)**:

Before:
```
## Front Matter Example

Complete Front Matter block showing both existing and new fields:

```yaml
---
title: Agent Reorganization
area: agent
tags: [architecture, reorganization]
related: [00_governance_01_documentation-policy.md]
keywords: [agent, architecture, structure]
scope: agent
audience: developer
status: stable
priority: high
version: 1.0.0
last_updated: "2026-07-22"
author: agent-team
completeness: complete
---
```
```

After:
```
## Front Matter Example

Complete Front Matter block showing the four required fields plus the one
optional field:

```yaml
---
title: Agent Reorganization
area: agent
tags: [architecture, reorganization]
related: [00_governance_01_documentation-policy.md]
status: stable
---
```
```

**Edit 4 — Metadata Requirements for Active Documents (REQ-003)**:

Before:
```
## Metadata Requirements for Active Documents

Every document in the active documentation set must carry the five existing metadata
fields (title, category, tags, related, keywords). A document should add the
recommended fields listed above when doing so improves AI agent document selection;
`status` MUST use one of the two allowed values.
```

After:
```
## Metadata Requirements for Active Documents

Every document in the active documentation set must carry the four required
metadata fields (title, area, tags, related). `status` is optional: when
present, it must use one of the two allowed values (`stable`, `draft`); when
absent, it defaults to `stable`.
```

## Compatibility considerations
No other document links to "Existing Metadata Fields", "Recommended Additional
Fields", "Front Matter Example", or "Metadata Requirements for Active Documents"
by anchor in a way these edits would disturb (headings are unchanged; only body
content within each section changes). Independent of seq 02/03 — this row can be
applied in any order relative to them. Does not overlap with
`plans/done/20260903-090945_plan.md`'s "Terminology Glossary" edit (see
Assumptions).

## Security considerations
None — documentation-only rewrite of a metadata-conventions document; no code,
credentials, or access-control content is affected.

## Rollback considerations
Single-file, four-edit change to a Markdown document under version control;
revert via `git revert`. No other file's content depends on the removed
`category`/`keywords`-as-front-matter-key/seven-recommended-fields wording (this
Plan's own Background confirms zero real-document adoption of those fields), so
rollback carries no cross-file follow-up.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_02_documentation-metadata.md | Automated doc quality check | `uv run python tools/check_docs_quality.py` | No new errors |
| docs/00_governance_02_documentation-metadata.md | Structure/front-matter check | `uv run python tools/check_docs_structure.py docs/00_governance_02_documentation-metadata.md` | Passes; this document's own front matter (`area: governance`) already matches the finalized contract |
| docs/00_governance_02_documentation-metadata.md | Manual cross-check | Re-read all four rewritten sections | No mention of `category` as a field; `keywords` appears only as the body-section convention; `status`'s optional/default-stable behavior is unambiguous; the `area` enum lists exactly 10 values including `adr`/`security`/`shared` |

## Completion criteria
- No reference to `category` as a required field or front-matter key remains;
  `keywords` is not listed as a front-matter key; the Front Matter Example
  matches the required-field list exactly plus optional `status` (AC-1).
- `status`'s optional/default-`stable` behavior is stated with no MUST-reading
  language remaining (AC-2).
- The seven zero-adoption "Recommended Additional Fields" and their subsections
  are gone (AC-3).
- The `area` enum includes `adr` and `security`, and spells the shared-DB value
  `shared` (AC-4).
- `uv run python tools/check_docs_quality.py` and `uv run python
  tools/check_docs_structure.py docs/00_governance_02_documentation-metadata.md`
  report no new errors.

## Out of scope
`schemas/doc_front_matter.json` (seq 02),
`docs/00_governance_03_issue-and-uncertainty-management.md` (seq 03) — each has
its own implementation-procedure document per this Plan's Implementation Target
Files table. This document's "Terminology Glossary" section — owned by
`plans/done/20260903-090945_plan.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903 | 20260903 | Re-verified lines 17-141 before editing — no drift. Applied Edits 1-4 exactly as designed. |
| 2 | Add or update tests per Validation plan | Completed | 20260903 | 20260903 | N/A: documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903 | 20260903 | `check_docs_quality.py`: 0 errors, 1 pre-existing unrelated warning. `check_docs_structure.py`: All checks passed (10511 bytes). `grep -n "category\|^keywords:"` confirms `category` appears only in the "not a valid front-matter key" clarification sentence, no `keywords:` front-matter key remains. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260903 | 20260903 | N/A: no `docs/00_index.md` task-scope mapping applies |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/done/20260902-194021_docmeta01_finalize_canonical_documentation_metadata_schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-124425_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-154428
- **Related target files**: docs/00_governance_02_documentation-metadata.md

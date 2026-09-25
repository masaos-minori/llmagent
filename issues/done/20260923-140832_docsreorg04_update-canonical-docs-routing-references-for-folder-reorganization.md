# Update canonical docs routing references for folder reorganization

## Priority
High

## Summary
Add the new folder path to every specific `docs/*.md` filename reference in
`docs/00_index.md`'s "Document References by Task" table, `rules/env.md`, and
`routing.md`, so these three canonical routing references keep pointing at the correct
location once the planned folder reorganization moves the referenced files. No
filename changes — only prepending the target subfolder to each reference.

## Background
A separate investigation (2026-09-23) evaluated reorganizing `docs/` into area-based
subfolders while keeping every existing filename unchanged. `docs/00_index.md`'s
"Document References by Task" table, `rules/env.md`, and `routing.md` are the three
files that `skills/code-implementation/SKILL.md`, `skills/code-implementation/workflow.md`,
`skills/python-documentation/SKILL.md`, and `templates/plan.md` repeatedly point to as
the canonical way to find "which doc covers this task" — they are load-bearing routing
tables, not incidental mentions.

## Problem
- `docs/00_index.md`'s "Document References by Task" section (lines 48-144) contains 50
  distinct bare-filename mentions (backtick-quoted, e.g. `` `agent_00_document-guide.md` ``)
  with no directory component. `docs/00_index.md` itself also moves (into
  `docs/00_governance/` per the folder classification), so both the file's own new
  location and every filename it lists inside need the correct new subfolder to remain
  a precise routing reference. Its earlier "Categories" and "Recommended Reading Order"
  sections (lines 14-41) also contain bare-filename Markdown links to `01_overview.md`,
  `02_deployment.md`, `03_rag_00_document-guide.md`, `04_mcp_00_document-guide.md`,
  `agent_00_document-guide.md`, `06_eventbus_00_document-guide.md`,
  `shared_00_document-guide.md`, `00_governance_01_documentation-policy.md`,
  `00_governance_02_documentation-metadata.md`,
  `00_governance_03_issue-and-uncertainty-management.md`,
  `00_governance_04_documentation-checks.md`, `adr-index.md` — these are real Markdown
  links (not just prose mentions) and will render as broken (404) links for anyone
  reading the file on GitHub or in a plain Markdown viewer once the referencing and
  referenced files move into different folders (see `docsreorg01`'s Constraints for why
  this is a separate concern from the automated checker).
- `rules/env.md` contains ~15 specific `docs/*.md` path references that need their
  directory component updated (e.g. `docs/04_mcp_01_system_overview.md`,
  `docs/agent_00_document-guide.md`, `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md`).
  It also already contains several **pre-existing, unrelated broken references** to
  `-part1.md`/`-part2.md` file variants that do not exist in the repository under any
  name (e.g. `docs/02_deployment-part1.md`,
  `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md`,
  `docs/05_agent_08_01_configuration-loading-agent-config-part1.md`) — these are a
  separate, pre-existing defect and must not be conflated with this issue's directory
  update (see Out of Scope).
- `routing.md` contains 4 specific `docs/*.md` path references needing an updated
  directory component: `docs/04_mcp_03_01_dispatch-and-routing.md`,
  `docs/04_mcp_06_02_configuration-file-inventory.md`,
  `docs/agent_10_01_operations-and-observability-startup-and-health.md`,
  `docs/00_governance_03_issue-and-uncertainty-management.md`, and the mention of
  `docs/00_index.md` itself. Its other `docs/` mentions (e.g. "Any `docs/*.md` file was
  added or edited") are generic scope descriptions, not specific file paths, and do not
  need updating.

## Reason for Change
If these three files are not updated in step with the physical move, the single most
consulted "where do I find the doc for X" reference in the whole documentation set
becomes stale immediately, defeating the reorganization's purpose and actively
misdirecting anyone (human or AI agent) who trusts it.

## Implementation Intent
For every specific filename reference identified in Problem, prepend the correct new
subfolder path per the folder classification (see Dependencies), leaving the filename
itself unchanged. Do not attempt to fix the pre-existing `-part1`/`-part2` broken
references in `rules/env.md` as part of this issue — that is an independent,
already-existing defect unrelated to the folder move.

## Target Files or Areas
- `docs/00_index.md`
- `rules/env.md`
- `routing.md`

## Required Changes
- `docs/00_index.md`: update all 50 bare-filename mentions in "Document References by
  Task" (lines 48-144) to include their new subfolder path; update the Markdown links
  in "Categories" and "Recommended Reading Order" (lines 14-41) the same way.
- `rules/env.md`: update every specific, currently-valid `docs/*.md` path reference to
  include its new subfolder path. Leave the pre-existing `-part1`/`-part2` broken
  references exactly as they are (out of scope).
- `routing.md`: update the 4 specific path references listed in Problem to include
  their new subfolder path.

## Constraints
- Do not fix the pre-existing `-part1.md`/`-part2.md` broken references in
  `rules/env.md` — track that separately if desired, not here.
- Do not rename any filename — only add a directory prefix to existing references.
- `docs/00_index.md` itself is also subject to the physical-move issue for the
  `00_governance` folder; this issue's content edit and that move should land together
  or in immediate sequence, since editing the file's content is independent of its own
  physical relocation but both affect the same file.

## Acceptance Criteria
- Every specific `docs/*.md` filename mentioned in `docs/00_index.md`'s "Document
  References by Task", "Categories", and "Recommended Reading Order" sections includes
  the correct new subfolder path, verified against the folder classification.
- Every specific, currently-valid `docs/*.md` path in `rules/env.md` includes the
  correct new subfolder path; the pre-existing `-part1`/`-part2` broken references are
  unchanged (still broken, as before — not newly introduced or newly fixed by this
  issue).
- The 4 specific `docs/*.md` paths in `routing.md` include the correct new subfolder
  path.
- `uv run python tools/check_docs_structure.py "docs/**/*.md"` reports no new broken
  link introduced by this edit (run once the corresponding physical moves have also
  landed).

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md"` after the corresponding
  physical moves have landed.
- Manual review: spot-check a handful of updated references by opening the new path to
  confirm the file exists there.

## Documentation Impact
This issue is itself a documentation-content update; no further documentation-impact
statement beyond what is described above.

## Out of Scope
- Fixing the pre-existing `-part1.md`/`-part2.md` broken references in `rules/env.md`.
- Any physical file move (tracked by separate per-area issues).
- Removing or shortening any filename prefix.
- Any `docs/*.md` mention in `routing.md` that describes a generic scope (e.g. "Any
  `docs/*.md` file was added or edited") rather than a specific file path.

## Dependencies
- Depends on: the folder classification decided during the docs-reorg investigation
  (which file moves to which of the 11 target folders).
- Should land in the same coordinated change window as the corresponding area-move
  issues, so this file's content stays accurate rather than temporarily describing a
  location the physical move hasn't reached yet.

## Unresolved Questions
N/A: none — all three files and their specific path references were directly confirmed
during issue drafting.

## AI Implementation Instruction
Change only the directory-component of the specific `docs/*.md` references identified
in Required Changes, in exactly the 3 named files. Do not touch the pre-existing
`-part1`/`-part2` broken references in `rules/env.md`. Do not perform any physical file
move. Do not edit any generic (non-path-specific) mention of `docs/*.md`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-140832
- **Related target files**: docs/00_index.md, rules/env.md, routing.md

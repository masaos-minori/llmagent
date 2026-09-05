# Redesign the 01_overview-files-* series from file trees to design intent

## Priority
Medium

## Summary
Rewrite `docs/01_overview-files-01-build.md`, `-02-rag.md`, `-04-shared.md`,
`-05-config.md`, `-06-misc.md`, and `docs/01_overview-arch-01-process.md` —
currently built almost entirely around literal ASCII directory trees with a
per-file one-line description and, in places, an inline "implemented in
`{file}`" mapping — into design-intent documentation per `skills/DESIGN.md`
Docs content policy — remove/retain.

## Background
`issues/done/20260903-200135_docscope1_define-design-intent-content-policy.md`
and `...docscope2_build-content-policy-detection-tool.md` already defined the
policy and shipped `tools/check_docs_content_policy.py` (registered as
`GV-021`, report-only). Both issues explicitly deferred the actual content
rewrite as future follow-up work — this issue is that follow-up for the
`01_overview-files-*` series, which their own evidence already identified as
the single largest violation cluster in the corpus.

## Problem
Running `uv run python tools/check_docs_content_policy.py` reports 155
warnings across these six files: `01_overview-files-04-shared.md` (44),
`01_overview-files-06-misc.md` (41), `01_overview-files-05-config.md` (35),
`01_overview-files-01-build.md` (19), `01_overview-files-02-rag.md` (11), and
`01_overview-arch-01-process.md` (5) — almost entirely "full file tree" and
"per-file one-line description embedded in a tree" findings. Concretely,
`01_overview-files-04-shared.md`'s "## 3. File Structure" section is a
literal `/opt/llm/` directory tree with `├─`/`│`/`└─` characters and one-line
comments per file/directory (e.g. `rag.sqlite ... — see 90_shared_04 sections
3-6`), followed by a "## 3b. File Structure" section that lists every file
under `scripts/shared/` grouped by theme, each with a one-line description
naming its classes (e.g. `llm_client.py — LLMClient: SSE streaming &
exponential backoff retry`). The same file does already contain a
"### Design Intent and Operational Specifications" subsection (cache/health
check behavior, drift-validation behavior) — this is the kind of content the
policy wants kept, currently a small fraction of the file's total content.

## Reason for Change
File trees and per-file descriptions go stale on every file move, rename, or
refactor, and duplicate what `grep`/`git`/the code itself already answer
authoritatively. They also crowd out the design-intent content (component
responsibility, owned state, allowed dependency direction, reasons for
process/config separation, cross-cutting design boundaries) that is
genuinely hard to recover from code alone and is this series' stated
purpose per `01_overview.md`'s architecture-overview framing.

## Implementation Intent
For each of the six files: remove the ASCII directory tree and its inline
per-file descriptions. Where the tree currently groups files thematically
(e.g. "LLM Client/Transport", "Tool Routing/Execution", "Configuration" in
`01_overview-files-04-shared.md`), keep the thematic grouping as prose
structure but replace the file-by-file listing with a description of what
that group of components is *responsible for*, what *state* it owns, and
which direction its dependencies run (per `rules/env.md` Architecture's
layer diagram — reference it, do not restate it). Preserve and expand each
file's existing design-intent subsections rather than discarding them.
Replace bare file/class enumeration with a single pointer sentence (e.g.
"see `scripts/shared/` for the current file layout") per
`skills/DESIGN.md` Avoid implementation-reference duplication — do not
re-list every filename to prove nothing was lost.

## Target Files or Areas
- `docs/01_overview-files-01-build.md`
- `docs/01_overview-files-02-rag.md`
- `docs/01_overview-files-04-shared.md`
- `docs/01_overview-files-05-config.md`
- `docs/01_overview-files-06-misc.md`
- `docs/01_overview-arch-01-process.md`

## Required Changes
1. Remove every ASCII tree-drawing block (`├─`/`│`/`└─`) and its attached
   per-entry description in all six files.
2. Remove inline implementation-location statements (e.g. "moved by
   `ingester.py`") — describe the responsibility, not the file.
3. For each thematic file group currently enumerated (DB layer, LLM
   client/transport, tool routing, configuration, etc.), write a short prose
   section covering: component responsibility, state owned, allowed
   dependency direction (referencing `rules/env.md` Architecture), reason
   for process separation (if the group corresponds to a separate process),
   reason for per-process configuration separation (if applicable), and any
   design boundary that needs joint review when changed.
4. Preserve existing design-intent subsections (e.g.
   `01_overview-files-04-shared.md`'s "Design Intent and Operational
   Specifications") without loss of content.
5. Update `Related Documents` cross-references in any other `docs/*.md` file
   that currently links into a section being restructured, if the section
   heading changes.
6. Handle literal port numbers in `01_overview-files-05-config.md` per
   `dcp001`'s decision (see Dependencies) rather than deciding independently.

## Constraints
- Do not modify `rules/env.md`'s content — reference it, do not duplicate
  its dependency-direction diagram.
- Do not merge or delete any of the six files outright — the File Split
  Rule's 400-line threshold and existing `routing.md` Docs → task mapping
  entries assume this file boundary; propose a merge only as an Unresolved
  Question, not as an unreviewed action.
- Preserve every existing `Needs confirmation` marker verbatim; do not
  resolve or remove one as a side effect of rewriting surrounding prose.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero findings
  for all six target files.
- Each file's rewritten content addresses, where applicable to its subject
  area: component responsibility, owned state, allowed dependency
  direction, reason for process separation, reason for per-process config
  separation, and design boundaries needing joint review.
- `uv run python tools/check_docs_structure.py docs/01_overview-files-*.md
  docs/01_overview-arch-01-process.md` passes (file size, headings, Front
  Matter, Related Documents/Keywords, internal link reachability).
- `uv run python tools/check_docs_consistency.py --domain overview` passes.

## Testing Expectations
Documentation-only change with no code behavior impact — run the four
`docs/*.md` checkers listed in Acceptance Criteria; no `pytest`/`mypy`/
`ruff` run required unless a cross-referenced `docs/*.md` link needs fixing
in a file outside this scope (in which case, fix the link, not the target
file's content).

## Documentation Impact
Yes — this issue's entire deliverable is the rewrite of the six listed
files.

## Out of Scope
- Any file outside the six listed above (tracked in `dcp003`–`dcp006`).
- Changing `rules/env.md`.
- Deciding the auto-generated port-reference-table exemption (tracked in
  `dcp001`) — apply whatever `dcp001` decides for
  `01_overview-files-05-config.md`'s port content once available.

## Dependencies
Depends on `dcp001` for how `01_overview-files-05-config.md`'s port-number
content should be resolved. Does not depend on `dcp003`–`dcp006` — this
issue can proceed independently of the other per-domain cleanups.

## Unresolved Questions
- Whether the six-file split of this series should be consolidated into
  fewer files once file-tree content is removed (each file may shrink well
  below the 400-line File Split Rule trigger) — flagged for the
  implementer to assess after the rewrite, not decided in advance here.

## AI Implementation Instruction
Rewrite content file by file; do not attempt a single mechanical
find-and-delete across all six files, since each file's thematic grouping
differs and the replacement prose must reflect that file's actual
component boundaries. Preserve every `Needs confirmation` marker and
existing design-intent subsection verbatim unless it is being expanded, not
shortened. Run `tools/check_docs_content_policy.py` after each file to
confirm zero findings before moving to the next. Stop and ask if a file's
existing design-intent content is too sparse to produce a meaningful
retain-category section without inventing unverified claims about the
code.

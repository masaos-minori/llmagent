# Implementation: remove/trim plugin-mentioning documentation

Source plan: `plans/20260717-123416_plan.md` ("Remove plugin subsystem completely"), Implementation
step 7.

Cross-cutting slug used because this item spans ~32-36 documentation files with two dispositions
(outright delete/removal-note vs. incidental trim), not one target file, and the plan itself does not
enumerate all ~31 incidental files by exact name (only the 5 dedicated ones).

## Goal

Remove the 5 dedicated plugin-subsystem documentation files (or convert to a short dated removal note
if live cross-references are found) and trim incidental plugin mentions from the remaining
plugin-referencing docs, so no dangling documentation describes a subsystem that no longer exists.

## Scope

**In scope**

**Dedicated plugin docs (delete outright, or removal-note if cross-referenced)** — confirmed to exist
at these exact paths via direct `test -f` check:
- `docs/05_agent_11_01_extension-points-plugin-command.md`
- `docs/05_agent_11_02_extension-points-tool-registration-part1.md`
- `docs/05_agent_11_02_extension-points-tool-registration-part2.md`
- `docs/05_agent_11_03_extension-points-registry-rules.md`
- `docs/90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`

**Incidental-mention docs (trim only)** — 27 files found via `rg -l "plugin" docs/ -i` at
implementation-doc-writing time (the plan's own prose estimated "~31"; this doc's own fresh scan found
27 — see Assumptions #1 for the discrepancy):
```
docs/01_overview-arch-03-features.md
docs/01_overview-files-03-scripts-part2.md
docs/01_overview-files-04-shared-part2.md
docs/03_rag_01_system_overview-part1.md
docs/03_rag_01_system_overview-part2.md
docs/03_rag_03_01_query_pipeline-overview.md
docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md
docs/03_rag_03_05_query_pipeline-augment-stages.md
docs/04_mcp_03_01_dispatch-and-routing.md
docs/04_mcp_06_16_pre-production-fail-open-checklist.md
docs/05_agent_00_document-guide.md
docs/05_agent_01_system-overview.md
docs/05_agent_02_runtime-architecture-part2.md
docs/05_agent_06_01_tool-execution-and-approval-execution.md
docs/05_agent_07_01_cli-and-commands-cli-reference.md
docs/05_agent_07_03_cli-and-commands-command-registry.md
docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
docs/05_agent_08_01_configuration-loading-agent-config-part1.md
docs/05_agent_08_03_configuration-tools-memory.md
docs/05_agent_10_02_operations-and-observability-audit-and-otel.md
docs/90_shared_00_document-guide.md
docs/90_shared_01_01_overview-purpose-and-scope.md
docs/90_shared_01_02_overview-layer-responsibilities.md
docs/90_shared_02_01_types_and_protocols-core-types.md
docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md
docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md
docs/90_shared_03_01_runtime_and_execution-config-and-logging.md
docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md
docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md
docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md
docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md
docs/99_documentation_sync_report.md
```
(27 incidental files, plus the 5 dedicated ones = 32 total found by this doc's own scan — 4 fewer than
the plan's stated "36". This discrepancy is not reconciled here; see Assumptions #1. Re-run
`rg -l "plugin" docs/ -i` at implementation time to get the authoritative current count before
proceeding, in case the plan's larger count reflects files that were renamed, merged, or already
partially cleaned up since plan authorship.)

**Out of scope**
- Any doc not matched by `rg -l "plugin" docs/ -i`.
- Rewriting doc content unrelated to the plugin subsystem.

## Assumptions

1. The plan states "36 files found". A fresh `rg -l "plugin" docs/ -i` run during this doc's
   investigation returned 32 total matches (5 dedicated + 27 incidental) — 4 fewer than the plan's
   count. This doc's Scope section lists the 27 incidental files found by this scan as the working
   target; the gap versus the plan's "36" is an open discrepancy, not resolved here. The exact
   incidental-file count must be re-verified with a fresh `rg -l "plugin" docs/ -i` at implementation
   time (docs may have been added, renamed, or merged between plan authorship and implementation) —
   this is in addition to the same open point already flagged by plan Unknown #2.
2. Per plan Unknown #2: whether each incidental doc "describes plugins as one topic among several
   (needing a trim) vs. being 100% plugin-focused (needing outright deletion)" is resolved by reading
   each file in full at implementation time — this doc does not pre-judge that per-file, consistent
   with the plan's own stated resolution path ("Resolve during Implementation Step 6 [doc's step 7] by
   reading each file").
3. Per the plan's Risk section: "Deleting 5 dedicated plugin docs (rather than converting them to
   removal notes) could break cross-references from other docs that still link to them" —
   mitigation is to check for inbound links/`related:` front-matter references before outright
   deletion; convert to a short dated removal note instead of hard-deleting if any live cross-reference
   is found, matching this repo's established convention for fully-removed features (the plan cites
   `implementations/done/20260717-001510_mcp_watchdog_removal.md` as the precedent for this convention
   — not read here per this task's own rule against reading other implementation docs' contents, but
   the reference is on the record from the plan text itself).

## Implementation

### Target file

32 files under `docs/` per this doc's own scan (5 dedicated, 27 incidental) — vs. 36 per the plan's
original count; see Scope tables above and re-scan at implementation time per Assumption #1.

### Procedure

1. Re-run `rg -l "plugin" docs/ -i` at implementation start to get the authoritative current file list
   (docs may drift between plan authorship and implementation).
2. For each of the 5 dedicated docs: run `rg -rn "05_agent_11_01_extension-points-plugin-command\|05_agent_11_02_extension-points-tool-registration\|05_agent_11_03_extension-points-registry-rules\|90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime" docs/` to find inbound cross-references (e.g. `related:` front-matter, markdown links) from *other* docs.
   - If no inbound references found for a given dedicated doc: delete it outright.
   - If inbound references found: replace the doc's content with a short dated removal note (per this
     repo's established convention for fully-removed features) rather than deleting the file, so
     inbound links do not 404.
3. For each of the (re-scanned) incidental docs: read the file in full; if the plugin-related content
   is a small, self-contained section (a paragraph, a bullet list entry, a single cross-reference),
   trim just that section; if the file is 100% plugin-focused despite not being on the "dedicated"
   list, treat it as a 6th dedicated-doc case (delete or removal-note per step 2's same logic).
4. Update `docs/99_documentation_sync_report.md`'s own plugin mention (it is itself in the incidental
   list) to reflect the new state, since this file is a meta-report about doc consistency — leaving a
   stale plugin reference there would itself be a doc-consistency violation.
5. Re-run `rg -l "plugin" docs/ -i` after all edits; every remaining hit must be either (a) a dated
   removal note intentionally preserving the word "plugin" for historical context, or (b) a genuinely
   unrelated use of the English word outside this subsystem (none identified during this survey).

### Method

Per-file read-then-decide (delete / removal-note / trim) — no bulk find-and-replace, since each file's
disposition depends on how central "plugin" is to its content (per plan Unknown #2). No production code
is touched; this is a documents-only step within a documents-only step (the source plan's own step 7).

### Details

- The 5 dedicated docs live in two doc series: `05_agent_11_*` (agent extension-points series, 4
  files: `_01_...plugin-command`, `_02_...tool-registration-part{1,2}`, `_03_...registry-rules`) and
  `90_shared_03_02_...plugin-and-tool-runtime` (shared runtime series, 1 file). Their numbering
  (`11_01`, `11_02`, `11_03`) suggests they form a self-contained sub-section of the `05_agent_*` doc
  tree — check `docs/05_agent_00_document-guide.md` (itself in the incidental list) for a table of
  contents / index entry pointing at `11_*` that would also need updating once those files are gone.
- `docs/90_shared_00_document-guide.md` is analogous for the `90_shared_*` series and should be checked
  for an index entry pointing at `90_shared_03_02_...`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Current plugin-doc census | `rg -l "plugin" docs/ -i \| wc -l` | re-run before and after to size the remaining work |
| No remaining plugin mentions (except intentional removal notes) | `rg -n "plugin" docs/ -i` | only removal-note survivors, if any |
| No dangling cross-references to deleted docs | `rg -rn "05_agent_11_01\|05_agent_11_02\|05_agent_11_03\|90_shared_03_02" docs/` | 0 matches, or only the removal-note file(s) themselves |
| Doc consistency checker | `uv run check-agent-docs` (per requirement 17, if available) or manual review | no dangling plugin references |
| Pre-commit | `uv run pre-commit run --all-files` | pass |

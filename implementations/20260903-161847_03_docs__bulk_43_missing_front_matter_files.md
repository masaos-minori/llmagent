## Goal
Add a complete, compliant front-matter block (`title`, `area`, `tags`, `related`)
to the 43 `docs/*.md` files currently missing one entirely, using
`tools/manage_frontmatter.py add-missing --fix` as the primary generation
mechanism, with every inferred value manually reviewed and corrected against
each document's actual content before acceptance.

**Consolidated by explicit user decision** (2026-09-03): this document covers
all 43 files together — the user chose "group by type into a small number of
documents" over one implementation-procedure document per file, given this
Plan's 56-row scale. The mechanism, review protocol, and completion criteria
are identical across all 43 files; only the specific per-file title/tags/related
content differs, and that content is inherently determined by reviewing each
file's actual body at execution time (see Design decisions), not pre-specified
here.

## Scope
- **In-Scope**: the 43 files listed in Details below — adding a complete
  front-matter block to each.
- **Out-of-Scope**: `docs/01_overview-files-03-scripts.md` and
  `docs/01_overview-files-04-shared.md` (seq 01/02 of this Plan — different
  mechanism, manual fence repair, not `add-missing --fix`); the 11 ADR `tags`
  additions (seq 04 — `add-missing --fix` cannot reach `docs/adr/`, per this
  Plan's own Background); any document body-content change; adding `status` or
  any other optional field beyond the four required fields.

## Assumptions
- All 43 files are confirmed still missing front matter entirely as of
  2026-09-03 — re-verified via `uv run python tools/check_docs_structure.py
  docs/*.md docs/adr/*.md`, diffed line-for-line against this Plan's own
  43-file table with zero differences (`diff` exit 0) — no drift since Plan
  creation.
- `tools/manage_frontmatter.py add-missing --dry-run` (re-run 2026-09-03)
  confirms all 43 files resolve to a non-`AMBIGUOUS` `area` (0 `[AMBIGUOUS]`
  lines in the dry-run output) — no file requires the "stop and report rather
  than guess" path this Plan's `UNK-01`/Implementation intent anticipates for
  a genuinely ambiguous area.
- `docs/06_eventbus_00_document-guide.md` infers `area: eventbus` correctly in
  this re-run (re-verifying REQ-004/AC-5) — the `06_eventbus`-prefix
  area-inference bug this Plan's investigation originally found is confirmed
  fixed at the tool level (see this Plan's own Background correction).
- The tool's inferred `tags` value is minimal by design — re-verified: for
  most of the 43 files, the dry-run's `tags:` list contains only the inferred
  `area` name itself (e.g. `tags: [shared]`, `tags: [mcp]`), not
  topic-specific keywords. `related:` is frequently empty. This confirms
  REQ-002's "every inferred value manually reviewed and corrected" requirement
  is not a formality — meaningful `tags`/`related` values require reading each
  file's actual content, which this row's Method describes as a per-file
  review step rather than pre-determining 43 files' final tag sets in this
  document (see Design decisions).
- Three tool-inferred `title` values collide across different files (`"DB API
  and Operations"` for 3 `90_shared_05_*` files; `"Shared Runtime and
  Execution Infrastructure"` for 3 `90_shared_03_*` files) — flagged for
  manual review to differentiate (e.g. appending a distinguishing subtitle, matching
  this corpus's existing convention for multi-part documents, e.g. `"Memory
  Layer — Overview and Modes (Part 1)"`).

## Design decisions
- **This document specifies the mechanism and review protocol, not each of
  the 43 files' exact final `title`/`tags`/`related` values** — REQ-002 itself
  requires those values to be "manually reviewed and corrected... against the
  document's actual content," meaning the final values are determined by
  reading each file's real content at execution time, not decidable in
  advance from this Plan's or this procedure's own investigation. Pre-baking
  43 sets of exact values into this document without that per-file content
  review would violate REQ-002's own requirement in spirit, even if done
  during procedure-generation rather than during implementation.
- **`tools/manage_frontmatter.py add-missing --fix` is run once against the
  whole `docs/` corpus** (its own glob scope), not once per file — the tool
  itself already batches this correctly (confirmed: it globs `docs/*.md` and
  writes only to files actually missing front matter), so invoking it 43
  times would be needless repetition of the same single command.
- **The per-file review checklist is explicit and repeatable** (title
  accuracy against the document's actual first heading/content; `tags`
  enriched with genuine topic keywords beyond the bare `area` name; `related`
  populated where an actual related document is identifiable, left empty
  only when genuinely none exists) — this gives the execution step a concrete
  standard to apply uniformly across all 43 files, rather than leaving "manual
  review" as an unstated, individually-judged bar per file.

## Alternatives considered
- **Generate 43 separate implementation-procedure documents (one per file)**
  — the strict, unmodified convention — explicitly declined by the user for
  this Plan given its 56-row scale, in favor of this consolidated approach.
- **Pre-write all 43 files' final tags/related values now, based on a quick
  skim of each file** — considered, rejected (see Design decisions): REQ-002
  itself requires this review to happen against actual content, and doing a
  "quick skim" now to pre-fill 43 documents' worth of content would not meet
  the same evidentiary bar this session has applied to every other row (grep/Read
  verification, not surface-level guessing) — better to leave this as an
  explicit, described execution-time step than to produce 43 unverified
  guesses now.

## Implementation
### Target file
43 files under `docs/` (see the full list below) — no single canonical target
path; this document is filed under a descriptive slug
(`docs/_bulk_43_missing_front_matter_files`) per the user's consolidation
decision, not a real repository path.

### Procedure
1. Re-run `uv run python tools/check_docs_structure.py docs/*.md
   docs/adr/*.md` and re-confirm the 43-file list matches Details below (done
   above at generation time; re-confirm again immediately before editing, per
   this Plan's own Phase 1).
2. Run `uv run python tools/manage_frontmatter.py add-missing --fix` once,
   generating a front-matter block for all 43 files in a single pass.
3. For each of the 43 files, apply the Review Checklist (Details below)
   against the file's actual current body content, correcting `title`/`tags`/
   `related` as needed. Pay particular attention to:
   - `docs/06_eventbus_00_document-guide.md`: verify `area: eventbus` (REQ-004,
     AC-5) — expected to already be correct via the tool's own inference.
   - The 3 `90_shared_05_*` files sharing the inferred title `"DB API and
     Operations"`, and the 3 `90_shared_03_*` files sharing `"Shared Runtime
     and Execution Infrastructure"` — differentiate each with a distinguishing
     subtitle.
   - `docs/04_mcp_06_12_watchdog-configuration-monitoring.md`: the tool infers
     title `"MCP Watchdog — Removed (2026-07-16)"` directly from the
     document's own heading — confirm this reflects the document's actual,
     current content (a body-content decision about whether this doc itself
     is stale is out of this row's scope; only confirm the *title* accurately
     reflects what the document currently says).

### Method
`tools/manage_frontmatter.py add-missing --fix` (automated draft generation)
followed by manual `Edit` per file (review and correction), per the Review
Checklist in Details.

### Details

**The 43 target files** (re-verified 2026-09-03, matching this Plan's own
table with zero drift):

| # | File | Tool-inferred `area` |
|---|---|---|
| 1 | `docs/00_index.md` | overview |
| 2 | `docs/03_rag_91_design_notes.md` | rag |
| 3 | `docs/04_mcp_02_02_startup-modes-and-health.md` | mcp |
| 4 | `docs/04_mcp_03_03_transport-and-health.md` | mcp |
| 5 | `docs/04_mcp_03_05_lifecycle-and-new-server.md` | mcp |
| 6 | `docs/04_mcp_04_02_file-write-file-delete-shell.md` | mcp |
| 7 | `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md` | mcp |
| 8 | `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | mcp |
| 9 | `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | mcp |
| 10 | `docs/04_mcp_06_01_purpose.md` | mcp |
| 11 | `docs/04_mcp_06_04_major-default-values.md` | mcp |
| 12 | `docs/04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md` | mcp |
| 13 | `docs/04_mcp_06_08_end-to-end-tool-call-tracing.md` | mcp |
| 14 | `docs/04_mcp_06_09_mcp-failure-diagnosis.md` | mcp |
| 15 | `docs/04_mcp_06_10_settings-with-high-operational-impact.md` | mcp |
| 16 | `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` | mcp |
| 17 | `docs/04_mcp_06_12_watchdog-configuration-monitoring.md` | mcp |
| 18 | `docs/04_mcp_07_tool_schema_export_policy.md` | mcp |
| 19 | `docs/04_mcp_08_tool_capability_naming_convention.md` | mcp |
| 20 | `docs/05_agent_02_runtime-architecture.md` | agent |
| 21 | `docs/05_agent_03_01_turn-processing-flow-overview.md` | agent |
| 22 | `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md` | agent |
| 23 | `docs/05_agent_03_03_turn-processing-flow-workflow-engine.md` | agent |
| 24 | `docs/05_agent_04_02_state-and-persistence-history-compression.md` | agent |
| 25 | `docs/05_agent_05_llm-and-streaming.md` | agent |
| 26 | `docs/05_agent_07_02_cli-and-commands-cliview.md` | agent |
| 27 | `docs/05_agent_10_05_operations-and-observability-monitoring.md` | agent |
| 28 | `docs/05_agent_12_01_memory-overview-and-modes.md` | agent |
| 29 | `docs/05_agent_12_02_memory-gate-data-model-search.md` | agent |
| 30 | `docs/05_agent_12_04_memory-module-ref-retrieval-and-injection.md` | agent |
| 31 | `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md` | agent |
| 32 | `docs/05_agent_13_reference-api.md` | agent |
| 33 | `docs/06_eventbus_00_document-guide.md` | eventbus |
| 34 | `docs/90_shared_02_01_types_and_protocols-core-types.md` | shared |
| 35 | `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` | shared |
| 36 | `docs/90_shared_02_03_types_and_protocols-reference.md` | shared |
| 37 | `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` | shared |
| 38 | `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md` | shared |
| 39 | `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md` | shared |
| 40 | `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md` | shared |
| 41 | `docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` | shared |
| 42 | `docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md` | shared |
| 43 | `docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md` | shared |

**Two files among the 43 also carry a stray `category:` line inside an
unfenced pseudo-YAML block** (rows 4 and 8 above:
`04_mcp_03_03_transport-and-health.md`,
`04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`) — when
`add-missing --fix` rebuilds these files' front matter, confirm the rebuilt
block uses `area:` and that the old unfenced `category:` line is removed, not
carried over as stray body text.

**Review Checklist** (apply to each of the 43 files after `add-missing --fix`
runs):
1. **Title**: read the document's actual first heading/opening content; does
   the tool-inferred `title` accurately and distinctly describe this
   document? Fix if inaccurate; add a distinguishing subtitle if it collides
   with another file's title (see the 3+3 duplicate-title cases above).
2. **Area**: confirm the inferred `area` matches the document's actual
   subject matter, not just its filename prefix — flag as a new Needs
   Confirmation entry (REQ-005) rather than guessing if genuinely ambiguous
   (none identified as of this row's own re-verification).
3. **Tags**: the tool's default (`[<area>]`) is a placeholder, not a final
   value — add 2-4 genuine topic-specific keywords drawn from the document's
   actual content (matching this corpus's existing tag-richness convention,
   e.g. `docs/00_governance_02_documentation-metadata.md`'s own
   `[governance]`, or a populated multi-tag document elsewhere in the corpus).
4. **Related**: where the document's content clearly references or is
   referenced by another specific document (check existing Markdown links in
   the body), add that document to `related:`; leave empty only when
   genuinely no related document is identifiable — do not guess.

## Compatibility considerations
No other document links to any of these 43 files' front matter by anchor
(front matter is not itself an anchor target). Independent of seq 01/02/04 —
this row's own files are disjoint from the fence-repair files (seq 01/02) and
the ADR files (seq 04, under `docs/adr/`, outside this tool's glob scope).

## Security considerations
None — documentation-only front-matter additions; no code, credentials, or
access-control content is affected.

## Rollback considerations
43 individual file edits (via one tool invocation plus per-file manual
correction) under version control; revert via `git revert` of the resulting
commit(s). No other file depends on any of these 43 files' front-matter
structure.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All 43 target files | Structure/front-matter check | `uv run python tools/check_docs_structure.py docs/*.md` | Zero "missing Front Matter" findings among the 43 files |
| All 43 target files | Automated doc quality check | `uv run python tools/check_docs_quality.py` | No new errors introduced |
| Sample of the 43 files | Manual spot-check | Hand review of `title`/`area`/`tags`/`related` against document content, focused on the 3 duplicate-title cases and `docs/06_eventbus_00_document-guide.md` | Values are accurate and distinct, not just mechanically present |

## Completion criteria
- All 43 files have a front-matter block containing `title`, `area`, `tags`,
  and `related`, each manually reviewed against the document's actual content
  per the Review Checklist (AC-2).
- `docs/06_eventbus_00_document-guide.md`'s `area` is confirmed `eventbus`
  (AC-5, REQ-004).
- No two of the 43 files retain an identical, undifferentiated `title`.
- `uv run python tools/check_docs_structure.py docs/*.md` reports zero
  "missing Front Matter" findings among these 43 files; `uv run python
  tools/check_docs_quality.py` reports no new errors.

## Out of scope
`docs/01_overview-files-03-scripts.md` / `docs/01_overview-files-04-shared.md`
(seq 01/02), the 11 ADR `tags` additions (seq 04) — each covered by its own
implementation-procedure document. Confirming full-corpus `area` enum
membership and re-running the final compliance survey (REQ-005/REQ-006) —
covered by this Plan's own Phase 3 steps, applied across all 56 files
together once seq 01/02/03/04 all land, not owned by any single row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Covers all 43 files via one tool invocation plus per-file manual review |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/done/20260902-194021_docmeta02_migrate_all_documents_to_canonical_metadata_schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-125112_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-161847
- **Related target files**: the 43 files listed in Details above

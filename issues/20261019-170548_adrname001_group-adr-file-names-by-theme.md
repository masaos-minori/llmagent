# Rename the ADR files so that files of the same theme are grouped by name (group-number prefix)

## Priority
Medium

## Summary
Rename the 14 files `docs/10_adr/adr_02_NNN_*.md` to `adr_02_<GG>_<NNN>_<group>-<topic>.md`, where `GG` is a two-digit theme-group number and `group` is the theme word, so that ADRs of one theme sit next to each other in a directory listing. Keep ADR IDs, ADR content, `adr_00_document-guide.md`, and `adr_01_index.md` unchanged, and update every reference, tool, test, and rule that depends on the old name shape.

## Background
- Request from `memo1.md` (2026-10-19): review the relationships among the ADR files under `docs/` and propose grouped file names. The owner then chose option B, the group-number-first scheme, so that groups are physically adjacent in a listing.
- Current names are ID-ordered with no theme element (`adr_02_NNN_<slug>.md`); six slugs already begin with a theme word (`rag-`, `eventbus-`, `agent-`). Other documentation areas encode grouping in the name (for example `rag_02_01_ingestion_pipeline-overview.md`).
- ADR-011 is intentionally unassigned (stated in `docs/10_adr/adr_01_index.md`) and stays so.

## Problem
- Related ADRs are not adjacent: for example ADR-005, ADR-009, and ADR-010 (RAG) and ADR-006 and ADR-013 (EventBus) are interleaved with unrelated ADRs, so a reader or an agent cannot find a theme by listing the directory.
- Relationships found from the ADR bodies (2026-10-19): ADR-002 (config isolation) and ADR-004 (failure handling) are each referenced by 10 ADRs (platform foundations); ADR-014 references 001, 002, 003, 004 and ADR-003 references 001, 002, 004 (agent control plane); ADR-012 references 007 (MCP); ADR-013 references 006 (EventBus); ADR-009 and ADR-010 reference 005 (RAG); ADR-008 references 002, 004, 005, 006, 013 (database); ADR-015 references no ADR (documentation governance).

## Reason for Change
- Maintainability and usability: theme grouping by name makes the ADR set navigable for people and for AI agents without opening each file.
- Doing it once now, with the tool support that exists (`tools/rename_doc.py`), is cheaper than after more ADRs and references accumulate.

## Implementation Intent
- Name shape: `adr_02_<GG>_<NNN>_<group>-<topic>.md`. The `adr_02_` class prefix and the three-digit ADR ID stay, so the ID remains the stable key; the group number inserted before it orders files by theme.
- Group registry (group number, word, members):
  - 01 `platform`: 002, 004
  - 02 `agent`: 001, 003, 014
  - 03 `mcp`: 007, 012
  - 04 `eventbus`: 006, 013
  - 05 `db`: 008
  - 06 `rag`: 005, 009, 010
  - 07 `docs`: 015
- New names (the topic part keeps the old slug; a leading theme word that duplicates the group is not repeated, and `http-mcp` and `git-mcp` become `mcp-http` and `mcp-git`):
  - `adr_02_01_002_platform-config-isolation.md`, `adr_02_01_004_platform-environment-failure-handling-policy.md`
  - `adr_02_02_001_agent-workflow-engine-mandatory.md`, `adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `adr_02_02_014_agent-control-plane-responsibility-boundaries.md`
  - `adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`, `adr_02_03_012_mcp-git-server-side-write-enforcement.md`
  - `adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `adr_02_04_013_eventbus-authentication-authorization.md`
  - `adr_02_05_008_db-sqlite-4db-separation.md`
  - `adr_02_06_005_rag-source-derived-index-relationships.md`, `adr_02_06_009_rag-fts5-text-separation.md`, `adr_02_06_010_rag-fallback.md`
  - `adr_02_07_015_docs-reference-document-class-disposition.md`
- Perform the renames with `tools/rename_doc.py` (dry-run first, then `--apply`), which uses `git mv` and rewrites Markdown links and front matter `related:` entries under `docs/`; fix the references outside `docs/` and the name-shape patterns by hand; do all of it in one commit so no intermediate state is published.
- Record the group registry and the naming rule where a new ADR author will find them (the ADR document guide, plus a group column in the ADR list of the Index).

## Target Files or Areas
- The 14 files `docs/10_adr/adr_02_NNN_*.md` (renamed, content unchanged except self and cross references)
- `docs/10_adr/adr_00_document-guide.md` (Reading Order table, naming rule, group registry) and `docs/10_adr/adr_01_index.md` (ADR list paths, optional group column)
- References in 49 other documents under `docs/` (rewritten by `tools/rename_doc.py`); `docs/00_governance/governance_01_documentation-policy.md` also states the name pattern (`adr_02_{NNN}` in the claim-type definitions and Resolution Matrix, and `adr_02_NNN_*.md` in the ADR heading rule)
- Tools that encode the name shape: `tools/check_docs_structure.py` (`ADR_ID_RE`, `SIZE_EXCEPTIONS` keys), `tools/check_adr_structure.py` (`_ADR_FILE_RE`), `tools/check_workitem_traceability.py` (the `adr_02_{NNN}_*.md` glob), `tools/check_known_deviation_sync.py` (target path parsing, to verify), `tools/check_docs_quality.py`, `tools/check_adr_reference.py`, `tools/check_adr_invariant_matrix.py`, `tools/check_adr_preservation.py`, `tools/check_db_separation.py` (mentions to verify), `tools/TOOL_DESCRIPTIONS.md`
- Tests: `tests/tools/test_check_docs_structure.py`, `test_check_known_deviation_sync.py`, `test_check_docs_quality.py`, `test_check_adr_structure.py`, `test_check_adr_reference.py`, `test_check_adr_invariant_matrix.py`, `test_manage_frontmatter.py`
- `scripts/shared/tool_registry.py` and `scripts/shared/tool_routing_validation.py` (ADR path mentions in docstrings or comments), and `skills/python-refactoring/path-c.md` (the rule for naming a new ADR file)

## Required Changes
- Rename the 14 files as above with `tools/rename_doc.py`, one dry-run and one apply each, and confirm the rewritten links and `related:` entries.
- Update the name-shape patterns in the tools and tests: `ADR_ID_RE` and `_ADR_FILE_RE` accept `adr_02_<GG>_<NNN>_` and still capture the ADR ID, the traceability glob matches the new shape, and the `SIZE_EXCEPTIONS` keys use the new names.
- Handle the size ceilings (see Constraints): three ADRs would exceed their limits after the rename.
- Update the ADR Index list, the document guide Reading Order, the naming rule and group registry, `governance_01_documentation-policy.md`, `skills/python-refactoring/path-c.md`, and `tools/TOOL_DESCRIPTIONS.md` for the new shape.
- Fix the code, comment, and test mentions found under `scripts/`, `tools/`, and `tests/`.
- Do not rewrite historical documents under `issues/done/`, `plans/done/`, and `implementations/done/` (they are records); confirm that no checker depends on their old file names.
- Search the whole repository (excluding those archives, `memo*`, and git history) for the old names and fix every remaining mention.

## Constraints
- ADR IDs, ADR status, decisions, invariants, and content stay unchanged; only file names and references change (`tools/check_adr_preservation.py` must not report an ERROR for the edited files).
- Size ceilings: the rename lengthens the file names that appear inside ADR bodies and front matter. Estimated from the occurrences of the new names (2026-10-19): ADR-003 grows by 33 bytes (26569 to 26602 against a 26592 ceiling), ADR-004 by 33 (32272 to 32305 against 32280), and ADR-007 by 24 (24572 to 24596 against the 24576 default); the other ADRs stay within their limits. `tools/check_docs_structure.py` already records owner-accepted exceptions keyed by file name, so these three need an owner decision: raise or add the ceilings by the growth, or trim body text.
- Do the rename in a single commit on a clean, up-to-date tree: other documentation work lands on this branch frequently and `tools/rename_doc.py` rewrites many files at once.
- Do not change `adr_00_document-guide.md` or `adr_01_index.md` file names (fixed names are used by several tools).

## Acceptance Criteria
- The 14 files exist under the new names, the old names are gone, and `git log --follow` still follows each file's history.
- `tools/check_docs_structure.py`, `check_docs_quality.py`, `check_adr_structure.py`, `check_adr_reference.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py`, `check_docs_consistency.py` (all domains that apply), `check_docs_content_policy.py --strict`, and `check_docs_japanese.py` pass; `check_adr_preservation.py` reports no ERROR.
- No link, `related:` entry, tool, test, script comment, skill, or rule outside the done-archives refers to an old ADR file name.
- The tools' tests pass and cover the new name shape (including a case that fails on the old shape).
- The ADR Index and document guide state the group registry and naming rule; a new-ADR instruction in the skill matches it.

## Testing Expectations
- `uv run pytest tests/tools -q` (the pattern tests), the documentation checkers named above, and `tools/rename_doc.py` dry-run output for each file before `--apply`.
- The `rules/toolchain.md` sequence for the changed Python files; `tools/check_tool_descriptions_sync.py` if tool descriptions change.
- A final repository search for the old names; the full test suite once, with the production snapshot comparison used for the test-isolation work.

## Documentation Impact
Yes: the ADR document guide, the ADR Index, `docs/00_governance/governance_01_documentation-policy.md`, `tools/TOOL_DESCRIPTIONS.md`, and the 49 documents whose links are rewritten. Write in English.

## Out of Scope
- Changing any ADR's content, ID, status, or decision, and assigning ADR-011.
- Renaming documents in other directories, or the `adr_00_` and `adr_01_` files.
- Rewriting historical records under `issues/done/`, `plans/done/`, and `implementations/done/`.
- Changing the ADR heading rules or the Index verification matrix.

## Dependencies
- N/A: none. No open issue under `issues/` overlaps; sibling check recorded 2026-10-19.
- Coordination: other documentation changes touching `docs/` should be merged first or paused, because the rename rewrites many files.

## Unresolved Questions
- Confirm the group numbering (platform 01, agent 02, mcp 03, eventbus 04, db 05, rag 06, docs 07) and group words, and whether ADR-003 belongs to `agent` (as proposed, from its dependence on ADR-001 and ADR-014) or to `mcp`.
- The owner decision for the three size ceilings (ADR-003, ADR-004, ADR-007): raise the ceilings or trim text.
- Where a new ADR author records the group of a new ADR: assumption, the registry in the document guide and a group column in the Index.
- Whether any tool other than those listed parses ADR file names (a final search of `tools/`, `tests/`, `scripts/`, `skills/`, `rules/`, and `config/` found the files above; `tools/check_known_deviation_sync.py`, `check_db_separation.py`, and `check_adr_preservation.py` mentions still need a closer look).

## AI Implementation Instruction
- Use `tools/rename_doc.py` for every rename (dry-run, then `--apply`) and never move files with plain `mv`; then fix what the tool reports as outside `docs/`.
- Change names and references only; do not edit ADR decisions, invariants, or statuses.
- Make the change in one commit on a clean tree; run all documentation and tool checkers named above before committing.
- Stop and report if a checker depends on the old shape in a way that is not listed, or if the three size ceilings need an owner decision before the work can finish.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-170548
- **Related target files**: `docs/10_adr/adr_00_document-guide.md`, `docs/10_adr/adr_01_index.md`, `tools/check_docs_structure.py`, `tools/check_adr_structure.py`, `tools/check_workitem_traceability.py`

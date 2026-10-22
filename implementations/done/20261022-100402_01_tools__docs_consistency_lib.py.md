## Goal
Make `check_broken_internal_links` resolve the `#anchor` part of links against the target document's headings, for cross-document and same-page links, and report an unresolved anchor as a Warning (REQ-001: stale anchor reported; REQ-002: same-page anchors; REQ-003: one documented slug rule; REQ-004: existing ERROR behavior unchanged).

## Scope
- Add a heading-slug computation and anchor resolution inside the existing link check.
- No signature change, no new CLI option, no change to the missing-file ERROR path.

## Assumptions
- Docs are rendered with GitHub-style heading slugs (UNK-01 of the Plan; the live prototype found 1 stale anchor of 79, matching a manual check).
- `DocFile.lines` carries the document's own content, so same-page anchors need no filesystem read; cross-document anchors need the target file text from the docs tree (the function already enumerates `docs_dir.rglob("*.md")`).
- `report_and_exit` fails only on ERROR, so Warning findings keep exit 0 for existing runs.

## Design decisions
- Slug rule (single implementation): strip a Markdown link wrapper to its text, lowercase, remove every character that is not a letter, digit, space, hyphen, or underscore, replace spaces with hyphens; the n-th repeat of an identical slug gets the suffix `-1`, `-2`, ... ; headings inside fenced code blocks are ignored.
- Compare the anchor exactly (no case folding), as the renderer slugs are lowercase.
- Emit WARNING for anchors and keep ERROR for a missing file; skip the anchor check when the file part is missing (the ERROR already reports it) and for paths containing `/` (outside the check's current scope).

## Alternatives considered
- A separate new check function and skip option: rejected, it would touch `check_docs_consistency.py` (a second tool shared with another Plan) for no behavior gain; `--skip links` covers both.
- Putting the check in `check_docs_structure.py`: rejected, its link regex drops the anchor and the library already parses the anchor.

## Implementation
### Target file
`tools/_docs_consistency_lib.py`

### Procedure
1. Add a helper `_slugify_heading(text)` (new) implementing the slug rule above.
2. Add a helper `_heading_slugs(lines)` (new) that walks the lines, toggles on ```` ``` ```` fences, matches ATX headings (`#` to `######`), and returns the set of slugs with duplicate suffixes.
3. In `check_broken_internal_links`, after the existing target-file handling: when an anchor is present and non-empty, compute the slug set for the target (same page: `doc.lines`; other file: its text read from the docs tree, cached per file name for the call) and append a WARNING `Issue` when the anchor is not in the set.
4. Remove the "pure #anchor link is skipped" shortcut in favor of the same-page branch; keep the `http`/`mailto` and `/`-path skips.

### Method
- Keep the function signature and return type; add small private helpers rather than inlining so the function's complexity stays low.
- Use a name-to-path map built once from the same `rglob` that builds `existing_files`; resolve a bare file name to its path through the map (file names are unique in `docs/`).
- WARNING message names the anchor and the target file, for example: `anchor '#x' not found in headings of file.md`.

### Details
- A target file that cannot be read (`OSError`) yields no anchor finding.
- Anchors in links inside inline code or fenced blocks follow the existing link regex behavior (not changed).
- Do not change `_split_link_target`.

## Compatibility considerations
The function is called from `check_docs_consistency.py` for every domain and its output only gains Warning findings; callers and exit codes are unchanged. Expected live result: one new Warning (`mcp_03_01_dispatch-and-routing.md` linking to a heading of `mcp_06_07_mcp-failure-diagnosis.md` that no longer exists).

## Security considerations
N/A: read-only docs checker; reads files only under the docs tree.

## Rollback considerations
Revert the commit; no persisted state.

## Validation plan
- `uv run pytest tests/tools/test_check_agent_docs_consistency.py -q` (after the test procedure), then `uv run pytest tests/tools -q`.
- `uv run ruff format`/`check` on the file, `uv run mypy tools/_docs_consistency_lib.py`, `uv run bandit tools/_docs_consistency_lib.py`.
- Live runs: `uv run python tools/check_docs_consistency.py --domain mcp` (known Warning, exit 0) and the other domains (exit 0); `uv run python tools/check_docs_structure.py`.

## Completion criteria
- A link to a nonexistent anchor yields one Warning; a link to an existing anchor yields none; same-page anchors are resolved; duplicate headings resolve with `-1`/`-2` suffixes; fenced-code headings are ignored.
- A missing target file is still one ERROR.
- Live runs exit 0 with only the known extra Warning.

## Out of Scope
- Fixing the stale anchor in the docs, EventBus/Shared/DB domains, and `related:` basename rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the slug helpers and anchor resolution to `check_broken_internal_links` | Completed | 20261022-104203 | 20261022-104203 | Changed: tools/_docs_consistency_lib.py |
| 2 | Tests are covered by the procedure for `tests/tools/test_check_agent_docs_consistency.py` | Completed | 20261022-104203 | 20261022-104203 | validated; full suite 9692 passed, 14 skipped; tools tests 1077 passed; docs checkers pass; live mcp run: one anchor Warning triaged to issues/20261022-104121_mcpanchor_fix-stale-anchor-mcp-dispatch-doc.md (REQ-007) |
| 3 | Run the tool validation sequence and live runs | Completed | 20261022-104203 | 20261022-104203 | validated; full suite 9692 passed, 14 skipped; tools tests 1077 passed; docs checkers pass; live mcp run: one anchor Warning triaged to issues/20261022-104121_mcpanchor_fix-stale-anchor-mcp-dispatch-doc.md (REQ-007) |
| 4 | File a follow-up issue for the stale anchor (REQ-007); docs updates are in the docs procedures | Completed | 20261022-104203 | 20261022-104203 | validated; full suite 9692 passed, 14 skipped; tools tests 1077 passed; docs checkers pass; live mcp run: one anchor Warning triaged to issues/20261022-104121_mcpanchor_fix-stale-anchor-mcp-dispatch-doc.md (REQ-007) |

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
- **Requirement ID**: `REQ-001` (stale anchor reported), `REQ-002` (same-page anchors), `REQ-003` (slug rule), `REQ-004` (ERROR path unchanged), `REQ-007` (triage live findings)
- **Source issue**: `issues/20261021-101812_anchorcheck_add-a-dedicated-anchor-validation-check-for-docs-links.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093452_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100402
- **Related target files**: tools/_docs_consistency_lib.py
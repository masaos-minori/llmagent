# Make docs domain checkers subfolder-aware

## Priority
High

## Summary
Update every tool that discovers or references `docs/*.md` files via a hardcoded
flat-`docs/`-root assumption (prefix-only non-recursive glob, or a full hardcoded
path constant) so each continues to find its target file(s) once the planned `docs/`
folder reorganization moves them into area subfolders. No filename changes; only the
directory component of these tools' path assumptions changes.

## Background
A separate investigation (2026-09-23) evaluated reorganizing `docs/` into area-based
subfolders (`00_governance/`, `01_overview/`, `10_adr/`, `21_rag/`, `22_mcp/`,
`23_agent/`, `24_eventbus/`, `40_shared/`, `41_db/`, `90_deployment/`, `91_security/`)
while keeping every existing filename unchanged.

## Problem
Several tools assume `docs/` is flat (no subfolders) and locate their target file(s)
either by a prefix-only, non-recursive glob, or by a full hardcoded path constant built
from today's flat layout:

- `tools/_docs_consistency_lib.py:52-60` — `discover_md_files(docs_dir, *, prefix)` runs
  `docs_dir.glob(f"{prefix}*.md")` (non-recursive). `tools/check_docs_consistency.py:58-60`
  hardcodes `"agent": "05_agent_"`, `"mcp": "04_mcp_"`, `"rag": "03_rag_"` as the prefix
  passed in. Once these files move into `docs/23_agent/`, `docs/22_mcp/`,
  `docs/21_rag/` respectively, this glob (run against `docs/`) stops finding them.
- `tools/_docs_consistency_lib.py:71` — `_BARE_MD_FILENAME_RE` detects backtick-quoted
  bare filenames referencing removed/historical docs in prose; this depends only on the
  filename pattern (`NN_...`), not the directory, so it is unaffected by the move — no
  change needed here, listed for completeness/reference only.
- `tools/check_dependency_graph_cycles.py:107` — `discover_md_files(DOCS_DIR, prefix="")`
  plus `GRAPH_DOC_NAME = "00_governance_01_documentation-policy.md"` compared by exact
  match; breaks once this file moves into `docs/00_governance/`.
- `tools/check_needs_confirmation_inventory.py:44` — same pattern,
  `INVENTORY_DOC_NAME = "00_governance_03_issue-and-uncertainty-management.md"`.
- `tools/check_known_deviation_sync.py:45-46,52,116,150` — `ADR_DIR = DOCS_DIR / "adr"`
  hardcoded, `_GOVERNANCE_KNOWN_ISSUES_DOC` exact-match, and its own
  `discover_md_files(ADR_DIR, prefix="")` call; breaks once ADR files move from
  `docs/adr/` to `docs/10_adr/` and the governance doc moves to `docs/00_governance/`.
- `tools/check_adr_structure.py`, `tools/check_adr_reference.py:147,163,186`,
  `tools/check_adr_invariant_matrix.py:116,138` — fixed references to
  `docs/adr-index.md` / `docs/adr/*.md`; breaks once these move to `docs/10_adr/`.
- `tools/generate_reference_table.py:67-72` — hardcodes four output-target path
  constants (`REFERENCE_DOC_MCP`, `REFERENCE_DOC_DEPLOYMENT`, `REFERENCE_DOC_AGENT`,
  and the memory-module reference doc), each pointing at today's flat `docs/` layout.

## Reason for Change
These tools are exercised by pre-commit hooks and/or CI (e.g. `adr-invariant-matrix`,
`adr-reference-scoped` in `.pre-commit-config.yaml`). If they silently stop finding
their target file after the move, the checks they perform (dependency graph cycle
detection, needs-confirmation inventory sync, known-deviation sync, ADR structure/
reference integrity) go dark without raising an error — a dangerous failure mode where
nothing looks broken but the safety net is gone.

## Implementation Intent
For each tool listed in Problem, update its hardcoded directory assumption to point at
the new location the corresponding file(s) will occupy once moved (per the folder
classification in Dependencies). Prefer pointing `discover_md_files`/path constants
directly at the new specific subfolder (e.g. `docs/23_agent` instead of `docs` with a
`"05_agent_"` prefix) over making the glob blindly recursive across all of `docs/` —
this keeps each checker scoped to exactly the files it is meant to validate. Do not
change any filename string itself; only the directory portion of each constant/glob
call changes. `tools/generate_reference_table.py`'s four output-path constants each
get their directory component updated to match the new folder; the filename itself is
unchanged.

Note: `tools/generate_reference_table.py --type deployment` (without `--dry-run`)
already has a pre-existing, unrelated bug — it references
`docs/02_deployment-part2.md`, which does not exist in the repository under any name.
Do not attempt to fix this pre-existing bug as part of this issue; only update the
directory component of the constants that will remain otherwise unchanged.

## Target Files or Areas
- `tools/_docs_consistency_lib.py`
- `tools/check_docs_consistency.py`
- `tools/check_dependency_graph_cycles.py`
- `tools/check_needs_confirmation_inventory.py`
- `tools/check_known_deviation_sync.py`
- `tools/check_adr_structure.py`
- `tools/check_adr_reference.py`
- `tools/check_adr_invariant_matrix.py`
- `tools/generate_reference_table.py`
- Corresponding test files under `tests/tools/` for each of the above (confirm exact
  names during implementation)

## Required Changes
- `tools/_docs_consistency_lib.py` / `tools/check_docs_consistency.py`: change each
  domain's `discover_md_files` call site to target the file's new subfolder directly
  (e.g. call with `docs_dir=<repo_root>/docs/23_agent` for the agent domain), rather
  than scanning flat `docs/` with a prefix filter across the whole tree.
- `tools/check_dependency_graph_cycles.py`: update the path used to locate
  `GRAPH_DOC_NAME` to `docs/00_governance/00_governance_01_documentation-policy.md`.
- `tools/check_needs_confirmation_inventory.py`: update the path used to locate
  `INVENTORY_DOC_NAME` to `docs/00_governance/00_governance_03_issue-and-uncertainty-management.md`.
- `tools/check_known_deviation_sync.py`: update `ADR_DIR` to `docs/10_adr`, and
  `_GOVERNANCE_KNOWN_ISSUES_DOC`'s path to `docs/00_governance/...`.
- `tools/check_adr_structure.py`, `tools/check_adr_reference.py`,
  `tools/check_adr_invariant_matrix.py`: update every hardcoded `docs/adr` /
  `docs/adr-index.md` reference to `docs/10_adr`.
- `tools/generate_reference_table.py`: update the directory component of
  `REFERENCE_DOC_MCP`, `REFERENCE_DOC_DEPLOYMENT`, `REFERENCE_DOC_AGENT`, and the
  memory-module reference constant to each file's new folder.
- Update each affected tool's own test fixtures/assertions that hardcode the old flat
  path, to the new path.

## Constraints
- Do not change any filename string — only directory components.
- Do not fix the pre-existing, unrelated `docs/02_deployment-part2.md` bug in
  `tools/generate_reference_table.py` as part of this issue.
- These changes are only meaningful once the corresponding physical file move has
  happened (or is happening in the same coordinated migration) — see Dependencies.

## Acceptance Criteria
- Each of the 9 listed tools, run against a `docs/` tree where the relevant files
  already live in their new subfolder, finds and validates them exactly as it did
  against the old flat layout (same findings, same exit code).
- `uv run pre-commit run adr-invariant-matrix adr-reference-scoped --all-files`
  (or the equivalent direct tool invocations) passes after the corresponding files have
  moved.
- No tool in this list silently reports "0 files found" / "file not found" and exits 0
  after the move — a missing target must still be a loud failure, not a silent no-op.

## Testing Expectations
- Run each affected tool's existing test suite: `uv run pytest tests/tools/ -q` (or the
  specific test file names once confirmed) after updating both the tool and its test
  fixtures.
- Manually verify each of the 9 tools against the actual post-move `docs/` tree once
  the corresponding physical-move issue(s) have landed (see Dependencies).

## Documentation Impact
If `tools/TOOL_DESCRIPTIONS.md` documents any of these tools' expected `docs/` layout,
update it to reflect the new subfolder locations.

## Out of Scope
- Physically moving any file under `docs/` (tracked by separate per-area issues).
- Removing or shortening any filename prefix.
- The cross-reference resolution change in `tools/check_docs_structure.py` (tracked by
  a separate issue).
- Fixing the pre-existing `docs/02_deployment-part2.md` bug in
  `tools/generate_reference_table.py`.

## Dependencies
- Depends on: the folder classification decided during the docs-reorg investigation
  (which file moves to which of the 11 target folders) — this issue's path updates use
  that mapping and must stay consistent with it.
- Should land before (or in the same coordinated change window as) each corresponding
  area's physical-move issue, so the affected pre-commit hooks and CI checks do not go
  dark between the move and this fix.

## Unresolved Questions
- Exact test file names for each of the 9 tools were not individually re-verified in
  this issue — confirm each during implementation.

## AI Implementation Instruction
Change only the directory component of the path constants/glob calls listed in
Required Changes, in the 9 named tool files and their own tests. Do not touch any
`docs/*.md` content, do not perform any physical file move, and do not attempt to fix
the unrelated pre-existing `docs/02_deployment-part2.md` bug. If any of the 9 tools
turns out to have additional hardcoded `docs/` path assumptions not listed here, stop
and report them rather than silently expanding scope.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-140602
- **Related target files**: tools/_docs_consistency_lib.py, tools/check_docs_consistency.py, tools/check_dependency_graph_cycles.py, tools/check_needs_confirmation_inventory.py, tools/check_known_deviation_sync.py, tools/check_adr_structure.py, tools/check_adr_reference.py, tools/check_adr_invariant_matrix.py, tools/generate_reference_table.py

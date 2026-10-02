# Correct stale governance document path references across docs, tools, skills, and routing

## Priority
Medium

## Summary
Governance documents live at `docs/00_governance/governance_0[0-4]_*.md`, but many references across the repository use paths that do not exist: the old prefixed form `docs/00_governance_0N_*.md`, the directory-less form `docs/governance_0N_*.md`, and in `routing.md` the form `docs/00_governance/00_governance_03_*.md`. Correct these references to the actual paths so that humans, AI agents, and tool docstrings point at existing files. This is the follow-up for references outside the Policy's `## Area Canonical Maps` section, which `canon001` covers.

## Background
- The governance docs were renamed/consolidated into the four-plus-guide files under `docs/00_governance/` (see the dated correction comments in `tools/check_needs_confirmation_inventory.py`). `Explicit in code`
- Not every reference was updated during that rename.

## Problem
Repository search (2026-10-01):
- Old prefixed form `docs/00_governance_0N_*` appears in: `docs/00_governance/governance_01_documentation-policy.md` (outside and inside Area Canonical Maps), `skills/python-refactoring/path-c.md`, `tools/TOOL_DESCRIPTIONS.md`, `tools/check_adr_invariant_matrix.py`, `tools/check_adr_reference.py`, `tools/check_adr_structure.py`, `tools/check_compat_shims.py`, `tools/check_dependency_graph_cycles.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_issue_inventory_conformance.py`, `tools/check_known_deviation_sync.py`. `Explicit in code`
- `routing.md` "When to run which tool" tells agents to register markers in `docs/00_governance/00_governance_03_issue-and-uncertainty-management.md`, which does not exist. `Explicit in code`
- Directory-less form `docs/governance_0N_*` appears 42 times across 20 files, mostly ADRs under `docs/10_adr/`, area docs under `docs/21_rag/` and `docs/24_eventbus/`, and the governance docs themselves. `Explicit in code`
- Whether the directory-less form is an accepted shorthand convention in this repository is `Needs confirmation`; no document defining such a convention was found.
- Whether any tool reads one of these paths at runtime (versus only mentioning it in a docstring/comment) is `Needs confirmation` per file; a runtime read would be a behavior bug, not just a stale reference.

## Reason for Change
- `routing.md` is the entry point for AI task routing; a nonexistent path there directly misroutes agents.
- Stale paths in tool docstrings and descriptions make checker rules untraceable to their governing document.

## Implementation Intent
- Replace each stale reference with the actual existing path, preserving the referenced section names.
- For the directory-less form, first confirm whether it is an intended convention; if not, correct it, otherwise document the convention once and leave references unchanged.
- For each `tools/*.py` hit, determine whether it is a comment/docstring or a runtime path; treat runtime uses as bugs requiring a test.
- Edit only path strings; do not rewrite surrounding text.

## Target Files or Areas
- `routing.md`
- `skills/python-refactoring/path-c.md`
- `tools/TOOL_DESCRIPTIONS.md`
- `tools/check_adr_invariant_matrix.py`, `tools/check_adr_reference.py`, `tools/check_adr_structure.py`, `tools/check_compat_shims.py`, `tools/check_dependency_graph_cycles.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_issue_inventory_conformance.py`, `tools/check_known_deviation_sync.py`
- `docs/00_governance/governance_01_documentation-policy.md` (references outside `## Area Canonical Maps`)
- Files containing `docs/governance_0N_*` references under `docs/` (ADRs, RAG, EventBus, governance), pending the convention decision

## Required Changes
- Fix the `routing.md` path to the Needs Confirmation Inventory.
- Fix all `docs/00_governance_0N_*` references to `docs/00_governance/governance_0N_*`.
- Decide on the directory-less `docs/governance_0N_*` form and apply the decision consistently.
- For any tool that reads a stale path at runtime, fix it and add a regression test.

## Constraints
- Path-string edits only; no unrelated wording or formatting changes.
- `docs/` edits must follow `skills/DESIGN.md` Shared Vocabulary.
- Modified `tools/*.py` must pass the `routing.md` "Adding a new tool" validation sequence.

## Acceptance Criteria
- `grep -rnE "docs/00_governance_0[0-4]_|00_governance/00_governance_0" docs tools skills rules config routing.md AGENTS.md templates prompts` returns no matches outside the Policy's `## Area Canonical Maps` section (which `canon001` handles).
- The directory-less form is either eliminated or documented as an intended convention.
- Every corrected path resolves to an existing file.
- All checkers listed in Testing Expectations pass or show no new findings.

## Testing Expectations
- `uv run python tools/check_skills_references.py` (for `routing.md` and `skills/` edits)
- `uv run python tools/check_docs_structure.py` and `uv run python tools/check_docs_quality.py` (for `docs/` edits)
- `uv run python tools/check_tool_descriptions_sync.py`
- `uv run pytest tests/tools` and `uv run ruff check tools/`, `uv run mypy <each modified tool>` for modified tools
- Regression test for any runtime path fix

## Documentation Impact
Yes, path references only. No change in intent, boundaries, or rules.

## Out of Scope
- Area Canonical Maps rows in the Policy (`canon001`).
- Renaming or moving governance documents.
- References in `plans/done/`, `implementations/done/`, and `issues/done/` (historical records).

## Dependencies
- Coordinate with `canon001`, which edits the same Policy file; land in either order but avoid conflicting edits in `## Area Canonical Maps`.

## Unresolved Questions
- Is `docs/governance_0N_*` (no directory) an intended shorthand?
- Does any listed tool use a stale governance path at runtime?

## AI Implementation Instruction
- Run the repository search first and classify each hit (comment, docstring, runtime path, doc reference) before editing.
- Change only the path strings; keep diffs minimal.
- Stop and ask if the directory-less form turns out to be a deliberate convention.
- Do not touch historical `*/done/` directories.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-103636
- **Related target files**: routing.md, skills/python-refactoring/path-c.md, tools/TOOL_DESCRIPTIONS.md, tools/check_adr_invariant_matrix.py, tools/check_adr_reference.py, tools/check_adr_structure.py, tools/check_compat_shims.py, tools/check_dependency_graph_cycles.py, tools/check_docs_content_policy.py, tools/check_docs_quality.py, tools/check_docs_structure.py, tools/check_issue_inventory_conformance.py, tools/check_known_deviation_sync.py, docs/00_governance/governance_01_documentation-policy.md

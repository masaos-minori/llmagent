# Add a verified Markdown section move tool

## Priority
Low

## Summary
Add a tool that moves a text region between Markdown files verbatim, proves the text is unchanged, and reports the sizes, replacing the ad hoc scripts used for skill text moves.

## Background
Evidence (`Explicit in code`, by history): verbatim text moves were done five times on 2026-11-27 with one-off Python and one-off comparisons: one paragraph of `skills/plan-to-implementation-procedure/workflow.md` to its edge file (commit `a832d84f5`), and the four final-report sections of the pipeline skills (commit `eb202c0a2`). `AGENTS.md` Global Rule 7 asks for a tool after three repetitions. `tools/module_nodes.py` moves Python nodes only.

## Problem
Each move rewrites the extraction, the insertion, and the equality check by hand, and one run hit a heading-cycle gate that a tool could warn about.

## Reason for Change
Repeated code and review cost; the verbatim guarantee depends on a fresh script each time.

## Implementation Intent
A small tool with exact anchors, a mandatory equality check, and a dry run.

## Target Files or Areas
- `tools/move_markdown_section.py` (new)
- `tests/tools/test_move_markdown_section.py` (new)
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Arguments: source file, start anchor, end anchor (each exact text that occurs once; the end anchor optional for end of section), destination file, destination heading to append after or a heading to create, and an optional replacement text for the source region.
- Refuse an anchor that is missing or ambiguous; write both files atomically; verify that the whitespace-normalized region equals the text now in the destination; print source and destination sizes before and after.
- `--dry-run` prints both diffs and writes nothing; document the tool.

## Constraints
- The moved text is never edited by the tool.
- The tool stays under the 24576 B tools size gate.

## Acceptance Criteria
- [ ] A move of a region between two files leaves the text identical and reports the equality result.
- [ ] An ambiguous or missing anchor writes nothing and exits non-zero.
- [ ] `--dry-run` writes nothing.

## Testing Expectations
Unit tests with temporary files (identical text, ambiguous anchor, missing anchor, replacement text, dry run); ruff, mypy, bandit; `tools/check_tool_descriptions_sync.py`.

## Documentation Impact
Yes. The tool row.

## Out of Scope
- Python code moves (`module_nodes.py`); automatic detection of what to move.

## Dependencies
N/A: none

## Unresolved Questions
- `不明`: whether the tool should also warn about a heading cycle (`check_skills_heading_cycles.py` already detects it).

## AI Implementation Instruction
Reuse `tools/_atomic_write.py`; keep the tool read-only unless the move is requested.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120106
- **Related target files**: `tools/move_markdown_section.py`, `tests/tools/test_move_markdown_section.py`, `tools/TOOL_DESCRIPTIONS.md`

# Reduce the Documentation Policy below the docs structure size limit

## Priority
Medium

## Summary
`docs/00_governance/governance_01_documentation-policy.md` is about 31.3 KB. That is above the 24 KB per-file limit enforced by `tools/check_docs_structure.py`, so the structure check fails for this file. Bring it under the limit without losing any normative rule. Do this by removing duplicated content, or by moving a self-contained section to its own governance document that the Policy references.

## Background
- `tools/check_docs_structure.py` enforces a per-file size limit (24576 bytes). Its source comments explain that the limit was raised once already to make room for required governance content. `Explicit in code`
- Observed output on 2026-10-01: `governance_01_documentation-policy.md: size 31309 bytes exceeds 24576 byte limit`. `Explicit in code`
- Measured sizes of the largest sections: `## Claim Type Taxonomy` about 9.6 KB, `## Area Canonical Maps` about 3.5 KB, `## Software Runtime Dependency Graph` about 2.3 KB, `## Resolution Workflow` about 1.9 KB. `Explicit in code`
- `tools/check_dependency_graph_cycles.py` parses the `## Software Runtime Dependency Graph` section of this file. Moving or renaming that section affects the tool. `Explicit in code`

## Problem
- The structure check reports this file as non-conforming, so any task that edits the Policy cannot show a clean structure result.
- The file is the largest governance document, which makes it harder to load selectively. Selective loading is required by `AGENTS.md` Global Rule 1.

## Reason for Change
- Several open issues (`canon001`, `govpath001`, `langdoc001`) edit this file. Without a size reduction, each of them inherits a failing structure check.

## Implementation Intent
- Remove the work done by `canon001` from the size count first. If `canon001` removes or shrinks `## Area Canonical Maps`, measure again before doing anything else.
- Then prefer, in this order: removing content duplicated elsewhere (for example, the Claim Type Taxonomy subsections versus its summary table), then moving one self-contained section to a new governance document that the Policy references.
- If a section moves, update every reference to it, including tools that parse it by file and heading.
- Keep every normative rule. A move must not change wording beyond what the relocation requires.
- Do not raise the size limit in the checker.

## Target Files or Areas
- `docs/00_governance/governance_01_documentation-policy.md`
- A new file under `docs/00_governance/`, only if a section is moved
- `docs/00_governance/governance_00_document-guide.md` (navigation), if a new file is added
- `tools/check_dependency_graph_cycles.py` and `tools/TOOL_DESCRIPTIONS.md`, if the dependency graph section moves
- `config/documentation_canonical_sources.toml`, if a moved section is a registered canonical source

## Required Changes
- Measure the file size again after `canon001` lands.
- Pick the reduction approach and record the rationale.
- Apply the change and update all references and the tools that parse the file.

## Constraints
- Do not lose or reword any normative rule.
- Do not change the `check_docs_structure.py` size limit.
- A new governance document must meet the Front Matter, Related Documents, and Keywords requirements.
- Modified `tools/*.py` must pass the `routing.md` "Adding a new tool" validation sequence.

## Acceptance Criteria
- `uv run python tools/check_docs_structure.py "docs/00_governance/*.md"` reports no size finding for any governance file.
- Every normative rule that existed before the change is still present in the Policy or in a referenced governance document. Show a section-by-section mapping in the PR.
- `uv run python tools/check_dependency_graph_cycles.py` still parses the dependency graph and passes.
- No broken links.

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/00_governance/*.md"`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_dependency_graph_cycles.py`
- `uv run pytest tests/tools`, if any tool is changed
- `uv run python tools/check_tool_descriptions_sync.py`, if a tool or its description changes

## Documentation Impact
Yes. The governance documents are restructured. No rule changes.

## Out of Scope
- Changing the meaning of any governance rule.
- Size problems in other files. Five ADRs also exceed the limit; their size is affected by `langadr001`.
- The other structure-check findings across `docs/` (missing sections, broken links, front matter references).

## Dependencies
- Should follow `canon001`, which may shrink `## Area Canonical Maps`.
- Coordinate with `govpath001` and `langdoc001`, which also edit this file.

## Unresolved Questions
- If moving a section is needed, which one should move? The Claim Type Taxonomy is the largest candidate, but it is central to the Policy.

## AI Implementation Instruction
- Measure first. Do not split the file if de-duplication is enough.
- Record a section-by-section mapping, before and after.
- Do not reword rules. Stop and ask if a reduction seems to require a semantic change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-104656
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md, docs/00_governance/governance_00_document-guide.md, tools/check_dependency_graph_cycles.py, tools/TOOL_DESCRIPTIONS.md, config/documentation_canonical_sources.toml

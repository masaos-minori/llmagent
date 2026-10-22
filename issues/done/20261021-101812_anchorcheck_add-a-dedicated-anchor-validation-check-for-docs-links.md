# Add a dedicated anchor validation check for docs links

## Priority
Low

## Summary
Decide whether to add a dedicated check that validates the `#anchor` part of Markdown links in `docs/` against the target document's headings, and apply the decision.

## Background
`memo4.md` ("Unexecuted checks") lists a dedicated anchor check as not run; link reachability in `check_docs_structure.py` was used as a substitute. In `tools/_docs_consistency_lib.py`, the broken-link check splits a link target into file and anchor parts, resolves only the file part, and skips pure `#anchor` links within the same page. `tools/check_docs_structure.py` verifies `related:` entries as plain basenames without anchors. From this reading, the existing tools check that the target file exists, not that the anchor exists in it. This is based on reading the tools' source, not on running them against a stale anchor.

## Problem
A link such as `[text](other.md#some-heading)` still passes when `some-heading` no longer exists, for example after a heading rename or after compression removed a section. The cleanup relies on anchors staying valid, so such breakage is not detected.

## Reason for Change
The docs cleanup removes and renames sections. Dangling anchors are a named acceptance condition of that work (no dangling link or anchor), yet no tool verifies them.

## Implementation Intent
First confirm the gap by running the existing checks against a deliberately stale anchor fixture. If confirmed, extend the existing link check in the shared consistency library to resolve anchors against the target's headings, using the same slug rules as the renderer the docs use. Prefer extending the existing check over a new script, and start at Warning level.

## Target Files or Areas
- `tools/_docs_consistency_lib.py` (link check) or `tools/check_docs_structure.py` (link reachability); the owning tool is to be chosen during implementation
- `tests/tools/` (Unknown if a matching test file exists)
- `tools/TOOL_DESCRIPTIONS.md`
- `docs/00_governance/governance_04_documentation-checks.md` (if a rule is added)

## Required Changes
- Reproduce the gap with a stale anchor fixture against the current tools.
- Define the heading slug rule (case, punctuation, duplicate headings, Japanese-free English headings per the docs language policy).
- Implement anchor resolution in the chosen tool, including same-page `#anchor` links.
- Run on live `docs/`, triage findings (fix the link or the heading, or file follow-ups).
- Document the check in the tool description and, if it is a gate, in the Verification Matrix.

## Constraints
- Report-only first; no blocking gate on the existing corpus.
- Heading slugs must match how links are actually rendered; if the rendering rule is unknown, record it as an assumption and confirm it.
- Follow `routing.md` "Adding a new tool" validation for tool changes.

## Acceptance Criteria
- A link to a nonexistent anchor is reported; a link to an existing anchor is not.
- Same-page anchors are covered, or explicitly listed as an accepted limit.
- Findings on live `docs/` are triaged.
- Existing link, structure, and consistency checks still pass.

## Testing Expectations
- Unit tests: valid anchor, stale anchor, same-page anchor, duplicate heading.
- Smoke run on live `docs/`.
- `uv run ruff`, `uv run mypy <tool file>`, `uv run bandit <tool file>`.
- `uv run python tools/check_tool_descriptions_sync.py`, `check_docs_structure.py`, `check_docs_quality.py`.

## Documentation Impact
Yes if a gate or rule is added: `governance_04` and `tools/TOOL_DESCRIPTIONS.md`. Otherwise tool description only.

## Out of Scope
- Fixing every stale anchor found (triage separately).
- Domain coverage for EventBus and Shared/DB (separate issue).
- Changing the `related:` basename rule.

## Dependencies
Related open issues in the same batch: `domaincov` and `identmatch` (both extend `check_docs_consistency.py` or its library). Coordinate edit order if the link check lives in the shared library. Sibling-issue check: `compat001` and `compat002` do not touch these files.

## Unresolved Questions
- Which heading slug rule do the docs use when links are rendered?
- Should the check live in `check_docs_structure.py` or the shared consistency library?

## AI Implementation Instruction
Reproduce the gap before changing code; stop and report if the existing tools already catch a stale anchor. Extend an existing tool, keep findings at Warning, and do not edit docs content in the same change.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-101812
- **Related target files**: `tools/_docs_consistency_lib.py`, `tools/check_docs_structure.py`, `tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_04_documentation-checks.md`

# Detect enumeration generalization without universal wording after docs compression

## Priority
Low

## Summary
Decide whether to close the gap that the check for over-generalized enumerations after a docs compression only finds added lines containing universal words (`each`, `every`, and similar), and if so, extend verification to cover generalizations that use no such word.

## Background
`memo4.md` ("Remaining work", item 5) records that the search for compressions that generalized an enumeration is limited to added lines containing universal words. A generalization that does not use such a word is not found by that method. The routing tools table has no tool for this check (a search of `tools/` for compression or generalization checkers found none), so the check appears to have been performed ad hoc. This is an assumption from the memo, not verified against a tool.

## Problem
A compression that replaces an explicit list with a general statement, for example without `each` or `every`, can silently drop a concrete requirement and pass the current method.

## Reason for Change
The docs cleanup removes enumerations by design. Without a way to detect meaning loss in the non-universal-word case, the risk of dropping a constraint remains unverified.

## Implementation Intent
First decide whether a mechanical check is feasible and worth it. Candidate approaches, to be evaluated rather than assumed:

- Compare removed list items (bullets, table rows, backtick identifiers) against the replacement text of a docs diff and flag removed items that have no counterpart.
- Keep it as a manual review step in the cleanup procedure instead.

Prefer extending an existing docs tool over a new script (`routing.md` "When to run which tool", last paragraph).

## Target Files or Areas
- `tools/` (an existing docs check, if extended; otherwise Unknown)
- `docs/00_governance/governance_04_documentation-checks.md` (only if a rule is added)
- `prompts/08_document-sync.md` or the cleanup procedure (only if the manual step is chosen)

## Required Changes
- Confirm how the current check is performed and where it is recorded.
- Evaluate the approaches above on a real past docs diff and record the false positive and miss rate.
- Implement the chosen approach, or record the manual review step and its owner.

## Constraints
- A new check must be report-only (Warning) at first; it must not block on the existing corpus.
- Adding a check that is a tool requires `tools/TOOL_DESCRIPTIONS.md` sync and the lighter tool validation in `routing.md` "Adding a new tool".

## Acceptance Criteria
- The detection limit is either removed for the evaluated cases or recorded as an accepted limit with a manual review step.
- If a tool is added or extended: it runs on live repository data, passes lint, type check, and bandit, and is documented.
- The decision and its rationale are recorded in a canonical place, not only in `memo4.md`.

## Testing Expectations
- Unit tests with a fixture diff containing a generalization without universal wording.
- Manual smoke run on a real docs diff.
- `uv run python tools/check_tool_descriptions_sync.py` if a tool changes.

## Documentation Impact
Yes if a rule is added or the manual step is chosen: `governance_04` (Verification Matrix row) or the cleanup procedure. Otherwise none.

## Out of Scope
- Re-running the full docs cleanup.
- Identifier matching limits (separate issue).
- Changing any docs content.

## Dependencies
N/A: none (sibling-issue check: no open issue overlaps). Related to the identifier matching issue in the same batch; both may share one tool.

## Unresolved Questions
- Was the current check a script or an ad hoc command, and where is it recorded?
- Is a mechanical check worth its false positive rate compared with manual review?

## AI Implementation Instruction
Verify the current method before designing. Do not add a blocking gate. Keep changes minimal and stop to report if feasibility is not demonstrated.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-100336
- **Related target files**: `tools/`, `docs/00_governance/governance_04_documentation-checks.md`, `prompts/08_document-sync.md`

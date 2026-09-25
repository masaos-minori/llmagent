# Clarify redundant category field statement in 00_governance_02_documentation-metadata.md

## Priority
Low

## Summary
Rewrite the overly verbose sentence about the `category` field in `docs/00_governance/00_governance_02_documentation-metadata.md` line 22. The current phrasing is confusing and self-referential, making it unclear whether `category` is simply invalid or has some special conditional status.

## Background
Line 22 of the metadata document reads:
```
area: agent — Document area: one of `overview`, `deployment`, `rag`, `mcp`, `agent`, `eventbus`, `shared`, `governance`. ADR documents (`docs/adr/`) and security documents (`docs/00_security_*.md`) use `area: governance` — resolved 2026-09-14 (`NC-030`) rather than carrying their own top-level values, since both are cross-cutting governance/policy content rather than a distinct runtime area. The sole category-style field — `category` is not a valid front-matter key.
```

The last clause ("The sole category-style field — `category` is not a valid front-matter key.") is tacked onto the end of the `area` field description without clear structural separation. It mixes two unrelated concepts (the `area` field's allowed values and the non-existence of a `category` field) in a way that obscures both.

## Problem
The statement about `category` being invalid is embedded mid-sentence within the `area` field description. This makes it hard for readers to:
1. Parse which concept belongs to which metadata field
2. Find all rules about `category` (there are none elsewhere)
3. Understand whether `category` was once valid and was removed, or was never valid

## Reason for Change
Clarity and scannability. Each metadata field's description should cover only that field's rules. Cross-field negative constraints (e.g., "X does not exist") should be stated explicitly, not buried as a trailing clause.

## Implementation Intent
Move the `category` statement out of the `area` field description into its own short paragraph or bullet, either:
- As a separate bullet after the four required fields listing, or
- As a brief note under "Existing Metadata Fields" stating clearly that `category` is not a recognized front-matter key and should not be used

## Target Files or Areas
- `docs/00_governance/00_governance_02_documentation-metadata.md`

## Required Changes
- Extract the `category` statement from the end of the `area` field description (line 22)
- Place it as a clearly separated statement (new bullet or paragraph) immediately after the four required fields list
- Reword for clarity: e.g., "`category` is not a valid front-matter key and should not be used."

## Constraints
- Do not introduce a new `category` field or imply one exists
- Do not modify any other metadata field descriptions
- Preserve the NC-030 resolution reference in the `area` description (it belongs there)

## Out of Scope
- Adding `category` as a valid field
- Modifying the terminology glossary
- Changing the four required fields or their allowed values
- Modifying any other governance document

## Dependencies
- None

## Acceptance Criteria
- [ ] The `category` statement is no longer embedded within the `area` field description
- [ ] The `category` statement appears as a clearly separated bullet or paragraph
- [ ] Wording is unambiguous: `category` is not a valid front-matter key
- [ ] NC-030 resolution reference remains in the `area` field description
- [ ] No other content in `00_governance_02_documentation-metadata.md` modified
- [ ] `uv run python tools/check_docs_structure.py docs/00_governance/00_governance_02_documentation-metadata.md` passes

## Testing Expectations
Not required — documentation-only change. Manual review for clarity improvement.

## Documentation Impact
This is a wording clarification in a metadata convention document. One sentence is restructured for readability.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Edit only `docs/00_governance/00_governance_02_documentation-metadata.md`. In the `## Existing Metadata Fields` section, extract the trailing clause about `category` from the `area` bullet (line 22). Add a new bullet point after the four required fields list: `- **category**: Not a valid front-matter key. Do not use.` Ensure the `area` bullet still contains the NC-030 resolution reference. Verify `check_docs_structure.py` reports no new issues.

## Traceability
- **Workflow phase**: issue-creator
- **Source finding**: L-3 from governance folder audit (2026-09-25)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-125053
- **Related target files**: docs/00_governance/00_governance_02_documentation-metadata.md

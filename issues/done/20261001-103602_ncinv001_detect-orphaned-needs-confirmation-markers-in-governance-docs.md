# Detect orphaned Needs Confirmation status markers in governance docs

## Priority
Medium

## Summary
`tools/check_needs_confirmation_inventory.py` skips every governance document when looking for untracked inline Needs Confirmation markers. Because of this, the 8 `(Needs Confirmation — path does not exist in repository ...)` status markers in `docs/00_governance/governance_01_documentation-policy.md` are not reported, although the central Needs Confirmation Inventory has no Active Item for them. Make the checker distinguish governance text that defines or discusses the label from actual unresolved-item markers, so orphaned markers in governance docs are detected.

## Background
- The Needs Confirmation Inventory in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` is the single central place for unresolved items; a marker left only in an individual document is not allowed.
- The checker excludes `_GOVERNANCE_META_DOCS` (all five `governance_0[0-4]_*.md` files) in `check_untracked_inline_markers()`, because those documents define and cross-reference the label itself. `Explicit in code`

## Problem
- `docs/00_governance/governance_01_documentation-policy.md` contains 8 Area Canonical Maps rows whose Status cell is an unresolved `Needs Confirmation` marker, and the Inventory `### Active Items` states no active item remains open. `Explicit in code` (document content)
- The checker reports nothing for these rows because the whole file is excluded. `Explicit in code`
- Untracked markers are reported at `WARNING` severity and the checker exits 0 even when such warnings exist (observed 2026-10-01 with 8 warnings in `docs/23_agent/` and `docs/21_rag/`). Whether warnings should fail verification is `Needs confirmation`.

## Reason for Change
- The work in `canon001` requires proving that no orphaned Needs Confirmation marker remains in the Policy; the current checker cannot provide that evidence, so verification would rely on manual grep only.

## Implementation Intent
- Keep governance docs exempt for definitional/discussion uses of the label, but detect marker uses that denote an unresolved item (for example a Needs Confirmation status value in a table cell, or a parenthesized status annotation).
- Prefer a narrow, explicit rule (pattern or section-scoped) over removing the exemption entirely, to avoid flooding false positives from the label's definition text.
- Keep the output format and existing severities unless the confirmed intent requires change.

## Target Files or Areas
- `tools/check_needs_confirmation_inventory.py` (`_GOVERNANCE_META_DOCS` handling in `check_untracked_inline_markers`)
- `tests/tools/test_check_needs_confirmation_inventory.py`
- `tools/TOOL_DESCRIPTIONS.md` (if documented behavior changes)
- `docs/00_governance/governance_04_documentation-checks.md` (only if the check's documented rule changes)

## Required Changes
- Define which marker forms inside governance docs count as unresolved-item markers.
- Report those markers when they have no matching Inventory entry.
- Add regression tests: a governance doc fixture with a definitional mention (not reported) and a status-cell marker (reported).
- Record the decision on whether untracked-marker warnings should cause a non-zero exit.

## Constraints
- Do not edit `docs/00_governance/governance_01_documentation-policy.md` content in this issue; resolving its markers is `canon001`.
- Do not register Inventory entries in this issue.
- Follow the `routing.md` "Adding a new tool" validation sequence for modified `tools/*.py`.

## Acceptance Criteria
- Against the current repository, the checker reports the Area Canonical Maps status markers in `governance_01_documentation-policy.md` as untracked (until `canon001` resolves them).
- Definitional mentions of the label in governance docs are not reported.
- New regression tests fail before and pass after the change; existing tests pass.
- The exit-status decision for untracked markers is implemented or documented.

## Testing Expectations
- `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py`
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit` on `tools/check_needs_confirmation_inventory.py`
- Smoke run: `uv run python tools/check_needs_confirmation_inventory.py` on the live `docs/`
- `uv run python tools/check_tool_descriptions_sync.py`

## Documentation Impact
Possibly. If the checker's rule changes, update the check description in `tools/TOOL_DESCRIPTIONS.md` and, if it documents this rule, `docs/00_governance/governance_04_documentation-checks.md`.

## Out of Scope
- Registering or resolving the existing untracked markers in `docs/23_agent/` and `docs/21_rag/`.
- Resolving the Policy's Area Canonical Maps markers (`canon001`).
- Changing the Inventory entry format.

## Dependencies
- Supports `canon001` verification. If `canon001` lands first, test with fixtures rather than live Policy content.

## Unresolved Questions
- Exact boundary between a definitional mention and an unresolved-item marker in governance docs.
- Should untracked-marker findings make the checker exit non-zero?

## AI Implementation Instruction
- Inspect every current `needs confirmation` occurrence in the five governance docs and classify it before designing the rule.
- Keep the exemption narrow; do not remove it wholesale.
- Do not modify any `docs/` content to make the checker pass.
- Stop and report if no rule can separate the two uses without false positives.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-103602
- **Related target files**: tools/check_needs_confirmation_inventory.py, tests/tools/test_check_needs_confirmation_inventory.py, tools/TOOL_DESCRIPTIONS.md, docs/00_governance/governance_04_documentation-checks.md

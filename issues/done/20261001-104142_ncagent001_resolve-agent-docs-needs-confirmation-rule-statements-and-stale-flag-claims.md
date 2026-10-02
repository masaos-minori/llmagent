# Resolve Needs Confirmation rule statements and stale flag claims in Agent docs

## Priority
Low

## Summary
`tools/check_needs_confirmation_inventory.py` reports six untracked Needs Confirmation markers in `docs/23_agent/`. None of them is an unresolved item: four restate the rule for how Needs Confirmation should be used, and two claim that "differences between legacy documentation and current code are explicitly marked with `Needs Confirmation` flags", although no such flag exists anywhere in `docs/23_agent/`. Replace the duplicated rule statements with a reference to the canonical governance document, correct the stale claims, and leave the Agent docs with no untracked markers and no false statements about flags.

## Background
- How to handle Needs Confirmation items is defined by `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 2) and the Documentation Policy. Area docs restating that rule duplicate a canonical source. `Documentation only`
- The checker exempts only the five governance docs from untracked-marker detection, so rule statements in area docs are reported as untracked items. `Explicit in code`

## Problem
Checker output (2026-10-01), classified by reading each line in context:
- `docs/23_agent/agent_00_document-guide.md`, `## Responsibility Boundary`: "handling of Known Issues / Deprecated Items / Needs Confirmation entries" — scope statement, not an item.
- `docs/23_agent/agent_00_document-guide.md`, `## Key Constraints`: "Unrecoverable design rationales must be explicitly marked `Needs Confirmation`..." — rule restatement.
- `docs/23_agent/agent_13_reference-api.md`, `## Key Constraints` in Part 1 and Part 2 (same sentence twice): "Incomplete implementation changes must be explicitly marked with a `Needs Confirmation` flag." — rule restatement.
- `docs/23_agent/agent_13_reference-api.md`, `## Known Limitations` in Part 1 and Part 2 (same sentence twice): "Differences between legacy documentation and current code are explicitly marked with `Needs Confirmation` flags." — factual claim; repository search finds no such flag in `docs/23_agent/` other than these sentences, so the claim is stale. `Explicit in code` (repository search)

## Reason for Change
- Six false "untracked" findings hide genuine findings in checker output and make the Needs Confirmation check unusable as verification evidence.
- The stale claim misleads readers into believing legacy/code differences have been flagged.

## Implementation Intent
- Per line, choose the minimal correct action:
  - rule restatements: replace with a short reference to the canonical governance rule (or remove if the reference already exists in the doc's Related Documents);
  - scope statement: keep the meaning, but phrase it as a reference to the governance inventory rather than as a marker-like label, only if needed to clear the finding without losing meaning;
  - stale claims: remove, or replace with an accurate statement; if actual legacy/code differences are known, register them in the central Inventory instead.
- Do not make the finding disappear merely by changing capitalization or spelling of the label; the change must be justified by removing duplication or a false claim.
- If the team prefers keeping these statements, the alternative is a checker-side rule distinguishing definitional uses (issue `ncinv001`); record that decision instead of editing docs.

## Target Files or Areas
- `docs/23_agent/agent_00_document-guide.md` (`## Responsibility Boundary`, `## Key Constraints`)
- `docs/23_agent/agent_13_reference-api.md` (`## Key Constraints` and `## Known Limitations`, both Part 1 and Part 2)

## Required Changes
- Replace or remove the four rule-restatement sentences as described in Implementation Intent.
- Remove or correct the two stale "explicitly marked with Needs Confirmation flags" claims.
- Keep Part 1 and Part 2 of `agent_13_reference-api.md` consistent with each other.
- Record the per-line decision (kept / replaced / removed and why) in the plan or PR.

## Constraints
- Edits limited to the listed sentences; do not restructure the documents.
- `docs/` text must follow `skills/DESIGN.md` Shared Vocabulary (English, no source-code line numbers, no concrete config values).
- Do not register non-items in the central Inventory just to silence the checker.

## Acceptance Criteria
- `uv run python tools/check_needs_confirmation_inventory.py` reports no untracked marker in `docs/23_agent/`, or each remaining one has a recorded justification tied to `ncinv001`.
- No sentence in `docs/23_agent/` claims that Needs Confirmation flags exist when they do not.
- The rule for using Needs Confirmation is stated only in the governance canonical source, referenced from the Agent docs where needed.

## Testing Expectations
Documentation-only. Run and record:
- `uv run python tools/check_needs_confirmation_inventory.py`
- `uv run python tools/check_docs_structure.py "docs/23_agent/*.md"` and `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Documentation Impact
Yes. Remove duplicated governance rules and a false claim from Agent docs; no change in design intent.

## Out of Scope
- Changing `tools/check_needs_confirmation_inventory.py` (issue `ncinv001`).
- The RAG markers (issue `ncrag001`).
- Other observations in `agent_00_document-guide.md` found during investigation and not addressed here: `## Key Constraints` contains what look like leftover authoring instructions ("Do not modify other documents in the `agent_*.md` set.", "Do not add new content beyond what exists in the current document.", "Do not change the doc set directory structure."), and the `### Related ADRs` link descriptions are written in Japanese. These are tracked in issues `docleft001` and `langdoc001`.
- The Part 1 / Part 2 duplication of meta sections in `agent_13_reference-api.md` beyond the listed sentences (issue `agentref001`).

## Dependencies
- Related to `ncinv001` (alternative checker-side resolution for definitional uses).

## Unresolved Questions
- Are there actual legacy-documentation/code differences in the Agent reference API that should have been flagged? If so, they must be registered in the central Inventory rather than silently dropped with the stale claim.
- Should area docs keep any statement about Needs Confirmation handling, or only reference governance?

## AI Implementation Instruction
- Read each flagged sentence in context and record a per-line decision before editing.
- Change only those sentences; do not touch the out-of-scope observations.
- Do not alter the label text purely to evade the checker.
- Stop and report if any sentence turns out to describe a real unresolved item.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-104142
- **Related target files**: docs/23_agent/agent_00_document-guide.md, docs/23_agent/agent_13_reference-api.md

# Define the Blocking field in the Needs Confirmation inventory

## Priority
Low

## Summary
Define the meaning and allowed values of the `Blocking` field of Needs Confirmation entries in `governance_03`, and make NC-041's empty `Blocking` value consistent with that definition and with the inventory checker.

## Background
A document consistency review (memo4, 34th edition, finding V34-02) reported that the required `Blocking` field of NC-041 is empty and proposed that the checker treat empty required fields as errors, with allowed values such as `Blocking` / `Non-blocking`.

Repository evidence differs from the review's assumption:

- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` requires fifteen fields per NC entry, including `Blocking`, but defines no allowed values or meaning for it (Priority, Status, Owner and other fields have value sections).
- `tools/check_needs_confirmation_inventory.py` (`check_blocking_reference`) treats `Blocking` as a reference to another NC id and warns when a non-empty value is not a known NC id. An empty value is explicitly accepted.
- The `Blocking status` field with `Blocking` / `Non-blocking` values belongs to Part 3 (Canonical Source Conflict), not Part 2.

So the empty value in NC-041 is not a checker violation today, but the governance document leaves the field undefined, so an empty value cannot be distinguished from "not yet assessed". The reviewer's proposed `Blocking` / `Non-blocking` values would conflict with the checker's NC-id semantics.

Sibling-issue check: open issues under `issues/` that mention blocking concern the governance_04 gate matrix and do not cover this field. `issues/20261021-104507_gitdrift_register-the-github-mcp-criticality-disagreement-in-the-configuration-drift-inventory.md` edits the same governance document but a different part.

## Problem
The meaning of `Blocking` in a Needs Confirmation entry is undefined in governance, and the checker and the review disagree about its semantics. An entry may carry an empty value with no way to tell "blocks nothing" from "unassessed". For NC-041, which concerns a disabled mandatory component, the release/deployment impact is not recorded anywhere.

## Reason for Change
The inventory's stated purpose is that entries are trackable and actionable. A mandatory field with no definition cannot be used for release decisions, and a reviewer can reasonably misread it (as happened in the review). Resolving the semantics first also prevents a wrong checker rule from being added.

## Implementation Intent
Decide the semantics, document them next to the other field value sections of Part 2, and align the checker and NC-041 with the decision.

- Option A: keep the current checker semantics (a reference to the NC id that this item blocks, or an explicit none value) and document it, including how an unassessed state is written.
- Option B: change the field to a release/deployment blocking classification and migrate the checker accordingly.
- Prefer Option A unless the owner needs release gating in this field, because it matches existing checker behavior and requires no migration.
- After the definition is fixed, consider whether an empty value should become a finding; do this only if the definition makes empty ambiguous. Do not make it a blocking gate on the existing corpus.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 2 field value definitions, NC-041 `Blocking`)
- `tools/check_needs_confirmation_inventory.py` (only if the definition requires a checker change)
- `tests/test_check_needs_confirmation_inventory.py`, only if the checker changes

## Required Changes
- Obtain the owner's decision between Option A and Option B (or another definition).
- Add a "Blocking Values" definition (meaning, allowed values, how empty or unassessed is written) to Part 2 of `governance_03`.
- Set a valid `Blocking` value for NC-041 under the chosen definition.
- Align `check_needs_confirmation_inventory.py` with the definition, or record that no checker change is needed.
- If the checker changes, add or update tests and the `tools/TOOL_DESCRIPTIONS.md` row.

## Constraints
- Do not apply the `Blocking` / `Non-blocking` vocabulary of Part 3 to Part 2 without an explicit decision.
- Docs under `docs/` are written in English.
- A new check must report-only or use a baseline; it must not fail the existing corpus.
- Follow `skills/DESIGN.md` Docs content policy.

## Acceptance Criteria
- `governance_03` Part 2 defines the meaning and allowed values of `Blocking`, including the unassessed case.
- NC-041's `Blocking` holds a value that is valid under that definition.
- The checker's behavior matches the documented definition, or the issue records that no change was needed.
- The checkers listed under Testing Expectations pass.

## Testing Expectations
- `uv run python tools/check_needs_confirmation_inventory.py`
- `uv run python tools/check_issue_inventory_conformance.py`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- If the checker changes: its tests via `uv run pytest`, then ruff, mypy with the explicit file path, bandit, and `uv run python tools/check_tool_descriptions_sync.py` per `routing.md` "Adding a new tool".

## Documentation Impact
Yes. `governance_03` Part 2: field value definition for `Blocking`, and the NC-041 entry. `tools/TOOL_DESCRIPTIONS.md` only if checker behavior changes.

## Out of Scope
- Deciding the `github` required/optional outcome of NC-041.
- Adding the same empty-value check to Known Issue, Canonical Source Conflict, and Configuration Drift schemas (the review's last recommendation); file separately if wanted after this definition exists.
- Changing the Part 3 `Blocking status` vocabulary.
- Changing the governance_04 gate matrix.

## Dependencies
- Related: `issues/20261021-100235_nc041_resolve-the-github-mcp-server-required-classification-disagreement.md` (NC-041 owner decision; independent of this definition).
- Related: `issues/20261021-104507_gitdrift_register-the-github-mcp-criticality-disagreement-in-the-configuration-drift-inventory.md` (same document, different part; whether Part 4 gains a blocking field depends on the definition chosen here).

## Unresolved Questions
- Which semantics does the owner want for `Blocking` (NC-id reference, or release/deployment classification)?
- How should an unassessed value be written, and should empty be flagged afterwards?
- Should the empty-value check extend to the other inventory schemas? Assumption: no, not in this issue.

## AI Implementation Instruction
Do not adopt the review's `Blocking` / `Non-blocking` values or an empty-value error rule before the owner decides the semantics; stop and report if no decision is recorded. Change only the files listed. Do not alter the NC-041 evidence or decision content. Keep any checker change report-only.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-104533
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `tools/check_needs_confirmation_inventory.py`

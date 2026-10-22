# Register the github-mcp criticality disagreement in the Configuration Drift inventory

## Priority
Medium

## Summary
Make the central governance inventory consistent about the `github-mcp` criticality disagreement: either register it as an active Configuration Drift entry, or document explicitly why the Needs Confirmation entry NC-041 alone is the correct record until the owner decides.

## Background
A document consistency review (memo4, 34th edition, finding V34-01, rated High by the reviewer) observed that `docs/00_governance/governance_03_issue-and-uncertainty-management.md` records NC-041 with concrete evidence that the deployed `github` MCP configuration (`required = false`, `startup_mode = "none"` in `config/agent.toml`, commit `4e2442a75`) disagrees with the approved classification (`github` = `required` in `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, ADR-004 Decision Group 3 item 13). The same document's Part 4 (Configuration Drift) states "No active Configuration Drift items remain."

Part 4 defines Configuration Drift as a discrepancy between deployed and approved operational values. By that definition the `github` disagreement qualifies, so the two inventory parts describe the same state differently.

Priority is set to Medium rather than the reviewer's High: the cause is an operational one (`GITHUB_TOKEN` not yet provisioned), the owner decision itself is already tracked by the open NC-041 issue, and this issue only concerns how the inventory represents the state.

Sibling-issue check: the open issue `issues/20261021-100235_nc041_resolve-the-github-mcp-server-required-classification-disagreement.md` resolves NC-041 by obtaining the owner decision. It does not cover Part 4 of the inventory. If that issue is completed first and the disagreement is resolved, this issue must be re-verified against current source and may be closed as no longer applicable.

## Problem
Part 2 (NC-041) and Part 4 ("No active Configuration Drift items remain") of `governance_03` give contradictory pictures of the same deployed-versus-approved disagreement. Release and deployment decisions that read only Part 4 would conclude there is no drift.

Unknown: whether the project intends NC-041 to be the sole record while the question "approved reclassification or deviation" is undecided. The governance document does not state a rule for this case, so the intended relationship between Part 2 and Part 4 is not confirmed.

## Reason for Change
An inventory whose parts contradict each other cannot be trusted for release gating. The disagreement concerns a mandatory component that was disabled by configuration alone, which ADR-004 prohibits, so its visibility in the drift inventory matters.

## Implementation Intent
Decide the relationship between Needs Confirmation and Configuration Drift entries for a not-yet-decided disagreement, then record it so the inventory is internally consistent.

- Prefer registering a Configuration Drift entry for `github-mcp` (decision target: component criticality and startup availability; deployed value: `required = false`, `startup_mode = "none"`; approved value: `required` per the classification table and ADR-004), cross-referencing NC-041 rather than duplicating its content.
- If the project chooses NC-041 as the sole record, state that rule in the Part 2 / Part 4 purpose text instead, and keep Part 4's "no active items" statement accurate under that rule.
- Keep the owner decision itself out of this issue; it stays with the NC-041 issue.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 2 NC-041 entry, Part 4 Configuration Drift)
- `tools/check_needs_confirmation_inventory.py` and any Part 4 checker, only if a consistency check is added (see Unresolved Questions)

## Required Changes
- Confirm with the owner which representation is intended (Drift entry, or NC-041 only with a stated rule).
- Apply the chosen representation in `governance_03` so Part 2 and Part 4 no longer contradict each other.
- If a Drift entry is added, fill all six fields required by the Part 4 entry template (ID, Decision target, Deployed value description, Approved operational value description, Severity, Status) and cross-reference NC-041.
- State in the entry how long the entry remains (until deployed and approved values agree, or the approved value is formally changed), consistent with Part 4's removal rule.

## Constraints
- Do not change `config/agent.toml` or the classification table; the owner decision is out of scope.
- Do not print or store `GITHUB_TOKEN` values.
- Docs under `docs/` are written in English.
- ADR-004 Decision text must not change.
- Follow `skills/DESIGN.md` Docs content policy: reference canonical sources instead of copying implementation detail.

## Acceptance Criteria
- Part 2 and Part 4 of `governance_03` describe the `github` disagreement consistently: either an active Drift entry exists with all six fields, or a stated rule explains why none is required.
- If a Drift entry exists, it cross-references NC-041 and does not duplicate NC-041's full evidence text.
- The Part 4 statement "No active Configuration Drift items remain" is accurate after the change.
- The checkers listed under Testing Expectations pass.

## Testing Expectations
- `uv run python tools/check_needs_confirmation_inventory.py`
- `uv run python tools/check_issue_inventory_conformance.py`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- If a `tools/` file changes: ruff, mypy (explicit path), bandit, and `uv run python tools/check_tool_descriptions_sync.py` per `routing.md` "Adding a new tool".

## Documentation Impact
Yes. `governance_03` Part 2 and Part 4: the relationship between a Needs Confirmation entry and a Configuration Drift entry for an undecided disagreement, and the active Drift entry if one is added.

## Out of Scope
- Deciding whether `github` is `required` or optional.
- Editing `config/agent.toml`, the classification table, or ADR-004.
- Adding a `Blocking` field to the Part 4 template (tracked separately under the Blocking field definition issue, and only if the owner wants it).
- Provisioning `GITHUB_TOKEN`.

## Dependencies
- Related: `issues/20261021-100235_nc041_resolve-the-github-mcp-server-required-classification-disagreement.md` (resolves the underlying disagreement; if completed first, re-verify this issue and close it if the Drift entry is no longer needed).
- Related: `issues/20261021-104533_blockingdef_define-the-blocking-field-in-the-needs-confirmation-inventory.md` (filed in the same session; independent, but both edit `governance_03`).

## Unresolved Questions
- Should an undecided disagreement be recorded in Part 4 immediately, or only in NC-041 until the owner decides?
- Should the Part 4 entry template gain a release/deployment blocking field (the reviewer's recommendation 6), and if so, with which allowed values?
- Who is the owner for the Drift entry? NC-041 currently has `Assigned To: Unknown`.

## AI Implementation Instruction
Do not decide the `github` required/optional outcome. Obtain the representation choice first; if it is not recorded, stop and report. Change only `governance_03` (and a checker only if explicitly agreed). Do not modify the ADR Decision, `config/agent.toml`, or unrelated governance parts. Do not include secrets.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-104507
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `tools/check_needs_confirmation_inventory.py`

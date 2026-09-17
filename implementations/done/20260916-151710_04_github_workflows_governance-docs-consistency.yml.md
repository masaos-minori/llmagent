## Goal

Wire `tools/check_issue_inventory_conformance.py` into `.github/workflows/governance-docs-consistency.yml`: add it to both the `push` and `pull_request` `paths:` filters, and add a new step running it, following the existing `check_needs_confirmation_inventory.py` step's exact pattern.

## Scope

- Add `tools/check_issue_inventory_conformance.py` to the `paths:` filter under both `push` and `pull_request` events.
- Add a new CI step that runs the checker, following the existing `check_needs_confirmation_inventory.py` step's pattern exactly.

## Assumptions

- The existing CI workflow follows the pattern established by `check_needs_confirmation_inventory.py`:
  - A `paths:` entry listing the tool script itself.
  - A CI step that runs `python tools/check_needs_confirmation_inventory.py` (or equivalent).
- The workflow file currently has 63 lines with existing `check_needs_confirmation_inventory.py` step and path entries confirmed at lines 7, 17, 42-45 based on Repository Evidence.

## Design decisions

- Follow the exact pattern of the existing `check_needs_confirmation_inventory.py` step — same YAML indentation, same command format, same trigger placement.
- Do not modify any other steps or sections of the workflow.

## Alternatives considered

- Using a different CI mechanism — rejected because the Plan's intent is to wire the checker into the existing governance-docs-consistency workflow.

## Implementation
### Target file

`.github/workflows/governance-docs-consistency.yml`

### Procedure

1. Locate the `push` event's `paths:` filter (approximately line 7 based on Reference Files evidence).
2. Add `tools/check_issue_inventory_conformance.py` to the `paths:` list under `push`.
3. Locate the `pull_request` event's `paths:` filter (approximately line 17 based on Reference Files evidence).
4. Add `tools/check_issue_inventory_conformance.py` to the `paths:` list under `pull_request`.
5. Locate the existing `check_needs_confirmation_inventory.py` step (approximately line 42-45 based on Reference Files evidence).
6. Add a new CI step after the existing one, following the exact same pattern but referencing `check_issue_inventory_conformance.py`.

### Method

Current state: The workflow file has existing `paths:` entries and a `check_needs_confirmation_inventory.py` step.

Required additions:
```yaml
# Under push.paths:
- tools/check_issue_inventory_conformance.py

# Under pull_request.paths:
- tools/check_issue_inventory_conformance.py

# New CI step (following the existing check_needs_confirmation_inventory.py pattern):
- name: Check issue inventory conformance
  run: python tools/check_issue_inventory_conformance.py
```

The exact YAML structure may vary slightly depending on the current file layout — verify against the live document at implementation time.

### Details

The new CI step should use the same indentation level as the existing `check_needs_confirmation_inventory.py` step. The `run:` command should follow the same format — `python <script_name>` without additional arguments or flags.

## Compatibility considerations

- This is a CI configuration change — no application code compatibility impact.
- The new CI step will only run when `tools/check_issue_inventory_conformance.py` changes, minimizing unnecessary CI runs.

## Security considerations

- No security impact — the CI step runs a local Python script that reads Markdown files and reports findings; it does not access external resources or credentials.

## Rollback considerations

- If the CI step is found to produce false positives, the step can be removed from the workflow without removing the entire tool.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `.github/workflows/governance-docs-consistency.yml` | CI syntax check | `uv run yamllint .github/workflows/governance-docs-consistency.yml` (if available) | Passes with no new findings |
| `.github/workflows/governance-docs-consistency.yml` | Manual review | Review the added paths entry and CI step against the existing pattern | Matches the existing pattern exactly |

## Completion criteria

- `tools/check_issue_inventory_conformance.py` appears in both `push` and `pull_request` `paths:` filters.
- A new CI step exists that runs the checker, following the exact pattern of the existing `check_needs_confirmation_inventory.py` step.
- The CI workflow file remains valid YAML.
- The new CI step would trigger correctly when `tools/check_issue_inventory_conformance.py` changes.

## Out of scope

- Modifying any other CI workflow files.
- Adding additional CI steps beyond the one required for this checker.
- Changing the existing `check_needs_confirmation_inventory.py` step.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260915-200449_gov03_add-conformance-and-referential-integrity-checks-for-the-issue-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-151710_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-151710
- **Related target files**: .github/workflows/governance-docs-consistency.yml

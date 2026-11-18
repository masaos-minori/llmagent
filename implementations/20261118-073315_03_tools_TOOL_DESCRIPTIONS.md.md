# Procedure: tools/TOOL_DESCRIPTIONS.md - the authoring rule in the plan_dependency_order.py row

## Goal

State the dependency-authoring rule and the prose-fallback consequence in the tool description of
`tools/plan_dependency_order.py`, so a reader of the tool docs learns the same rule the Plan template
states (sibling procedure document).

## Scope
**Release unit**: N/A: not part of a release unit

- Add one bullet to the detailed section of the `plan_dependency_order.py` description stating the
  authoring rule and the fallback consequence. (REQ-003)
- Leave the summary table row and all other tool rows untouched. (REQ-003)

## Assumptions

- Guidance-only is the chosen option; the maintainer confirmation recorded as UNK-01 gates Phase 2
  execution and this edit does not run before it lands. (Plan Assumption)
- The tool behavior is unchanged (REQ-005); the added bullet describes existing behavior: prose paths
  in the `Dependencies` line are read as phase `all` dependencies with a `prose-dependency` warning,
  and a named path under `plans/done/` or `implementations/done/` resolves by existence only.
  (Verified 20261118 against the tool and its test module.)
- `tools/TOOL_DESCRIPTIONS.md` is edited row-level by several batch plans; re-read the current
  `plan_dependency_order.py` rows immediately before editing and touch no other tool's rows
  (Plan UNK-02).

## Design decisions

- Copy the canonical wording's substance from `templates/plan.md` (sibling procedure document) so AC-3
  compares three matching statements: "Record a must-wait cross-plan dependency as a structured
  `Depends on` bullet, never as a path in the prose `Dependencies` line. A prose path is read as a
  dependency on the whole chain (`all`) with a `prose-dependency` warning; sequencing-only notes
  therefore name the other Plan by title or id."
- The rule goes into the detailed section as a new bullet after the first bullet, not into the summary
  table row: other tools' caveats sit in the detailed section, and the summary row stays a one-line
  capability statement.

## Alternatives considered

- Rewording the summary table row. Rejected: the row states inputs and modes; behavioral caveats live
  in the detailed section throughout the file.
- Changing the `--json` or `blocked (missing file)` bullets. Rejected: they already describe the gate
  semantics the rule leans on; no gap to fill.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md` (exists)

### Procedure

1. Re-read the current `plan_dependency_order.py` summary row and detailed section (the file is
   edited by sibling batch plans; do not trust cached line numbers).
2. Insert the authoring-rule bullet as the second bullet of the detailed section, after the
   capability bullet and before the `--json` bullet.
3. Leave the summary row, the `--json` bullet, and the `blocked (missing file)` gate bullet unchanged.

### Method

Single bullet insertion inside the existing detailed section; no row moves, no other tool's section
touched.

### Details

- The wording must stay accurate against the tool's actual behavior; the sibling test procedure
  document (`tests/tools/test_plan_dependency_order.py`) pins that behavior.

## Compatibility considerations

- `tools/check_tool_descriptions_sync.py` compares this file against the tools' docstrings/CLI help;
  the added bullet documents existing behavior, so the sync check stays green.
- Sibling batch plans edit other rows of the same file; row-level edits keep those independent
  (Plan UNK-02).

## Security considerations

- None; documentation edit.

## Rollback considerations

- Removing the added bullet restores the previous row; no other content changes.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` passes.
- `uv run python tools/check_workitem_structure.py --file implementations/<this doc>` passes.
- Review: AC-3 — the rule in this row matches the wording in `templates/plan.md` and
  `skills/issue-to-plan/workflow.md`.

## Completion criteria

- AC-3: the detailed section states the authoring rule and the `prose-dependency` consequence, and the
  sync checker passes.

## Out of Scope

- The `issue_to_workitem.py` row and every other tool's rows (sibling plans' territory).
- `tools/plan_dependency_order.py` itself (unchanged, REQ-005).
- The summary table row.

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261117-132205_wftoolfu005_plan-prose-dependency-gating.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-134609_wftoolfu005_plan-prose-dependency-gating.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-073315
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`

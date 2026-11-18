# Procedure: tools/TOOL_DESCRIPTIONS.md - the authoring rule in the plan_dependency_order.py row

## Goal

State the dependency-authoring rule and the prose-fallback consequence in the tool description of
`tools/plan_dependency_order.py`, so a reader of the tool docs learns the same rule the Plan template
states (sibling procedure document).

## Scope
**Release unit**: N/A: not part of a release unit

- Add the authoring rule and the fallback consequence as one sentence inside the description cell of the
  `plan_dependency_order.py` row in the Work Items target table. (REQ-003)
- Leave the summary table row and all other tool rows untouched. (REQ-003)

## Assumptions

- Guidance-only is the chosen option. UNK-01 is resolved: the maintainer's 20261118 execution instruction
  (`memo3.md`) directs running this procedure set. (Plan Assumption; resolved 20261118)
- The tool behavior is unchanged (REQ-005); the added sentence describes existing behavior: prose paths
  in the `Dependencies` line are read as phase `all` dependencies with a `prose-dependency` warning
  (`parse_dependencies`), an open one labels the Plan `gated (prose)` (`readiness`), and a named path
  under `plans/done/` or `issues/done/` resolves by existence only (`resolve_dependency`).
  (Re-verified 20261118 against the tool source; the earlier `implementations/done/` mention was wrong —
  only `plans/` and `issues/` paths are read.)
- `tools/TOOL_DESCRIPTIONS.md` is edited row-level by several batch plans; re-read the current
  `plan_dependency_order.py` rows immediately before editing and touch no other tool's rows
  (Plan UNK-02).

## Design decisions

- Copy the canonical wording's substance from `templates/plan.md` (sibling procedure document) so AC-3
  compares three matching statements: "Record a must-wait cross-plan dependency as a structured
  `Depends on` bullet, never as a path in the prose `Dependencies` line. A prose path is read as a
  dependency on the whole chain (`all`) with a `prose-dependency` warning; sequencing-only notes
  therefore name the other Plan by title or id."
- Verification 20261118: the tool has no bullet-style detailed section — its description is one row in the
  file's Work Items target table (line 256; the summary row is line 114). The rule is inserted as one
  sentence inside that description cell, after the fallback sentence (`... emits a \`prose-dependency\`
  warning.`) and before `Prints a recommended order`; the summary row stays a one-line capability
  statement.

## Alternatives considered

- Rewording the summary table row. Rejected: the row states inputs and modes; behavioral caveats sit in
  the description cell throughout the file.
- Touching the description cell's `--format text\|json` and exit-code sentences. Rejected: they already
  state the gate semantics the rule leans on; no gap to fill. (The doc's earlier `blocked (missing file)`
  bullet claim does not exist in the current file — re-verified 20261118.)

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md` (exists)

### Procedure

1. Re-read the current `plan_dependency_order.py` summary row and description row (the file is edited by
   sibling batch plans; do not trust cached line numbers).
2. Insert the authoring-rule sentence into the description cell after the fallback sentence
   (`... emits a \`prose-dependency\` warning.`) and before `Prints a recommended order`.
3. Leave the summary row and the rest of the description cell (the `--format text\|json` and exit-code
   sentences) unchanged.

### Method

Single sentence insertion inside the existing description cell of the tool's table row; no row moves, no
other tool's row touched.

### Details

- The wording must stay accurate against the tool's actual behavior; the sibling test procedure
  document (`tests/tools/test_plan_dependency_order.py`) pins that behavior.

## Compatibility considerations

- `tools/check_tool_descriptions_sync.py` verifies that every `tools/*.py` file is named in this file and
  that CI/hook config references resolve; it does not compare cell text against docstrings. A row-level
  sentence insertion touches no tool name or config path, so the sync check stays green (re-verified
  20261118 against the checker source).
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Add or update tests per Validation plan | Completed | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — |  |

### Verification Findings
| ID | Finding | Action |
|----|---------|--------|
| V1 | The tool has no bullet detailed section: summary row line 114, description row line 256 (Work Items target table) | Procedure/Method/Design updated to a sentence insertion in the cell |
| V2 | `blocked (missing file)` does not appear in the current file or the tool | Stale claim removed from Scope/Alternatives/Procedure |
| V3 | `implementations/done/` is not a readable dependency path (only `plans/` and `issues/`) | Assumption corrected |
| V4 | The sync checker verifies coverage and config references, not cell text | Compatibility wording updated; checker still run per AC-6 |

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
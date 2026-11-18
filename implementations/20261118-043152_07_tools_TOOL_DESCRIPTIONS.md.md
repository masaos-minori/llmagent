## Goal

Correct `tools/TOOL_DESCRIPTIONS.md`: rewrite the audit entry to match the tool's actual behavior, state the routing trigger for both tools, add the new gate module's row, and update the definition module's row after the move (Plan REQ-005; AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the Index audit row, the Index `Shared base` rows for `_validation_gate_defs.py` and the new `_validation_gate_toolchain.py`, and the Work Items detail rows for `audit_plan_target_paths.py` (new) and `sync_plan_workitem_status.py` (trigger mention).
- Out of scope: the tools themselves (unchanged); `routing.md` rows (seq 05 document); the gate module edits (seq 01-03 documents).

## Assumptions

- The Index audit row (line 103 at revalidation time) claims the tool reports "cross-plan overlaps and path references in plan bodies not covered by a target row"; the tool audits only the `Implementation Target Files` paths and prints findings plus a count line (verified 20261118) — overlap reporting belongs to `tools/check_plan_target_overlaps.py`, which has its own rows (Plan row 7 evidence, Decision 5).
- The Index `Shared base` row for `_validation_gate_defs.py` (line 71) names "the toolchain and routing gate tables"; after the move only the routing table remains there, and `check_tool_descriptions_sync.py` requires every `tools/*.py` file to appear in the document, so the new module needs its own row (verified 20261118).
- `audit_plan_target_paths.py` has no detail row in the Work Items table today (verified 20261118); `sync_plan_workitem_status.py` already has one, whose Trigger cell is "one Plan file under `plans/`".
- The audit is read-only with no `--dry-run` option, so it does not join the `--dry-run` Convention writer list (line 56-58 region).

## Design decisions

- Rewrite the audit entries to the tool's verified behavior instead of trimming the claim (Plan Decision 5); the detail row records the exit codes and default arguments because the same table documents `amend_plan.py`, which prints the audit's results.
- State the routing trigger for both tools in the Work Items table, the section that carries trigger information: a new detail row for the audit, one appended sentence for the reconciliation tool (REQ-005).

## Alternatives considered

- Delete the overlap phrase and add nothing else: rejected — REQ-005 also requires the routing triggers, the new module row, and the definition-module row update.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`
### Procedure
1. Rewrite the Index audit row (line 103) description cell to: "Read-only audit of plan target-file paths against the current tree; flags a target path that does not exist unless the row's `Change Responsibility` signals a creation; with no arguments audits every `plans/*.md`; exit 1 on any finding".
2. Update the Index `Shared base` row for `_validation_gate_defs.py` (line 71) to: "The `Gate` type, the argv helpers it depends on, the source and mode constants, and the routing gate table of `run_validation_gates.py`".
3. Insert after it a new `Shared base` row for `_validation_gate_toolchain.py`: "The toolchain gate table and the bare-except rule of `run_validation_gates.py`, moved out of `_validation_gate_defs.py` to keep room for routing mappings".
4. In the Work Items table, insert after the `amend_plan.py` detail row a new row: `audit_plan_target_paths.py` | Trigger `plans/*.md` (excluding `plans/done/`) | Behavior: "Read-only audit of the `Implementation Target Files` paths: a target path that does not exist is flagged unless the row's `Change Responsibility` cell contains `create`, `new`, `generated`, `manifest;`, or `registry;`; with no arguments audits every `plans/*.md`; prints findings and a count line; exit 1 on any finding, 0 otherwise; also printed by `amend_plan.py` after a real run. Routing trigger (`routing.md`): before `issue-to-plan` Step 8b marks the table `Frozen`."
5. Append to the existing `sync_plan_workitem_status.py` detail row in the Work Items table one sentence: "Routing trigger (`routing.md`): reconciling a Plan after a procedure was archived outside the `code-implementation` batch close; run with `--dry-run` first."

### Method
- Row-level edits in two tables; every other row and the `--dry-run` Convention paragraph stay untouched.

### Details
- Land this document in Plan Phase 4, after the Phase 1 commit that moves the tables: while the move is uncommitted the definition-module row would read wrong (Plan UNK-01: this file is edited by several Plans and procedures — the wftool003 seq 07 document edits the `--dry-run` writer list and the marker-tool rows, disjoint regions; land the earlier edit first if regions coincide).
- Do not remove the audit row from the Index; the tool keeps existing — only its claimed behavior changes.

## Compatibility considerations

- `check_tool_descriptions_sync.py` compares the document against the live `tools/` directory: the new module row must land in the same change as (or after) the new module file, or the checker reports a missing entry (Plan row 7 Related Tests).
- Cross-plan overlap on this file with the remaining memo2 Plans was reported by `tools/check_plan_target_overlaps.py` (20261118); all are row-level and judged compatible in their own documents (Plan Assumptions).

## Security considerations

- N/A: documentation edits.

## Rollback considerations

- Revert the row edits; if the move is also reverted, restore the old definition-module row text naming both tables.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` → no finding: every `tools/*.py` file including `_validation_gate_toolchain.py` is listed and no stale name remains (AC-5).
- Manual read-through: the audit entries match `tools/audit_plan_target_paths.py` (its findings are target-path findings only) and both routing triggers match the seq 05 rows (AC-5).

## Completion criteria

- The audit entries describe the tool's actual behavior; both routing triggers are stated; the new module has a `Shared base` row; the definition-module row names only the routing table; the sync checker passes (AC-5).

## Out of Scope

- `routing.md` (seq 05); the gate modules (seq 01-03); `skills/issue-to-plan/workflow.md` (seq 06); the `--dry-run` Convention writer list (the audit writes nothing).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: doc-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This document is the documentation change |

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
- **Requirement ID**: `REQ-005` (audit entry corrected, routing triggers stated, module rows)
- **Source issue**: issues/20261117-123333_wftool004_orphan-tool-routing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125207_wftool004_orphan-tool-routing.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-043152
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`

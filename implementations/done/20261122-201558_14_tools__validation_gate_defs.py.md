## Goal

Add the gate mapping entry the new comment-length checker needs (REQ-005): `run_validation_gates.py drift` requires every row of `rules/tool-gates.md`'s "When to run which tool" table to have a mapping entry, so the tool-gates row (sibling procedure seq 11) cannot be valid without it.

## Scope
**Release unit**: N/A: not part of a release unit

One file is modified: the gate definitions. The situation-table row itself is sibling procedure seq 11; the tool is seq 07.

## Assumptions
- Adversarial finding (2026-11-22): `drift_report()` compares the table rows against `ROUTING_GATES` and reports a row without a mapping entry as drift (lines 519-530). The Plan's earlier assumption that no mapping is needed unless a pre-commit hook is added is wrong; owner decision (2026-11-22): add the `Gate` entry, class `scope`.
- No pre-commit hook is added, so the hook half of the drift check is unaffected.

## Design decisions
- One `Gate` entry in `ROUTING_GATES`, `source=SOURCE_ROUTING`, following the shape of the existing CI-gated entries (`generate_reference_table_check`, line 413), with `patterns=("config/**",)` so a change under `config/` selects it.
- The `Run` cell written by seq 11 must match this entry's command exactly, because the drift check derives the checker id from the cell.

## Alternatives considered
Leaving the row unmapped was rejected: `run_validation_gates.py drift` fails, which is seq 11's own validation step.

## Compatibility considerations
Existing gate entries are unchanged; the new entry is additive. `check_workitem_structure.py` and the drift check must both report no findings after the change.

## Security considerations
N/A: static registration.

## Rollback considerations
N/A: revert the commit (the tool, its `TOOL_DESCRIPTIONS.md` row, the gate row, and this entry are one change).

## Implementation
### Target file
`tools/_validation_gate_defs.py`
### Procedure
1. Add the `Gate` entry for `check_config_comment_length.py`.
### Method
Command and checker id as the tool-gates row states them; `patterns=("config/**",)`.
### Details
N/A: single entry addition.

## Validation plan
- `uv run python tools/run_validation_gates.py drift` — no drift.
- `routing.md` Tools sequence on the changed file.

## Completion criteria
The entry exists, its checker id matches the seq 11 row, and the drift check reports no findings.

## Out of Scope
The tool (seq 07), the situation-table row (seq 11), the `TOOL_DESCRIPTIONS.md` row (seq 09), CI wiring (seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the gate mapping entry per Procedure/Method/Details | Completed | 2026-11-23 | 2026-11-23 | `check_config_comment_length` entry added to `ROUTING_GATES` with `patterns=("config/**",)`, matching the `config/**/*.toml` row added by seq 11. **Deviation recorded**: `Gate` has no `entry_class` or `scope` field, so the plan's `entry_class`/`scope` wording is carried by the path-keyed `patterns` value; no field was added to the dataclass |
| 2 | Run `run_validation_gates.py drift` | Completed | 2026-11-23 | 2026-11-23 | `OK: 48 rules/tool-gates.md checker(s) all mapped; pre-commit hooks in parity` |

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
- **Requirement ID**: `REQ-005` (gate registration requires its mapping entry)
- **Source issue**: `issues/done/20261120-114214_agentcfg006_reduction-integration-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-190238_agentcfg006_reduction-integration-verification.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-201558
- **Related target files**: `tools/_validation_gate_defs.py`

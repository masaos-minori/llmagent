## Goal
Map the `tools/` size gate in the gate table (Part A), then move the gate type, helpers, and tables into `tools/_validation_gate_defs.py` while this module stays the CLI entry and re-exports them (Part B) (`REQ-002`, `REQ-006`, `REQ-007`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: Part A: one `ROUTING_GATES` entry; Part B: running `module_nodes.py extract` to move nodes and the re-export imports in this file.
- Out of scope: gate semantics, `drift`, the CLI, `COMMIT_ONLY_HOOKS`.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the module is about 42.6 KB; `Gate` (a frozen dataclass whose `checker_id` property calls `_checker_id_from_command`, and whose `requires_context` property uses `_PLACEHOLDER_TOKEN_RE`), `GateResult`, the constants `SOURCE_*`, `MODE_*`, `_TOOL_PY_RE`, `_VALUE_FLAG_RE`, `_PLACEHOLDER_TOKEN_RE`, `_BARE_EXCEPT_RULE`, and the two tables `TOOLCHAIN_GATES` and `ROUTING_GATES` (the tables end the file) are here; `drift_report` requires every `ROUTING_GATES` checker id to appear in a `routing.md` Run cell and vice versa. `tests/tools/test_run_validation_gates.py` imports `ROUTING_GATES`, `TOOLCHAIN_GATES`, `Gate`, `MODE_FAST`, `MODE_FULL`, `SOURCE_ROUTING`, `SOURCE_TOOLCHAIN`, `COMMIT_ONLY_HOOKS`, `_checker_id_from_cell`, `_checker_id_from_command`, `_split_md_row`, `classify`, `drift_report`, `parse_precommit_hooks`, `run_gate`, and `select_gates` from this module.
- Plan correction (2026-11-06): the definitions module must also receive `_checker_id_from_command`, `_TOOL_PY_RE`, `_VALUE_FLAG_RE`, `_PLACEHOLDER_TOKEN_RE`, and `_BARE_EXCEPT_RULE`, or it would import the entry module (a cycle); the entry re-exports every name the tests import.
- Sequencing: this Plan lands last among the `tools/` Plans; the procedures of `toolcommon001` and `toolwrite001` (archived with their procedures generated) are expected to have executed first, because they edit `run_validation_gates.py` and `manage_workitem_stage.py` before this Plan moves code from them.
- Part A must land in the same commit as the `routing.md` row and the new hook (drift parity). The `toolcommon001` procedure for this file (git call, `REPO_ROOT`, bootstrap) is expected to have landed.
- Overlap judgment: the earlier Plans edit other code in this file (git call, bootstrap), so they are compatible and sequential.

## Design decisions
- Part A: add the gate `check_module_size_tools` (new) as `Gate(name="check_module_size_tools", command=(("uv", "run", "python", "tools/check_module_size.py", "--scripts-dir", "tools", "--baseline", "tools/check_module_size_tools_baseline.txt"),), source=SOURCE_ROUTING, mode=MODE_FAST, patterns=("tools/*.py", "tools/check_module_size_tools_baseline.txt"))` after the existing `check_module_size` gate; its checker id is `check_module_size:tools`.
- Part B: the entry module keeps the CLI, the runner, `drift`, and `COMMIT_ONLY_HOOKS`, and imports the moved names from the definitions module (one-directional: the entry imports the definitions, never the reverse).

## Alternatives considered
- Leave the helper functions in the entry module and import lazily: rejected, it hides a cycle and breaks `Gate.checker_id` at import time.

## Implementation
### Target file
`tools/run_validation_gates.py`

### Procedure
1. (Part A) Add the `Gate` entry above to `ROUTING_GATES`.
2. (Part B, after the manage_workitem_stage split) Run `uv run python tools/module_nodes.py measure tools/run_validation_gates.py` to confirm the cluster boundary, then `module_nodes.py extract --src tools/run_validation_gates.py --dest tools/_validation_gate_defs.py` with `--name` for `Gate` and `_checker_id_from_command` and `--range` for the constant block and the two tables (the tool creates the destination).
3. Add `from tools._validation_gate_defs import (...)` for every moved name still used here or imported by tests; a name kept only for the tests carries `# noqa: F401 — re-exported for tests/tools/test_run_validation_gates.py` (suppression rule).
4. Prove the move with `module_nodes.py compare` for the moved functions and run the validation steps.

### Method
- `extract` moves the exact source ranges; the entry module's remaining code is untouched except for the new import block.

### Details
- After Part B lower the `tools/` baseline entry for this file with `--update-baseline`, review the diff so no entry is raised or added (`REQ-007`), and run `drift` and the gates.

## Compatibility considerations
- CLI behavior, gate selection, and every import path used by the tests are unchanged; by-path and `-m` forms keep working.

## Security considerations
N/A: no new input; the gate commands are fixed argument tuples.

## Rollback considerations
- Part B is the risky change (this is the gate entry point): revert the commit if `drift` or the tests fail; the extract is verbatim, so a revert restores the original file.

## Validation plan
- `uv run pytest tests/tools/test_run_validation_gates.py -q`, then `uv run pytest tests/tools -q`.
- `uv run python tools/run_validation_gates.py drift` and `uv run python tools/run_validation_gates.py`.
- Before and after Part B: compare the output of `uv run python tools/run_validation_gates.py --full` summaries (names and statuses).
- `routing.md` "Adding a new tool" steps 1-3 for this file.

## Completion criteria
- Part A: the gate exists and `drift` is clean together with the `routing.md` row; Part B: the moved names live in `tools/_validation_gate_defs.py`, every test import still resolves, the baseline entry for this file is lower, and the gates and tests pass.

## Out of Scope
- `drift` logic, other gates, the other oversized tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Part A: add the gate entry and run `drift` with the `routing.md` row and hook | Pending | — | — | |
| 2 | Part B: measure and extract the definitions, add the re-export imports, prove with `compare` | Pending | — | — | |
| 3 | Part B: lower the baseline entry, run the tests, `drift`, and the gates | Pending | — | — | |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (gate mapping), `REQ-006` (split), `REQ-007` (baseline shrinks)
- **Source issue**: issues/20261104-152002_toolsizegate001_apply-size-gate-to-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110406_toolsizegate001_apply-size-gate-to-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092637
- **Related target files**: `tools/run_validation_gates.py`

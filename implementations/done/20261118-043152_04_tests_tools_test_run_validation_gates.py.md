## Goal

Update `tests/tools/test_run_validation_gates.py` for the toolchain-table move: the identity test points at the new module, the CI-lint parity message names the new module, the captured tables are compared after the move, and new tests cover the two manual mappings (Plan REQ-001, REQ-002; AC-1, AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the identity test edit, the message edit, the before/after table comparison, an import-cycle guard test, and the new mapping tests.
- Out of scope: the modules the tests target (seq 01-03 documents); the `routing.md` rows whose Run cells the mapping tests read (seq 05 document).

## Assumptions

- `test_reexported_gate_definitions_are_the_same_objects` currently asserts `entry.TOOLCHAIN_GATES is defs.TOOLCHAIN_GATES` (verified 20261118); after the move the asserted object lives in `tools._validation_gate_toolchain`.
- The CI-lint parity assertion message names `tools/_validation_gate_defs.py` (verified 20261118); the toolchain commands it points a maintainer to now live in the new module.
- The existing toolchain parity tests (gate commands against `rules/toolchain.md`) stay unchanged; they read `TOOLCHAIN_GATES` through the orchestrator's re-export (seq 03 document), so they need no import edit.
- `select_gates` skips `SOURCE_ROUTING` gates with `patterns=()` in both fast and full mode (verified 20261118), which is what the non-selection test asserts (AC-2).
- The runner module exposes `_parse_routing_run_cells` and `_checker_id_from_cell` at module level; the mapping tests may import them from `tools.run_validation_gates`.

## Design decisions

- Keep one identity test comparing all re-exported names, now with a third import (`import tools._validation_gate_toolchain as toolchain`), so the re-export contract stays covered in a single place (Plan Phase 1 checklist item 5).
- Assert mapping ids against the ids derived from the live `routing.md` Run cells, not hardcoded strings: the test then fails if either side of the drift pair changes (Risk 3 mitigation, "a test compares the ids").

## Alternatives considered

- Rely on the drift check alone for id equality: rejected — AC-2 names tests, and a dedicated test localizes the failure to the mapping or the row (Plan Risks).

## Implementation
### Target file
`tests/tools/test_run_validation_gates.py`
### Procedure
1. Phase 1 (with seq 01-03 in the same commit): in `test_reexported_gate_definitions_are_the_same_objects`, add `import tools._validation_gate_toolchain as toolchain` and change the toolchain assertion to `assert entry.TOOLCHAIN_GATES is toolchain.TOOLCHAIN_GATES`; keep the `Gate`, `ROUTING_GATES`, and `_checker_id_from_command` assertions against `defs`.
2. Change the parity failure message to `"...(add one to tools/_validation_gate_toolchain.py and rules/toolchain.md, or a reviewed exception here)..."`.
3. Add a fresh-interpreter guard (Risk 2 mitigation): a test running `[sys.executable, "-c", "import tools._validation_gate_defs, tools._validation_gate_toolchain"]` via `subprocess.run` and asserting returncode 0 — no import cycle between the two gate modules.
4. Compare the live tables with the capture (Plan Phase 1 checklist item 5, characterization): run
   `uv run python -c "import json, tools._validation_gate_toolchain as t, tools._validation_gate_defs as d; print(json.dumps({'toolchain': [[g.name, [list(c) for c in g.command], g.mode, list(g.patterns), list(g.env), g.exclusive] for g in t.TOOLCHAIN_GATES], 'routing': [[g.name, [list(c) for c in g.command], g.mode, list(g.patterns), list(g.env), g.exclusive] for g in d.ROUTING_GATES]}, ensure_ascii=False))" | diff -u - /tmp/opencode/gate_tables_before_move.json`
   → no diff (throwaway check, not a permanent test; the capture is made by the seq 01 document).
5. Phase 2 (with seq 02's mappings and seq 05's rows): add mapping tests —
   - existence and shape: for each new gate name, the `ROUTING_GATES` entry has `patterns == ()`, `requires_context` true, `source == SOURCE_ROUTING`, `mode == MODE_FAST`;
   - ids: `{_checker_id_from_cell(cell) for cell in _parse_routing_run_cells(Path("routing.md").read_text())}` contains both `audit_plan_target_paths:<plan>` and `sync_plan_workitem_status:<plan>` (the positional token after the tool path appends a `:<positional>` suffix — precedent `amend_plan:<plan>`; ids corrected 20261118 by adversarial re-verification), and each equals the corresponding gate's `checker_id`;
   - non-selection: `select_gates(changed, MODE_FAST)` and `select_gates(changed, MODE_FULL)` with a representative changed list (e.g. `["tools/audit_plan_target_paths.py", "plans/x.md", "routing.md"]`) exclude both gate names (AC-2).

### Method
- Test edits only; the gate modules are changed by seq 01-03 in the same commits.

### Details
- Keep the test file's existing import style (`from tools.run_validation_gates import ...`); add `_checker_id_from_cell`, `_parse_routing_run_cells`, and `select_gates` to that import list if not already present.
- Do not duplicate the drift check's pre-commit hook comparisons in the new tests; `run_validation_gates.py drift` already covers hook parity (AC-3).

## Compatibility considerations

- The test module is one of the two direct importers of the definition module (Plan Design - Dependency graphing); its import edits land in the same commit as the move.
- Churn 10, single author (Plan Affected areas): no cross-team coordination needed.

## Security considerations

- N/A: test-only changes.

## Rollback considerations

- Revert the test commit with the code commit; the old identity assertions match the pre-move modules again.

## Validation plan

- `uv run pytest tests/tools/test_run_validation_gates.py -v` → all tests pass before and after the table comparison (AC-1, AC-2).
- The diff command in step 4 → empty (AC-1).
- `uv run ruff format tests/tools && uv run ruff check tests/tools` and `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` → clean (Plan Validation plan).

## Completion criteria

- The identity test asserts the new module's object; the message names the new module; the captured and live tables are identical (AC-1); both mapping tests exist and pass, including non-selection (AC-2).

## Out of Scope

- The gate modules and orchestrator (seq 01-03 documents); `routing.md` (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-102158 | 20261118-103215 | identity test repointed to the toolchain module, parity message names the new module, fresh-interpreter cycle guard added |
| 2 | Add or update tests per Validation plan | Completed | — | 20261118-103215 | This document is the test change N/A: this document is the test change; three manual-mapping tests added (shape, id parity with routing.md cells, non-selection in fast and full mode) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261118-103215 | 102 tests pass; ruff format/check and mypy clean; captured-tables diff: no diff |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261118-103215 | N/A N/A |

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
- **Requirement ID**: `REQ-001` (identity test and message), `REQ-002` (mapping tests)
- **Source issue**: issues/20261117-123333_wftool004_orphan-tool-routing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125207_wftool004_orphan-tool-routing.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-043152
- **Related target files**: `tests/tools/test_run_validation_gates.py`
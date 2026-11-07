## Goal
- Make `tools/module_nodes.py` treat the first decorator line as the start of a top-level class or function node, so `extract` moves decorated nodes verbatim (decorators included), `measure` reports spans that include decorators, and `compare` fails when the moved node's decorators differ between the source and destination.

## Priority
Medium

## Scope
- **In-Scope**:
  - Include decorator lines in the node span used by `measure` and `extract` (`_node_index` and the inline span in `measure`).
  - Make `compare` report a moved function/class whose decorators differ.
  - Add unit tests for a decorated class and a decorated function that is moved and compared.
- **Out-of-Scope**:
  - The atomic write and `--dry-run` behavior of `extract`.
  - Any other module splits besides the reproduction case.
  - Changing how `_normalize` rewrites `self._attr` reads or drops injected arguments.
- **Dependencies**: `N/A: none`
  - **Depends on**: `N/A: none`

## Background
`module_nodes.py` is the sanctioned tool to split large modules. Its `extract --name <Class>` subcommand moves a class or function from one module to another. While splitting `tools/run_validation_gates.py`, `extract --name Gate` moved `class Gate` without its `@dataclass(frozen=True)` decorator: the destination defined a plain class and the source kept the decorator, which then sat directly above `GateResult` next to its own `@dataclass(frozen=True)`. `class Gate` lives in `tools/_validation_gate_defs.py` and is imported by `tools/run_validation_gates.py`. The root cause is that the AST reports a class/function start line at the `class`/`def` keyword, excluding decorator lines, so the moved span omits the decorator. The pre-split and post-split modules were compared by object (`repr` of the gate tables), which exposed no difference only after the decorator was restored by hand.

## Problem
A moved decorated class or function loses its decorators: the decorator stays in the source and stacks on the next definition, and the destination defines a plain class instead of the decorated one. This silently changes behavior (a frozen dataclass becomes a plain class) and leaves a stray decorator in the source.

## Reason for Change
The tool is the sanctioned way to split large modules; a silent semantic change in a "verbatim" move defeats the move proof that `compare` is meant to provide.

## Implementation Intent
Treat the first decorator line as the start of a node in `extract` (for `--name` selection) and in `measure`, so the span includes decorators, and make `compare` detect a decorator difference. Keep the existing public symbols, output format, option names, and exit codes.

## Requirements
- `REQ-001`: In `measure` and in `_node_index`, the span of a decorated top-level class or function starts at the smallest `decorator_list` line number (or `node.lineno` when there are no decorators) so moved segments include the decorators.
- `REQ-002`: In `compare`, a moved function or class whose decorators differ between the old and new source is reported as `DIFFERS` and fails the command.
- `REQ-003`: Add tests covering a decorated class and a decorated function that are moved and compared.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified` per `issue-to-plan` Step 8; see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/module_nodes.py` | Implement | Fix node span to include decorators in `measure`/`_node_index` (REQ-001) and make `compare` detect decorator differences (REQ-002) | REQ-001, REQ-002 | `Explicit in code` (`tools/module_nodes.py`) | `tests/tools/test_module_nodes.py` | `Verified` |
| `tests/tools/test_module_nodes.py` | Test | Add decorated-class and decorated-function cases for `measure`, `extract`, and `compare` | REQ-001, REQ-002, REQ-003 | Existing test file | `tests/tools/test_module_nodes.py` | `Verified` |
| `tests/tools/test_module_nodes_extract_atomic.py` | Test | Add a decorated-node atomic-move case | REQ-001 | Existing test file | `tests/tools/test_module_nodes_extract_atomic.py` | `Verified` |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/_validation_gate_defs.py` | Defines `class Gate` (a real decorated node) used as the reproduction context for tests | `tools/module_nodes.py` (REQ-001) |
| `tools/run_validation_gates.py` | Caller that exercises the split workflow against `tools/_validation_gate_defs.py` | `tools/module_nodes.py` (REQ-001) |

## Acceptance Criteria
- Extracting a decorated class or function moves its decorators with it (REQ-001; `tools/module_nodes.py`).
- `measure` spans include decorators (REQ-001; `tools/module_nodes.py`).
- `compare` fails when decorators differ (REQ-002; `tools/module_nodes.py`).
- New unit tests cover a decorated class and a decorated function moved and compared (REQ-003; `tests/tools/test_module_nodes.py`, `tests/tools/test_module_nodes_extract_atomic.py`).

## Tests
Unit tests in `tests/tools/test_module_nodes.py` (new decorated-class and decorated-function cases for `measure`, `extract`, `compare`) and `tests/tools/test_module_nodes_extract_atomic.py` (decorated-node atomic move), run via `uv run pytest tests/tools -q` and the `tools/` validation steps of `routing.md` "Adding a new tool". Each test references REQ-001, REQ-002, or REQ-003.

## Documentation Impact
`tools/TOOL_DESCRIPTIONS.md` (the `module_nodes.py` row) states that decorators move with the node; verify the row is accurate after the fix and update it if it does not already say decorators are included. Driven by REQ-001.

## Assumptions
- `node.decorator_list` is non-empty exactly when the node has decorators, so `min(decorator lineno)` is a safe span start; `ast` decorator line numbers are 1-based like `node.lineno`.
- Preserving decorators in `compare`'s normalized dump does not regress undecorated nodes: both sides keep an empty `decorator_list`, so their dumps stay equal.
- Decorators that transfer verbatim on a move (e.g. `@dataclass`, `@staticmethod`) apply equally at the destination, so identical decorators do not produce a false `DIFFERS`.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether preserving decorators in `_normalize` could produce a false `DIFFERS` for a decorator that is valid only inside a class body (e.g. a descriptor bound to the class) | None missing; settled by assumption 3 and by the failing-test check | Verify with a decorated-function test that identical decorators pass; if a class-only decorator regresses, scope it out and record as a known limitation | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/module_nodes.py` | Private helpers `_node_index`, `measure`, `_normalize`/`compare`; no public signature change | CLI tool only; no external importers | N/A: Path A skipped historical analysis | N/A | None: not a deployed service |

## Design
`module_nodes.py` is a standalone CLI tool (`main()` dispatches `measure`/`extract`/`compare`); it has no external importers, so changing private helpers cannot break callers. The node span is computed in two places: the inline span in `measure` (start = `node.lineno`) and `_node_index` (used by `_extract_lines`, which `extract` calls). Both must clamp the start down to the earliest decorator line. `compare` currently strips decorators in `_normalize` (`node.decorator_list = []`) before dumping the AST; to detect a decorator difference it must preserve the decorator list so differing decorators change the normalized dump. Existing compare tests use undecorated functions, so keeping an empty decorator list for them keeps their dumps equal (no regression).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step. Declare a release unit when a phase breaks existing callers or tests until another phase lands.

1. **Phase 1: Failing tests**
   - [ ] Add a decorated-class and a decorated-function case to `tests/tools/test_module_nodes.py` asserting `measure` spans include decorators (REQ-001; `tests/tools/test_module_nodes.py`)
   - [ ] Add a decorated-node case to `tests/tools/test_module_nodes.py` asserting `extract --name` moves the decorator with the node (REQ-001; `tests/tools/test_module_nodes.py`)
   - [ ] Add a decorated-node case to `tests/tools/test_module_nodes.py` asserting `compare` returns non-zero when decorators differ (REQ-002; `tests/tools/test_module_nodes.py`)
   - [ ] Add a decorated-node atomic-move case to `tests/tools/test_module_nodes_extract_atomic.py` (REQ-001; `tests/tools/test_module_nodes_extract_atomic.py`)
2. **Phase 2: Include decorators in the node span**
   - [ ] Clamp the span start down to the earliest `decorator_list` line in `measure` (`tools/module_nodes.py`, REQ-001)
   - [ ] Clamp the span start down to the earliest `decorator_list` line in `_node_index` (`tools/module_nodes.py`, REQ-001); `_extract_lines` inherits this because it reads `_node_index`
3. **Phase 3: Detect decorator differences in compare**
   - [ ] Preserve the decorator list in `_normalize` so `compare` reports differing decorators as `DIFFERS` (`tools/module_nodes.py`, REQ-002)
4. **Phase 4: Validation**
   - [ ] Run `uv run pytest tests/tools -q` and the `tools/` validation steps of `routing.md` "Adding a new tool"; confirm all pass and exit codes/format are unchanged (REQ-001, REQ-002, REQ-003)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/module_nodes.py` | Unit: decorated-node measure/extract/compare | `uv run pytest tests/tools -q` | New and existing tests pass; `compare` exits non-zero on differing decorators |
| `tests/tools/test_module_nodes.py` | Unit (new cases) | `uv run pytest tests/tools -q` | Decorated-class and decorated-function cases pass |
| `tests/tools/test_module_nodes_extract_atomic.py` | Unit (new case) | `uv run pytest tests/tools -q` | Decorated-node atomic-move case passes |

## Risks
- **Risk**: Preserving decorators in `_normalize` produces a false `DIFFERS` for a decorator valid only inside a class body. → **Mitigation**: `UNK-01` resolved by a failing-test check with identical decorators; scope any class-only decorator out and document it as a known limitation.
- **Risk**: Changing the span start shifts byte sizes reported by `measure` for decorated nodes. → **Mitigation**: `Constraints` pin that byte sizes for decorated nodes include the decorators; the REQ-001 test asserts this explicitly.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-123522_modnodes001_extract-drops-class-decorators.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-153921
- **Related target files**: `tools/module_nodes.py`, `tests/tools/test_module_nodes.py`, `tests/tools/test_module_nodes_extract_atomic.py`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent / Required Changes; `_node_index` uses `node.lineno`, `measure` uses `node.lineno` (verified in `tools/module_nodes.py`) | `tools/module_nodes.py` | Phase 2 | `measure` spans include decorators; extracting a decorated node moves its decorators | `measure`/`extract` decorated-node cases in `tests/tools/test_module_nodes.py` | Confirmed by repository evidence |
| REQ-001 | same as above | `tests/tools/test_module_nodes.py` | Phase 1 | same as above | `measure`/`extract` decorated-node cases | Confirmed by repository evidence |
| REQ-001 | same as above | `tests/tools/test_module_nodes_extract_atomic.py` | Phase 1 | extracting a decorated node moves its decorators | decorated-node atomic-move case | Confirmed by repository evidence |
| REQ-002 | Implementation Intent / Required Changes; `_normalize` sets `node.decorator_list = []`, `compare` never compares decorators (verified in `tools/module_nodes.py`) | `tools/module_nodes.py` | Phase 3 | `compare` fails when decorators differ | `compare` differing-decorator case in `tests/tools/test_module_nodes.py` | Confirmed by repository evidence |
| REQ-002 | same as above | `tests/tools/test_module_nodes.py` | Phase 1 | `compare` fails when decorators differ | `compare` differing-decorator case | Confirmed by repository evidence |
| REQ-003 | Testing Expectations | `tests/tools/test_module_nodes.py` | Phase 1 | new unit tests cover a decorated class and function moved and compared | `uv run pytest tests/tools -q` | Explicit in issue |
| REQ-003 | same as above | `tests/tools/test_module_nodes_extract_atomic.py` | Phase 1 | new unit tests cover a decorated node moved | `uv run pytest tests/tools -q` | Explicit in issue |

# module_nodes.py extract leaves a class decorator behind

## Priority
Medium

## Summary
`module_nodes.py extract --name <Class>` moves the class but not its decorators, so the decorator stays in the source file and stacks on the next definition.

## Background
While splitting `tools/run_validation_gates.py`, `extract --name Gate` moved `class Gate` without `@dataclass(frozen=True)`: the destination defined a plain class, and the source kept the decorator, which then sat directly above `GateResult` next to its own `@dataclass(frozen=True)`. The cause is that `ast` reports a class or function start line at the `class` or `def` keyword, excluding decorator lines. The pre-split and post-split modules were compared by object (`repr` of the gate tables), which exposed no difference only after the decorator was restored by hand.

## Problem
A moved decorated class or function loses its decorators, silently changing behavior (a frozen dataclass becomes a plain class) and leaving a stray decorator in the source.

## Reason for Change
The tool is the sanctioned way to split large modules; a silent semantic change in a "verbatim" move defeats the move proof.

## Implementation Intent
Treat the first decorator line as the start of a node in `extract` (for `--name` selection) and in `measure`, so the span includes decorators, and make `compare` detect a decorator difference.

## Target Files or Areas
`tools/module_nodes.py`, `tests/tools/test_module_nodes.py`, `tests/tools/test_module_nodes_extract_atomic.py`.

## Required Changes
- Use the smallest `decorator_list` line number together with `lineno` for the span of a decorated class or function in `extract` and `measure`.
- Make `compare` report a function whose decorators differ.
- Add tests with a decorated class and a decorated function, moved and compared.

## Constraints
Keep the output format, option names, and exit codes; byte sizes in `measure` for decorated nodes will include the decorators.

## Acceptance Criteria
- Extracting a decorated class or function moves its decorators with it.
- `measure` spans include decorators.
- `compare` fails when decorators differ.

## Testing Expectations
Unit tests in `tests/tools/test_module_nodes.py` (new cases) and `uv run pytest tests/tools -q`; the `tools/` validation steps of `routing.md` "Adding a new tool".

## Documentation Impact
Yes: `tools/TOOL_DESCRIPTIONS.md` (the `module_nodes.py` row) states that decorators move with the node.

## Out of Scope
The atomic write and `--dry-run` behavior of `extract`, and any other module splits.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Change only `tools/module_nodes.py` and its tests; keep the existing public symbols; write the failing tests first.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-123522
- **Related target files**: `tools/module_nodes.py`, `tests/tools/test_module_nodes.py`

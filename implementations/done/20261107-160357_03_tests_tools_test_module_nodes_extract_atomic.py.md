## Goal

Add a decorated-node atomic-move case to `tests/tools/test_module_nodes_extract_atomic.py` asserting that `extract --name` moves a decorated function with its decorator atomically (REQ-001).

## Scope
**Release unit**: N/A: not part of a release unit
In scope: append one test and one source constant to `tests/tools/test_module_nodes_extract_atomic.py`. Do not modify the existing `SRC`/`DEST_OLD` constants or existing tests.

## Assumptions
- The existing helpers (`_extract`, `_leftovers`) operate on whatever `--name` and source the caller supplies, so a decorated `SRC` exercises the same atomic-write path (Plan assumption 1; decorator line numbers are 1-based like `node.lineno`).
- Adding a new constant and test does not change any existing assertion (Plan assumption 3).

## Design decisions
- Introduce a dedicated `SRC_DECORATED` (new) constant so the existing `SRC` (used by every current test) is untouched.
- Assert three things about the decorated move: the destination contains the decorator and the function, the source no longer contains the decorator (it moved with the node), and no `.tmp` leftover remains (the atomic guarantee holds for decorated nodes).

## Alternatives considered
N/A: the Plan's frozen Implementation steps fix the test shape (a decorated atomic-move case); this procedure implements that shape, not an alternative.

## Implementation
### Target file
`tests/tools/test_module_nodes_extract_atomic.py`
### Procedure
- REQ-001: add a decorated-node atomic-move test.
### Method
- Add a `SRC_DECORATED` (new) constant next to the existing `SRC`/`DEST_OLD` constants (lines 16-18), defining a top-level decorated function `alpha`.
- Append a test that runs `extract --name alpha` into a fresh destination and asserts the decorator travels with the node and the atomic-write contract still holds.
### Details
- Add after line 18:
  ```python
  SRC_DECORATED = "@decorator\n\n\ndef alpha():\n    return 1\n\n\ndef gamma():\n    return 3\n"
  ```
- Append at end of file:
  ```python
  def test_decorated_node_moves_with_decorator_atomically(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      src = tmp_path / "src.py"
      dest = tmp_path / "dest.py"
      src.write_text(SRC_DECORATED, encoding="utf-8")

      assert (
          module_nodes.main(
              ["extract", "--src", str(src), "--dest", str(dest), "--name", "alpha"]
          )
          == 0
      )

      dest_text = dest.read_text(encoding="utf-8")
      src_text = src.read_text(encoding="utf-8")
      assert "@decorator" in dest_text
      assert "def alpha()" in dest_text
      assert "@decorator" not in src_text
      assert _leftovers(tmp_path) == []
  ```
  The `capsys` parameter is kept only for signature parity with sibling tests; it is unused here. If the linter flags the unused fixture, drop it.

## Compatibility considerations
N/A: test-only addition; no production code or public API touched.

## Security considerations
N/A: no input handling or trust boundary change.

## Rollback considerations
N/A: revert the single commit.

## Validation plan
- Run `uv run pytest tests/tools -q`; confirm the new decorated-move test passes and all existing extract/atomic tests still pass unchanged.

## Completion criteria
- `test_decorated_node_moves_with_decorator_atomically` (new) exists and passes.
- Destination contains `@decorator` and `def alpha()`; source no longer contains `@decorator`.
- No `.tmp` leftover after the decorated move; existing tests unaffected.

## Out of Scope
- Any change to the atomic-write, `--dry-run`, or failure-isolation behavior beyond adding the decorated case.
- Decorated-class moves (covered by `tests/tools/test_module_nodes.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-07 | 2026-11-07 | implement |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-07 | 2026-11-07 | test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-07 | 2026-11-07 | validate |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-07 | 2026-11-07 | n/a |

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
- **Requirement ID**: REQ-001 (move decorated nodes verbatim)
- **Source issue**: `issues/20261106-123522_modnodes001_extract-drops-class-decorators.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-153921_modnodes001_extract-drops-class-decorators.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-160357
- **Related target files**: `tests/tools/test_module_nodes_extract_atomic.py`

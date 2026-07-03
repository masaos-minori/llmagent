# Implementation: Add aggregate set equality tests to `tests/test_tool_constants.py`

## Goal

Add or create `tests/test_tool_constants.py` with tests verifying that:
1. `GIT_TOOLS == GIT_READ_TOOLS | GIT_WRITE_TOOLS` (aggregate equality)
2. `GITHUB_TOOLS == GITHUB_READ_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS`
3. No tool appears in multiple sub-classifications (disjoint sets)
4. `is_side_effect()` returns True for git and GitHub write/dangerous tools
5. `is_side_effect()` returns False for git and GitHub read tools

## Scope

- In-Scope: Add `TestGitToolClassification` and `TestGithubToolClassification` test classes.
  If `tests/test_tool_constants.py` already exists, append new classes at the end.
  If not, create the file with these two classes.
- Out-of-Scope: No changes to `tool_constants.py` or `tool_executor_helpers.py`.

## Assumptions

1. `scripts/shared/tool_constants.py` defines `GIT_READ_TOOLS`, `GIT_WRITE_TOOLS`, `GIT_TOOLS`,
   `GITHUB_READ_TOOLS`, `GITHUB_WRITE_TOOLS`, `GITHUB_DANGEROUS_TOOLS`, `GITHUB_TOOLS`
   (prerequisite: `tool_constants_py.md`).
2. `is_side_effect()` is importable from `shared.tool_executor_helpers`.
3. After require-36, `_SIDE_EFFECT_TOOLS` includes `GIT_WRITE_TOOLS | GITHUB_WRITE_TOOLS |
   GITHUB_DANGEROUS_TOOLS`.
4. `uv run pytest` is the test runner.

## Implementation

### Target file

`tests/test_tool_constants.py` (existing or new)

### Procedure

1. Check if `tests/test_tool_constants.py` exists. If yes, read its end to find the append point.
2. Add (or create) the two test classes.
3. Run `uv run ruff check tests/test_tool_constants.py` — expect 0 errors.
4. Run `uv run pytest tests/test_tool_constants.py -v` — all pass.

### Method

```python
from shared.tool_constants import (
    GIT_READ_TOOLS,
    GIT_TOOLS,
    GIT_WRITE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_READ_TOOLS,
    GITHUB_TOOLS,
    GITHUB_WRITE_TOOLS,
)
from shared.tool_executor_helpers import is_side_effect


class TestGitToolClassification:
    def test_git_tools_is_union_of_read_and_write(self) -> None:
        assert GIT_TOOLS == GIT_READ_TOOLS | GIT_WRITE_TOOLS

    def test_git_read_write_are_disjoint(self) -> None:
        assert GIT_READ_TOOLS.isdisjoint(GIT_WRITE_TOOLS)

    def test_git_read_tools_not_side_effect(self) -> None:
        for tool in GIT_READ_TOOLS:
            assert not is_side_effect(tool), f"{tool!r} should not be a side-effect"

    def test_git_write_tools_are_side_effect(self) -> None:
        for tool in GIT_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"


class TestGithubToolClassification:
    def test_github_tools_is_union_of_sub_sets(self) -> None:
        assert GITHUB_TOOLS == GITHUB_READ_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS

    def test_github_sub_sets_are_pairwise_disjoint(self) -> None:
        assert GITHUB_READ_TOOLS.isdisjoint(GITHUB_WRITE_TOOLS)
        assert GITHUB_READ_TOOLS.isdisjoint(GITHUB_DANGEROUS_TOOLS)
        assert GITHUB_WRITE_TOOLS.isdisjoint(GITHUB_DANGEROUS_TOOLS)

    def test_github_read_tools_not_side_effect(self) -> None:
        for tool in GITHUB_READ_TOOLS:
            assert not is_side_effect(tool), f"{tool!r} should not be a side-effect"

    def test_github_write_tools_are_side_effect(self) -> None:
        for tool in GITHUB_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"

    def test_github_dangerous_tools_are_side_effect(self) -> None:
        for tool in GITHUB_DANGEROUS_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"
```

### Details

- Tests depend on `tool_constants_py.md` (sub-classifications) and the `tool_executor_helpers.py`
  `_SIDE_EFFECT_TOOLS` extension (covered by existing `tool_executor_helpers_py.md`).
- If `is_side_effect()` tests fail because `_SIDE_EFFECT_TOOLS` has not yet been extended,
  implement the `_SIDE_EFFECT_TOOLS` extension first.

## Validation plan

```bash
# Lint
uv run ruff check tests/test_tool_constants.py
# Expected: 0 errors

# Run tests
uv run pytest tests/test_tool_constants.py::TestGitToolClassification tests/test_tool_constants.py::TestGithubToolClassification -v
# Expected: all pass

# Regression
uv run pytest tests/test_tool_executor_helpers.py -q
# Expected: all pass
```

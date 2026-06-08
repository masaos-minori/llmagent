[tasks]
Show progress as you work.
Refactor `~/llmagent/scripts/**/*.py`.
Follow these rules exactly.
Create a Git commit.

# Core Rules

- Change only one feature or one responsibility at a time.
- Keep every change small.
- Do not change external behavior, public APIs, or visible output.
- If a change may alter behavior, do not implement it.
- Record it as a proposal instead.
- Minimize changes to exception handling, state, side effects, I/O, and concurrency.

# Refactoring Rules

- Give each function one responsibility.
- Do not mix fetching, transformation, decision logic, and persistence in one function.
- Reduce nesting, branching, and long functions.
- Prefer early returns and small helper functions when they improve clarity.
- Use clear and explicit names.
- Extract shared logic only when it should evolve together later.
- Avoid unnecessary abstraction.

# Type Safety Rules

- Add explicit type annotations where needed.
- Add boundary checks where types are unclear.
- Do not use `Any`, unnecessary casts, or unsafe assertions.
- Prevent invalid `None` flow.
- Keep input validation separate from internal logic.

# Required Output

- Preserve behavior.
- Keep diffs minimal.
- Report results for each file.
- For each file, report:
  - what changed
  - why it changed
  - whether behavior was preserved
  - proposals not implemented because they may affect behavior

# Procedure

## 1. Preparation

- Use `pydeps` to inspect the import graph.
- Use `rg` to find symbol usages.
- Use `import-linter` to verify module boundaries.
- Use `ast-grep` for structural usage search.
- Identify files affected by `deploy.sh`.
- Record the impact scope in a table.

## 2. Behavior Lock

- Record baseline coverage with `pytest-cov`.
- If coverage is below 80%, add characterization tests.
- Run `mutmut`.
- Ensure there are no surviving mutations in the refactored paths.

## 3. Transformation

- Use `libcst` or `bowler` for symbol-level refactoring when needed.
- Run `ruff` after each transformation.
- Ensure no legacy symbol names remain.

## 4. Validation

- Run `mypy`.
- Cross-check with `pyright`.
- Run `ruff`.
- Run characterization tests.

## 5. Incremental Migration

- Commit each logical unit separately.
- Ensure every commit is rollback-safe.
- Stage changes per hunk with `lazygit`.
- Run tests, `ruff`, and `mypy` at each step.

## 6. CI Gate

- Run `pre-commit run --all-files`.
- Run `lint-imports`.
- Run `diff-cover`.
- Review changes with `git log` and `git diff`.
- Ensure no legacy symbol names remain.

# Special Cases

- If refactoring `tool_executor.py` or `route_resolver.py`, perform extra verification for MCP routing.
- Update `config/agent.toml` if required.
- If modules are added or removed, update:
  - `deploy.sh`
  - `routing.md`
  - `AGENTS.md`

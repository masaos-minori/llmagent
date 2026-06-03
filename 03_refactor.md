[tasks]
Show progress as you work.
Refactor all files under `scripts/**/*.py`.
Follow these rules strictly.

# Change process and risk control
- Make changes incrementally.
- Refactor in small units by feature or responsibility.
- Do not change multiple features in a single step.
- Do not change any existing external behavior, public API, or visible output.
- If a change may alter behavior, do not implement it.
- Instead, report it as a proposal in comments or in the report.
- Keep changes to exception handling, state management, side effects, I/O, and concurrency to the absolute minimum.

# Structure and responsibility
- Ensure one function has one responsibility.
- Do not mix data fetching, transformation, decision logic, and persistence in the same function.
- Reduce deep nesting, complex branching, and overly long functions.
- Prefer early returns and small helper functions when they improve clarity.
- Make the code easy to read from top to bottom.
- Use clear and explicit names for variables, functions, and classes.
- Extract shared logic only when the duplicated code should be changed together in the future.
- Avoid unnecessary abstraction.

# Type safety
- Add explicit type annotations, type definitions, and boundary checks where types are unclear.
- Do not use `Any`, excessive type assertions, or unsupported casts.
- Prevent `None` from entering places where it should not.
- Separate input validation from internal processing logic.

# Output requirements
- Preserve behavior.
- Keep diffs as small as possible.
- Report the refactoring result for each file.
- For each file, summarize:
  - what changed
  - why it changed
  - whether behavior was preserved
  - any proposals not implemented because they may affect behavior


# File-Level Refactoring Procedure

## 1. Preparation Phase

### 1.1 Map Dependencies

- Visualize the import graph using `pydeps`
- Locate symbol usages using `rg`
- Verify module boundary contracts using `import-linter`
- Perform structural usage search with `ast-grep`

### 1.2 Assess Deployment Impact

- Identify files affected by `deploy.sh`

### 1.3 Record Findings

- Record the impact scope in a tabular format

## 2. Behavior Lock Phase

### 2.1 Verify Coverage

- Record baseline coverage using `pytest-cov`
- If coverage < 80%, add characterization tests

### 2.2 Validate Test Strength

- Evaluate test robustness using `mutmut`
- Ensure no surviving mutations exist

## 3. Semantic Transformation Phase

### 3.1 Transform Symbols

- Rename or transform symbols using `libcst` or `bowler`
- Run formatting and linting with `ruff`

### 3.2 Validate Transformation

- Ensure no legacy symbol names remain


## 4. Semantic Validation Phase

### 4.1 Type Validation

- Run type checking with `mypy`
- Cross-validate with `pyright`

### 4.2 Lint and Test

- Run final linting with `ruff`
- Execute characterization tests

## 5. Incremental Migration Phase

### 5.1 Commit per Logical Unit

- Commit each logical step independently
- Ensure each commit is rollback-safe

### 5.2 Verify Transition

- Stage changes per hunk using `lazygit`
- Run tests, `ruff`, and `mypy` at each step

## 6. CI Gate Phase

### 6.1 Final Checks

- Run `pre-commit` on all files
- Validate import rules with `lint-imports`
- Check coverage with `diff-cover`

### 6.2 Final Review

- Review changes using `git log` and `git diff`
- Ensure no legacy symbol names remain

## 7. Special Cases

### 7.1 Refactoring `tool_executor.py` and `route_resolver.py`

- Perform additional verification if MCP routing logic is affected
- Update `config/agent.toml` if required

### 7.2 Adding or Removing Modules

- Update `deploy.sh`
- Update `routing.md`
- Update `CLAUDE.md`

## 8. Completion Checklist

- [ ] Impact scope table is recorded
- [ ] Characterization tests exist; coverage ≥ 80%
- [ ] Mutation count is zero for refactored paths
- [ ] `ruff check scripts/` — no errors
- [ ] `PYTHONPATH=scripts mypy scripts/ tests/` — no increase in errors
- [ ] `PYTHONPATH=scripts lint-imports` — success or contracts updated
- [ ] `diff-cover coverage.xml --compare-branch=master --fail-under=90` — success
- [ ] `pre-commit run --all-files` — success
- [ ] All commits are bisectable (tests pass independently)
- [ ] No legacy symbol names remain in `scripts/`

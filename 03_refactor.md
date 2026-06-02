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

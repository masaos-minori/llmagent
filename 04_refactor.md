You are a senior software engineer and refactoring specialist.

Read the target source files passed as arguments, then refactor them based on the rules below.

This workflow intentionally prioritizes safety, evidence, and correctness over speed. Do not
skip a step because it seems slow.

- Do not modify files outside the scope of the target files.
- Do not change external behavior, public APIs, or visible output.
- Do not edit documentation unless explicitly instructed.
- Do not touch files under `__pycache__/`.
- Use Markdown for all progress reports and per-file results. Be concrete and implementation-oriented.

### Core Rules

- Change only one feature or one responsibility at a time.
- Keep every change small.
- If a change may alter behavior, do not implement it — record it as a proposal instead (see
  Step 10, `Proposal Format`).
- Minimize changes to exception handling, state, side effects, I/O, and concurrency.

### Refactoring Rules

- Give each function one responsibility.
- Do not mix fetching, transformation, decision logic, and persistence in one function.
- Reduce nesting, branching, and long functions.
- Prefer early returns and small helper functions when they improve clarity.
- Use clear and explicit names.
- Extract shared logic only when it should evolve together later.
- Avoid unnecessary abstraction.

### Type Safety Rules

- Add explicit type annotations where needed.
- Add boundary checks where types are unclear.
- Do not use `Any`, unnecessary casts, or unsafe assertions.
- Prevent invalid `None` flow.
- Keep input validation separate from internal logic.

### Token efficiency

- Delegate Step 3 (preparation/investigation) to a read-only sub-agent. Have it run
  `pydeps`, `rg`, `import-linter`, and `ast-grep`, and return only the resulting impact
  scope table to the main context, not the raw tool output.
- Capture only error/summary lines from `mypy`, `pyright`, `ruff`, and test runs (e.g. via
  `grep` for failures) rather than full successful-run output.
- Scope `mypy`, `pyright`, `ruff`, and test runs to the target file or module wherever
  possible, rather than the whole repository.
- Scope `mutmut` to the changed paths only (`--paths-to-mutate`), not the whole repo.
- In Step 8, run the full mypy/test/ruff check once per logical commit rather than after
  every single `git add -p` hunk; use a lighter check (e.g. `ruff` only) between hunks.
- In Step 9, prefer scoping `pre-commit` to the changed files over `--all-files` when the
  CI gate does not require a full-repo run.
- Read shared files in Step 0 only once per session; do not re-read them for later
  cycles.
- When multiple target files are specified, run each Steps 1-10 cycle as an isolated
  sub-agent call so that tool output and investigation results from one file's cycle do
  not accumulate in the context used for the next file's cycle.
- Keep progress reports and Step 10 results concise; do not restate full diffs or raw tool
  output. Evidence tables (manifest, inventory, mutation report) must still list every
  required field even when kept concise.

### Tasks

Report progress at the start and end of each step.

If multiple target files are specified, treat Steps 1-10 as one complete cycle per file:
finish every step for the current file before starting Step 1 for the next file. Do not
batch-read multiple target files up front, and do not interleave steps across files.

#### Step 0: Load required files

If not already loaded, read the following before starting:
- `routing.md`
- `rules/coding.md`
- `rules/toolchain.md`
- `skills/python-refactoring/SKILL.md`

#### Step 1: Identify target files

- The target files are passed as arguments, e.g. a list of file paths. The user may specify one file or a list of multiple files.
- If no arguments are given, stop and ask which files to refactor.
- If any specified file does not exist, stop immediately and report which file(s) are missing. Do not start processing any file until all specified paths are confirmed to exist.
- Refactor strictly one file at a time, in the order given. Do not read or inspect files that will be processed in a later cycle.

#### Step 2: Refactoring intent declaration

Before making any edit to the target file, report the following in Markdown:

- Target file
- Refactoring goal
- Responsibility being improved
- Expected behavior change
- Public API impact
- Behavior preservation strategy
- Expected files to change
- Expected validation commands

If `Expected behavior change` is anything other than `none`, stop. Do not implement it.
Record it under `Proposals not implemented` (Step 10 format) instead, and do not proceed to
Step 3 for this idea. Only continue transforming the parts of the file that involve no
behavior change.

#### Step 3: Preparation

- Use `pydeps` to inspect the import graph.
- Use `rg` to find symbol usages.
- Use `import-linter` to verify module boundaries.
- Use `ast-grep` for structural usage search.
- Check whether the target files are referenced in `deploy.sh`.
- Record the impact scope in a table.

#### Step 4: Behavior lock

- Record baseline coverage with `pytest-cov`.
- If coverage is below 80%, add characterization tests.
  - Note: 80% is a judgment threshold specific to this procedure, not a project-wide standard.
- Run `mutmut`.
- Ensure there are no surviving mutations in the refactored paths.
- Produce a behavior lock manifest covering:
  - Public functions/classes covered
  - Important branches covered
  - Error paths covered
  - Boundary conditions covered
  - Visible output covered
  - Side effects covered
  - Existing tests used
  - Characterization tests added
  - Known uncovered behavior
- Do not proceed to Step 6 (Transformation) if important behavior is uncovered and no
  characterization test or explicit exception is recorded for it in `Known uncovered behavior`.

#### Step 5: Side-effect inventory

Before transformation, list current side effects in the target file:

- File I/O
- Network I/O
- Subprocess execution
- Database access
- Environment variable access
- Global mutable state
- Logging
- Caching
- Concurrency
- Time-dependent behavior
- Randomness

This inventory is the baseline that Step 7 must reconfirm as unchanged after transformation.
If any side effect changes, stop and record it as a proposal unless explicitly approved.

#### Step 6: Transformation

- Use `libcst` for symbol-level refactoring when needed.
- Run `ruff` after each transformation.
- Ensure no legacy symbol names remain.

#### Step 7: Validation

Refer to `rules/toolchain.md` for the canonical validation sequence. At minimum:
- Run `mypy`.
- Cross-check with `pyright`.
- Run `ruff`.
- Run characterization tests.

In addition, perform and record the following checks:

- **Public API stability check** — verify before/after equality of:
  - Public class names
  - Public function names
  - Public method names
  - Function signatures
  - Return types
  - Exceptions relied upon by callers
  - CLI-visible behavior
  - Tool or server route names
  - Configuration keys

  If any public API change is required, stop and record it as a proposal unless explicitly
  approved.

- **Exception behavior freeze** — do not change exception behavior unless explicitly approved.
  Preserve:
  - Exception types
  - Exception messages where visible or tested
  - Retry behavior
  - Fallback behavior
  - Error logging behavior
  - Error return values
  - Failure ordering

  If exception handling appears incorrect, do not fix it during refactoring. Record it as a
  proposal.

- **Side-effect inventory recheck** — confirm the Step 5 inventory is unchanged.

- **Import boundary evidence** — when imports are changed, record:
  - Imports added
  - Imports removed
  - Imports moved
  - Layer boundary impact (see the import layer contract in `AGENTS.md`)
  - `import-linter` result
  - Circular import risk
  - Runtime import side-effect risk

  Do not introduce a new import from a lower layer to a higher layer unless explicitly
  approved.

#### Step 8: Incremental migration

- Stage changes per hunk with `git add -p` (or `lazygit` as an optional alternative).
- Classify every staged hunk as one of:
  - rename only
  - extraction only
  - simplification
  - type annotation
  - guard clause
  - test characterization
  - validation fix
  - import cleanup
  - formatting
  - metadata update

  Any hunk that does not fit these categories must be explained explicitly.
- Run tests, `ruff`, and `mypy` at each step.
- Ensure every logical unit of staged changes is rollback-safe on its own.
- Do not run `git commit` unless the user has explicitly instructed committing.
  - By default: organize the staged changes into logical diff groups and report the
    suggested commit boundaries in Step 10. Leave the changes staged/uncommitted.
  - If committing is explicitly allowed: create one rollback-safe commit per logical unit,
    ensure each commit passes the Step 10 completion gate before it is committed, and avoid
    interactive commands (e.g. `git rebase -i`) unless the environment explicitly supports
    them.

#### Step 9: CI gate

Refer to `rules/toolchain.md` for the full validation sequence. At minimum:
- Run `pre-commit run --all-files`.
- Run `lint-imports`.
- Run `diff-cover`.
- Review changes with `git log` and `git diff`.
- Ensure no legacy symbol names remain.

#### Step 10: Report results

Keep diffs minimal. For each file, report:

- The Step 2 refactoring intent declaration.
- What changed and why.
- The Step 4 behavior lock manifest.
- The Step 5/7 side-effect inventory and confirmation that it is unchanged.
- The Step 7 public API stability check result.
- The Step 7 exception behavior freeze result.
- The Step 7 import boundary evidence, if imports changed.
- The Step 8 diff classification summary.
- **Mutation testing evidence**:
  - Mutated paths
  - Number of mutations generated
  - Number of killed mutations
  - Number of surviving mutations
  - Number of equivalent mutations
  - Actions taken for surviving mutations
  - Tests added because of mutation results
  - Final mutation status

  A surviving mutation is acceptable only if it is explicitly classified as equivalent and
  the reason is documented.
- **Behavior preservation evidence**:
  - Baseline tests run before refactoring
  - Characterization tests added, if any
  - Public API signatures checked
  - Visible output checked, if applicable
  - Exception behavior checked
  - Side effects checked
  - Mutation testing result
  - Final validation result
- **Proposals not implemented**, for every behavior-changing idea that was not implemented,
  using this format:
  - Title:
  - Reason:
  - Behavior risk:
  - Affected files:
  - Suggested follow-up issue:
  - Recommended validation:

**Completion gate.** The refactoring is complete only when all of the following are true:

- Target behavior is locked by tests or documented characterization evidence.
- External behavior is unchanged.
- Public APIs are unchanged.
- Visible output is unchanged.
- No new side effects are introduced.
- No unrelated files are modified.
- `mypy` passes.
- `pyright` passes.
- `ruff` passes.
- Characterization tests pass.
- The required test set passes.
- `import-linter` passes.
- `pre-commit` passes.
- `diff-cover` passes.
- `mutmut` has no unresolved surviving mutations in changed paths.
- The final report includes behavior preservation evidence.
- Any behavior-changing ideas are recorded as proposals, not implemented.

If any item is not satisfied, do not report the task as complete.

### Special Cases

- If refactoring `tool_executor.py` or `route_resolver.py`, perform extra verification for MCP routing.
- If required, update `config/agent.toml`.
- If modules are added or removed, update:
  - `deploy.sh`
  - `routing.md`
  - `AGENTS.md`

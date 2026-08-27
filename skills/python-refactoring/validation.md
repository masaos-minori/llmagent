# Python Refactoring — Side-Effect, Test, Type, and API Validation

Load this file at Step 0 (unconditionally — applies to every Path A/B/C target file).
It covers the Step 5 side-effect baseline and Step 7 validation content that
`workflow.md` delegates here.

---

## Side-Effect Inventory (Step 5 baseline)

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

This inventory is the baseline that the Required Validation section below MUST reconfirm
as unchanged after transformation (`workflow.md` Step 7). If any side effect changes,
stop and record it as a proposal unless explicitly approved.

---

## Required Validation (Step 7)

Run repository-defined validation for:
- formatting
- linting
- type checking
- affected tests
- public API stability
- exception behavior
- side effects
- import boundaries when imports change

At minimum:
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

- **Side-effect inventory recheck** — confirm the Step 5 inventory above is unchanged.

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

Path C additionally requires `path-c.md`'s Architecture Comparison Validation section —
apply it in the same Step 7 pass as the checks above.

---

## Conditional Validation (Step 7)

Run these tools only when the repository configures and supports them:
- `mutmut`
- `diff-cover`
- `import-linter`
- `pydeps`
- `ast-grep`
- `pyright`
- `pre-commit`
- `libcst`

If a conditional tool is unavailable:
- Report why it was not run.
- Use a repository-defined alternative when available.
- Do not report the skipped check as passed.
- Report `Blocked` only if the missing check is required to prove behavior preservation.
- Otherwise, continue and record the check as `Not run`.

Do not require interactive Git commands. Use non-interactive `git diff` commands. Do not
stage or commit unless the user explicitly requests it. Report suggested commit
boundaries in the final report (`report-template.md`).

If mutation testing is not configured, report `Not run`. Do not invent mutation results.

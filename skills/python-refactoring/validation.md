# Python Refactoring — Side-Effect, Test, Type, and API Validation

Loaded at Step 0 for every Path. Covers the Step 5 side-effect baseline and Step 7 validation
that `workflow.md` delegates here.

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

Required Validation below MUST reconfirm this inventory unchanged after transformation. If any
side effect changes, stop and record a proposal unless explicitly approved.

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
- complexity (`radon cc` grade against the Step 4 baseline)
- import boundaries when imports change

At minimum:
- Run `ruff format`/`ruff check --fix` (per `workflow.md` Step 6, immediately after
  each transformation).
- Run `mypy`.
- Cross-check with `pyright`.
- Run characterization tests.

Per `rules/ai-execution.md` Repository Tool Usage #8, empty output/exit 0 is not proof: confirm
each tool analyzed/collected the target (a zero-test run or a path-typo no-match run is not a
clean result).

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

  A required public API change: stop and record a proposal unless explicitly approved.

- **Exception behavior freeze** — MUST NOT change exception behavior unless explicitly
  approved. Preserve:
  - Exception types
  - Exception messages where visible or tested
  - Retry behavior
  - Fallback behavior
  - Error logging behavior
  - Error return values
  - Failure ordering

  MUST NOT fix apparently incorrect exception handling during refactoring; record it as a proposal.

- **Side-effect inventory recheck** — confirm the Step 5 inventory above is unchanged.

- **Complexity check** — re-run `uv run radon cc <target file> -s` and compare each
  function with the Step 4 baseline. A function whose grade got worse MUST be fixed or
  recorded as a Proposal (`SKILL.md` Core rules); an improvement is reported, not
  required. A function that did not exist in the baseline (a new helper) is compared
  against the grade of the code it was extracted from.

- **Import boundary evidence** — when imports are changed, record:
  - Imports added
  - Imports removed
  - Imports moved
  - Layer boundary impact (see `skills/DESIGN.md`, section "Import layer contract")
  - `import-linter` result
  - Circular import risk
  - Runtime import side-effect risk

  MUST NOT introduce a new import from a lower layer to a higher layer unless explicitly
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

If a conditional tool is unavailable, apply `skills/DESIGN.md` "Tool availability guard":
`Blocked` only if the missing check is required to prove behavior preservation, otherwise
continue and record `Not run`.

Use non-interactive `git diff` only (staging/commit policy: `workflow.md` Step 8).

If mutation testing is not configured, report `Not run`; MUST NOT invent results. 0 surviving of
0 generated mutants means the target was not mutated (e.g. an empty `source_paths` match)
(`rules/ai-execution.md` Repository Tool Usage #8); require a non-zero mutant count before
treating a run as evidence.

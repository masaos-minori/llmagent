## Goal

Expand the new ruff gate's `__CHANGED_FILES__` sentinel to the changed `scripts/`
Python files and run ruff through the existing `_subprocess_runner`, so the fast-mode
gate scopes to the changed files instead of the whole repository
(`REQ-001`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

Orchestrator change to `tools/run_validation_gates.py` only. The gate definition lives
in `tools/_validation_gate_defs.py` (sibling document). This is the additive-guard
change that enables `REQ-004` scoping.

## Assumptions

- `run_gate(gate, *, runner=None)` (current line 244) runs each of `gate.command` in
  order via `effective_runner(list(cmd), env)`, stopping at the first non-zero exit, and
  short-circuits to `Not available` when `gate.requires_context` is `True`. It currently
  takes **no** changed-files argument and expands **no** sentinel.
- `_run_gates(base, mode)` (current line 487) computes `changed = _changed_files(base)`
  once and calls `run_gate(gate)` for each selected gate — passing no changed files.
- `requires_context` (in `tools/_validation_gate_defs.py`) is `True` only for tokens
  matching `[<\[\]]|\.\.\.`; the new ruff gate's `__CHANGED_FILES__` carries none, so it
  stays auto-runnable and reaches the run loop.
- `_matches(changed, patterns)` (current line 183) decides whether a changed path matches
  a gate's patterns; the ruff gate's patterns are `("scripts/*.py", "scripts/**/*.py")`.
- Every other gate's commands carry no `__CHANGED_FILES__` token, so a guard on the
  sentinel's presence leaves them byte-for-byte unchanged.

## Design decisions

- **Expand inside `run_gate`, guarded on the sentinel.** Add a `changed_files` keyword to
  `run_gate`. When it is not `None` and some command in `gate.command` contains the literal
  token `__CHANGED_FILES__`, replace that token in each such command with the changed
  files that match `gate.patterns`; otherwise run `gate.command` unchanged. This is purely
  additive: gates without the sentinel (all existing ones) are unaffected.
- **Scope by the gate's own patterns.** The expanded file list is
  `[f for f in changed_files if _matches([f], gate.patterns)]`, i.e. only the changed
  `scripts/` Python files, never a bare `scripts/` directory or unrelated paths
  (`REQ-004`).
- **No second runner.** Expansion feeds the existing `_subprocess_runner` through the
  unchanged `for cmd in ...` loop; the argv is built as a plain list, so the
  "external commands always run as subprocesses with a list argument" contract holds.

## Alternatives considered

- **Expand in `_run_gates` before calling `run_gate`.** Rejected in favor of expanding in
  `run_gate` (the plan's Design 1): it keeps the substitution next to the run loop and
  mirrors how the existing `requires_context` short-circuit already lives in `run_gate`.
- **A scoped-ruff helper under `tools/`.** Rejected (sibling document): it would be a new
  tool and trigger the "Adding a new tool" routing.md sequence.

## Implementation
### Target file
`tools/run_validation_gates.py`

### Procedure
1. Add a module-level sentinel constant and a small expansion helper.
2. Change `run_gate`'s signature to accept `changed_files` and expand the sentinel.
3. Change `_run_gates` to pass `_changed_files(base)` into `run_gate`.

### Method
1. After the regex-constant block near the top, add:
   ```python
   # Non-placeholder token the ruff routing gate uses where the changed-file list goes.
   # Deliberately free of <, [, ], ... so Gate.requires_context stays False and the gate
   # is auto-runnable; run_validation_gates.py substitutes the real paths for it.
   CHANGED_FILES_SENTINEL = "__CHANGED_FILES__"
   ```
2. Add the expansion helper next to `_merge_env`:
   ```python
   def _expand_changed_files(
       command: tuple[str, ...], matched: list[str]
   ) -> tuple[str, ...]:
       """Replace the __CHANGED_FILES__ token in ``command`` with ``matched`` changed files.

       Returns ``command`` unchanged when it carries no sentinel, so gates without the
       token are byte-for-byte unaffected. The single token expands to every matched
       changed file, keeping ruff scoped to the changed ``scripts/`` Python files.
       """
       if CHANGED_FILES_SENTINEL not in command:
           return command
       out: list[str] = []
       for tok in command:
           if tok == CHANGED_FILES_SENTINEL:
               out.extend(matched)
           else:
               out.append(tok)
       return tuple(out)
   ```
   The pattern filtering (which changed files count as "matched") happens in `run_gate`
   via `gate.patterns`; this helper only substitutes the token.
3. Change `run_gate`:
   ```python
   def run_gate(
       gate: Gate, *, runner: Runner | None = None, changed_files: list[str] | None = None
   ) -> GateResult:
   ```
   Inside, after the `requires_context` check and before the `for cmd in gate.command`
   loop, substitute:
   ```python
   commands = gate.command
   if changed_files is not None and any(
       CHANGED_FILES_SENTINEL in cmd for cmd in gate.command
   ):
       matched = [p for p in changed_files if _matches([p], gate.patterns)]
       commands = tuple(_expand_changed_files(cmd, matched) for cmd in gate.command)
   try:
       for cmd in commands:
           proc = effective_runner(list(cmd), env)
           ...
   ```
   Keep the rest of `run_gate` (the `FileNotFoundError`/`OSError` handling and the final
   `Pass`) operating on `commands`.
4. Change `_run_gates`:
   ```python
   def _run_gates(base: str, mode: str) -> int:
       changed = _changed_files(base)
       gates = select_gates(changed, mode)
       results = [run_gate(gate, changed_files=changed) for gate in gates]
       _print_summary(results, changed, mode)
       return 1 if any(res.status == "Fail" for res in results) else 0
   ```

### Details
- `_matches` takes an iterable of paths; call it per path (`_matches([p], gate.patterns)`)
  to filter `changed_files` down to the changed `scripts/` files only. Do not pass the
  whole `changed` list and then run ruff over everything.
- `gate.patterns` is `()` for manual/content-based gates; those gates never carry the
  sentinel, so the `any(...)` guard short-circuits and they run unchanged.
- The sentinel appears in **both** ruff commands (format then check); the expansion runs
  for each, so both argvs carry the same changed-file list.
- Existing test calls `run_gate(gate, runner=_runner_for(...))` remain valid: `changed_files`
  defaults to `None`, so the sentinel branch is skipped and behavior is identical.

## Compatibility considerations

- Additive keyword argument with a `None` default; no positional-argument or existing
  signature change. No existing gate carries the sentinel, so the substitution branch is
  dead for all current gates. Blast radius is confined to `run_gate`/`_run_gates`.

## Security considerations

N/A: no authentication, authorization, or input-handling change. Paths come from
`git diff --name-only` and are validated by `_validate_ref` before reaching the runner.

## Rollback considerations

Revert this single commit; the sentinel, helper, and keyword are new and touch no
runtime data shape.

## Validation plan

- `uv run pytest tests/tools/test_run_validation_gates.py` — the full suite still passes
  (regression), plus the new passing/failing/scoped changed-file cases
  (`REQ-001`, `REQ-004`, `REQ-006`).
- Injected-runner scoping assertion: the ruff argv the runner receives carries the changed
  `scripts/` paths, not a bare `scripts/` directory (`REQ-004`, `AC-004`).
- `uv run ruff check tools/run_validation_gates.py`; `uv run mypy tools/` — clean.
- Manual end-to-end: run the fast gate against a `scripts/` file with a deliberate
  `I001` error (reverted after) and confirm it reports `Fail` and names the file
  (`AC-001`).

## Completion criteria

- A changed `scripts/` file carrying an `I001` error yields `Fail` naming the file; a
  clean changed file yields no ruff `Fail` (`REQ-001`, `REQ-002`, `AC-001`, `AC-002`).
- The ruff argv carries the changed `scripts/` paths, not a bare `scripts/` directory
  (`REQ-004`, `AC-004`).
- All existing gate tests still pass (`REQ-006`).

## Out of Scope

- Defining the gate itself (`tools/_validation_gate_defs.py`, sibling document).
- Adding the `routing.md` drift row, the `rules/toolchain.md` doc (separate documents).
- Installing or documenting the git pre-commit hook (out of scope for the Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Expand the ruff gate's changed-file sentinel in `run_gate`/`_run_gates` (`tools/run_validation_gates.py`) | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: `issues/20261115-183024_lintgate001_ruff-check-local-gate.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-202908_lintgate001_ruff-check-local-gate.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095520
- **Related target files**: `tools/run_validation_gates.py`

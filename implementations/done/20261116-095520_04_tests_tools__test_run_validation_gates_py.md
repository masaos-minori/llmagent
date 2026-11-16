## Goal

Add unit tests for the new fast-mode ruff gate: a passing changed-file case, a failing
changed-file case (an `I001` import-order error yields `Fail` and names the file), a
scoping assertion (the argv carries the changed `scripts/` paths, not a bare `scripts/`
directory), and a drift-still-passes assertion after the `routing.md` row is added
(`REQ-001`, `REQ-004`, `REQ-005`, `REQ-006`, `AC-001`–`AC-005`).

## Scope
**Release unit**: N/A: not part of a release unit

Test-only change to `tests/tools/test_run_validation_gates.py`. These tests validate the
gate definition (`tools/_validation_gate_defs.py`, sibling document) and the
sentinel-expansion behavior (`tools/run_validation_gates.py`, sibling document). No
source or docs file changes here.

## Assumptions

- The file uses an injected-runner pattern (`_runner_for`, current line 42) rather than
  `unittest.mock`, so `check_mock_patch_targets` never sees a module-level patch target.
  The injected `Runner` receives `(argv, env)` and returns a
  `subprocess.CompletedProcess`; tests can capture `argv` and return a chosen
  `returncode`.
- `run_gate(gate, *, runner=None)` (current signature) is extended by the sibling
  document with a `changed_files` keyword. Tests call it as
  `run_gate(gate, runner=<capturing>, changed_files=[...])`.
- The new gate is found in `ROUTING_GATES` by name `ruff_format_check_changed` (defined in
  the sibling document).
- `select_gates(["scripts/x.py"], MODE_FAST)` selects the new gate, since its patterns
  match `scripts/*.py`.

## Design decisions

- **Classify each new test by which Requirement it backs**, but keep them in this single
  test file because the file validates both siblings' rows and neither sibling can claim
  it as a companion (both name it in their `Related Tests` cell). One test per concern:
  passing, failing, scoping, drift.
- **Scoping is proven via the captured argv**, not a real ruff subprocess: the capturing
  runner records the argv it received, and the assertion checks the changed paths are
  present and a bare `scripts/` directory is absent.

## Alternatives considered

- **A real subprocess run against a fixture file.** Rejected for the unit test: the
  injected-runner pattern avoids spawning ruff and keeps the suite hermetic; the real
  `I001`→`Fail` end-to-end is covered by the manual gate run in the sibling documents'
  validation plans.

## Implementation
### Target file
`tests/tools/test_run_validation_gates.py`

### Procedure
Append four tests after the `run_gate runner injection` section (near the end of the
file), before the re-export test.

### Method
1. Passing changed-file case:
   ```python
   def _ruff_gate():
       return next(g for g in ROUTING_GATES if g.name == "ruff_format_check_changed")
   
   def test_ruff_gate_passes_on_clean_changed_file() -> None:
       """A clean changed scripts/ file yields Pass (AC-002)."""
       gate = _ruff_gate()
       assert gate.mode == MODE_FAST
       result = run_gate(gate, runner=_runner_for(0), changed_files=["scripts/clean.py"])
       assert result.status == "Pass"
   ```
2. Failing changed-file case (the `I001` semantics are asserted via the manual run; the
   unit test asserts the non-zero exit classifies as `Fail` and names the file):
   ```python
   def test_ruff_gate_fails_on_i001_changed_file() -> None:
       """A non-zero ruff exit on a changed scripts/ file yields Fail naming the file (AC-001)."""
       gate = _ruff_gate()
       result = run_gate(
           gate, runner=_runner_for(1), changed_files=["scripts/bad.py"]
       )
       assert result.status == "Fail"
       assert "bad.py" in result.detail or "exit code 1" in result.detail
   ```
3. Scoping assertion (REQ-004 / AC-004):
   ```python
   def test_ruff_gate_scopes_argv_to_changed_paths() -> None:
       """The ruff argv carries the changed scripts/ paths, not a bare scripts/ directory."""
       gate = _ruff_gate()
       captured: dict[str, list[str]] = {}
   
       def _capture(argv: list[str], env: dict[str, str] | None):
           captured["argv"] = argv
           return subprocess.CompletedProcess(args=argv, returncode=0)
   
       result = run_gate(
           gate,
           runner=_capture,
           changed_files=["scripts/a.py", "scripts/sub/b.py"],
       )
       assert result.status == "Pass"
       argv = captured["argv"]
       assert "scripts/a.py" in argv
       assert "scripts/sub/b.py" in argv
       # Not a bare directory argument.
       assert "scripts/" not in argv
       # Runs via the pinned uv ruff, format then check.
       assert argv[0:3] == ["uv", "run", "ruff"]
   ```
4. Drift-still-passes after the `routing.md` row (REQ-005 / AC-005):
   ```python
   def test_drift_still_passes_after_ruff_gate_added() -> None:
       """After the routing.md row is added, every checker is still mapped (AC-005)."""
       text = ROUTING_MD.read_text(encoding="utf-8")
       count, errors = drift_report(text)
       assert count == 0, errors
       assert any(g.checker_id == "uv" for g in ROUTING_GATES)
   ```

### Details
- Import `subprocess` is already present at the top of the file; `_runner_for` is already
  defined. Do not add a `unittest.mock` import.
- The scoping test asserts `argv[0:3] == ["uv", "run", "ruff"]` to pin the pinned-ruff
  invocation (`REQ-003` / AC-003) alongside the scoping proof.
- The failing test does not spawn ruff; the real `I001`→`Fail` end-to-end is the manual
  gate run documented in the sibling documents' validation plans.

## Compatibility considerations

- Additive tests only; no existing test is modified, so the 59-test baseline regression
  is preserved (`REQ-006`).
- The injected-runner pattern is unchanged, so `check_mock_patch_targets` stays clean.

## Security considerations

N/A: test-only change; no authentication, authorization, or input-handling change.

## Rollback considerations

Revert this single commit; the added tests are new and touch no runtime data shape.

## Validation plan

- `uv run pytest tests/tools/test_run_validation_gates.py` — the new passing, failing,
  scoping, and drift tests pass and all prior tests still pass (`REQ-006`, `AC-001`–
  `AC-006`).
- `uv run ruff check tests/tools/test_run_validation_gates.py`; `uv run mypy tools/` —
  clean.
- Manual end-to-end: run the fast gate against a `scripts/` file with a deliberate
  `I001` error (reverted after) and confirm it reports `Fail` and names the file
  (`AC-001`).

## Completion criteria

- A clean changed `scripts/` file yields `Pass`; a non-zero ruff exit on a changed
  `scripts/` file yields `Fail` (`REQ-001`, `REQ-002`, `AC-001`, `AC-002`).
- The ruff argv carries the changed `scripts/` paths, not a bare `scripts/` directory
  (`REQ-004`, `AC-004`), starts with `uv run ruff` (`REQ-003`, `AC-003`), and the drift
  invariant stays green after the `routing.md` row (`REQ-005`, `AC-005`).

## Out of Scope

- Defining the gate (`tools/_validation_gate_defs.py`, sibling document).
- Expanding the sentinel in the orchestrator (sibling document), the `routing.md` row,
  and the `rules/toolchain.md` doc (separate documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261116-211620 | 20261116-211620 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261116-211620 | 20261116-211620 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-211620 | 20261116-211620 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261116-211620 | 20261116-211620 |  |

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
- **Requirement ID**: `REQ-001`, `REQ-004`, `REQ-005`, `REQ-006`
- **Source issue**: `issues/20261115-183024_lintgate001_ruff-check-local-gate.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-202908_lintgate001_ruff-check-local-gate.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095520
- **Related target files**: `tests/tools/test_run_validation_gates.py`
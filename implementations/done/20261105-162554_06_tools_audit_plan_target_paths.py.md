## Goal
- Give `tools/audit_plan_target_paths.py` an `argparse` entry with a positional `plans` list, so it answers `--help` while `main()` keeps reading `sys.argv[1:]` as it does today and its behavior and exit codes stay identical (`REQ-003`: `--help` through `argparse`, no behavior change; `REQ-005`: no hook or CI change).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `tools/audit_plan_target_paths.py` only: a `_parse_args` (new) helper and the `main(argv)` signature.
- Plan: `plans/done/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md`, Plan step 3 (Phase 3).

## Assumptions
- Today `main()` takes no argument and reads `sys.argv[1:]`; `tools/amend_plan.py` runs the tool by path with one plan argument, and `tests/tools/test_audit_plan_target_paths.py` (added by the `toolstest001` Plan) calls `main()` after patching `sys.argv`, in sorted-order and exit-code cases (verified 2026-11-05).
- Unlike the other four tools, this one keeps the `sys.argv` fallback: `main(None)` uses `sys.argv[1:]`, so those tests and `amend_plan.py` keep working unchanged.
- `audit` is graded C (19) by `radon cc` and is not touched; `main` stays small.
- Plan overlap: no other open Plan targets this file; the `toolstest001` tests land first (the Plan's `Depends on`).

## Design decisions
- `_parse_args(argv: list[str]) -> argparse.Namespace` defines the positional `plans` with `nargs="*"` and the module docstring's first line as description.
- `main(argv: list[str] | None = None) -> int` computes `args = _parse_args(sys.argv[1:] if argv is None else argv)` and then builds `plans = [Path(a) for a in args.plans] if args.plans else sorted(Path("plans").glob("*.md"))`, with the rest unchanged.

## Alternatives considered
N/A: keeping the current `sys.argv` fallback preserves the existing test and caller contract.

## Implementation
### Target file
`tools/audit_plan_target_paths.py`

### Procedure
1. Add `import argparse` next to the existing imports.
2. Add `_parse_args` (new) above `main`.
3. Change `main` to `main(argv: list[str] | None = None) -> int` and replace its first line (`args = sys.argv[1:]`) with the parser call above; keep the loop, the summary line, and the return unchanged.

### Method
- A positional argument that starts with `-` is now a flag error (exit `2` through argparse) instead of being treated as a plan path; no caller passes such an argument.

### Details
- Keep the `__main__` block as `sys.exit(main())`: `main(None)` already reads `sys.argv[1:]`.
- Do not change `audit`, `ROW_RE`, or `CREATE_HINTS`.

## Compatibility considerations
- `amend_plan.py` (one plan path) and the existing tests (patched `sys.argv`) keep working.

## Security considerations
N/A: the tool reads plan files and checks path existence only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_audit_plan_target_paths.py tests/tools/test_amend_plan.py -q` passes.
- `uv run python tools/audit_plan_target_paths.py --help` exits `0`; `uv run python tools/audit_plan_target_paths.py plans/<one plan>.md` prints the same lines and exit code as before.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy tools/audit_plan_target_paths.py`, `uv run bandit tools/audit_plan_target_paths.py` are clean.

## Completion criteria
- `--help` exits `0`, `main()` still reads `sys.argv[1:]`, outputs and exit codes match the before-run, and the checks above are clean.

## Out of Scope
- The audit logic, the create-hint matching, and `amend_plan.py`.

## Adversarial Verification (20261106)
- Applied `rules/ai-execution.md` Adversarial Verification (Base). Claims treated as unverified; checked `tools/audit_plan_target_paths.py`, `tests/tools/test_audit_plan_target_paths.py`, `tools/amend_plan.py`, `tools/run_validation_gates.py`, and the open plans referencing this tool.
- Claim 1 (`main()` takes no argument and reads `sys.argv[1:]`; `amend_plan.py` runs it by path with one plan argument; tests call `main()` after patching `sys.argv`): CONFIRMED. `main()` line 55 reads `sys.argv[1:]` (line 56); `amend_plan.py` invokes `[TOOLS_DIR/"audit_plan_target_paths.py", rel]` (lines 512-513); tests `monkeypatch.setattr(sys, "argv", [...])` then call `main()` (lines 135, 150, 167).
- Claim 2 (keeps the `sys.argv` fallback vs. the other four: `main(None)` uses `sys.argv[1:]`): CONFIRMED. Current `main()` reads `sys.argv[1:]` directly; the design's `main(None)` branch preserves this so `amend_plan.py` and patched-argv tests keep working.
- Claim 3 (`audit` graded C (19); no other open Plan targets this file; `toolstest001` tests land first): CONFIRMED. `radon cc -s` reports `audit - C (19)`; no open plan lists `tools/audit_plan_target_paths.py` as a change target; the tests exist (dependency satisfied).
- Detail check: `argparse` is not yet imported and `main()` takes no argument — consistent with Step 1.
- Deliverable state: implementation steps remain `Pending` (not executed under this verify-only task). No behavioral claim is stale.
- Gates: `pytest` (this + `test_amend_plan.py`) -> 48 passed; `ruff check` clean; `mypy` -> no issues; `bandit` -> 0 findings.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_parse_args` and the `main(argv)` signature | Pending | — | — | |
| 2 | Update the existing tests only if one breaks; otherwise record `N/A: no test change needed` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and a before-and-after run on live plans | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (`--help` through `argparse`), `REQ-005` (no hook or CI change)
- **Source issue**: issues/20261104-152002_toolcli001_define-cli-and-exit-code-convention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-162554
- **Related target files**: `tools/audit_plan_target_paths.py`

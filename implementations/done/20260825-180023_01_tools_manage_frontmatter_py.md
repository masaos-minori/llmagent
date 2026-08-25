# Implementation Procedure: Fix manage_frontmatter.py add-missing destructive-by-default CLI

## Goal

Make `manage_frontmatter.py add-missing` safe by default: no-flag invocation must report-only (no writes), require explicit opt-in (`--fix`) to perform actual writes, and fix the `main()` → `cmd_add_missing()` argument hand-off so `--dry-run` actually reaches the subcommand parser.

## Scope

- **In-Scope**: `tools/manage_frontmatter.py` (`cmd_add_missing`, `main`)
- **Out-of-Scope**: Changes to `cmd_dedupe_lists` behavior, changes to Front-Matter content-generation logic (`build_frontmatter`, `extract_category_from_filename`, etc.), any other `tools/*.py` script.

## Assumptions

- The intended default behavior is dry-run/report-only (not write), based on the presence of the `--dry-run` flag declaration and the fact that the `--fix` flag was added but never wired up — suggesting the original design intent was dry-run-first.
- The existing `--fix` flag name is acceptable as the write-enabling flag; if ambiguous, stop and ask rather than guessing.
- **Uncertainty**: The issue itself states "If the intended default behavior (dry-run vs. fix) is ambiguous, stop and ask rather than guessing." This assumption is not confirmed by evidence — it is an inference from the existence of an unconnected `--fix` flag.

## Design decisions

### Remove round-trip re-encoding

Rather than patching the string conversion, have `cmd_add_missing` accept the already-parsed `Namespace` object directly. This eliminates the underscore/hyphen mismatch entirely.

### Flip default to non-destructive

Change `cmd_add_missing` so that:
1. No-flag invocation = dry-run/report-only (no writes)
2. `--fix` = explicit opt-in to write
3. `--dry-run` = still works as documented (preview only)

This means the condition on line 198 flips: `if args.fix:` triggers writes instead of `if not args.dry_run:`.

### Keep `--dry-run` flag

Retain the `--dry-run` flag for backward compatibility with users who may have scripts referencing it. Both `--dry-run` and no-flag now behave identically (report-only). Only `--fix` enables writes.

## Alternatives considered

- **Patch the string conversion** in `main()` to convert underscores to hyphens before passing to `cmd_add_missing`. Rejected because it adds complexity and doesn't solve the root problem (re-encoding parsed args back into strings is fragile).
- **Rename `--fix` to `--write`**. Not done — the issue states the existing `--fix` flag name is acceptable.

## Implementation

### Target file

`tools/manage_frontmatter.py`

### Procedure

#### Phase 1: Argument wiring fix

1. Modify `cmd_add_missing` signature to accept `argv: list[str] | Namespace | None = None`
2. In `cmd_add_missing`, detect if `argv` is a `Namespace` object and use it directly instead of parsing again
3. Update `main()` to pass `args` (the `Namespace`) directly to `cmd_add_missing` instead of the round-trip string list

#### Phase 2: Flip default to non-destructive

1. Change the write condition from `if not args.dry_run:` to `if args.fix:` in `cmd_add_missing`
2. Update the `else` branch to always print a preview (no-flag case)
3. Update the `--fix` help text to clarify it enables actual writes

#### Phase 3: Update documentation

Update the script's `Usage` docstring to state that no-flag invocation is safe/non-destructive and name the flag required to write.

#### Phase 4: Add tests

1. Create `tests/tools/test_manage_frontmatter.py` with temp directory fixture
2. Test: no-flag call performs no writes
3. Test: `--dry-run` performs no writes and exits 0
4. Test: `--fix` performs the expected write

#### Phase 5: Validation

1. Run `uv run pytest tests/tools/test_manage_frontmatter.py -v`
2. Run `uv run ruff check tools/manage_frontmatter.py`
3. Run `uv run mypy tools/manage_frontmatter.py`

### Method

Phase 1 changes the data flow: instead of `main()` converting `Namespace` → string list → parse again in `cmd_add_missing`, pass the `Namespace` directly. This requires:

```python
def cmd_add_missing(argv: list[str] | Namespace | None = None) -> int:
    if isinstance(argv, Namespace):
        args = argv
    else:
        parser = argparse.ArgumentParser(...)
        parser.add_argument("--dry-run", ...)
        parser.add_argument("--fix", ...)
        args = parser.parse_args(argv)
```

Phase 2 changes the conditional logic at line 198:

```python
# Before:
if args.dry_run:
    # print preview
else:
    # write to file

# After:
if args.fix:
    # write to file
else:
    # print preview (both --dry-run and no-flag cases)
```

Phase 3 updates the Usage docstring at line 12-14.

### Details

Verified against current source:
- Line 333-336: `cmd_add_missing([f"--{k}" for k, v in vars(args).items() if v and k not in ("subcommand",)])` — confirmed, `dry_run` becomes `--dry_run` which doesn't match `--dry-run`
- Line 163: `--fix` is declared but never checked in the function body — confirmed, `args.fix` is never referenced
- Line 198-206: When `args.dry_run` is falsy (default), writes to files — confirmed

## Compatibility considerations

- Retaining `--dry-run` flag ensures backward compatibility with any external scripts that reference it
- The change from "destructive-by-default" to "safe-by-default" is a behavioral breaking change for users relying on the current default
- Document the change clearly in the Usage docstring and release notes

## Security considerations

N/A: no security-sensitive operations affected.

## Rollback considerations

If the new default breaks workflows, revert to the old behavior by restoring `if not args.dry_run:` as the write condition. The rollback is a single-line change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/manage_frontmatter.py` | Unit test — no-flag path | `uv run pytest tests/tools/test_manage_frontmatter.py::test_no_flag_no_write -v` | Exit 0, zero file mutations |
| `tools/manage_frontmatter.py` | Unit test — `--dry-run` path | `uv run pytest tests/tools/test_manage_frontmatter.py::test_dry_run_no_write -v` | Exit 0, preview printed, zero file mutations |
| `tools/manage_frontmatter.py` | Unit test — `--fix` path | `uv run pytest tests/tools/test_manage_frontmatter.py::test_fix_performs_write -v` | Exit 0, front matter written |
| `tools/manage_frontmatter.py` | Lint | `uv run ruff check tools/manage_frontmatter.py` | Clean (no errors) |
| `tools/manage_frontmatter.py` | Type check | `uv run mypy tools/manage_frontmatter.py` | Clean (no new regressions) |

## Completion criteria

- [ ] No-flag invocation does not modify any file under `docs/`
- [ ] `--dry-run` runs to completion without modifying files
- [ ] `--fix` is the only write-enabling invocation
- [ ] Regression test exercises both paths using temp files

## Out of scope

- Changing the `--fix` flag name to something more descriptive (e.g., `--write`)
- Adding a confirmation prompt before writing
- Modifying `cmd_dedupe_lists` or any other subcommand
- Adding a separate `--confirm` flag for write operations

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: REQ-001 through REQ-005
- **Source issue**: issues/20260824_01_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-174653_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-180023
- **Related target files**: tools/manage_frontmatter.py

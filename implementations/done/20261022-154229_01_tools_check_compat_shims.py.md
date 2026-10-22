## Goal

Replace the static `DEFAULT_ALLOWLIST` set in `tools/check_compat_shims.py` with a manifest-driven model: load and validate `tools/compat_exceptions.toml`, fail on expired/incomplete entries, and add a report-only `--check-doc-symbols` stage that reuses `tools/_docs_consistency_lib.check_function_references` (REQ-001, REQ-002, REQ-003, REQ-004; AC-1, AC-2, AC-3, AC-4).

## Scope

- Modify `tools/check_compat_shims.py` only.
- Remove `DEFAULT_ALLOWLIST`; add `load_exceptions`, `validate_exceptions`, and `check_doc_symbols` helpers; wire expiry failure and `--check-doc-symbols` into `main()`.
- Keep the public surface unchanged: the `allowlist` parameter of `check_all()` and the `--allowlist` CLI flag keep their exact signatures and behavior.

## Assumptions

- The manifest stores repo-relative `path` values; the loader resolves them against `ROOT_DIR` so the resulting `set[Path]` matches the absolute paths `main()` scans (mirroring `DEFAULT_ALLOWLIST`).
- `owner` is the governance owner role ("Repository owner") already used in the repository; no per-person owner is invented.
- Python 3.13 `tomllib` is available for loading the manifest.

## Design decisions

- Add three small helpers (`load_exceptions`, `validate_exceptions`, `check_doc_symbols`) instead of growing `main()`, whose radon complexity is C(16); this keeps `main()` flat.
- `main()` loads the manifest only when `--allowlist` is not given, so tests that inject an allowlist keep their current behavior.
- The symbol stage post-filters the library result: drop names defined under `tools/` and manifest-listed allowances, then print the remaining findings as `WARNING` without touching the exit code.

## Alternatives considered

- Folding manifest loading and validation into `main()` — rejected: would raise `main()`'s complexity past the baseline and mix concerns.
- Making `--check-doc-symbols` blocking — rejected by the Plan (UNK-03 is a separate decision); the stage stays report-only.

## Implementation

### Target file

`tools/check_compat_shims.py`

### Procedure

1. Delete the `DEFAULT_ALLOWLIST` block (definition plus its comment header).
2. Add `load_exceptions(manifest_path)` — parse the TOML with `tomllib`, resolve each entry's `path` against `ROOT_DIR`, return `(list[entry], set[Path])`.
3. Add `validate_exceptions(entries)` — enforce required fields, valid category, parseable `expires`, id uniqueness, and non-expiry; raise/return a finding list; exit code 1 naming any offending id.
4. Add `check_doc_symbols(repo_root, docs_dir)` — reuse `check_function_references`, post-filter `tools/`-defined names and manifest allowances, collect `WARNING` issues.
5. Wire expiry failure and `--check-doc-symbols` into `main()`.
6. Run ruff, mypy, bandit, the targeted tests, and the live smoke runs.

### Method

- Replace the `allowlist` fallback in `main()`:

  ```python
  if args.allowlist and args.allowlist.exists():
      allowlist = {...existing custom-load logic...}
  else:
      entries, allowlist = load_exceptions(ROOT_DIR / "tools" / "compat_exceptions.toml")
      validate_exceptions(entries)   # exits 1 on an expired/incomplete entry
  ```

- Add the new argument after `--check-removed-names`:

  ```python
  parser.add_argument(
      "--check-doc-symbols",
      action="store_true",
      help="Report-only: warn about doc references to functions absent from scripts/.",
  )
  ```

- After the existing scan loop, when `args.check_doc_symbols` is set, call `check_doc_symbols(ROOT_DIR, ROOT_DIR / "docs")`, print each `WARNING` to stderr, and never add to `total_issues` (exit code unaffected).

### Details

- Evidence in-file: `DEFAULT_ALLOWLIST` is defined at lines 117-165 and consumed only at line 474 (`allowlist = DEFAULT_ALLOWLIST.copy()`).
- `check_function_references(docs_dir, files, repo_root)` lives in `tools/_docs_consistency_lib.py` and returns `Issue(severity="WARNING", ...)` objects; `extract_defined_function_names()` scans only `scripts/`, so `tools/`-defined names must be post-filtered here.
- Required entry fields: `id`, `path`, `reason`, `owner`, `expires` (ISO date), `removal_condition`, `category` ∈ {`compatibility`, `migration`, `fallback`, `fixture`}. An unknown category, unparseable date, duplicate id, or `expires` earlier than today is a finding → exit 1 naming the id (REQ-002).
- The 20 migrated paths are exactly the 20 `DEFAULT_ALLOWLIST` entries that still produce findings under `check_all(..., allowlist=set(), include_removed_names=True)`; the 4 that do not (3 with no finding, 1 deleted `tests/agent/test_startup_routing_drift.py`) are dropped, not migrated.

## Compatibility considerations

N/A: no runtime contract changes; `check_all()` and `--allowlist` keep their signatures. Behavior is identical when an allowlist is injected; the manifest only replaces the default.

## Security considerations

N/A: no auth, authorization, or input-handling path is added; the manifest is trusted tool configuration under `tools/`.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/check_compat_shims.py` | Unit + live smoke | `uv run ruff check tools/`; `uv run mypy --no-namespace-packages tools/check_compat_shims.py`; `uv run bandit -q tools/check_compat_shims.py`; `uv run python tools/check_compat_shims.py --check-removed-names`; `uv run python tools/check_compat_shims.py --check-doc-symbols` | Linters pass; removed-names exits 0; symbol stage prints Warnings, exits 0 |
| Manifest validation | Unit | temp manifest with missing field / bad category / bad date / duplicate id / expired entry | Each fails with exit 1 naming the id |

## Completion criteria

`DEFAULT_ALLOWLIST` is absent from the source, the manifest loads and validates (20 entries, all fields valid), an expired/incomplete entry fails the run with exit code 1 naming the id, `--check-doc-symbols` prints Warnings and exits 0 on the live repository, and `ruff`, `mypy`, `bandit`, `--check-removed-names`, and `--check-doc-symbols` all behave as expected.

## Out of Scope

- Editing `tools/_docs_consistency_lib.py` or the existing pattern checks.
- Making the symbol stage blocking.
- Removing the compatibility features or runtime telemetry themselves.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove DEFAULT_ALLOWLIST; add manifest loader, validator, expiry, and --check-doc-symbols | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (manifest schema and validation), `REQ-002` (expired/incomplete entry fails), `REQ-003` (migrate or delete each allowlist path), `REQ-004` (report-only symbol stage reusing the existing check)
- **Source issue**: `issues/20261022-124220_compatexp_add-expiring-compat-exceptions-and-symbol-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130804_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-154229
- **Related target files**: `tools/check_compat_shims.py`

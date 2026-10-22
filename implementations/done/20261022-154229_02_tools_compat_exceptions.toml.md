## Goal

Create `tools/compat_exceptions.toml` holding the 20 migrated compatibility-exception entries (each with `id`, `path`, `reason`, `owner`, `expires`, `removal_condition`, `category`) plus the symbol-stage allowance set (REQ-001, REQ-003; AC-1, AC-3).

## Scope

- Create the new data file `tools/compat_exceptions.toml` only.
- No other file is modified by this row.

## Assumptions

- Location follows the `tools/*_baseline.txt` precedent (tool data under `tools/` is not deployed).
- `expires` is a review-by date ~6 months ahead of the migration date; `owner` is the "Repository owner" governance role.

## Design decisions

- Model each entry as a TOML table under a top-level `[[compatibility_exceptions]]` array, mirroring the `[[canonical_sources]]` structure in `config/documentation_canonical_sources.toml` (loaded via `tomllib`).
- Keep the symbol-stage allowance as a separate top-level table so the loader can read both from one file.

## Alternatives considered

- Storing the allowlist as a plain list of paths (the old `--allowlist` format) — rejected: it carries no owner, reason, expiry, or removal condition, which is the whole point of this change.

## Implementation

### Target file

`tools/compat_exceptions.toml` (new)

### Procedure

1. Create the file with a `version` key and a `[[compatibility_exceptions]]` array of 20 tables.
2. For each of the 20 needed paths, copy its repo-relative `path` and the intent of its `DEFAULT_ALLOWLIST` comment into `reason`, set `owner` to the governance role, set `expires` to the review-by date, and state the `removal_condition` and a `category` in {`compatibility`, `migration`, `fallback`, `fixture`}.
3. Add the symbol-stage allowance table (names to drop from `check_function_references` output).
4. Validate the file loads under `tomllib` and every entry has all required fields.

### Method

- Repo-relative paths (resolved against `ROOT_DIR` by the loader), e.g.:

  ```toml
  version = "1"

  [[compatibility_exceptions]]
  id = "rag-get-cfg-test"
  path = "tests/agent/test_rag_get_cfg.py"
  reason = "Test file intentionally referencing the removed re-export stub"
  owner = "Repository owner"
  expires = "2027-04-22"
  removal_condition = "Remove this exception when the test no longer references the removed re-export stub."
  category = "fixture"
  ```

- The 20 paths are exactly those still producing findings under `check_all(..., allowlist=set(), include_removed_names=True)`; the 4 that do not are omitted.

### Details

- Evidence: the current `DEFAULT_ALLOWLIST` (lines 117-165 of `tools/check_compat_shims.py`) holds 24 entries; measurement shows 20 produce findings and 4 do not (`docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md`, `tests/shared/test_rag_tools_consistency.py`, `tests/shared/test_route_resolver.py` produce no finding; `tests/agent/test_startup_routing_drift.py` no longer exists).
- `tomllib` is available on Python 3.13.

## Compatibility considerations

N/A: new data file only; the loader consumes it, no runtime contract is affected.

## Security considerations

N/A: trusted tool configuration under `tools/`.

## Rollback considerations

N/A: revert the commit (deletes the file).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/compat_exceptions.toml` | Unit | parity + validation tests; `python -c "import tomllib; tomllib.load(open('tools/compat_exceptions.toml','rb'))"` | Loads; 20 entries, all fields valid; loaded paths == the 20 needed paths |

## Completion criteria

The file parses under `tomllib`, contains 20 entries each with all required fields and a valid category/date, the loaded paths are exactly the 20 needed paths, and the symbol-stage allowance table is present.

## Out of Scope

- Editing `tools/check_compat_shims.py` (separate row).
- Adding any of the 4 dropped paths.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the manifest with the 20 migrated entries and the symbol-stage allowance | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (manifest schema and validation), `REQ-003` (migrate or delete each allowlist path)
- **Source issue**: `issues/20261022-124220_compatexp_add-expiring-compat-exceptions-and-symbol-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130804_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-154229
- **Related target files**: `tools/compat_exceptions.toml`

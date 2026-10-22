## Goal

Keep `tools/TOOL_DESCRIPTIONS.md` in sync with `tools/check_compat_shims.py` after the manifest migration and the new `--check-doc-symbols` flag: describe the manifest-backed exceptions and the report-only symbol stage at the existing `check_compat_shims.py` entry (REQ-007; AC-7).

## Scope

- Modify `tools/TOOL_DESCRIPTIONS.md` only.
- Update the `check_compat_shims.py` row(s) to reflect the new behavior; leave other rows unchanged.

## Assumptions

- The sync checker (`check_tool_descriptions_sync.py`) compares each tool's description against its actual flags/behavior; the description must mention the manifest and `--check-doc-symbols` to stay in sync.
- The `--check-removed-names` description already on the row stays accurate.

## Design decisions

- Extend the existing detailed `check_compat_shims.py` entry (in the detailed table) rather than adding a new row, so the tool keeps a single canonical description.

## Alternatives considered

- Adding a separate short note elsewhere — rejected: the sync checker keys off the tool's own description row.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

1. Update the `check_compat_shims.py` detailed entry to state that the allowlist is now loaded from `tools/compat_exceptions.toml` (each entry carries `id`, `path`, `reason`, `owner`, `expires`, `removal_condition`, `category`), and that an expired or incomplete entry fails the run.
2. Add a sentence describing `--check-doc-symbols` (report-only; warns about doc references to functions absent from `scripts/`, reusing `check_function_references`, non-blocking).
3. Run `check_tool_descriptions_sync.py`.

### Method

- Append to the existing detailed paragraph at the `check_compat_shims.py` row, e.g. after the `--check-removed-names` sentence:

  > The default allowlist is loaded from `tools/compat_exceptions.toml`; each entry requires `id`, `path`, `reason`, `owner`, `expires` (ISO review-by date), `removal_condition`, and a `category` (`compatibility` / `migration` / `fallback` / `fixture`), and an expired or incomplete entry fails the run (exit code 1 naming the id). `--check-doc-symbols` (default OFF) is report-only: it warns about backtick-quoted function references in `docs/` that have no matching definition under `scripts/`, reusing `check_function_references`, drops `tools/`-defined names and manifest allowances, and never changes the exit code.

### Details

- Evidence in-file: the detailed `check_compat_shims.py` row currently describes only pattern detection and `--check-removed-names`; the summary table row names it a "Consistency checker". Neither mentions the manifest or a symbol flag yet.

## Compatibility considerations

N/A: documentation-only; no runtime contract is affected.

## Security considerations

N/A: no auth, authorization, or input-handling path is described here.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Static | `uv run python tools/check_tool_descriptions_sync.py` | Pass |

## Completion criteria

`check_tool_descriptions_sync.py` passes, the `check_compat_shims.py` entry describes the manifest-backed exceptions and `--check-doc-symbols`, and no other row changed.

## Out of Scope

- Editing any other tool's description row.
- Changing the tool's actual behavior (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Describe the manifest and --check-doc-symbols at the check_compat_shims.py entry | Pending | — | — | |
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
- **Requirement ID**: `REQ-007` (tool description sync: describe the manifest and the new flag)
- **Source issue**: `issues/20261022-124220_compatexp_add-expiring-compat-exceptions-and-symbol-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130804_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-154229
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`

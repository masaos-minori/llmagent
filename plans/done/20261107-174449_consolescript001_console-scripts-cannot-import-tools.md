## Goal
- Replace the failing console-script shorthand invocations in the toolchain documentation with the working `python -m tools.<name>` module form, treating `tools/` as a dev-only directory and leaving `pyproject.toml` packaging unchanged.

## Priority
Medium

## Scope
- **In-Scope**:
  - Replace the `uv run check-mcp-docs` / `uv run check-agent-docs` shorthand in `rules/toolchain.md` with the working module form `uv run python -m tools.check_docs_consistency --domain mcp` / `--domain agent`.
  - Remove the "console script `check-tool-descriptions`" / "console script `check-needs-confirmation`" caller mentions in `tools/TOOL_DESCRIPTIONS.md` so no document names a console-script entry point that cannot run.
- **Out-of-Scope**:
  - Any change to `pyproject.toml` (`[tool.setuptools.packages.find]`, `[project.scripts]`): `tools/` stays non-installable by owner decision.
  - Removing the `[project.scripts]` entries or rewriting any tool's behavior.
  - Editing documents beyond the two target files named in the issue.
- **Dependencies**: `N/A: none`
  - **Depends on**: N/A: none

## Background
`pyproject.toml` declares four console scripts whose entry points reference `tools.*` modules, but `[tool.setuptools.packages.find]` uses `where = ["scripts"]`, so the root-level `tools/` directory is not packaged and the installed entry points cannot import it. The documented shorthand commands therefore fail with `ModuleNotFoundError`, while the module and path forms work.

## Problem
`rules/toolchain.md` documents `uv run check-mcp-docs` and `uv run check-agent-docs` as runnable shorthand, and `tools/TOOL_DESCRIPTIONS.md` lists `check-needs-confirmation` / `check-tool-descriptions` as console-script callers. Both names refer to entry points that cannot run in this repository, which contradicts the acceptance criterion that no document names a script that cannot run.

## Reason for Change
A documented command that fails erodes trust in the toolchain documentation. The owner has decided `tools/` is dev-only (not installable), so the fix is to stop documenting the broken console-script shorthand and point users at the working module form instead of changing packaging.

## Implementation Intent
Keep `tools/` non-installable. Rewrite the two documented shorthand/caller references so they use the `python -m tools.<name>` module form (verified working) or drop the un-runnable console-script name, and leave every tool's behavior and `pyproject.toml` untouched.

## Requirements
- `REQ-001`: `rules/toolchain.md`'s `uv run check-mcp-docs` / `uv run check-agent-docs` shorthand is replaced with the working module form `uv run python -m tools.check_docs_consistency --domain mcp` / `--domain agent`.
- `REQ-002`: `tools/TOOL_DESCRIPTIONS.md` no longer names `check-needs-confirmation` / `check-tool-descriptions` as runnable console scripts; the three documented invocation forms stay accurate.

## Implementation Target Files
**Freeze status**: Frozen.

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `rules/toolchain.md` | Modify | Replace the failing `check-mcp-docs` / `check-agent-docs` console-script shorthand with the working module form | REQ-001 / AC-001 | `python -m tools.check_docs_consistency --domain mcp --help` exits 0 with all domains; hyphenated console-script names are never invoked in `.pre-commit-config.yaml` or `.github/workflows/` (checked in Step 3) | N/A | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Remove the "console script `check-tool-descriptions`" / "console script `check-needs-confirmation`" caller mentions that name un-runnable entry points | REQ-002 / AC-002 | `.pre-commit-config.yaml` and `.github/workflows/governance-docs-consistency.yml` invoke these tools via the module/path form only; no workflow references the hyphenated entry-point names (checked in Step 3) | N/A | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `pyproject.toml` | Confirm `[tool.setuptools.packages.find] where = ["scripts"]` and the four `[project.scripts]` entries; establish that `tools/` is not installable | Basis for Option C (no packaging change) — REQ-001/REQ-002 |
| `.pre-commit-config.yaml` | Confirm the real caller invocation form (`python -m tools.check_tool_descriptions_sync`) | Real-caller evidence for `tools/TOOL_DESCRIPTIONS.md` — REQ-002 |
| `.github/workflows/governance-docs-consistency.yml` | Confirm CI invokes `check_needs_confirmation_inventory.py` via the path form | Real-caller evidence for `tools/TOOL_DESCRIPTIONS.md` — REQ-002 |

## Acceptance Criteria
- `AC-001` (REQ-001): No `uv run check-mcp-docs` or `uv run check-agent-docs` shorthand remains in `rules/toolchain.md`; the per-domain checker is documented via the module form.
- `AC-002` (REQ-002): `tools/TOOL_DESCRIPTIONS.md` no longer names `check-needs-confirmation` / `check-tool-descriptions` as runnable console scripts, and the three invocation forms (module, path, test import) remain accurate.
- `AC-003` (REQ-001/REQ-002): `pyproject.toml` is unchanged and both `python tools/<name>.py` and `python -m tools.<name>` still work.

## Tests
- Run `uv run python tools/check_docs_consistency.py --domain mcp` (or `--domain agent`) after the edit to confirm the documented module form still runs.
- Run `uv run python tools/check_tool_descriptions_sync.py` to confirm `tools/TOOL_DESCRIPTIONS.md` still cross-checks cleanly after the caller-cell edit.

## Documentation Impact
N/A: this Plan edits only `rules/toolchain.md` and `tools/TOOL_DESCRIPTIONS.md` (both are rules/tools reference docs, not `docs/*.md`); no `docs/*.md` is generated or refreshed by this change.

## Assumptions
- The owner decision (recorded) treats `tools/` as dev-only and non-installable, so packaging is intentionally left as-is.
- The module form `python -m tools.check_docs_consistency` behaves identically to the path form `python tools/check_docs_consistency.py` for the same `--domain` value (both run the same module).
- The pre-commit hook and CI workflow already use the module/path form, so no caller needs updating.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether other documents name the hyphenated console-script entry points as runnable commands (the earlier scan found many `check-mcp-docs` mentions across the repo) | Full corpus scan of every doc for runnable invocations of the four entry-point names | Resolved by the documentation consistency checkers in the validation step; if other runnable invocations exist, they become fallout rows | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `rules/toolchain.md` | Modify | Low | N/A | N/A | None: `deploy.sh` does not ship or invoke these docs |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | N/A | N/A | None: editing a caller-description cell does not change tool behavior or the build |

## Design
N/A: Path A. No architecture, dependency graphing, or historical analysis. The change is a scoped prose edit to two reference documents; the module-form invocation was verified working before planning.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Edit `rules/toolchain.md` (REQ-001; Implementation Target Files row 1)**
   - [ ] Replace the `uv run check-mcp-docs` / `uv run check-agent-docs` shorthand on the shorthand line with the module form `uv run python -m tools.check_docs_consistency --domain mcp` / `--domain agent`, preserving the `--skip` / `main_mcp()` / `main_agent()` context.
2. **Phase 2: Edit `tools/TOOL_DESCRIPTIONS.md` (REQ-002; Implementation Target Files row 2)**
   - [ ] Remove the "console script `check-tool-descriptions`" mention in the `check_tool_descriptions_sync.py` caller cell, keeping the pre-commit hook caller.
   - [ ] Remove the "console script `check-needs-confirmation`" mention in the `check_needs_confirmation_inventory.py` caller cell, keeping the `governance-docs-consistency.yml` caller.
3. **Phase 3: Validate (AC-001/AC-002/AC-003)**
   - [ ] Run the documentation consistency checkers and `check_tool_descriptions_sync.py` / `check_docs_consistency.py` to confirm the documented forms still run and the file cross-checks cleanly.

### Release units
N/A: no release unit

## Validation plan
N/A: the validation plan lives in the implementation procedure (`skills/code-implementation/workflow.md` reads the procedure's plan, not this Plan's).

## Risks
- **Risk**: Rewording the `tools/TOOL_DESCRIPTIONS.md` caller cells could introduce a backtick-quoted `.py` name that `check_tool_descriptions_sync.py` flags as an unindexed tool. → **Mitigation**: drop the console-script names without adding new concrete `.py` references, and re-run `check_tool_descriptions_sync.py` after the edit.
- **Risk**: Removing the "console script" caller wording loses historical caller information. → **Mitigation**: keep the pre-commit hook and CI workflow caller names in each cell; only the un-runnable entry-point reference is removed.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`. Default rows for a freshly generated Plan (replace with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `rules/toolchain.md` shorthand to module form (REQ-001) | In Progress | — | — |  |
| 2 | Edit `tools/TOOL_DESCRIPTIONS.md` caller cells (REQ-002) | In Progress | — | — |  |
| 3 | Validate documented forms still run (AC-001/AC-002/AC-003) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261107-180341_01_rules_toolchain.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261107-180341_02_tools_TOOL_DESCRIPTIONS.md.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-123523_consolescript001_console-scripts-cannot-import-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-174449
- **Related target files**: `rules/toolchain.md`, `tools/TOOL_DESCRIPTIONS.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261107-180341 -->
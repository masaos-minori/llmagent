## Goal
Document the private helper and the currently supported invocation forms in `tools/TOOL_DESCRIPTIONS.md`, and run the Plan's final verification (`REQ-006`; Plan phase 5).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one Index row, one shared-base detail row, and a short invocation-forms and migration-status note in this file.
- Out of scope: any convention text (owned by the `toolcli001` Plan), report-model rows (`toolreport001`), atomic-write rows (`toolwrite001`), size-gate rows (`toolsizegate001`), converting callers to one invocation form (owner decision UNK-01).

## Assumptions
- Verified on 2026-11-06 (Step 3a): the Index table lists the private modules `_adr_authority_core.py`, `_docs_consistency_lib.py`, `_front_matter_schema.py` with category `Shared base`, and a detail row with "(shared base; cannot run standalone)" exists for `_docs_consistency_lib.py` and `_front_matter_schema.py`; `_contract_manifests.py` is listed as `(private helper; cannot run standalone)` in the reference-generators table. The file has no invocation-forms section and no CLI and exit-code convention section yet.
- Needs confirmation (non-blocking): the archived `toolcli001` Plan would add the convention section, but its procedures were archived with every step `Pending`. Write the note without a link or reference to a convention section; if that section exists when this procedure runs, the owner decides whether to cross-reference it.
- Overlap judgment: four Frozen Plans target this file (`toolsdocsync001` is archived and implemented; `toolcli001`, `toolreport001`, `toolwrite001`, `toolsizegate001` add other rows or sections). This Plan's sections are the Index/detail rows for `_tool_common.py` and one new subsection, different from the others, so they are compatible, with this Plan landing first.
- Facts for the note (verified in Step 3a): the module-form `uv run python -m tools.<name>` is what `.pre-commit-config.yaml` uses; the by-path form `python tools/<name>.py` is what the CI workflows, skills, and docs use; `python3 "${REPO_ROOT}/tools/manage_binaries.py"` is used by `deploy/deploy.sh`, `deploy/build_binaries.sh`, and `deploy/start_agent.sh`; tests import `tools.<name>`.

## Design decisions
- Name the migrated tools in a list rather than stating counts, so the note stays correct as tools change.
- State the migration status as facts only (which tools use the helper, that the guarded `sys.path` bootstrap remains temporarily in them, that the standard invocation form is not decided).

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Add to the Index table, after `_front_matter_schema.py`, a row for `_tool_common.py` with category `Shared base` and the purpose: repository root, one `git` runner (UTF-8 text mode with replacement or bytes mode, optional `check` and `timeout`), and the exit-code constants.
2. Add a detail row next to the `_front_matter_schema.py` row with "(shared base; cannot run standalone)": the three exports, the stdlib-only constraint (it must import under the system `python3` that `deploy/*.sh` uses), and that exceptions propagate to the caller.
3. Add a short subsection (for example `## Invocation forms`) listing the supported forms above and the migration status: `check_adr_preservation.py`, `check_workitem_traceability.py`, `classify_changes.py`, `manage_binaries.py`, `module_nodes.py`, `rename_doc.py`, `run_validation_gates.py`, and `scan_change_consumers.py` use `tools/_tool_common.py`; a file without the repository's guarded bootstrap gained it so by-path runs can import the helper, and the follow-up Plans remove the bootstraps after the owner decides the standard form.
4. Run the Plan phase 5 verification after all tool procedures have landed (see Validation plan).

### Method
- Keep the existing table column order and the file's sentence style; one row per file in the Index.

### Details
- `tools/check_tool_descriptions_sync.py` cross-checks `tools/*.py` against backticked `*.py` names here: backtick every filename above exactly as the file is named.

## Compatibility considerations
- N/A: documentation only; no behavior changes.

## Security considerations
- N/A: no secrets, hosts, or ports are written.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — expected `No issues found.` once `tools/_tool_common.py` exists and is documented.
- Final verification for the Plan (after all procedures of this Plan are executed): `uv run pytest tests/tools -q`; `uv run python tools/run_validation_gates.py`; `rg -n "subprocess.run" ` over the eight migrated tools (only the non-git gate runner in `tools/run_validation_gates.py` may remain); the by-path and `-m` smoke from each procedure; `python3 tools/manage_binaries.py --help`; and the before-and-after live-data comparison recorded per procedure.
- `uv run python tools/check_mock_patch_targets.py` and `uv run python tools/check_suppression_justification.py`.
- Deployment: no `scripts/` or `config/` change; `tools/manage_binaries.py` runs on the deploy path, so deploying after commit and push is the user's separate decision (`skills/deploy/SKILL.md`).

## Completion criteria
- The Index and detail rows exist, the invocation-forms note states the supported forms and the migration status without counts, and `check_tool_descriptions_sync.py` reports no issue.
- The final verification list above has been run and its results recorded in the final report.

## Out of Scope
- Convention text, the other Plans' rows, changing any caller's invocation form, deploying.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Index row, the detail row, and the invocation-forms note | Completed | 20261106-095335 | 20261106-100339 | Changed: tools/TOOL_DESCRIPTIONS.md (Index row, detail row, Invocation forms section) |
| 2 | Run `check_tool_descriptions_sync.py` | Completed | 20261106-100339 | 20261106-100339 | check_tool_descriptions_sync passes |
| 3 | Run the Plan's final verification list (Validation plan) | Completed | 20261106-100339 | 20261106-100339 | full suite 11680 passed; tests/tools green; gates show only known findings; AC-2 rg clean; diff-cover N/A (tools/ outside coverage scope) |

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
- **Requirement ID**: `REQ-006` (document the helper and invocation forms), `REQ-005` (final invocation smoke)
- **Source issue**: issues/20261104-152002_toolcommon001_shared-helper-for-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105811_toolcommon001_shared-helper-for-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-090444
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`

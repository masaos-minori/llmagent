## Goal
Make `tools/check_workitem_structure.py` judge companion documents against their own templates: resolve their kind by filename, load their template headings, include them in discovery, and accept the two new kinds in `--kind` (`REQ-001`, `REQ-002`, `REQ-003`; `REQ-004`: stay within the size gate).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `load_template_specs`, `infer_kind`, `discover_documents`, the `--kind` choices and default set, and the docstring and help text.
- Companion kinds receive only the missing-section rule: no leftover, release-unit, status-value, or length rule (the `if kind == ...` branches in `collect_findings` and `collect_single_file_findings` already skip them).

## Assumptions
- `tools/_workitem_companion_kinds.py` exists from the `seq` 01 procedure and exports `COMPANION_TEMPLATES` and `companion_kind`; this document relies on it (an earlier-`seq` sibling, resolved by `stale_detector.py`).
- `--kind issue` meaning ordinary Issues only is acceptable: no caller passes `--kind issue` (`rg` over `tools/`, `skills/`, `rules/`, `.pre-commit-config.yaml` found none, checked in Step 3a); callers use `--file` or the default scan.
- The checker is 23,930 B against the 24,576 B gate with no baseline entry (checked in Step 3a); the edit must add fewer than 646 B net.
- Legacy archived companions fail their own current template (26 of 32); `--include-done` reporting them matches the behavior for other kinds' archives and is left as is (`UNK-03`).

## Design decisions
- `infer_kind` asks `companion_kind(rel_path)` first and falls back to the top-level directory map (`tools/check_workitem_structure.py:372`).
- `discover_documents` assigns each file of the `issues` directory to its companion kind when `companion_kind` matches, otherwise to `issue`, and keeps a file only when its resolved kind is selected (`:163`).

## Alternatives considered
Extending `_WORK_ITEM_KINDS` (`:119-124`) with filename patterns was rejected: the tuple is directory-keyed and the size gate leaves no room.

## Implementation
### Target file
`tools/check_workitem_structure.py`

### Procedure
1. Import `COMPANION_TEMPLATES` and `companion_kind` from `tools._workitem_companion_kinds`.
2. In `load_template_specs` (`:155`), after the existing loop, add one `TemplateSpec` per companion kind from `_extract_template_headings(ROOT_DIR / template)`.
3. In `infer_kind` (`:372`), return `companion_kind(rel_path)` when it is not `None`, else the existing directory lookup; keep the `None` result for paths outside the three directories.
4. In `discover_documents` (`:163`), iterate the `issues` directory when `issue` or any companion kind is selected; resolve each file's kind with `companion_kind` and keep it only if that kind is in `kinds`.
5. In `build_arg_parser` (`:499`), extend the `--kind` choices (`:521`) with the companion kinds and update the help text; in `main`, make the default kind set include them. Update the module docstring (the kinds, the templates, and `--kind issue` meaning ordinary Issues).

### Method
Keep every addition to a few lines; measure `wc -c tools/check_workitem_structure.py` after the edit and require at most 24,576. If the limit is exceeded, stop and report a Plan amendment for a second extracted module (`tools/amend_plan.py`); do not add a baseline entry.

### Details
- `--file` on `issues/{ts}_unknowns.md` must resolve to `unknowns` through `infer_kind` and report only missing headings of `templates/unknowns-issue.md`.
- `--include-done` and `--archived-status` behavior for the three existing kinds must not change; `--kind plan` and `--kind implementation` must still skip the `issues` directory.

## Compatibility considerations
Default scan and `--file` now judge companion documents by their own template; `--kind issue` no longer includes them (documented in the docstring and tool rows). Exit codes, output format, and the other flags are unchanged.

## Security considerations
N/A: read-only checker; no new I/O beyond reading two templates already in the repository.

## Rollback considerations
Revert the commit; the new module stays unused.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_structure.py -q` (the cases are in the `seq` 03 procedure).
- `wc -c tools/check_workitem_structure.py` at most 24,576; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.
- `uv run ruff format --check tools/check_workitem_structure.py`, `uv run ruff check tools/check_workitem_structure.py`, `uv run mypy tools/check_workitem_structure.py`, `uv run bandit tools/check_workitem_structure.py`.
- `uv run python tools/check_workitem_structure.py` exits 0 with only advisory findings; `uv run pre-commit run workitem-structure --all-files`.

## Completion criteria
- A companion scaffold from `generate_workitem.py --kind unknowns|risks` yields no finding, a companion missing a template heading is reported, and the three existing kinds behave as before.
- The size gate passes without a baseline entry.

## Out of Scope
- Leftover rules for companion documents; changing the hook regex; editing any companion document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Wire `load_template_specs`, `infer_kind`, `discover_documents`, `--kind`, and the docstring | Pending | — | — | |
| 2 | Add or update tests (carried by the `seq` 03 procedure) | Pending | — | — | |
| 3 | Run the size gate, ruff, mypy, bandit, the checker, and the hook | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: issues/20261125-091717_gate001_workitem-structure-companion-kinds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-102213_gate001_workitem-structure-companion-kinds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-104147
- **Related target files**: `tools/check_workitem_structure.py`

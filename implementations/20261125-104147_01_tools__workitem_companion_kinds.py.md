## Goal
Create the small module that owns the companion work-item kinds for the structure checker: the strict filename pattern and the template map for Unknown and Risk companion documents (`REQ-001`: kind detection by filename; `REQ-002`: headings from the companion templates; `REQ-004`: the logic stays out of the size-gated checker).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new module and nothing that imports it; wiring is the next procedure (`seq` 02), tests are `seq` 03.
- The module is read-only, has no I/O, and imports only `re` and `pathlib`.

## Assumptions
- Producer names are exactly `{timestamp}_unknowns.md`, `{timestamp}_{seq}_unknowns.md`, `{timestamp}_risks.md`, and `{timestamp}_{seq}_risks.md`; `{seq}` is an unvalidated `--seq` string, digits being the documented form (`tools/generate_workitem.py:245-261`, checked in Step 3a; the Plan was corrected from a fixed two-digit sequence to any digits).
- An ordinary Issue id always contains a letter (`skills/issue-creator/SKILL.md` Issue Filename Generation), so a digits-only segment never collides with `{timestamp}_{id}_{slug}.md`.
- The caller passes a repository-relative path, so the module does not depend on the checker's patched `ROOT_DIR`.

## Design decisions
- `companion_kind(rel_path)` takes a repository-relative `Path` and returns `"unknowns"`, `"risks"`, or `None`; it accepts `issues/<name>` and `issues/done/<name>` only.
- The filename pattern is anchored: `^\d{8}-\d{6}(?:_\d+)?_(unknowns|risks)\.md$`.
- `COMPANION_TEMPLATES` (new) maps each kind to its template path relative to the repository root, so the checker needs no per-kind code.

## Alternatives considered
Adding filename patterns to `_WORK_ITEM_KINDS` inside the checker was rejected: `tools/check_workitem_structure.py` is 23,930 B of the 24,576 B module-size gate, so the logic must live in a new module (`REQ-004`).

## Implementation
### Target file
`tools/_workitem_companion_kinds.py` (new)

### Procedure
1. Create `tools/_workitem_companion_kinds.py` with a module docstring that names the two kinds, the filename forms, and the consumer (`tools/check_workitem_structure.py`).
2. Define `COMPANION_TEMPLATES` (new): `{"unknowns": "templates/unknowns-issue.md", "risks": "templates/risks-issue.md"}`.
3. Define `_COMPANION_NAME_RE` (new) as above and `companion_kind` (new).

### Method
`companion_kind(rel_path: Path) -> str | None`: take `rel_path.parts`; return `None` unless the first part is `issues` and the path has either two parts or three parts whose middle part is `done`; match the last part with `_COMPANION_NAME_RE` (new); return the captured kind. Use `from __future__ import annotations` and full type hints (mypy runs over `tools/`).

### Details
- Accepted: `issues/20261125-091717_unknowns.md`, `issues/20261125-091717_02_risks.md`, `issues/done/20261125-091717_1_unknowns.md`.
- Rejected: `issues/20261125-091717_gate001_unknowns.md` (id with a letter), `plans/20261125-091717_unknowns.md` (wrong directory), `issues/x/20261125-091717_unknowns.md` (wrong depth), `issues/20261125-091717_unknowns.txt`, a non-numeric sequence.

## Compatibility considerations
New file with no importers until `seq` 02; no existing behavior changes.

## Security considerations
N/A: pure string matching on a repository path; no I/O.

## Rollback considerations
N/A: revert the commit; nothing else imports the module before `seq` 02.

## Validation plan
- `uv run ruff format tools/_workitem_companion_kinds.py` and `uv run ruff check tools/_workitem_companion_kinds.py`, `uv run mypy tools/_workitem_companion_kinds.py`, `uv run bandit tools/_workitem_companion_kinds.py` (`routing.md` Adding a new tool, items 1-3).
- `uv run pytest tests/tools/test_check_workitem_structure.py -q -k companion` after `seq` 03 adds the cases.
- `uv run python tools/check_tool_descriptions_sync.py` after `seq` 05 adds the row.

## Completion criteria
- The module exists, is lint, type, and bandit clean, and `companion_kind` (new) returns the documented result for every accepted and rejected form above.

## Out of Scope
- Leftover, release-unit, status, or length rules for companion documents; wiring into the checker; any change to `generate_workitem.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the module with `COMPANION_TEMPLATES` (new), the name pattern, and `companion_kind` (new) | Pending | — | — | |
| 2 | Add the detection tests (carried by the `seq` 03 procedure) | Pending | — | — | |
| 3 | Run ruff, mypy, bandit, and the companion tests | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (kind detection), `REQ-002` (template map), `REQ-004` (size gate)
- **Source issue**: issues/20261125-091717_gate001_workitem-structure-companion-kinds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-102213_gate001_workitem-structure-companion-kinds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-104147
- **Related target files**: `tools/_workitem_companion_kinds.py`

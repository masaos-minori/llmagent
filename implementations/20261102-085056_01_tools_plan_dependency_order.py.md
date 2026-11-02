## Goal
- Add a read-only tool that reads Plan dependency lines, builds the dependency graph of open Plans, detects cycles, prints a recommended order, and reports each open Plan as `ready` or `gated` with the blocking item (`REQ-001`, `REQ-002`).

## Scope
- In scope: the new module only (parsing, graph, cycles, order, readiness, text and JSON rendering, `main`). The unit tests are the row 02 document.
- Out of scope: deciding or changing any Plan's order, editing any Plan or procedure, network access.

## Assumptions
- Plan A1, A3, A4, A9: a dependency is a Plan or Issue path plus a phase; existing prose dependencies are read through the fallback with a warning; the tool recommends and the owner decides.
- Step 3a verified (2026-11-02): `tools/check_plan_target_overlaps.py` exposes `discover_plan_documents()` and `find_cross_plan_target_overlaps()`; the latter lists Frozen Plans only (`is_frozen`), so a Draft Plan's shared files are not reported as `overlap` notes. `tools/manage_workitem_stage.py` exposes `parse_execution_status_rows()` returning dicts keyed by the header columns. Tools import siblings as `from tools.<module> import ...` after a `sys.path` insert of the repository root (the `check_adr_authority.py` pattern).
- Step 3a verified: the live open Plans carry prose `Dependencies` lines only; none carries the structured line yet (the structured line is defined in row 05).
- Overlap (Step 2): no other Plan targets this new file.
- Sibling dependency: the structured line is documented in row 05 (`templates/plan.md`); this module is runnable and testable without it because the parser is driven by the line format stated here.

## Design decisions
- Pure functions over text and a root directory so tests need no live repository: `parse_dependencies(plan_text)` (new) is the only parser; `main()` does the I/O.
- Overlap data is reused, not re-derived: import `discover_plan_documents` and `find_cross_plan_target_overlaps` from `tools.check_plan_target_overlaps`; shared files are `overlap` notes only and never edges, because the tool may not infer an order the owner has not stated.
- A fallback dependency (a `plans/` or `issues/` path found in the free-text `Dependencies` bullet) gets phase `all`, a `prose-dependency` warning, and is labelled `gated (prose)` when open.

## Alternatives considered
- Inferring edges from shared target files: rejected (Plan Design), it would decide an order the owner has not stated.
- Reading dependencies from the `Source issue` link: rejected, several Plans share one Issue.
- A new `Status` value for gated Plans: out of scope, row 06 defines the `Notes` marker.

## Implementation
### Target file
`tools/plan_dependency_order.py` (new)

### Procedure
- Create the module with a docstring in the style of `tools/check_plan_target_overlaps.py` (purpose, read-only, usage, exit codes).
- Add `Dependency` (new) and `PlanNode` (new) frozen dataclasses, and the functions listed under Method.
- Wire `build_arg_parser()` (new) and `main(argv)` (new): options `--plan <path>` (report one Plan), `--format text|json`, `--root <dir>` (default the repository root, used by tests); output header states: `Recommended order only. The owner decides the order; this tool never reorders or edits a document.`
- Exit code: 0 on a completed run, including gated Plans, warnings, and cycles (report-only); 1 only for a missing `--plan` path or an unreadable `plans/` directory.

### Method
- `parse_dependencies(plan_text) -> tuple[list[Dependency], list[str]]` (new): scan the `## Scope` section. A bullet matching `^- \*\*Depends on\*\*:\s*(\S+)\s*\|\s*phase\s+(\S+)\s*\|\s*(.+)$` yields `Dependency(path, phase, reason, declared=True)`; `phase` is an integer or `all`. If no structured bullet exists, scan the `- **Dependencies**:` bullet for `(plans|issues)/[\w./-]+\.md` paths, each yielding `Dependency(path, "all", "prose", declared=False)` plus the warning `prose-dependency: {plan}: {path}`. `N/A: none` yields no dependency.
- `load_plans(root)` (new): the open Plans are `plans/*.md` (never `plans/done/`), each parsed to a `PlanNode(path, dependencies, targets, steps)`.
- `resolve_dependency(dep, root, plans)` (new) returns `closed`, `open`, or `unresolvable`: an Issue path under `issues/done/` or a Plan path under `plans/done/` is `closed`; an Issue still in `issues/` is `open`; a Plan still in `plans/` is `open` unless `phase` is an integer and that step's row in the Plan's `### Execution Status` (via `parse_execution_status_rows`) is `Completed`; a path found in neither location, or a phase row that cannot be matched, is `unresolvable` and reported as `Needs confirmation: {path} phase {phase}` (UNK-02).
- `find_cycles(nodes)` (new): depth-first search over declared edges between open Plans, returning each cycle as an ordered path list; report `cycle: a -> b -> a`.
- `recommended_order(nodes)` (new): Kahn topological order over declared edges to open Plans, ties broken by the Plan filename timestamp prefix; Plans in a cycle are appended last and flagged.
- `readiness(node, ...)` (new): `ready` when every dependency is `closed`; `gated` when any dependency is `open`, naming the first blocking `{path} phase {phase}` (and `gated (prose)` for a fallback dependency); `unresolvable` dependencies add a `Needs confirmation` line and do not by themselves gate.
- Render: order list, then `ready` and `gated` lists with the blocking item, then `overlap` notes, cycles, and warnings, in text or JSON.

### Details
- Read-only by construction: only `Path.read_text`/`glob`; no `open(..., "w")`, no `subprocess`, no sockets.
- The structured line grammar is `**Depends on**: {path} | phase {N or all} | {reason}`; the same text is the definition row 05 writes into the template.
- A depended-on Plan whose phase is an integer is matched by Execution Status `Step` number, which equals the Plan's `Implementation steps` numbering.

## Compatibility considerations
- New tool, no existing caller. Existing Plans without the structured line keep working through the fallback.
- Importing `tools.check_plan_target_overlaps` and `tools.manage_workitem_stage` couples this module to their public names (`discover_plan_documents`, `find_cross_plan_target_overlaps`, `parse_execution_status_rows`); the sibling Plans that edit `manage_workitem_stage.py` (flowimp002 and others) add functions and do not rename these.

## Security considerations
- Read-only, no network, no subprocess. Paths come from Plan text, so a dependency path is resolved only under `plans/`, `plans/done/`, `issues/`, and `issues/done/` of the root and rejected if it escapes the root (`Path.resolve()` prefix check). Bandit must stay clean on the file.

## Rollback considerations
- N/A: revert the commit; the tool writes nothing.

## Validation plan
- `uv run pytest tests/tools/test_plan_dependency_order.py -v` (row 02).
- `uv run ruff format tools/plan_dependency_order.py`; `uv run ruff check tools/plan_dependency_order.py --fix`, then `uv run ruff check tools/plan_dependency_order.py`; `uv run mypy tools/plan_dependency_order.py`; `uv run bandit tools/plan_dependency_order.py`.
- Live smoke run: `uv run python tools/plan_dependency_order.py`; review the order and `ready`/`gated` lists against the open Plans' stated dependencies and report the `prose-dependency` warnings it produces (UNK-01, AC-2).

## Completion criteria
- The tool prints a recommended order, `ready`/`gated` lists with the blocking path and phase, cycles, overlap notes, and warnings; the header states that the owner decides.
- The structured line and the prose fallback both parse, the fallback with a warning.
- The tool writes nothing; lint, type, and security checks are clean; the live smoke run completes and its output is reviewed.

## Out of Scope
- Tests (row 02), the order view (row 03), template and skill text (rows 05 to 08), registration (rows 09 to 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Implementation, including the live smoke run review |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests live in the row 02 document (`tests/tools/test_plan_dependency_order.py`); run them here |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Tool lint sequence of `routing.md` "Adding a new tool" |

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
- **Requirement ID**: REQ-001, REQ-002 (structured line with prose fallback; read-only graph, cycles, order, readiness)
- **Source issue**: issues/20261030-191144_flowimp003_plan-dependency-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080134_flowimp003_plan-dependency-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085056
- **Related target files**: tools/plan_dependency_order.py

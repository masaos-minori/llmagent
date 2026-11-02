## Goal
- Teach `tools/stale_detector.py` to resolve a flagged name or import against `(new)` declarations in earlier sibling procedures of the same Plan (`REQ-001`: resolve and report), apply the order rule with options (`REQ-002`: earlier `seq` only by default), and keep unmarked names and no-sibling documents unchanged (`REQ-003`: compatibility).

## Scope
- Modify only `tools/stale_detector.py`: sibling discovery, declaration extraction, order rule, two CLI options, informational output, and a warnings list. Blast radius is Medium: the tool runs in every procedure generation and execution, and four marking scripts import or call it.

## Assumptions
- A1: Step 3a: `StaleResult` has `is_stale`, `target_file`, and `mismatches`; `is_stale` drives `abort_execution`; `_check_symbol_refs` reports `symbol_missing` with detail `Symbol '<name>' not found in source`, `_check_import_refs` reports `import_missing` with detail `Import 'from <module> import <names>' not found in source`, and `_is_marked_new` decides the marker (verified by Read, 2026-11-02).
- A2: Step 3a: `tools/mark_procedure_new_symbols.py` runs this tool as a subprocess and matches `Symbol '<name>' not found in source` in stdout (Plan A9). The informational lines MUST NOT contain that phrase; a mismatch kept stale because of a later sibling MUST keep it as the start of its detail. The other importers (`tools/fix_procedure_new_markers.py`, `tools/mark_new_112317.py`, `tools/mark_new_115752.py`) only mention the marker or the tool (verified by `rg`).
- A3: `Source plan` is a required Traceability field. Siblings are matched by the basename of the Plan path, so `plans/<file>` and `plans/done/<file>` match (Plan A1). A value starting with `N/A` means no siblings.
- A4: The order source is the `seq` in the file name `{timestamp}_{seq}_{slug}.md` (Plan A2). A document whose own `seq` cannot be parsed gets no eligible sibling in the default rule and a warning; the accept-any rule still works.
- A5: Siblings are searched under `implementations/` and `implementations/done/` relative to `source_dir` (default: current directory, the repository root). Statuses are not read (Plan A3).
- A6: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): `tools/stale_detector.py` is also targeted by `plans/20261102-080828_flowimp009_test-row-grouping.md`. Judged a sequencing dependency, not a conflict: this Plan adds a sibling pass after the per-document checks, that Plan changes how the document's own target and companions are read first; whichever lands second rebases (Plan A8). Locate code by symbol name, not line number.
- A7: Dependencies in the shared pass: procedures `01` to `06` of this Plan are processed in `seq` order; this document is `seq` 01 and declares nothing for the others, so no name here depends on a sibling.

## Design decisions
- Sibling pass runs after the existing four checks, only for mismatches of type `symbol_missing` and `import_missing`; other mismatch types are untouched.
- New dataclass field `resolved` (default empty list) and `warnings` (default empty list) on `StaleResult`; `is_stale` and `abort_execution` depend only on `mismatches`, and `to_dict`/`from_dict` stay valid (the new keys are optional on read).
- `from_procedure` gains a keyword `sibling_mode` (new) with values `earlier` (default), `any`, `off`; the CLI maps `--sibling-order {earlier,any}` and `--no-siblings` onto it.
- Text only: names are collected with the same `_SYMBOL_RE` plus `_is_marked_new` rule and the same import regex (marker group), so there is one marker rule.

## Alternatives considered
- Order from the Plan phase order view of the flowimp003 Plan: rejected for this version (Plan A2); the `seq` source can be replaced later in one function.
- Treat any sibling as eligible by default: rejected; it would accept a name that a later row creates after the earlier row already needed it (UNK-02: shipped as an option).

## Implementation
### Target file
`tools/stale_detector.py`

### Procedure
1. Add module constants for the Source plan line, the file-name `seq` pattern, and the mismatch-name extraction (`_SOURCE_PLAN_RE` (new), `_SEQ_RE` (new), `_MISSING_NAME_RE` (new)).
2. Add `resolved` and `warnings` fields to `StaleResult`, and print them in `summary` (see Details).
3. Add helpers `_source_plan_basename` (new), `_procedure_seq` (new), `_find_siblings` (new), `_collect_new_declarations` (new), and `_resolve_from_siblings` (new).
4. Call `_resolve_from_siblings` (new) at the end of `StaleResult.from_procedure` (before returning the result of the checks) unless `sibling_mode` (new) is `off`.
5. Add `--sibling-order` and `--no-siblings` to `main`; print the active rule.
6. Extend the module docstring with one sentence on sibling resolution.

### Method
- `_source_plan_basename(text)`: search `_SOURCE_PLAN_RE` (new) on the Traceability line, strip backticks and spaces, return `None` for an empty or `N/A` value, else `Path(value).name`.
- `_procedure_seq(path)`: match `_SEQ_RE` (new) against `path.name` (`^\d{8}-\d{6}_(\d+)_`), return an int or `None`.
- `_find_siblings(source_dir, plan_name, self_path)`: list `*.md` under `implementations/` and `implementations/done/`, read each once, keep those whose Source plan basename equals `plan_name` and whose resolved path is not self_path; an `OSError` or `UnicodeDecodeError` appends a warning and skips that file.
- `_collect_new_declarations(text)`: return the set of names (`_SYMBOL_RE` match followed by `_is_marked_new`) and the set of `(module, names)` import pairs whose marker group is set.
- `_resolve_from_siblings` (new): for each mismatch of type `symbol_missing` or `import_missing`, extract the name or import pair from the detail; look for a declaring sibling among eligible ones (earlier `seq`, or all in `any` mode); if found, remove the mismatch, append `{name, document}` to `resolved`; if the name is declared only by an ineligible later sibling, keep the mismatch and append to its detail ` (declared (new) only by a later sibling: {document}; order rule: earlier)`. Recompute `is_stale` as `bool(mismatches)` after the pass.

### Details
- Summary layout when siblings are active: first line `Sibling resolution: order rule = {earlier|any}`, then one line per resolved name `resolved from sibling: {name} declared (new) in {document}` (the wording must not contain `not found in source`), then warnings as `warning: {text}`, then the existing stale or not-stale text. With `off` or without a `Source plan`, none of these lines is printed, so the output is byte-identical to the current output (REQ-003). Warnings print only when the pass ran.
- A declaration cycle (A uses a name B declares, B uses a name A declares) resolves only for the document with the later `seq`, because each document is checked against earlier siblings only; in `any` mode both resolve (documented behavior of the option).
- The same Plan file name appearing under both `plans/` and `plans/done/` is a warning, not an error (Plan Risks).
- Keep `from_procedure(proc_path, source_dir=None)` callable unchanged; the new keyword has a default.

## Compatibility considerations
- `StaleResult(is_stale=..., target_file=..., mismatches=...)` construction, `from_dict`, `to_dict`, `clean`, `stale`, and `merge` keep working; the new fields have defaults. `merge` should also extend `resolved` and `warnings` from the other result.
- CLI output is unchanged for documents without a `Source plan` or without siblings; exit code semantics are unchanged.
- Consumers: `tools/mark_procedure_new_symbols.py` keeps parsing stdout (A2); a name resolved from a sibling is not reported missing, so its `mark` command refuses it, which is intended.

## Security considerations
- N/A: local text-only reads of repository files, no network or execution; paths come from directory listings under `implementations/`, and file reads are bounded to those two directories.

## Rollback considerations
- N/A: revert the commit; `--no-siblings` restores the prior behavior without a revert.

## Validation plan
- `uv run pytest tests/tools/test_stale_detector.py tests/tools/test_mark_procedure_new_symbols.py -v`: all pass (the new cases are in `seq` 02, and the existing consumer suite runs unchanged).
- `uv run ruff format tools/stale_detector.py`, `uv run ruff check tools/stale_detector.py`, `uv run mypy tools/stale_detector.py`, `uv run bandit tools/stale_detector.py`: clean.
- Smoke run against live data: `uv run python tools/stale_detector.py implementations/{one of this Plan's procedures}` and one archived procedure of `dbmig001`, with and without `--no-siblings`; confirm the output is as designed.

## Completion criteria
- A name marked `(new)` only by an earlier sibling of the same Plan is reported as resolved and does not make the document stale (AC-1).
- A name declared only by a later sibling stays stale with the reason; `--sibling-order any` resolves it; the active rule is printed (AC-2).
- Documents without `Source plan` or siblings behave exactly as before; an unreadable sibling is a warning; a declaration cycle resolves only earlier to later (AC-3).
- Lint, type, and security checks are clean; the consumer suites pass unchanged.

## Out of Scope
- Checking that the declaring sibling actually creates the name; reading sibling statuses; the Plan phase order; changing how `(new)` is written; the one-off marking scripts; the companion-file reading of the flowimp009 Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add sibling discovery, declaration extraction, order rule, options, and output to `tools/stale_detector.py` | Completed | 20261102-130849 | 20261102-130849 | Files: tools/stale_detector.py. Step 2 stale check clean; Step 3a verified (A1/A2 by Read/rg), no correction needed. |
| 2 | Add the sibling test cases (procedure `02`) and keep the consumer suites unchanged | Completed | 20261102-130849 | 20261102-130849 | New sibling cases land in procedure 02; consumer suites (test_stale_detector, test_mark_procedure_new_symbols) pass unchanged: 111 passed. testmon-forceselect: 138 passed, 1 known pre-existing failure (test_mdq_health_posture). Full suite deferred to plan end. |
| 3 | Run lint, type, and security checks on `tools/stale_detector.py` (`rules/toolchain.md`, `routing.md` Adding a new tool) | Completed | 20261102-130849 | 20261102-130849 | ruff format/check, mypy tools/stale_detector.py, bandit clean; live smoke (scratch repo: earlier/any/--no-siblings) as designed. Full suite deferred to plan end. |
| 4 | Update the tool description (procedure `06`); no `docs/*.md` change | Completed | 20261102-130849 | 20261102-130849 | N/A: tool description is procedure 06; no docs/00_index.md task-scope row for tools/stale_detector.py |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20261030-191457_flowimp007_stale-sibling-new.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080513_flowimp007_stale-sibling-new.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085029
- **Related target files**: `tools/stale_detector.py`
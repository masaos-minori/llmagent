## Goal
- Add an explicit, repeatable `--companion` option to `tools/generate_workitem.py` for `--kind implementation-procedure` that scaffolds a document listing the target and its companions, each companion with its own procedure and validation lines (`REQ-005`: companion option; single-target scaffold unchanged).

## Scope
- Modify only `tools/generate_workitem.py`: the argument parser, validation in the procedure render path, a scaffold-completion helper, and the module docstring. `--all-rows` is unchanged and rejected together with `--companion` (out of scope in the Plan). Medium blast radius (the tool scaffolds every work item).

## Assumptions
- A1: Step 3a (verified by Read, 2026-11-02): `render_implementation_procedure` requires `--source-plan`, `--target-file-path`, and `--seq`, extracts the fenced skeleton with `extract_fenced_skeleton` (first `markdown` fence of the template), and names the file from the target path via `implementation_procedure_output_path`; the skeleton keeps the template placeholders (`{target_file_path}` in `Related target files`, an empty `### Target file`); `main` rejects `--target-file-path`/`--seq` with `--all-rows`.
- A2: Decision (Plan Design, A5): the scaffold is changed only when `--companion` is given. Without it the written text is byte-identical to the skeleton (AC-6). With it: the target path is written under `### Target file`, the `Related target files` placeholder line becomes the target first and then each companion (backticked, comma-separated), and the `### Companion test files` block is inserted after `### Details` with, per companion, a bullet and indented `Procedure:` and `Validation:` placeholder lines.
- A3: The block format is defined in the `seq` 03 template note; the generator builds it from a small helper, not from the template, because the fenced block (which `extract_fenced_skeleton` reads) deliberately does not contain the companion heading (the `seq` 03 procedure, A2). A test in seq 10 asserts the helper's heading equals the template note's heading so the two cannot drift.
- A4: Each companion path must lie under `tests/`, differ from the target and from every other companion; a violation is a `GenerationError` before any write. The tool does not verify that the paths are Plan rows (it only reads the Plan for the timestamp marker); the check for that is `tools/check_workitem_traceability.py --plan-coverage`.
- A5: Overlap judgment (Step 2, 2026-11-02): this file is targeted by no other active Plan. The `(new)` choice for a companion that does not exist yet is left to the author; the scaffold text says so.

## Design decisions
- `--companion` uses `action="append"`; `--seq` and `--target-file-path` stay required for the single-row path, so a document always has a primary target.
- The completion helper is a pure function `apply_companions` (new) over the skeleton text, so it is unit-testable without files.

## Alternatives considered
- Make `--all-rows` group rows automatically by `Related Tests`: rejected (Plan Out-of-Scope).

## Implementation
### Target file
`tools/generate_workitem.py`

### Procedure
1. Add `--companion` (repeatable, `action="append"`) to `build_arg_parser`.
2. In `render_implementation_procedure`, when companions are given, validate them (A4) and pass the skeleton through `apply_companions` (new) before returning it.
3. Add `apply_companions` (new) and `companion_block` (new).
4. In `main`, reject `--companion` with `--all-rows` and for any `--kind` other than `implementation-procedure`.
5. Extend the module docstring with one paragraph on `--companion`.

### Method
- `apply_companions(skeleton, target, companions)`: replace the first `### Target file\n` with that heading plus the backticked target; replace the first `{target_file_path}` placeholder with the comma-separated list; insert the block after `### Details\n`. Fail with `GenerationError` when an anchor is missing.
- `companion_block(companions)`: heading line `### Companion test files`, then per path a bullet with a backticked path and two indented lines `Procedure: {one line}` and `Validation: {one line}`; the first line after the heading is a short placeholder reminding the author to add `(new)` after a path that does not exist yet.
- Validation uses `_require` as the neighboring checks do.

### Details
- Output filename and pass-timestamp marker handling are unchanged (the name derives from the target).
- `--estimate-tokens` runs on the completed skeleton when companions are given.

## Compatibility considerations
- Without `--companion` nothing in the render path changes; the existing flags, `--all-rows`, and collision rejection behave as before.

## Security considerations
- N/A: no new inputs reach a shell; paths are validated strings written into a Markdown skeleton under the existing output directory.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_generate_workitem.py -v`: all pass (tests in seq 10).
- `uv run ruff format tools/generate_workitem.py`; `uv run ruff check tools/generate_workitem.py`; `uv run mypy tools/generate_workitem.py`; `uv run bandit tools/generate_workitem.py`: clean.
- Smoke test on live data: `uv run python tools/generate_workitem.py --kind implementation-procedure --source-plan {a live Plan} --target-file-path tools/example.py --seq 01 --companion tests/tools/test_example.py --estimate-tokens` (exits without writing) and the same call with a non-`tests/` companion (expected: rejected).

## Completion criteria
- The generator scaffolds a document with a target and companions, the single-target scaffold is byte-identical to before, invalid companions are rejected before any write (AC-6); the four tool checks are clean.

## Out of Scope
- `--all-rows` grouping, the template fenced block, and `tools/TOOL_DESCRIPTIONS.md` text (Plan UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `--companion` option, validation, and scaffold helpers; update the module docstring | Completed | 20261102-134321 | 20261102-134321 | added --companion, COMPANION_HEADING, companion_block, apply_companions, _validate_companions (extra helper), main rejection, docstring; changed: tools/generate_workitem.py; validation runs before the Plan marker write |
| 2 | Add or update tests per Validation plan (seq 10 procedure) | Completed | 20261102-134321 | 20261102-134321 | tests in seq 10 (43 passed) |
| 3 | Run the tool lint sequence (ruff format, ruff check, mypy, bandit) and the live-data smoke test | Completed | 20261102-134321 | 20261102-134321 | ruff format/check, mypy, bandit clean; smoke on a scratch copy of the Plan (a live Plan would receive the pass-timestamp marker): scaffold ok, non-tests companion rejected, --all-rows rejected; TOOL_DESCRIPTIONS out of scope (UNK-03); full suite deferred to plan end |

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
- **Requirement ID**: REQ-005 (generator companion option)
- **Source issue**: issues/20261030-191615_flowimp009_test-row-grouping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080828_flowimp009_test-row-grouping.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085649
- **Related target files**: `tools/generate_workitem.py`

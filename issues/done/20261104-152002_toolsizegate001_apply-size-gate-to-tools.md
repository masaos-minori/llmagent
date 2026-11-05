# Apply the module size gate to tools/ and split the largest tools

## Priority
Low

## Summary
Extend the module size gate to `tools/` with a grandfathering baseline, then split the two or three largest tools so they are reviewable.

## Background
Confirmed by repository evidence on 2026-11-04:

- `tools/check_module_size.py` measures only `.py` files under `scripts/` (`--scripts-dir`, default `scripts`) against 24576 B (raised from 20480 B on 2026-11-04), with a baseline file `tools/check_module_size_baseline.txt` as a ceiling; that baseline is now empty.
- 15 files directly under `tools/` exceed 24576 B (the original text said 14; corrected by adversarial verification on 2026-11-05; the 14th and 15th are `_adr_authority_core.py` at 25,689 B and `check_docs_structure.py` at 24,977 B). The largest are `manage_workitem_stage.py` (57,146 B, 1526 lines; its `build_parser` is 208 lines), `generate_reference_table.py` (42,997 B), `run_validation_gates.py` (42,591 B, 1264 lines), `check_canonical_source_conflicts.py` (41,349 B), and `stale_detector.py` (40,847 B).
- `routing.md` ties the size gate to `scripts/**/*.py` modules only.

## Problem
Tools have no size discipline, so the very files that gate and move workflow documents grow without review limits, and long functions such as `build_parser` are hard to test.

## Reason for Change
Maintainability only; no incident. Timing is flexible and the work is large, hence Low.

## Implementation Intent
Cover `tools/` with the same gate and a separate baseline so only new growth fails, then split the largest tools by responsibility (for example separating parser construction and subcommands in `manage_workitem_stage.py`) using the existing Path C split rules.

## Target Files or Areas
- `tools/check_module_size.py`, a new baseline file for `tools/`
- `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `routing.md`, `rules/toolchain.md` (gate scope text)
- `tools/manage_workitem_stage.py`, `tools/run_validation_gates.py` (first split candidates)

## Required Changes
- Let `check_module_size.py` accept `tools/` (second directory or separate invocation) with its own baseline of the 15 current violations.
- Wire the new invocation into pre-commit and CI and update the scope text in `routing.md` and toolchain docs.
- Split `manage_workitem_stage.py` and `run_validation_gates.py` in separate changes and tighten the baseline after each.

## Constraints
- Splitting follows the Path C rules and must keep CLI behavior and import paths used by pre-commit and CI.
- Existing violations are grandfathered; the baseline must only shrink.

## Acceptance Criteria
- A new oversized tool fails the gate; baselined tools fail only on growth.
- The gate runs in pre-commit and CI for `tools/`.
- After the splits, the two tools' baseline entries are removed or reduced and every existing test passes.

## Testing Expectations
- Unit tests for the multi-directory gate (new violation, growth, shrink, stale entry); `uv run pytest tests/tools -q`; the validation gates.

## Documentation Impact
Update the gate scope text in `routing.md` and `rules/toolchain.md`.

## Out of Scope
- Splitting the remaining 13 oversized tools.
- Changing the 24576 B limit for `scripts/`.

## Dependencies
- Depends on `issues/20261104-152002_toolstest001_add-tests-for-untested-tools.md` (tests before moving code) and benefits from `issues/20261104-152002_toolmypy001_add-tools-to-mypy-scope.md`.
- Coordinate with `issues/20261104-152002_toolcommon001_shared-helper-for-tools.md`, which touches the same files.

## Unresolved Questions
- Whether 24576 B is the right limit for tools: unknown.

## AI Implementation Instruction
Add the gate with a full baseline first so nothing turns red; split one tool per change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-152002
- **Related target files**: `tools/check_module_size.py`, `tools/check_module_size_baseline.txt`, `tools/manage_workitem_stage.py`, `tools/run_validation_gates.py`, `routing.md`

# Add batch issue generation from a spec to the work item generator

## Priority
Low

## Summary
`tools/generate_workitem.py --kind issue` creates one empty skeleton per call, so filing a set of issues from one source needs an ad hoc script. Add a spec-driven batch mode that allocates unique timestamps and creates the files safely.

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. Claims below were verified in this investigation by reading tool source, running `--help`, and `rg`, unless marked `Needs confirmation`.

## Problem
The tool creates one skeleton and fills no field (`Explicit in code`, `--help`: placeholder text only, reject-only on collision). When a consolidated list of 23 issues was filed from one source in this repository, the files were produced by a one-off generator outside the repository, with timestamps assigned in advance in one-second steps instead of the creation-time `date` that the skill describes (`Operationally observed`, this session). `tools/generate_workitem.py` is already over the `tools/` size gate and grandfathered in the baseline (`Explicit in code`).

## Reason for Change
- Batch filing is a recurring path (review findings, audit tasks, and refactoring proposals all produce several issues), and each use currently reinvents generation, naming checks, and collision checks.
- Ad hoc generators skip the exact-path absence check in both `issues/` and `issues/done/` unless the author reimplements it.
- The skill's single-issue loop (scaffold, fill, check) stays valid; the batch mode adds a supported path rather than replacing it.

## Implementation Intent
- A spec file lists issues with their field content; the tool creates each file from `templates/issue.md`, with a unique monotonic timestamp and a name validated against the naming convention.
- The tool keeps the reject-only collision rule, supports `--dry-run`, writes atomically, and runs the structure check on every created file.
- New code lives in a new module; `generate_workitem.py` does not grow.

## Target Files or Areas
- tools/generate_workitem.py (dispatch only; no growth)
- tools (new module for the batch mode)
- templates/issue.md (reference only)
- `skills/issue-creator/SKILL.md`
- skills/issue-creator/workflow.md (Step 10.2)
- `tools/TOOL_DESCRIPTIONS.md`
- `tests/tools/`

## Required Changes
- Decide the spec format (the choice is in Unresolved Questions) and document it in `tools/TOOL_DESCRIPTIONS.md`.
- Implement the batch mode in a new module with timestamp allocation, name validation, the absence check in both directories, `--dry-run`, and atomic writes.
- Run the structure and leftover check on every created file and report per-file results.
- Describe the batch path in `skills/issue-creator/workflow.md` Step 10.2 without changing the single-issue path.

## Constraints
- The tool MUST NOT invent field content; all content comes from the spec.
- `generate_workitem.py` is over the size gate; its baseline entry MUST NOT grow.
- Follow `routing.md` Tools, section "Adding a new tool", for every changed `tools/*.py`: ruff format and check, mypy, bandit, a smoke run against real repository data, and `tools/TOOL_DESCRIPTIONS.md` sync (`tools/check_tool_descriptions_sync.py`).
- Respect the `tools/` module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`): the baseline only shrinks, so a tool at or over the limit MUST NOT grow; put new logic in a new module instead.
- Follow the tool CLI conventions recorded in `tools/TOOL_DESCRIPTIONS.md`: exit codes `0` pass, `1` findings, `2` usage or environment error; `--dry-run` and atomic writes for tools that rewrite files.
- Follow the Current-Specification-Only policy: no aliases, shims, or history-style comments for removed behavior.
- Keep code comments, log text, and documentation in English; change only the Target Files and report any other needed file as a scope amendment.

## Acceptance Criteria
- A spec of several issues creates the matching files, none overwritten, with unique and increasing timestamps (test).
- A pre-existing path in `issues/` or `issues/done/` makes the tool refuse that file without writing it (test).
- `--dry-run` writes nothing, and `tools/check_module_size.py` (tools scope) passes.

## Testing Expectations
Unit tests under `tests/tools/` for allocation, collision refusal, dry-run, and the structure check call; smoke run in a scratch directory; ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. `tools/TOOL_DESCRIPTIONS.md` (spec format) and `skills/issue-creator/workflow.md` Step 10.2.

## Out of Scope
- Batch generation of plans or procedures.
- Posting issues to GitHub.

## Dependencies
- `issues/20261117-123330_wftool001_gate-workitem-structure.md` provides the multi-file structure and leftover check that the batch mode should call (soft dependency).
- `tools/TOOL_DESCRIPTIONS.md` is also edited by the other tooling issues of this batch; fix the order with the owner.

## Unresolved Questions
- The spec format (JSON, YAML, or Markdown with front matter) is `不明`.
- Whether the batch mode may fill the Traceability fields from the spec or must set them itself is `不明`.

## AI Implementation Instruction
- Present the spec format options with trade-offs and stop before implementing.
- Do not grow `generate_workitem.py`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123334
- **Related target files**: tools/generate_workitem.py (dispatch only; no growth); tools (new module for the batch mode); templates/issue.md (reference only); `skills/issue-creator/SKILL.md`; skills/issue-creator/workflow.md (Step 10.2); `tools/TOOL_DESCRIPTIONS.md`; `tests/tools/`

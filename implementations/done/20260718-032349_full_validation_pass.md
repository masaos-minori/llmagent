# Implementation: full validation pass for tool-source compatibility relabeling (plan step 8)

Source plan: `plans/20260717-130629_plan.md` (requirement `requires/done/20260717_10_require.md`),
Implementation step 8.

Cross-cutting slug, not tied to one file — this is the terminal verification step for this whole
requirement, run after items 2-7 (`tool_registry.py`, `tool_constants.py`, `config_dataclasses.py`,
`tool_executor_helpers.py`/`tool_policy.py`, the Unknown resolution, and the `docs/` sweep) have all
landed. Not to be confused with `implementations/20260717-202631_full_validation_pass.md`, which is
the terminal validation step for a **different** plan (`plans/20260717-123416_plan.md`, "Remove plugin
subsystem completely") — that is a stale filename match for this batch, flagged rather than reused,
since it validates an unrelated change set (plugin subsystem removal, not tool-source relabeling).

## Goal

Run the repo's standard validation sequence (`rules/toolchain.md`) after all of this requirement's
docstring/comment/documentation edits land, to confirm the change set is purely
documentation/comment-level (per this plan's Assumption 2 and Validation plan) and introduces zero new
test failures, lint errors, type errors, or import-boundary violations — since this requirement, unlike
requirements 04-09, is explicitly not supposed to alter runtime behavior.

## Scope

**In scope**
- Running the full standard validation sequence once items 2-7 of this plan have all been applied to
  real source (i.e., after the gate in `implementations/20260717-225949_requirements_04_09_landing_check.md`
  clears for requirements 04-07, and the `docs/` sweep from
  `implementations/20260718-032201_docs_tool_source_sweep.md` is applied).
- Confirming the change set touches only: module docstrings (`tool_registry.py`, `tool_constants.py`),
  one field comment (`config_dataclasses.py`), fallback-labeling code comments
  (`tool_executor_helpers.py`, `tool_policy.py`), and `docs/*.md` prose — no dataclass shape, function
  signature, or control-flow change attributable to *this* requirement (as opposed to requirements
  04-07's own logic changes, which are validated by their own test suites per those plans).

**Out of scope**
- Writing new tests for requirements 04-07's actual logic (their own plans' job).
- Fixing failures that originate from requirements 04-07's own migration logic, as opposed to failures
  introduced by this requirement's comment/doc edits — if the full suite fails, first determine which
  requirement's change set is responsible before attributing it here.

## Assumptions

1. This requirement's own Validation plan table (plan lines 75-80) already specifies the check list:
   manual code review (no runtime path treats static sources as primary), manual doc review (no stale
   authority claims), `uv run pytest -v` (no new failures), `uv run pre-commit run --all-files` (pass).
   This item expands that table to the full standard sequence from `rules/toolchain.md`, since
   "manual review" plus "full suite" alone omits ruff/mypy/lint-imports/bandit/diff-cover, which are
   this repo's standard gate per `rules/toolchain.md`'s Completion checklist and should not be skipped
   just because the plan's own table under-specifies them.
2. Per this plan's Assumption 2, this requirement is documentation/comment-only — so ruff/mypy/bandit/
   lint-imports are expected to pass **trivially** (no import, type, or security-relevant change);
   the primary signal from this step is the `check-mcp-docs` entry point (`rules/toolchain.md`,
   "MCP documentation consistency" section) and `diff-cover`/`pytest`, since those are the checks
   capable of catching a genuinely wrong doc/comment edit (e.g. a stale authority claim `check-mcp-docs`
   flags, or a docstring edit that accidentally broke a doctest-like example).
3. `uv run check-mcp-docs` (registered in `pyproject.toml` per `rules/toolchain.md`) explicitly checks
   "Routing authority language consistency" and "Tool count consistency against canonical frozensets"
   — both directly relevant to this requirement's subject matter (correcting stale routing-authority
   claims). This is the single most targeted automated check for this requirement's own goal and
   should be run and its output read, not merely invoked and ignored.

## Implementation

### Target file

N/A — this is a command-sequence verification item, not a source-file edit. It depends on all of
items 2-7 having landed in real source first (see companion docs
`implementations/20260717-230029_tool_registry.py.md`,
`implementations/20260717-230059_tool_constants.py.md`,
`implementations/20260717-230126_config_dataclasses.py.md`,
`implementations/20260717-230149_tool_executor_helpers_and_tool_policy_fallback_labeling.md`,
`implementations/20260717-230218_startup_static_fallback_unknown_resolution.md`,
`implementations/20260718-032201_docs_tool_source_sweep.md`).

### Procedure

1. Confirm items 2-7 have been applied to real source (not just described in the design docs above) —
   re-check with `git diff` / `git status` that `scripts/shared/tool_registry.py`,
   `scripts/shared/tool_constants.py`, `scripts/agent/config_dataclasses.py`,
   `scripts/shared/tool_executor_helpers.py`, `scripts/agent/tool_policy.py`, and the identified
   `docs/*.md` files actually changed.
2. Run the standard sequence from `rules/toolchain.md` in order: `ruff format`/`ruff check`, `mypy`,
   `lint-imports`, `ast-grep`, `bandit`, `pytest` (targeted then full), `diff-cover`, `pre-commit`.
3. Run `uv run check-mcp-docs` and read its output for the "Routing authority language consistency" and
   "Tool count consistency" checks specifically — these are the two checks this requirement's own doc
   sweep is meant to satisfy.
4. If any failure surfaces, classify it as attributable to this requirement's own edits (comment/doc
   text) vs. requirements 04-07's logic changes, before deciding who should fix it.

### Method

Shell command sequence, no code produced by this item itself; a pure verification pass over the
combined result of items 2-7.

### Details

Command sequence (paraphrased from `rules/toolchain.md`, adjusted to this requirement's expected
"trivial pass" outcome per Assumption 2):

```
uv run ruff format scripts/
uv run ruff check scripts/ --fix
uv run ruff check scripts/
uv run mypy scripts/
PYTHONPATH=scripts uv run lint-imports
ast-grep --pattern 'except: $$$' --lang python scripts/
uv run bandit -r scripts/ -c pyproject.toml
uv run pytest tests/test_tool_registry.py tests/test_tool_constants.py tests/test_config_dataclasses.py -v
uv run pytest -v
uv run coverage run -m pytest tests/
uv run coverage xml
uv run diff-cover coverage.xml --compare-branch=main --fail-under=90
uv run check-mcp-docs
uv run pre-commit run --all-files
```

- Targeted test files listed above are a best-effort guess based on this requirement's touched
  modules; confirm actual test filenames exist (`tests/test_tool_registry.py`,
  `tests/test_tool_constants.py`) before relying on them — `ls tests/ | grep -i tool_registry` /
  `grep -i tool_constants` at execution time.
- Expected outcome per Assumption 2: all checks pass with zero new findings, since this requirement's
  change set is comment/docstring/prose-only. Any ruff/mypy/bandit finding would indicate an
  out-of-scope code change slipped into this requirement's edits and should be reverted from this
  requirement's diff, not fixed in place (per the plan's own Out-of-scope: "Re-doing requirements
  04-09's actual migration work").

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/`, `uv run ruff check scripts/` | pass, zero new findings |
| Type check | `uv run mypy scripts/` | pass, no new regressions |
| Import boundary | `PYTHONPATH=scripts uv run lint-imports` | pass (docstring/comment edits cannot violate `.importlinter`, but run anyway per standard sequence) |
| Security scan | `uv run bandit -r scripts/ -c pyproject.toml` | pass, no high/medium findings |
| Full suite | `uv run pytest -v` | no new failures |
| Diff coverage | `uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | ≥ 90% on changed lines (mostly docstrings/comments, so likely trivially satisfied) |
| Doc consistency | `uv run check-mcp-docs` | passes; specifically confirms routing-authority language and tool-count consistency post-edit |
| Pre-commit | `uv run pre-commit run --all-files` | pass |

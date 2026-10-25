# Procedure: `tools/TOOL_DESCRIPTIONS.md`

Stage-2 output for Issue 20261024-105844 / Plan 20261025-090535. Source plan: `plans/20261025-090535_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md`. Frozen decisions are copied from the plan; this procedure does not re-decide any of them.

**Row:** 3 of 4, Type `Doc`, Path `tools/TOOL_DESCRIPTIONS.md`, Action `Update`, Size `S`, Depends on `tools/check_ci_results.py`

## File Scope

- One file, two coordinated edits: the `## Index` table row and a full description section for `tools/check_ci_results.py` (new).
- Content must match doc0001's shipped implementation exactly (exit codes, gh allowlist, `--max-annotations` default). If doc0001's implementation deviates, this file is updated to match the code, not the other way around.

## Pre-Change State

- `tools/TOOL_DESCRIPTIONS.md` line 15: `## Index (53 modules)`.
- Index table format confirmed: `| Path | Category | Purpose |` with entries like `| tools/check_test_deps.py | Validation | ... |` (line 19).
- `tools/check_ci_results.py` is not yet registered (confirmed: no reference in the file, Step 3a).

## Frozen Decisions (from the plan, copied not re-decided)

- Category for the new row: `Validation` (matches check_test_deps.py/check_workitem_structure.py siblings — plan Assumptions).
- The description must state the gh allowlist (REQ-003) and exit-code contract (REQ-006) because the tool's security contract is part of its operational identity.

## Implementation Procedure

1. Index edits:
   - Bump the header to `## Index (54 modules)`.
   - Add one table row in the Validation block (alphabetical position next to `check_test_deps.py`), Purpose column one line: "Fetch GitHub Actions CI results via the approved gh allowlist, group them, and report failed runs for the test-and-fix workflow."
2. Description section (placed in the file's per-tool section area, following the existing per-tool heading style):
   - Purpose: maps CI results to the `python-test-and-fix` workflow entry point (plan REQ-001 "report only" scope — explicitly say it does not read tests, diagnose, or generate plans).
   - Usage: `uv run python tools/check_ci_results.py [--max-annotations N]`; exit codes 0/1/2 (REQ-006).
   - gh allowlist summary (REQ-003): `gh run list`, `gh run list --failed`, `gh run view --comments`; forbidden: `gh run log`, `gh run view` without `--comments`, repo-override flags, list filters beyond `--failed`/`--per-page`.
   - Cross-reference: operational notes live in `rules/toolchain.md` (doc0004's section).
3. Drift guard: the count in `## Index (54 modules)` must equal the actual row count after the edit; `tools/stale_detector.py`'s TOOL_DESCRIPTIONS coverage checks are the automated confirmation.

## Validation Commands

```bash
uv run python tools/stale_detector.py implementations/20261025-100210_03_tools_TOOL_DESCRIPTIONS.md.md   # this doc
uv run python tools/stale_detector.py tools/check_ci_results.py                                          # after doc0001 lands: coverage of the new tool
```

Plus the repo rule: any `tools/` edit requires the applicable checker from `routing.md` (TOOL_DESCRIPTIONS↔tools drift) — the stale_detector coverage check above is that gate for this row.

## Risk & Impact

- Documentation only; zero runtime blast radius.
- Hidden coupling: stale_detector's orphan-entry and coverage checks fail if this registration lands while `tools/check_ci_results.py` does not exist — hence the plan's dependency (`tools/check_ci_results.py`) ordering.
- Deployment coupling: deploy.sh syncs `tools/` to the production /opt/llm tree wholesale (no per-file list to update — plan Phase 4), so no additional registration is needed anywhere else.

## Scope Decisions

- In: index row + description section only. Out: docs/ registration (docs/00_index mapping does not apply to a tools-only change), any reformatting of neighbouring entries.

## Definition of Done

- Index count matches actual rows; description section present and consistent with the shipped tool; stale_detector coverage checks green; no other file touched.

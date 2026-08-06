# Implementation: tools/check_suppression_justification.py (new) — Phase 3: automated enforcement mechanism

## Goal

Add a pre-commit-runnable check that fails when a `# noqa`, `# type: ignore`, or
`# nosec` comment lacks both a rule/error code and an em-dash-delimited justification, so
`rules/coding.md` §Suppression governance is enforced automatically instead of only by
convention.

## Scope

**In-Scope:**
- New module `tools/check_suppression_justification.py`, modeled on the existing
  `tools/check_no_compat.py` pattern (regex-based line scan + allowlist + CLI entry
  point).
- Detect three suppression comment kinds across `scripts/` and `tests/`:
  `# noqa` (optionally with a code, e.g. `# noqa: BLE001`), `# type: ignore` (optionally
  with `[code]`), `# nosec` (optionally with a code, e.g. `# nosec B603`).
- Require, uniformly across all three kinds: a rule/error code present, AND an
  em-dash (` — `) delimited justification following it.
- Baseline allowlist covering today's ≥330 pre-existing non-compliant lines (77
  `BLE001`/`PLC0415` noqa + 244 `type: ignore` + up to 14 `nosec`), following
  `check_no_compat.py`'s `DEFAULT_ALLOWLIST`/`--allowlist` pattern, so only new/modified
  violations fail the check.
- CLI entry point invoked as `python -m tools.check_suppression_justification` (matching
  `no-compat-stubs`'s `python -m tools.check_no_compat` invocation style — no
  `[project.scripts]` console-script entry needed per the plan's Deploy Impact analysis).

**Out-of-Scope:**
- Bulk-remediating the ≥330 pre-existing non-compliant lines — grandfathered via the
  baseline allowlist, not fixed by this tool.
- Enforcing anything beyond the three suppression comment kinds (`noqa`, `type: ignore`,
  `nosec`) — no new suppression-like patterns are added.
- Wiring into `tox.ini` — the plan explicitly keeps this a pre-commit-only check, not a
  `tox -e lint` addition.
- The `tests/tools/test_check_suppression_justification.py` test file itself — separate
  implementation procedure.
- The `.pre-commit-config.yaml` hook wiring — separate implementation procedure.

## Assumptions

- `tools/check_no_compat.py` is the confirmed structural precedent (per plan UNK-06):
  module-level `DEFAULT_ALLOWLIST: set[Path]`, `--allowlist <path>` CLI override,
  `check_*` functions taking `(content, filepath, allowlist)` and returning
  `list[str]` issue messages, `main()` returning an `int` exit code, `ROOT_DIR` resolved
  relative to the module's own path (`Path(__file__).resolve().parent.parent`, since
  `tools/` is one level below repo root, vs. `check_no_compat.py`'s
  `.parent.parent.parent` because it currently lives at
  `scripts/checks/check_no_compat.py`-style depth — confirm actual depth against the real
  `tools/check_no_compat.py` path at implementation time).
- Baseline allowlisting is per-line (or per-file, whichever `check_no_compat.py`'s actual
  granularity is) rather than diff-scoped — per plan Assumption 5, chosen because it
  matches this existing precedent; no diff-scoped pre-commit precedent exists in this
  repo.
- Multi-line/parenthesized-import noqa style already exists in the codebase, e.g.
  `scripts/agent/commands/cmd_config.py` line ~44:
  ```python
  from shared.config_loader import (  # noqa: PLC0415
      _BASE_CONFIG_FILES,
      ConfigLoader,
  )
  ```
  This line has a code but no em-dash justification — under the new rule it is a real
  violation (not a false positive), and per the plan's stated risk, must be covered by
  the baseline allowlist (as a legitimately-flagged pre-existing line), not special-cased
  as "not a violation."

## Design decisions

- Model the module directly on `check_no_compat.py`'s shape (allowlist set + regex checks
  + `main()` CLI) rather than inventing a new structure — minimizes review friction and
  reuses a working, understood pattern (per plan UNK-06 and Assumption 5).
- Apply one uniform justification rule (code + em-dash) across all three suppression
  kinds, rather than three different rules — per plan's stated risk: building the check
  to match `rules/coding.md`'s pre-fix asymmetric examples verbatim "would silently
  perpetuate the same gap the requirement is trying to close."
- Use a baseline allowlist (not diff-scoped enforcement) — per plan Assumption 5, this
  matches the one existing precedent in the repo and avoids introducing a second,
  inconsistent enforcement style.

## Alternatives considered

- Diff-scoped (changed-lines-only) enforcement via a mechanism similar to `diff-cover` —
  considered and rejected per plan Assumption 5: no diff-scoped pre-commit hook precedent
  exists in this repo (`diff-cover` is a separate, coverage-specific, manually/CI-run
  tool, not a pre-commit hook), whereas the allowlist approach has a direct, working
  precedent (`check_no_compat.py`).
- Per-suppression-kind distinct rules (e.g. keep `nosec` strict but `noqa`/`type: ignore`
  code-only) — rejected: this is exactly the asymmetry the plan identifies as UNK-05 and
  requires fixed, not preserved in the new tool.

## Implementation

### Target file
`tools/check_suppression_justification.py` (new)

### Procedure
1. Create the module with:
   - Three regex patterns (or one parameterized pattern applied three times) matching
     `# noqa`, `# type: ignore`, `# nosec` occurrences per line.
   - A classification function per match: has a code? has an em-dash after the code?
     Flag as an issue if either is missing.
   - A `DEFAULT_ALLOWLIST` (or baseline-file-based allowlist, per the plan's "specific
     line references or a generated baseline file" option) seeded with today's ≥330
     non-compliant lines.
   - A `main()` CLI accepting optional file args (default: scan `scripts/` and `tests/`)
     and an `--allowlist` override, returning nonzero exit on any non-allowlisted
     violation.
2. Do not implement yet — this is a document-only phase; the actual file creation happens
   at `prompts/03_implementation.md` time, consuming this procedure document.

### Method
New Python module, `argparse`-based CLI, `re`-based line scanning — consistent with
`check_no_compat.py`'s implementation approach (no new third-party dependency).

### Details
- Per plan Implementation Steps Phase 3, bullet 1 (verbatim intent): "Create
  `tools/check_suppression_justification.py`, modeled on `tools/check_no_compat.py`:
  detect `# noqa`, `# type: ignore`, `# nosec` comments across `scripts/` and `tests/`;
  require a rule/error code and an em-dash-delimited justification; include a
  `DEFAULT_ALLOWLIST`-equivalent baseline ... covering today's ≥330 pre-existing
  non-compliant lines so only new/modified violations fail the check."
- Baseline counts to seed the allowlist, per plan UNK-07 (resolved):
  - `rg -n "noqa: (BLE001|PLC0415)" scripts/ tests/ | grep -v "—" | wc -l` → 77
  - `rg -n "# type: ignore" scripts/ tests/ | grep -v "—" | wc -l` → 244 (all lack an
    em-dash)
  - `# nosec` → 9 files / 14 occurrences, mixed compliance
- Must be validated against `uv run pre-commit run check-suppression-justification
  --all-files` passing on the current baseline before the hook is enabled repo-wide (see
  the `.pre-commit-config.yaml` procedure and Phase 3's final checklist item).
- Rollback/incremental note: per plan Implementation Steps, Phase 3 is a distinct,
  independently reviewable step after Phase 1/2 land.

## Compatibility considerations

- New file, additive only; does not change any existing module's behavior or public
  contract. No import-linter boundary implications (pure `tools/`-local utility, same
  layer as `check_no_compat.py`).
- `deploy/deploy.sh` unaffected — confirmed by plan's Deploy Impact analysis
  (`grep -n "tools/" deploy/deploy.sh` → no matches; `tools/check_*.py` modules are never
  copied by `deploy.sh`).

## Security considerations

- Read-only static analysis tool (regex scan over source text); no execution of scanned
  file content, no subprocess invocation beyond the CLI's own entry point. No new attack
  surface.

## Rollback considerations

- Additive new file with no callers outside `.pre-commit-config.yaml`'s new hook entry —
  rollback is deleting the file and removing the hook entry (see the
  `.pre-commit-config.yaml` procedure); no migration or state to unwind.

## Validation plan

- `uv run pytest tests/tools/test_check_suppression_justification.py -v` — all cases
  (bare/partial/justified/allowlisted, all three suppression kinds) pass (see the
  separate test-file procedure for exact case list).
- `uv run pre-commit run check-suppression-justification --all-files` — passes against
  the allowlisted baseline; must be re-verified after any Phase 2 triage edits change
  `# noqa: BLE001` line content.
- `uv run mypy scripts/` is not directly applicable (module lives in `tools/`, outside
  `[tool.mypy] files = ["scripts/"]`) — confirm at implementation time whether `tools/`
  is separately type-checked (grep `pyproject.toml`'s `[tool.mypy]` `files` list) and
  align expectations accordingly; if not covered, note this as a pre-existing toolchain
  gap, not a new regression introduced by this file.

## Out of scope

- The test file itself — `implementations/` procedure for
  `tests/tools/test_check_suppression_justification.py`.
- `.pre-commit-config.yaml` wiring — separate `implementations/` procedure.
- BLE001 triage edits in `scripts/`/`tests/` files — separate `ble001-triage-batch`
  procedure.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260806-133908_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-135732
- Related target files: tools/check_suppression_justification.py

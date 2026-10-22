# Add expiring exceptions and a current-symbol check to the compatibility checker

## Priority
Medium

## Summary
Extend `tools/check_compat_shims.py` so that compatibility exceptions carry an owner, a reason, an expiration date, and a removal condition, and so that active documentation presenting a symbol that no longer exists in source as current behavior is detected.

## Background
`memo-issue.md` item M-02 asked for continuous removed-name checks, expiring exceptions, and current-symbol validation. Checked against the repository:
- The removed-name check already runs in CI: `.github/workflows/backward-compat-check.yml` runs `python tools/check_compat_shims.py --check-removed-names` with `set -euo pipefail` (so a finding fails the job) on pushes and pull requests that touch `scripts/**/*.py`, `docs/**/*.md`, `tests/**/*.py`, or the tool itself. The memo's "only with the flag" description does not hold for CI.
- Exceptions are still a static set, `DEFAULT_ALLOWLIST`, of file paths in the tool, with comments but no owner, expiration date, or removal condition; there is no manifest and expired exceptions cannot fail CI.
- The removed-name check matches a fixed set of names (`_REMOVED_NAME_PATTERNS`) and historical-context markers; it deliberately does not attempt the harder case of a name that still exists in source but is no longer the current production path, and it has no index of the symbols that currently exist, so a documentation example naming a deleted symbol is found only when its name was added to the pattern list beforehand. The earlier `read_json_file()` Glossary example was found by manual review, not by the tool.
- `tests/tools/test_check_compat_shims.py` holds the checker's regression tests.

## Problem
An allowlist entry never expires, so a temporary exception can stay forever, and a documentation reference to a deleted symbol is detected only if someone first thought of adding its name.

## Reason for Change
Compatibility leftovers are removed on the owner's schedule only if every exception is tracked with an owner and a deadline, and the Glossary-style staleness that already occurred should be caught mechanically.

## Implementation Intent
Add a small exception manifest read by the checker (fields: id, pattern or path, reason, owner, expiry date, removal condition, category compatibility / migration / fallback) and make an expired or incomplete entry a CI failure; migrate the existing `DEFAULT_ALLOWLIST` entries into it, or remove those no longer needed. Add a report-only first stage of the current-symbol check that compares backtick-quoted function or class references in `docs/*.md` with a symbol index built from `scripts/`, with an explicit allowance mechanism to control false positives; decide the blocking date once the corpus is clean.

## Target Files or Areas
- `tools/check_compat_shims.py` and `tests/tools/test_check_compat_shims.py`
- New exception manifest file (location to be decided; Unknown)
- `.github/workflows/backward-compat-check.yml`
- `tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_04_documentation-checks.md`
- `tools/check_docs_consistency.py` / `tools/_docs_consistency_lib.py` (function-reference check; reuse, do not duplicate)

## Required Changes
- Define the manifest schema and its validation (required fields, valid category, parseable date).
- Fail the check when an entry is expired or incomplete; migrate or delete each `DEFAULT_ALLOWLIST` path.
- Add the report-only current-symbol stage with false-positive controls and tests for stale-reference, valid-reference, and historical-context cases.
- Document the manifest, the new check, and the date for making the symbol stage blocking.

## Constraints
- New checks start at Warning and must not fail the existing corpus.
- Follow `routing.md` "Adding a new tool" validation for tool changes.
- Do not weaken the existing removed-name and pattern checks.

## Acceptance Criteria
- Every exception has a reason, owner, expiration date, and removal condition, and an expired exception fails the check.
- A documentation reference to a symbol absent from `scripts/` is reported as a Warning, and a stale example like the former Glossary one would be reported.
- Existing checker behavior and its tests are unchanged; new tests cover the manifest and the symbol check.
- `ruff`, `mypy` (explicit path), `bandit`, `check_tool_descriptions_sync.py`, and the documentation checkers pass.

## Testing Expectations
- Unit tests for manifest validation, expiry, and the symbol stage; a smoke run on live `docs/` and `scripts/`.
- `uv run pytest tests/tools/test_check_compat_shims.py -q`, then the full suite once.

## Documentation Impact
Yes. The checks description and the tool description list the manifest and the report-only symbol check.

## Out of Scope
- Removing the compatibility features themselves.
- Runtime telemetry and general documentation lint.
- Making the symbol check blocking in this change.

## Dependencies
- `tools/_docs_consistency_lib.py` and `tools/check_docs_consistency.py` were extended for anchors and new domains in the same period; re-read them first.
- Sibling-issue check: no open issue under `issues/` and no active plan under `plans/` touches `tools/check_compat_shims.py`.

## Unresolved Questions
- Where should the exception manifest live, and in which format? Unknown; the repository has no precedent beyond `config/documentation_canonical_sources.toml`.
- Who owns each current allowlist entry? Unknown.
- Should the symbol check reuse the existing function-reference check instead of a new index? To be decided during design.

## AI Implementation Instruction
Extend the existing tool; do not add a parallel script. Keep new findings at Warning. Stop and report if an allowlist entry has no identifiable owner instead of inventing one.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261022-124220
- **Related target files**: tools/check_compat_shims.py, tests/tools/test_check_compat_shims.py, .github/workflows/backward-compat-check.yml, tools/TOOL_DESCRIPTIONS.md, docs/00_governance/governance_04_documentation-checks.md

# Extend the compatibility checker with the leftover phrases found in the review

## Priority
Low

## Summary
Add the phrases that marked compatibility leftovers in the review to `tools/check_compat_shims.py`, with a test fixture for each, and trim the "historical context" marker set to what is still needed, so that a removed leftover cannot return unnoticed.

## Background
- Source: `memo-issue.md` item L-02 (consolidated version), re-checked against current source on 2026-11-10.
- `Explicit in code`: `tools/check_compat_shims.py` detects compatibility leftovers through the `COMPAT_PATTERNS` regex table, the `ADR_PROHIBITED_PATTERNS` table, removed-name patterns for documents, and a `_HISTORICAL_CONTEXT_MARKERS` set (for example "legacy", "historical", "removed", "resolved", and Japanese equivalents) that lets a historical note pass; per-file exemptions live in `tools/compat_exceptions.toml` as fixture-only entries with an owner and an expiry. Tests are in `tests/tools/test_check_compat_shims.py`.
- `Operationally observed` (run on 2026-11-10): `uv run python tools/check_compat_shims.py` reports "All checks passed", so none of the leftovers listed in `memo-issue.md` is currently blocked by it.
- `Explicit in code`: among the memo's phrases only "pre-migration gate" has a related pattern; "predates", "additive", "signature stability", "re-exported", "Precedent", "replaces the", "Extracted from", "Refactored", "user-approved", and "bypass" have none. Some phrases span two lines in the source (for example a docstring that says "mirroring ..." on one line and "... exactly" on the next), which a line-based regex does not match.
- `Operationally observed` (case-insensitive search on 2026-11-10, matches in `scripts/` / `docs/`): "predates" 1/1, "additive" 3/2, "signature stability" 3/0, "re-exported" 4/1, "pre-migration" 5/1, "replaces the" 6/10, "Precedent" 5/4, "Extracted from" 59/6, "bypass" 23/57. Several phrases (especially "bypass" and "replaces the") are ordinary words with legitimate uses, so a bare pattern will produce false positives; the matches of "Extracted from" and "Precedent" are the leftovers `issues/20261110-171040_rmcompat007_history-comment-sweep.md` removes.

## Problem
- Every leftover found in the review was found by reading code. Without new patterns, the same kinds of compatibility wording will return unnoticed, and a "historical context" marker set larger than necessary lets leftovers through.

## Reason for Change
- Manual review does not scale; the checker already runs in CI and in the pre-commit and validation gates, so extending it is the cheapest way to keep the cleanup from regressing. Low urgency: it only prevents recurrence.

## Implementation Intent
- Each kind of leftover found in the review fails the checker automatically, with patterns specific enough that ordinary words do not cause false positives.
- Keep the exemption mechanism fixture-only as it is; do not add a production-category allowlist.

## Target Files or Areas
- `tools/check_compat_shims.py`, `tools/compat_exceptions.toml`
- `tests/tools/test_check_compat_shims.py`
- `tools/TOOL_DESCRIPTIONS.md` (only if the tool's documented behavior changes)

## Required Changes
- Add patterns for the phrases in the memo list, scoped to the leftover meaning (for example "bypass" only in the "bypass build_db_config" sense), and handle phrases that span lines where needed.
- Add a test fixture for each added pattern that fails the checker, and a fixture that shows a legitimate use of an ordinary word passes.
- Review `_HISTORICAL_CONTEXT_MARKERS` and remove markers no longer needed.
- Update the tool description if its behavior changes.

## Constraints
- The checker must pass on the repository at the time this issue lands; patterns that match remaining text require the sweep issue to land first (see Dependencies).
- Do not widen exemptions in `tools/compat_exceptions.toml` to make new patterns pass (fixture-only policy).
- Changes to `tools/` follow the lighter validation sequence in `routing.md` Tools "Adding a new tool" (ruff, mypy, bandit, a smoke run on real repository data, `tools/check_tool_descriptions_sync.py`).
- `tools/check_compat_shims.py` is also read by `plans/20261110-095137_adrrev005_schema-fingerprint-unify.md` for a related change; coordinate edits.

## Acceptance Criteria
- Re-adding any of the removed leftover phrases (in the scoped meaning) to `scripts/` or `docs/` makes `uv run python tools/check_compat_shims.py` exit non-zero, shown by one test fixture per pattern.
- An ordinary use of "bypass" or "replaces the" outside the leftover meaning does not fail, shown by a test fixture.
- `uv run python tools/check_compat_shims.py` passes on the repository.
- `tests/tools/test_check_compat_shims.py` passes, and ruff, mypy, bandit, and `tools/check_tool_descriptions_sync.py` pass for the changed files.

## Testing Expectations
- Unit tests in `tests/tools/test_check_compat_shims.py` for each pattern (positive and negative) and for the trimmed marker set.
- Smoke run of the checker on the live repository (`routing.md` "Adding a new tool" step 4), recording the matches before and after the sweep issue.

## Documentation Impact
- Update `tools/TOOL_DESCRIPTIONS.md` only if behavior changes. Update `docs/00_governance/governance_04_documentation-checks.md` (GV-017) only if it enumerates the checked patterns; describe the intent of the check, not the pattern list.

## Out of Scope
- Removing the current matches (`issues/20261110-171040_rmcompat007_history-comment-sweep.md`).
- The documentation forbidden-pattern list and severity (`issues/20261109-113351_adrrev018_docs-checker-harden.md`).
- Changing the checker's exemption policy or CI wiring.

## Dependencies
- Depends on `issues/20261110-171040_rmcompat007_history-comment-sweep.md` (remaining matches must be gone before the patterns are enforced).
- Related: `issues/20261109-113351_adrrev018_docs-checker-harden.md` (docs forbidden patterns; decide which checker owns each pattern before implementing).
- Related: `plans/20261110-095137_adrrev005_schema-fingerprint-unify.md` (touches `tools/check_compat_shims.py`).

## Unresolved Questions
- `不明`: severity of the new patterns (blocking or warning) and whether they apply to `docs/` as well as `scripts/`; the same question is open for `issues/20261109-113351_adrrev018_docs-checker-harden.md`.
- `不明`: how to scope "bypass", "additive", and "replaces the" to avoid false positives; the measured match counts above show bare patterns are too broad, and the intended meaning of each phrase has to be fixed by the maintainer before patterns are written.
- `不明`: which checker owns each pattern when `issues/20261109-113351_adrrev018_docs-checker-harden.md` is decided (that issue's forbidden-pattern list is also open).
- `Needs confirmation`: which entries of `_HISTORICAL_CONTEXT_MARKERS` are still needed.

## AI Implementation Instruction
- Change only `tools/check_compat_shims.py`, `tools/compat_exceptions.toml` (only if unavoidable and fixture-only), its tests, and the tool description.
- Measure matches on the live repository before adding each pattern; stop and report if a pattern needs an exemption to pass.
- Do not edit the sources that currently match; that belongs to the sweep issue.
- Keep comments and log text in English.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261110-171157
- **Related target files**: `tools/check_compat_shims.py`, `tools/compat_exceptions.toml`, `tests/tools/test_check_compat_shims.py`

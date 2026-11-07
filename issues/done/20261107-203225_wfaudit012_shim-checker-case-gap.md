# Make compat-shim detection case-insensitive so adapter aliases are caught

## Priority
Low

## Summary
The compatibility-shim checker's patterns are case-sensitive, so capitalized shim markers — the adapter's "Backward-compatible" alias block and the `LEGACY_MARKER_TABLES` constant — sail through it. Fix the checker so the project's own shim-detection gate actually detects this domain's existing shims.

## Background
Code review evidence (Verified):
- The checker greps for markers such as lowercase "backward-compat" and `legacy_`-style names, without case-insensitive matching.
- `scripts/agent/workflow_engine_adapter.py` carries a section header and docstrings reading "Backward-compatible ..." — capitalized, with a hyphen — and zero production callers (filed as the dead-alias issue). The checker passes on that file.
- `scripts/agent/services/workflow_schema.py` defines `LEGACY_MARKER_TABLES` (uppercase `LEGACY_`), also unflagged.
- Related policy context: `issues/done/20261020-123232_compat007_track-compatibility-exceptions-and-obsolete-symbols-in-a-manifest-with-owner-and-expiry.md` (compat tracking expectations).

## Problem
The gate exists to catch leftover compatibility shims, but its current patterns miss the exact shims present in the workflow domain. A passing checker run gives false assurance.

## Reason for Change
Small tooling fix that directly enables the dead-alias cleanup to be verified: once the checker is case-insensitive, any alias that survives (or is re-added) is flagged, keeping the cleanup durable.

## Implementation Intent
Case-insensitive matching for the shim marker patterns in the checker, then a run against `scripts/` to inventory what the corrected checker newly flags. Existing intentional constructs that would newly trip (e.g. `LEGACY_MARKER_TABLES`, whose legacy-marker semantics are deliberate) get an explicit allow-list entry or rewording decision — flagged, reviewed, decided; not silently suppressed.

## Target Files or Areas
- tools/check_compat_shims.py
- scripts/agent/workflow_engine_adapter.py (flagged target, no change in this issue)
- scripts/agent/services/workflow_schema.py (flagged target, review only)

## Required Changes
- Make the marker patterns case-insensitive.
- Run the corrected checker over `scripts/` and record the newly flagged set.
- Decide per flagged symbol: allow-list entry with reason, rename, or hand-off to a cleanup issue.

## Constraints
- Do not auto-suppress newly flagged symbols; every flag must end in an explicit decision recorded in the checker config or the PR text.
- Keep checker runtime negligible (single pass over scripts).
- Do not change production code in this issue.

## Acceptance Criteria
- The corrected checker flags the adapter alias block and `LEGACY_MARKER_TABLES`.
- CI (or the standard validation sequence) passes with each flag disposition documented.

## Testing Expectations
- Checker unit test (if the tool has one) covering capitalized markers.
- Manual run output captured in the PR text as the flag inventory.

## Documentation Impact
If tool descriptions (`tools/TOOL_DESCRIPTIONS.md`) describe the checker's matching behavior, update the wording to case-insensitive. No product docs affected.

## Out of Scope
- Removing the flagged aliases (dead-alias issue).
- Renaming `LEGACY_MARKER_TABLES` unless the review decides to.
- Extending the checker with new pattern categories.

## Dependencies
- Pairs with `issues/20261107-203221_wfaudit008_dead-alias-test-patches.md`: land the checker fix first so post-cleanup runs prove the aliases stayed gone.

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
Change only the checker and its tests/config. Any newly flagged symbol gets a one-line disposition note in the PR text — allowed (with reason), renamed, or handed to a cleanup issue. Do not silence flags with pattern tweaks narrower than case-insensitivity.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203225
- **Related target files**: tools/check_compat_shims.py, scripts/agent/workflow_engine_adapter.py, scripts/agent/services/workflow_schema.py

## Adversarial Validation

Validated against current source on 2026-11-08 (issue-to-plan Step 2 cycle), including live checker runs.

- Case-sensitivity confirmed mechanically: `COMPAT_PATTERNS` matches are applied via `re.search(pattern, stripped)` with no flags (`tools/check_compat_shims.py:630-633`); the pattern `"backward-compatible keyword": r"backward-compatible"` (L95) does not match the capitalized section header "Backward-compatible public API" (`scripts/agent/workflow_engine_adapter.py:106`) or the four "Backward-compatible alias for ..." docstrings (L121,128,135,144). Live repro: `re.search(r"backward-compatible", "Backward-compatible ...")` -> False; with `re.IGNORECASE` -> True. — Evidence: `Verified by test` (live repro) — Confidence: High
- Live checker run confirms the pass: `uv run python tools/check_compat_shims.py scripts/agent/workflow_engine_adapter.py` and the same with `--check-removed-names` on both target files both print "All checks passed" at HEAD. — Evidence: `Verified by test` — Confidence: High
- `LEGACY_MARKER_TABLES` claim needs a mechanism correction: the constant is not covered by `COMPAT_PATTERNS` at all (no `LEGACY_`-shaped pattern exists there — confirmed by scan of the dict). The removed-names scan separately handles the marker table names via `_REMOVED_NAME_PATTERNS` (L447-449), and the checker comment at L128-133 states this placement is deliberate because `COMPAT_PATTERNS` has no historical-context exemption; the removed-names path applies case-insensitive `_HISTORICAL_CONTEXT_MARKERS` exemption (`legacy` in the frozenset, L345-347, applied at L494), which is why the constant line is not flagged there. The gap is that neither scan flags the capitalized constant name itself. — Evidence: `Verified by test` — Confidence: High
- CI wiring confirmed: `.github/workflows/backward-compat-check.yml:39` runs `check_compat_shims.py --check-removed-names --check-doc-symbols`, so any case-insensitivity fix must be validated against the whole repository to avoid a flood of new findings (docs contain legitimate capitalized "Backward" history prose). — Evidence: `Verified by test` — Confidence: High

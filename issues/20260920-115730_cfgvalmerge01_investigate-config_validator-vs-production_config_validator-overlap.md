# Investigate config_validator vs production_config_validator overlap

## Priority
Medium

## Summary
Investigate the actual scope difference between
`scripts/shared/config_validator.py`'s `RagConfigValidator` and
`scripts/shared/production_config_validator.py`'s
`ProductionConfigValidator`, document the boundary between them, and
determine whether consolidation is warranted or whether the two should
instead be more clearly distinguished (e.g. by naming) as intentionally
separate, complementary validators.

## Background
Direct reading (2026-09-20) of both files:
- `scripts/shared/config_validator.py` (79 lines) defines
  `RagConfigValidator`, whose `validate()` checks exactly two things against
  the RAG config section: whether `use_rrf` is disabled (a quality warning)
  and whether any removed semantic-cache key (`semantic_cache_max_size`,
  `semantic_cache_threshold`, `use_semantic_cache`) is still present (a
  migration error). It also defines the shared `ConfigValidationResult`
  dataclass (`errors`/`warnings`/`ok` property).
- `scripts/shared/production_config_validator.py` (340 lines) defines
  `ProductionConfigValidator`, whose `validate()` checks a much broader set
  of production-security concerns against the *entire* configuration:
  required strict-mode keys, tool safety-tier consistency, approval
  risk-floor rules, and valid top-level key membership derived from
  dataclass field introspection. It already imports `ConfigValidationResult`
  from `config_validator.py` (`from shared.config_validator import
  ConfigValidationResult`) — the two modules are not fully independent
  today.

Both validators are invoked together, not as alternatives, at the same call
sites: `scripts/agent/config_builders.py` calls `RagConfigValidator()`
(line 198, against the RAG config section specifically) and separately
`ProductionConfigValidator()` (line 484, against the full production
config); `scripts/agent/services/security_audit.py` calls only
`ProductionConfigValidator()` (line 142). Both are covered by their own
dedicated test files (`tests/shared/test_config_validator.py`,
`tests/shared/test_production_config_validator.py`), plus at least
`tests/agent/test_startup.py`,
`tests/integration/test_production_security_regression.py`,
`tests/shared/test_config_loader.py`, and
`tests/shared/test_shared_boundary_conditions.py` reference one or both.

Based on this reading, the two validators currently appear to serve
genuinely different, complementary scopes (RAG-section-specific quality/
migration checks vs. whole-config production-security checks) rather than
duplicating the same validation — but this is a preliminary read of both
files' top-level structure, not an exhaustive line-by-line comparison, and
does not rule out a narrower overlap (e.g. a check that conceptually
belongs in one file but was added to the other) or a naming-clarity problem
(two similarly-named "config validator" modules in the same directory being
mistaken for alternatives) that a full investigation should still surface.

## Problem
Not yet determined — this issue exists to investigate, not to fix a
pre-identified defect. The concrete question is whether the current split
between these two validators reflects an intentional design boundary that
should simply be documented and clarified, or an accidental duplication/
misplacement that should be consolidated.

## Reason for Change
Two similarly-named validator modules in the same directory
(`scripts/shared/`), one already depending on the other for a shared
dataclass, create a plausible risk of a future contributor adding a check
to the wrong one, or duplicating a check across both, without a clear
statement of which module owns which validation concern.

## Implementation Intent
Read both files in full (not only their top-level structure, already
summarized in Background), read every call site and its surrounding
context (why that call site needs RAG-specific vs. production-wide
validation), and read both test files' full coverage. Produce one of two
outcomes: (a) document the intentional boundary explicitly (e.g. a module
docstring update in each file cross-referencing the other and stating the
scope split, plus/or a `docs/*.md` note if a relevant document already
describes config validation architecture) if the investigation confirms
they are correctly separated; or (b) propose a specific consolidation or
rename if the investigation finds a genuine misplacement, naming confusion,
or duplicated check. Do not implement either outcome as part of this
issue's own scope — this issue produces the investigation findings and
recommendation; a follow-up issue/plan implements whichever outcome is
chosen, unless the finding is trivial enough to fold into the same
implementation cycle (judgment call for whoever picks this up).

## Target Files or Areas
- `scripts/shared/config_validator.py`
- `scripts/shared/production_config_validator.py`
- `scripts/agent/config_builders.py` (both call sites, lines ~198 and ~484)
- `scripts/agent/services/security_audit.py` (call site, line ~142)
- `tests/shared/test_config_validator.py`
- `tests/shared/test_production_config_validator.py`
- Unknown: whether any `docs/*.md` file already documents a config-
  validation architecture that should be updated with the investigation's
  findings — not confirmed in this issue.

## Required Changes
- Read both files in full, every call site, and both test files.
- Determine whether any check currently in one validator conceptually
  belongs in the other, or duplicates a check in the other.
- Document the conclusion: either the explicit boundary (module docstrings
  cross-referencing each other, or a `docs/*.md` update) or a specific,
  scoped consolidation/rename proposal.

## Constraints
Do not change either validator's runtime behavior as part of this
investigation issue itself — a behavior change (if warranted) is a
follow-up implementation, not this issue's own scope. Any proposed
consolidation must preserve every current call site's existing validation
coverage (RAG-section checks at `config_builders.py:198`, production checks
at `config_builders.py:484` and `security_audit.py:142`) — do not drop a
check as a side effect of reorganizing.

## Acceptance Criteria
- Both files, all identified call sites, and both test files have been
  read in full (not summarized from partial reads).
- A clear written conclusion exists: either "these are intentionally
  separate; boundary documented at {location}" or "these should be
  consolidated/renamed as follows: {specific proposal}".
- If consolidation is recommended, the proposal names the exact target
  structure (which module keeps which class/function, what either call
  site's import statement becomes) rather than a vague "merge them".

## Testing Expectations
Not required for this investigation issue itself (no code change). If a
follow-up implementation results from this issue's conclusion, that
follow-up's own testing expectations apply then (existing test suites for
both validators must continue to pass with no regression).

## Documentation Impact
If the investigation concludes the two validators are intentionally
separate, document the boundary (module docstring update at minimum, a
`docs/*.md` update if a relevant document exists — see Target Files or
Areas' Unknown item). If consolidation is recommended, documentation impact
is scoped by that follow-up's own plan, not resolved here.

## Out of Scope
- Implementing a consolidation or rename — this issue produces the
  investigation and recommendation only, per Implementation Intent.
- Any other `scripts/shared/*.py` file not named in Target Files or Areas.
- The documentation cross-file-duplication issues filed the same day
  (`docdup01tool`, `docdup01val`) — unrelated area, filed separately per
  Task Grouping (different validation strategy: code investigation here vs.
  documentation editing there).

## Dependencies
N/A: none. This issue is fully independent of the documentation-duplication
issues filed the same day.

## Unresolved Questions
Resolved during adversarial verification (2026-09-20): neither test file
documents the intended scope boundary. `tests/shared/test_config_validator.py`'s
module docstring ("Startup validator for RAG config cross-file consistency")
only restates `config_validator.py`'s own docstring — it does not
cross-reference `production_config_validator.py` or explain why the split
exists. `tests/shared/test_production_config_validator.py` has no module
docstring at all (its first line is `from __future__ import annotations`).
This confirms the full investigation this issue calls for (Implementation
Intent) still needs to happen — no shortcut answer exists in either test
file's docstring — but rules out spending investigation effort re-checking
this specific spot.

## AI Implementation Instruction
Read both source files and both test files in full before concluding
anything — the Background section above is based on a structural read (line
counts, class/method names, docstrings, call-site line numbers), not a
line-by-line review of every check's logic. Do not propose a consolidation
without first confirming, for each individual check in both files, which
call site needs it and why. If the investigation is inconclusive within a
reasonable effort bound, report the specific remaining question rather than
guessing at a recommendation.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-115730
- **Related target files**: scripts/shared/config_validator.py,
  scripts/shared/production_config_validator.py,
  scripts/agent/config_builders.py,
  scripts/agent/services/security_audit.py

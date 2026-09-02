# Wire the finalized Documentation Metadata schema into automated CI validation

## Priority
Medium

## Summary
Once `docmeta01` produces a machine-readable schema and `docmeta02` brings the document
corpus into compliance, extend `tools/check_docs_structure.py` (or add a narrowly-scoped new
checker) to validate every document's front matter against the schema — required fields, the
finalized `area` enum, the `status` enum, and any date-format field the schema defines — and
wire that check into CI so a future non-compliant document or a regression back to `category`
fails automatically instead of silently reappearing.

## Background
`tools/check_docs_structure.py` already performs partial front-matter validation
(`check_front_matter()` requires `title`/`area`/`tags`/`related` to be present, and can check
`area` against an expected value via `--area`), but it does not validate against a schema
file, does not enumerate allowed `area`/`status` values, and does not check any date-format
field. `docmeta01` will produce the schema this issue needs as input; `docmeta02` will bring
the corpus to a state where enabling stricter enum/schema validation will not immediately
generate a wall of pre-existing failures.

## Problem
Without CI enforcement, the consistency `docmeta01`/`docmeta02` establish is not durable — a
future document can reintroduce `category:`, use an area value outside the finalized enum, or
omit required fields, and nothing will catch it before merge.

## Reason for Change
Per `rules/ai-execution.md` Repository Tool Usage and this repository's general
"AGENTS.md Global Rule 9 — do not rely on manual review alone for what these already
automate" convention, a structural rule this well-defined (a fixed field set, a fixed enum)
should be automated, not left to reviewer memory.

## Implementation Intent
Extend the existing `tools/check_docs_structure.py` rather than duplicating its file-walking
and Front Matter parsing logic in a new script, unless the schema-validation logic is
substantial enough to warrant a dedicated module (decide during implementation). Reuse
`docmeta01`'s schema artifact as the single source of truth for required fields and enum
values — do not hand-duplicate the enum list a second time inside the checker.

## Target Files or Areas
- `tools/check_docs_structure.py` (extend `check_front_matter()`, or add a sibling function
  that loads and applies `docmeta01`'s schema artifact)
- `.github/workflows/governance-docs-consistency.yml` (or whichever existing workflow already
  runs `check_docs_structure.py` — confirm the exact workflow file at implementation time)
- `tools/TOOL_DESCRIPTIONS.md` (update if this issue changes `check_docs_structure.py`'s
  documented behavior materially, per `routing.md` Tools guidance)

## Required Changes
- Load `docmeta01`'s schema artifact (path decided in that issue) and validate each
  document's parsed front matter against it: required fields present, `area` value in the
  finalized enum, `status` value in its enum when present.
- Report violations using the same file-and-reason format `check_docs_structure.py` already
  uses for its other findings, so existing CI failure parsing (if any) keeps working.
- Wire the extended check into the CI workflow that already runs documentation checks, so it
  runs on every relevant pull request.
- Confirm the check runs cleanly (zero findings) against the post-`docmeta02` corpus before
  making it a blocking CI check — if `docmeta02` has not fully landed by the time this issue
  is implemented, land this issue's check in report-only (non-blocking) mode first.

## Constraints
- Do not re-implement JSON Schema validation from scratch if a suitable library is already a
  project dependency — check `pyproject.toml` first, per `rules/ai-execution.md` Repository
  Tool Usage; only add a new dependency if none is already available and the need is
  confirmed.
- Do not change `check_front_matter()`'s existing required-field tuple in a way that breaks
  its current `--area` single-file-expected-value usage (`docs → task mapping` callers may
  depend on that flag's current behavior).
- Do not block CI on this check before `docmeta02`'s migration has actually landed — sequence
  this issue's CI-blocking cutover after `docmeta02` is verified complete.

## Acceptance Criteria
- `check_docs_structure.py` (or its new sibling) validates front matter against `docmeta01`'s
  schema artifact, not a second hand-maintained copy of the field/enum list.
- Running the check against the full `docs/*.md docs/adr/*.md` corpus after `docmeta02` has
  landed reports zero findings.
- A deliberately introduced schema violation (e.g. a test fixture using `category:` instead
  of `area:`, or an `area` value outside the enum) is detected and reported by the check.
- The check is wired into the relevant CI workflow and runs on pull requests touching
  `docs/*.md` or `docs/adr/*.md`.

## Testing Expectations
Add or extend a test (likely under `tests/tools/` if such a directory exists for `tools/`
scripts, or a corresponding test file matching existing conventions for this tool) that
exercises the new schema-validation logic against both a compliant and a non-compliant fixture
front matter block. Run the full existing `check_docs_structure.py` test suite (if any) to
confirm no regression to its current required-field/`--area` behavior.

## Documentation Impact
Update `tools/TOOL_DESCRIPTIONS.md` if `check_docs_structure.py`'s behavior or CLI surface
changes materially, per `routing.md` Tools → "When to run which tool" convention.

## Out of Scope
- Deciding the schema or `area` enum — that is `docmeta01`'s scope.
- Migrating any individual document — that is `docmeta02`'s scope.
- Adding new metadata fields beyond what `docmeta01` finalizes (e.g. do not reintroduce
  `scope`/`audience`/`priority`/etc. as CI-validated fields).

## Dependencies
- Depends on `docmeta01` (schema artifact and finalized enum must exist before this issue can
  implement against them).
- Depends on `docmeta02` (corpus must be compliant before this issue's check can be made
  CI-blocking without generating a wall of pre-existing failures — see Constraints).
- N/A: no other open issue or plan currently targets `check_docs_structure.py`'s front-matter
  validation logic, confirmed by `grep -rl "check_front_matter" issues/ plans/` returning no
  matches at investigation time (aside from this issue and its two dependencies).

## Unresolved Questions
- Whether a JSON-Schema-validation library is already available in this project's
  dependencies, or needs to be added — check `pyproject.toml` at implementation time; not
  blocking (a hand-written equivalent check is an acceptable fallback if no library is
  available and adding one is not justified for this single use case).
- Exact CI workflow file to wire this into — `Unknown`, to be confirmed at implementation
  time by inspecting `.github/workflows/` for the workflow that currently invokes
  `check_docs_structure.py` or `check_docs_quality.py`.

## AI Implementation Instruction
Confirm `docmeta01` and `docmeta02` have both landed (their issues moved to `issues/done/`
and their target files updated) before starting implementation — do not implement against a
schema or corpus state that may still change. Reuse `docmeta01`'s schema artifact as the
single source of truth; do not hand-copy its enum values into `check_docs_structure.py`'s
source. If the post-`docmeta02` corpus is not fully clean when this issue is implemented,
land the check in report-only mode and say so explicitly in the final report rather than
silently making it blocking.

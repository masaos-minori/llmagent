# Detect code-fallback-vs-operational-value duplication in docs

## Priority
Medium

## Summary
Extend `tools/check_docs_content_policy.py` with a new check that flags a
design document restating a "code default vs. operational/production value"
comparison — a config-value duplication pattern the tool's current 15
categories do not detect, confirmed present in at least 3 `docs/*.md` files.

## Background
`skills/DESIGN.md`'s "No concrete configuration values" section
(`skills/DESIGN.md:188-196`) already prohibits copying concrete values from
`config/*.toml` into design documents, and `tools/check_docs_content_policy.py`
already implements 15 report-only checks for related implementation-detail
categories (see `tools/TOOL_DESCRIPTIONS.md`'s two entries for it). Running the
tool against the full `docs/` tree today (2026-09-20, 36 total warnings)
produces zero findings for three files independently confirmed (by direct
reading) to contain exactly the pattern this policy prohibits:
- `docs/03_rag_02_02_ingestion_pipeline-crawler.md`'s "2.1.1 Configuration
  Parameters" table (header `| Parameter | Code Fallback Value | Production
  Value (config/crawler.toml) |`, rows for `max_depth`/`max_pages`/
  `skip_nofollow`).
- `docs/03_rag_01_system_overview.md`'s "## Constraints" section (heading
  confirmed via `grep -n '^## '`, 2026-09-20 — corrects this issue's
  original "Operational Constraints" heading name, which does not exist in
  this file), header `| Constraint | Value | Source |`, rows for "Crawl
  Depth"/"Max Pages Per Site" explicitly stating "Operational value is 3...
  Differs from code fallback" / "Operational value is 200... Code fallback
  is 500". This section's own Note (immediately below the table) already
  states: "No empirical basis or trade-off analysis for these six
  constraint values is recorded in this repository's code, configuration
  files, or ADRs... If these values are tuned, verify the change against
  actual retrieval quality/performance" — the document's own author already
  flags this uncertainty, yet the values remain duplicated across 3 files
  with no automated check.
- `docs/03_rag_05_5-constraints-reference.md`'s "Crawl depth"/"Max crawl
  pages" rows (same comparison, restated a third time).

All three duplicate values already canonically owned by
`docs/03_rag_05_1-configuration-reference.md`'s own `1.1 config/crawler.toml`
table. `docs/03_rag_05_5-constraints-reference.md`'s own "Evidence" section
(line 34) documents a **past staleness incident**: "Previous versions stated
`config/agent.toml:43`, `max 6 hops`, and `max 500 pages`, but... actual
`config/crawler.toml` values are `max_depth=3` and `max_pages=200`" — direct,
already-occurred proof of the drift risk an automated check would catch on
recurrence.

## Problem
None of `check_docs_content_policy.py`'s 15 existing check functions match
either table shape above: `check_field_type_table` requires a `Field`/`Key`
header column paired with `Type`/`Default`; `check_config_file_inventory_table`
requires a bullet-list under a "Configuration Fields"/"Config Reference"
heading, not a table; `check_default_value_restatement` only matches
`` `x` defaults to `y` `` prose and explicitly skips any line starting with
`|` (a table row). No existing check inspects a `Parameter`/`Constraint` +
`Value` table's cell content for a code-default-vs-operational-value
comparison phrase.

## Reason for Change
The same category of documentation drift the tool's existing 15 checks
already guard against (implementation detail restated in a design document,
going stale the moment the underlying value changes) applies here, with a
concrete, already-realized staleness incident as evidence — not a
hypothetical risk.

## Implementation Intent
Add one new check function to `tools/check_docs_content_policy.py`, following
the exact `check_*(files: list[DocFile]) -> list[Issue]` signature, module-
level regex-constant, and `_is_guard_start`/`_is_guard_end` auto-generated-
block-exemption pattern the existing 15 checks already use — do not
introduce a different code style or a second detection module. Detect a
table row (or nearby prose) that names both a code-level default/fallback
value and a separate operational/production value for the same parameter —
match on column headers (`Code Fallback`, `Production Value`) or nearby
phrases (`code default`, `code fallback is`, `operational config uses`,
`operational value is`), conservatively (prefer missing an edge case over
flagging a legitimate single-value statement), consistent with
`check_default_value_restatement`'s existing conservatism (its rationale-
marker skip). Exempt `docs/03_rag_05_1-configuration-reference.md` explicitly
if a targeted check shows it would otherwise false-positive on its own
legitimate "code default; operational config uses" comparisons (see
Unresolved Questions) — do not assume this without verifying during
implementation.

## Target Files or Areas
- `tools/check_docs_content_policy.py`
- `tests/tools/test_check_docs_content_policy.py`
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Add a new regex constant (or constants) for the code-fallback-vs-
  operational-value comparison pattern.
- Add a new `check_*` function implementing the detection, wired into
  `main()`.
- Add unit tests: at least one positive case (the pattern is detected) and
  one negative case (a legitimate single-value statement, or a value stated
  without any fallback/operational comparison, is not flagged).
- Update `tools/TOOL_DESCRIPTIONS.md`'s two `check_docs_content_policy.py`
  entries (currently "15カテゴリ" with a full Japanese enumeration) to name
  the new category and update the count to 16.

## Constraints
Report-only (`WARNING` severity) — must not block CI, consistent with the
tool's existing operation (`docs/00_governance_04_documentation-checks.md`'s
Governance Verification Matrix entry for this tool is unaffected). Must not
produce a false positive against `docs/03_rag_05_1-configuration-reference.md`
itself, which legitimately documents code-default/operational-value pairs as
part of its role as the canonical configuration reference (see Unresolved
Questions). Must respect the existing `<!-- AUTO-GENERATED -->` guard
convention.

## Acceptance Criteria
- The new check function follows the `check_*(files: list[DocFile]) ->
  list[Issue]` signature and is wired into `main()`.
- Running the tool against current `docs/` content produces at least one new
  finding for each of the three confirmed files in Background.
- Running the tool against `docs/03_rag_05_1-configuration-reference.md`
  produces no new finding attributable to the new check.
- New unit tests pass; the full existing test suite (`uv run pytest
  tests/tools/test_check_docs_content_policy.py`) passes with no regression
  to its current test count.
- `tools/TOOL_DESCRIPTIONS.md`'s two entries are updated per Required
  Changes.

## Testing Expectations
Unit tests for the new check function (positive and negative cases) in
`tests/tools/test_check_docs_content_policy.py`, following the existing
`_doc()` fixture pattern in that file. Run
`uv run python tools/check_docs_content_policy.py` before and after the
change and diff the output to confirm the only new findings are the 3 (or
more) expected ones, with zero regressions to the current 36-warning
baseline.

## Documentation Impact
Update `tools/TOOL_DESCRIPTIONS.md` per Required Changes. No `docs/*.md`
file is edited by this issue — the companion issue (see Dependencies) owns
remediating the actual `docs/*.md` content this check newly detects.

## Out of Scope
- Editing any `docs/*.md` file to fix a finding this new check produces —
  tracked as a separate, dependent issue (see Dependencies).
- Adding detection for every configuration-value type named in the source
  request (`min_chunk`, `embed_retry`, `embed_workers`, cache limits,
  similarity thresholds, log paths) individually — this issue's narrow
  target is the specific code-fallback-vs-operational-value comparison
  pattern proven undetected; a plain single-value restatement without a
  fallback/operational comparison is a different, broader category not
  scoped here (see the companion issue's own Unresolved Questions for
  whether a further tool extension is warranted after its manual review).
- Modifying any of the existing 15 check functions' behavior.

## Dependencies
None block this issue — it can proceed independently. The companion
documentation-remediation issue (see `issues/` for a doc filed the same day
titled "Remove concrete configuration values from RAG design docs") depends
on this issue for full-corpus discovery and post-edit validation, though its
own 3 confirmed locations can be remediated without waiting for this issue
to land.

## Unresolved Questions
Whether `docs/03_rag_05_1-configuration-reference.md`'s own "1.4
`config/rag_pipeline_mcp_server.toml`" section — which itself states
comparisons like "`top_k_search` | `5` (code default; operational config
uses `20`)" — would trigger a false positive from the new check, given that
this file is the intended canonical destination other docs should point to
instead of restating the comparison themselves (the same precedent as
`docs/03_rag_05_4-error-handling-reference.md` being exempted from the
implementation-reference-duplication check in a prior, completed cycle). Not
blocking — verify and add an explicit exemption during implementation if the
false positive materializes, per Implementation Intent.

## AI Implementation Instruction
Follow the exact structural pattern of the existing 15 `check_*` functions
in `tools/check_docs_content_policy.py` (same signature, same
`_is_guard_start`/`_is_guard_end` handling, same `Issue` construction) — do
not introduce a different code style or module. Do not modify any existing
check function's behavior or regex. Do not touch any `docs/*.md` file. Keep
the new regex conservative (prefer a false negative over a false positive),
consistent with `check_default_value_restatement`'s existing rationale-
marker skip. Verify the Unresolved Questions concern against
`docs/03_rag_05_1-configuration-reference.md`'s actual current content before
finalizing the regex, not by assumption.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-102200
- **Related target files**: tools/check_docs_content_policy.py,
  tests/tools/test_check_docs_content_policy.py, tools/TOOL_DESCRIPTIONS.md

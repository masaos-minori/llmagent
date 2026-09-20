# Remove concrete configuration values from RAG design docs

## Priority
Medium

## Summary
Remove hand-restated configuration values and code-default-vs-operational-
value comparisons from RAG design documents, replacing each with a
description of the value's role and constraint plus a pointer to the
canonical configuration reference (and to an existing Needs-Confirmation
entry where the value's rationale is unconfirmed), instead of duplicating
the value itself.

## Background
`skills/DESIGN.md`'s "No concrete configuration values" section
(`skills/DESIGN.md:188-196`) already states: "Do not copy concrete values
from `config/*.toml`... into design documents — paths, hosts, ports,
timeouts, retry limits, thresholds... Describe the policy and its
consequences instead... and point to the owning configuration file for the
current operational value." Direct reading (2026-09-20) confirms at least 3
`docs/*.md` files violate this by restating values already canonically
owned by `docs/03_rag_05_1-configuration-reference.md`:
- `docs/03_rag_02_02_ingestion_pipeline-crawler.md`'s "2.1.1 Configuration
  Parameters" table (`max_depth`, `max_pages`, `skip_nofollow`, each with a
  "Code Fallback Value" and "Production Value" column).
- `docs/03_rag_01_system_overview.md`'s "## Constraints" section (heading
  confirmed via `grep -n '^## '`, 2026-09-20 — corrects this issue's
  original "Operational Constraints" heading name, which does not exist in
  this file), rows "Crawl Depth" and "Max Pages Per Site" (explicit
  code-vs-operational comparisons: "Operational value is 3... Differs from
  code fallback" / "Operational value is 200... Code fallback is 500") and
  rows "Chunk Size"/"Chunk Overlap" (single-value restatement, no explicit
  comparison, but still duplicating `config/chunk_splitter.toml`'s
  `min_chunk`/`max_chunk`/`chunk_overlap` values).
- `docs/03_rag_05_5-constraints-reference.md`'s "Crawl depth" and "Max crawl
  pages" rows (a third restatement of the same two values) — **and**, found
  during this adversarial verification pass (2026-09-20), the same file's
  "Chunk size range" and "Chunk overlap" rows, which restate
  `config/chunk_splitter.toml`'s `min_chunk`/`max_chunk`/`chunk_overlap`
  values a second time (the first being `docs/03_rag_05_1-configuration-reference.md`'s
  own canonical table) — this issue's original draft omitted these two rows
  from scope entirely, despite them being the exact same category of
  violation as the file's Crawl depth/Max crawl pages rows.

`docs/03_rag_05_5-constraints-reference.md`'s own "Evidence" section (line
34) documents a **past staleness incident**: earlier versions of that file
stated `config/agent.toml:43`, "max 6 hops", and "max 500 pages" as the
operational values — all since proven wrong; the actual current values are
`config/crawler.toml`'s `max_depth=3` and `max_pages=200`. This is direct,
already-realized evidence of the drift risk this issue addresses, not a
hypothetical concern.

Two of the underlying "why this specific value" questions are already
correctly tracked as Needs-Confirmation entries in
`docs/00_governance_03_issue-and-uncertainty-management.md`: **NC-034**
(`min_chunk`/`max_chunk`/`chunk_overlap` — "No rationale comment... no
explanation exists for why 40/500/50 were chosen") and **NC-035**
(`max_depth`/`max_pages` — "no explanation exists for why 3 and 200 were
chosen"). This issue does not need to create new NC entries for these two
value groups — only to ensure the 3 confirmed design-doc locations point to
NC-034/NC-035 for the rationale gap instead of silently restating the values
as fixed, self-contained facts.

## Problem
Restating a configuration value in more than one design document (a) goes
stale the moment the operational config or code default changes, since
nothing enforces agreement across the duplicate copies, and (b) has already
gone stale once in this exact corpus (see Background), yet the duplication
pattern remains present in 3 confirmed locations today.

## Reason for Change
Proven documentation drift risk (a past staleness incident already
occurred, not merely a theoretical one) and duplication across at least 3
files of values that have exactly one canonical owner
(`docs/03_rag_05_1-configuration-reference.md`).

## Implementation Intent
For each of the 3 confirmed locations, replace the restated value with (a)
a description of what the value controls and why it exists as a boundary
(per the source request's own before/after example: "crawl range needs an
upper bound to prevent unbounded growth in processing time, storage, and
external-site load; the current operational value is authoritative in
config") and (b) a pointer to `docs/03_rag_05_1-configuration-reference.md`
for the current value, plus a pointer to NC-034/NC-035 where the rationale
gap applies. Retain, per the source request's own exception list, any value
that is: a fixed value affecting protocol compatibility; related to DB
format or persisted-data compatibility; a security boundary; a threshold
that changes algorithm meaning; or a value whose design rationale is already
recorded — apply the same "point to the source, describe the role" pattern
`skills/DESIGN.md`'s existing policy already establishes, not a new scheme.
`docs/03_rag_05_1-configuration-reference.md` itself is the canonical
destination and is **not** a remediation target — same precedent as
`docs/03_rag_05_4-error-handling-reference.md` being exempted from the
implementation-reference-duplication cleanup in a prior, completed cycle.

## Target Files or Areas
- `docs/03_rag_02_02_ingestion_pipeline-crawler.md` — "2.1.1 Configuration
  Parameters" table (confirmed).
- `docs/03_rag_01_system_overview.md` — "## Constraints" section, rows for
  Crawl Depth/Max Pages Per Site/Chunk Size/Chunk Overlap (confirmed).
- `docs/03_rag_05_5-constraints-reference.md` — "Crawl depth"/"Max crawl
  pages" **and** "Chunk size range"/"Chunk overlap" rows (all 4 confirmed);
  this file's remaining rows — language-detection threshold, "Replication",
  `chunk_index` type constraint, `url`/`content` non-empty requirements,
  `lang`/`chunking_strategy` validation scope — read as
  architectural/algorithm/validation-level invariants rather than
  environment-config values, and are likely out of this issue's scope (see
  Unresolved Questions).
- Unknown: the broader `docs/` corpus. This issue's own manual review found
  3 confirmed files; the companion tool issue (see Dependencies) adds
  automated detection so a full-corpus sweep can confirm or rule out further
  locations (e.g. other `03_rag_05_*` reference docs, or non-RAG domains)
  not yet individually confirmed here.

## Required Changes
- Replace the 3 confirmed files' target locations (crawler.md's table;
  system_overview.md's 4 rows; constraints-reference.md's 4 rows — 2 more
  than this issue's original draft, see Background) with role-and-constraint
  prose plus a pointer to `docs/03_rag_05_1-configuration-reference.md`
  (and to NC-034/NC-035 where applicable), per Implementation Intent.
- Once the companion tool issue lands, run it across the full `docs/` tree
  and remediate any further RAG-domain finding it confirms.
- Do not create new Needs-Confirmation entries duplicating NC-034/NC-035.

## Constraints
Do not change any `config/*.toml` file or source code default value. Do not
remove or alter NC-034/NC-035's own content in
`docs/00_governance_03_issue-and-uncertainty-management.md` — only add a
pointer to them from the edited design docs. Do not edit
`docs/03_rag_05_1-configuration-reference.md`. Preserve every exception
category listed in Implementation Intent — this is not a blanket removal of
every numeric value from RAG docs.

## Acceptance Criteria
- None of the confirmed locations (crawler.md's table; system_overview.md's
  4 rows; constraints-reference.md's 4 rows) restate the config value as an
  isolated, duplicated fact; each states the value's role/constraint and
  points to `docs/03_rag_05_1-configuration-reference.md` for the current
  value.
- Every `max_depth`/`max_pages` location additionally points to NC-035, and
  every `min_chunk`/`max_chunk`/`chunk_overlap` location (confirmed in
  constraints-reference.md's "Chunk size range"/"Chunk overlap" rows, and in
  system_overview.md's "Chunk Size"/"Chunk Overlap" rows) points to NC-034.
- `tools/check_docs_content_policy.py` (once extended by the companion
  issue) reports zero new findings for the 3 edited locations.
- `docs/03_rag_05_1-configuration-reference.md` and
  `docs/00_governance_03_issue-and-uncertainty-management.md` are unedited
  except where explicitly permitted above.

## Testing Expectations
Not required for code (documentation-only, no behavior or public API
change). Run `tools/check_docs_quality.py`, `tools/check_docs_structure.py`,
and `tools/check_docs_content_policy.py` on every edited file.

## Documentation Impact
This issue is itself a documentation change. Apply `routing.md`'s
Documentation row per `AGENTS.md` Global Rule 10.

## Out of Scope
- Extending `tools/check_docs_content_policy.py` — tracked as the companion
  issue (see Dependencies).
- Any `docs/*.md` file not yet confirmed to contain this duplication
  pattern — full-corpus discovery is deferred to the plan phase, using the
  companion tool once it exists.
- Resolving NC-034 or NC-035 themselves (each requires owner/historical
  confirmation, already tracked and assigned separately in
  `docs/00_governance_03_issue-and-uncertainty-management.md`).
- Any change to `config/*.toml` files or source code.
- `docs/03_rag_05_5-constraints-reference.md`'s architectural/algorithm/
  validation-level rows (language-detection threshold, "Replication",
  type/non-empty/validation-scope constraints) — see Target Files or Areas
  and Unresolved Questions.

## Dependencies
Depends on the companion issue "Detect code-fallback-vs-operational-value
duplication in docs" (filed the same day) for full-corpus discovery beyond
this issue's 3 confirmed files, and for automated post-edit validation. This
issue's own confirmed locations (within those 3 files) can be planned and
remediated without waiting for the companion issue to land, since they were
confirmed by direct reading, not by the (not-yet-existing) tool check.

## Unresolved Questions
Whether `docs/03_rag_05_5-constraints-reference.md`'s remaining rows
(language-detection threshold, "Replication", `chunk_index` type
constraint, `url`/`content` non-empty requirements, `lang`/
`chunking_strategy` validation scope) count as the source request's
"threshold that changes algorithm meaning" keep-exception, or should also be
reduced — Assumption: these are architectural/algorithm/validation-level
invariants enforced in code regardless of any config file, not
environment-config values subject to drift, so they are out of this issue's
scope. Flagged for confirmation during plan creation, not resolved here.

## AI Implementation Instruction
Confirm each of the 3 target locations still contains the described
duplication before editing — do not edit based solely on this issue's
citation if content has since changed. Point to
`docs/03_rag_05_1-configuration-reference.md` and NC-034/NC-035 rather than
restating values. Do not create a new Needs-Confirmation entry duplicating
NC-034/NC-035. Do not touch `docs/03_rag_05_1-configuration-reference.md` or
`docs/00_governance_03_issue-and-uncertainty-management.md`'s existing NC
entries. Preserve the exception categories listed in Implementation Intent —
when in doubt whether a specific row qualifies as an exception, leave it
unedited and record it as a Needs-Confirmation item in the plan rather than
removing it.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-102252
- **Related target files**: docs/03_rag_02_02_ingestion_pipeline-crawler.md,
  docs/03_rag_01_system_overview.md,
  docs/03_rag_05_5-constraints-reference.md

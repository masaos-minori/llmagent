# Add a lint tool that catches ADR structural drift this session's manual review found (missing Known Deviations heading, Implementation Notes/References duplication) — full four-way content classification is out of reach for automation

## Priority
Medium

## Summary
This session manually reviewed all 13 ADRs' `## Implementation Notes` sections against four classification buckets (delete / promote to ADR-Decision-or-design-body / move to Known Issue / move to Needs Confirmation) and found two mechanically-detectable structural problems that no existing tool catches: (1) ADR-004 is missing the standard `## Known Deviations` heading entirely, with deviation content embedded elsewhere instead; (2) all 13 ADRs' Implementation Notes carry a file/class/config/test list that duplicates their own `### Implementation References` subsection. Both are checkable by a script; the deeper four-way semantic classification (does this sentence explain a "why," does it read as a provisional/unclear deviation, etc.) is not — that judgment requires reading and understanding prose, which this issue does not propose automating.

## Background
This issue follows a review requested in this session ("ドキュメント編集や削除対象検知にツールを作成するべきか判断し、ツール作成が必要なら issue に記載してください" — decide whether tooling is warranted for detecting document-edit/deletion targets, and file an issue if so). This issue is that judgment: yes for the two structural checks below, no for full semantic classification.

## Problem
Confirmed during this session's manual audit (see companion issues `20260914-124357_docqa01_...`, `20260914-124438_docqa02_...`, `20260914-124517_docqa03_...`, `20260914-124601_docqa04_...`):
- `docs/adr/ADR-004-environment-failure-handling-policy.md` lacks a `## Known Deviations` heading — confirmed via `grep -n "^## " docs/adr/ADR-004-*.md` returning no match, while every other ADR in `docs/adr/` has one. No existing tool in `tools/` (`check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_docs_structure.py`, `check_docs_quality.py`) checks that every ADR has this heading — `check_docs_structure.py` currently fails to even run in this environment (`ModuleNotFoundError: No module named 'yaml'`, unrelated to this issue but noted since it may be the intended location for such a check).
- All 13 ADRs' Implementation Notes file/class/config/test list duplicates the same ADR's own Implementation References subsection — confirmed for ADR-001, ADR-002, ADR-004 by direct comparison; expected structurally identical for the remainder per the shared template, but not individually diffed for all 13 during this session (the companion issue `20260914-124438_docqa02_...` covers doing so). No existing tool detects this class of intra-document duplication.
- By contrast, the semantic classification itself (is this sentence a "why," does it imply an unclear/provisional state, does it look like a value with no stated rationale) was performed by direct reading and judgment during this session — no proposed heuristic (keyword matching on "なぜ"/"理由"/"暫定" etc.) was found reliable enough to replace that reading, and this issue does not recommend building one.

## Reason for Change
The two structural checks above are exactly the kind of drift that recurs silently: a future ADR author can easily forget the `Known Deviations` heading, or let an Implementation Notes list drift out of sync with Implementation References after a rename, with nothing currently flagging either. This project already has a working precedent for this class of tool (`tools/check_adr_reference.py`, `tools/check_adr_invariant_matrix.py`) — extending that family with two more narrowly-scoped, mechanically-verifiable checks fits the existing pattern rather than introducing a new one.

## Implementation Intent
Add a new tool (or extend an existing one, e.g. `check_adr_reference.py` or a new `check_adr_structure.py`) that: (a) verifies every file under `docs/adr/*.md` contains a `## Known Deviations` heading (or an explicitly-stated equivalent per whatever the template ultimately requires — confirm against `docs/00_governance_01_documentation-policy.md`'s section-header rule first), and (b) for each ADR, extracts the file/symbol references under `## Implementation Notes` and under `### Implementation References`, and flags a mismatch (a file/symbol in one list absent from the other) as a warning — not necessarily requiring the two lists be textually identical, since Implementation Notes may legitimately have zero list content after the companion cleanup issue is implemented.

## Target Files or Areas
- `tools/` (new script or extension to `check_adr_reference.py`)
- `docs/00_governance_04_documentation-checks.md` (register the new check per this project's existing convention for documenting checks)

## Required Changes
- Implement the `Known Deviations` heading-presence check across all `docs/adr/*.md` files.
- Implement the Implementation Notes vs. Implementation References file/symbol cross-reference check, scoped to flag drift (not to enforce byte-identical lists, since the companion cleanup issue may leave Implementation Notes with no list at all).
- Add the new check to whatever CI/pre-commit pipeline already runs `check_adr_reference.py`/`check_adr_invariant_matrix.py` (check `.pre-commit-config.yaml` or equivalent for the existing hook registration pattern).
- Document the new check in `docs/00_governance_04_documentation-checks.md` following the existing entries' format.

## Constraints
Do not attempt to automate the four-way semantic classification (delete/promote/Known-Issue/Needs-Confirmation) itself — this issue is scoped to the two structural checks only, per the Reason for Change above; a false sense of "the tool would have caught it" for the semantic judgment would be misleading, since no keyword heuristic was found reliable during this session's actual review.

## Acceptance Criteria
- Running the new tool against the current `docs/adr/` directory (before the companion cleanup issues are implemented) flags ADR-004's missing `Known Deviations` heading and reports the Implementation-Notes-vs-Implementation-References duplication pattern found across the 13 ADRs.
- The tool is registered in the same pre-commit/CI pipeline as `check_adr_reference.py`.
- The new check is documented in `docs/00_governance_04_documentation-checks.md`.

## Testing Expectations
Add a unit test for the new tool (following the pattern of any existing test for `check_adr_reference.py`, if one exists — check `tests/` for `test_check_adr_reference.py` or equivalent) covering: an ADR missing the heading (should flag), an ADR with a duplicated Implementation Notes/References list (should flag), and a clean ADR (should not flag).

## Documentation Impact
Register the new check in `docs/00_governance_04_documentation-checks.md`.

## Out of Scope
- Automating the four-way semantic classification itself (delete/promote/Known-Issue/Needs-Confirmation) — explicitly ruled out per Constraints above.
- Fixing `tools/check_docs_structure.py`'s current `ModuleNotFoundError: No module named 'yaml'` failure — noted as observed during this issue's drafting but unrelated to this issue's scope; file separately if it blocks CI.
- The actual ADR content fixes this review identified (ADR-004's Known Deviations restructuring, the 13-ADR list duplication cleanup, ADR-006/ADR-007's prose reclassification) — tracked in their own dedicated issues from the same review.

## Dependencies
N/A: none for building the tool itself, though running it against the current state will surface the same findings already filed as `20260914-124357_docqa01_...` and `20260914-124438_docqa02_...` — implement those first or expect the new tool to fail on the current tree until they land.

## Unresolved Questions
Whether `check_adr_reference.py` should be extended in place or a new dedicated script should be added — resolve during implementation by reading `check_adr_reference.py`'s existing scope statement (it explicitly frames itself as intentionally narrow, "a smaller, well-scoped 'ADR-vs-code' audit rather than a repository-wide mandate") to judge whether these two new checks fit its stated scope or warrant a sibling script.

## AI Implementation Instruction
Read `tools/check_adr_reference.py` in full first to match its existing code style, CLI argument conventions (`--format json`), and use of `tools/_docs_consistency_lib.py`'s `Issue`/`report_and_exit` helpers before writing the new check — do not introduce a different reporting format or library.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-124634
- **Related target files**: tools/check_adr_reference.py, docs/00_governance_04_documentation-checks.md

# Re-record drifted docs size ceilings

## Priority
Medium

## Summary
`tools/check_docs_structure.py` fails at `HEAD` with three size findings that pre-date any current
work item: `adr_02_01_004`, `adr_02_05_008` and `deployment_01` each grew past the ceiling recorded
in its `SIZE_EXCEPTIONS` entry. Bring the three documents and their recorded ceilings back into
agreement so the checker exits 0 with no findings.

## Background
Each `SIZE_EXCEPTIONS` entry in `tools/check_docs_structure.py` carries a dated comment stating that
"the ceiling equals the accepted size, so further growth fails". The three entries below were last
re-recorded at sizes smaller than the files now have, so growth landed without being re-accepted:

- `adr_02_01_004_platform-environment-failure-handling-policy.md`: recorded 32586 (2026-11-11), file
  is 33944 B. Grew in `83879685e` (adrrev008, fail-closed `mcp_dedup` store).
- `adr_02_05_008_db-sqlite-4db-separation.md`: recorded 34206, file is 36197 B. Grew in
  `c3573341e` (adrrev005), `83879685e` (adrrev008) and `8ab061b3c` (adrrev009).
- `deployment_01_deployment.md` (`docs/90_deployment/`): recorded 26797 (2026-11-09), file is
  27339 B. Grew in `df511141b` (generalized fingerprint gate description).

`20261001-104656_docsize001_reduce-documentation-policy-below-structure-size-limit.md` and
`20261001-125058_adrsize001_reduce-oversized-adrs-below-docs-structure-size-limit.md`
(both in `issues/done/`) are the earlier lineage of the same gate; this issue is the drift that
accumulated after they closed.

## Problem
Because the gate exits 1 for reasons unrelated to the change under review, every procedure that runs
`check_docs_structure.py` in its Validation plan gets a red signal it cannot fix within its own scope,
and cannot tell whether its own edits are what broke the gate. The recorded ceilings also no longer
describe reality, so the "further growth fails" contract is not being enforced at the intended size.

## Reason for Change
The adrrev010 ADR-013 procedure hit the same shape of failure (ADR-013 sat exactly at its 28097
ceiling and its mandated wording grew it to 28647 B). That one was resolved by re-recording the
ceiling with a dated comment. Resolving only the single file under review leaves the other three
findings in place, so the checker still fails for the next procedure.

## Implementation Intent
For each of the three files, decide per-file whether the growth was owner-intended, then apply one of
the two accepted resolutions:
- Re-record the `SIZE_EXCEPTIONS` ceiling to the current accepted size, with a dated comment naming
  the commit and the content that grew (the convention already used for every other entry).
- Condense the document back under the recorded ceiling, keeping invariants, approvals, Known
  Deviations, and test citations intact.
Do not raise `MAX_SIZE` and do not remove an entry; each file stays individually accounted for.

## Target Files or Areas
- `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
- `docs/90_deployment/deployment_01_deployment.md`
- `tools/check_docs_structure.py` (`SIZE_EXCEPTIONS` entries and their comments)
- `tools/check_module_size_tools_baseline.txt` (`check_docs_structure.py` row, only if the checker
  file grows as a result of re-recording)

## Required Changes
- Confirm the byte size of each of the three files against its recorded ceiling and the commit that
  grew it (`git log -p` on the doc, `git log` on the checker).
- For each file, re-record the ceiling to the accepted size with a dated comment, or condense the
  content under the existing ceiling; record which resolution was chosen and why.
- Keep `tools/check_docs_structure.py` within its `tools/` size baseline; if re-recording grows it,
  bump `check_docs_structure.py` in `tools/check_module_size_tools_baseline.txt` to the new size.
- Re-run the gate and confirm zero findings.

## Constraints
- ADR invariants, normative keywords, Implementation References, Known Deviations and Approval records
  must not be edited to save bytes; condensation may only touch prose that duplicates other sections
  (`skills/DESIGN.md` "Avoid implementation-reference duplication", "Docs content policy — remove").
- Re-recorded ceilings must equal the accepted size exactly, so later growth fails.
- No change to `MAX_SIZE`, no new exceptions, no unrelated reformatting of either document.

## Acceptance Criteria
- `uv run python tools/check_docs_structure.py` exits 0 and prints no findings.
- Each of the three files either sits at or below its recorded ceiling, or its ceiling comment records
  the accepted size, the date, and the commit and content that justified the increase.
- `uv run python tools/check_adr_preservation.py` reports no ERROR against `HEAD`; any reduction is
  accompanied by a sentence-level mapping for the sections it flags.
- `uv run python tools/check_docs_quality.py`, `check_docs_content_policy.py`,
  `check_docs_japanese.py`, `check_docs_consistency.py --domain eventbus` and
  `check_docs_consistency.py --domain workflow` pass.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline
  tools/check_module_size_tools_baseline.txt` exits 0.

## Testing Expectations
Documentation-only change: no unit or integration test changes. Verification is the documentation
checkers above plus `check_module_size.py` for the tools/ side. Manual check: diff each document
against `HEAD` and confirm no normative or approval text changed.

## Documentation Impact
No new documentation. The change is inside the three documents themselves plus the ceiling comments in
`tools/check_docs_structure.py`. If condensation is chosen for an ADR, its `Known Deviations` and
`Review Triggers` sections must stay consistent with what was removed.

## Out of Scope
- ADR-013 (`adr_02_04_013_eventbus-authentication-authorization.md`): its ceiling was re-accepted at
  28647 on 2026-11-11 by the adrrev010 procedure and must not be changed here.
- Raising `MAX_SIZE` or splitting `tools/check_docs_structure.py` into modules.
- Any change to `scripts/`, tests, or `config/`.
- The paused Plans `plans/20261111-104605_adrrev016_adr-authority-format.md` and
  `plans/20261111-110144_adrrev017_docs-history-wording.md`.

## Dependencies
- `issues/20261111-163903_deploydoc001_lifecycle-deployment-docs.md` (active) also targets
  `docs/90_deployment/`. Sequence this issue after it, or re-anchor the `deployment_01` ceiling against
  the post-deploydoc001 size, so the ceiling is not re-recorded twice.

## Unresolved Questions
- Whether the growth introduced by `83879685e`, `8ab061b3c` and `df511141b` was owner-accepted (then
  re-record the ceilings) or incidental (then condense the documents). Needs-Confirmation: owner
  decision per file.
- Whether ADR-004 and ADR-008 should be split into smaller ADRs instead of carrying raised ceilings, as
  `adrsize001` did for earlier oversize ADRs.

## AI Implementation Instruction
Handle the three files one at a time, one resolution per file. Never edit invariant, reference,
Known Deviation, or Approval text to fit a byte budget. Every ceiling change must be paired with a
dated comment naming the commit and the grown content, and the ceiling must equal the resulting size.
Finish only when `check_docs_structure.py` reports zero findings.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261111-000400_adrrev010_eventbus-authz-harden.md`
- **Source implementation procedure**: `implementations/20261111-212354_01_docs_10_adr_adr_02_04_013_eventbus-authentication-authorization.md.md`
- **Generated at**: 20261111-224650
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/90_deployment/deployment_01_deployment.md`, `tools/check_docs_structure.py`, `tools/check_module_size_tools_baseline.txt`

# Resolve dangling and unparseable Known Issue references flagged by check_known_deviation_sync.py

## Priority
Low

## Summary
`tools/check_known_deviation_sync.py` reports `[WARNING]` dangling-reference and
Status-parse findings for several Known Issue IDs referenced across ADRs and the EventBus
overview. Investigate each reference and resolve it (add a canonical entry or remove/rework
the reference) so the checker passes, without changing any ADR decision.

## Background
`check_known_deviation_sync.py` treats every
`docs/*/_90_inconsistencies_and_known_issues.md` file plus
`docs/00_governance/governance_03_issue-and-uncertainty-management.md` as canonical. No
`*_90_*` files remain after the governance reorg, so `governance_03` is the sole canonical
source. Its canonical-header regex (`^#{3,4} ([A-Z]+-\d+)(?::|\s*$)`) accepts an ID
followed by `:` at end of line or nothing else; entries titled `### <ID>: <title>` are NOT
recognized as canonical headers.

## Problem
The following findings are reported (all pre-existing; out of scope for the kdref001
dangling-resolution cycle):
- `adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md:391` — `EVENTBUS-001` dangling
- `adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md:397` — `EVENTBUS-003` dangling
- `adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md:403` — `EVENTBUS-004` dangling
- `adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md:421` — `EVENTBUS-009` dangling
- `adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md:428` — `EVENTBUS-010` dangling
- `adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md:448` — `INV-07` dangling
- `adr/ADR-009-rag-ft5-text-separation.md:362` — `DESIGN-2` dangling
- `adr/ADR-010-rag-fallback.md:342` — `DESIGN-1` dangling
- `adr/ADR-013-eventbus-authentication-authorization.md:317` — `EVENTBUS-008` dangling
- `eventbus_01_system-overview.md:62` — `EVENTBUS-001`'s Status field could not be parsed in
  either the bullet-list or inline-prose format (skipped from cross-check)

`governance_03` has no `#### <ID>` heading for any of these IDs. Several have local
`### <ID>: <title>` sections (for example `EVENTBUS-001` in
`docs/24_eventbus/eventbus_01_system-overview.md`), but those titled headings are not
recognized as canonical and lack a parseable `**Status**: ...` field.

## Reason for Change
These warnings keep `check_known_deviation_sync.py` non-zero in CI and point readers at
references whose canonical state cannot be validated. They were deliberately deferred during
kdref001 and are now being closed out.

## Implementation Intent
High level only. For each flagged reference, determine the correct outcome and apply it
doc-only:
- If the Known Issue is still tracked/valid, add a proper `#### <ID>` entry to
  `governance_03` with a parseable `**Status**: ...` field (and, where the same ID has a
  dedicated overview section such as `EVENTBUS-001`, add the missing `**Status**: ...`
  field there too).
- If the reference is stale/legacy (no longer corresponding to current content), remove the
  dangling clause from the ADR's `### Known Issues` pointer bullet.

Decide per-ID during planning using Known Issue history; do not guess. See Constraints.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (add canonical
  entries if needed)
- `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- `docs/10_adr/ADR-009-rag-ft5-text-separation.md`
- `docs/10_adr/ADR-010-rag-fallback.md`
- `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`
- `docs/24_eventbus/eventbus_01_system-overview.md`

## Required Changes
- Resolve each dangling reference listed above (add canonical entry or remove the dangling
  clause).
- Add a parseable `**Status**: ...` field to the `EVENTBUS-001` entry in
  `docs/24_eventbus/eventbus_01_system-overview.md` so the parser can read it.
- Ensure no flagged ID remains unaddressed.

## Constraints
- Do not change any ADR decision, invariant ID, status, date, or quoted code beyond what
  resolving the reference requires.
- Do not reformat IDs to evade `_ID_LOOKAHEAD_RE` — delete whole `ID (description)` clauses
  when removing them; never hide IDs behind full-width punctuation.
- Do not change `check_known_deviation_sync.py` lookahead/canonical-scan behavior.
- Keep ADR/governance text in English.

## Acceptance Criteria
- `uv run python tools/check_known_deviation_sync.py` reports no `[WARNING]` for
  `EVENTBUS-001`, `EVENTBUS-003`, `EVENTBUS-004`, `EVENTBUS-009`, `EVENTBUS-010`,
  `INV-07`, `DESIGN-1`, `DESIGN-2`, `EVENTBUS-008`.
- No new `[ERROR]`/`[WARNING]` findings are introduced.
- The two pre-existing `[ERROR]` status-mismatch findings (`CI-001`, `CI-016`) and all
  other out-of-scope findings are left untouched.

## Testing Expectations
Documentation-only. Run `uv run python tools/check_known_deviation_sync.py` and
`uv run pytest tests/tools/test_check_known_deviation_sync.py`.

## Documentation Impact
Yes. ADR `### Known Issues` pointer bullets and `governance_03` canonical entries.

## Out of Scope
- The `[ERROR]` status-mismatch findings (`CI-001`, `CI-016`) — tracked in a separate issue.
- Changing `check_known_deviation_sync.py` lookahead/canonical-scan behavior.

## Dependencies
- Follows the kdref001 dangling-resolution cycle.

## Unresolved Questions
- Per ID: still-open (add canonical entry) vs stale (remove reference)? Requires Known Issue
  history (`git log` of `governance_03`, closing plans) to confirm.
- Should `EVENTBUS-001`'s existing `docs/24_eventbus/eventbus_01_system-overview.md`
  section be kept alongside a new `governance_03` entry, or consolidated?

## AI Implementation Instruction
Confirm each ID's canonical state from `governance_03` and git history before editing. Add
`#### <ID>` entries with a parseable `**Status**: ...` where the issue is genuinely
tracked; otherwise delete the whole dangling `ID (...)` clause from the ADR pointer bullet.
Fix the missing `**Status**: ...` on the `EVENTBUS-001` overview entry. Verify with the
checker and unit tests; ensure no new findings appear.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-080956
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md, docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md, docs/10_adr/ADR-009-rag-ft5-text-separation.md, docs/10_adr/ADR-010-rag-fallback.md, docs/10_adr/ADR-013-eventbus-authentication-authorization.md, docs/24_eventbus/eventbus_01_system-overview.md

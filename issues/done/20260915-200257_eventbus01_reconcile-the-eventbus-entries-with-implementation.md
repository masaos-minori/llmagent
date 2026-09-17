# Reconcile the EventBus entries with the current implementation and document set

## Priority
Medium

## Summary
EVENTBUS-001 cites a source that may no longer be on the live path, carries a severity that overstates its actual exposure, and points at two entries that are removed or absent. Separately, EVENTBUS-002's resolution rests on a document whose existence the same document set calls into question.

## Background
This issue is derived from a consolidated audit of the governance documentation set recorded in `memo3.md` (repository root) — an 18-item review of `docs/00_governance_03_issue-and-uncertainty-management.md` and related documents, later consolidated into 9 issues. No further background beyond the Summary and Reason for Change is needed.

## Problem
EVENTBUS-001's `Source` is `scripts/eventbus/offsets.py::write_offset()`, but `scripts/eventbus/ack_route.py` carries the comment "write_offset removed — replaced by ack_event_for_consumer() transactional path." The current ACK path stores `consumer_id` verbatim into `consumer_delivery` and `consumer_offsets` with no call to `_sanitize_consumer_id()`, so `user.1` and `user_1` land in distinct rows and cannot collide. The residual risk is confined to `migrate_legacy_offsets()`, and only on the branch taken when a legacy offset file has no `.map` companion — a one-time, conditional migration step. The entry nonetheless carries `Severity: High` and a `Summary` describing "silent overwriting of offsets," which reads as a continuously exploitable defect in the live delivery path. Its `Related` field compounds the problem: `EVENTBUS-008` was declared removed in the same document, and `EVENTBUS-003` has no heading at all — not even a removal placeholder. `First Found` is `Unconfirmed`.

Separately, EVENTBUS-002 cites `docs/eventbus/03_replay_operations.md` in four separate fields as the document that now specifies the `{total, limit, offset, items}` response shape. But the Area Canonical Map lists `docs/eventbus/specification.md` with the annotation "(Needs Confirmation — path does not exist in repository, see plans/20260905-185329_plan.md)", and no `docs/eventbus/` content appears anywhere in the consolidated document set reviewed. Either the map annotation is stale, or an entry was closed against a document that does not exist.

## Reason for Change
These are batched because a single pass over `scripts/eventbus/` and `docs/eventbus/` settles both, and because both hinge on the same question: does the artifact each entry cites still exist and still do what the entry says?

`High` severity is defined in the governance document as "requires immediate attention; affects safety or critical functionality," and a one-time migration fallback does not meet that bar. Severity is what drives triage order, so an inflated one displaces genuinely urgent work. For EVENTBUS-002, closing an entry against a document that may not exist means the resolution is unverifiable — the Decision Target Canonical Source Matrix requires resolutions to be checkable against a real, current artifact.

## Implementation Intent
Bring both entries into alignment with what the repository actually contains, so that severity reflects real exposure and every cited artifact can be confirmed.

For EVENTBUS-001 the goal is narrowing, not closing. The collision risk is real — it is simply much smaller and reachable only under a specific condition. Rewriting `Source`, `Severity`, `Summary`, `Current Description`, and `Impact` to describe the migration fallback preserves the finding while removing the false implication that live traffic is affected.

For EVENTBUS-002 the goal is evidence. A directory listing either substantiates the resolution and makes the canonical map's annotation removable, or invalidates the resolution and requires the entry reopened. This must be settled before the status-vocabulary issue (`docs/00_governance_03_issue-and-uncertainty-management.md`'s status-vocabulary cleanup, tracked separately) converts EVENTBUS-002 into a placeholder asserting that it was resolved — this issue's directory-listing evidence is a prerequisite for that other issue's EVENTBUS-002 decision, per `memo3.md`'s stated Execution Order.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `docs/00_governance_01_documentation-policy.md` (Area Canonical Maps)
- `scripts/eventbus/offsets.py`
- `scripts/eventbus/db.py`
- `scripts/eventbus/ack_route.py`
- `docs/eventbus/` (directory listing)
- `plans/20260905-185329_plan.md`

## Required Changes

**EVENTBUS-001**
- Confirm from the code whether `write_offset()` is still reachable on any live path.
- Update `Source` to `scripts/eventbus/db.py::migrate_legacy_offsets()` if the confirmation holds.
- Lower `Severity` from `High` to `Medium`, reflecting one-time-migration-only exposure.
- Narrow `Summary`, `Current Description`, and `Impact` to the missing-`.map`-companion fallback.
- Remove `EVENTBUS-008` from `Related`. Either remove `EVENTBUS-003` or add a removal placeholder for it.
- Set `First Found` to a confirmed date if determinable.

**EVENTBUS-002 evidence**
- Produce a real directory listing of `docs/eventbus/`.
- If `03_replay_operations.md` exists and documents the pagination shape: update the Area Canonical Map to drop the stale Needs Confirmation annotation and register the correct canonical path.
- If it does not exist: reopen EVENTBUS-002 and record that its resolution evidence is missing.
- Resolve whether the canonical EventBus API reference is `specification.md`, `03_replay_operations.md`, or neither.

## Constraints
- Do not change `ack_event_for_consumer()` or any part of the live ACK path.
- Do not implement collision detection in `migrate_legacy_offsets()`.
- Do not change `write_offset()`.
- Do not author `docs/eventbus/` content.
- Do not remove the canonical map's Needs Confirmation annotation without a directory listing as evidence.
- Complete the EVENTBUS-002 verification before the status-vocabulary issue converts it to a placeholder.

## Acceptance Criteria
- [ ] EVENTBUS-001 `Source` names the file and function that actually carries the risk.
- [ ] EVENTBUS-001 `Severity` is `Medium` with the narrowed trigger condition stated in the entry body.
- [ ] EVENTBUS-001 `Related` contains no reference to a removed or nonexistent entry.
- [ ] EVENTBUS-001 no longer implies the live ACK path is affected.
- [ ] A directory listing of `docs/eventbus/` is recorded in the issue.
- [ ] EVENTBUS-002's status reflects whether its cited evidence exists.
- [ ] The Area Canonical Map's EventBus row matches the filesystem.
- [ ] No canonical map row cites a path that cannot be confirmed.

## Testing Expectations
Not required for code — documentation-only change with no behavior impact. Manually verify each Acceptance Criteria item by reading the edited sections and by running `ls docs/eventbus/` to confirm the recorded directory listing is accurate, and run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` / `docs/00_governance_01_documentation-policy.md` to confirm no new structural findings.

## Documentation Impact
Yes. `docs/00_governance_03_issue-and-uncertainty-management.md` (EVENTBUS-001 and EVENTBUS-002 entries) and `docs/00_governance_01_documentation-policy.md` (Area Canonical Map's EventBus row) are both corrected by this issue.

## Out of Scope
- Implementing collision detection.
- Authoring EventBus API reference content.
- Any change to delivery semantics.

## Dependencies
`memo3.md`'s Execution Order places this issue fourth, ahead of the status-vocabulary issue (`docs/00_governance_03_issue-and-uncertainty-management.md`'s single-status-vocabulary cleanup), because that issue's EVENTBUS-002 status decision needs this issue's `docs/eventbus/` directory-listing evidence first. No other issue blocks this one.

## Unresolved Questions
N/A: none — the open questions this issue exists to answer (whether `write_offset()` is still reachable, and whether `docs/eventbus/03_replay_operations.md` exists) are resolved by Required Changes itself, not left open after it.

## AI Implementation Instruction
Do not rewrite unrelated files. Delete resolved entries recorded in `docs/00_governance_03_issue-and-uncertainty-management.md` rather than retaining them with a closed-out status, per that document's Current-Specification-Only Policy. Confirm from the code whether `write_offset()` is still reachable before rewriting `Source`, and obtain a real directory listing before editing either document. Stop and report if `write_offset()` is still on the live ACK path, since the severity reduction would then be unjustified.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-200257
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md, docs/00_governance_01_documentation-policy.md, scripts/eventbus/offsets.py, scripts/eventbus/db.py, scripts/eventbus/ack_route.py

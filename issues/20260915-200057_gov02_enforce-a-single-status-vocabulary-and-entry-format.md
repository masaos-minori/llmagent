# Enforce a single, defined status vocabulary and entry format across Part 1

## Priority
High

## Summary
Two entries carry `Status` values that do not exist in the document's own Status Values list — EVENTBUS-002 uses `resolved` and CI-003 uses `Mitigated` — and EVENTBUS-002 additionally retains three fields outside the 16-field template, establishing a second, competing convention for representing resolved entries.

## Background
This issue is derived from a consolidated audit of the governance documentation set recorded in `memo3.md` (repository root). No further background beyond the Summary and Reason for Change is needed.

## Problem
`docs/00_governance_03_issue-and-uncertainty-management.md` defines exactly three status values (`open`, `investigating`, `deferred`) and a disposal rule stating that a resolved entry is removed, not retained with a closed-out status. EVENTBUS-002 violates this by staying as a full entry with `Status: resolved` plus three undefined fields (`Resolved Date`, `Resolution`, `Impact Resolved`). CI-003 violates it differently: `Status: Mitigated` is undefined, wrongly capitalized, and contradicts its own `Recommended Action`, which begins "Resolved — E2E test in `tests/agent/services/test_config_reload.py` confirms only policy fields are updated and no discovery call occurs."

## Reason for Change
The document defines exactly three status values and one disposal rule, and both are unambiguous:

> Status Values: **open** — Issue acknowledged but not yet investigated; **investigating** — Investigation underway; **deferred** — Resolution postponed to future work.
>
> An item is removed from this active inventory once it is resolved or no longer applies to the current system; it is not retained here with a closed-out status.

Eight entries already comply with the disposal rule by being replaced with short prose placeholders: RAG-003, RAG-004, DESIGN-1, SHARED-001, EVENTBUS-008, CI-004, CI-005, CI-006. EVENTBUS-002 does not. It stays as a full entry with `Status: resolved` plus `Resolved Date`, `Resolution`, and `Impact Resolved` — three fields the 16-field template does not define. The document therefore demonstrates two mutually exclusive ways to handle the same situation, and offers no rule for choosing between them. Any future author will copy whichever one they happen to read first.

CI-003 is a different failure of the same vocabulary. `Mitigated` is undefined, is capitalized where every defined value is lowercase, and conflicts with the entry's own `Recommended Action`, which begins "Resolved — E2E test in `tests/agent/services/test_config_reload.py` confirms only policy fields are updated and no discovery call occurs." The status field says one thing, the action field says another, and the disposal rule implies the entry should not be present at all.

These are batched because they are the same defect class and require the same decision. Fixing one without the other would leave the vocabulary half-enforced and would not answer the question that both raise: is a resolved entry removed, or retained with a status?

## Implementation Intent
Converge on one convention and apply it to both entries, so that the Status Values list becomes a closed set that an automated check can validate. The recommended direction is to keep the existing three-value set and the removal rule, because eight entries already follow it and only one does not — the cost of conforming EVENTBUS-002 is far lower than the cost of retrofitting eight placeholders into a retained-entry format.

For CI-003 specifically, the substantive question is whether the entry is resolved. Its `Current Description` states that end-to-end verification exists via `test_apply_config_dict_exercises_real_registry_and_no_discovery_call`, which constructs a real `RuntimeToolRegistry`, calls `ConfigReloadService._sync_services()` with tier and allowed-tools changes, and asserts both that registry state changed and that no discovery-style HTTP call occurred. If that test exists and passes, the ADR-003 invariant is verified and the entry belongs in placeholder form. The only reason to keep it open is the stated dependency on `mcpagent04`, and that dependency should be expressed in `Recommended Action`, not encoded as an invented status value.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `tests/agent/services/test_config_reload.py` (read-only verification)
- `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` (read-only verification)

## Required Changes

For EVENTBUS-002, apply one of:

**Option A — recommended.** Replace the entry with a prose placeholder in the established form, naming the resolution date and the document that now specifies the `{total, limit, offset, items}` response shape, and stating that its absence from the active list is the correct, policy-compliant state.

**Option B.** Amend the Status Values list to include `resolved`, amend the retention rule to permit retained resolved entries, extend the 16-field template to define `Resolved Date` / `Resolution` / `Impact Resolved`, and retrofit all eight existing placeholders to the same format.

For CI-003:
- Verify that `test_apply_config_dict_exercises_real_registry_and_no_discovery_call` exists in `tests/agent/services/test_config_reload.py`.
- If it exists and the invariant is verified: replace CI-003 with a prose placeholder citing the test by name, and record the `mcpagent04` re-evaluation trigger in the placeholder text so the dependency is not lost.
- If it does not exist, or the entry is deliberately held open: set `Status: open` and move the re-evaluation condition into `Recommended Action`, removing the word "Resolved" from that field.

## Constraints
- Do not leave the document using both conventions.
- Do not add `Mitigated` to the Status Values list.
- If Option A is chosen for EVENTBUS-002, carry the resolution evidence into the placeholder prose rather than deleting it.
- Do not modify `scripts/shared/runtime_tool_registry.py` or any test.
- EVENTBUS-002's cited resolution document must be confirmed to exist before its placeholder asserts resolution — coordinate with the EventBus reconciliation issue if that verification has not yet landed.

## Acceptance Criteria
- [ ] No entry in Part 1 carries a `Status` value absent from the Status Values list.
- [ ] No `Status` value uses non-conforming capitalization.
- [ ] Resolved entries are represented in exactly one consistent form throughout Part 1.
- [ ] CI-003's `Status` and `Recommended Action` no longer contradict each other.
- [ ] The `mcpagent04` re-evaluation dependency is preserved somewhere in the document.
- [ ] No entry carries fields outside the 16-field template, unless Option B was chosen and the template was formally extended.

## Testing Expectations
Not required for code — documentation-only change. Manually confirm `test_apply_config_dict_exercises_real_registry_and_no_discovery_call` exists and passes (`uv run pytest tests/agent/services/test_config_reload.py -k test_apply_config_dict_exercises_real_registry_and_no_discovery_call`) before treating CI-003 as resolved. Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` after editing.

## Documentation Impact
Yes. `docs/00_governance_03_issue-and-uncertainty-management.md`'s EVENTBUS-002 and CI-003 entries are rewritten; no other document is affected unless Option B is chosen, in which case the 16-field template documentation itself would also need updating (out of this issue's recommended path).

## Out of Scope
- Implementing `mcpagent04`.
- Changing `/replay` behavior or authoring its documentation.
- Any code change.

## Dependencies
Depends on the EventBus reconciliation issue (ISSUE-5 in `memo3.md`) for verification that EVENTBUS-002's cited resolution document (`docs/eventbus/03_replay_operations.md`) actually exists — that verification must land before this issue's EVENTBUS-002 placeholder asserts resolution. `memo3.md`'s Execution Order places this issue after that one for the same reason.

## Unresolved Questions
Whether Option A or Option B is the intended direction is a judgment call recommended toward Option A in this issue's Implementation Intent, but not mandated — confirm with the document owner before implementing if Option B is preferred.

## AI Implementation Instruction
Do not rewrite unrelated files. Delete resolved entries recorded in `docs/00_governance_03_issue-and-uncertainty-management.md` rather than retaining them with a closed-out status, per that document's Current-Specification-Only Policy. Prefer Option A for EVENTBUS-002. Confirm the named test exists before treating CI-003 as resolved. Stop and report if the EventBus replay documentation cited by EVENTBUS-002 cannot be located, since its resolution would then be unverifiable.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-200057
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md

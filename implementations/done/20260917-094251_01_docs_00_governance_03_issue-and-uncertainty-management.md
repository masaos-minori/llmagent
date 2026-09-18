## Goal

Restore internal consistency of `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1 by deleting the two stale, contradictory bullets under the `#### CI-005` removal placeholder and rebuilding the Part 1 closing summary sentence so it enumerates, mechanically and accurately, only entries whose `Status` is `open`, `investigating`, or `deferred`. Per REQ-001 through REQ-006; AC-1 through AC-7.

## Scope

- Delete two orphaned bullets following the `#### CI-005` placeholder paragraph
- Rebuild the Part 1 closing summary sentence from a mechanical parse of `#### ` headings and their `Status` fields
- Scan every other removal placeholder in Part 1 for the same orphaned-bullet pattern
- Documentation-only change — no code modification

## Assumptions

- The two orphaned bullets at lines 304-305 are indeed stale and contradict the preceding CI-005 placeholder paragraph (which states the config-loading defect is already fixed)
- The Part 1 closing summary sentence (lines 501-502) contains stale ID enumeration — the current text ("...CI-001, CI-003 through CI-016 above") names IDs that either lack full `#### ` headings or carry non-conforming `Status` values
- The source issue's Constraint "Leave the placeholder paragraph itself unchanged" applies only to the CI-005 placeholder paragraph (line 300), not to the orphaned bullets following it

## Design decisions

- Rebuild the closing summary from scratch via mechanical heading/Status parsing rather than editing the existing sentence — so the result reflects the document's real current state rather than propagating a prior author's assumption
- Replace the `EVENTBUS-001 through EVENTBUS-008` contiguous range notation with an explicit list since the range spans entries with mixed disposition (EVENTBUS-001 `Mitigated`, EVENTBUS-002 `resolved`, EVENTBUS-005/006/007 `deferred`, EVENTBUS-008 removed/no heading)
- Separate deferred entries from open entries in the rebuilt sentence if doing so improves clarity, per the issue's own Required Changes

## Alternatives considered

- Editing the existing closing summary sentence in place: rejected because the source issue specifies a mechanical rebuild from headings rather than targeted editing
- Using contiguous range notation for any subset of IDs: rejected because the source issue identifies the range-notation defect as the core problem

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

Delete two orphaned bullets, scan other removal placeholders, and rebuild the closing summary sentence.

### Method

Edit Part 1 of the governance document: remove orphaned bullets, re-scan placeholders, and replace the closing summary sentence with a mechanically parsed version.

### Details

**REQ-001: Delete the two orphaned bullets.**

Current state (lines 298-306):
```markdown
#### CI-005

CI-005 ("ADR-004 INV-03 — fail-closed for missing config not implemented") was resolved and removed from this active inventory 2026-09-14. Confirmed by direct code inspection: this entry's `Source` field cited a non-existent `scripts/shared/config_loader.py::load_config()` — the actual `load_config()` (`scripts/agent/config_builders.py`) calls `ConfigLoader().load_all()`, whose `strict` parameter already defaults to `True` (`scripts/shared/config_loader.py`), and `_REQUIRED_CONFIG_FILES` includes `agent.toml`. `ConfigMissingError` is a `ValueError` subclass, so it is caught by `load_config()`'s own exception handler and re-raised as `ConfigLoadError` — a missing required config file already fails closed. Its absence from the active list is the correct, policy-compliant state — do not create a `#### CI-005` heading. `ConfigLoader.load_all()`'s docstring previously contradicted its actual `strict: bool = True` default ("If False (default), missing files are skipped") — corrected 2026-09-14.

**EventBus-specific verification (REQ-006)**: Verified by configuration test confirming `ConfigMissingError` is raised when a required config file is missing. The EventBus `load_config()` function (`scripts/eventbus/config.py`) validates required keys via `_REQUIRED_CONFIG_KEYS` and raises `ValueError` for missing keys — consistent with the fail-closed behavior described in CI-005.

- **Impact**: Missing critical configuration silently fails open across all environments, including production.
- **Recommended Action**: Pass `strict=True` to `load_all()` or add explicit validation after config loading.

#### CI-006
```

After edit (delete lines 304-305 only):
```markdown
#### CI-005

CI-005 ("ADR-004 INV-03 — fail-closed for missing config not implemented") was resolved and removed from this active inventory 2026-09-14. Confirmed by direct code inspection: this entry's `Source` field cited a non-existent `scripts/shared/config_loader.py::load_config()` — the actual `load_config()` (`scripts/agent/config_builders.py`) calls `ConfigLoader().load_all()`, whose `strict` parameter already defaults to `True` (`scripts/shared/config_loader.py`), and `_REQUIRED_CONFIG_FILES` includes `agent.toml`. `ConfigMissingError` is a `ValueError` subclass, so it is caught by `load_config()`'s own exception handler and re-raised as `ConfigLoadError` — a missing required config file already fails closed. Its absence from the active list is the correct, policy-compliant state — do not create a `#### CI-005` heading. `ConfigLoader.load_all()`'s docstring previously contradicted its actual `strict: bool = True` default ("If False (default), missing files are skipped") — corrected 2026-09-14.

**EventBus-specific verification (REQ-006)**: Verified by configuration test confirming `ConfigMissingError` is raised when a required config file is missing. The EventBus `load_config()` function (`scripts/eventbus/config.py`) validates required keys via `_REQUIRED_CONFIG_KEYS` and raises `ValueError` for missing keys — consistent with the fail-closed behavior described in CI-005.

#### CI-006
```

**REQ-002: Re-scan other removal placeholders.**

Re-scan the 8 other removal placeholders in Part 1 (RAG-003, RAG-004, DESIGN-1, SHARED-001, EVENTBUS-008, CI-001, CI-004, CI-006) for the same orphaned-bullet pattern found at CI-005. If no new instances are found (as currently confirmed), make no edit — record the outcome in the progress update.

**REQ-003, REQ-004, REQ-005: Rebuild the Part 1 closing summary sentence.**

Current state (lines 501-502):
```markdown
No other active Known Issues beyond RAG-005, DESIGN-1, DESIGN-2,
EVENTBUS-001 through EVENTBUS-008, and CI-001, CI-003 through CI-016 above.
```

Mechanical parse results:
- Entries with `#### ` headings AND qualifying `Status` (`open`/`investigating`/`deferred`):
  - RAG-005 (open), DESIGN-2 (open), EVENTBUS-005 (deferred), EVENTBUS-006 (deferred), EVENTBUS-007 (deferred), CI-007 (open), CI-008 (open), CI-009 (open), CI-010 (open), CI-011 (open), CI-012 (open), CI-013 (open), CI-014 (open), CI-015 (open), CI-016 (open)
- Excluded entries:
  - RAG-003 (no qualifying Status — check), RAG-004 (no qualifying Status — check), EVENTBUS-001 (Mitigated), EVENTBUS-002 (resolved), CI-003 (Mitigated), CI-004 (check), CI-005 (check), CI-006 (check), DESIGN-1 (no heading), SHARED-001 (no heading), EVENTBUS-008 (no heading), CI-001 (no heading)

After edit (replace lines 501-502):
```markdown
No other active Known Issues beyond RAG-005, DESIGN-2, CI-007 through CI-016,
and EVENTBUS-005, EVENTBUS-006, EVENTBUS-007 (deferred) above.
```

Note: The exact wording may vary depending on whether separating deferred entries improves clarity (REQ-005). The key requirement is that every ID named has a full `#### ` entry whose `Status` is `open`, `investigating`, or `deferred`, and no ID named elsewhere in the document as resolved/removed/non-conforming appears.

## Compatibility considerations

N/A: documentation-only change, no runtime behavior impact.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

If the rebuilt closing summary proves inaccurate later, the rollback is reverting to the original sentence — no code revert needed. If the deleted orphaned bullets were actually valid content, the rollback is restoring them.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Documentation structural check | `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` | Passes with no new findings |
| docs/00_governance_03_issue-and-uncertainty-management.md | Manual heading/Status cross-check | `grep -n "^\- \*\*Status\*\*:\|^#### "` | Every ID in the rebuilt closing summary has a heading with `Status` in `open`/`investigating`/`deferred`; no gap-containing range remains |
| docs/00_governance_03_issue-and-uncertainty-management.md | Manual orphaned-bullet re-scan | `grep -n "silently fails open"` | No output |

## Completion criteria

- [ ] AC-1: No bullet list appears between the `#### CI-005` placeholder paragraph and the `#### CI-006` heading
- [ ] AC-2: The document contains no remaining statement that missing configuration fails open
- [ ] AC-3: Every ID named in the closing summary has a full `#### ` entry whose `Status` is `open`, `investigating`, or `deferred`
- [ ] AC-4: No ID named in the closing summary is described elsewhere in the document as resolved, removed, or carrying a non-conforming `Status` value
- [ ] AC-5: No contiguous range notation is used where the range contains a gap
- [ ] AC-6: No other removal placeholder in Part 1 is followed by orphaned field-style bullets
- [ ] AC-7: Markdown structure remains valid and no heading levels changed

## Out of scope

- Changing the `Status` value of any entry
- Modifying `scripts/shared/config_loader.py` or `scripts/agent/config_builders.py`
- Resolving or reclassifying any individual Known Issue entry
- Amending the Current-Specification-Only Policy itself
- Converting EVENTBUS-001, EVENTBUS-002, or CI-003 to prose placeholders (that is `plans/20260916-150416_plan.md`'s scope)
- Relocating `SHARED-001`, adding a `CI-002` placeholder, or fixing `NC-033`'s indentation (that is `plans/20260916-152650_plan.md`'s scope)
- Any code change

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the two orphaned CI-005 bullets | Completed | 20260918-171552 | 20260918-171552 |  |
| 2 | Re-scan 8 other removal placeholders for orphaned bullets | Completed | 20260918-171552 | 20260918-171552 |  |
| 3 | Rebuild the Part 1 closing summary sentence | Completed | 20260918-171552 | 20260918-171552 |  |
| 4 | Run check_docs_quality.py and confirm it passes | Completed | 20260918-171552 | 20260918-171552 |  |
| 5 | Manually re-scan grep for heading/Status cross-check | Completed | 20260918-171552 | 20260918-171552 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 through REQ-006
- **Source issue**: issues/20260915-195957_gov01_resolve-self-contradictory-statements-in-the-known-issues-part-1-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-155440_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260917-094251
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
## Goal
- The `tools/TOOL_DESCRIPTIONS.md` Index heading carries no hand-maintained module count, so no stale count can exist and `check_tool_descriptions_sync.py` stays the only drift check for that document.

## Priority
Low

## Scope
- **In-Scope**: change the heading `## Index (65 modules)` to `## Index` in `tools/TOOL_DESCRIPTIONS.md`.
- **Out-of-Scope**: reworking the document structure or the other tables; adding a count check to `check_tool_descriptions_sync.py`; a convention for batch-specific tools.
- **Dependencies**: N/A: none. `issues/20261104-152002_toolcli001_define-cli-and-exit-code-convention.md` also edits this document, so the two changes apply in either order; this Plan is sequenced first because it is a one-line edit.

## Background
The heading read `61 modules` while `tools/` held more files, and was corrected by hand to 65. Adversarial verification on 2026-11-05 confirmed that `check_tool_descriptions_sync.py` compares only the set of backticked `*.py` names in the document with `tools/*.py` and checks `tools/<name>.py` and `-m tools.<name>` references in CI, pre-commit, and tox configuration: it has no check of the number (`main` computes `undocumented`, `stale`, and `dangling` only). Earlier implementation procedures also record the count as already stale and left alone.

## Problem
A hand-maintained number in a document that already has a mechanical checker drifts silently, so a clean checker result does not show the document is accurate.

## Reason for Change
Documentation and code mismatch; low severity and easy to fix.

## Implementation Intent
Remove the number, as the Issue prefers and its AI Implementation Instruction states ("Prefer deleting the number"). Nothing consumes the number, so no check needs to replace it.

## Requirements
- `REQ-001`: The Index heading in `tools/TOOL_DESCRIPTIONS.md` MUST NOT contain a module count.
- `REQ-002`: `check_tool_descriptions_sync.py` behavior and exit codes MUST stay unchanged, and `uv run python tools/check_tool_descriptions_sync.py` and its tests MUST pass.
- `REQ-003`: The change MUST NOT break any reference to the heading (anchors or parsers).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Remove the hand-maintained count | Rewrite the heading `## Index (65 modules)` as `## Index` | `REQ-001`, `REQ-003`; AC-1, AC-3 | Heading at the start of the Index table; 65 non-package modules in `tools/` today; no anchor or parser references the heading text (`rg` over rules, skills, templates, prompts, tools, tests, docs found none) (checked in Step 2 and Step 3) | `tests/tools/test_check_tool_descriptions_sync.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/check_tool_descriptions_sync.py` | Confirms it compares name sets only and never reads the count | `REQ-002` |
| `tests/tools/test_check_tool_descriptions_sync.py` | Existing tests stay valid; no test depends on the heading | `REQ-002` |

## Acceptance Criteria
- AC-1: No count remains in the Index heading, so a stale count cannot pass the checker (`REQ-001`).
- AC-2: `uv run python tools/check_tool_descriptions_sync.py` reports `No issues found.` and `uv run pytest tests/tools/test_check_tool_descriptions_sync.py -q` passes (`REQ-002`).
- AC-3: A repository search for the old heading text and for an `index-` anchor finds no live consumer (`REQ-003`).

## Tests
- No new test: removing the number leaves no behavior to test (the Issue asks for a test only if a check is kept) (`REQ-001`).
- Run the existing checker and its tests (`REQ-002`).

## Documentation Impact
Yes: the change is itself the documentation update of `tools/TOOL_DESCRIPTIONS.md` (`REQ-001`). No `docs/*.md` file is affected.

## Assumptions
- Removal, not a derived check, satisfies the Issue's Acceptance Criteria ("or no count exists to go stale") and follows its stated preference (judgment).
- Overlap judgment (`check_plan_target_overlaps.py`): `tools/TOOL_DESCRIPTIONS.md` is also a target of the `toolcli001` Plan; the designs are compatible (this Plan edits only the Index heading, that Plan adds a new section) and this Plan lands first.
- The count was never an accepted contract: the Issue's Unresolved Question "whether anything parses the heading's number" is answered by the `rg` search in Step 3 (none found).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether an external consumer outside the repository reads the heading | Cannot be searched from the repository | Not actionable here; the repository search found none, and the risk is a rename of one heading | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low (one heading; the checker reads backticked file names only) | 82 | High (one author across the repository history) | not applicable (rsynced) |

## Design
- Path A (one target file, no interface or schema change). Validation quality baseline: `N/A: no Python target`.
- Churn on `tools/TOOL_DESCRIPTIONS.md` is the highest in the repository (82 commits in 30 days), so the edit is a single-line change to keep merge conflicts minimal, and it is sequenced before the `toolcli001` edit of the same document.
- Consumer scan: not applicable; no persisted schema, public API, or shared constant changes.

## Implementation steps
1. **Phase 1: Remove the count**
   - [ ] Change the heading to `## Index` (`REQ-001`; `tools/TOOL_DESCRIPTIONS.md`)
2. **Phase 2: Verification**
   - [ ] Run `uv run python tools/check_tool_descriptions_sync.py`, and `uv run pytest tests/tools/test_check_tool_descriptions_sync.py -q`; search the repository for the old heading text (`REQ-002`, `REQ-003`; `tools/TOOL_DESCRIPTIONS.md`). No deploy step: only `tools/` documentation changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Integration (sync checker) | `uv run python tools/check_tool_descriptions_sync.py` | `No issues found.`, exit 0 |
| `tools/TOOL_DESCRIPTIONS.md` | Unit (existing) | `uv run pytest tests/tools/test_check_tool_descriptions_sync.py -q` | All pass |
| `tools/TOOL_DESCRIPTIONS.md` | Reference search | `rg -n 'Index \(' tools/ rules skills routing.md` | No remaining count |

## Risks
- **Risk**: A later edit reintroduces a count and it drifts again → **Mitigation**: accepted; the Issue allows removal as the fix, and a derived check would be new behavior the Issue ranks second.
- **Risk**: Concurrent Plans edit the same high-churn document → **Mitigation**: one-line edit; apply before the `toolcli001` Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the module count from the Index heading | Pending | — | — | |
| 2 | Run the sync checker, its tests, and the reference search | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261104-152002_toolsdocsync001_check-index-count-in-tool-descriptions.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-105554
- **Related target files**: tools/TOOL_DESCRIPTIONS.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; Implementation Intent; AI Implementation Instruction | `tools/TOOL_DESCRIPTIONS.md` | 1 | AC-1 | Sync checker run | Explicit in issue |
| REQ-002 | Constraints; Acceptance Criteria 2; `check_tool_descriptions_sync.py` `main` (Step 3) | `tools/TOOL_DESCRIPTIONS.md` | 2 | AC-2 | Checker and its existing tests | Confirmed by repository evidence |
| REQ-003 | Unresolved Questions; repository search (Step 3) | `tools/TOOL_DESCRIPTIONS.md` | 2 | AC-3 | Reference search | Confirmed by repository evidence |

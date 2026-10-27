## Goal
- Classify the unimplemented context-aware case of the removed-name check (`GV-017`) exactly once, as an Accepted Limit, in `governance_04_documentation-checks.md`, so that the check description, the `GV-017` matrix row, `Follow-up Work Needed` and `Accepted Limits` no longer contradict each other.

## Priority
Medium

## Scope
- **In-Scope**:
  - Reword the "Not yet implemented (follow-up)" sentence of the second detection case.
  - Add that case to `Accepted Limits` with current behavior, Owner, rationale and a re-evaluation condition.
  - Align the `GV-017` row (Status and Follow-up columns) with the same classification.
  - Confirm `Follow-up Work Needed` stays consistent.
- **Out-of-Scope**:
  - Implementing the unimplemented detection case in `tools/check_compat_shims.py`.
  - Changing the `GV-014` rule text or other matrix rows.
  - ADR changes, including references to removed command names (tracked separately).
- **Dependencies**: N/A: none. No open issue or in-flight plan touches this document section; the other issues of the same review batch edit different documents.

## Background
- The removed-name check has two detection cases. The first (a name fully absent from source) is implemented. The second (a name that remains in source but is no longer the current production path) is described as "Not yet implemented (follow-up)". `Follow-up Work Needed` in the same document says no follow-up work is tracked, and `Accepted Limits` lists only two other gaps.
- The second case is unimplemented in the tool: a comment in `tools/check_compat_shims.py` states that the context-aware check is not attempted. The design plan `plans/done/20260903-090945_plan.md` classified that half as an out-of-scope follow-up, and no issue tracks it.
- `GV-014` (no unimplemented auto-check documented as implemented) is not literally violated, because the document states the case is unimplemented.

## Problem
The document states two incompatible things about one gap: the case is unimplemented and labeled follow-up, but the follow-up register says there is none. A reader cannot tell whether the gap is accepted, tracked or forgotten, and cannot tell the effective coverage of `GV-017`.

## Reason for Change
Governance documents define how every other document is verified. An ambiguous coverage statement can make reviewers assume a stale name presented as current is detected automatically. Nothing makes the change time-sensitive beyond that risk.

## Implementation Intent
Keep one classification per gap. Classify the case as an Accepted Limit because it needs a current-specification section analysis that a name search cannot provide, and manual review already covers it. State the Owner, rationale and re-evaluation condition in the form of the existing Accepted Limits. Preserve the behavior description of the first case and the opt-in design of the check.

## Requirements
- `REQ-001`: Reword the second detection case so it states that the case is a documented limit of the automated check, detected only by manual review, without calling it follow-up work.
- `REQ-002`: Add the case to `Accepted Limits` with current behavior stated factually, Owner `Repository owner (reviewed quarterly)`, a rationale and the condition that would justify implementing it.
- `REQ-003`: Update the `GV-017` row so its Follow-up column states the same classification and the Status column stays `Existing` (the matrix defines no other Status value, and the implemented first case keeps the row `Existing`).
- `REQ-004`: Keep `Follow-up Work Needed` consistent with the final classification and leave the documentation checkers without findings.

## Implementation Target Files
**Freeze status**: Frozen (validated by `issue-to-plan` Step 8's
Implementation Target Files Validation — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Governance documentation-checks rules | Reword the second detection case, add the Accepted Limit, align the `GV-017` row | REQ-001, REQ-002, REQ-003, REQ-004; AC-1 to AC-4 | The removed-name section ends "Not yet implemented (follow-up)"; `### Follow-up Work Needed` says none is tracked; `## Accepted Limits` lists two items; the `GV-017` row reads "Opt-in by design (--check-removed-names); not promoted to default-on" (checked in Step 3) | N/A: documentation-only; validated by the documentation checkers under Tests | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/check_compat_shims.py` | Confirms the second detection case is not attempted by the tool | REQ-001, REQ-002 |
| `plans/done/20260903-090945_plan.md` | Design origin of the asymmetric rule and the deferred follow-up | REQ-002 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Owner Values used by the new Accepted Limit | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): The second detection case is described once as a documented limit detected only by manual review, and no sentence calls it follow-up while `Follow-up Work Needed` says none is tracked.
- AC-2 (REQ-002): `Accepted Limits` contains the case with an Owner defined in `governance_03` Owner Values, a rationale and a re-evaluation condition.
- AC-3 (REQ-003): The `GV-017` row's Follow-up cell states the same classification as the description and `Accepted Limits`, and its Status cell remains `Existing`.
- AC-4 (REQ-004): `Follow-up Work Needed` is consistent with the classification, and the checkers under Tests pass.

## Tests
- `uv run python tools/check_docs_quality.py` (REQ-001 to REQ-004).
- `uv run python tools/check_docs_structure.py docs/00_governance/governance_04_documentation-checks.md` (REQ-004).
- `uv run python tools/check_docs_content_policy.py --strict` (REQ-001, REQ-002).
- `uv run python tools/check_docs_japanese.py` (REQ-001 to REQ-004).

## Documentation Impact
Yes. `docs/00_governance/governance_04_documentation-checks.md` changes (the verification boundary of the removed-name check and the Accepted Limits register); REQ-001 to REQ-004 drive it. All text is written in English.

## Assumptions
- Accepted Limit is the right classification; the repository owner confirms it (UNK-01). If the owner prefers a tracked follow-up, the same locations are aligned to that classification instead.
- The new Accepted Limit follows the form of the existing two (current behavior, Owner, rationale) plus a re-evaluation condition.
- Verified in `plan-to-implementation-procedure` Step 3a: the existing two Accepted Limits use the Owner text `Repository owner (reviewed quarterly)`, which begins with the `Repository owner` value of `governance_03` Owner Values; the new item reuses that exact text. The `GV-017` Status cell is `Existing` and the matrix legend defines no other Status value. The unimplemented case is stated as not attempted in a `tools/check_compat_shims.py` comment (`check_removed_name_reintroduction()` area).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Accepted Limit or tracked follow-up for the second detection case? | No stated owner decision | Record the repository owner's decision on this plan before the edit, per the sign-off channel of `rules/coding.md` Explicit sign-off gates | False |
| UNK-02 | Is the re-evaluation condition time-based (quarterly review) or event-based? | No stated preference | Use "reviewed quarterly" with an event condition (a stale name found by manual review) unless the owner decides otherwise | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Modify | Medium | N/A | N/A | not applicable (rsynced) |

## Design
- Path A: one documentation file, no public interface, no schema. Validation baseline is `N/A: no Python target`.
- Decision: Accepted Limit rather than tracked follow-up. Rationale: the case needs a context-aware analysis of whether a current-specification section presents a name as production; the design plan deferred it and no issue was ever filed.
- The `GV-017` row keeps Status `Existing` and extends its Follow-up cell to point to `Accepted Limits`; its other cells are unchanged.
- Blast radius: the document is referenced by 24 files and had 49 commits in 30 days, so the edit is small and committed once.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Edit the document**
   - [ ] Reword the second detection case (REQ-001; `docs/00_governance/governance_04_documentation-checks.md`)
   - [ ] Add the Accepted Limit (REQ-002; `docs/00_governance/governance_04_documentation-checks.md`)
   - [ ] Update the `GV-017` row and confirm `Follow-up Work Needed` (REQ-003, REQ-004; `docs/00_governance/governance_04_documentation-checks.md`)
2. **Phase 2: Verification (no deployment)**
   - [ ] Run the checkers under Tests and confirm no finding (REQ-004; `docs/00_governance/governance_04_documentation-checks.md`). No `scripts/` or `config/` file changes, so no deploy step applies.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Documentation checks | `check_docs_quality.py`; `check_docs_structure.py` (changed file); `check_docs_content_policy.py --strict`; `check_docs_japanese.py` | No finding |

## Risks
- **Risk**: The owner prefers a tracked follow-up, so the Accepted Limit wording is wrong → **Mitigation**: Confirm UNK-01 before editing; the edit touches four known locations only.
- **Risk**: The document is edited by other work (49 commits in 30 days) → **Mitigation**: Make one small commit and re-run the checkers after any sync.
- **Risk**: The new wording introduces forbidden implementation-location content → **Mitigation**: Run `check_docs_content_policy.py --strict`.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document (second case, Accepted Limit, `GV-017` row) | Completed | — | 20261027-123803 |  |
| 2 | Run the documentation checkers (no deployment) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261027-111308_01_docs_00_governance_governance_04_documentation-checks.md.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-101728_govrev001_governance-followup-state-conflict.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-103907
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (rewrite the sentence); Problem | `docs/00_governance/governance_04_documentation-checks.md` | Phase 1 | AC-1 | `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes (add the Accepted Limit); Constraints | `docs/00_governance/governance_04_documentation-checks.md` | Phase 1 | AC-2 | `check_docs_content_policy.py --strict` | Confirmed by repository evidence |
| REQ-003 | Required Changes (update the `GV-017` row) | `docs/00_governance/governance_04_documentation-checks.md` | Phase 1 | AC-3 | `check_docs_quality.py` | Explicit in issue |
| REQ-004 | Required Changes (keep Follow-up Work Needed consistent); Acceptance Criteria | `docs/00_governance/governance_04_documentation-checks.md` | Phase 1, Phase 2 | AC-4 | Checkers listed under Tests | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-111308 -->
# Implementation Procedure: DOC-005 Update ADR-012 Known Deviations section

## Goal

Update `ADR-012-git-mcp-server-side-write-enforcement.md`'s Known Deviations section: remove `GIT-001` and `GIT-002` as unqualified open gaps; leave Status field unchanged (`Proposed`). Also check the Verification section for stale test-existence claims and correct them if found.

## Scope

- Remove `GIT-001` from Known Deviations section (DOC-005 REQ-005)
- Remove `GIT-002` from Known Deviations section (DOC-005 REQ-005)
- Leave ADR-012's Status field unchanged (DOC-005 REQ-006)
- Check Verification section for stale test-existence claims (UNK-01)

## Assumptions

- **Corrected during Step 3 adversarial verification (this cycle)**: the
  plan's cited line numbers are stale — `Known Deviations` is now at line 208
  (not 176-182), with the `GIT-001`/`GIT-002` bullets at lines 213-214 (not
  181-182). The file has been edited since this procedure was generated (the
  `MCP-004` bullet's wording has also changed to describe a config
  floor-check/preview-formatting gap, unrelated to `GIT-001`/`GIT-002`). The
  `GIT-001`/`GIT-002` bullet text itself is unchanged and still matches this
  document's Details section verbatim, so the edit target is unaffected —
  only the line-number references were stale.
- The plan's claim that ADR-012's Status=Proposed is correct (re-confirmed:
  `## Status` section states `Proposed`).
- The plan's claim that the Verification section may have stale
  test-existence claims needs checking (UNK-01) — **resolved in this cycle**:
  `rg -n "GIT-001|GIT-002"` against the full file finds only the two Known
  Deviations bullets being removed; no other section (Verification or
  otherwise) references `GIT-001`/`GIT-002`, confirming the Method section's
  own note that no correction is needed there.

## Design decisions

- Remove the two Known Deviations entries for `GIT-001` and `GIT-002` — the adversarial verification confirms these gaps are closed.
- Do NOT change ADR-012's Status field — that is an owner decision tied to NC-019's residual scope.
- Check the Verification section before editing: if it references `GIT-001`/`GIT-002` as open gaps requiring future test coverage, correct those references too.

## Alternatives considered

- Replace the entries with "Resolved — see DOC-005" instead of removing — rejected because the Known Deviations section should only list currently-open deviations, not resolved ones.
- Change ADR-012's Status to Accepted alongside removing the gaps — rejected because the plan explicitly forbids changing the Status field (REQ-006).

## Implementation

### Target file

`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`

### Procedure

#### Phase 1: Preparation

1. Read the full Verification section of ADR-012 to check for stale test-existence claims referencing `GIT-001`/`GIT-002` (UNK-01)
2. Confirm ADR-012's Status field = Proposed (line 15)

#### Phase 2: Core Logic Implementation

3. Remove `GIT-001` Known Deviation entry (line 181): `- **Known Issue**: GIT-001 — git_checkout/git_pull do not reject dirty worktree or detached HEAD before write operations.`
4. Remove `GIT-002` Known Deviation entry (line 182): `- **Known Issue**: GIT-002 — postcondition verification (branch/HEAD confirmation, conflict detection) missing after write operations.`
5. If Verification section has stale claims about `GIT-001`/`GIT-002`, correct them in the same edit pass
6. Ensure ADR-012's Status field remains `Proposed` (do not touch line 15)

#### Phase 3: Deployment & Verification

7. Manual verification — re-read the affected sections to confirm edits are accurate and consistent (AC-003, AC-004)

### Method

- The Known Deviations section at lines 176-182 currently lists five items. Lines 181-182 reference `GIT-001` and `GIT-002` which are now resolved per DOC-005 target row 1.
- The Verification section (lines 147-155) lists automated tests for INV-01 through INV-03 and manual review for MCP-005 audit target fix. No direct reference to `GIT-001`/`GIT-002` in this section — no correction needed here.
- The Security Consequences subsection (line 115) mentions "Requires fixing the audit `target` field (MCP-005)" — this is separate from `GIT-001`/`GIT-002` and should remain.

### Details

#### Known Deviations section update (**corrected during Step 3 adversarial
verification**: current content is at lines 208-214, not the plan's cited
176-182; the `MCP-004` bullet's wording has also changed since the plan/this
procedure were written — irrelevant to this document's scope, quoted below
as-is for an accurate before/after record):

Current content:
```markdown
## Known Deviations

- **Known Issue**: MCP-003 — no protected-branch/Force-Push guard; confirmed option-injection exploit via `branch`/`remote`.
- **Known Issue**: MCP-004 — effective risk below HIGH for git tools can occur if config is downgraded (no floor check); approval-screen preview for git tools falls through to generic JSON dump; no end-to-end test exercises the shipped config through the actual approval flow.
- **Known Issue**: MCP-005 — audit `target` field likely always empty due to a key-name mismatch.
- **Known Issue**: GIT-001 — `git_checkout`/`git_pull` do not reject dirty worktree or detached HEAD before write operations.
- **Known Issue**: GIT-002 — postcondition verification (branch/HEAD confirmation, conflict detection) missing after write operations.
```

New content (remove last two bullet points; `MCP-003`/`MCP-004`/`MCP-005` untouched):
```markdown
## Known Deviations

- **Known Issue**: MCP-003 — no protected-branch/Force-Push guard; confirmed option-injection exploit via `branch`/`remote`.
- **Known Issue**: MCP-004 — effective risk below HIGH for git tools can occur if config is downgraded (no floor check); approval-screen preview for git tools falls through to generic JSON dump; no end-to-end test exercises the shipped config through the actual approval flow.
- **Known Issue**: MCP-005 — audit `target` field likely always empty due to a key-name mismatch.
```

## Compatibility considerations

- No source-code compatibility impact — documentation-only change.
- Other documents referencing `GIT-001`/`GIT-002` as open in ADR-012 context will be consistent once all DOC-005 rows are applied.

## Security considerations

- Low risk: documentation correction only. Removing resolved Known Issues from the Known Deviations section improves accuracy of the security posture assessment.

## Rollback considerations

- Simple revert: restore the two removed bullet points. No operational impact since no code changes are involved.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` | Manual review: verify Known Deviations no longer lists GIT-001/GIT-002 as open gaps; Status=Proposed preserved | Manual read | Known Deviations corrected; Status unchanged |

## Completion criteria

- Known Deviations section no longer lists `GIT-001` as an open gap (REQ-005)
- Known Deviations section no longer lists `GIT-002` as an open gap (REQ-005)
- ADR-012's Status field remains `Proposed` (REQ-006)

## Out of scope

- Updating Known Issues doc entries for GIT-001/GIT-002 (separate target file row)
- Updating security policy doc's Git MCP bullet (separate target file row)
- Changing ADR-012's Status field (owner decision tied to NC-019)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260831-110530 | 20260831-110530 | Corrected during Step 3 adversarial verification: cited line numbers were stale (Known Deviations moved to line 208; MCP-004's wording changed, unrelated) — removed the two `GIT-001`/`GIT-002` bullets by exact text match, unaffected by the line-number drift. Confirmed `Status: Proposed` unchanged and no Verification-section references to `GIT-001`/`GIT-002` existed (UNK-01 resolved: none found). |
| 2 | Add or update tests per Validation plan | Completed | 20260831-110530 | 20260831-110530 | Not required — documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260831-110530 | 20260831-110530 | Not required — documentation-only change; ran `tools/check_docs_structure.py`/`check_docs_quality.py` instead |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260831-110530 | 20260831-110530 | This document's Target file *is* the documentation edit. Structure check found 2 pre-existing issues (Front Matter missing 'tags', missing '## Keywords') confirmed via `git stash` comparison to predate this edit — left as-is, out of scope. |

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
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: issues/20260828-161729_doc005_git001_git002_stale_open_status.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-121751_doc005_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-201308
- **Related target files**: docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md

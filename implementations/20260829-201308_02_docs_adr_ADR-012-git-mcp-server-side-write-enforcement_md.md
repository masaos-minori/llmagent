# Implementation Procedure: DOC-005 Update ADR-012 Known Deviations section

## Goal

Update `ADR-012-git-mcp-server-side-write-enforcement.md`'s Known Deviations section: remove `GIT-001` and `GIT-002` as unqualified open gaps; leave Status field unchanged (`Proposed`). Also check the Verification section for stale test-existence claims and correct them if found.

## Scope

- Remove `GIT-001` from Known Deviations section (DOC-005 REQ-005)
- Remove `GIT-002` from Known Deviations section (DOC-005 REQ-005)
- Leave ADR-012's Status field unchanged (DOC-005 REQ-006)
- Check Verification section for stale test-existence claims (UNK-01)

## Assumptions

- The plan's claim that lines 181-182 still list both `GIT-001` and `GIT-002` as open gaps is correct (verified in this cycle)
- The plan's claim that ADR-012's Status=Proposed is correct (line 15 confirmed)
- The plan's claim that the Verification section may have stale test-existence claims needs checking (UNK-01)

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

#### Known Deviations section update (current content at lines 176-182):

Current content:
```markdown
## Known Deviations

- **Known Issue**: MCP-003 — no protected-branch/Force-Push guard; confirmed option-injection exploit via `branch`/`remote`.
- **Known Issue**: MCP-004 — approval tier for these tools falls back to `MEDIUM` (`y/N`) rather than the documented `HIGH` (full-word `yes`).
- **Known Issue**: MCP-005 — audit `target` field likely always empty due to a key-name mismatch.
- **Known Issue**: GIT-001 — `git_checkout`/`git_pull` do not reject dirty worktree or detached HEAD before write operations.
- **Known Issue**: GIT-002 — postcondition verification (branch/HEAD confirmation, conflict detection) missing after write operations.
```

New content (remove last two bullet points):
```markdown
## Known Deviations

- **Known Issue**: MCP-003 — no protected-branch/Force-Push guard; confirmed option-injection exploit via `branch`/`remote`.
- **Known Issue**: MCP-004 — approval tier for these tools falls back to `MEDIUM` (`y/N`) rather than the documented `HIGH` (full-word `yes`).
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Not required — documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Not required — documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Not applicable |

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

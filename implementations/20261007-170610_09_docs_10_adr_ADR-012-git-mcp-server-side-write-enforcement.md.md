# Implementation Procedure

## Goal

Update `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md` to reflect the
Plan's resolution of MCP-002 and the pending status of MCP-004, and to refresh the
INV-01..INV-04 verification-status entries against the new allow-list ref validation and
destination-based protected-branch decision. Driven by `REQ-001` (allow-list ref
validation) and `REQ-002` (destination-based protected-branch decision).

## Scope

Modifies only `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`. The
underlying code changes live in `scripts/mcp_servers/git/git_service.py` and
`scripts/mcp_servers/git/repository_state.py` (own documents). This document describes
ONLY the prose updates to this ADR.

## Assumptions

- The ADR is updated in the implementation phase (after the code lands), so invariant
  and deviation descriptions match post-change behavior.
- The ADR's existing structure (Invariants, Automated Tests, Known Deviations) is
  retained; entries within are refreshed, not restructured.

## Design decisions

- **Known Deviations: record MCP-002 resolved, MCP-004 pending.** MCP-002 (the
  `branch`-required contract contradiction) is resolved by REQ-004; MCP-004 remains
  open (force-push via `branch` was the threat, now closed server-side, but the
  broader "no technical Force-Push block" deviation persists by design). Add explicit
  entries rather than assuming they exist.
- **Invariant verification: tie each of INV-01..INV-04 to the new controls.** INV-01
  (ref/remote allow-list), INV-03 (destination-based protected-branch rejection) get
  the new tests; INV-02/INV-04 are unchanged.

## Alternatives considered

- **Update only Known Deviations and leave the Invariants section untouched.**
  Rejected: the plan explicitly requires refreshing INV-01..INV-04 verification status,
  and INV-01/INV-03 now map to new controls that the existing test list does not cover.

## Implementation

### Target file

`docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`

### Procedure

1. Refresh the "Automated Tests" invariant verifications (INV-01, INV-03).
2. Update "Known Deviations" (MCP-002 resolved, MCP-004 pending).

### Method

#### Step 1 — "Automated Tests" invariant verifications (lines 168-176)

- **INV-01 row (line 169):** the current test list (`test_is_safe_ref`,
  `test_git_pull_unsafe_remote`, `test_git_show_unsafe_ref`) covers the old
  leading-`-`-only check. Add the allow-list tests (`test_git_service_dispatch.py`
  allow-list rejection suite; Test 1) that reject `+main`, `feature:main`,
  `HEAD:main`, `refs/heads/main`, `main~1`, `main..`, `a b`, `a\b`, `a@{1}`, `[x]`,
  `\0`, `HEAD` and malformed remotes. Note read-tool ref tests remain for the
  option-injection-only check.
- **INV-03 row (line 171):** add the destination-based protection tests
  (`test_repository_state.py::TestStage3DestinationProtection`;
  `test_git_service_dispatch.py::TestDestinationBasedProtection`) that reject a
  protected destination reached directly through the pipeline (pre-pipeline check
  bypassed) and allow checkout away from a protected branch. Keep the existing
  protected-branch test names.
- **INV-02 / INV-04 rows (lines 170, 174):** unchanged — no `force` field remains;
  approval-state independence is unchanged.

#### Step 2 — "Known Deviations" (lines 182-184)

The current section lists only MCP-001. Add entries for MCP-002 and MCP-004:

- **MCP-002 — Resolved.** `git_pull`/`git_push` now require a non-empty `branch`
  (REQ-004); the empty-branch default that always failed `_validate_protected("")` is
  removed. Reference REQ-004.
- **MCP-004 — Pending (closure noted).** The force-push-via-`branch` vector is now
  closed server-side: the write-tool allow-list rejects `+main` and other refspec
  forms before any GitPython call, and Stage 3 rejects a push onto a protected
  destination. Retain MCP-004 as a known deviation for the residual "no generic
  technical Force-Push block" point (no `force` field exists, so there is nothing to
  guard for ordinary pushes), noting the `branch`-vector closure under REQ-001/REQ-002.

Retain the existing MCP-001 entry.

### Details

- Verify each invariant/test reference against the landed code and test suite before
  publishing; do not cite a test that the implementation did not add.
- Preserve the ADR's citation style (`**Verifies**: INV-0N — **Type**: ... —
  **Blocking**: ...`).

## Compatibility considerations

- The ADR is a governance artifact cross-referenced in `adr-index.md` (own document);
  keep the invariant IDs (INV-01..INV-04) stable so the index link does not break.

## Security considerations

- Do not claim MCP-004 is fully closed if the residual "no generic Force-Push block"
  point remains; state precisely which vector (force-push via `branch`) is closed and
  which (generic force option) is intentionally out of scope.

## Rollback considerations

- Revert the single commit touching this ADR. No code or config is affected.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| ADR-012 inversions/deviations | Manual review against code | read `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md` + diff against landed code + tests | INV-01/INV-03 reference the new allow-list/destination tests; MCP-002 resolved, MCP-004 closure noted |

## Completion criteria

- INV-01 and INV-03 verification entries reference the new allow-list and
  destination-based protection tests.
- Known Deviations has explicit MCP-002 (resolved) and MCP-004 (pending, `branch`-
  vector closure noted) entries alongside the existing MCP-001 entry.
- Each claim matches the landed code and tests.

## Out of scope

- The allow-list validator and destination check implementation —
  `git_service.py` / `repository_state.py`, own documents.
- adr-index refresh — own document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Refresh INV-01/INV-03 automated-test verifications | Pending | — | — | REQ-001/002 |
| 2 | Update Known Deviations (MCP-002 resolved, MCP-004 pending) | Pending | — | — | REQ-004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (allow-list ref validation for write `branch`/`remote`), `REQ-002` (route protected-branch decision to destination), `REQ-004` (make `branch` required in `git_pull`/`git_push`)
- **Source issue**: `issues/20261007-153840_gitref01_fix-git-mcp-ref-validation-and-protected-branch-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261007-162035_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261007-170610
- **Related target files**: `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`

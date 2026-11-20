## Goal
Register the `git_add`/`git_commit` protected-branch INV/test gap in ADR-012 `Known Deviations`, per plan REQ-001 (register the confirmed coverage gap instead of adding an Invariant or a test).

## Scope
**Release unit**: N/A: not part of a release unit
- Replace the `Not applicable` body of `## Known Deviations` with one deviation entry. No other section of the file changes.
- Append one new `MCP-005` Known Issue entry to Part 1 of `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (verification finding V1-1, 2026-11-20): `tools/check_known_deviation_sync.py` `find_bullets_without_id` reports a Known Deviations bullet that cites no Known Issue ID as ERROR, and no Part 1 entry currently covers this gap. `governance_03` is a row of the plan's frozen `Implementation Target Files` table; the row's stated responsibility names only AAL-038, so this companion entry is recorded as a scope extension of that row.
- Re-record the `governance_03` size ceiling in `tools/check_docs_structure.py` `SIZE_EXCEPTIONS` (31908 -> 33915) (verification finding V1-2, 2026-11-20): the MCP-005 entry takes the file over the 32768-byte `MAX_SIZE` gate; the map is the established re-acceptance mechanism (precedent entries dated 2026-11-11/2026-11-12/2026-11-20 record the accepted size verbatim). This is the one non-docs file this procedure touches.

## Assumptions
- Documentation-only row: no test is added (plan Out-of-Scope), so the deviation is registered, not closed.
- The INV-11 alternative (a new Invariant for the HEAD-destination check) stays an owner decision (plan Unknowns UNK-02, non-blocking).
- Gated Plan: `tools/plan_dependency_order.py` reports this plan gated (prose) by `issues/20261117-123022_adrchk022_history-comment-removal.md` phase all; the owner chose to proceed with this Plan first (2026-11-20).

## Design decisions
- Known Deviations registration is the plan-selected route (REQ-001); the section is plain (unguarded) text, safe to edit directly.
- The entry text is single-sourced from the code artifact (`verify_authorization()` destination rule) and INV-03's current text, not restated from the review package.
- The deviation is registered as a new canonical Known Issue ID `MCP-005` (next free ID in the `MCP` prefix group; Part 1 holds MCP-001..MCP-004 and SHARED-002) and cited from the ADR bullet in the `- **Known Issue**: <ID>` label form — the form `check_known_deviation_sync.py` `_LABELED_BULLET_RE`/`_ID_LOOKAHEAD_RE` parse (the corpus's other form `- **Known Issue:**` is not extracted by `parse_adr_references`, which would leave the citation untracked).
- No volatile source line numbers are written into the ADR or ledger text; the code artifact is named by function and file path (stale line references in documents are a known drift source).

## Alternatives considered
- N/A: the new-Invariant alternative is recorded in the Plan's Unknowns (UNK-02) for the owner; it is a decision change and out of this procedure.

## Implementation
### Target file
- `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (companion, per Scope V1-1)

### Procedure
1. In `## Known Deviations` of ADR-012, replace the single line `Not applicable` with the citation bullet below (Details).
2. In `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 `### Active Items`, append the `#### MCP-005` entry below (Details) after the `#### MCP-004` entry (before `#### SHARED-002`), keeping the prefix-group order and the 17-field entry template.
3. Land both edits in the same commit as this procedure's other target-file work; the bullet and its ledger entry are one unit (dangling-citation rule).

### Method
Describe the deviation as current specification only: what the code enforces, which Invariant does not mandate it, and that no test covers it. Do not add history wording, do not touch the Scope section (the behavior is already described there), and do not add or change any Invariant, Verification row, or cited test ID. The ledger entry states only observed implementation and an owner decision path; no approval is written or simulated.

### Details
ADR-012 `## Known Deviations` bullet (adapt line-wrapping only):

- **Known Issue**: MCP-005 — The destination (HEAD) protected-branch check applied to `git_add`/`git_commit` by `verify_authorization()` in `scripts/mcp_servers/git/repository_state.py` is enforced in code but mandated by no Invariant — INV-03 names only `git_checkout`/`git_pull`/`git_push` — and has no dedicated protected-branch test. Recorded pending a maintainer decision on an Invariant for the check; not resolved. See `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1.

`#### MCP-005` entry (17 fields, MCP-001..MCP-004 form):

```markdown
#### MCP-005

- **ID:** MCP-005
- **Title:** git_add/git_commit HEAD-destination protected-branch check is mandated by no Invariant and has no dedicated test
- **Status**: open
- **Severity:** Medium
- **Area:** MCP
- **Type:** design-gap
- **Source:** adrchk021 ADR editorial defect re-verification, ADR-012 `## Known Deviations` gap scan
- **Owner:** Repository owner
- **First Found:** adrchk021 ADR editorial defect re-verification
- **Target:** `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
- **Related:** None
- **Summary:** `verify_authorization()` evaluates the protected-branch decision against the operation destination and protects the current HEAD for `git_add`/`git_commit`, but no Invariant mandates this and no dedicated protected-branch test covers those two tools.
- **Current Description:** ADR-012 INV-03 names only `git_checkout`/`git_pull`/`git_push`; the Scope section describes the destination-based protection without an Invariant obligation for `git_add`/`git_commit`.
- **Observed Implementation:** `scripts/mcp_servers/git/repository_state.py` `verify_authorization()` treats the current HEAD as the destination for `git_add`/`git_commit` and rejects it when it is a configured protected branch; the only `git_add`/`git_commit` tests are dirty-worktree reachability tests in `tests/mcp_servers/git/test_git_security_compliance.py`, not protected-branch tests.
- **Impact:** A safety-relevant enforcement runs with no Invariant mandate and no regression test; it can drift or regress silently.
- **Recommended Action:** the owner decides whether to add an Invariant for the HEAD-destination check (pending amendment via the ADR Approval Ledger) or record it as out of scope; protected-branch tests for `git_add`/`git_commit` follow whichever decision is recorded. No approval is written here.
- **Resolution Target:** maintainer decision recorded in ADR-012 (Invariant plus pending amendment, or explicit out-of-scope statement) with matching test coverage
```

## Compatibility considerations
- N/A: docs-only change; the section is outside every generated guard block, so `generate_adr_authority.py` and `generate_reference_table.py` outputs are unaffected.

## Security considerations
- Registers an enforcement-vs-governance gap for protected branches; changes no enforcement behavior.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py` — 0 errors, no new warning (the pre-existing ADR-015 L126 warning is procedure 03's target).
- `uv run python .github/run_cited_adr_tests.py` — all cited node IDs still pass (baseline re-confirmed 2026-11-20 at HEAD: "All 70 cited ADR invariant tests passed", exit 0).
- `uv run python tools/check_adr_invariant_matrix.py` — matrix rows/citations consistent.
- `uv run python tools/check_known_deviation_sync.py` — "No issues found", exit 0 (baseline re-confirmed 2026-11-20 at HEAD).
- `uv run python tools/check_docs_structure.py "docs/10_adr/*.md" "docs/00_governance/*.md"` and `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py` — pass after the V1-2 ceiling re-record.

## Completion criteria
- `Known Deviations` names the `git_add`/`git_commit` HEAD-destination check, its INV-03 exclusion, and the absent test, citing `MCP-005`; `governance_03` Part 1 contains the matching `MCP-005` entry; every other section of ADR-012 is byte-identical to before; the validation commands pass.

## Out of Scope
- Adding a new Invariant or Verification row to ADR-012; adding tests; editing `docs/10_adr/adr_01_index.md`; the adrchk022 history-text cleanup of other ADRs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-20 | 2026-11-20 | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) Implemented with V1-1 (MCP-005 companion entry in governance_03 Part 1) and V1-2 (SIZE_EXCEPTIONS ceiling 31908->33915) |
| 2 | Run the documentation checkers named in `routing.md` Tools (Validation plan) | Completed | 2026-11-20 | 2026-11-20 | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) 70/70 cited tests; check_adr_structure: only pre-existing ADR-015 L126 warning (procedure 03 target); check_known_deviation_sync/matrix/docs checkers green |

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
- **Requirement ID**: REQ-001 (register the git_add/git_commit protected-branch INV/test gap in ADR-012 Known Deviations)
- **Source issue**: issues/20261117-123021_adrchk021_adr-editorial-defects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-172527_adrchk021_adr-editorial-defects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-174933
- **Related target files**: docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md; docs/00_governance/governance_03_issue-and-uncertainty-management.md (MCP-005 companion entry, frozen-table row 5 scope extension)
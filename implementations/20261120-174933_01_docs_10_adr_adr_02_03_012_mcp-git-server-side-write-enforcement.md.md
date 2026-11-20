## Goal
Register the `git_add`/`git_commit` protected-branch INV/test gap in ADR-012 `Known Deviations`, per plan REQ-001 (register the confirmed coverage gap instead of adding an Invariant or a test).

## Scope
**Release unit**: N/A: not part of a release unit
- Replace the `Not applicable` body of `## Known Deviations` with one deviation entry. No other section of the file changes.

## Assumptions
- Documentation-only row: no test is added (plan Out-of-Scope), so the deviation is registered, not closed.
- The INV-11 alternative (a new Invariant for the HEAD-destination check) stays an owner decision (plan Unknowns UNK-02, non-blocking).
- Gated Plan: `tools/plan_dependency_order.py` reports this plan gated (prose) by `issues/20261117-123022_adrchk022_history-comment-removal.md` phase all; the owner chose to proceed with this Plan first (2026-11-20).

## Design decisions
- Known Deviations registration is the plan-selected route (REQ-001); the section is plain (unguarded) text, safe to edit directly.
- The entry text is single-sourced from the code artifact (`verify_authorization()` destination rule) and INV-03's current text, not restated from the review package.

## Alternatives considered
- N/A: the new-Invariant alternative is recorded in the Plan's Unknowns (UNK-02) for the owner; it is a decision change and out of this procedure.

## Implementation
### Target file
- `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`

### Procedure
1. In `## Known Deviations`, replace the single line `Not applicable` with a bullet registering the deviation below (Details).

### Method
Describe the deviation as current specification only: what the code enforces, which Invariant does not mandate it, and that no test covers it. Do not add history wording, do not touch the Scope section (the behavior is already described there), and do not add or change any Invariant, Verification row, or cited test ID.

### Details
Entry wording (adapt line-wrapping only):

- The destination (HEAD) protected-branch check applied to `git_add`/`git_commit` by `verify_authorization()` in `scripts/mcp_servers/git/repository_state.py` (L129-152) is enforced in code but mandated by no Invariant — INV-03 names only `git_checkout`/`git_pull`/`git_push` — and has no dedicated protected-branch test. Adding an Invariant for it is an owner decision, not recorded here.

## Compatibility considerations
- N/A: docs-only change; the section is outside every generated guard block, so `generate_adr_authority.py` and `generate_reference_table.py` outputs are unaffected.

## Security considerations
- Registers an enforcement-vs-governance gap for protected branches; changes no enforcement behavior.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py` — 0 errors, no new warning.
- `uv run python .github/run_cited_adr_tests.py` — all cited node IDs still pass (baseline 2026-11-20: 70/70).
- `uv run python tools/check_adr_invariant_matrix.py` — matrix rows/citations consistent.

## Completion criteria
- `Known Deviations` names the `git_add`/`git_commit` HEAD-destination check, its INV-03 exclusion, and the absent test; every other section of ADR-012 is byte-identical to before; the three validation commands pass.

## Out of Scope
- Adding a new Invariant or Verification row to ADR-012; adding tests; editing `docs/10_adr/adr_01_index.md`; the adrchk022 history-text cleanup of other ADRs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) |
| 2 | Run the documentation checkers named in `routing.md` Tools (Validation plan) | Pending | — | — | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) |

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
- **Related target files**: docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md

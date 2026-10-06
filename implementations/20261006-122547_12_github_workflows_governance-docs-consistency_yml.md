## Goal

Make the CI structure check blocking over `docs/**/*.md` (separate blocking step; schema stays non-blocking per UNK-01). (REQ-007 / AC-7)

## Scope

- Make the CI structure check blocking over `docs/**/*.md`
- Keep the schema variant non-blocking (`continue-on-error`)
- Add a separate blocking structural step

## Assumptions

- The current CI workflow runs the structure check with `continue-on-error: true` over `docs/*.md docs/10_adr/*.md --schema`
- Subdirectories such as `docs/22_mcp`, `docs/21_rag` are not covered
- UNK-01 recommendation: keep schema non-blocking + add a separate blocking structural step

## Design decisions

- Adopt the recommended option: keep schema non-blocking + add a separate blocking structural step
- Change the CI invocation from `docs/*.md docs/10_adr/*.md` to `docs/**/*.md`
- Add a separate blocking step for the structural checks

## Alternatives considered

- Making the schema variant blocking — rejected because schema validation has known edge cases (e.g., enum constraints on the 5 empty-list files); structural checks are deterministic and should block
- Keeping the current CI configuration — rejected because local and CI results differ

## Implementation

### Target file

`.github/workflows/governance-docs-consistency.yml`

### Procedure

1. Change the CI invocation from `docs/*.md docs/10_adr/*.md` to `docs/**/*.md`
2. Keep the schema variant non-blocking (`continue-on-error: true`)
3. Add a separate blocking structural step

### Method

- Edit the workflow file directly
- Ensure the updated text matches the new rule behavior

### Details

**Before:**
The CI workflow runs the structure check with `continue-on-error: true` over `docs/*.md docs/10_adr/*.md --schema`.

**After:**
The updated workflow:
- Runs the schema variant with `continue-on-error: true` over `docs/**/*.md --schema`
- Adds a separate blocking structural step over `docs/**/*.md`
- Both steps cover the whole `docs/` tree (not just `docs/*.md docs/10_adr/*.md`)

## Compatibility considerations

- This is a CI pipeline change — may affect CI behavior for all PRs
- The change aligns local and CI results
- Tests must be updated to cover the new behavior

## Security considerations

- No security implications — this is a CI pipeline update
- The change prevents silent acceptance of violations in CI

## Rollback considerations

- Reverting would restore the ability to silently allow body `Related Documents` headings in CI
- If the change causes regressions, the CI configuration can be adjusted

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `.github/workflows/governance-docs-consistency.yml` | CI: local == CI comparison | Run the workflow's structure step exactly as written vs default local run | Results agree |
| Full docs-tooling suite | Integration: repo passes its own checks | `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py` | All pass |

## Completion criteria

- CI structure check runs over `docs/**/*.md`
- Schema variant stays non-blocking (`continue-on-error: true`)
- Separate blocking structural step added
- Local and CI results agree
- No stale statements of the old rule remain

## Out of scope

- Any change to ADR documents or ADR rules (handled by `rel002`)
- Changing contextual links inside ordinary prose
- Removing `Reading Order`, `Related ADRs` or other purpose-specific navigation sections
- Reorganizing or renaming documents
- Changing front matter fields other than `related:`
- Adding a local gate to `.pre-commit-config.yaml`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Make CI structure check blocking over `docs/**/*.md` | Pending | — | — | REQ-007 |
| 2 | Keep schema variant non-blocking | Pending | — | — | REQ-007 |
| 3 | Add separate blocking structural step | Pending | — | — | REQ-007 |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261005-143453_rel001_consolidate-related-document-information-into-front-matter-related.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-073642_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-122547
- **Related target files**: .github/workflows/governance-docs-consistency.yml

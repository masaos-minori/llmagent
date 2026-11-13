## Goal

Update the two `check_compat_shims.py` rows and add the private-helper rows so the tool documentation matches the new behavior (REQ-006 / AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Re-read the file immediately before editing: other landed plans shift row positions (adrrev018 owns the documentation-checker rows; this row touches only the `check_compat_shims.py` rows and adds the helper rows).

## Design decisions
- Describe by scope and intent, following the existing row style; `docs/00_governance/governance_04_documentation-checks.md` needs no change because it lists scanned directories and intent, not patterns (Plan Documentation Impact).

## Alternatives considered
- Adding a new governance section for the phrase table: rejected; ownership stays with `tools/TOOL_DESCRIPTIONS.md` and the adrrev018 rules.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`
### Procedure
Re-read the file, apply the four row edits in Details, then run the sync checker.
### Method
Markdown table row edits.
### Details
- Line 84: the quick-reference `check_compat_shims.py` row: state that the checker also runs the path-scoped leftover-phrase patterns supplied by the private helper.
- Line 180: the detailed `check_compat_shims.py` row: state that `check_all` always runs `check_leftover_phrases (new)` from `tools/_compat_leftover_phrases.py (new)`, summarize the `scripts/`-centered path scoping (plus `docs/` for the user-approved phrase and `scripts/rag/` for the build_db_config bypass phrase), and that the historical-context marker set is now `legacy` and `removed`; keep every existing claim that stays true.
- Line 117: model for the new quick-reference row: add a `tools/_compat_leftover_phrases.py (new)` row in the same section as the `_contract_manifests.py` private row, category Reference generation (private) style wording (private helper).
- Line 195: model for the new detailed row: add the matching detailed entry (cannot run standalone; exports `LEFTOVER_PHRASES (new)` and `check_leftover_phrases (new)`; standard library only).

## Compatibility considerations
- Documentation-only change; `check_tool_descriptions_sync.py` gates the match between rows and the tools tree.

## Security considerations
- N/A: documentation.

## Rollback considerations
- Revert the row edits.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` reports no findings (AC-6).
- Re-running the row search finds exactly one quick-reference and one detailed row for `check_compat_shims.py` and one pair for the helper.

## Completion criteria
- The sync checker passes with the new helper rows present.

## Out of Scope
- `docs/00_governance/governance_04_documentation-checks.md` stays unchanged (REQ-006 Documentation Impact).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20261110-171157_rmcompat008_compat-checker-patterns.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122408_rmcompat008_compat-checker-patterns.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-083958
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`

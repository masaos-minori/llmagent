## Goal
Make ARCH-003 name the same six-database set as ADR-008 (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: the `current_value` and the review trigger `The four-database separation changes` of `ARCH-003`.
- `UNK-02` records that the approval path of an assumption change is a maintainer question; this edit changes text only.

## Assumptions
- `generate_adr_authority.py --check` reports no drift at baseline; ARCH-003 is not in any guarded block (checked in Step 3a with `rg ARCH-003`).

## Design decisions
- New `current_value`: `All persistent platform state is stored in local SQLite database files under the ADR-008 six-database separation (four platform domains and two non-domain stores)`; the trigger becomes `The six-database separation changes`.

## Alternatives considered
N/A: the maintainer's decisions are recorded in the Plan's Design section.

## Implementation
### Target file
`config/adr_authority.toml`

### Procedure
1. Edit the two strings in the `ARCH-003` table.
2. Run `uv run python tools/generate_adr_authority.py --check`; if it reports drift, run the generator and review the diff.

### Method
- Keep `applicable_adrs`, `validation_method`, and `owner` unchanged.

### Details
- Not a Python file; the TOML must stay valid (`uv run python -c "import tomllib; tomllib.load(open('config/adr_authority.toml','rb'))"`).

## Compatibility considerations
N/A: documentation or comment text only.

## Security considerations
N/A: no approval statement is written or simulated; pending bullets only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_adr_authority.py --check`, `uv run python tools/check_adr_authority.py`, the checkers `routing.md` Tools lists for a `docs/` edit (`uv run python tools/run_validation_gates.py` runs the ones the changed files trigger).

## Completion criteria
- ARCH-003 and ADR-008 name the same set; the generator and checkers report no drift.

## Out of Scope
- Other assumptions, generated files edited by hand.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the ARCH-003 strings (Implementation > Procedure) | Pending | — | — | |
| 2 | Run the generator check and the checkers (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142957_adrchk008_db-data-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-143801
- **Related target files**: `config/adr_authority.toml`

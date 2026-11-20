## Goal

- Break the governance_01 <-> checker header-list reference loop by exposing `check_adr_structure.py`'s normative heading constant as the single declared source, so the generator can mirror it into governance_01.

## Scope
**Release unit**: N/A: not part of a release unit

- REQ-013 (expose the normative heading constant; docstring states the single-source role).

## Assumptions
- Verified current source: the module-level `_REQUIRED_HEADINGS` tuple (line 144 area, with a comment naming governance_01 "ADR Section Header Standardization" as its source) already carries the list; check (c) in the docstring (line 18-21) defers the allowed list to a governance_01 "list" that does not enumerate it — that deferral direction is what this row reverses.
- The companion test file for this row does not exist as a frozen table row: `tests/tools/test_check_adr_structure.py` exists and must keep passing unmodified. If implementation ever requires editing it, that is an additional-target-file discovery to report `Blocked`, not a change to make.

## Design decisions
- Keep the list in place and expose it for import (`tools/generate_adr_authority.py` imports it in the generator row; import direction generator -> checker, per the Plan Design); the docstring's check (c) text is reworded to state that this constant is the normative source and governance_01's visible list is a generated mirror.
- The governance_01 citation comment above the constant is kept but reworded to match the corrected §18 anchor and mirror semantics (the §17 -> §18 fix itself belongs to the governance_01 row).

## Alternatives considered
- Moving the list into governance_01 as hand-written text and generating the checker constant from it — rejected: the checker's enforcement behavior must not become derivative of a document edit (Plan Design fixes the import direction).

## Implementation
### Target file
`tools/check_adr_structure.py`
### Procedure
- Expose the heading constant for import by the generator (public name or accessor; keep one definition site) (REQ-013).
- Reword docstring check (c) and the constant's source comment so the file states it is the single normative source and governance_01's block is generated from it (REQ-013).
### Method
- Naming/visibility change plus docstring wording; enforcement logic (headers, order, required set) unchanged.
### Details
- Downstream consumers of the derived slices (`_REQUIRED_HEADINGS[: index("Verification")]` at lines 170-172) stay unchanged; the generator consumes the same tuple.

## Compatibility considerations
- `tests/tools/test_check_adr_structure.py` imports must keep working; if the constant is renamed, update only within this file (the test file imports check functions, not the private constant — verified by reading the test file before renaming, and any import breakage is reported, not patched in the test).
- All live ADRs must keep passing `check_adr_structure.py` (AC-5 precondition).

## Security considerations
- N/A: read-only checker.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_adr_structure.py` — all existing tests keep passing unmodified.
- `uv run python tools/check_adr_structure.py` — exit 0 on the live ADR set.
- `rules/toolchain.md` static checks (ruff, mypy).

## Completion criteria
- The constant is importable by the generator row's code, the docstring names this file as the normative source, and all ADR structure checks stay green (AC-5).

## Out of Scope
- The generator's governance_01 block generation (its own row) and the governance_01 document wording (its own row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Expose the heading constant and reword the single-source wording (REQ-013) | Pending | — | — | |
| 2 | Run `check_adr_structure.py`, its test module, and the static checks | Pending | — | — | |

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
- **Requirement ID**: REQ-013 (checker as the declared single normative source)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `tools/check_adr_structure.py`

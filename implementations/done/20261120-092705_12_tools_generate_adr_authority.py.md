## Goal

- Give the generator a second output target — the governance_01 guarded `adr-section-header-list` block generated from `check_adr_structure.py`'s exposed constant — and make refusal-on-model-findings explicit for the new finding codes.

## Scope
**Release unit**: N/A: not part of a release unit

- REQ-014 (generate the governance_01 header-list block; `--check` detects its drift) — the recorded scope amendment, confirmed at plan review 20261120-091749.
- REQ-003 (refuse generation while model findings such as `EDGE_DUPLICATE` / `ADR_STATUS_INVALID` exist).

## Assumptions
- Verified current source: guard constants `GUARD_START_REFERENCE` / `GUARD_START_AUTHORITY` / `GUARD_START_CYCLES` (lines 55-68) plus `GUARD_END` (line 54); the block-name -> renderer map is at lines 146-148; the docstring already states the generator refuses to emit when the model fails the shared validation — REQ-003's job is to confirm the refusal gate runs the core's full `validate_model` (so the new codes gate it) and lock that with tests.
- governance_01 has no guard block today (verified by grep in Step 2): the new block must be inserted into the "ADR Section Header Standardization" section as part of the governance_01 row's document — this document only generates its content once that block exists; the two rows land in the same Phase 2 commit.
- Import direction is generator -> checker (the checker stays the normative source, Plan Design).

## Design decisions
- New guard id `adr-section-header-list` with a `GUARD_START_HEADER_LIST` (new) constant mirroring the existing three, so `--check` treats the governance_01 block with the same missing/diverging rules as the Index blocks.
- The renderer emits the exposed constant from `check_adr_structure.py` verbatim in the document's existing readable-list form — no formatting transformation, so a reader and the checker see identical strings.

## Alternatives considered
- Writing the list by hand into governance_01 with `--check` comparing against the constant — rejected by the Plan: a hand-written mirror drifts silently between edits; the generator is the only writer.

## Implementation
### Target file
`tools/generate_adr_authority.py`
### Procedure
- Import the heading constant exposed by `tools/check_adr_structure.py` (its procedure document) and add a `render_header_list` (new) renderer plus the `adr-section-header-list` guard constants (new), wired into the block map (REQ-014).
- Extend the write path and `--check` to cover the governance_01 target file in addition to the Index: missing block or content differing from generated output exits 1 (REQ-014).
- Confirm the pre-generation model gate reports every core finding (including `EDGE_DUPLICATE` and `ADR_STATUS_INVALID` from the core row) and refuses generation; adjust the gate only if it filters codes (REQ-003).
### Method
- Extend the existing block registry; target-file handling generalizes from one document to two (Index + governance_01).
### Details
- Generation and `--check` keep their refuse-on-diff semantics per block; a model finding aborts before any file write.
- The governance_01 block text must match exactly what the governance_01 row's inserted guard comments contain.

### Companion test files
- `tests/tools/test_generate_adr_authority.py`
  - Procedure: add tests that the generated governance_01 block equals the checker constant, that `--check` flags a hand-edited block as drift, and that generation refuses on an `EDGE_DUPLICATE` fixture model (REQ-027).
  - Validation: `uv run pytest tests/tools/test_generate_adr_authority.py` plus `uv run python tools/generate_adr_authority.py --check` reporting no drift on the live tree after both Phase 2 rows land.

## Compatibility considerations
- Blast radius: CI drift gate (GV-025) now covers one more guarded block; existing three Index blocks keep byte-identical output for an unchanged model.
- `tools/TOOL_DESCRIPTIONS.md` must describe the new behavior in the same commit (its own row, mandated by `check_tool_descriptions_sync.py`).

## Security considerations
- N/A: file-generation tool operating on repo-local docs; no network or config trust boundary changes.

## Rollback considerations
- Revert the generator commit together with the governance_01 block insertion (one Phase 2 commit); Index guarded sections are untouched by this row.

## Validation plan
- `uv run pytest tests/tools/test_generate_adr_authority.py` — block equality, drift, and refusal tests pass (AC-5).
- `uv run python tools/generate_adr_authority.py --check` — exit 0 after the governance_01 row lands.
- `rules/toolchain.md` static checks (ruff, mypy, bandit).

## Completion criteria
- The governance_01 block is generated from the checker constant and `--check` reports no drift; a model finding (any code) blocks generation (AC-5).

## Out of Scope
- The governance_01 document's guard-block insertion and wording (its own row), the constant exposure (checker row), and the tool-description rows (TOOL_DESCRIPTIONS row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `adr-section-header-list` renderer and guard wiring (REQ-014) | Completed | 20261120 | 20261120 | lands with the governance_01 row in one Phase 2 commit |
| 2 | Extend `--check` and the write path to the governance_01 target (REQ-014) | Completed | 20261120 | 20261120 | — |
| 3 | Confirm/lock refusal on all model findings incl. new codes (REQ-003) | Completed | 20261120 | 20261120 | — |
| 4 | Add the companion tests per Validation plan (REQ-027) | Completed | 20261120 | 20261120 | — |
| 5 | Run the Validation plan commands | Completed | 20261120 | 20261120 | — |

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
- **Requirement ID**: REQ-014 (generated governance_01 header list), REQ-003 (refusal on model findings)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `tools/generate_adr_authority.py`, `tests/tools/test_generate_adr_authority.py`

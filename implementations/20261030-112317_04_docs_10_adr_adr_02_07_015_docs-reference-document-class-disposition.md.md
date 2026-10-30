# Implementation Procedure: adr_02_07_015 disposition doc as manifest extension

## Goal

Describe the `registry/manifests/*.yaml` outputs of `generate_reference_table.py`
manifest mode as an extension of the ADR-015 generated-reference document class
(REQ-005: manifest mode; REQ-006 manifest set).

## Scope

**In scope:**
- One subsection in the ADR body stating: contract manifests are machine-readable
  generation outputs under the same "generated from live code, drift-checked" rule as
  the guarded Markdown blocks; the guard-block renderers now consume manifests
  (doc 05) rather than regenerating directly.

**Out of scope:**
- Any change to ADR-015 invariant text or its matrix rows (frozen per plan Excluded list).

## Assumptions
- Needs Confirmation: exact insertion point (Implementation Notes vs References section);
  `tools/check_adr_structure.py` enforces heading drift rules, so the subsection must
  sit under an existing allowed heading.

## Design decisions
- Prose only, no new headings beyond the ADR's existing structure — keeps
  `adr-reference-scoped` and `adr-structure` hooks green.

## Alternatives considered
N/A: docs-only row.

## Implementation
### Target file
`docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`

### Procedure
1. Add a short subsection under the document-class disposition text: manifest files are
   the machine-readable counterpart of generated blocks; both are drift-checked by the
   same tool (`--check` two-way, doc 05).

### Method
Docs-only edit.

### Details
- Name the seven shipped manifests (REQ-006 list) and the three deferred ones
  (REQ-007) explicitly as deferred-state.

## Compatibility considerations
Matrix row for ADR-015 references stay valid; body↔index containment (doc 02 checker)
must still pass.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py` and
  `uv run python tools/check_adr_invariant_matrix.py` green; `docs` checker sequence
  from `routing.md`.

## Completion criteria
ADR-015 body states manifests as a generation extension with the seven/deferred split,
and all ADR structure hooks pass.

## Out of Scope
All other ADR bodies; checker code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checker sequence (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`, `REQ-006` (manifest mode and manifest set described under ADR-015)
- **Source issue**: `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_adrcov001_contract-manifests-invariant-coverage.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-112317
- **Related target files**: `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`

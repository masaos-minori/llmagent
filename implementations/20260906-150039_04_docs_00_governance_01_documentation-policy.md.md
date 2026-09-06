## Goal
Add a "Canonical Source Registry" subsection to `docs/00_governance_01_documentation-policy.md`
stating the registry is the system of record for canonical-source ownership, and
that area guides must not maintain an independent hand-edited canonical-source
mapping going forward (REQ-009).

## Scope
- In scope: adding one new subsection at the end of "## Area Canonical Maps"
  (currently lines 173-224), immediately before "## Conflict Resolution Rule"
  (currently line 225).
- Out of scope: rewriting the existing Area Canonical Maps per-area Primary/Secondary
  tables themselves (lines 173-223) — this row only adds a forward-pointing
  system-of-record statement, per the Plan's own Out-of-Scope ("area-guide migration
  is `M-01-06`'s scope"); any other section of this file.

## Assumptions
- **Registry schema drift, carried forward from row 01/02's findings**: the actual
  registry file (`config/documentation_canonical_sources.toml`) uses a flat
  `decision_target`/`claim_type`/`source_paths`/`area`/`notes` schema, not this
  Plan's originally-envisioned nested-table one — this row's new subsection describes
  the registry's *role* (system of record) and *file location*, not its field-level
  schema, so it is unaffected by that drift; word it generically enough that it
  remains accurate regardless of which schema row 02 ultimately validates against.
- This row's addition is independent of row 02's (`tools/check_canonical_source_registry.py`)
  actual implementation status — the policy statement ("area guides must not
  maintain independent mappings going forward") is true prescriptively regardless of
  whether the validating tool already exists.

## Design decisions
- Place the new subsection at the end of "## Area Canonical Maps" rather than as a
  new top-level `##` section — keeps it adjacent to the hand-maintained tables it
  describes as being superseded, consistent with how `M-01-02`'s "Recency Is Not
  Authority" subsection (a sibling `M-01` Plan, `plans/done/20260905-165006_plan.md`)
  was placed adjacent to the section it qualifies.
- State the registry's file location (`config/documentation_canonical_sources.toml`)
  by name, not by field-level schema detail — the schema itself is documented in the
  registry file's own comments / the validating tool's docstring (row 02), not
  duplicated here, per `skills/DESIGN.md`'s "reference, don't duplicate" pattern.

## Alternatives considered
- Describe the registry's exact field schema inline in this subsection: rejected —
  given the confirmed three-way schema drift (row 01/02), inlining specific field
  names here risks this document going stale again the moment the schema question is
  finally reconciled; a role-and-location statement is more durable.

## Implementation
### Target file
`docs/00_governance_01_documentation-policy.md`

### Procedure
1. Re-read "## Area Canonical Maps" (currently lines 173-224) immediately before
   editing, to re-confirm its end boundary (before "## Conflict Resolution Rule").
2. Add a new "### Canonical Source Registry" subsection at the end of "## Area
   Canonical Maps", stating: `config/documentation_canonical_sources.toml` is the
   system of record for canonical-source ownership, superseding the hand-maintained
   Primary/Secondary tables above as the authoritative mapping; area guides (each
   area's own "Canonical Source Rule(s)" section) must not maintain an independent,
   hand-edited canonical-source mapping going forward — new or changed canonical
   mappings are recorded in the registry, not restated by hand per area; migrating
   each area guide to link to or display the registry is `M-01-06`'s scope
   (forward pointer, not implemented here).

### Method
Confirmed this cycle (2026-09-06) via direct read: "## Area Canonical Maps" spans
lines 173-224 (Overview through Governance area tables), immediately followed by
"## Conflict Resolution Rule" at line 225 — matches the insertion point Design
decisions specifies. Confirmed via row 01/02's already-generated procedure documents
(read this cycle) that the registry file exists but with a different schema than
this Plan originally proposed — informs this row's decision to keep the new
subsection schema-agnostic (Assumptions).

### Details
No change to the existing per-area Primary/Secondary tables.

## Compatibility considerations
N/A: additive new subsection; no existing cross-reference to "## Area Canonical
Maps" as a whole is invalidated by appending content at its end.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `check_docs_quality.py` flags an
issue.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_01_documentation-policy.md`
- `uv run python tools/check_docs_structure.py docs/00_governance_01_documentation-policy.md`

## Completion criteria
- A "### Canonical Source Registry" subsection exists at the end of "## Area
  Canonical Maps", naming the registry file and stating the no-independent-mapping
  rule and the `M-01-06` forward pointer.

## Out of scope
- The existing per-area Primary/Secondary tables' own content.
- `config/documentation_canonical_sources.toml` — tracked in seq 01.
- `tools/check_canonical_source_registry.py` — tracked in seq 02.
- `docs/00_governance_04_documentation-checks.md` — tracked in seq 05 (this same
  cycle, a sibling row).

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/20260903-103027_m0104_introduce-machine-readable-canonical-source-registry.md
- **Source plan**: plans/20260905-165405_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-150039
- **Related target files**: docs/00_governance_01_documentation-policy.md

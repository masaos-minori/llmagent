## Goal
Replace `docs/06_eventbus_00_document-guide.md`'s "Canonical Source Rule" section's
independent restatement with a link to the two new registry entries added by REQ-005,
removing the now-duplicate hand-edited mapping per REQ-006.

## Scope
- **In-Scope**: replace lines 39-41 ("## Canonical Source Rule" section) with a reference
  to the two registry entries in `config/documentation_canonical_sources.toml`.
- **Out-of-Scope**: every other change to this file; adding/removing any other section.

## Assumptions
- REQ-005's procedure (separate implementation procedure) has already created
  `config/documentation_canonical_sources.toml` with the two entries before this
  procedure executes (Phase 0 prerequisite check).
- The replacement text should preserve the existing heading level and section structure.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Replace the entire "Canonical Source Rule" section (heading + body) rather than just
  the body paragraph — the heading itself becomes redundant when the authority claim
  is delegated to the registry.
- Link format uses relative path to `config/documentation_canonical_sources.toml` so
  readers can navigate directly to the registry entries.

## Alternatives considered
N/A: straightforward section replacement; no alternative approach applies.

## Implementation
### Target file
`docs/06_eventbus_00_document-guide.md`

### Procedure
1. Replace the "Canonical Source Rule" section (lines 39-41) with a reference to the
   two registry entries.
2. Preserve the surrounding sections ("Known Issues / Deferred Items", "Reference API")
   unchanged.

### Method
Edit via exact string replacement using Edit tool.

### Details
- Current content (lines 39-41):
  ```
  ## Canonical Source Rule

  The canonical source for behavior is the **source code** (`scripts/eventbus/`), not these documents. If there is a conflict between the documentation and the code, trust the code and update the documentation.
  ```
- Replacement content:
  ```
  ## Canonical Source Rule

  See [EventBus runtime-behavior](../config/documentation_canonical_sources.toml#eventbuscore-behavior) and [EventBus persistence-schema](../config/documentation_canonical_sources.toml#eventbuspersistence-schema) in the Canonical Source Registry.
  ```
- This removes the one duplicate hand-edited mapping this Plan resolves (REQ-006).

## Compatibility considerations
N/A: area document-guide for EventBus; no runtime/code caller.

## Security considerations
N/A.

## Rollback considerations
- Revert the edit to restore the original "Canonical Source Rule" section text.

## Validation plan
- Manual diff review confirming changes scoped to canonical-source declarations only (AC9).
- `uv run python tools/check_docs_structure.py docs/06_eventbus_00_document-guide.md` passes.
- `uv run python tools/check_docs_quality.py` on the same file passes.

## Completion criteria
- `docs/06_eventbus_00_document-guide.md` no longer independently restates the two
  migrated claims — it links to the registry instead (AC3).
- Documentation structural/quality validation passes (AC8).

## Out of scope
- Every other change to this file.
- Updating `config/documentation_canonical_sources.toml` (REQ-005, separate procedure).
- Marking stale Area Canonical Maps paths (REQ-009, separate procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-006` (update EventBus document-guide to link to registry entries instead of independently restating authority claim)
- **Source issue**: issues/20260903-103029_m0106_inventory-and-migrate-existing-canonical-source-declarations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-185329_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185329
- **Related target files**: docs/06_eventbus_00_document-guide.md

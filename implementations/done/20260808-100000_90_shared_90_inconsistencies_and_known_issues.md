## Goal
- Restructure `docs/90_shared_90_inconsistencies_and_known_issues.md` to remove overly detailed metadata field templates while explicitly preserving meaning of each known issue, why it's a problem, operational notes, fix criteria. Explicitly preserve SHARED-001 (recover_corruption propagates exception on actual page corruption) and its unresolved status.

## Scope
- **In-Scope**: 
  - `docs/90_shared_90_inconsistencies_and_known_issues.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/DB chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe known issue decisions as authoritative reference
- `rules/coding.md` "Current behavior" classification table is valid; entries must be verified against current code before removal
- SHARED-001 impact and unresolved statement must not be weakened
- Existing internal links and cross-references must remain valid after editing

## Design decisions
### Part 1 (Known Issues):
- Compress Section migration note (lines 21-26): replace with prose describing format transition at conceptual level
- Compress SHARED-001 full 17-field error template (lines 38-56): replace with prose describing known issue at conceptual level
- Compress unverified metadata fields (Owner / First Found / Target / Related): replace with prose describing verification needs
- Compress detailed implementation file/test names: replace with prose describing affected components
- Compress mechanical documentation gap classification: replace with prose describing classification rationale
- Preserve: meaning of each known issue, why it's a problem, operational notes, fix criteria
- Explicitly preserve SHARED-001 impact and unresolved status

## Alternatives considered
- Remove entire section: rejected — known issues are critical operational guidance
- Replace all tables with prose: rejected — tabular format for known issues is efficient for reference
- Remove SHARED-001 entirely: rejected — impact and unresolved status must not be weakened

## Implementation
### Target files
- `docs/90_shared_90_inconsistencies_and_known_issues.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which known issue design judgments are scattered across sections
   - Check SHARED-001 current status (still unresolved?)
   - Classify each entry according to `rules/coding.md` §「Current behavior」classification table

2. **Phase 2: Core Logic Implementation**
   - Part 1: Compress migration note (lines 21-26)
   - Part 1: Compress SHARED-001 full 17-field error template (lines 38-56)
   - Part 1: Compress unverified metadata fields (Owner / First Found / Target / Related)
   - Part 1: Compress detailed implementation file/test names
   - Part 1: Compress mechanical documentation gap classification
   - Preserve: meaning of each known issue, why it's a problem, operational notes, fix criteria
   - Explicitly preserve SHARED-001 impact and unresolved status

3. **Phase 3: Deployment & Verification**
   - Confirm SHARED-001 impact and unresolved statement not weakened
   - Confirm each entry classified per rules/coding.md five-way classification
   - Confirm cross-references to `scripts/db/recovery.py` exist
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline Python definitions with prose summaries of field semantics
- Pseudo-code removal: replace procedural pseudo-code with behavioral descriptions
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
#### Part 1 (Known Issues):
- Migration note: replace with prose: "Migration date: 2026-07-23; Source format: existing bullet format (Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference); Destination format: common template (17 fields); Note: existing entry content preserved; missing fields filled with 'unconfirmed'."
- SHARED-001: replace with prose: "recover_corruption() does not catch sqlite3.DatabaseError on actual page corruption and propagates it. ID: SHARED-001; Status: open; Severity: High; Area: Shared/DB; Type: implementation-bug; Source: db/recovery.py::_run_integrity_check(), db/recovery.py::recover_corruption(); Owner: Unassigned; First Found: unconfirmed; Target: db/recovery.py; Related: tests/integration/test_session_recovery.py. Summary: _run_integrity_check() does not catch sqlite3.DatabaseError; recover_corruption() does not return RecoveryResult. Current description: except clause catches only (sqlite3.OperationalError, ValueError, RuntimeError); DatabaseError not subclass of OperationalError so not caught. Observed implementation: sqlite3.DatabaseError raised when executing PRAGMA journal_mode=WAL, propagated unhandled to recover_corruption() caller. Impact: recover_corruption() may raise exception on physically corrupted file. Recommended Action: add sqlite3.DatabaseError (or common base sqlite3.Error) to _run_integrity_check() except clause. Resolution Notes: pending completion."
- Remove Related Documents and Keywords sections — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/db/recovery.py`, `scripts/db/models.py`, `tests/integration/test_session_recovery.py` must remain valid after restructuring
- Internal Markdown links must be verified against actual file paths in `docs/90_shared_*` directories
- No change to source code contracts — document-only modification

## Security considerations
- N/A — document-only modification, no security-sensitive content affected

## Rollback considerations
- If restructuring causes link breakage, revert to original structure and apply targeted compression instead of full rewrite
- All removed details point to source files for verification

## Validation plan
| Check | Tool | Target |
|---|---|---|
| SHARED-001 Impact and Unresolved Status | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/db/recovery.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| Five-Way Classification | Manual | Each entry classified per rules/coding.md |

## Out of scope
- Source code changes
- Test modifications
- Cross-chapter structural changes beyond this file
- Auto-generation of documentation (future work)

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-213056_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-100000
- Related target files: docs/90_shared_90_inconsistencies_and_known_issues.md

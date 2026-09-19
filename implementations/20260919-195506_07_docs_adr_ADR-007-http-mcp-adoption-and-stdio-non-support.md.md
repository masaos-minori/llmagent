## Goal
Classify `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`'s 1 real
`## Implementation Notes` bullet against `docs/00_governance_02_documentation-metadata.md`'s
Decision Categories and apply the corresponding action (REQ-001, REQ-003).

## Scope
In scope: the 1 confirmed real bullet in this file's `## Implementation Notes` section.
Out of scope: this file's other sections; any other file.

## Assumptions
Confirmed 20260919 (`plan-to-implementation-procedure` Step 3a): this file's
`## Implementation Notes` section contains exactly 1 real bullet (beyond the standard
boilerplate intro/outro): "Circuit Breaker: INV-11参照（`McpServerHealthRegistry`が実装）" —
a cross-reference to INV-11, naming `McpServerHealthRegistry` as its implementing class.

## Design decisions
Per `skills/python-design/SKILL.md`'s "Avoid implementation-reference duplication": this
bullet is a bare navigational pointer (invariant ID + implementing class name), the same
shape as the `Delete`-candidate criteria ("file/line/function-name-describable,
unambiguous from source") — but it also serves as the only place a reader lands on the
class name when following the circuit-breaker concept from this ADR's prose. Classify
against whether `## Invariants`' own INV-11 entry already names
`McpServerHealthRegistry` — if so, this bullet is pure duplication (`Delete`); if the
`## Invariants` entry only states the invariant abstractly without naming the
implementing class, this bullet carries navigation value worth retaining in a compressed
form.

## Alternatives considered
N/A: the classification mechanism is fixed by REQ-001 — no alternative scheme applies.

## Implementation
### Target file
docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md

### Procedure
1. Read the INV-11 entry in `## Invariants` to confirm whether it already names
   `McpServerHealthRegistry`.
2. Classify the bullet per the Design decisions reasoning above.
3. Apply the action (delete if fully duplicated; compress to a bare class-name
   cross-reference if not).
4. Re-run the Validation plan's checkers.

### Method
`Edit` tool — direct text edit within `## Implementation Notes`.

### Details
If retained, keep the bullet to a single short line (class name + INV cross-reference) —
do not expand it into a longer explanation, since the "why" of the circuit breaker design
belongs in `## Rationale`, not here.

## Compatibility considerations
Only `## Implementation Notes` within this file is affected.

## Security considerations
N/A: documentation-only, no credentials or runtime behavior change.

## Rollback considerations
`git checkout -- docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` reverts
this row independently.

## Validation plan
- `uv run python tools/check_docs_quality.py` — confirm no new finding for this file.
- `uv run python tools/check_docs_structure.py` — confirm no new finding for this file.
- `uv run python tools/check_adr_structure.py` — confirm no new finding for this file
  (this bullet cites no `scripts/`/`tests/` path in backtick form beyond the class name,
  so the Implementation Notes vs References drift check's applicability depends on
  whether `McpServerHealthRegistry` is treated as a path citation by that check —
  re-verify against the check's actual regex at execution time).

## Completion criteria
The bullet is classified into exactly one Decision Categories bucket and the
corresponding action applied; the 3 checkers above report no new finding for this file.

## Out of scope
This file's other sections beyond `## Implementation Notes`; any other ADR or design doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Classify and apply action for 1 real bullet |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, no test to add |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | check_docs_quality.py, check_docs_structure.py, check_adr_structure.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own Target file IS the documentation being updated |

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
- **Requirement ID**: REQ-001, REQ-003 (classify 1 real bullet; apply action)
- **Source issue**: issues/20260919-193722_impln01_audit-and-reclassify-docs-implementation-notes-items-per-existing-decision-categories.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-194628_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-195506
- **Related target files**: docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md

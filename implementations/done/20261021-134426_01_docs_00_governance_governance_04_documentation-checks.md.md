## Goal
Record the accepted enumeration-generalization detection limit (and its rationale) in `docs/00_governance/governance_04_documentation-checks.md` so the limit is captured in a canonical place rather than only in a memo.

## Scope
- Modify only `docs/00_governance/governance_04_documentation-checks.md`: add an accepted-limit note and/or a Governance Verification Matrix row documenting that non-universal-word enumeration generalizations after docs compression are not mechanically detected.
- Do not change any other governance file, checker logic, or docs content.

## Assumptions
- The owner's decision (mechanical / manual / do-nothing-with-recorded-limit) is recorded before this executes (Plan REQ-001); this procedure documents the "record the accepted limit" branch so it can be applied once decided.
- Wording stays present-tense per the Current-Specification-Only Policy.

## Design decisions
- Record the limit in `governance_04` (matrix row or an accepted-limit note) rather than a memo, satisfying REQ-004's canonical-place requirement.
- Keep the entry factual about current behavior (no mechanism exists), not aspirational.

## Alternatives considered
- Adding a mechanical check instead: out of scope for this row — that is the `tools/<existing-docs-check>.py` row (REQ-002/REQ-003).
- Inferring the owner's decision: rejected, REQ-001 makes the recorded decision a hard gate.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`

### Procedure
1. Confirm the owner's decision is recorded (REQ-001). If absent, stop and report; do not infer.
2. If the "record the accepted limit" branch is chosen, add to `governance_04`:
   - A Governance Verification Matrix row (or an accepted-limit note) stating that enumeration generalizations that drop a concrete requirement without a universal word (`each`/`every`) are not mechanically detected after docs compression, and that this is an accepted limit.
   - The owner/owner-id and the rationale (no current mechanism exists; a mechanical check is high-effort and unproven on the corpus).
3. Ensure the entry cross-references the manual review step if one is added under `prompts/08_document-sync.md`.

### Method
- Locate the Governance Verification Matrix section (confirmed present via `docs/00_governance/governance_04_documentation-checks.md`).
- Append the new row/note at the end of the relevant section, preserving the existing table structure and column order.

### Details
- The claim to record is verified at planning time: no `tools/*.py` implements the universal-word heuristic, `prompts/08_document-sync.md` has no related manual step, and `memo4.md` does not exist. The limit is "no mechanism exists", not "the current check misses some cases".
- If the owner instead chooses the mechanical branch, this row is left as the canonical home for the accepted-limit note only; the tool change lives under the `tools/<existing-docs-check>.py` row.

## Compatibility considerations
- Downstream plans reference `governance_04` as the verification contract; keeping the accepted-limit entry accurate maintains a self-consistent contract.

## Security considerations
N/A: documentation-only update of a governance matrix row; no code, secrets, or access changes.

## Rollback considerations
N/A: revert the commit that edits `governance_04_documentation-checks.md`.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Docs quality / structure / content policy / registry | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_canonical_source_registry.py` | Pass |
| Manual | Accepted-limit entry matches the recorded owner decision | Manual review | Matches REQ-001 decision |

## Completion criteria
- The accepted enumeration-generalization limit is recorded in `governance_04` with its owner and rationale.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_canonical_source_registry.py` pass.
- No other governance file or checker logic changed.

## Out of Scope
- Implementing a mechanical check (that is the `tools/<existing-docs-check>.py` row).
- Editing any `docs/` content beyond `governance_04`.
- Changing another rule's matrix row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the accepted enumeration-generalization limit + owner + rationale in `governance_04` | Pending | — | — | Branch selected by owner decision (REQ-001) |
| 2 | Run the docs quality/structure/content-policy/registry checks | Pending | — | — | check_docs_quality.py, check_docs_structure.py, check_docs_content_policy.py, check_canonical_source_registry.py |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner decision (mechanical / manual / record-limit) not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (record the accepted limit) and `REQ-004` (canonical place) — record the enumeration-generalization detection limit with owner and rationale in `governance_04`
- **Source issue**: `issues/20261021-100336_compressverify_detect-enumeration-generalization-without-universal-wording-after-docs-compression.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-124107_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-134426
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`

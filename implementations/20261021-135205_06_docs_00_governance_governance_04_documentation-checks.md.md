## Goal
Record the accepted identifier-matching detection limit (and its rationale) in `docs/00_governance/governance_04_documentation-checks.md` so the limit is captured in a canonical place rather than only in a memo.

## Scope
- Modify exactly `docs/00_governance/governance_04_documentation-checks.md`: add an accepted-limit note and/or a Governance Verification Matrix row documenting the identifier-matching gap.
- Do not change any other governance file, checker logic, or docs content.

## Assumptions
- The owner's decision is recorded before this executes (Plan REQ-001); this documents the "record the accepted limit" branch so it can be applied once decided.
- Wording stays present-tense per the Current-Specification-Only Policy.

## Design decisions
- Record the limit in `governance_04` (matrix row or accepted-limit note) rather than a memo, satisfying REQ-004's canonical-place requirement.
- State the limit factually about current behavior: `name()` function calls and `*_db_path` config keys are covered; bare snake_case variables and non-`_db_path` config keys are not mechanically verified.

## Alternatives considered
- Adding a mechanical check instead: out of scope for this row — that is the `tools/check_docs_consistency.py` row (REQ-002/REQ-003).
- Inferring the owner's decision: rejected, REQ-001 makes the recorded decision a hard gate.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`

### Procedure
1. Confirm the owner's decision is recorded (REQ-001). If absent, stop and report; do not infer.
2. If the "record the accepted limit" branch is chosen, add to `governance_04`:
   - A Governance Verification Matrix row (or an accepted-limit note) stating that bare snake_case variable references and non-`_db_path` config-key names are not mechanically verified against `scripts/` / `config/`, and that this is an accepted limit.
   - The owner/owner-id and the rationale (high false-positive risk against prose words in backticks; requires an allowlist; no observed gap on the current corpus).
3. Ensure the entry cross-references the canonical config source used if a mechanical check is later adopted.

### Method
- Locate the Governance Verification Matrix section (confirmed present via `docs/00_governance/governance_04_documentation-checks.md`).
- Append the new row/note at the end of the relevant section, preserving the existing table structure and column order.

### Details
- Verified at planning time: `check_function_references` already covers snake_case `name()` forms; `check_config_key_presence` only covers `*_db_path` keys; zero non-`_db_path` config-ish references exist on the live corpus; the only genuine gap is bare snake_case variable references (high-false-positive risk, needs an allowlist). The limit is described against current behavior, not an aspirational one.
- If the owner instead chooses the mechanical branch, this row records the implemented scope instead of a limit; the tool change lives under the `tools/check_docs_consistency.py` row. If implementing requires a file not listed in `Implementation Target Files`, that is an additional-target-file discovery — stop and report `Blocked`.

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
- The accepted identifier-matching limit is recorded in `governance_04` with its owner and rationale.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_canonical_source_registry.py` pass.
- No other governance file or checker logic changed.

## Out of Scope
- Implementing a mechanical check (that is the `tools/check_docs_consistency.py` row).
- Editing any `docs/` content beyond `governance_04`.
- Changing another rule's matrix row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the accepted identifier-matching limit + owner + rationale in `governance_04` | Pending | — | — | Branch selected by owner decision (REQ-001) |
| 2 | Run the docs quality/structure/content-policy/registry checks | Pending | — | — | check_docs_quality.py, check_docs_structure.py, check_docs_content_policy.py, check_canonical_source_registry.py |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner decision (mechanical / accept-limit) not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (record the accepted limit) and `REQ-004` (canonical place) — record the identifier-matching detection limit with owner and rationale in `governance_04`
- **Source issue**: `issues/20261021-100351_identmatch_extend-identifier-matching-to-snake_case-names-and-config-keys-in-docs-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-125149_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-135205
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`

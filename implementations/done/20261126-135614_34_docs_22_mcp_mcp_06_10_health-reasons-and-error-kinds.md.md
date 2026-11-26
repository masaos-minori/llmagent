## Goal
- Present the degraded reason codes as the closed contract vocabulary (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the reason-code catalog; the health schema section (seq 33) is out.

## Assumptions
- Verified in Step 3a: this file is the canonical home of the health reason catalog; the contract module (seq 01) defines the closed set this document must match.
- Re-checked in this cycle: `config/documentation_canonical_sources.toml` carries no entry for the health reason catalog, so the canonical-home claim rests on this document and the plan's decision, not on the registry. The code side is the closed set in the contract module, and the three names in this document match its constants.

## Design decisions
- A code outside the set is a parse failure, not a warning (REQ-004).

### Corrected in Step 3b
- The existing Availability Hint section stated "a closed set of two codes", which contradicts the contract vocabulary that adds `config_missing`. The section now reads as the two availability-hint codes of the closed vocabulary, so the two statements agree.
- The vocabulary is placed as a subsection under Health Reasons Priority, next to "Degraded Reasons Are Not Stored", and states that it is a parse-time rule for the body rather than a stored per-server reason, so it does not contradict that subsection.
- The procedure's rule not to restate the field names is honored: the section names the codes and points to the contract module as the single definition, and does not name the body fields.
- `config_missing` was added to the Keywords section, where the other two codes are already listed.
- Post-cycle fix: the bullet that named `shared.security.result_dto` was flagged by `tools/check_compat_shims.py` (removed name reintroduced as current, `shared[./]security`), so the bullet now names the owning modules without the `shared.security` spelling. The docs gates still pass.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`

### Procedure
1. State the codes as a closed vocabulary that producers may emit only.
2. State that an out-of-vocabulary code is rejected by the strict parser.

### Method
- Names must equal the constants in `scripts/shared/mcp_health_contract.py`.

### Details
- Do not restate the field names here; the constants in `scripts/shared/mcp_health_contract.py` are canonical (seq 01).

## Compatibility considerations
- N/A: existing reason descriptions stay.

## Security considerations
- N/A: documentation-only; reason codes carry no credential content.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- docs gate: `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`, `check_docs_japanese.py`; then `rules/toolchain.md`.

## Completion criteria
- The document states the rule as implemented; docs gates pass.

## Out of Scope
- Code changes and the other docs files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the document and run the docs gates (`rules/tool-gates.md`) | Completed | 20261126-194939 | 20261126-194939 | Changed file: docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md. Added the Degraded Reason-Code Vocabulary subsection (closed vocabulary, producers emit only these codes, out-of-vocabulary code is a parse failure), reconciled the existing two-code wording with the vocabulary, and added config_missing to Keywords. Docs gates pass: check_docs_quality, check_docs_structure, check_docs_content_policy --strict, check_docs_consistency --domain mcp, check_docs_japanese. Full suite pending at end of batch. |

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
- **Requirement ID**: `REQ-009` (Documentation Impact)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`
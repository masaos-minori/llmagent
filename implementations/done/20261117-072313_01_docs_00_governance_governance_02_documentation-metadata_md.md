## Goal

Add the missing `Replay` and `Idempotency` rows to the Compatibility and Lifecycle Terminology table in `docs/00_governance/governance_02_documentation-metadata.md`, distinct from Backward Compatibility and Operational Fallback, each with a category-level example that names no specific symbol and describes a behavior that exists in the repository. (`REQ-001`; AC: glossary distinguishes backward compatibility, operational fallback, replay, idempotency; examples category-level and behaviors exist in repo.)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The glossary currently holds seven terms (Backward Compatibility, Operational Fallback, Default, Lenient Parsing, Migration, Obsolete, Dead Code); the new rows extend it to nine. Verified by reading the table.
- The no-symbol rule at `governance_02:108` ("its examples describe categories and name no specific symbol") applies to the new rows; examples stay category-level.
- Replay and Idempotency behaviors exist in the repository: consumer-offset replay via a stored position (`scripts/eventbus/delivery_repo.py::get_resume_position`, `consumer_offsets` re-delivering unacked events) and idempotent duplicate handling (`scripts/shared/http_transport.py::derive_idempotency_key`, `X-Idempotency-Key`, server-side `_duplicate_cache` dedup). These anchor the examples without naming symbols.

## Design decisions
- **Append after `Dead Code`**: place the two new rows at the end of the table so the existing seven rows and their column alignment are untouched.
- **Category-level examples anchored in repo behavior**: "resuming a consumer from a stored offset and re-delivering its unacked events" (replay) and "discarding a re-sent duplicate that an idempotency key marks as already processed" (idempotency) — both describe real behaviors, name no symbol.

## Alternatives considered
- Covering replay and idempotency only via the review rule in `governance_04`. Rejected: the Issue's acceptance criteria require the glossary itself to distinguish all four categories.

## Implementation
### Target file
`docs/00_governance/governance_02_documentation-metadata.md`
### Procedure
1. Add a `Replay` row and an `Idempotency` row after the `Dead Code` row in the Compatibility and Lifecycle Terminology table, each with Term / Definition / Example columns consistent with the existing rows.
### Method
Two appended table rows; definitions distinguish replay from Operational Fallback (replay resumes from a stored position, not a per-call alternate-path decision) and idempotency from the other categories.
### Details
- `Replay`: "Resuming a consumer or stream from a stored position and re-delivering the events it had not yet acknowledged, rather than continuing from the current tip. Distinct from Operational Fallback (a per-call runtime alternate-path decision): replay restores a prior position across a reconnect." Example: "A reconnecting subscriber resumes from its last stored offset and is re-delivered the events it sent but did not acknowledge."
- `Idempotency`: "Treating a repeated, otherwise-duplicate operation as a single effect by recognizing it as a re-send of an already-processed request, rather than applying the effect again. Distinct from Backward Compatibility (interface preservation) and Operational Fallback (alternate path)." Example: "A re-sent write carrying a deterministic key is recognized as a duplicate and discarded instead of being applied twice."
- Keep both examples category-level; do not name `Last-Event-ID`, `consumer_offsets`, `X-Idempotency-Key`, or any other symbol (per `governance_02:108`).

## Compatibility considerations
N/A: additive glossary rows; no term is renamed or redefined, so existing usage is unaffected.

## Security considerations
N/A: documentation-only; no runtime path.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `governance_02` | Nine terms present; Replay/Idempotency distinct; examples category-level, no symbol; content-policy clean. | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` | All pass; no new errors. |
| Whole change | No Japanese; no removed-name reintroduction. | `uv run python tools/check_docs_japanese.py`, `check_compat_shims.py` | All pass. |

## Completion criteria
- Two new rows (`Replay`, `Idempotency`) exist after `Dead Code`, each with distinct definitions and category-level examples naming no symbol.
- The glossary now distinguishes backward compatibility, operational fallback, replay, and idempotency as separate categories.
- All named documentation checkers pass.

## Out of Scope
- Rewriting or redefining any existing glossary row.
- Adding the classification rule (that is `governance_04`, `REQ-002`).
- Rewriting EventBus wording (`REQ-003`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `Replay` and `Idempotency` rows to `governance_02` | Completed | 20261117-074751 | 20261117-074751 | Additive; append after `Dead Code` |
| 3 | Run the documentation checkers (`rules/toolchain.md`) | Completed | 20261117-074751 | 20261117-074751 | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`, `check_compat_shims.py` |

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
- **Requirement ID**: `REQ-001` (glossary distinguishes all four categories; category-level no-symbol examples)
- **Source issue**: `issues/20261116-115026_compat005_compat-fallback-terminology.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261117-000631_compat005_compat-fallback-terminology.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-072313
- **Related target files**: `docs/00_governance/governance_02_documentation-metadata.md`

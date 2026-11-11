## Goal

Bring `security_01` into line with `rag_05_07`: set the orphan-vector remediation to `rebuild_vec` and mark the embedding-dimension-mismatch row as ingest-time handling (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 226 (embedding dimension mismatch) currently says "Chunk skipped, WARNING logged"; it describes ingest-time behavior but does not label it as such.
- Line 229 (orphan vector rows) currently says "Run `ingester.py --force`".
- `security_01` is also targeted by `plans/20261111-110144_adrrev017_docs-history-wording.md`; this edit changes only the two orphan-vector/dimension-mismatch rows.
- Gated: `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md` phase all — sequence this Plan after it.

## Design decisions
- Change line 229's remediation to `rebuild_vec` (matching `rag_05_07`); drop `ingester.py --force` for this finding.
- Add an explicit "at ingest time" qualifier to the dimension-mismatch row (line 226) so the ingest-time skip-and-warn behavior is unambiguous and distinct from any startup handling.

## Alternatives considered
- Leaving `ingester.py --force` on line 229: rejected by `REQ-002`; `security_01` must agree with the single policy source.

## Implementation
### Target file
`docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Procedure
1. Edit the orphan-vector row (line 229): `Run \`ingester.py --force\`` → `rebuild_vec`.
2. Edit the dimension-mismatch row (line 226): add an explicit ingest-time qualifier to "Chunk skipped, WARNING logged".

### Method
Evidence checked: line 226 ("Chunk skipped, WARNING logged"), line 229 ("Run `ingester.py --force`"). Keep the rest of the table intact.

### Details
- No severity or trust-boundary change; only the remediation wording and the ingest-time label.

## Compatibility considerations
- N/A: documentation alignment only.

## Security considerations
- N/A: no trust-boundary or behavioral change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain overview` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- `security_01` gives `rebuild_vec` for `orphan_vec_count > 0` (no `ingester.py --force`) and labels the dimension-mismatch row as ingest-time handling (`AC-1`, `AC-2`).

## Out of Scope
- Changing which findings are Degraded or Fatal; the identity-gate wording (owned by rmcompat001/rmcompat003); other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md phase all - edits rag_05_07 wording it rewrites; sequence this Plan after it |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md phase all - sequence after it |

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
- **Requirement ID**: `REQ-001` (ingest-time dimension-mismatch labeled) and `REQ-002` (`orphan_vec_count > 0` → `rebuild_vec`)
- **Source issue**: issues/20261109-113123_adrrev013_rag-consistency-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-102935_adrrev013_rag-consistency-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-063813
- **Related target files**: `docs/91_security/security_01_architecture-and-trust-boundaries.md`

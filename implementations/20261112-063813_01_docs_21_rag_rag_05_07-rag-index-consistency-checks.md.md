## Goal

Make `rag_05_07` the single policy source for RAG index consistency findings: state startup versus ingest-time dimension-mismatch handling separately, state the failed/timed-out check behavior as the one policy, and standardize the `orphan_vec_count > 0` row on `rebuild_vec` (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current line 94 reads "`rebuild_vec` ... (or `ingester.py --force`)"; the `(or \`ingester.py --force\`)` clause is the only place in this file that still offers it for this finding.
- The dimension-mismatch startup behavior is a Fatal abort in `scripts/db/rag_consistency.py` / `scripts/agent/startup_validation.py`; ingest-time behavior skips the chunk and logs a warning.
- `rag_05_07` is also edited by `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md` (identity-gate wording) and `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md` (corpus identity); this edit touches different sentences.
- Gated: `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md` phase all — this is the file rmcompat001 rewrites; sequence this Plan after it.

## Design decisions
- Add two explicit statements to `rag_05_07`: one for ingest-time dimension mismatch (chunk skipped, warning logged) and one for startup (Fatal abort, startup stops). Do not change any severity.
- Remove the `(or \`ingester.py --force\`)` alternative from the `orphan_vec_count > 0` row (line 94), leaving `rebuild_vec` as the sole remediation.

## Alternatives considered
- Leaving the `ingester.py --force` alternative in place: rejected by `REQ-002`; operators cannot predict whether an inconsistency stops the service while two remediations coexist.

## Implementation
### Target file
`docs/21_rag/rag_05_07-rag-index-consistency-checks.md`

### Procedure
1. Locate the dimension-mismatch handling and the failed/timed-out check description (plan cites lines 22-26) and state ingest-time versus startup handling as two distinct sentences.
2. State the failed-or-timed-out check behavior as the single policy the other documents reference.
3. Edit the `orphan_vec_count > 0` row (line 94) to drop the `ingester.py --force` alternative.

### Method
Read the current severity table (lines 44-45) and the `orphan_vec_count > 0` row (line 94): replace `Run `/session rag-rebuild-vec` (or `ingester.py --force`)` with `Run `/session rag-rebuild-vec``. Add the ingest-time/startup dimension-mismatch distinction near the existing startup-handling text (lines 22-26) without altering the Degraded/Fatal classification.

### Details
- Evidence checked: line 94 currently offers `(or \`ingester.py --force\`)`; lines 44-45 severity table; lines 22-26 startup handling.
- No severity is changed (`vec != chunks` stays Degraded); only the remediation wording and the dimension-mismatch dimension are clarified.

## Compatibility considerations
- N/A: documentation clarification only; no code or behavior change.

## Security considerations
- N/A: no security-relevant behavior changes; the Fatal abort path is left untouched.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain rag` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- `rag_05_07` states ingest-time (skip + warn) versus startup (Fatal abort) dimension-mismatch handling separately, the failed/timed-out check as one policy, and no row still offers `ingester.py --force` for `orphan_vec_count > 0` (`AC-1`, `AC-2`).

## Out of Scope
- Changing which findings are Degraded or Fatal; the identity-gate or "unverifiable" wording (owned by rmcompat001/rmcompat003); any ADR or other document (each handled by its own procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md phase all - edits rag_05_07 startup paragraph it rewrites; sequence this Plan after it |
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
- **Requirement ID**: `REQ-001` (separate ingest-time/startup dimension-mismatch handling, no severity change) and `REQ-002` (standardize `orphan_vec_count > 0` on `rebuild_vec`)
- **Source issue**: issues/20261109-113123_adrrev013_rag-consistency-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-102935_adrrev013_rag-consistency-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-063813
- **Related target files**: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`

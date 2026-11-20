## Goal
- Rewrite the two migration-framed `notes` values in `config/documentation_canonical_sources.toml` so they state the current canonical role only (Plan REQ-005: delete the "candidate replacement" migration framing).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Re-run the Plan AC-1 history search on this file immediately before editing; if a note is already rewritten, skip it and record the evidence (source issue AI Implementation Instruction). Verified present on 20261120 (lines 22, 29).
- No consumer cites this file's live "candidate replacement" values (re-verified 20261120 adversarial pass: `rg -l "candidate replacement"` also matches `tests/tools/test_check_canonical_source_conflicts.py`, but only as its hardcoded pre-seq-03 `DEFECTIVE_ROWS` fixture written to a tmp registry — it never reads this file; the same file's live-registry tests assert `source_paths`/`claim_type`, not these two notes values).

## Design decisions
- Keep each remaining `notes` sentence intact after deleting only the migration clause — the clause is a migration-status statement about a future replacement decision, which the Current-Specification-Only policy bars in active config.

## Alternatives considered
- Delete the whole `notes` key on both entries — rejected: the remaining notes carry current-claim context (documentation-metadata kind per the Resolution Matrix; deploy script role) that the registry consumers document.

## Implementation
### Target file
- `config/documentation_canonical_sources.toml`

### Procedure
- Line 22 entry (`overview.architecture-overview`): delete the clause "candidate replacement for docs/architecture.md; " so the notes read "Architecture process overview; registered as a documentation-metadata claim, whose canonical source kind per the Resolution Matrix is the documentation-metadata document."
- Line 29 entry (`deployment.deploy-script`): delete the clause "; candidate replacement for deploy.sh" so the notes read "Deploy script."

### Method
- Change only the two `notes` string values; leave `decision_target`, `claim_type`, `source_paths`, `area`, and every other entry byte-identical.

### Details
- Locate the clauses at edit time with `rg -n "candidate replacement"`; do not renumber by stale line numbers.

## Compatibility considerations
- `tools/check_canonical_source_registry.py` validates schema and registered paths, not note wording; no docs file cites the deleted clauses (verified in Assumptions).

## Security considerations
- N/A: metadata wording change only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_canonical_source_registry.py` (Plan AC-4).
- `uv run pytest tests/tools/test_check_canonical_source_conflicts.py` — live-registry consumer tests (added by the Step 3a adversarial verification on 20261120: this test file reads the repo registry in `TestRegistryRowCorrectionsT12`).
- History search re-run on this file returns no hit for the Plan AC-1 pattern (`candidate replacement` included).

## Completion criteria
- Neither notes value contains migration framing; registry validation passes; every other registry field is unchanged.

## Out of Scope
- Any change to registered paths, claim types, or other registry entries; the Resolution Matrix docs themselves.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-205907 | 20261120-205955 | changed config/documentation_canonical_sources.toml (two notes clauses removed) |
| 2 | Run the validation sequence (`rules/toolchain.md`) with the registry checker named in the Validation plan | Completed | 20261120-205956 | 20261120-210852 | stale-detector clean; check_canonical_source_registry Pass; pytest test_check_canonical_source_conflicts 45 passed (live-registry tests do not pin the removed notes clauses); history re-search no hit; full-suite pending batch end |

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
- **Requirement ID**: `REQ-005` (rewrite the two migration-framed registry notes as current-role statements)
- **Source issue**: issues/20261117-123022_adrchk022_history-comment-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-201816_adrchk022_history-comment-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-202848
- **Related target files**: `config/documentation_canonical_sources.toml`
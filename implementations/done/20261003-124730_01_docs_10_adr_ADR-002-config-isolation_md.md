# Implementation Procedure — Fix CI-001 status-mismatch ERROR in ADR-002

## Goal

Remove the `- **Known Issue**: CI-001` labeled-bullet inside the `### CI-001` subsection of `docs/10_adr/ADR-002-config-isolation.md` so `check_known_deviation_sync.py` stops reporting a `[ERROR]` status mismatch for `CI-001`, while preserving the documented resolution information and the ADR decision/status/date. Result invariant: `uv run python tools/check_known_deviation_sync.py` reports no `[ERROR]` for `CI-001`.

## Scope

Single modification to `docs/10_adr/ADR-002-config-isolation.md`: delete the `- **Known Issue**: CI-001` labeled-bullet line (line 352) within the `### CI-001` subsection under `## Known Deviations`.

## Assumptions

- The `- **Known Issue**: CI-001` line is redundant because the section heading `### CI-001: ...` already identifies the Known Issue ID. Removing it does not lose any substantive information.
- Both `### CI-001` and `### CI-016` subsections carry explicit resolution evidence (`**Status**: Resolved` plus resolution description referencing the REQ-001 unit test), confirming these deviations are genuinely resolved.
- The correct fix is a doc-only restructuring of the subsection; the checker's canonical-scan and lookahead behavior is intentionally out of scope and must not change.
- `governance_03` does not hold a canonical `CI-001` entry requiring a coordinated update (verified: grep found none).

## Design decisions

- Remove the `- **Known Issue**: CI-001` labeled-bullet line entirely — the section heading already contains the ID, so this line is redundant and causes the double-read artifact.
- Preserve all other content in the subsection unchanged: summary, conflicting source, expected design, observed implementation, impact, recommended action, owner, status, and resolution target.

## Alternatives considered

- Relabeling the bullet (e.g., changing `Known Issue` to another label): rejected — unnecessary complexity when the line is redundant given the heading already carries the ID.
- Modifying `check_known_deviation_sync.py`'s `_LABELED_BULLET_RE` regex: forbidden per Constraints in the Plan.
- Suppressing the finding: rejected — the Plan requires confirmation and resolution, not suppression.

## Implementation

### Target file

`docs/10_adr/ADR-002-config-isolation.md`

### Procedure

Delete the `- **Known Issue**: CI-001` labeled-bullet line within the `### CI-001` subsection to eliminate the `open-like` signal that collides with the `resolved-like` canonical status.

### Method

Edit — targeted text deletion.

### Details

1. Baseline: confirm current state with `uv run python tools/check_known_deviation_sync.py` and expect `[ERROR]` for `CI-001`.
2. Delete the `- **Known Issue**: CI-001` line (currently line 352) within the `### CI-001` subsection.
   - Before: `- **Known Issue**: CI-001`
   - After: (line removed; subsequent bullets shift up one line)
3. Verify the subsection still documents the resolved status:
   - `**Status**: resolved` remains present
   - Resolution description referencing the REQ-001 unit test remains intact
   - No decision, invariant ID, date, or true status altered
4. Run `uv run python tools/check_known_deviation_sync.py` and expect no `[ERROR]` for `CI-001`.
5. Run `uv run pytest tests/tools/test_check_known_deviation_sync.py` and expect no regressions.
6. Run `uv run python tools/check_canonical_source_registry.py` and expect clean output.
7. Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py` and expect clean output.

## Compatibility considerations

None — documentation-only edit with no behavioral effect. The subsection retains its full semantic meaning without the redundant `- **Known Issue**: CI-001` line.

## Security considerations

None — documentation-only change.

## Rollback considerations

Simple revert via `git checkout -- docs/10_adr/ADR-002-config-isolation.md`. No code impact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_known_deviation_sync.py` | Unit (existing) | `uv run pytest tests/tools/test_check_known_deviation_sync.py` | passes, no regressions |
| `docs/10_adr/ADR-002-config-isolation.md` | Consistency (doc checker) | `uv run python tools/check_known_deviation_sync.py` | no `[ERROR]` for `CI-001`; no new findings |
| `docs/10_adr/ADR-002-config-isolation.md` | Canonical-source registry | `uv run python tools/check_canonical_source_registry.py` | clean (registered ADR entries still Accepted) |
| `docs/10_adr/ADR-002-config-isolation.md` | Structure / quality / content policy / Japanese | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py` | clean |

## Completion criteria

- Against the current repository, `uv run python tools/check_known_deviation_sync.py` reports no `[ERROR]` for `CI-001`.
- The `### CI-001` subsection still documents that the deviation is resolved, including its resolution description and `**Status**: resolved` marker.
- No new `[ERROR]`/`[WARNING]` findings introduced anywhere in the checker output.
- No decision, invariant ID, date, or true status altered.

## Out of scope

- Translation (done by `langadr001`).
- Restructuring ADRs beyond the single-line removal.
- Modifying decisions, invariants, statuses, or identifiers.
- `docs/00_governance/governance_01_documentation-policy.md` size (`docsize001`).
- Any other Known Issue besides `CI-001` and `CI-016`.
- Changing `check_known_deviation_sync.py`'s `_ID_LOOKAHEAD_RE` lookahead or canonical-scan behavior.
- Touching `governance_03` unless a resolution genuinely requires it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Investigate how `parse_adr_references`/`cross_check` match the internal `- **Known Issue**: <ID>` bullet | Pending | — | — | Addresses UNK-01 |
| 2 | (`REQ-001`) Delete the `- **Known Issue**: CI-001` labeled-bullet line in ADR-002 | Pending | — | — | |
| 3 | (`REQ-003`) Verify resolved status preserved; no decision/invariant/date changed | Pending | — | — | |
| 4 | Run Validation plan (checker + unit tests + doc checkers) | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261003-080955_kd002_adr_known_deviation_status_mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261003-091632_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-124730
- **Related target files**: docs/10_adr/ADR-002-config-isolation.md

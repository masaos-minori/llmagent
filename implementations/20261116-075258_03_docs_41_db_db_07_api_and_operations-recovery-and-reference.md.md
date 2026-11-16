## Goal
- Update `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 12 so the drill contract states the landed post-change behavior: archive-stage failures are recorded per domain (other domains still drill) and `rto_seconds` covers the isolated restore copy plus verification.

## Scope
**Release unit**: drill-harness-fidelity (Phases 1-3 of the plan; lands after `20261116-075258_01`)

- In scope: section 12 (`:156-191`; artifact field table `:179-189`) — the failure-semantics wording and the `rto_seconds` row.
- Out of scope: sections 9-11/13 (owned by plans 002/003/004, landed); the frequency/artifact-retention defer line at `:191` (drill-output retention is Plan 008's scope with its own UNK marker); any other `docs/` file.

## Assumptions
- Verification finding (2026-11-16, re-confirmed at HEAD `948d7b6d5`): section 12 spans `:156-191`; the `rto_seconds` row is `:184` ("Measured restore-and-verify wall time (restore start to completion). Measurement semantics, not a threshold.") and the `error` row is `:189` ("Populated when the drill could not complete; the artifact is still written."). The `error` row already promises an artifact on failure; REQ-001 (procedure `_01`) makes it true for the archive stage, so the docs change is a wording clarification, not a new promise.
- Plans 002/003/004 landed (commits through `693f71679`), so the section-12 line numbers above are post-landing anchors; the procedure re-reads the landed file before editing (plan Dependency Gate).
- `rto_seconds` scope widens after REQ-002 (copy included): the existing `:184` sentence must name the widened scope explicitly so a reader comparing historical artifact values doesn't misread the jump (plan Risks; "Measurement semantics, not a threshold" wording stays).
- Plan 006's deferred phase 99 test (`20261116-072110_04` procedure) targets exactly this `rto_seconds` artifact claim; this docs update and that deferred test read the same claim — no contradiction once both land.

## Design decisions
- Edit only the two affected statements (plan Documentation Impact (a)/(b)); keep the section's structure, table format, and the UNK-01 defer marker at `:191` untouched (plan cross-plan judgment: 009 edits only section 12's drill semantics; 008 later owns the retention window sentence).
- New failure-semantics wording names the exception classes as the code records them (`FileNotFoundError`, integrity/identity `RuntimeError`, sqlite3 errors) so docs match the caught set in procedure `_01` step 1 (plan Design: catch-at-domain-boundary).

## Alternatives considered
- Adding a `verification.archive_failed` row to the artifact field table: rejected for this procedure — the key is failure-path-only (UNK-01), and the `verification` row (`:188`) already says "Per-domain checks ... plus per-domain fields"; the failure sentence in (a) carries the contract. If the UNK-01 fallback (no new key) is chosen during `_01` implementation, no table change is needed either.
- Updating the retention sentence at `:191`: rejected — retention is Plan 008's scope and the UNK-01 marker defers it to the owner.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. Re-read the landed section 12 (`:156-191`) after procedure `20261116-075258_01` has landed.
2. Add one sentence to the paragraph after the artifact table intro or the `error` row (`:189`): archive-stage failures (`FileNotFoundError`, integrity/identity `RuntimeError`, sqlite3 errors) are recorded in that domain's artifact (`verification` non-passing, `error` populated, artifact still written) and the remaining domains are still drilled; the exit code stays `1` when any domain fails (REQ-001 / AC-1 wording).
3. Rewrite the `rto_seconds` row (`:184`) to: "Measured restore-and-verify wall time: the isolated restore copy plus verification, from restore start to completion. Measurement semantics, not a threshold." (REQ-002 / AC-2 wording).

### Method
- Prose/table edits only; no code blocks or commands change in section 12 (the run examples at `:160-175` and the exit-code paragraph at `:175` stay valid post-change — CLI tests confirm).

### Details
- The section-12 wording is the only place in `docs/` that describes drill artifact fields (grep 2026-11-16: the sole `rto_seconds` doc hit repo-wide is `db_07:184`), so no other docs file needs a matching edit in this cycle.

## Compatibility considerations
- Historical artifacts keep verification-only `rto_seconds` values; the rewritten row describes post-change artifacts (plan WI-009-1 follow-up already records the historical-value caveat).
- Deploy opt-in drill hook (docs `:175`, deploy row 13) reads exit codes only — unaffected.

## Security considerations
- Docs-only change; no secrets, no commands altered.

## Rollback considerations
- Revert together with the release-unit commit (`git checkout` of the unit commit covering `_01` and this document); docs must never describe pre-`_01` behavior after the unit lands.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` → no findings (plan Phase 3 step; the docs anchors and claims in section 12 match the landed code).
- Docs structure/frontmatter check for `docs/41_db/` per `routing.md` "When to run which tool" (docs change → applicable checker).
- Cross-check after `_01` lands: `grep -n "rto_seconds" docs/41_db/db_07_api_and_operations-recovery-and-reference.md` shows only the widened wording; section numbering unchanged (`## 12. Recovery Drills`, `## 13. Verification Plan`).

## Completion criteria
- Section 12 states: archive-stage failures are recorded per domain and other domains still drill (AC-1 contract), and `rto_seconds` covers the isolated copy plus verification (AC-2 contract); both statements match the landed `recovery_drill.py` behavior; `check_docs_consistency.py --domain db` clean.

## Out of Scope
- Drill cadence and artifact-retention window (`:191` defer marker; Plan 008 / UNK-01 owner decision).
- Restore/probe sections owned by plans 002/003/004 (already landed).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update section 12 failure-semantics and `rto_seconds` wording (plan Phase 3) | Pending | — | — | REQ-001, REQ-002 docs wording; gated: plans/done/20261115-041859_dbreview004_integrity-probe-side-effects.md phase all - re-read landed drill section first (004 landed at commit `693f71679`); also lands only after `20261116-075258_01` |
| 2 | Run the docs checkers (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002 (Documentation Impact wording)
- **Source issue**: issues/20261114-092858_dbreview009_drill-harness-fidelity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-051359_dbreview009_drill-harness-fidelity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-075258
- **Related target files**: docs/41_db/db_07_api_and_operations-recovery-and-reference.md

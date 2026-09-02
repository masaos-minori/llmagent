## Goal
Rewrite the CI-002 entry in `docs/90_shared_90_inconsistencies_and_known_issues.md`
(REQ-002) so it no longer cites a nonexistent ADR-011 INV-01/INV-02 invariant pair,
and instead states the investigation outcome: no production/local auto-recovery
distinction exists in any current or historical ADR-011/ADR-008 text.

## Scope
Modify exactly the `### CI-002` section (docs/90_shared_90_inconsistencies_and_known_issues.md,
currently at line 74). No other CI-xxx entry in this file is touched (Plan
Out-of-Scope).

## Assumptions
- Re-verified 2026-09-02: `### CI-002: former-ADR-011 INV-01/INV-02 — Production/local
  recovery distinction (stale reference)` is present at line 74, wording matches the
  Plan's Background/Design quotes exactly — no drift since Plan creation.
- Re-verified 2026-09-02: commits `e87db8e3`, `e886b98a`, `03f51e1b` (cited as the
  Plan's git-history evidence) all exist in this repository's history (`git cat-file -t`
  confirms each is a commit object).
- Re-verified 2026-09-02: `docs/adr/ADR-008-sqlite-4db-separation.md` line 84 states
  "対象Environment Profile: すべての環境（local/dev/production）" — no production/local
  distinction for recovery, consistent with the Plan's Design conclusion.
- Re-verified 2026-09-02: `docs/adr-index.md` line 37 confirms ADR-011 was merged into
  ADR-008 and deleted.

## Design decisions
Rewrite CI-002's body to state the confirmed absence of a production/local distinction
as fact (not as an open question needing re-investigation), and reclassify its Status
from "open ... needs re-investigation" to a closed/stale-reference classification,
per the Plan's Design section conclusion. Point the Design reference at ADR-008 (the
current owner of recovery policy) rather than the deleted ADR-011 file — this is
already CI-002's existing Design reference target, so no change is needed there.

## Alternatives considered
Raising a new ADR-008 Decision Detail for a production/local recovery distinction —
rejected per the Plan's own Design section: investigation (git history of all three
ADR-011 revisions, plus current ADR-008 text) found no evidence such a requirement was
ever real; inventing one now would contradict the investigation's own conclusion.

## Implementation
### Target file
docs/90_shared_90_inconsistencies_and_known_issues.md

### Procedure
Replace the CI-002 section's body text to state the investigation's conclusion and
close the "stale reference" status, per the Plan's Implementation steps Phase 2.

### Method
1. Locate the current CI-002 section (line 74):
   ```
   ### CI-002: former-ADR-011 INV-01/INV-02 — Production/local recovery distinction (stale reference)

   `recover_corruption()` in `db/recovery.py` does NOT distinguish between production and local environments. This entry's original wording cited an "INV-01 (production MUST NOT auto-recover without explicit operator confirmation)" / "INV-02 (local MAY auto-recover)" pair that does not correspond to any invariant in the current (pre-deletion) ADR-011 text, nor to any invariant in ADR-008 after the ADR-011 merger — ADR-008 defines no production/local distinction for recovery. Status: open / Severity: Critical / Type: stale reference — needs re-investigation. Impact: it is unclear whether a real production/local gap exists in `recover_corruption()`, or whether this entry described a since-superseded draft of ADR-011. Action: re-investigate whether a production/local distinction for auto-recovery is an intended current requirement; if so, raise it as a new decision against ADR-008, since ADR-008 (which absorbed ADR-011) contains no such invariant today. Design reference: [ADR-008](adr/ADR-008-sqlite-4db-separation.md).
   ```
2. Replace with:
   ```
   ### CI-002: former-ADR-011 INV-01/INV-02 — Production/local recovery distinction (resolved: stale reference)

   `recover_corruption()` in `db/recovery.py` does NOT distinguish between production and local environments — this is confirmed to be the correct, intended current behavior, not a gap. This entry's original wording cited an "INV-01 (production MUST NOT auto-recover without explicit operator confirmation)" / "INV-02 (local MAY auto-recover)" pair that was investigated against all three tracked ADR-011 revisions (commits `e87db8e3`, `e886b98a`, `03f51e1b`) and the current ADR-008 text: no such invariant pair was ever present. Status: resolved (stale reference, closed) / Severity: N/A / Type: stale reference. Impact: none — no production/local recovery gap exists; the entry described a citation that never corresponded to real ADR content. Action: none required; this entry is retained as a historical record of the investigation. Design reference: [ADR-008](adr/ADR-008-sqlite-4db-separation.md).
   ```

### Details
The Design reference link target (`adr/ADR-008-sqlite-4db-separation.md`) is unchanged
from the existing text — CI-002 already pointed at ADR-008, not the deleted ADR-011
file, so REQ-002's "point to ADR-008" acceptance criterion is already satisfied by the
existing link and requires no edit beyond the body text and heading/Status changes
above.

## Compatibility considerations
Documentation-only change to a Known Issues entry; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a Known Issues entry correction.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- `uv run python tools/check_docs_quality.py` (or `.venv/bin/python`/`UV_OFFLINE=1 uv run --offline python` fallback) — structural/formatting validation, per Plan Validation plan.
- `uv run python tools/check_docs_structure.py docs/90_shared_90_inconsistencies_and_known_issues.md` — file structure validation, per Plan Validation plan.

## Completion criteria
CI-002 no longer cites a nonexistent ADR-011 invariant number as an open question; its
Status reflects a resolved/closed stale reference; its Design reference continues to
point at ADR-008.

## Out of scope
Any other CI-xxx entry in this file (Plan Out-of-Scope). Re-litigating ADR-008's
already-decided recovery policy for rag/session/workflow/eventbus (Plan Out-of-Scope).

## Documentation
`docs/90_shared_90_inconsistencies_and_known_issues.md` has a `docs/00_index.md`
Document References by Task mapping (Known Issues / governance area) — this row's
change is itself the documentation update; no separate Step 5 target applies since
this workflow phase (`plan-to-implementation-procedure`) does not edit `docs/*.md`
directly. The actual edit and its validation (`check_docs_quality.py`/
`check_docs_structure.py`) are deferred to the `code-implementation` phase's Steps 3/6,
per this document's Validation plan above.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | Already implemented — CI-002 status reflects resolved stale reference |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | N/A: documentation-only, no automated test beyond the doc checkers listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | This document's own target file IS the documentation being updated |

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
- **Requirement ID**: REQ-002 (rewrite CI-002 to reflect investigation outcome)
- **Source issue**: issues/20260831-181721_adr008_02_ci002_stale_reference_reinvestigation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-120040_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-183217
- **Related target files**: docs/90_shared_90_inconsistencies_and_known_issues.md

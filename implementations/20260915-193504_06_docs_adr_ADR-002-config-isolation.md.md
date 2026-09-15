## Goal
Insert a `## Known Deviations` heading into `docs/adr/ADR-002-config-isolation.md`
immediately before line 356, per `REQ-008`, resolving the sole current
violation flagged by sibling procedure 01's check (a).

## Scope
- In scope: inserting the `## Known Deviations` heading at the precise point
  established by this Plan's adversarial verification; moving the misplaced
  Known-Deviations lead-in sentence (line 356) and the `### CI-001` block
  (lines 358-370) under it.
- Out of scope: rewriting `### CI-001`'s content — only its parent heading
  changes; `## Implementation Notes`'s own boilerplate (lines 350, 352, 354)
  is untouched and remains under `## Implementation Notes`.

## Assumptions
- Re-confirmed this pass via direct read (`sed -n '345,360p'
  docs/adr/ADR-002-config-isolation.md | cat -n`) that the exact current
  structure is:
  - Line 347: `## Implementation Notes`
  - Line 349: `現在の実装がDecisionをどのように実現しているかを簡潔に記載する。`
  - Line 351: `この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。`
  - Line 353: `行番号は記載せず、File PathとSymbol名で参照する。`
  - Line 355: `ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。` ← this is the misplaced Known-Deviations lead-in sentence
  - Line 357: `### CI-001: EventBus does NOT use ConfigLoader at all`
  - Lines 357-370: the full CI-001 block, ending with `- **Resolution Target**: ...`
  - Line 371 (blank), line 372: `## Review Triggers`
  
  Note: an earlier pass of this procedure's own drafting mistakenly computed
  355/357 from a `sed -n '340,375p' | cat -n` local-line-to-file-line
  offset-by-one arithmetic error — code-implementation Step 3a's final
  re-verification (via the `Read` tool, whose line numbers are the actual
  file line numbers directly) confirmed the Plan's original citation, 356
  (lead-in sentence) / 358 (`### CI-001`), is correct as stated. That
  drafting-time self-correction is itself retracted here; no impact on the
  actual edit either way, since it is anchored on exact text content via the
  `Edit` tool, not on line numbers.
- ADR-003's `## Known Deviations` section (confirmed precedent this session:
  "確認済みの差異なし" pattern for ADRs with zero deviations) is NOT the
  applicable precedent here, since ADR-002 has an actual existing deviation
  (CI-001) to carry over — the applicable structural precedent is instead
  ADR-004's post-docqa01-fix `## Known Deviations` section (already
  containing populated `### {ID}` entries in this same session's earlier
  work), confirming a populated Known Deviations section is a normal,
  valid state.

## Design decisions
- Insert `## Known Deviations\n\n` immediately before the lead-in sentence
  line (currently-confirmed file line 355, pending final Step 3a re-check).
- The lead-in sentence and the entire `### CI-001` block move as-is under
  the new heading — no rewording, no reformatting of CI-001's own fields
  (this session's docqa01 CI-001-format precedent already showed ADR-002's
  CI-001 fields are in the correct target format; only the section-heading
  placement was wrong).
- `## Implementation Notes` retains exactly its own three boilerplate lines
  (currently 349, 351, 353) and nothing else — becomes a heading with no
  ADR-specific content, matching the now-common post-docqa02 pattern where
  Implementation Notes across most ADRs holds only generic boilerplate plus
  (where still populated) a one-line Implementation References pointer;
  ADR-002 has no such pointer sentence currently and none is added by this
  Plan (out of this Plan's REQ-008 scope — a `docs/adr/ADR-002-config-isolation.md`
  Implementation References pointer-line check was not requested).

## Alternatives considered
- Leave `## Implementation Notes` with just the four boilerplate/lead-in
  lines and place only a NEW empty `## Known Deviations` heading before
  `### CI-001` — rejected: sibling procedure 01's check (a) only checks
  heading *presence*, not the parent of `### CI-001`, but leaving the
  lead-in sentence in Implementation Notes would keep the same substantive
  misclassification the Plan's adversarial-verification pass explicitly
  corrected (REQ-008's precise insertion point exists specifically to move
  that sentence, not just add a heading elsewhere).

## Implementation
### Target file
`docs/adr/ADR-002-config-isolation.md`

### Procedure
1. Step 3a: re-run `sed -n '340,375p' docs/adr/ADR-002-config-isolation.md
   | cat -n` immediately before editing to get the authoritative current
   line numbers and confirm no other session/commit has touched this range
   since this procedure was written.
2. Using the `Edit` tool, replace the exact text spanning from the lead-in
   sentence through the end of the CI-001 block's blank-line boundary with
   the same content, prefixed by a new `## Known Deviations\n\n` heading —
   i.e. old text:
   ```
   ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

   ### CI-001: EventBus does NOT use ConfigLoader at all
   ...
   - **Resolution Target**: Before ADR-002 moves from Proposed to Accepted status
   ```
   new text:
   ```
   ## Known Deviations

   ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

   ### CI-001: EventBus does NOT use ConfigLoader at all
   ...
   - **Resolution Target**: Before ADR-002 moves from Proposed to Accepted status
   ```
   (full CI-001 block body carried over verbatim, unchanged).

### Method
`Edit` tool, single anchored replacement using the full lead-in-sentence +
CI-001 block text as `old_string` (long enough to be unique in the file) so
the edit does not depend on exact line numbers.

### Details
- Do not alter `## Implementation Notes`'s own three boilerplate lines.
- Do not alter any field within the `### CI-001` block.
- Confirm no other `## Known Deviations` heading already exists elsewhere in
  the file (it should not — this is the violation sibling procedure 01's
  check (a) currently flags).

## Compatibility considerations
- This is the fix that makes sibling procedure 03's `adr-structure`
  pre-commit hook pass on its first live run — this row must land before or
  in the same commit as procedure 03's hook registration, per this Plan's
  own Execution Status step ordering (ADR-002 fix = step 2, before
  `.pre-commit-config.yaml` = step 3).

## Security considerations
N/A: documentation content move only, no code/behavior change.

## Rollback considerations
Revert by removing the added heading line and restoring the lead-in sentence
directly under `## Implementation Notes` — no other document references
ADR-002's internal section structure by exact heading in a way this move
would break (cross-references to CI-001 by ID are unaffected by which parent
heading it sits under).

## Validation plan
- `uv run python tools/check_adr_structure.py` — the ADR-002 finding (check
  (a) ERROR) is gone.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-002-config-isolation.md` — clean (heading order still matches the canonical ADR section-header list per `00_governance_04_documentation-checks.md` entry 11, with Known Deviations now correctly positioned as item 10, after Implementation Notes at item 9).
- `uv run python tools/check_docs_quality.py docs/adr/ADR-002-config-isolation.md` — clean.
- `uv run python tools/check_known_deviation_sync.py` — CI-001's Status/ID cross-reference remains consistent (this move does not change CI-001's field content).
- Manual diff review: only the heading insertion and section-boundary move are present — CI-001's body text is byte-identical before/after.

## Completion criteria
- `## Known Deviations` heading exists in `docs/adr/ADR-002-config-isolation.md`, positioned per the canonical ADR section order (after Implementation Notes, before Review Triggers).
- `check_adr_structure.py`'s check (a) no longer flags this file.
- CI-001's content is unchanged.

## Out of scope
- CI-001's field content/status; Implementation Notes/References pointer-line addition (not requested by REQ-008).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-194720 | 20260915-194720 | Step 3a re-count required immediately before editing — see Assumptions' noted ±1 line discrepancy Step 3a re-verification found the Plan's original line 356/358 citation correct; this procedure's own earlier drafting-time 355/357 correction was itself in error and has been retracted (see Assumptions) |
| 2 | Add or update tests per Validation plan | Completed | 20260915-194720 | 20260915-194720 | N/A: ADR content change, no test file; validated via project doc-consistency tools |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-194720 | 20260915-194720 | Documentation change — validated via `check_adr_structure.py`/`check_docs_structure.py`/`check_docs_quality.py`/`check_known_deviation_sync.py` check_adr_structure.py: ADR-002 ERROR gone (exit 0, only pre-existing ADR-004 WARNING remains); check_docs_structure.py: identical 6-issue baseline confirmed via git stash comparison (25823->25844 bytes, same finding set, no new finding); check_docs_quality.py: clean; check_known_deviation_sync.py: 14 pre-existing warnings unrelated to ADR-002/CI-001 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-194720 | 20260915-194720 | This row IS the documentation update This row IS the documentation update (docs/adr/ADR-002-config-isolation.md); no docs/00_index.md task-scope row separately applies |

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
- **Requirement ID**: REQ-008 — insert Known Deviations heading at the precise point in ADR-002
- **Source issue**: issues/done/20260914-124634_docqa05_adr-implementation-notes-lint-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-192743_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-193504
- **Related target files**: docs/adr/ADR-002-config-isolation.md
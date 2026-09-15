## Goal
Restructure `docs/adr/ADR-004-environment-failure-handling-policy.md` so it has a
single, template-standard `## Known Deviations` section (ADR-002's structured field
format), no duplicated `## Alignment with INV-01/INV-02` heading, and an internally
consistent `### Known Issues` cross-reference, per `REQ-001` through `REQ-005`
(fix the ADR's known-deviations discoverability gap and its duplicate heading).

## Scope
- In scope: remove the duplicate `## Alignment with INV-01/INV-02` occurrence; add a
  `## Known Deviations` heading in the template-standard position; move and reformat
  the four existing Known Issue-shaped entries into it; update the Completion
  Checklist line and the `### Known Issues` subsection so both stay consistent with
  the new section.
- Out of scope: any other ADR-004 content (Decision, Rationale, Invariants,
  Verification prose); `docs/00_governance_03_issue-and-uncertainty-management.md`
  (covered by the sibling procedure document for that row); adding a new automated
  checker; translating ADR-004's Japanese prose to English; fixing ADR-004's
  pre-existing, unrelated broken links (original lines 521/522/527) or front-matter
  `related` findings — see Plan `plans/20260915-145322_plan.md` Design "Pre-existing
  `check_docs_structure.py` baseline".

## Assumptions
- New field labels (`Known Issue`, `Type`, `Summary`, etc.) and any new connective
  text are written with English field labels around the existing Japanese prose,
  matching every sibling ADR's `## Known Deviations` convention and ADR-002's
  `### CI-001` entry — not a full translation of ADR-004 (Plan Assumptions).
- The two "解消済み" entries' plan references, dates, and resolution descriptions are
  reproduced verbatim inside the new field structure — only the surrounding
  container format changes (Plan `REQ-003` constraint, mirroring the source issue's
  own Constraint).

## Design decisions
- Remove the second `## Alignment with INV-01/INV-02` occurrence (originally lines
  461-467, byte-identical to the first at lines 353-359) and insert `## Known
  Deviations` in its place — this satisfies `REQ-001` and `REQ-002` in one edit,
  since the duplicate already sits exactly where the new heading belongs (between
  `## Implementation Notes` and `## Review Triggers`). The first occurrence (between
  `## Invariants` and `## Verification`) is left untouched.
- Use ADR-002's `### {ID}: {title}` field set literally for all four moved entries —
  `Known Issue`, `Type`, `Summary`, `Conflicting Source`, `Expected Design`,
  `Observed Implementation`, `Impact`, `Recommended Action`, `Owner`, `Status`,
  `Resolution Target` — per the source issue's explicit instruction, even though
  some sibling ADRs' `## Known Deviations` sections use a looser bullet style.

## Alternatives considered
- Keep the looser bullet style some sibling ADRs (e.g. ADR-006) use for `## Known
  Deviations` instead of ADR-002's structured fields — rejected because the source
  issue's own "AI Implementation Instruction" explicitly requires ADR-002's format
  and forbids inventing a different one.
- Delete the non-standard `## Alignment with INV-01/INV-02` heading entirely instead
  of merging its duplicate — rejected as out of scope; the source issue's Required
  Changes ask only to "merge into one occurrence, or rename... if the content is
  genuinely distinct," not to eliminate the heading (tracked separately as `UNK-02`
  in the Plan).

## Implementation
### Target file
`docs/adr/ADR-004-environment-failure-handling-policy.md`

### Procedure
1. Re-confirm (idempotent recheck) that both `## Alignment with INV-01/INV-02`
   occurrences remain byte-identical and that lines 469-472 still hold the four
   unstructured entries, before editing (`grep -n "^## Alignment with INV-01/INV-02"`
   should still return exactly 2 matches; `grep -n "^## Known Deviations"` should
   still return 0).
2. Remove the second `## Alignment with INV-01/INV-02` occurrence (originally lines
   461-467) in full, including its three numbered `INV-01`/`INV-02`/
   "No environment-based relaxation" bullets.
3. In its place, insert a new `## Known Deviations` heading. The project's standard
   duplicate-note line "ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する。"
   (existing line originally at 474) is reused verbatim but its position is
   corrected from this document's earlier draft: re-checking ADR-003 and ADR-006
   (both already loaded as Reference Files) during Step 3a adversarial verification
   found that both place this note at the *end* of `## Known Deviations`, immediately
   before `## Review Triggers` — not directly under the heading. Follow that
   confirmed placement: heading, then the four `### {ID}` blocks (step 4 below), then
   this note line, then the existing revision-record paragraph (originally line 476,
   already positioned after the note in the current file) unchanged.
4. Under the new `## Known Deviations` heading, add one `### {ID}: {title}` block per
   entry, in this order, each using ADR-002's exact field set (`Known Issue`, `Type`,
   `Summary`, `Conflicting Source`, `Expected Design`, `Observed Implementation`,
   `Impact`, `Recommended Action`, `Owner`, `Status`, `Resolution Target` — use
   `N/A: {short reason}` for any field the source bullet has no equivalent content
   for; never leave a field blank):
   - **Block 1** — from the original line-469 bullet ("解消済み、2026-09-04確認 —
     ADR-004-D1-profile-config-model-still-present"): `Known Issue`:
     `ADR-004-D1-profile-config-model-still-present`; `Type`: `Design Deviation
     (Resolved)`; carry the original bullet's full Japanese description into
     `Summary`/`Current Description`-equivalent content split across `Conflicting
     Source` (what `McpServerConfig`/`McpToolDiscoveryService` did before the fix),
     `Expected Design` (necessity determination must be environment-independent, per
     Decision Group 3), `Observed Implementation` (the pre-fix
     `required_in_production`/`required_in_local` branch), `Recommended Action`
     (verbatim: the `plans/done/20260903-091417_plan.md` resolution sentence,
     unchanged word-for-word per the Plan's REQ-003 constraint); `Impact`: `INV-01,
     INV-02, INV-09, INV-10, INV-14 — 解消済み` (verbatim from the original); `Owner`:
     `TBD` (matching ADR-002's `CI-001` convention, since no owner is named); `Status`:
     `Resolved (2026-09-04)`; `Resolution Target`: `N/A: already resolved`.
   - **Block 2** — from the original line-470 bullet (`production_config_validator.py`
     `is_production` severity-downgrade deviation): same field mapping approach;
     `Known Issue`: reuse the existing description as the title (no prior explicit ID
     was assigned to this one in the ADR text — assign a short, descriptive slug
     consistent with `ADR-004-D1-...`'s naming style, e.g.
     `ADR-004-D2-production-config-validator-severity-downgrade`, and note in
     `Conflicting Source` that this is a newly-assigned ID for a previously
     unnamed entry, not a renumbering of an existing one); preserve the
     `plans/done/20260903-091417_plan.md` REQ-004 resolution sentence verbatim in
     `Recommended Action`; `Status`: `Resolved (2026-09-04)`; `Resolution Target`:
     `N/A: already resolved`.
   - **Block 3** — from the original line-471 bullet (Decision #18/INV-09
     report-only item): `Known Issue`: `N/A: not registered as a governance Known
     Issue — see Recommended Action`; `Type`: `Resolved Gap` (matching ADR-006's
     `EVENTBUS-007`-style precedent for an already-confirmed item); `Summary`/
     `Expected Design`: Decision #18/INV-09's non-required-component-continuation
     requirement; `Observed Implementation`: `tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllUnreachableServers`
     already verifies this (cite the ADR's own `## Verification` section, lines
     395-399, `Status: Confirmed`); `Impact`: `N/A: not an active discrepancy`;
     `Recommended Action`: state explicitly that no new governance Known Issue was
     filed for this item, and why — "already Confirmed in this ADR's own
     Verification section; not an active discrepancy" (this is the Plan `REQ-004`
     "explicit decision not to register" record, and it must live in this ADR, not
     only in the Plan); `Status`: `Resolved`; `Resolution Target`: `N/A: already
     resolved`.
   - **Block 4** — from the original line-472 bullet (Decision #12/INV-14
     report-only item): `Known Issue`: `CI-016`; `Type`: `operational-gap`; `Summary`/
     `Expected Design`: Decision #12/INV-14's "undefined criticality must not be
     assumed non-required" requirement; `Observed Implementation`:
     `McpServerConfig.required` defaults to `True`
     (`scripts/shared/mcp_config.py:95`), a safe default, but no automated test
     verifies it and no distinct "undefined criticality" error path exists (cite the
     ADR's own Completion Checklist line, originally 555, and Manual Review line,
     originally 442); `Impact`: "a future change to the default value would silently
     violate INV-14 with no automated check to catch the regression"; `Recommended
     Action`: "tracked as `CI-016` in
     `docs/00_governance_03_issue-and-uncertainty-management.md` — see the sibling
     `implementations/20260915-150541_02_docs_00_governance_03_issue-and-uncertainty-management.md.md`
     procedure"; `Owner`: `Unassigned`; `Status`: `open`; `Resolution Target`: `Add a
     unit test asserting the `required` default and/or undefined-criticality
     handling`.
5. Update the Completion Checklist line "現行実装との差異がKnown Issueへ登録されている（一部は新規登録が必要、Known Deviations参照）"
   (originally line 558) to state registration is now complete, e.g.:
   "現行実装との差異がKnown Issueへ登録されている（`CI-016`として登録済み、`## Known
   Deviations`参照）" — keep the `- [x]` checkbox state unchanged (it was already
   checked; only the parenthetical needs updating).
6. Update `## Related Documents` > `### Known Issues` (originally lines 529-531,
   currently "- なし") to read a link to the governance doc, following ADR-006's
   precedent but with the corrected relative path (ADR-006's own equivalent link is
   itself broken — see Plan Design "`### Known Issues` cross-reference"):
   `- [Issue and Uncertainty Management](../00_governance_03_issue-and-uncertainty-management.md) — ADR-004関連のKnown Issue（CI-016）`
   Use the `../` prefix — do not copy ADR-002/006/009's unprefixed link.
7. Leave `## Implementation Notes` lines 454-455 (the memory-only
   `StartupValidationResult` aggregate note; the fixed-delay single-retry note)
   unchanged — per `REQ-007`'s analysis (this Plan's Design section), neither
   corresponds to a Decision/Invariant requirement, so both remain "Accepted current
   specification" in place. No edit is made here; this is a documented no-op, not an
   omission.

### Method
Use `Edit` (exact-string replacement) against
`docs/adr/ADR-004-environment-failure-handling-policy.md` for each of steps 2-6 above,
one edit per step, in order — do not batch multiple structural changes into a single
`Edit` call, so each change remains independently reviewable in the diff.

### Details
- Preserve every plan reference, date, and resolution sentence from the two
  "解消済み" bullets (originally lines 469-470) character-for-character inside the
  new field blocks — only their container (bullet → `### {ID}` block) and label
  structure change. Do not paraphrase, translate, or shorten the existing Japanese
  text.
- The `### {ID}` blocks for Blocks 3 and 4 are new prose (the original bullets had no
  structured fields), so write them in the mixed English-label/Japanese-content style
  already used by this ADR's own Blocks 1-2 and by ADR-002's `CI-001` — do not write
  Blocks 3-4 in a different register than Blocks 1-2 within the same section.
- Confirm no other section between `## Implementation Notes` and `## Review Triggers`
  is disturbed by the heading swap in step 2-3 (the existing boilerplate lines
  originally at 457-459 — "この章は設計判断の根拠にしない。..." — belong to
  `## Implementation Notes` and must remain there, before the new `## Known
  Deviations` heading, not be pulled into the new section).

## Compatibility considerations
N/A: documentation-only change to an ADR's own internal section structure; no
consumer code, config, or test reads `## Known Deviations` or `### Known Issues` by
section name today (confirmed: neither `tools/check_docs_structure.py` nor
`tools/check_docs_quality.py` parses ADR section content by name beyond front matter
and generic structural rules).

## Security considerations
N/A: documentation-only change; no credentials, secrets, or executable content is
introduced. The new `../00_governance_03_issue-and-uncertainty-management.md` link
must resolve to an existing repository file (verified in Validation plan below) —
an unresolved internal link is a documentation-quality defect, not a security one.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via `git checkout -- docs/adr/ADR-004-environment-failure-handling-policy.md`
(or the specific commit, once committed) if any validation step below fails and
cannot be fixed forward within the attempt bound in `AGENTS.md` Loop Prevention.
No other file depends on this file's internal section structure, so rollback carries
no cross-file cleanup.

## Validation plan
- `grep -n "^## Known Deviations" docs/adr/ADR-004-environment-failure-handling-policy.md` — expect exactly one match.
- `grep -c "^## Alignment with INV-01/INV-02" docs/adr/ADR-004-environment-failure-handling-policy.md` — expect `1`.
- `grep -n "CI-016" docs/adr/ADR-004-environment-failure-handling-policy.md` — expect at least one match (Block 4 and the `### Known Issues` cross-reference).
- `ls docs/00_governance_03_issue-and-uncertainty-management.md` from within
  `docs/adr/` context (i.e. confirm `docs/00_governance_03_issue-and-uncertainty-management.md`
  exists relative to `docs/adr/../`) — confirms the new `### Known Issues` link target resolves.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-004-environment-failure-handling-policy.md` — expect zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-004-environment-failure-handling-policy.md` — expect exactly the pre-existing 9-finding baseline recorded in the Plan (size limit, missing `## Keywords`, 3 pre-existing broken links at originally 521/522/527, 4 unresolved front-matter `related` entries) and no new finding beyond it.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — expect zero findings (both currently pass; this change does not touch `docs/adr-index.md`, their actual target).

## Completion criteria
- `## Known Deviations` exists exactly once, in the template-standard position.
- `## Alignment with INV-01/INV-02` exists exactly once.
- All four original entries (lines 469-472) appear under `## Known Deviations` as
  `### {ID}: {title}` blocks using ADR-002's field set, with the two "解消済み"
  entries' evidence text unchanged.
- The Completion Checklist line and `### Known Issues` subsection both reference
  `CI-016` and no longer read as if registration were still outstanding or as if no
  Known Issues existed.
- All Validation plan checks above pass (or, for `check_docs_structure.py`, produce
  no finding beyond the recorded pre-existing baseline).

## Out of scope
- `docs/00_governance_03_issue-and-uncertainty-management.md` (`CI-016` registration
  itself) — covered by the sibling procedure document,
  `implementations/20260915-150541_02_docs_00_governance_03_issue-and-uncertainty-management.md.md`.
- Fixing ADR-004's own pre-existing broken links (originally lines 521/522/527),
  missing `## Keywords` section, byte-size limit excess, or front-matter `related`
  findings — pre-existing, unrelated to this Plan (see Plan Design "Pre-existing
  `check_docs_structure.py` baseline").
- Reconciling `docs/adr-index.md` INV-021 against this ADR's own Completion
  Checklist wording (`UNK-01` in the Plan) — `docs/adr-index.md` is not a target
  file of this Plan.
- Adding a new automated checker for `## Known Deviations` heading presence across
  ADRs — explicitly deferred by the source issue to a companion tooling issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-150541 | 20260915-151350 | Step 3a correction (20260915-151225): fixed the "ADR本文を..." note's position in Procedure step 3 from directly-under-heading to end-of-section, per re-checked ADR-003/ADR-006 precedent Applied Procedure steps 1-7 to docs/adr/ADR-004-environment-failure-handling-policy.md via Edit; see Step 3a correction note above |
| 2 | Add or update tests per Validation plan | Completed | 20260915-151350 | 20260915-151350 | N/A: documentation-only, no automated test suite targets ADR prose — Validation plan is grep/tool checks, not pytest N/A: documentation-only, no automated test suite targets ADR prose |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-151350 | 20260915-151350 | Use this document's own Validation plan (doc checkers), not the Python `rules/toolchain.md` sequence — not applicable to a documentation-only change check_docs_quality: 0 findings; check_docs_structure: exactly the pre-existing 9-finding baseline, no new finding; check_adr_reference/check_adr_invariant_matrix: 0 findings; all grep acceptance checks passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-151350 | 20260915-151350 | N/A: this document's own target file IS the documentation being updated N/A: this document's own target file IS the documentation being updated; docs/00_index.md has no task-scope row for docs/adr/ADR-004-environment-failure-handling-policy.md requiring a further update |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005 — resolve duplicate heading, add Known Deviations, move/reformat 4 entries, update cross-references
- **Source issue**: issues/20260914-124357_docqa01_adr-004-known-deviations-section-missing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-145322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-150541
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md
## Goal

Satisfy `REQ-001`, `REQ-002`, `REQ-003` (WF-001/WF-002/WF-003 re-investigation): correct or
close WF-001, WF-002, and WF-003 in
`docs/05_agent_90_inconsistencies_and_known_issues.md` so each entry's text matches current
ADR-001 evidence, and make the document's "Operational Notes" claim ("There are currently no
open items") consistent with the result.

## Scope

Modify exactly `docs/05_agent_90_inconsistencies_and_known_issues.md`: the WF-001 entry
(current lines 57-76), the WF-002 entry (current lines 79-98), the WF-003 entry (current
lines 101-119), and the "Operational Notes" bullet (current line 49). No other section of
this file, and no other file, is touched.

## Assumptions

- Re-verified 2026-09-02 (this cycle's adversarial verification): `docs/adr/ADR-001-workflow-engine-mandatory.md`'s `## Invariants` section (lines 211-219) contains INV-01 through INV-07;
  INV-01 = "ワークフロー定義ファイルが欠落している場合、Agentの起動を中止する。" (missing workflow definition file → abort startup); INV-03 = "実行成功と検証成功は区別され、それぞれ独立して検証される。" (execution success and verification success are distinguished and independently verified); INV-05 = "ワークフロー定義ファイルの検証失敗時は起動を中止する。" (workflow definition file validation failure → abort startup).
- Re-verified: ADR-001's `## Verification` section (lines 250-253) cites
  `test_execute_success_verify_failure_marks_task_failed` as verifying INV-03; this test is
  confirmed present at `tests/agent/workflow/test_workflow_engine.py:469`.
- Re-verified: ADR-001 Decision Detail #5 (line 49) reads "すべてのAgent処理は、単純な質問応答を含め、Workflow Engineの管理下に置かれる。処理が単純であることは、Workflow Engineを迂回する理由にはならない。" — it does not specify or require a separate single-stage Q&A workflow implementation.
- **New finding during this cycle's adversarial verification** (not fully captured by the
  Plan's original Background, which has been corrected — see `plans/20260901-072521_plan.md`
  Background/Design, corrected 2026-09-02): WF-002's actual document text
  (`docs/05_agent_90_inconsistencies_and_known_issues.md` lines 79-97) does not merely omit a
  test for real INV-03. It misquotes INV-03 as "When the Workflow Engine reports successful
  execution, the corresponding document state must reflect that execution" (a RAG-ingestion
  document-state claim unrelated to the real INV-03 text above), and its "Observed
  Implementation" cites `scripts/rag/ingester.py::execute_ingestion()` — confirmed via `ls`/
  `grep` that `scripts/rag/ingester.py` does not exist anywhere in the current repository.
  WF-002 is a fabricated/misattributed entry, not a stale-but-accurate test-gap claim.
- Re-verified: WF-001's document text (lines 57-76) quotes INV-01 as "All execution paths must
  flow through the Workflow Engine" and INV-05 as "The Workflow Engine is the sole orchestrator
  of tool execution" — neither matches the real INV-01/INV-05 text above (this part of the
  Plan's Background was accurate, no correction needed).
- Re-verified: WF-003's document text (lines 101-119) accurately restates its own claim
  ("Decision #5... specifies a simple Q&A single-stage workflow... no such workflow is
  implemented") — the claim itself is a misreading of Decision Detail #5's real text, not a
  misquote of it (this part of the Plan's Background was accurate, no correction needed).
- Re-verified (new, during this cycle): full-document grep of
  `docs/05_agent_90_inconsistencies_and_known_issues.md` for `Status` found exactly 3 matches
  (lines 61, 83, 105 — WF-001/WF-002/WF-003, all `open`); the document is 123 lines total with
  no other discrepancy entries. This resolves the Plan's UNK-04 (see
  `plans/20260901-072521_plan.md`, corrected 2026-09-02): once WF-001/002/003 are closed, the
  "Operational Notes" claim becomes accurate for the first time.

## Design decisions

Per `skills/python-design/SKILL.md` scope (a few relevant bullets only): apply this
document's own 5-level classification scheme (Key Constraints, line 45: Accepted current
specification / Implementation fix required / Documentation fix required / Issue already
tracked / Obsolete and removable) to each entry rather than inventing a new resolution
vocabulary:
- **WF-001**: classify as **Accepted current specification** — the real INV-01 (missing
  file → abort) and INV-05 (invalid file → abort) are two distinct, non-duplicative
  precondition-failure modes, not a documentation defect requiring a fix; the entry's own
  quoted text is stale and must be corrected to the real wording, then the entry closed as
  not describing a real duplication.
- **WF-002**: classify as **Obsolete and removable** — the entry's premise (a
  RAG-ingestion invariant tied to a nonexistent `scripts/rag/ingester.py`) does not
  correspond to any real, current invariant or code path. This is a correction from the
  Plan's original framing ("resolved by an existing test") to a more accurate closure
  reason, since the entry never actually described real INV-03 to begin with.
- **WF-003**: classify as **Documentation fix required**, resolved by this correction —
  the underlying claim is a misreading of ADR-001 Decision Detail #5, not evidence of a
  missing feature; once corrected to state the real Decision Detail #5 text and the
  resolution, the entry is closed.
- Preserve each entry's structural fields (`ID`, `Title`, `Source`, `Owner`, `First Found`,
  `Target`, `Related`) where still accurate; update `Status` to `resolved` (this document's
  own template does not define a `closed` status value distinct from `resolved` — confirmed
  by reading the file's Key Constraints/classification list, which speaks only of
  processing/classifying entries, not a separate lifecycle state), and rewrite `Summary`/
  `Current Description`/`Observed Implementation`/`Resolution Notes` to reflect the
  corrected, current-evidence-based understanding for each entry.

## Alternatives considered

Removing WF-001/WF-002/WF-003 entirely rather than correcting and closing them in place —
rejected: this document's own Key Constraints (line 43) requires resolved-but-informative
entries to remain as a record ("For entries classified as 'Implementation fix required',
create a separate ticket" implies other classifications are resolved in place, not deleted);
none of the three classifications chosen above (Accepted current specification / Obsolete and
removable / Documentation fix required) is "Implementation fix required," so no separate
ticket is warranted, and no deletion is called for either — correcting and closing in place
preserves the audit trail per `rules/coding.md` Documentation notes — "Current behavior"
classification guidance.

## Implementation

### Target file

docs/05_agent_90_inconsistencies_and_known_issues.md

### Procedure

Rewrite the WF-001, WF-002, and WF-003 entries' `Status`, `Summary`, `Current Description`,
`Observed Implementation`, and `Resolution Notes` fields to reflect corrected, current-evidence
findings, and confirm/leave unchanged the "Operational Notes" bullet once all three are closed
(no rewording needed for that bullet itself — see Details).

### Method

1. **WF-001** (current lines 57-76): change `- **Status**: open` (line 61) to
   `- **Status**: resolved`. Rewrite `- **Summary**:` (line 70) to quote the real current
   INV-01/INV-05 text from `docs/adr/ADR-001-workflow-engine-mandatory.md` lines 211-219
   ("ワークフロー定義ファイルが欠落している場合、Agentの起動を中止する。" for INV-01;
   "ワークフロー定義ファイルの検証失敗時は起動を中止する。" for INV-05) and state they are
   two distinct precondition-failure modes (absent vs. present-but-invalid), not a
   duplication. Rewrite `- **Current Description**:` (line 71) and
   `- **Observed Implementation**:` (line 72) to match. Rewrite `- **Resolution Notes**:`
   (line 75) to state the entry is closed as "Accepted current specification — INV-01 and
   INV-05 are distinct, non-duplicative invariants; the entry's originally-quoted text did
   not match the real ADR-001 wording and has been corrected."
2. **WF-002** (current lines 79-98): change `- **Status**: open` (line 83) to
   `- **Status**: resolved`. Rewrite `- **Summary**:` (line 92), `- **Current Description**:`
   (line 93), and `- **Observed Implementation**:` (line 94) to state that the entry's
   original text misquoted INV-03 and cited a nonexistent file
   (`scripts/rag/ingester.py`, confirmed absent from the repository), and that real INV-03
   ("実行成功と検証成功は区別され、それぞれ独立して検証される。") is already verified by
   `test_execute_success_verify_failure_marks_task_failed`
   (`tests/agent/workflow/test_workflow_engine.py:469`, cited in ADR-001's own `##
   Verification` section, lines 250-253). Rewrite `- **Resolution Notes**:` (line 97) to
   state the entry is closed as "Obsolete and removable — the entry's premise did not
   correspond to any real invariant or existing code path."
3. **WF-003** (current lines 101-119): change `- **Status**: open` (line 105) to
   `- **Status**: resolved`. Rewrite `- **Summary**:` (line 114) to state that ADR-001
   Decision Detail #5 requires simple Q&A to remain under Workflow Engine management, and
   does not itself specify a separate single-stage Q&A workflow implementation. Rewrite
   `- **Current Description**:` (line 115) and `- **Observed Implementation**:` (line 116)
   to match. Rewrite `- **Resolution Notes**:` (line 118) to state the entry is closed as
   "Documentation fix required, resolved — the original claim was a misreading of Decision
   Detail #5's actual text."
4. Confirm the "Operational Notes" bullet (line 49, "There are currently no open items...")
   requires no wording change — it is already phrased as a general operational claim, not
   scoped to a specific date, and becomes accurate once WF-001/WF-002/WF-003 are the only
   entries in the document (confirmed, see Assumptions) and all three are closed by this
   change. If a future entry is added and left open, this bullet would again require
   updating at that time — out of scope for this row.

### Details

This does not change the document's classification scheme, template structure, or Key
Constraints section (Plan Scope Out-of-Scope) — only the three named entries' content and,
by consequence, the accuracy of the existing "Operational Notes" bullet (no edit to that
bullet's text itself is required, per Method step 4).

## Compatibility considerations

Documentation-only change to a Known Issues tracking document; no code, schema, or runtime
behavior affected. No other document references WF-001/WF-002/WF-003 by ID (not independently
re-verified beyond a targeted grep during this cycle — see Validation plan) — cross-reference
breakage risk is low given this document's narrow, self-contained entry format.

## Security considerations

N/A: no security-relevant content in a documentation-accuracy correction.

## Rollback considerations

Trivially revertable via `git revert`/`git checkout` of this single file — reverting restores
the three entries' current (stale) text and reopens `Status: open` for all three.

## Validation plan

- Manual review: confirm each entry's rewritten `Summary`/`Current Description`/`Observed
  Implementation` matches the current, re-verified ADR-001/test evidence cited above.
- `rg -n "WF-001|WF-002|WF-003" docs/` and `rg -n "05_agent_90_inconsistencies_and_known_issues" docs/ implementations/ plans/` — confirm no other document cross-references these entries in a way this change would orphan.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py docs/05_agent_90_inconsistencies_and_known_issues.md` — structural checks for the edited file.
- `uv run python tools/check_docs_consistency.py --domain agent` — this file falls under the `agent` domain per `docs/00_index.md`'s Document References by Task mapping.

## Completion criteria

WF-001, WF-002, and WF-003 each have `Status: resolved` with `Summary`/`Current Description`/
`Observed Implementation`/`Resolution Notes` matching current, re-verified evidence; no entry
still quotes stale or fabricated invariant text; the "Operational Notes" claim is accurate
given the (now all-closed) entries in the document.

## Out of scope

Re-editing `docs/adr/ADR-001-workflow-engine-mandatory.md` itself (Plan Scope Out-of-Scope).
Any entry in `docs/05_agent_90_inconsistencies_and_known_issues.md` other than WF-001/WF-002/
WF-003 (none exist per this cycle's full-document scan — see Assumptions, UNK-04). Filing a
new `issues/` ticket for WF-002 (not warranted — classified Obsolete and removable, not
Implementation fix required, per Design decisions).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct and close WF-001 per Method | Pending | — | — | |
| 2 | Correct and close WF-002 per Method | Pending | — | — | |
| 3 | Correct and close WF-003 per Method | Pending | — | — | |
| 4 | Confirm Operational Notes consistency (no edit needed) | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md` / Validation plan above) | Pending | — | — | |
| 6 | Update documentation (N/A — this document is the target of the change itself) | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (correct/close WF-001/WF-002/WF-003; make Operational Notes consistent)
- **Source issue**: issues/20260831-185650_adr001_02_wf001_content_mismatch_agent_known_issues.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-072521_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-183353
- **Related target files**: docs/05_agent_90_inconsistencies_and_known_issues.md

## Goal

`REQ-001`/`REQ-002`: resolve ADR-001 Known Deviations `WF-001` by correcting `INV-05`'s
wording (removing its overlap with `INV-01`) to match the `Verification` section's
existing two-scenario test structure and the implementation's already-distinguishable
exception types, and mark `WF-001` resolved.

## Scope

- **In-Scope**: edit `INV-05`'s text (`docs/adr/ADR-001-workflow-engine-mandatory.md:239`)
  from "ワークフロー定義ファイルの欠落または検証失敗時は起動を中止する。" to "ワークフ
  ロー定義ファイルの検証失敗時は起動を中止する。"; update the `### WF-001` entry
  (currently lines 384-395) to record the "distinguish, don't merge" resolution; add one
  `## Change History` line.
- **Out-of-Scope**: merging `INV-01`/`INV-05` into one Invariant (rejected — the
  `Verification` section already binds two distinct test scenarios to them, and
  `orchestrator.py`'s exception handling already distinguishes `FileNotFoundError` from
  `WorkflowLoadError` as types, even though both currently resolve to the same
  `RuntimeError`-wrapped startup abort); any code change to
  `scripts/agent/startup.py`/`scripts/agent/orchestrator.py` (none needed — see
  Assumptions).

## Assumptions

- Confirmed via Read that `INV-01` (line 235) reads "ワークフロー定義ファイルが欠落し
  ている場合、Agentの起動を中止する。" and `INV-05` (line 239) reads "ワークフロー定義
  ファイルの欠落または検証失敗時は起動を中止する。" — both currently cover the
  missing-file case, confirming the reported duplication.
- Confirmed via Read (`docs/adr/ADR-001-workflow-engine-mandatory.md:291-298`,
  `### Automated Tests`) that the `Verification` section already binds "ワークフロー
  定義欠落時の起動失敗テスト" to `INV-01` and "ワークフロー定義不正時の起動失敗テスト"
  to `INV-05` — two distinct scenarios (missing vs. malformed/invalid), consistent with
  the resolution direction this Requirement adopts (distinguish, not merge).
- Confirmed via Read (`scripts/agent/orchestrator.py:178-182`,
  `Orchestrator.__init__`) that `WorkflowLoader().load()` is wrapped in `except
  (WorkflowLoadError, FileNotFoundError) as exc:`, re-raising as `RuntimeError` — the two
  original exception types remain distinguishable at the point they are caught, even
  though both currently collapse to the same `RuntimeError`-wrapped startup abort
  message; this supports the source Plan's claim that the implementation structure
  already distinguishes the two failure modes, without requiring any code change.
- Confirmed via Read (`scripts/agent/startup.py:314-320`,
  `StartupOrchestrator._check_workflow_definition()`) that `check_workflow_definition()`
  is caught generically via `except RuntimeError as e:` — this is a uniform startup-abort
  action for both failure modes, not a re-merging of the two exception types (the
  distinction is preserved upstream in `orchestrator.py`/`WorkflowLoader`, only the
  final action taken is shared).
- **[Minor finding, not in this Requirement's scope]** `WF-001`'s `Conflicting Source`
  cites `docs/adr/ADR-001-workflow-engine-mandatory.md:243, ...:247`, but `INV-01`/
  `INV-05` are actually at lines 235/239 (a few lines off, likely from prior edits
  shifting line numbers). The entry already carries a `(deprecated: use section-based
  references)` annotation acknowledging this fragility — REQ-001/REQ-002 do not cover
  `Conflicting Source`, so this is left uncorrected here, consistent with how the same
  kind of stale line-number reference was treated as out-of-scope in the companion
  `docs/adr/ADR-002-config-isolation.md` and `WF-003` implementation procedure documents
  generated earlier in this batch.
- **[Cross-document note]** This file is also the target of two other implementation
  procedure documents generated in this same batch: `implementations/20260825-174354_02_docs_adr_ADR-001-workflow-engine-mandatory.md.md`
  (Source plan `plans/20260825-132852_plan.md`, edits the `WF-003` entry and one
  `Change History` line) and (for `docs/adr/ADR-002-config-isolation.md`, a different
  file, not applicable here). Both this document and the `WF-003` document edit
  different, non-overlapping subsections (`INV-05`/`WF-001` here vs. `WF-003` there) of
  the same file, plus each adds one `Change History` line — apply both `Change History`
  additions as two separate lines (do not let one overwrite the other), and re-read the
  file's current state before editing if the other document's changes have already
  landed, since exact line numbers will have shifted.

## Design decisions

- Replace `INV-05`'s text with exactly "ワークフロー定義ファイルの検証失敗時は起動を
  中止する。" — removing "欠落または" only, keeping the rest of the sentence structure
  identical to minimize diff noise.
- Update `WF-001`'s `Recommended Action` to state the adopted resolution: "INV-05の文言
  を「ワークフロー定義ファイルの検証失敗時は起動を中止する。」に訂正し、INV-01（欠落）
  とINV-05（検証失敗）が排他的な2シナリオを指すことを明確化した。既存のVerification節
  ・実装の例外型区別と整合する「区別を明確にする」案を採用（「統合」案は不採用）。"
- Add a `Status: Resolved (2026-08-25)` bullet after `Resolution Target` (same pattern
  used for the companion ADR-002 `CI-001` entry earlier in this batch), preserving
  `Resolution Target`'s historical value.
- Add one `## Change History` line: `- 2026-08-25: WF-001 を解決済みとして記録
  （INV-05の文言を検証失敗のみを指す表現に訂正）。`

## Alternatives considered

- Merging `INV-01`/`INV-05` into a single Invariant: rejected, per the source Plan's own
  Out-of-Scope — would require rewriting the `Verification` section's two-test binding
  and does not match the implementation's already-distinguishable exception types.

## Implementation

### Target file
`docs/adr/ADR-001-workflow-engine-mandatory.md`

### Procedure
1. Before editing, re-run `rg -n "INV-05|WF-001|## Change History"
   docs/adr/ADR-001-workflow-engine-mandatory.md` to get current line numbers — this
   file may have already been edited by the companion `WF-003` implementation procedure
   document (see Assumptions/Cross-document note), which would shift line numbers.
2. Replace `INV-05`'s text per Design decisions.
3. Update the `### WF-001` entry's `Recommended Action`, and add a `Status: Resolved
   (2026-08-25)` bullet after `Resolution Target`.
4. Add one line under `## Change History` — if the `WF-003` document's own
   `Change History` line has already been added, append this line after it rather than
   replacing it.
5. Run `grep -n "欠落" docs/adr/ADR-001-workflow-engine-mandatory.md` and confirm only
   `INV-01`'s line matches.

### Method
Two targeted text replacements (`INV-05`, `WF-001`) plus one new `Change History` line;
no other section of the document is touched.

### Details
- Do not alter `INV-01`, the `Verification` section, or any Decision Details text.

## Compatibility considerations

N/A: documentation-only change, no code or config file is affected.

## Security considerations

N/A: no security-relevant behavior is described or changed.

## Rollback considerations

- Revert `INV-05`'s text, the `WF-001` entry's two edited fields, and remove the added
  `Change History` line.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/adr/ADR-001-workflow-engine-mandatory.md` | Documentation verification | `grep -n "欠落" docs/adr/ADR-001-workflow-engine-mandatory.md` | Only `INV-01`'s line matches |
| `docs/adr/ADR-001-workflow-engine-mandatory.md` | Documentation verification | `uv run python tools/validate_docs_structure.py docs/adr/ADR-001-workflow-engine-mandatory.md` | Passes |

## Completion criteria

- `INV-05`'s text no longer contains "欠落".
- `WF-001`'s `Recommended Action` states the adopted "distinguish" resolution and
  carries a `Status: Resolved (2026-08-25)` marker.
- `## Change History` has one new line for this correction (in addition to, not
  replacing, the companion `WF-003` document's own line).

## Out of scope

- Merging `INV-01`/`INV-05`.
- Any code change to `scripts/agent/startup.py`/`scripts/agent/orchestrator.py`.
- `WF-001`'s `Conflicting Source` line-number reference — pre-existing staleness noted
  in Assumptions, not covered by REQ-001/REQ-002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm current line numbers before editing (this file is also edited by a companion `WF-003` document) | Pending | — | — | |
| 2 | Correct `INV-05`'s text | Pending | — | — | |
| 3 | Update `WF-001`'s `Recommended Action`, add `Status: Resolved` | Pending | — | — | |
| 4 | Add one `Change History` line (append, do not overwrite the companion document's line) | Pending | — | — | |
| 5 | Run documentation validation (`grep`, `validate_docs_structure.py`) | Pending | — | — | |
| 6 | Documentation update | Completed by Steps 2-4 | — | — | This document's entire purpose is the documentation update itself |

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
- **Requirement ID**: `REQ-001`, `REQ-002` — correct `INV-05` wording and resolve `WF-001`
- **Source issue**: `issues/20260822_wkfl_inv_duplication_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-133113_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-180423
- **Related target files**: `docs/adr/ADR-001-workflow-engine-mandatory.md`

## Goal
- REQ-002: replace the inline Japanese marker list with a reference to the checker constant; the file ends with no Japanese or full-width characters and no new checker findings (REQ-007: no regression).

## Scope
- In: the lines listed under Implementation > Details in `docs/00_governance/governance_04_documentation-checks.md`.
- Out: every other line of `docs/00_governance/governance_04_documentation-checks.md` and every other file.

## Assumptions
- Current content re-verified on 2026-10-01 (plan-to-implementation-procedure Step 3a); line numbers are a locating aid and may shift — locate by content.
- No prerequisite gate: this row does not depend on langadr001 output.

## Design decisions
- Reference the constant instead of transcribing tokens (`skills/DESIGN.md` Avoid implementation-reference duplication); no `check_docs_japanese.py` allowlist is needed.
- Edit only the Japanese/full-width text and the minimal surrounding words (Plan Implementation intent).

## Alternatives considered
- Keep the tokens and add a checker allowlist: rejected in Plan Design (tool change out of scope).

## Implementation
### Target file
- `docs/00_governance/governance_04_documentation-checks.md`

### Procedure
1. Check the prerequisite gate in Assumptions (if any); stop and log a blocker if unmet.
2. Locate each line listed in Details by content.
3. Apply the change described in Details.
4. Run the Validation plan.
5. Self-review the meaning and record the result in Execution Status Notes.

### Method
- Targeted single-line edits; confirm with `git diff -U0 docs/00_governance/governance_04_documentation-checks.md` that only the listed lines changed.

### Details
- Current lines:
  - 355: `     (解消/解決/廃止/撤廃/削除済み/確認済み) at the same time, since this repository's` (inside the 'Extended 2026-09-04' note on `_is_historical_context`)
- Change:
  - Rewrite the sentence '`_is_historical_context`'s marker set was extended with Japanese equivalents (解消/...) at the same time, ...' so that it says the marker set was extended with Japanese equivalents, defined in `tools/check_compat_shims.py` `_HISTORICAL_CONTEXT_MARKERS`, without listing the tokens.
  - Keep the rest of the note (reason: mixed-language prose produced false positives; unaffected 'local' meanings) unchanged; reflow only the affected lines to the note's existing indentation.

## Compatibility considerations
- No checker parses this sentence; `tools/check_compat_shims.py` behavior is unchanged.

## Security considerations
- N/A: documentation wording change only.

## Rollback considerations
- Revert with `git checkout -- docs/00_governance/governance_04_documentation-checks.md`; no other file in this Plan depends on this edit.

## Validation plan
- `uv run python tools/check_docs_japanese.py` — file not listed.
- `grep -nP '[\x{3000}-\x{303F}\x{FF00}-\x{FFEF}\p{Hiragana}\p{Katakana}\p{Han}]' docs/00_governance/governance_04_documentation-checks.md` — no output.
- `uv run python tools/check_docs_quality.py` — no new line for this file (baseline 5).

## Completion criteria
- No Japanese characters remain; the note names `_HISTORICAL_CONTEXT_MARKERS` in `tools/check_compat_shims.py`.
- Only the listed lines changed.

## Out of scope
- Pre-existing findings in this file listed in the Plan Design baseline; any line not listed in Details; ADR files; tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Details | Pending | — | — | |
| 2 | Run the Validation plan and compare with the Plan Design baseline | Pending | — | — | |
| 3 | Self-review meaning and record result in Notes | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-007 (AC-002, AC-007) — Plan Implementation steps Step 3
- **Source issue**: issues/20261001-104622_langdoc001_remove-japanese-text-from-non-adr-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-110459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-120650
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md

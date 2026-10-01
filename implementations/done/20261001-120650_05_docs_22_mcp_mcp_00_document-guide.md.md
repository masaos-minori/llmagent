## Goal
- REQ-004: replace the full-width range separator; REQ-005: replace Japanese ADR titles; the file ends with no Japanese or full-width characters and no new checker findings (REQ-007: no regression).

## Scope
- In: the lines listed under Implementation > Details in `docs/22_mcp/mcp_00_document-guide.md`.
- Out: every other line of `docs/22_mcp/mcp_00_document-guide.md` and every other file.

## Assumptions
- Current content re-verified on 2026-10-01 (plan-to-implementation-procedure Step 3a); line numbers are a locating aid and may shift — locate by content.
- Part B only — Prerequisite gate: `plans/done/20261001-105822_plan.md` (langadr001) Execution Status Steps 2-16 must be `Completed` (ADR H1 titles, boilerplate, and ADR-008 Assumptions translated) before this procedure starts. If not, record the blocker in Blocker Log and stop; do not translate independently (Plan Blocker Log, Steps 6-7).

## Design decisions
- Split into Part A (independent) and Part B (gated on langadr001) so the `〜` fix can land before the ADR translation.
- Edit only the Japanese/full-width text and the minimal surrounding words (Plan Implementation intent).

## Alternatives considered
- Use `-` or `..` as the range separator: rejected — ` to ` reads unambiguously next to `/`-separated links.

## Implementation
### Target file
- `docs/22_mcp/mcp_00_document-guide.md`

### Procedure
1. Check the prerequisite gate in Assumptions (if any); stop and log a blocker if unmet.
2. Locate each line listed in Details by content.
3. Apply the change described in Details.
4. Run the Validation plan.
5. Self-review the meaning and record the result in Execution Status Notes.

### Method
- Targeted single-line edits; confirm with `git diff -U0 docs/22_mcp/mcp_00_document-guide.md` that only the listed lines changed.

### Details
- Current lines:
  - 87-90: four chapter-table rows of the form `[mcp_0N_01](...) 〜 [_02](...)/...`
  - 155: `- [ADR-003](...) — RuntimeToolRegistryを唯一のルーティング権威とする`
  - 156: `- [ADR-004](...) — 環境における障害処理方針`
  - 157: `- [ADR-007](...) — HTTP MCP採用とstdio非サポート`
- Change:
  - Part A (Plan Step 5, no gate): in rows 87-90 replace each ` 〜 ` with ` to `; keep every link label/target and `/` separator unchanged.
  - Part B (Plan Step 6, gated): For each listed line, replace only the Japanese title text with the H1 title text (after `ADR-NNN: `) of the ADR the link points to, read from the translated ADR (`grep -h '^# ADR-' docs/10_adr/ADR-*.md`). Keep the link label, link target, separator, and list structure byte-identical.

## Compatibility considerations
- `check_compat_shims.py` reports 5 baseline lines for this file; they must stay identical (no new lines).

## Security considerations
- N/A: documentation wording change only.

## Rollback considerations
- Revert with `git checkout -- docs/22_mcp/mcp_00_document-guide.md`; no other file in this Plan depends on this edit.

## Validation plan
- `grep -n '〜' docs/22_mcp/mcp_00_document-guide.md` — no output after Part A.
- After Part B: `uv run python tools/check_docs_japanese.py` — file not listed; full-width grep (AC-007 pattern) — no output.
- Title comparison: each ADR-003/004/007 description equals the linked ADR's H1 text.
- `uv run python -m tools.check_compat_shims` — same 5 lines for this file as baseline; `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_00_document-guide.md` — only the baseline self-reference finding.

## Completion criteria
- No `〜` remains and table links are unchanged.
- Three ADR descriptions equal the translated ADR H1 titles; no Japanese characters remain.
- Only the listed lines changed.

## Out of scope
- Pre-existing findings in this file listed in the Plan Design baseline; any line not listed in Details; ADR files; tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Part A: replace full-width range separators | Completed | 20261001-140033 | 20261001-140033 |  |
| 2 | Confirm prerequisite gate for Part B | Completed | 20261001-140033 | 20261001-140033 |  |
| 3 | Part B: replace ADR titles | Completed | 20261001-140033 | 20261001-140033 |  |
| 4 | Run the Validation plan and compare with the Plan Design baseline | Completed | 20261001-140033 | 20261001-140033 |  |
| 5 | Self-review meaning and record result in Notes | Completed | 20261001-140033 | 20261001-140033 | Part A: 4 ' 〜 ' range separators -> ' to ' (lines 87-90, link labels/targets unchanged); Part B (langadr001 gate satisfied): ADR-003/004/007 descriptions replaced programmatically with the ADR H1 titles (lines 155-157); baseline compat lines (5) unchanged; all checks unchanged vs batch baseline; full suite deferred to batch end per user decision; docs-mapping step N/A |

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
- **Requirement ID**: REQ-004, REQ-005, REQ-007 (AC-004, AC-005, AC-007) — Plan Implementation steps Step 5 and 6
- **Source issue**: issues/20261001-104622_langdoc001_remove-japanese-text-from-non-adr-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-110459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-120650
- **Related target files**: docs/22_mcp/mcp_00_document-guide.md
## Goal
- Translate all Japanese content of `docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` into English without changing its normative meaning (REQ-001: translate ADR Japanese content), keeping every ADR checker result unchanged (REQ-003: checker baseline preserved) and leaving no Japanese characters (REQ-006: check_docs_japanese clean).

## Scope
- In: front matter `title`, H1, every Japanese heading, prose, list items, and table cells in `docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`; full-width punctuation in the same file.
- Out: every other file, including `docs/10_adr/adr-index.md` (Step 16 document) and area guides that copy this ADR's title (`langdoc001`).

## Assumptions
- Current state (2026-10-01, re-verified in Step 3a): 210 lines contain Japanese, 103 lines contain full-width punctuation; size 18573 bytes.
- Current title: `title: "ADR-007: HTTP MCP採用とstdio非サポート"`; H1: `# ADR-007: HTTP MCP採用とstdio非サポート`.
- `tools/check_adr_structure.py`, `tools/check_adr_reference.py`, `tools/check_adr_invariant_matrix.py` parse only English headings/labels, so translation of Japanese text does not affect their parsing (Plan Problem section).

## Design decisions
- Translate prose only; keep byte-identical: invariant IDs (INV-xx), Known Issue IDs, status values, dates, links and link targets, backtick-quoted identifiers/paths, and English headings parsed by checkers (`## Known Deviations`, `## Implementation Notes`, `### Implementation References`).
- Keep `**Known Issue**:` / `**Resolved**:` labels byte-identical (`check_known_deviation_sync.py` status signal); labels with an attached date stay non-matching (see Details).
- Fixed English wording for the shared boilerplate, identical in every ADR: 'This chapter is not a basis for design decisions.'; 'If not applicable, write "Not applicable".'; 'Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues.' (corrected in code-implementation Step 4b, 2026-10-01: the first and third sentences differ from the English glosses in `governance_01` `## ADR Section Header Standardization`; `langdoc001` procedure `implementations/20261001-120650_14_...` copies this ADR wording into governance_01). Replace the standalone value `対象外` with `Not applicable`.
- Rationale-heading pattern `### N. 最重要の採用理由 — X` / `第Nの採用理由 — X` becomes `### 1. Primary Reason for Adoption — X`, `### 2. Second Reason for Adoption — X`, `### 3. Third Reason for Adoption — X`, `### 4. Fourth Reason for Adoption — X`, used identically across all ADRs.
- Historical/resolved notes: where the original uses 解消/解決/廃止/撤廃/削除済み/確認済み in a historical sense, prefer the English words `resolved`/`removed`/`legacy`/`historical` so `check_compat_shims.py` historical-context detection keeps working.

## Alternatives considered
- Machine-translate the whole file in one pass: rejected — no review granularity; normative wording must be reviewed per section.
- Keep a Japanese parenthetical next to each English term: rejected — `skills/DESIGN.md` Output language allows no exception (bilingual rule handled by `langdoc001`).

## Implementation
### Target file
- `docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`

### Procedure
1. Record the Step 1 baseline outputs for this file (see Validation plan) if not already recorded by Plan Step 1.
2. Translate the front matter `title` and the H1 to the same English title.
3. Translate Japanese headings, preserving level, numbering, and any English suffix.
4. Translate the body section by section, top to bottom; apply the fixed boilerplate wording.
5. Convert remaining full-width punctuation to ASCII equivalents.
6. Run the Validation plan and compare against the baseline; fix only translation-caused differences.
7. Self-review semantic fidelity section by section against `git show HEAD:docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`; record the reviewer and result in the Execution Status Notes.

### Method
- Edit in place with targeted replacements per section (no full-file regeneration), so the diff stays reviewable against the original.
- Use `git diff --word-diff docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` to confirm identifiers, IDs, dates, and links did not change.

### Details
- Japanese headings to translate (4):
  - `# ADR-007: HTTP MCP採用とstdio非サポート`
  - `### 1. 最重要の採用理由 — Operability`
  - `### 2. 第2の採用理由 — Security`
  - `### 3. 第3の採用理由 — Portability`
- Boilerplate sentences present: Implementation Notes boilerplate (quoted by governance_01); 'write Not applicable' boilerplate (quoted by governance_01); Known Deviations boilerplate (quoted by governance_01). Use one fixed English wording for each across all ADRs (see Design decisions) so `governance_01` can quote it once (`langdoc001` REQ-006).
- Japanese historical-sense marker words present: 解決, 廃止.
- Labelled Known Deviations bullets matching `**Known Issue**:`/`**Resolved**:`: 0 (labels unchanged).
- No row-specific hazards found in Step 3a beyond the common rules above.

## Compatibility considerations
- The translated H1 title is copied verbatim by `langdoc001` (`plans/20261001-110459_plan.md` REQ-005) into ADR link descriptions in: mcp_00, agent_00; and by Step 16 (`docs/10_adr/adr-index.md`) of this Plan.
- Shared boilerplate wording must be identical across ADRs so `governance_01` can quote it (`langdoc001` REQ-006).
- `tests/tools/test_check_docs_quality.py` snapshot has 2 row(s) for this file; section-name or similarity changes are reconciled by the Step 17 document (REQ-004), not here.

## Security considerations
- N/A: documentation language change only; no secrets, credentials, or runtime behavior involved.

## Rollback considerations
- Revert with `git checkout -- docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` (single file); no other file depends on this change until Step 16/17 and `langdoc001` Steps 6-7 consume the new title/boilerplate.

## Validation plan
- `uv run python tools/check_docs_japanese.py` — `docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` not listed.
- `grep -nP '[\x{3000}-\x{303F}\x{FF00}-\x{FFEF}\p{Hiragana}\p{Katakana}\p{Han}]' docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` — no output.
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/check_adr_invariant_matrix.py` — "No issues found".
- `uv run python tools/check_known_deviation_sync.py` — baseline for this file: no finding attributed to this file; output unchanged.
- `uv run python -m tools.check_compat_shims` and `uv run python -m tools.check_compat_shims --check-removed-names` — no `docs/10_adr/` line.
- `uv run python tools/check_docs_structure.py "docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md"` — no finding outside the Plan Design baseline (size finding may only disappear).
- `wc -c docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` — record after-size.

## Completion criteria
- `docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` contains no Japanese or full-width characters.
- Front matter `title` and H1 carry the same English title.
- All Validation plan commands meet their expected outcome.
- Semantic-fidelity self-review recorded in Execution Status Notes.
- Size before: 18573 bytes (under the limit). Record the after-size for the Step 18 report (REQ-005).

## Out of scope
- Any decision, invariant, status, or date change; restructuring or splitting the ADR; fixing pre-existing broken links or known_deviation_sync findings; edits to any other file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record baseline outputs for this file | Completed | 20261001-130621 | 20261001-130621 | baseline from batch start (scratchpad base/); stale_detector clean; Step 4b corrected boilerplate-gloss claim |
| 2 | Translate front matter title and H1 | Completed | 20261001-130714 | 20261001-130714 |  |
| 3 | Translate Japanese headings | Completed | 20261001-130714 | 20261001-130714 |  |
| 4 | Translate body, boilerplate, and tables; convert full-width punctuation | Completed | 20261001-130714 | 20261001-130714 |  |
| 5 | Run the Validation plan and compare with baseline | Completed | 20261001-130714 | 20261001-130714 |  |
| 6 | Semantic-fidelity self-review and size record | Completed | 20261001-130714 | 20261001-130714 | 211 JP/full-width lines translated (line-aligned, indentation preserved); all validations pass (known_deviation_sync unchanged: the MCP-001/MCP-002 mention in Known Deviations is a paragraph, not scanned); compat 0; size 18573->18180 (under limit); lines 131/157 translated by meaning ('would rule out ...'); snapshot diff reconciled by seq 16; targeted tests only, full suite deferred per user decision; docs step N/A |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-006 (ADR translation; checker baseline preserved; no Japanese remains) — Plan Implementation steps Step 8
- **Source issue**: issues/20261001-104551_langadr001_translate-japanese-adr-content-to-english.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-105822_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-115707
- **Related target files**: docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md
# Implementation Procedure: Standardize Terminology and Repair Verified Markdown Quality Defects in docs/

## Goal
Bring `docs/*.md` terminology (EventBus / Known Issue / Needs Confirmation) into alignment with the existing canonical glossary, remove confirmed duplicate `## Related Documents` bullets, fix the self-referential "Part 1" link and duplicated section content in `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`, and replace unstable source line-number citations with stable symbol references — as a documentation-only change with zero code/behavior impact.

## Goal
Bring `docs/*.md` terminology (EventBus / Known Issue / Needs Confirmation) into alignment with the existing canonical glossary, remove confirmed duplicate `## Related Documents` bullets, fix the self-referential "Part 1" link and duplicated section content in `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`, and replace unstable source line-number citations with stable symbol references — as a documentation-only change with zero code/behavior impact.

## Scope
- Target files: `docs/*.md` (163 files with `## Keywords`, 112 with `## Related Documents`)
- Specific files to fix:
  - `docs/01_overview-files-03-scripts.md` — remove 30 duplicate self-reference bullets across 10 `## Related Documents` sections
  - `docs/03_rag_00_document-guide.md` — remove 1 duplicate bullet
  - `docs/03_rag_03_07_query_pipeline-tests.md` — remove 1 duplicate bullet
  - `docs/04_mcp_03_01_dispatch-and-routing.md` — remove 1 duplicate bullet
  - `docs/04_mcp_03_02_tool-registry.md` — remove 1 duplicate bullet
  - `docs/04_mcp_03_04_tool-call-tracing-and-watchdog.md` — remove 1 duplicate bullet
  - `docs/04_mcp_03_05_lifecycle-and-new-server.md` — remove 1 duplicate bullet
  - `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` — delete duplicated `## 2c.` section; remove/rewrite two dangling self-referential "Part 1" links
  - `docs/00_governance_05_deprecated-items.md` line 22 — replace `rag_pipeline_models.py:99-101` with stable symbol reference
  - `docs/00_governance_07_needs-confirmation-inventory.md` lines 69, 83, 156, 273 — replace exact line numbers with symbol names
  - `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` line 89 — replace `mdq_server.py:368` with function/symbol name
  - All `docs/*.md` — sweep non-canonical EventBus/Known Issue/Needs Confirmation spellings

## Assumptions
- The glossary file `docs/00_governance_09_terminology-glossary.md` is authoritative for canonical forms
- EventBus is CamelCase in English prose, "Event Bus" (with space) in Japanese text
- Code fences, file paths, and identifiers must not be touched
- Duplicate `## Related Documents` bullets found in 7 files + `01_overview-files-03-scripts.md` (10x duplication)
- The "Part 1" self-link and duplicated `## 2c.` section in `03_rag_03_02_query_pipeline-rag-pipeline-class.md` are vestigial copy-paste artifacts

## Design decisions
- Use exact forms from `docs/00_governance_09_terminology-glossary.md`:
  - English prose: "EventBus" (CamelCase)
  - Japanese prose: "Event Bus" (with space)
  - "Known Issue" / "既知の問題" (canonical)
  - "Needs Confirmation" / "要確認" (canonical)
- Only normalize prose/headings; skip code fences, paths, identifiers
- Per-occurrence manual/scripted classification before editing; no blind sed-replace
- Duplicate bullets: remove extras, keep one instance
- "Part 1" self-links: replace with plain prose or correct cross-reference
- Duplicated `## 2c.` section: delete entirely (byte-for-byte duplicate of `## 2b.`)
- Line-number citations: replace with symbol names where stable anchor exists; otherwise prefix with `~`

## Implementation steps

### Phase 1: Preparation
1. Re-confirm `docs/00_governance_09_terminology-glossary.md` current content (read-only sanity check)
2. Build per-file worklist: run the duplicate-`## Related Documents`-bullet detection script across all `docs/*.md`

### Phase 2: Core content fixes
1. **Step 2a**: Fix `docs/01_overview-files-03-scripts.md` — remove 30 duplicate self-reference bullets across 10 `## Related Documents` sections (keep one self-reference + one `01_overview.md` per section)
2. **Step 2b**: Fix 6 files with single duplicate bullet each:
   - `docs/03_rag_00_document-guide.md`
   - `docs/03_rag_03_07_query_pipeline-tests.md`
   - `docs/04_mcp_03_01_dispatch-and-routing.md`
   - `docs/04_mcp_03_02_tool-registry.md`
   - `docs/04_mcp_03_04_tool-call-tracing-and-watchdog.md`
   - `docs/04_mcp_03_05_lifecycle-and-new-server.md`
3. **Step 2c**: Fix `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`:
   - Read full file end-to-end
   - Delete duplicated `## 2c.` section and stray mid-file Related-Documents/Keywords/H1 block
   - Remove two self-referential "Part 1" links
   - Diff result against pre-edit version to confirm no unique content lost
4. **Step 2d**: Fix line-number citations:
   - `docs/00_governance_05_deprecated-items.md` line 22
   - `docs/00_governance_07_needs-confirmation-inventory.md` lines 69, 83, 156, 273
   - `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` line 89
5. **Step 2e**: Sweep `docs/*.md` for non-canonical EventBus/Known Issue/Needs Confirmation spellings in prose/headings (skip code fences, paths, identifiers)

### Phase 3: Verification (documentation-only gate)
1. Re-run grep-based verification scans:
   - EventBus variant-count scan
   - Known Issue / Needs Confirmation sweep
   - `## Related Documents` duplicate-bullet re-scan
   - Part-1 self-link / 2b-2c duplication check
   - Line-number citation cleanup check
2. `git diff --name-only` restricted to `docs/` and `requires/` — confirm only `docs/*.md` and `requires/` files changed
3. No deployment step applies (documentation-only change)

## Validation plan
- EventBus terminology sweep: `grep -oi "eventbus" docs/*.md | ...` — only glossary's preferred forms remain in prose/headings
- Known Issue / Needs Confirmation sweep: `grep -rn "Needs Confirmation\|要確認\|未確認" docs/` — every active marker outside governance-definition docs resolves to a registered, linked entry
- `## Related Documents` duplicate bullets: structural re-scan — zero sections with repeated bullet
- Part-1 self-link / 2b-2c duplication: `grep -n "Part 1" docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`; `diff` of 2b vs remaining content
- Line-number citation cleanup: `grep -rn '\.py:[0-9]\+' docs/*.md` — remaining hits are either symbol-qualified or `~`-prefixed
- Overall: `git diff --name-only` restricted to `docs/` and `requires/` — zero files outside those two directories changed

## Traceability
- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/done/20260818-222741_require.md
- Source plan: plans/20260819-181042_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-151035
- Related target files: (see Affected areas list in plan)